# INR (Item Not Received) Abuse Detection

*Signal spec for the Inconsistency Engine · Companion to FUSION_SCORING_V2.md and DAMAGE_CLAIM_DETECTION.md*

---

## 1. The problem precisely stated

The carrier scan says "delivered." The customer says "never arrived." Both can be telling the truth. Both can be lying. The system's job is to determine which — without treating innocent customers as suspects.

There are exactly three real scenarios:

| Scenario | What happened | Correct response |
|---|---|---|
| Genuine non-delivery | Carrier misdelivered (wrong address, wrong building, left with neighbour) | Refund or reship. Carrier is liable. |
| Genuine theft | Package stolen after correct delivery | Refund. Customer is innocent. |
| INR abuse | Customer received the package and is lying | Deny with evidence. |

The detection system must separate scenario 3 from scenarios 1 and 2. Misidentifying scenario 1 or 2 as fraud is the primary false positive risk — and it is severe, because the customer did nothing wrong.

---

## 2. Signal architecture overview

Six independent signals feed into the INR scorer. Each runs in parallel. No single signal can trigger a denial alone.

```
INR claim submitted
        |
        ├── Signal 1: GPS delivery verification
        ├── Signal 2: Post-delivery engagement
        ├── Signal 3: Customer INR history
        ├── Signal 4: Address/neighbourhood intelligence
        ├── Signal 5: OTP delivery confirmation (preventive)
        └── Signal 6: Ring detection (cross-account)
        |
        ↓
INR scorer (weighted fusion, 0–100)
        |
        ↓
Proportional response (refund / investigate / deny+evidence)
```

---

## 3. Signal 1 — GPS delivery verification

### 3.1 What to collect

Every carrier webhook event for `SHIPMENT_DELIVERED` must include:

```json
{
  "event":        "SHIPMENT_DELIVERED",
  "shipment_id":  "SHP-8821",
  "timestamp":    "2026-04-29T14:23:11Z",
  "driver_id":    "DRV-441",
  "gps_lat":      12.9716,
  "gps_lng":      77.5946,
  "accuracy_m":   8,
  "scan_type":    "BARCODE",
  "photo_url":    "https://carrier.cdn/proof/SHP-8821.jpg",
  "left_at":      "FRONT_DOOR"
}
```

Store `gps_lat`, `gps_lng`, `accuracy_m`, `photo_url`, and `left_at` in your `shipment_deliveries` table the moment the webhook fires. You need this permanently — it is your evidence in a chargeback dispute.

```sql
CREATE TABLE shipment_deliveries (
  shipment_id     TEXT PRIMARY KEY,
  order_id        TEXT NOT NULL,
  account_id      TEXT NOT NULL,
  delivered_at    TIMESTAMP NOT NULL,
  driver_id       TEXT,
  gps_lat         NUMERIC(9,6),
  gps_lng         NUMERIC(9,6),
  gps_accuracy_m  INT,
  photo_url       TEXT,
  left_at         TEXT,
  raw_payload     JSONB,
  created_at      TIMESTAMP DEFAULT now()
);
```

### 3.2 The 200-metre rule

```python
from geopy.distance import geodesic

def score_gps_verification(shipment_id: str, claim: INRClaim) -> GPSSignal:
    delivery = db.get(ShipmentDelivery, shipment_id)
    if not delivery or not delivery.gps_lat:
        # No GPS data — carrier didn't provide it
        # Do NOT treat as fraud signal. Treat as inconclusive.
        return GPSSignal(score=0, verdict="NO_GPS_DATA",
                         reason="Carrier did not provide GPS coordinates")

    delivery_coords = (delivery.gps_lat, delivery.gps_lng)
    address_coords  = geocode(claim.delivery_address)  # from address intelligence module

    distance_m = geodesic(delivery_coords, address_coords).meters

    if distance_m > 500:
        # Driver was far from address — likely misdelivery
        # Customer is probably innocent
        return GPSSignal(score=0, verdict="LIKELY_MISDELIVERY",
                         reason=f"Driver scanned {distance_m:.0f}m from delivery address. "
                                f"Possible misdelivery — carrier responsible.")

    elif distance_m > 150:
        # Ambiguous — GPS accuracy + building size can explain this
        return GPSSignal(score=20, verdict="GPS_MARGINAL",
                         reason=f"Driver {distance_m:.0f}m from address — within plausible range")

    else:
        # Driver was at the address
        return GPSSignal(score=55, verdict="GPS_CONFIRMED",
                         reason=f"Driver GPS confirmed at delivery address ({distance_m:.0f}m)")
```

