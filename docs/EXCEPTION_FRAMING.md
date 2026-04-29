# Returns Fraud as Logistics Exception — Framing Brief

*Generated: 2026-04-29 · Skill: logistics-exception-management · Companion to [MARKET_RESEARCH.md](MARKET_RESEARCH.md)*

The Inconsistency Engine is not a standalone fraud detector — it is an **exception-classification layer** that sits inside the larger returns / claims workflow. Reframing the problem this way pulls in three things the original four-signal model missed:

1. **Carrier-side data** as additional fraud signals (scan gaps, POD anomalies, OS&D reports, GPS).
2. **Hard legal deadlines** that constrain when the engine must produce a verdict.
3. **Integration with the existing claims process** — the engine's verdict feeds a real workflow, it isn't the end of one.

---

## 1. Mapping fraud archetypes to the exception taxonomy

Every fraud archetype the engine is built to detect maps to a recognised carrier-side exception type. This matters because **carriers already classify, document, and retain data on these exceptions** — and that data is reachable via TMS / WMS / carrier APIs.

| Fraud archetype (sec_logistics) | Exception class | Carrier-side data we can ingest |
|---|---|---|
| Empty-box / "box of rocks" | Shortage / concealed shortage | OS&D report, weight-at-pickup vs weight-at-delivery, package dimensions, POD piece count |
| Damaged-on-arrival fraud | Concealed damage | POD signature (clean vs noted exception), 5-day concealed-damage window, packaging integrity |
| Wardrobing | Refused delivery / return-after-receipt | Original delivery POD timestamp, return label scan-in time, condition codes from inspecting carrier |
| Receipt / order-ID manipulation | Misdelivered / overage | BOL chain-of-custody, consignee signature data, declared value mismatch |
| Organised return rings | Pattern across multiple shipments / consignees | Address-cluster data, repeated POD signatures, consignee blocklist data shared across carriers |

**The engine should expose these mappings explicitly in the evidence trail.** A reviewer reading the rejection report should see *"Concealed damage claim filed Day 3 of allowable 5-day window — within compliance"* not just *"score: 78."*

---

## 2. New signal sources (carrier-side) to add to the engine

The original four-signal model (EXIF, image-text, linguistic, behavioural) is all **retailer-side / claim-submission-side**. The exception-management lens unlocks four **carrier-side signals** that current fraud platforms ignore:

### a) **POD anomaly signal**

The signed Proof of Delivery is a richer data source than retailers use. Cross-check:

- **Signature integrity**: Is the consignee signature on this return claim consistent with their prior delivery signatures? (Forged signature = fraud red flag.)
- **POD condition code**: Was the original POD signed *clean* (no damage noted at delivery)? If yes, and the customer files damage claim 4 days later, this is a **concealed damage claim** — burden of proof shifts to claimant, and packaging integrity must be evidenced.
- **POD timestamp vs claim timestamp**: Industry standard is **5 days for concealed damage**. A claim filed Day 6+ is presumptively invalid; engine should auto-flag.

Source data: carrier APIs (FedEx/UPS/DHL/Delhivery/Bluedart all expose POD images and metadata).

### b) **Scan-gap signal**

A 72-hour scan gap on a high-value shipment is itself a known fraud vector ([skill knowledge base](C:\Users\HP\.claude\skills\logistics-exception-management)). For returns specifically:

- **Outbound scan gap → "lost in transit" claim**: Customer claims package never arrived, but scan history shows clean delivery. Engine should ingest the scan trail and contradiction-detect against the claim.
- **Return scan inconsistency**: Customer claims they shipped the return, no scan-in at carrier. Either the customer never actually shipped (fraud) or the carrier lost it (real). Engine should distinguish by checking dropoff-location CCTV-window or carrier-tendered receipt.

### c) **OS&D (Over, Short & Damage) report data**

When a return arrives at the warehouse, the inspecting carrier or warehouse files an OS&D report. The report contains:

- **Piece count at receiving** vs piece count claimed
- **Visible damage at receiving** vs damage claimed by customer
- **Packaging condition** (intact, opened, retaped, etc.) — a returned box that arrived intact at the warehouse contradicts a "damaged in shipping" claim from the customer

This is **direct ground-truth** for some fraud archetypes, and most retailers don't feed it back into their fraud-detection layer. The engine should consume the OS&D report (via WMS API) and update the verdict if the warehouse evidence contradicts the customer claim.

### d) **Address-cluster signal (carrier-shared)**

Industry exception-management practice already maintains carrier blocklists for repeated fraudulent consignees. Flipping this for returns:

- **Same shipping address across N supposedly-unrelated accounts** — proxy for ring formation.
- **High refusal rate at this address** — flagged across carrier networks.
- **Address scoring services** (Loqate, Melissa, Indian: HyperVerge, Bureau ID) can confirm address validity and fraud history.

