# Address Intelligence — 5th Signal Spec

*Generated: 2026-04-29 · Companion to [MARKET_RESEARCH.md](MARKET_RESEARCH.md) and [EXCEPTION_FRAMING.md](EXCEPTION_FRAMING.md)*

This document specifies the address-validation layer that becomes the **5th signal** in the Inconsistency Engine fusion. It is informed by competitive research on Shiprocket Engage and direct evaluation of Google's India-specific Address Validation API.

---

## 1. Why address intelligence is a distinct signal

Address data is dual-purpose: it operates **both at order placement (preventive)** and **at return claim time (detective)**. No competitor we surveyed runs the same address logic at both points. By doing so, the engine catches:

- **Fake addresses** at the front door (fraudulent orders never ship)
- **Recycled addresses** across multiple accounts (ring-cluster formation)
- **Address-manipulation patterns** designed to defeat naive deduplication
- **Tier-3 high-RTO zones** that correlate with COD fraud
- **Sub-premise inconsistencies** (claimed apartment doesn't exist)

The Indian context makes this especially valuable: addresses are non-standardised across cities, COD fraud rates are 8–10% ([bePragma/Razorpay](https://www.bepragma.ai/blogs/cod-fraud-in-indian-e-commerce)), and Tier-3 RTO rates hit 40–45% ([Delhivery via bePragma](https://www.bepragma.ai/blogs/cod-fraud-in-indian-e-commerce)).

---

## 2. Competitive analysis: how Shiprocket Engage works

Shiprocket Engage 360 ([product page](https://www.shiprocket.in/engage360/solution/)) is the dominant Indian solution. Its mechanism:

| Capability | How it works | Limitation |
|---|---|---|
| Address-quality score | Proprietary algorithm flags incomplete addresses | Pincode-level only, no sub-premise validation |
| WhatsApp confirmation loop | Auto-message asks customer to verify/correct address before shipping | Reactive, post-order only |
| COD-to-prepaid conversion | WhatsApp discount offers to risky-COD customers | Doesn't address fraudulent intent — just shifts payment |
| Risk prediction | AI model flags risky orders pre-shipment | Black-box; no per-signal evidence trail |
| Claimed RTO reduction | Up to 45% ([Shiprocket case studies](https://www.shiprocket.in/blog/reduce-rto-losses-in-cod-orders-with-predictive-technology/)) | RTO ≠ fraud; not all RTO is malicious |

**Critical gaps in Shiprocket's approach:**
1. No cross-account address ring detection (the Surat Meesho ring used shared addresses behind multiple personas — Shiprocket's per-order checks don't catch that pattern)
2. No address-manipulation detection (the [Signifyd-documented](https://www.signifyd.com/blog/shipping-fraud-with-address-manipulation-what-online-merchants-need-to-know/) insertion/deletion/repetition attacks bypass dedup)
3. No integration with return-claim flow (Engage stops at outbound shipping)
4. No geocoded validation — pincode-level signals miss building-level fraud

---

## 3. Google Address Validation API — capabilities & cost

### 3.1 India-specific ML model

Google launched a [dedicated India ML model in preview July 2024](https://mapsplatform.google.com/resources/blog/announcing-address-validation-api-with-machine-learning-for-india/). Direct from the announcement:

> *"Google Maps Platform's Places data and knowledge of localized address formats with a machine learning-powered prediction model for advanced parsing... handles typo corrections, street name completion, and applies locality-specific formatting."*

### 3.2 What it returns

Per [Google API docs](https://developers.google.com/maps/documentation/address-validation/overview):

| Field | What we use it for |
|---|---|
| Standardised address | Canonical form for hashing / cluster lookup |
| Per-component confidence | Each part of address scored 0–1 (street, locality, premise, sub-premise) |
| Geocode (lat/lng) | Cross-check against IP geolocation |
| Residential vs commercial | Catch returns claiming personal use to warehouse addresses |
| Verdict (CONFIRMED / UNCONFIRMED_BUT_PLAUSIBLE / UNCONFIRMED_AND_SUSPICIOUS / UNRESOLVED) | Direct fraud signal |
| Address completion flag | Was the input partial? |
| Inferred components | Did Google have to guess parts of the address? |

### 3.3 Pricing (April 2026)

Per [Google billing docs](https://developers.google.com/maps/documentation/address-validation/usage-and-billing):

| Monthly volume | Cost per request |
|---|---|
| 0 – 100,000 | **$0.017** |
| 100,000 – 500,000 | $0.0136 |
| 500,000+ | tiered further |

For a mid-size Indian D2C brand at 1,000 validations/day → **$510/month**. For hackathon scale (≤100/day during demo) → effectively free with the Google Cloud free tier.

### 3.4 Honest limitations

Per [PostGrid review](https://www.postgrid.com/google-address-validation-api/):
- Sub-premise (apartment number) validation is unreliable
- Can produce false positives on partial matches
- Restrictive storage rules — raw responses can't be cached indefinitely without consent
- Coverage outside India / US / UK is uneven

**Mitigation in our design**: treat Google's confidence as one input, not the only one. Combine with cluster check (which doesn't depend on Google) and Delhivery serviceability (which is free).

---

## 4. Carrier serviceability APIs (free fallbacks)

Beyond Google, every Indian carrier exposes a serviceability API:

| Carrier | Coverage | API |
|---|---|---|
| Delhivery | 18,000+ pincodes | [Pincode Serviceability API](https://delhivery-express-api-doc.readme.io/reference/1-pincode-servicability-api) — free with carrier account |
| Bluedart | 55,400+ locations | [Location Finder API](https://developer.dhl.com/api-reference/blue-dart-location-finder?language_content_entity=en) — free |
| Shiprocket aggregated | All Indian carriers | Postman collection: [Shiprocket API](https://www.postman.com/shiprocketdev/shiprocket-dev-s-public-workspace/collection/qu05zax/shiprocket-api) |

These return: pincode is/isn't serviceable, COD allowed yes/no, reverse-pickup allowed yes/no, expected transit time. **They don't validate address** — only the pincode. Use them as a corroborating signal alongside Google.

---

## 5. Address-manipulation detection (the fraud-ring vector)

[Signifyd's documentation](https://www.signifyd.com/blog/shipping-fraud-with-address-manipulation-what-online-merchants-need-to-know/) on a Southeast Asian fraud ring shows three manipulation patterns:

| Pattern | Example | Detection |
|---|---|---|
| **Insertion** | `6327 Oakley Rd` → `6327000000 O⏅kleeey Raod` | Levenshtein > 0.4 against Google-canonicalised form; check for non-ASCII chars in Latin-script address |
| **Deletion** | `6327 Oakley Road` → `6327 Oaklry Rod` | Same canonical form after Google standardisation but different raw input → cluster the canonical |
| **Repetition** | `Apartment 12` → `Apartment 12 12 12` | Detect repeating word/phrase in normalised form |

All three reduce to: **canonicalise via Google, hash the canonical, dedupe on the hash**. The raw address is preserved for evidence; the hash is the cluster key.

---

## 6. The 5th-signal architecture

### 6.1 Updated fusion scoring

```
fraud_score = 0.20·EXIF
            + 0.20·image_text_consistency
            + 0.20·linguistic_fingerprint
            + 0.10·behavioural
            + 0.15·address_intelligence    ← NEW
            + 0.15·carrier_signals
```

Why 0.15 weight: address intelligence is a strong **cross-account** signal but lower individual claim certainty than EXIF or image-text mismatch. The Indian fraud-ring busts ([Surat Meesho ₹5.5cr](https://www.businesstoday.in/technology/news/story/myntra-rs11-crore-refund-scam-heres-how-a-jaipur-based-gang-pulled-it-off-456827-2024-12-10), [Jaipur Myntra ₹1.1cr](https://www.businesstoday.in/technology/news/story/myntra-rs11-crore-refund-scam-heres-how-a-jaipur-based-gang-pulled-it-off-456827-2024-12-10)) all show shared addresses behind multiple personas — that's exactly the cluster signal this captures.

### 6.2 Two integration points

**a) At order placement (preventive)**
```
customer enters address →
  AddressIntelligence.validate(raw_address, customer_id)
    → Google Address Validation (region=IN)
    → Delhivery serviceability check
    → Cluster lookup (90-day window)
    → Manipulation pattern detection
  → AddressVerdict {
       score, confidence, recommendation,
       evidence: [structured signals],
       canonical_form,
       hash
     }
  → Recommendation:
       APPROVE          → ship normally
       VERIFY_WHATSAPP  → confirm via WhatsApp before ship
       REQUIRE_PREPAID  → don't allow COD
       BLOCK            → don't process order
```

**b) At return claim (detective)**
```
customer files return →
  re-canonicalise return-shipping address →
  query for matching hash in last 90 days across all accounts →
  if cluster_size ≥ 3 → cluster_signal = HIGH (escalate as ring) →
  feed into the engine's existing fusion score
```

### 6.3 Risk-signal taxonomy emitted

| Signal name | Source | Weight contribution |
|---|---|---|
| `address_unresolved` | Google verdict = UNRESOLVED | High (hard fail candidate) |
| `address_suspicious` | Google verdict = UNCONFIRMED_AND_SUSPICIOUS | High |
| `subpremise_low_confidence` | Component confidence < 0.5 on premise/sub-premise | Medium |
| `manipulation_detected` | Levenshtein > 0.4 with canonical | High |
| `cluster_size_high` | ≥3 accounts on same hash in 90d | High (auto-escalate to ring queue) |
| `tier3_high_rto_pincode` | Delhivery historic RTO data | Medium |
| `commercial_address_personal_claim` | Google residential flag = false | Medium |
| `geo_ip_mismatch` | Distance(IP_geo, address_geo) > 500km | Medium |
| `pincode_not_serviceable` | Delhivery serviceability = false | Medium |

The full list is emitted in the evidence trail for any flagged claim.

---

## 7. Database schema

```sql
CREATE TABLE address_signatures (
  id SERIAL PRIMARY KEY,
  hash TEXT NOT NULL,                    -- sha256 of canonical form
  customer_id TEXT NOT NULL,
  pincode TEXT NOT NULL,
  geocode_lat NUMERIC(9,6),
  geocode_lng NUMERIC(9,6),
  is_residential BOOLEAN,
  google_verdict TEXT,                   -- CONFIRMED / UNCONFIRMED_*
  raw_address_encrypted BYTEA,           -- encrypted at rest, DPDP-compliant
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_addr_hash_time ON address_signatures (hash, created_at DESC);
CREATE INDEX idx_addr_pincode ON address_signatures (pincode);
```

### 7.1 DPDP compliance notes

- **Hash, don't store**: cluster lookup uses the hash; raw address only retained encrypted for evidence retention (1-year minimum, 9-month for Carmack-style claims, 7-year for Large Data Fiduciaries per [DPDP Rules 2025](https://www.privacyworld.blog/2025/11/india-passes-the-digital-personal-data-protection-rules-ushering-in-a-new-digital-age-in-india/))
- **Right to erasure**: customer can request deletion → erase encrypted blob, retain hash for ring-detection (anonymous) or also delete on full opt-out
- **Purpose-limit**: stored only for fraud-investigation legitimate-interest carve-out

---

## 8. API surface

```
POST /api/v1/address/validate
{
  "address": "Flat 4B, 12 MG Road, Bengaluru, KA 560001",
  "customer_id": "cust_8821",
  "context": "order_placement" | "return_claim",
  "ip": "203.0.113.5"  // optional, for geo-IP mismatch
}

→ 200 OK
{
  "verdict": "FLAG",
  "score": 67,
  "confidence": 0.82,
  "canonical": "12 MG Road, Bengaluru, Karnataka, 560001, IN",
  "geocode": {"lat": 12.9716, "lng": 77.5946},
  "is_residential": true,
  "serviceability": {"delhivery": true, "bluedart": true, "cod_allowed": false},
  "evidence": [
    {"signal": "subpremise_low_confidence", "detail": "Flat 4B confidence 0.31"},
    {"signal": "cluster_size_high", "detail": "Address hash seen in 4 distinct customers in last 90 days: cust_2811, cust_2845, cust_2901, cust_3010"},
    {"signal": "tier3_high_rto_pincode", "detail": "Pincode 560001 historical RTO 38%"}
  ],
  "recommendation": "VERIFY_WHATSAPP",
  "ring_cluster_id": "RING-CLUSTER-7"
}
```

---

## 9. Cost model at production scale

| Volume tier | Validations/day | Validations/month | Google cost/month | Per-validation total cost |
|---|---|---|---|---|
| Hackathon demo | 100 | 3,000 | $51 (or free with $200 credit) | $0.017 |
| Small D2C | 1,000 | 30,000 | $510 | $0.017 |
| Mid D2C | 10,000 | 300,000 | $4,420 ($1,700 above 100k @ $0.0136) | $0.0147 |
| Enterprise | 100,000 | 3,000,000 | ~$40,000 | ~$0.013 |

Pass-through pricing model: charge retailer **$0.04–$0.05 per validation** (≈3× our cost) → healthy margin, still cheaper than Shiprocket Engage's bundled subscription for low-volume merchants.

---

## 10. How this beats existing solutions

| Capability | Shiprocket Engage | NoFraud / Wyllo (Shopify) | Loop / Narvar / AfterShip | **sec_logistics + Address Intel** |
|---|---|---|---|---|
| Google India ML standardisation | No | No | No | **Yes** |
| Sub-premise component validation | No | No | No | **Yes** |
| Cross-account address cluster detection | No | No | No | **Yes** |
| Manipulation-pattern detection | No | No | No | **Yes** |
| Pre-order **and** post-return validation | Pre-order only | Order-time only | None | **Both** |
| Plain-language evidence trail | No | Score+reasons | Rule-based | **Yes (per-signal evidence array)** |
| WhatsApp confirmation loop | **Yes** (their flagship) | No | No | Yes (planned, parity) |
| Carrier serviceability fallback | Yes | No | No | **Yes (Delhivery + Bluedart)** |
| India-native + DPDP-compliant by design | Yes | No | No | **Yes** |

**The pitch line:**

> *Shiprocket asks "is this address real?" once, before the parcel ships. We ask "is this address real, is it serviceable, and have we seen it before behind a different name?" — at every order, every return, and across every customer in the network.*

---

## 11. Build plan (3-hour add-on to MVP)

| Time | Task |
|---|---|
| 0:00 – 0:30 | Set up Google Cloud project, enable Address Validation API, get API key |
| 0:30 – 1:30 | Build `AddressIntelligence` service: Google client + Delhivery client + cluster check + manipulation detector |
| 1:30 – 2:00 | DB migration: `address_signatures` table with encryption-at-rest |
| 2:00 – 2:30 | Wire signal into fusion scorer (weight 0.15) |
| 2:30 – 3:00 | Frontend: live address-correction widget with risk badge (green/yellow/red) |

**Demo scenario for the pitch:**
1. Type a normal Bengaluru address → green badge, instant approve
2. Type a ring-cluster address (one of the seeded 4 addresses behind the demo fraud ring) → red badge, "RING-CLUSTER-7 escalated", whole cluster lights up on the network graph
3. Type a manipulated version of the ring address (`12 MG Road` → `12 M.G. Roadd`) → still flags because canonical form matches the cluster

---

## 12. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Google API rate limits / quota exhaustion | Fall back to Delhivery serviceability + manipulation detector + cluster check (still useful without Google) |
| Google sub-premise unreliability | Pair with Delhivery delivery-attempt history (if available); flag low-confidence to reviewer |
| DPDP non-compliance on raw address storage | Encrypt at rest, hash for cluster lookup, purpose-limit to fraud investigation |
| Customers using legitimate shared addresses (hostels, joint families) | Cluster threshold is 3+ DISTINCT customers, with similarity check on customer names/phones to allow legitimate co-residency |
| Adversarial address mutation | Use Google's canonical form (handles 90% of mutations) + Levenshtein on raw form |
| Vendor lock to Google | Abstract behind interface; can swap to MapMyIndia, HERE, or PostGrid without rewrite |

---

*This signal completes the Inconsistency Engine's six-input fusion: EXIF, image-text, linguistic, behavioural, **address intelligence**, and carrier signals. The full evidence trail produced by a flagged claim is the legally-defensible artefact that no competitor produces today.*