**Why GPS confirmation scores 55, not 100:** GPS confirmation means the driver was there — it does not prove the customer received it. The package could have been left at the door and stolen. GPS is necessary but not sufficient. It combines with other signals.

### 3.3 Delivery photo check

If the carrier provided a delivery photo, run a basic validation:

```python
def check_delivery_photo(photo_url: str, claim: INRClaim) -> int:
    if not photo_url:
        return 0  # No photo — neutral

    # Check photo timestamp (stored in carrier webhook) vs delivery timestamp
    # A photo taken hours after the delivery scan is suspicious
    # (driver may have photographed a different address later)

    # For MVP: simply confirm photo exists and log its URL for human review
    # In production: vision model checks if photo shows correct address/building
    return 10  # photo exists — mild corroboration
```

---

## 4. Signal 2 — Post-delivery engagement

### 4.1 The principle

After a package is delivered, a customer who actually received it will interact with the product or your platform. A customer who genuinely did not receive it will have no product-linked activity after the delivery date.

This is the strongest single signal for INR fraud — and the one the base document is correct to highlight.

### 4.2 Engagement events to collect

Register these events on every relevant user action:

```python
# Write to engagement_events table on every trigger
ENGAGEMENT_TRIGGERS = {
    "APP_LOGIN_POST_DELIVERY":      40,  # logged into app after delivery date
    "PRODUCT_APP_LOGIN":            60,  # logged into product's own app (phone, laptop, etc.)
    "WARRANTY_REGISTERED":          80,  # registered warranty for this product
    "QR_SCAN_PACKAGING":            90,  # scanned QR code on the box
    "PRODUCT_REVIEW_SUBMITTED":     85,  # left a review mentioning this product
    "WISHLIST_REMOVED_SAME_SKU":    50,  # removed product from wishlist after delivery
    "REORDER_SAME_SKU":             70,  # ordered same product again (suggests possession)
    "RETURN_INITIATED_DIFFERENT":   30,  # initiated a non-INR return on same order
}
```

```sql
CREATE TABLE engagement_events (
  id            SERIAL PRIMARY KEY,
  account_id    TEXT NOT NULL,
  order_id      TEXT NOT NULL,
  event_type    TEXT NOT NULL,
  occurred_at   TIMESTAMP NOT NULL,
  metadata_json JSONB,
  created_at    TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_engagement_order ON engagement_events (order_id, occurred_at);
```

### 4.3 Engagement scorer

```python
def score_post_delivery_engagement(order_id: str, delivered_at: datetime,
                                    claim: INRClaim) -> EngagementSignal:
    events = db.query(EngagementEvent).filter(
        EngagementEvent.order_id   == order_id,
        EngagementEvent.occurred_at > delivered_at
    ).all()

    if not events:
        # No engagement — does NOT mean fraud
        # Genuinely innocent customers also have no engagement
        return EngagementSignal(score=0, verdict="NO_ENGAGEMENT_DATA",
                                reason="No post-delivery activity detected — inconclusive")

    # Take the highest-weight event as the primary signal
    # (multiple events don't stack — one is enough to confirm possession)
    top_event = max(events, key=lambda e: ENGAGEMENT_TRIGGERS.get(e.event_type, 0))
    top_score = ENGAGEMENT_TRIGGERS.get(top_event.event_type, 0)

    return EngagementSignal(
        score   = top_score,
        verdict = "ENGAGEMENT_FOUND",
        reason  = f"{top_event.event_type} at {top_event.occurred_at} "
                  f"— {(top_event.occurred_at - delivered_at).days} days after delivery",
        events  = events
    )
```