The original engine had this as part of "behavioural" (weight 0.20). Treating it as carrier-side and ingesting cross-carrier blocklists makes it stronger.

---

## 3. Updated signal weights (proposal)

The original fusion was:

```
fraud_score = 0.30·EXIF + 0.25·image-text + 0.25·linguistic + 0.20·behavioral
```

With carrier-side signals integrated, propose:

```
fraud_score = 0.20·EXIF
            + 0.20·image-text
            + 0.20·linguistic
            + 0.15·behavioral
            + 0.15·carrier_pod_anomaly
            + 0.10·os_and_d_contradiction
```

Carrier signals are **lower individual weight** because they're not always available (depends on carrier API integration), but their evidentiary value when present is high — they're ground-truth from a third party. The asymmetric-threshold logic from §2.5 of MARKET_RESEARCH.md still holds: a single carrier-side hard fail (e.g. clean POD + Day-6 concealed damage claim) should be enough to flag regardless of total score.

---

## 4. Hard deadlines the engine must respect

These constrain *when* the engine must produce a verdict. The system architecture has to honour them:

| Window | Statute / Standard | Engine implication |
|---|---|---|
| **5 days** post-delivery | Concealed damage industry standard | Auto-flag any damage claim filed Day 6+ |
| **9 months** post-delivery | Carmack Amendment (49 USC § 14706, US domestic) | Evidence must be retained ≥9 months for any potential carrier claim |
| **30 days** | Carrier acknowledgment window | Engine should track claim age and surface aging exceptions |
| **120 days** | Carrier pay-or-deny window | After Day 90, escalation logic should fire |
| **14 days** (air) | Montreal Convention damage notice | Air-freight-specific carve-out |
| **2 years** post-decline | Suit-filing window | Evidence retention horizon |
| **1 year** | India DPDP Rules 2025 — minimum breach-investigation retention | All evidence in encrypted store ≥1 year |
| **7 years** | India DPDP — Large Data Fiduciary retention | Applies if the retailer crosses 20M Indian users |

The engine is therefore **not a real-time-only system** — it is a real-time *decisioner* that must also be a **9-month evidence vault**.

---

## 5. Edge cases from the skill that the engine must handle

These are the fraud-adjacent situations where the simple "score → decide" loop fails:

1. **Concealed damage at the *end* customer, not the buyer.** B2B retailer ships to distributor → distributor ships to end consumer → end consumer claims damage. Chain-of-custody is the determinant. Engine should support **multi-hop claims** with explicit chain documentation.

2. **POD signed clean by consignee, damage claimed 2 hours later.** Without driver contemporaneous notes, concealed-damage claim is winnable for the fraudster. Engine should **escalate aggressively** when POD-clean + same-day damage claim — that pattern is a known fraud signature.

3. **Cross-shipment / overage**: customer received the right product *plus* an extra item that belongs to another customer. They claim "wrong item delivered." Detecting this requires **inventory reconciliation across orders in the same dispatch**, not a single-claim view.

4. **Broker-insolvency mid-return**: third-party reverse-logistics broker goes dark while item is in transit back. The engine's verdict ("legit return") can't be acted on if the item physically can't be recovered. Flag as **operational exception**, not fraud.

5. **Peak-season false-positive amplification**: exception rates jump 30-50% in Oct-Jan. The engine's threshold tuning must be **seasonally adjusted** or the false-positive rate will spike during retailers' most sensitive period.

6. **Consignee-caused damage with clean POD**: "the consignee's forklift dropped the pallet at unloading." This isn't *fraud* but it's a false claim against the carrier. Engine outputs should distinguish **fraud** (intent) from **liability dispute** (no intent, legitimate disagreement).

---

## 6. Severity classification — applied to fraud claims

The skill's three-axis severity matrix maps cleanly onto fraud-claim triage. Use it to decide *what to do* once the engine has scored a claim:

**Financial axis (per claim):**
- L1 (<$1k): Auto-decision; if score 65+, auto-reject with templated evidence; if 35–64, send to junior reviewer queue.
- L2 ($1k–$5k): Auto-decision allowed only if score <35 or >80; everything in between → human review.
- L3 ($5k–$25k): No auto-decision above 35; mandatory human review with engine evidence trail.
- L4 ($25k–$100k): Engine evidence + manager review + carrier claim filing simultaneously.
- L5 (>$100k or pattern + safety/regulated category): VP-level + legal + potential criminal referral.

**Customer axis (relationship):**
- Standard customer → no elevation
- Key account with SLA → +1 level (engine should have a customer-tier flag input)
- Enterprise w/ penalty clauses → +2 levels
- Customer's production/launch at risk → automatic L4+

**Time axis:**
- Standard → no elevation
- Within 48h of customer-critical event → +1
- Same-day urgent → automatic L4+

The engine should accept these axes as inputs and **gate auto-decisions** by the resulting severity. A fraud score of 75 is enough to auto-reject an L1 claim but **never** enough to auto-reject an L4 — even when the engine is confident, the cost-of-error asymmetry (an enterprise customer wrongly blocked) demands human eyes.

