# sec_logistics — Returns Fraud: Market Research & Solution Brief

*Generated: 2026-04-29 · Sources: 30+ · Confidence: High on US/global numbers, Medium on India-specific figures*

---

## Executive Summary

E-commerce returns fraud is a **$103 billion-per-year** problem ([NRF/Appriss/Deloitte](https://www.dcvelocity.com/supply-chain/other-services/reverse-logistics/study-over-15-of-all-retail-returns-in-2024-were-fraudulent)) growing in both volume and sophistication. Roughly **15.14% of all retail returns in 2024 were fraudulent or abusive** — up from ~5% in 2018 ([Bellavix / NRF](https://www.bellavix.com/the-dirty-secret-behind-amazons-return-policy-small-sellers-are-paying-the-price/)). India is hit disproportionately hard via the cash-on-delivery channel: Myntra alone reported **₹50 crore in nationwide losses** to one fraud archetype in 2024 ([Goodreturns](https://www.goodreturns.in/news/myntra-refund-scam-2024-company-reportedly-loses-rs-50-crores-nationwide-to-false-refund-orders-1393323.html)), and **8–10% of all COD orders in India are fraudulent** ([bePragma / Razorpay](https://www.bepragma.ai/blogs/cod-fraud-in-indian-e-commerce)).

The market for fraud-detection software is real — projected to grow from **$380M (2025) to $1.5B by 2036** at 13.5% CAGR specifically for returnless-refund fraud detection ([Future Market Insights via Morningstar](https://www.morningstar.com/news/accesswire/1155525msn/returnless-refund-fraud-detection-market-to-reach-usd-15-billion-by-2036-as-ai-driven-decisioning-transforms-e-commerce-loss-prevention)) — but every existing solution treats fraud as a **single-signal scoring problem** (transaction risk, behavioral risk, device fingerprint). None of the major platforms — Signifyd, Riskified, Forter, Loop, Narvar — does **cross-modal verification of the actual claim evidence** (the photos and the text customers submit). That is the gap.

The **Inconsistency Engine** wedges into this gap by fusing four signals — EXIF forensics, image-text consistency via vision-language models, linguistic fingerprinting for ring detection, and behavioral scoring — into a single **explainable evidence trail** that fraud-ops reviewers can act on legally. The technical stack is feasible at hackathon-MVP scale on **~$0.001–$0.005 per fraud check** using Gemini 2.5 Flash-Lite ([Google](https://ai.google.dev/gemini-api/docs/pricing)). GTM is accessible: the Shopify App Store already hosts fraud apps in the **$29–$299/mo** SMB pricing band, and India's reverse-logistics platforms (Shiprocket, ClickPost, Unicommerce) are integration targets with thousands of merchants who currently lack any fraud layer.

---

## 1. Problem Definition

### 1.1 The trust break

Every online return runs on a trust contract: customer says "broken / wrong / missing," retailer issues refund (often *before* physical inspection to keep NPS high), reverse-logistics carrier moves the parcel back, warehouse inspects weeks later — if at all. This contract was designed for a world where most customers are honest and friction-cost > fraud-cost. **That math broke around 2020** as social media tutorials, Telegram refund-as-a-service channels, and AI-generated fake evidence collapsed the cost of attempted fraud to near zero.

### 1.2 Stakeholders & their pain

| Stakeholder | What they lose to fraud |
|---|---|
| Retailer | Direct refund losses; margin compression (a 2% fraud rate on a 5%-margin category halves profit) |
| Logistics provider (Delhivery, Bluedart, FedEx) | Liability for "lost" or "tampered" packages, claim reconciliation cost |
| **Honest customer** | False-positive blocks. **6× more expensive than fraud itself** — see §3.5 |
| Fraud-ops reviewer | Burnout from black-box risk scores with no actionable evidence |
| Legal / compliance | Inability to defend rejections in consumer courts (India CPA 2019, US FTC) |

### 1.3 The five fraud archetypes (working taxonomy)

1. **Empty-box / "box of rocks"** — claim package arrived empty; provide photos
2. **Damaged-on-arrival fraud** — real damage, but inflicted *after* delivery
3. **Wardrobing** — wear once, return as unused (≤80% return rate on occasionwear ([Landmark Global](https://landmarkglobal.com/eu/en/news-insights/wardrobing-bracketing-serial-returners-how-retailers-are-responding/)))
4. **Receipt / order-ID manipulation** — return a high-end version using a low-end SKU's receipt
5. **Organised return rings** — coordinated multi-account fraud using shared templates

Appriss / NRF data shows *retailers that track these signals reported a 71% increase in overstated quantity claims, 65% increase in empty-box, and 64% increase in decoy/counterfeit returns in 2024* ([Happy Returns / NRF](https://happyreturns.com/2025-happy-returns-nrf-returns-report)).

---

## 2. Market Size & Financial Impact

### 2.1 Global numbers (high confidence)

| Metric | Value | Source |
|---|---|---|
| Total US returns 2025 (forecast) | **$849.9B** (15.8% of sales) | [NRF / Happy Returns](https://nrf.com/media-center/press-releases/consumers-expected-to-return-nearly-850-billion-in-merchandise-in-2025) |
| Total US returns 2024 | $890B+ | [NRF](https://nrf.com/research/2024-consumer-returns-retail-industry) |
| **Fraud & abuse losses 2024** | **$103B** (up from $101B in 2023) | [Appriss/Deloitte via DC Velocity](https://www.dcvelocity.com/supply-chain/other-services/reverse-logistics/study-over-15-of-all-retail-returns-in-2024-were-fraudulent) |
| Fraud as % of returns 2024 | **15.14%** (vs ~5% in 2018) | [Bellavix](https://www.bellavix.com/the-dirty-secret-behind-amazons-return-policy-small-sellers-are-paying-the-price/) |
| Online return rate | 17.6%–19.3% | [NRF 2025](https://nrf.com/research/2025-retail-returns-landscape) |
| Apparel online return rate | **30–40%** (vs 8–10% in-store) | [Rewarx / RLA](https://www.rewarx.com/blogs/550-billion-fashion-returns-crisis-ecommerce) |
| Fraud YoY growth | ~20% in 2024 | [Appriss](https://apprissretail.com/blog/analyzing-retail-returns/) |

### 2.2 India-specific (medium confidence, single-source numbers flagged)

| Metric | Value | Source |
|---|---|---|
| Myntra Bengaluru complaint (Mar–Jun 2024) | ₹1.1 crore | [BusinessToday](https://www.businesstoday.in/technology/news/story/myntra-rs11-crore-refund-scam-heres-how-a-jaipur-based-gang-pulled-it-off-456827-2024-12-10) |
| **Myntra nationwide loss estimate (one archetype)** | **₹50 crore** | [Goodreturns](https://www.goodreturns.in/news/myntra-refund-scam-2024-company-reportedly-loses-rs-50-crores-nationwide-to-false-refund-orders-1393323.html) |
| Meesho Surat ring (single bust) | ₹5.5 crore | [BusinessToday](https://www.businesstoday.in/technology/news/story/myntra-rs11-crore-refund-scam-heres-how-a-jaipur-based-gang-pulled-it-off-456827-2024-12-10) |
| COD fraud rate (India) | **8–10%** | [bePragma / Razorpay](https://www.bepragma.ai/blogs/cod-fraud-in-indian-e-commerce) |
| Tier-3 / rural RTO rate | 40–45% | [bePragma / Delhivery](https://www.bepragma.ai/blogs/cod-fraud-in-indian-e-commerce) |
| Tier-1 RTO rate | 15–20% | same |
| Apparel size-mismatch as % of RTO | 41–48% | [Shiprocket](https://www.shiprocket.in/blog/minimize-cod-failures-and-returns/) |
| Serial-fraud customer segment | 4–7% of COD base | [bePragma](https://www.bepragma.ai/blogs/cod-fraud-in-indian-e-commerce) |

### 2.3 Wardrobing economics (apparel)

- **51% of Gen-Z and Millennials** admit to bracketing; **43% admit to wardrobing** ([Rewarx](https://www.rewarx.com/blogs/550-billion-fashion-returns-crisis-ecommerce)).
- **76% of shoppers** embellish return reasons to qualify for a refund they don't deserve ([NRF / Rewarx](https://www.rewarx.com/blogs/550-billion-fashion-returns-crisis-ecommerce)).
- Inditex (Zara) reported **€1.8 billion in returned-inventory cost** in a single fiscal year ([Rewarx](https://www.rewarx.com/blogs/550-billion-fashion-returns-crisis-ecommerce)).

### 2.4 Solution-market projection

The narrowly-defined **"returnless-refund fraud detection" sub-market** is forecast to grow from **$380M in 2025 to $1.5B by 2036**, a 13.5% CAGR ([Morningstar / Future Market Insights](https://www.morningstar.com/news/accesswire/1155525msn/returnless-refund-fraud-detection-market-to-reach-usd-15-billion-by-2036-as-ai-driven-decisioning-transforms-e-commerce-loss-prevention)). The broader fraud-detection-and-prevention market is on a **$65–$214B trajectory by 2030–2033** depending on definition ([MarketsandMarkets](https://www.marketsandmarkets.com/PressReleases/fraud-detection-prevention.asp), [GlobeNewswire](https://www.globenewswire.com/news-release/2024/09/12/2945414/0/en/Fraud-Detection-and-Prevention-Market-Size-is-Surpassing-USD-213-8-Billion-by-2033-Growing-at-Projected-19-5-CAGR.html)).

### 2.5 The asymmetric cost of false positives (critical for solution design)

- **False declines cost online merchants 6× more than fraud itself** — $43B/year vs $8B/year ([Anura](https://www.anura.io/blog/the-hidden-danger-high-cost-of-false-positives), CMSPI 2022).
- **33% of falsely-declined customers never shop with that brand again** ([Chargeflow](https://www.chargeflow.io/blog/fraud-false-positives)).
- Implication: any solution that maximises recall at the cost of precision destroys more value than it saves. The Inconsistency Engine must err on the side of approving and **only flag with explainable evidence**.

---

## 3. Fraud Taxonomy & 2024–2026 Trends

### 3.1 AI-generated fake damage photos (fastest-growing threat)

- **Fake AI-generated receipts jumped from 0% (2024) to 14% of all fraudulent documents (late 2025)** ([TruthScan](https://truthscan.com/blog/ai-driven-insurance-fraud-2025-trends-and-countermeasures/)).
- **Human reviewers miss ~75% of high-quality AI fakes** ([TruthScan](https://truthscan.com/blog/ai-driven-insurance-fraud-2025-trends-and-countermeasures/)).
- UK insurer **Admiral** linked a sharp 2025 rise to diffusion-model-edited bumper photos that inflated payouts by **~£13,000 per incident** ([Digital Trends / SAS](https://www.sas.com/en_gb/insights/articles/analytics/the-new-face-of-insurance-fraud.html)).
- Detection state of the art (2026): **Hive AI image detector** scores **89–94% accuracy** on Midjourney/DALL-E/Stable Diffusion ([Imagera AI 2026 review](https://imagera.ai/blog/ai-image-detector-comparison-2026)). Available as NVIDIA NIM endpoint or direct API.

### 3.2 Refund-as-a-service on Telegram / TikTok / Discord

- "Refund services" charge customers **~25% of recovered amount** as commission ([Chargebacks911](https://chargebacks911.com/refund-services/)).
- Amazon's named adversaries: **REKK, Mario Refunds, A$O, Plugged, Kanan, Wave** — collectively responsible for *millions* in losses ([CNBC](https://www.cnbc.com/2024/03/14/amazon-and-other-retailers-hit-by-refund-fraud-costing-them-billions.html), [PYMNTS](https://www.pymnts.com/news/security-and-risk/2024/refund-fraud-schemes-proliferate-apps-telegram/)).
- **REKK operator arrested in Lithuania, March 2025; €6 million in assets seized** ([DOJ WD-WA](https://www.justice.gov/usao-wdwa/pr/second-defendant-organized-refunding-fraud-ring-sentenced-30-months-prison)).
- Most-targeted brands: Amazon, Apple, Nike, eBay, Saks Fifth Avenue, Ralph Lauren ([CNBC](https://www.cnbc.com/2024/03/14/amazon-and-other-retailers-hit-by-refund-fraud-costing-them-billions.html)).

### 3.3 Organised retail crime (US, court-documented)

- **Pennsylvania defendant sentenced to 30 months** for wire fraud in online refunding scheme ([DOJ](https://www.justice.gov/usao-wdwa/pr/second-defendant-organized-refunding-fraud-ring-sentenced-30-months-prison)).
- **Northern District of California**: 7 defendants charged in counterfeit-electronics return ring ([DOJ NDCA](https://www.justice.gov/usao-ndca/pr/multiple-defendants-charged-organized-retail-theft-conspiracy-involving-returns)).
- **Santa Clara County (June 2025)**: largest retail-crime recovery since 2024 task force formed ([Santa Clara Sheriff](https://sheriff.santaclaracounty.gov/massive-retail-theft-and-fraud-ring-busted-santa-clara-county)).

### 3.4 India-specific patterns

- **Jaipur "₹1.1 crore Myntra gang"** (2024): bulk-ordered branded apparel via app, claimed missing/fake items, raised refund tickets ([BusinessToday](https://www.businesstoday.in/technology/news/story/myntra-rs11-crore-refund-scam-heres-how-a-jaipur-based-gang-pulled-it-off-456827-2024-12-10)).
- **Surat 3-person ring (Meesho)**: posed simultaneously as suppliers AND customers, ₹5.5 crore loss ([BusinessToday](https://www.businesstoday.in/technology/news/story/myntra-rs11-crore-refund-scam-heres-how-a-jaipur-based-gang-pulled-it-off-456827-2024-12-10)).
- **COD parcel scam (Storyboard18, 2025)**: fake parcels delivered to homes/offices, recipient duped into paying COD for items never ordered ([Storyboard18](https://www.storyboard18.com/trending/cash-on-delivery-scam-explained-how-fake-parcels-are-targeting-indian-homes-and-offices-90406.htm)).

### 3.5 Returnless-refund abuse (Amazon-driven secondary market)

- Amazon processed **18M+ returnless refunds in 2025–2026, a 380% increase from 2023** ([Bellavix](https://www.bellavix.com/the-dirty-secret-behind-amazons-return-policy-small-sellers-are-paying-the-price/)).
- 27% of Amazon sellers now use returnless refunds; saves $2,850/year per seller on processing — but **fraud abuse is rising in lockstep** ([Palmetto Digital](https://palmettodigitalmarketinggroup.com/amazon-returnless-refunds-2025-what-sellers-must-know/)).
- Confirms: more retailers are issuing refunds without ever inspecting the item → **the only signal left is the claim itself** (photos + text + behavior). This is *exactly* the layer the Inconsistency Engine targets.

### 3.6 EXIF anti-forensics (sophistication ramp)

- Sophisticated fraudsters strip or spoof EXIF using **ExifTool, third-party utilities, or built-in smartphone settings** ([CyberEngage](https://www.cyberengage.org/post/metadata-investigation-exiftool-a-powerful-tool-in-digital-forensics)).
- Counter-detection: cross-check `DateTimeOriginal` vs `FileModifyDate`; analyse whether EXIF *exists at all* (its absence on a "fresh phone photo" is itself a signal) ([EXIFData.org](https://exifdata.org/blog/detect-fake-exif-data-identifying-altered-photo-metadata)).
- Forensic depth: Error Level Analysis (ELA), source-camera identification from `Make`/`Model`/`SerialNumber` ([MDPI](https://www.mdpi.com/2313-433X/12/3/110), [Forensically](https://29a.ch/photo-forensics/)).

---

## 4. Competitive Landscape

### 4.1 Comparison matrix

| Vendor | Category | Returns-fraud focus | Image/vision check | Ring detection | Explainability | India presence |
|---|---|---|---|---|---|---|
| **Signifyd** | Enterprise fraud platform | Yes — Policy Abuse module | No (transaction-level only) | Network-data inference | Risk score + reasons | Limited |
| **Riskified** | Enterprise fraud platform | Yes — "Policy Protect" | No | Network-data inference | "Identity intelligence" | Limited |
| **Forter** | Enterprise fraud platform | Partial — disputes & ATO | No | Network behavioral | Decision rationale | Limited |
| **Sift** | Enterprise fraud platform | Partial | No | ML clustering | Score-based | Limited |
| **Kount (Equifax)** | Enterprise fraud platform | Partial | No | Limited | Score-based | Yes (Shopify) |
| **NoFraud / Wyllo** | SMB fraud | Yes | No | Limited | Yes | No |
| **SEON** | SMB fraud | Yes | No | Limited | "Whitebox AI" | Some |
| **Loop Returns** | Returns mgmt platform | Workflows + Custom Rules + Blocklists | No | Rule-based only | Rule-based | No |
| **Narvar Shield** | Returns mgmt platform | Yes | No | Rule-based | Rule-based | No |
| **AfterShip Returns** | Returns mgmt platform | "Wardrobing detection" | No | No | Rule-based | Yes (Shopify) |
| **ClickPost** | India RMS | "Anti-fraud detector" by behaviour | No | No | Behavioural flags | **Yes** (India-native) |
| **ReturnPrime** | India / Shopify RMS | Basic | No | No | No | **Yes** (India-native) |

Sources: [Signifyd](https://www.signifyd.com/), [Riskified Policy Protect](https://www.riskified.com/learning/policy-abuse/return-fraud/), [Loop](https://www.loopreturns.com/returns/automated-fraud-risk-detection/), [AfterShip / Cahoot](https://www.cahoot.ai/ecommerce-returns-management-which-software-is-right-for-you/), [ClickPost](https://www.clickpost.ai/returns-management-software), [ReturnPrime](https://www.returnprime.com), [Shopify App Store](https://apps.shopify.com/categories/store-management-security-fraud/all), [Capterra](https://www.capterra.com/financial-fraud-detection-software/compare/145184-136449/Riskified-vs-Signifyd).

### 4.2 What every existing player does well

- **Behavioural / network-data risk scoring** (Signifyd's chargeback guarantee model is mature)
- **Velocity rules** (return count, order value, account age)
- **Device fingerprinting + IP / geolocation**

### 4.3 The structural gap (= our wedge)

Across every vendor surveyed, **none publicly documents**:

1. **Cross-modal verification** — does the photo *agree* with the text claim? (No vendor uses a vision-language model to compare image content against claim semantics.)
2. **Linguistic ring detection** — TF-IDF / embedding similarity across claim text to surface coordinated templates. Academic work shows this approach reaches **98%+ accuracy on contract-cheating detection** ([Nature](https://www.nature.com/articles/s41599-024-03160-9)) but it is not productised in returns-fraud.
3. **EXIF + image-tampering forensics** at claim-submission time. No vendor publicly checks EXIF timestamp vs purchase date or runs ELA / AI-generation detection on uploaded photos.
4. **Plain-language evidence trail** for fraud-ops reviewers. Every vendor outputs a score; none outputs *"Reject reason: photo's EXIF DateTimeOriginal (2024-08-12) precedes order date (2024-09-03) by 22 days; photo claims water damage but VLM caption identifies cracked screen; claim text 0.87 cosine-similar to 4 other accounts in last 30 days."*

This last point is what 2025 XAI research is actively asking for — **"AI-generated investigation summaries explain in plain language why alerts were triggered"** ([Fintech Global / SEON](https://fintech.global/2025/09/30/seon-launches-ai-suite-to-boost-fraud-and-aml-detection/)) — but the returns-fraud niche has not yet caught up.

---

## 5. Proposed Solution: The Inconsistency Engine

### 5.1 Core thesis

**Fraud lives in the gap between signals, not in any single signal.** A sophisticated fraudster can defeat any one check (clean device fingerprint, normal velocity, plausible photo). They cannot easily defeat *four orthogonal* checks that must all corroborate each other — and the cost of fraud rises asymmetrically when *contradiction itself* becomes the evidence.

### 5.2 The four-signal fusion

```
fraud_score = 0.30·EXIF + 0.25·image-text + 0.25·linguistic + 0.20·behavioral
```

Asymmetric thresholds (per §2.5 false-positive economics):
- `score < 35` → **Approve** (fast lane, no friction)
- `35 ≤ score < 65` → **Flag** for human review with full evidence trail
- `score ≥ 65` → **Reject** with auto-generated legal-defensible report

### 5.3 Signal modules

#### a) EXIF forensics (weight: 0.30)
- Parse `DateTimeOriginal`, `Make`, `Model`, `Software`, `GPS*`, `SerialNumber`
- **Hard fail**: photo timestamp predates order timestamp
- **Soft fail**: missing EXIF on a claimed "fresh photo"; `Software` field shows Photoshop / generative-fill tags; timezone mismatch with delivery address
- Implementation: open-source `exifread` / `Pillow` / ExifTool wrappers — zero API cost

#### b) Image-text consistency (weight: 0.25)
- VLM (Gemini 2.5 Flash) caption + structured-extraction on the photo
- Compare extracted damage-type / item-type against the customer's free-text claim
- **Hard fail**: photo shows item A, claim describes item B
- **Soft fail**: photo shows undamaged item vs "extensive damage" claim; AI-generation probability >0.7 (Hive detector or open-source CNN)
- Cost: ~$0.002 per image at Gemini 2.5 Flash-Lite pricing ([Google](https://ai.google.dev/gemini-api/docs/pricing))

#### c) Linguistic fingerprinting (weight: 0.25)
- TF-IDF vectoriser, `ngram_range=(1,2)`, `stop_words='english'` (+ Hindi/regional stoplists for India)
- Cosine similarity against rolling window (last 90 days, all claims)
- Cluster detection: 3+ accounts with mutual similarity >0.75 = **ring escalation**
- Academic backing: 98.06% accuracy on contract-cheating detection with logistic regression + bag-of-words ([Nature](https://www.nature.com/articles/s41599-024-03160-9))
- Cost: in-process, zero API cost

#### d) Behavioral scoring (weight: 0.20)
- Return velocity (returns in 30/90 days)
- Account age vs return ratio
- Time-of-day / time-of-week anomaly (claim filed at 03:14 IST, all claims from this account file within ±10min of each other)
- Address-recycling (same shipping address across N accounts — proxy for ring formation)

### 5.4 The differentiator: **explainable evidence trail**

Every flagged claim emits a JSON evidence object → renderable as a one-page reviewer report:

```
{
  "claim_id": "RTN-2026-0429-8821",
  "decision": "REJECT",
  "score": 78,
  "evidence": [
    {"signal":"EXIF","verdict":"FAIL","detail":"DateTimeOriginal 2026-03-14 predates order 2026-04-02 by 19 days"},
    {"signal":"image_text","verdict":"FAIL","detail":"VLM caption: 'cracked screen smartphone'; claim text: 'water damage on speaker'"},
    {"signal":"linguistic","verdict":"FAIL","detail":"0.87 cosine-similarity with 4 claims from accounts A2811, A2845, A2901, A3010 in last 30 days — RING-CLUSTER-7 escalated"},
    {"signal":"behavioral","verdict":"WARN","detail":"7 returns in last 21 days; account 14 days old"}
  ],
  "recommended_action": "Reject + add to ring watchlist + report cluster to fraud-ops"
}
```

This addresses the explicit ask in 2025 XAI literature: *"AI-generated investigation summaries explain in plain language why alerts were triggered"* ([Fintech Global](https://fintech.global/2025/09/30/seon-launches-ai-suite-to-boost-fraud-and-aml-detection/)) and gives retailers a **legally defensible artefact** for India CPA-2019 / US FTC consumer disputes.

---

## 6. Solution Evaluation Against User's Six Criteria

| Criterion | Evaluation | Evidence |
|---|---|---|
| **Feasibility** | High — all four signals use proven libraries (sklearn, exiftool, Pillow) and an off-the-shelf VLM (Gemini 2.5 Flash). Buildable to MVP in 2–3 days. | §7.1, §7.2 |
| **Scalability** | High — stateless per-claim inference; horizontal scaling on serverless (Cloudflare Workers AI / AWS Lambda + Bedrock). Linguistic similarity is the only stateful component (rolling 90-day vector store) — solvable with FAISS or pgvector. | §7.3 |
| **Reliability** | High — fusion of orthogonal signals is more robust than any single model. Asymmetric thresholds protect against false positives (the dominant cost — 6× fraud per §2.5). | §2.5, §5.2 |
| **Novelty** | High — no surveyed competitor publicly does cross-modal verification + linguistic ring detection + plain-language evidence trail. The combination is the moat. | §4.3 |
| **Real-time usability** | High — total p95 budget ≤5 sec per claim (EXIF: <50ms, VLM: ~2–3s, TF-IDF: <100ms, behavioural: <50ms). Fits "before refund auto-approve" SLAs. | §7.2 |
| **Market need** | Validated — $103B problem, 15.8% return rate, growing 20% YoY, $380M→$1.5B sub-market projection at 13.5% CAGR. India: ₹50cr+ documented losses on a single archetype. | §2 |
| **Customer accessibility** | High — Shopify App Store distribution at $29–$299/mo SMB pricing; India RMS integration via Shiprocket / ClickPost / Unicommerce APIs; REST + webhook integration as table stakes. | §7.4 |

---

## 7. Technology Feasibility

### 7.1 Vision-language model pricing & latency (April 2026)

| Model | Input ($/M tokens) | Output ($/M tokens) | Notes |
|---|---|---|---|
| **Gemini 2.5 Flash-Lite** | **$0.10** | **$0.40** | Cheapest; best for high-volume fraud checks ([Google](https://ai.google.dev/gemini-api/docs/pricing)) |
| Gemini 2.5 Flash | $0.30 | $2.50 | Better reasoning for borderline cases ([Google](https://ai.google.dev/gemini-api/docs/pricing)) |
| Gemini 2.0 Flash | — | — | **Deprecated**; shut-off June 1, 2026 — do not depend on it |
| Open-source (Qwen-VL, LLaVA-Next, InternVL) | self-host | self-host | Viable for >100k checks/day to avoid per-call cost |

**Per-check cost estimate** (1 image + ~500 input tokens + ~150 output tokens with Flash-Lite): **~$0.0003–$0.001 per fraud check**. Even at Flash full pricing: **~$0.002–$0.005 per check**. At 10k checks/day, daily cost: **$3–$50**.

### 7.2 Latency budget

| Stage | Target p95 | Implementation |
|---|---|---|
| EXIF parse | <50ms | `Pillow` / `exifread` |
| AI-image detection | ~300ms | Hive API or self-hosted ONNX detector |
| VLM image-text check | 2–3s | Gemini 2.5 Flash, single call |
| TF-IDF + ring lookup | <100ms | scikit-learn + pgvector / FAISS |
| Behavioural score | <50ms | Postgres aggregate query |
| **Total p95** | **~3–4s** | Comfortably under 5s SLA |

### 7.3 Architecture

- **Stateless API service** (FastAPI / Node) — scales horizontally
- **Postgres + pgvector** for the rolling 90-day claim corpus (linguistic similarity + behavioural aggregates)
- **Object store** (S3 / R2) for claim photos with 1-year retention (per India DPDP Rules 2025 §7 below)
- **Webhook events** to retailer Slack / fraud-ops dashboard on every Flag/Reject
- **Edge caching** of VLM outputs by image hash (same photo submitted twice = 100% cache hit)

### 7.4 GTM channels (customer accessibility)

1. **Shopify App Store** ($29–$299/mo SMB tier). Existing fraud apps in this band: NoFraud/Wyllo, SEON, Kount, Riskified, Signifyd — but none at the **returns-claim-evidence** layer specifically. Pricing model: free first 100 checks/mo, then per-check or flat tier ([Wyllo Shopify listing](https://apps.shopify.com/nofraud-chargeback-prevention-and-protection)).
2. **India RMS integrations** — Shiprocket, ClickPost, Unicommerce, GoFrugal already have **anti-fraud detector** slots they admit are weak ([ClickPost](https://www.clickpost.ai/returns-management-software)). Partnership / OEM angle.
3. **Direct REST API** for mid-market and enterprise — webhook + REST is universal.
4. **D2C brand outreach** — Indian fashion D2C (Bewakoof, The Souled Store, Snitch) face wardrobing pain directly; small sales cycle.

### 7.5 Regulatory constraints (India + global)

- **India DPDP Act 2023 + Rules 2025** ([MEITY PDF](https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf), [EY guide](https://www.ey.com/en_in/insights/cybersecurity/decoding-the-digital-personal-data-protection-act-2023)):
  - Large-scale Data Fiduciary (>20M Indian users) → **7-year retention obligation** for fraud-investigation data
  - Mandatory **1-year retention** for breach-detection / investigation
  - Penalty up to **₹250 crore per breach instance**
  - Practical implication: claim photos & text must be stored encrypted-at-rest, deletable on consent withdrawal, retained for fraud-investigation purposes under the legitimate-interest carve-out
- **GDPR / CCPA**: standard data-minimisation, right-to-erasure, processing-purpose disclosure
- **No PCI scope** — we do not handle card data, only claim artefacts

---

## 8. Risk & Mitigation

| Risk | Likelihood | Mitigation |
|---|---|---|
| Fraudsters strip EXIF before upload | High (already happening) | EXIF *absence* itself is a soft signal; combine with VLM AI-generation detection |
| VLM hallucinates damage-type captions | Medium | Use structured output (JSON schema) + confidence threshold; fall back to "human review" when VLM confidence <0.6 |
| Fraud rings rotate language templates | Medium | Embedding-similarity (sentence-transformers) as upgrade path beyond TF-IDF; sliding-window re-vectorisation |
| False positives block legitimate customers | High (this is the killer risk) | Asymmetric thresholds; "approve unless ≥2 signals fire"; reviewer override loop feeds back into model |
| Vendor-lock if we depend on Gemini | Low–Medium | Abstract VLM call behind interface; can swap to Claude/GPT/open-source without rewrite |
| Data-privacy non-compliance in India | Medium | DPDP-compliant retention, consent banner at claim submission, encrypted storage, right-to-erasure flow |
| Competitor copies the architecture | Medium-High (in 12+ months) | Network effect on the linguistic-fingerprint corpus — every claim seen across customers strengthens ring detection ⇒ data moat compounds |

---

## 9. Build Plan (Hackathon → MVP)

### Phase 1: Engine (Day 1–2)
- 4 signal modules as pure functions (Python, sklearn, Pillow, Gemini SDK)
- Fusion scorer + decision tier
- Unit tests with synthetic claims
- **Deliverable**: CLI that takes (photo, claim_text, order_metadata) → decision JSON

### Phase 2: Seeded demo dataset (Day 2)
- 50 legitimate claims (varied)
- 5 EXIF-fail claims
- 5 image-text-mismatch claims
- 1 fraud ring of 4 accounts with shared linguistic template
- AI-generated photo set for the AI-detection path

### Phase 3: API + Storage (Day 2–3)
- FastAPI service with `/score` endpoint
- pgvector for claim corpus
- S3-compatible object store for photos
- Auth via API key

### Phase 4: Live demo UI (Day 3)
- React simulator: upload photo + claim → see scored evidence trail
- Threshold slider (interactive — judges can move it and see the decision change)
- Ring-cluster visualiser (force-directed graph showing the 4-account ring lighting up)

### Phase 5: Pitch (Day 3 evening)
- 90-second story: $103B problem → existing platforms miss the claim layer → demo a single fraud → demo the ring catch → ask
- Numbers to lead with: $103B, 15.14%, 6× false-positive cost, ₹50 cr (Myntra), $1.5B sub-market by 2036
- Practice 5 times. Rehearsal beats UI polish.

---

## 10. Sources

### Market sizing
1. [NRF — Consumers Expected to Return Nearly $850 Billion in 2025](https://nrf.com/media-center/press-releases/consumers-expected-to-return-nearly-850-billion-in-merchandise-in-2025)
2. [DC Velocity — 15% of all retail returns in 2024 were fraudulent](https://www.dcvelocity.com/supply-chain/other-services/reverse-logistics/study-over-15-of-all-retail-returns-in-2024-were-fraudulent)
3. [Appriss — 20% YoY surge in returns fraud](https://apprissretail.com/blog/analyzing-retail-returns/)
4. [NRF / Happy Returns 2025 Retail Returns Landscape](https://nrf.com/research/2025-retail-returns-landscape)
5. [Bellavix — small sellers paying the price for Amazon's policy](https://www.bellavix.com/the-dirty-secret-behind-amazons-return-policy-small-sellers-are-paying-the-price/)
6. [Morningstar / Future Market Insights — $1.5B by 2036 returnless-refund market](https://www.morningstar.com/news/accesswire/1155525msn/returnless-refund-fraud-detection-market-to-reach-usd-15-billion-by-2036-as-ai-driven-decisioning-transforms-e-commerce-loss-prevention)
7. [MarketsandMarkets — fraud-detection market $65B by 2030](https://www.marketsandmarkets.com/PressReleases/fraud-detection-prevention.asp)
8. [Loop Returns — state of returns fraud 2024–2025](https://www.loopreturns.com/blog/state-returns-fraud-abuse-trends-2024-2025/)

### India-specific
9. [BusinessToday — Myntra ₹1.1 cr Jaipur gang refund scam](https://www.businesstoday.in/technology/news/story/myntra-rs11-crore-refund-scam-heres-how-a-jaipur-based-gang-pulled-it-off-456827-2024-12-10)
10. [Goodreturns — Myntra ₹50 cr nationwide loss](https://www.goodreturns.in/news/myntra-refund-scam-2024-company-reportedly-loses-rs-50-crores-nationwide-to-false-refund-orders-1393323.html)
11. [bePragma / Razorpay — COD fraud in Indian e-commerce 8–10%](https://www.bepragma.ai/blogs/cod-fraud-in-indian-e-commerce)
12. [Shiprocket — minimise COD failures and returns](https://www.shiprocket.in/blog/minimize-cod-failures-and-returns/)
13. [Storyboard18 — fake parcel COD scam](https://www.storyboard18.com/trending/cash-on-delivery-scam-explained-how-fake-parcels-are-targeting-indian-homes-and-offices-90406.htm)

### Existing solutions / competitive landscape
14. [Riskified Policy Protect](https://www.riskified.com/learning/policy-abuse/return-fraud/)
15. [Signifyd platform](https://www.signifyd.com/)
16. [Capterra — Riskified vs Signifyd](https://www.capterra.com/financial-fraud-detection-software/compare/145184-136449/Riskified-vs-Signifyd)
17. [Loop Returns — fraud risk detection](https://www.loopreturns.com/returns/automated-fraud-risk-detection/)
18. [Cahoot — Loop vs Narvar vs AfterShip](https://www.cahoot.ai/ecommerce-returns-management-which-software-is-right-for-you/)
19. [ClickPost — returns management India](https://www.clickpost.ai/returns-management-software)
20. [ReturnPrime — Shopify returns](https://www.returnprime.com)
21. [Shopify App Store — fraud apps](https://apps.shopify.com/categories/store-management-security-fraud/all)

### Fraud techniques
22. [TruthScan — AI-driven insurance fraud 2025 trends](https://truthscan.com/blog/ai-driven-insurance-fraud-2025-trends-and-countermeasures/)
23. [SAS — AI-doctored images insurance fraud](https://www.sas.com/en_gb/insights/articles/analytics/the-new-face-of-insurance-fraud.html)
24. [CNBC — Refund fraud schemes on TikTok and Telegram](https://www.cnbc.com/2024/03/14/amazon-and-other-retailers-hit-by-refund-fraud-costing-them-billions.html)
25. [PYMNTS — Telegram refund fraud schemes](https://www.pymnts.com/news/security-and-risk/2024/refund-fraud-schemes-proliferate-apps-telegram/)
26. [DOJ WD-WA — REKK / refunding-ring sentencing](https://www.justice.gov/usao-wdwa/pr/second-defendant-organized-refunding-fraud-ring-sentenced-30-months-prison)
27. [DOJ NDCA — counterfeit electronics return ring](https://www.justice.gov/usao-ndca/pr/multiple-defendants-charged-organized-retail-theft-conspiracy-involving-returns)
28. [Imagera AI — 2026 image-detector accuracy comparison](https://imagera.ai/blog/ai-image-detector-comparison-2026)
29. [Hive Detect](https://hivedetect.ai/)

### Technology & forensics
30. [Google — Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
31. [SCIEPublish — forensic value of EXIF data](https://www.sciepublish.com/article/pii/567)
32. [MDPI — source camera identification from EXIF](https://www.mdpi.com/2313-433X/12/3/110)
33. [29a.ch Forensically — photo-forensics tools](https://29a.ch/photo-forensics/)
34. [Nature — linguistic fingerprint contract cheating 98% accuracy](https://www.nature.com/articles/s41599-024-03160-9)
35. [Fintech Global — SEON XAI fraud suite](https://fintech.global/2025/09/30/seon-launches-ai-suite-to-boost-fraud-and-aml-detection/)

### Regulatory
36. [MEITY — DPDP Act 2023 PDF](https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf)
37. [EY — DPDP Act compliance guide](https://www.ey.com/en_in/insights/cybersecurity/decoding-the-digital-personal-data-protection-act-2023)

### False-positive economics
38. [Anura — high cost of false positives](https://www.anura.io/blog/the-hidden-danger-high-cost-of-false-positives)
39. [Chargeflow — fraud false positives](https://www.chargeflow.io/blog/fraud-false-positives)
40. [CMSPI / ChargebackGurus](https://www.chargebackgurus.com/blog/fraud-false-positives)

### Wardrobing
41. [Rewarx — $550B fashion returns crisis](https://www.rewarx.com/blogs/550-billion-fashion-returns-crisis-ecommerce)
42. [Landmark Global — wardrobing & bracketing](https://landmarkglobal.com/eu/en/news-insights/wardrobing-bracketing-serial-returners-how-retailers-are-responding/)

---

## 11. Methodology & Confidence

- **Sources analyzed**: 40+ via WebSearch (16 queries) and 1 deep WebFetch on Appriss
- **Date range**: Prefer 2024–2026 sources; older only where canonical (NRF/Appriss baseline)
- **Confidence rating per claim type**:
  - **High**: $103B figure (multiply-corroborated NRF/Appriss/Deloitte), false-positive 6× ratio, Gemini pricing, vendor capability matrix
  - **Medium**: India-specific INR figures (most are single-source press; cross-checked across two outlets where possible), AI-receipt 0%→14% jump (single TruthScan source), 75% human-miss rate on AI fakes (single source)
  - **Acknowledged gap**: India-specific market size for fraud-detection software (no clean estimate found)

---

*This document is the canonical research basis for the sec_logistics build. Update after the hackathon with any new sources or corrected figures.*