**Critical false positive protection:** no engagement data returns score 0, not a high score. Absence of engagement is not evidence of fraud — it is simply the absence of evidence. Many legitimate customers never log into apps, register warranties, or leave reviews.

---

## 5. Signal 3 — Customer INR history

### 5.1 Claim count thresholds

```python
def score_inr_history(account_id: str, current_claim: INRClaim) -> HistorySignal:
    # Count prior INR claims in last 12 months
    prior_claims = db.query(ReturnDecision).filter(
        ReturnDecision.account_id   == account_id,
        ReturnDecision.claim_type   == "INR",
        ReturnDecision.created_at   >= datetime.now() - timedelta(days=365)
    ).count()

    if prior_claims == 0:
        return HistorySignal(score=0,
                             reason="First INR claim — assume genuine")

    elif prior_claims == 1:
        return HistorySignal(score=25,
                             reason="Second INR claim in 12 months — soft flag")

    elif prior_claims == 2:
        return HistorySignal(score=55,
                             reason="Third INR claim — pattern emerging")

    else:
        return HistorySignal(score=80,
                             reason=f"{prior_claims + 1} INR claims in 12 months — high-risk account")
```

### 5.2 Claim value escalation pattern

A separate sub-signal: if a customer's INR claims are increasing in value over time, that is a testing pattern — they start small to verify the system works, then escalate.

```python
def score_value_escalation(account_id: str, current_value: float) -> int:
    prior_inr_values = db.query(ReturnDecision.order_value).filter(
        ReturnDecision.account_id == account_id,
        ReturnDecision.claim_type == "INR"
    ).order_by(ReturnDecision.created_at).all()

    if len(prior_inr_values) < 2:
        return 0

    values = [r.order_value for r in prior_inr_values] + [current_value]
    # Check if each claim is larger than the previous
    if all(values[i] < values[i+1] for i in range(len(values)-1)):
        return 35  # strictly escalating claim values — testing pattern
    return 0
```

---

## 6. Signal 4 — Address and neighbourhood intelligence

### 6.1 Building-level vs. account-level distinction

This is the most important false positive protection in the entire INR module. Some buildings and neighbourhoods have genuine delivery problems — poor access, unreliable carriers, security restrictions. If multiple customers at the same address report INR, the problem is the carrier, not the customers.

```python
def score_address_inr_intelligence(delivery_address: str,
                                    account_id: str) -> AddressINRSignal:
    address_hash = hash_canonical(delivery_address)  # from address intelligence module

    # How many DISTINCT accounts at this address have filed INR in 90 days?
    distinct_accounts = db.query(
        func.count(distinct(INRClaim.account_id))
    ).filter(
        INRClaim.address_hash == address_hash,
        INRClaim.created_at   >= datetime.now() - timedelta(days=90)
    ).scalar()

    # How many INR claims from THIS specific account at this address?
    account_claims_here = db.query(INRClaim).filter(
        INRClaim.address_hash == address_hash,
        INRClaim.account_id   == account_id
    ).count()

    # Multiple distinct accounts = delivery problem, not fraud
    if distinct_accounts >= 5:
        return AddressINRSignal(
            score   = 0,
            verdict = "BUILDING_DELIVERY_PROBLEM",
            reason  = f"{distinct_accounts} different customers at this address "
                      f"reported INR — carrier delivery issue, not fraud. "
                      f"Escalate to carrier operations team."
        )

    # Same account, same address, multiple claims = fraud
    if account_claims_here >= 2:
        return AddressINRSignal(
            score   = 65,
            verdict = "REPEAT_ACCOUNT_SAME_ADDRESS",
            reason  = f"This account has filed {account_claims_here} INR claims "
                      f"at this address"
        )

    return AddressINRSignal(score=0, verdict="ADDRESS_CLEAN")
```