---

## 7. Integration touchpoints (build implications)

The engine has to live somewhere in the retailer's stack. Reachable integration surfaces:

| System | Data we read | Data we write |
|---|---|---|
| **TMS** (transportation management) | BOL, PRO numbers, scan trail, POD images, OS&D reports | Exception classifications, evidence trail |
| **WMS** (warehouse management) | Receiving inspection notes, inventory reconciliation | Verdict + recommended disposition (restock / discard / dispute) |
| **OMS / e-com platform** (Shopify, Magento, Unicommerce) | Order metadata, customer lifetime data, claim text/photos | Score + evidence webhook |
| **Returns portal** (Loop, AfterShip, Narvar, ReturnPrime) | Claim form submission | Real-time decision API |
| **Carrier APIs** (FedEx, UPS, Delhivery, Bluedart, Shadowfax) | POD, scan history, OS&D | (read-only) |
| **Fraud-ops dashboard** (custom) | All of the above | Reviewer feedback → engine retraining loop |

For the **hackathon MVP**, the realistic integration scope is: Shopify webhook (claim event) + Gemini API (VLM) + Postgres (corpus) + a synthetic carrier-API mock (no real carrier integration in 3 days). Real TMS/WMS integration is a **post-MVP** sales conversation.

---

## 8. Communication templates the engine outputs should drive

The skill provides communication patterns by severity. The engine's evidence trail should be **directly insertable** into these templates so fraud-ops doesn't re-write them. Three core ones:

### Template A — auto-rejection (L1, score ≥80, hard fail on a single signal)

```
Subject: Return claim {claim_id} — unable to process

We've reviewed your return claim and identified the following:

{auto-generated reason from evidence trail, e.g. "Photo metadata indicates
the image was taken on 2026-03-14, which is 19 days before the order date
of 2026-04-02."}

Because the evidence does not support the claim, we cannot process this
refund. If you believe this is in error, please reply with additional
documentation (original packaging photo, dated receipt, etc.) and we'll
re-review.

— {retailer} returns team
```

### Template B — manual-review handoff (engine to reviewer)

The engine produces a **one-page reviewer briefing**:
- Decision recommendation
- Evidence trail (4-6 bullets, plain language)
- Confidence
- Suggested action
- Carrier-side cross-references (POD link, scan trail link)
- Customer LTV context (defend-or-not signal)

### Template C — ring escalation (cluster detected)

When ≥3 accounts cluster above 0.75 cosine similarity, fire a separate dashboard alert with:
- Accounts in the cluster
- Total dollar exposure across accounts
- Common signals (shared address? shared linguistic template?)
- Recommended action (block all, escalate to fraud-ops manager, refer to law enforcement if >$25k)

---

## 9. KPIs (adapted from skill metrics)

The engine should expose these to the retailer's dashboard:

| Metric | Target | Red flag |
|---|---|---|
| Mean decision time (claim → verdict) | <5 sec | >30 sec |
| Auto-decision rate (no human review needed) | 60–70% | <50% or >85% |
| False-positive rate (legitimate customer wrongly flagged) | <2% | >5% |
| Fraud catch rate (true fraud caught vs total fraud) | >70% | <50% |
| Reviewer agreement rate (reviewer agrees with engine recommendation) | >85% | <70% |
| Ring-detection lead time (claims-to-cluster-detection) | <72h | >1 week |
| Evidence-trail completeness for legal disputes | 100% retained 9+ months | Any gap |

The 60–70% auto-decision target is deliberately not "as high as possible" — over-automating destroys the reviewer feedback loop the model needs for ongoing accuracy. The skill's emphasis on first-contact resolution and human judgment applies directly.

---

## 10. What this means for the Phase-1 build

Adding the exception-management lens, the **Phase-1 engine** changes shape:

- **Add** a `carrier_signals` module that consumes (mocked, in MVP) POD/scan/OS&D data
- **Add** a severity-classifier that takes (claim_value, customer_tier, time_sensitivity) → severity level → auto-decision gate
- **Add** an `evidence_pack` output that is the canonical artefact (not just a score) — this is what gets stored for 9 months and fed into reviewer templates
- **Defer** the seasonal-adjustment, multi-hop-chain-of-custody, and broker-insolvency edges to post-MVP — but **note them in the architecture** so the abstractions allow them.

The pitch story also gets stronger: instead of "we built a fraud scorer," the pitch becomes **"we built the exception-classification layer that current fraud and returns platforms don't have, with a 9-month-evidence-retention vault that makes every decision legally defensible."**

---

*This brief should be read alongside [MARKET_RESEARCH.md](MARKET_RESEARCH.md). It does not replace the four-signal architecture — it extends it by reframing fraud as a class of exception and pulling in the data sources, deadlines, and workflow primitives that come with that framing.*