### 6.2 Pincode-level delivery reliability

Pull from `pincode_intelligence` table (seeded in carrier signals module):

```python
def score_pincode_delivery_reliability(pincode: str) -> int:
    intel = db.get(PincodeIntelligence, pincode)
    if not intel:
        return 0

    # High RTO rate pincodes have real delivery problems — lower suspicion
    if intel.rto_rate >= 35:
        return -10  # negative weight — reduce suspicion for known-problematic areas
    return 0
```

---

## 7. Signal 5 — OTP delivery confirmation (preventive layer)

### 7.1 How it works

OTP at doorstep converts INR from a detective problem (catching fraud after it happens) into a preventive one (making the fraud impossible). Once the customer's phone number confirms receipt, no INR claim can succeed.

```
Order dispatched
        ↓
Order value check (see threshold table below)
        ↓
If OTP required: flag set on shipment record
        ↓
Driver's carrier app prompts for OTP on arrival
        ↓
Customer receives SMS OTP on registered mobile
        ↓
Customer provides OTP to driver
        ↓
Driver enters OTP → delivery marked CONFIRMED_OTP
        ↓
Stored in shipment_deliveries.otp_confirmed = true
```

### 7.2 Value thresholds

| Order value | OTP required | Signature required | Delivery photo |
|---|---|---|---|
| Under ₹500 / $10 | No | No | No |
| ₹500–₹2,000 / $10–$40 | No | No | Yes |
| ₹2,000–₹10,000 / $40–$200 | Yes | No | Yes |
| Above ₹10,000 / $200 | Yes | Yes | Yes |

### 7.3 INR scorer integration

```python
def check_otp_confirmation(shipment_id: str) -> OTPSignal:
    delivery = db.get(ShipmentDelivery, shipment_id)

    if delivery.otp_confirmed:
        # Customer's own phone number confirmed receipt
        # This is a hard signal — INR claim is almost certainly fraudulent
        return OTPSignal(score=92,
                         reason="OTP confirmation on file — customer's registered "
                                "mobile confirmed delivery")

    if delivery.otp_required and not delivery.otp_confirmed:
        # OTP was required but not completed — could be legitimate
        # (customer not home, no signal, OTP not received)
        return OTPSignal(score=0,
                         verdict="OTP_INCOMPLETE",
                         reason="OTP required but not completed — treat as standard delivery")

    return OTPSignal(score=0)  # OTP not required for this order value
```

### 7.4 Why OTP is not used for all orders

OTP adds 2–3 minutes per delivery. At 10,000 deliveries per day that is 500 hours of added delivery time across the fleet. SMS cost per OTP is ₹0.10–₹0.20 — negligible for high-value orders, not justified for a ₹99 item. Rural areas with poor mobile signal would see a spike in OTP failures, creating false "unconfirmed" records. The value-tiered approach gives full protection where fraud is costly and zero friction where it is not.

---

## 8. Signal 6 — Ring detection for INR

This signal reuses the velocity and graph infrastructure from `FUSION_SCORING_V2.md`. No new data collection required.

```python
def score_inr_ring_detection(account_id: str, claim: INRClaim) -> RingSignal:
    # Check if this account is in a known cluster
    cluster_id = redis.get(f"ring:account:{account_id}")

    if cluster_id:
        cluster_size = redis.scard(f"ring:cluster:{cluster_id}")
        inr_count_in_cluster = db.query(func.count(INRClaim.id)).filter(
            INRClaim.cluster_id == cluster_id,
            INRClaim.created_at >= datetime.now() - timedelta(days=30)
        ).scalar()

        if inr_count_in_cluster >= 5:
            return RingSignal(
                score   = 85,
                reason  = f"Cluster {cluster_id} has filed {inr_count_in_cluster} "
                          f"INR claims in 30 days across {cluster_size} accounts"
            )

    # Check device-level: multiple accounts on same device filing INR
    device_inr = db.query(func.count(INRClaim.id)).join(
        DeviceFingerprint,
        DeviceFingerprint.account_id == INRClaim.account_id
    ).filter(
        DeviceFingerprint.hash == claim.device_hash,
        INRClaim.created_at    >= datetime.now() - timedelta(days=60)
    ).scalar()

    if device_inr >= 3:
        return RingSignal(
            score  = 75,
            reason = f"{device_inr} INR claims from accounts sharing this device fingerprint"
        )

    return RingSignal(score=0)
```

---

## 9. Complete INR scorer

```python
def score_inr_claim(claim: INRClaim, order: Order, account_id: str) -> INRResult:
    # Run all signals in parallel
    gps_sig, engage_sig, history_sig, addr_sig, otp_sig, ring_sig = await asyncio.gather(
        score_gps_verification(claim.shipment_id, claim),
        score_post_delivery_engagement(order.id, order.delivered_at, claim),
        score_inr_history(account_id, claim),
        score_address_inr_intelligence(claim.delivery_address, account_id),
        check_otp_confirmation(claim.shipment_id),
        score_inr_ring_detection(account_id, claim)
    )

    # Hard exits — short-circuit before fusion
    if gps_sig.verdict == "LIKELY_MISDELIVERY":
        return INRResult(decision="REFUND_CARRIER_FAULT",
                         score=0, reason=gps_sig.reason)

    if addr_sig.verdict == "BUILDING_DELIVERY_PROBLEM":
        return INRResult(decision="REFUND_ESCALATE_CARRIER",
                         score=0, reason=addr_sig.reason)

    # Weighted fusion
    raw = (
        gps_sig.score     * 0.25
      + engage_sig.score  * 0.30   # highest weight — product engagement is definitive
      + history_sig.score * 0.15
      + addr_sig.score    * 0.10
      + otp_sig.score     * 0.10   # hard signal when present
      + ring_sig.score    * 0.10
    )

    # Corroboration: 2+ signals above 60 amplifies
    high = sum(1 for s in [gps_sig.score, engage_sig.score, otp_sig.score,
                            ring_sig.score] if s >= 60)
    if high >= 2:
        raw = min(raw * 1.20, 100)

    evidence = [s.reason for s in [gps_sig, engage_sig, history_sig,
                                    addr_sig, otp_sig, ring_sig] if s.score > 0]

    return INRResult(score=round(raw), evidence=evidence)
```

---

## 10. Decision mapping

| INR score | Decision | Customer experience |
|---|---|---|
| Hard exit: misdelivery | Refund + carrier complaint filed automatically | "We've identified a delivery issue and processed your refund" |
| Hard exit: building problem | Refund + carrier escalation | Same as above |
| 0–30 | Auto-refund | Instant. No friction. |
| 31–55 | Carrier investigation first | "We've raised an investigation with the carrier. Refund within 3–5 days." |
| 56–75 | Agent review | "Your claim is under review. You'll hear back within 24 hours." |
| 76–100 | Hold with evidence package | Agent reviews GPS data, engagement log, OTP record. Decision within 48h. Appeal path always shown. |

---

## 11. Evidence package for chargebacks

When a chargeback is filed for an INR dispute, auto-assemble this from stored data:

```python
def build_chargeback_evidence(order_id: str) -> ChargebackPackage:
    delivery  = db.get(ShipmentDelivery, order_id=order_id)
    events    = db.query(EngagementEvent).filter_by(order_id=order_id).all()
    inr_score = db.get(INRResult, order_id=order_id)

    return ChargebackPackage(
        delivery_timestamp = delivery.delivered_at,
        gps_coordinates    = f"{delivery.gps_lat}, {delivery.gps_lng}",
        distance_from_addr = inr_score.gps_distance_m,
        delivery_photo_url = delivery.photo_url,
        otp_confirmed      = delivery.otp_confirmed,
        post_delivery_activity = [
            f"{e.event_type} at {e.occurred_at}" for e in events
        ],
        carrier_driver_id  = delivery.driver_id,
    )
    # Exported as PDF for bank dispute submission
```

---

## 12. Database additions required

```sql
-- INR claim record (extends existing return_decisions)
ALTER TABLE return_decisions ADD COLUMN inr_gps_distance_m    INT;
ALTER TABLE return_decisions ADD COLUMN inr_otp_confirmed     BOOLEAN DEFAULT false;
ALTER TABLE return_decisions ADD COLUMN inr_engagement_found  BOOLEAN DEFAULT false;
ALTER TABLE return_decisions ADD COLUMN inr_evidence_json     JSONB;

-- Engagement events (new table)
CREATE TABLE engagement_events (
  id           SERIAL PRIMARY KEY,
  account_id   TEXT NOT NULL,
  order_id     TEXT NOT NULL,
  event_type   TEXT NOT NULL,
  occurred_at  TIMESTAMP NOT NULL,
  metadata_json JSONB,
  created_at   TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_engagement_order   ON engagement_events (order_id, occurred_at);
CREATE INDEX idx_engagement_account ON engagement_events (account_id, event_type);

-- OTP confirmation field on shipment_deliveries (already created in carrier signals module)
ALTER TABLE shipment_deliveries ADD COLUMN otp_confirmed  BOOLEAN DEFAULT false;
ALTER TABLE shipment_deliveries ADD COLUMN otp_required   BOOLEAN DEFAULT false;
ALTER TABLE shipment_deliveries ADD COLUMN otp_timestamp  TIMESTAMP;
```

---

## 13. Dependencies

```txt
geopy>=2.4.0        # GPS distance calculation — already in damage claims module
asyncio             # stdlib — parallel signal execution
```

No new external APIs required. All data comes from carrier webhooks (already set up in carrier signals module) and internal engagement event collection.

---

## 14. Build order for the hackathon

| Priority | Task | Time | Dependency |
|---|---|---|---|
| 1 | Carrier webhook GPS ingestion + `shipment_deliveries` table | 30 min | Carrier webhook already set up |
| 2 | GPS scorer (200m rule + hard exits) | 20 min | Above |
| 3 | Engagement events table + write triggers | 40 min | None |
| 4 | Engagement scorer | 20 min | Above |
| 5 | INR history scorer | 15 min | Existing `return_decisions` table |
| 6 | Address building vs account distinction | 20 min | Address intelligence module |
| 7 | OTP field additions + scorer | 20 min | Carrier webhook |
| 8 | Ring detection (reuse from FUSION_SCORING_V2) | 10 min | Already built |
| 9 | Full `score_inr_claim()` fusion | 25 min | All above |
| 10 | Chargeback evidence package builder | 20 min | Above |

**Total: ~3.5 hours.** All signals except engagement events reuse infrastructure already built in other modules.

---

## 15. What the base document got right and what this spec adds

| Capability | Base document | This spec |
|---|---|---|
| GPS 200m rule | Described conceptually | Implemented with `geopy`, thresholds, and hard exit logic |
| Post-delivery engagement | Described with examples | Event taxonomy, scoring weights, database schema, false positive protection |
| INR history scoring | Tier table provided | Implemented with 12-month window + value escalation sub-signal |
| Building vs account distinction | Described conceptually | Implemented with `distinct_accounts` query and hard exit |
| OTP delivery confirmation | Described with flow | Value thresholds, scorer integration, why not universal |
| Ring detection | Graph check described | Implemented using existing ring infrastructure from FUSION_SCORING_V2 |
| Chargeback evidence | Not mentioned | Full evidence package builder for bank dispute submission |
| False positive protection | Mentioned | Explicit: no engagement = neutral not suspicious; misdelivery = hard refund exit |

---

*The single most important rule from the base document stands: genuine customers leave no post-delivery digital trail because they have nothing to hide. Fraudsters always leave one — app logins, warranty registration, product reviews. That trail is collected silently and costs the customer nothing. The OTP layer makes INR fraud structurally impossible for high-value orders. Together they leave INR abuse with nowhere to go.*
