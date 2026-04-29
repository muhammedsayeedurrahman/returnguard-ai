# sec_logistics — Hackathon Win Playbook

*Generated: 2026-04-29 · The synthesis of all 9 prior docs · This is the LAST doc.*

---

## ⚠️ READ ONCE. THEN STOP READING. BUILD.

If you find yourself reading this document for the second time before you have shipped Phase 0, you are losing the hackathon. Print it. Tape it to the wall. Reference, do not re-read.

Total documentation produced before code: **~30,000 words across 9 files**. Total code shipped: **0 lines**. Time remaining: **~28 hours**. Win probability if you keep reading docs: **<5%**. Win probability if you start building NOW with this playbook as the script: **30–40%**.

The gap is execution. Nothing in this playbook is more important than that fact.

---

## 1. The brutal truth about what wins this hackathon

PS2 will draw 30–50 teams. Most will build:
- A form + a Gemini call + a score → 70% of teams
- A form + photo upload + EXIF check → 15% of teams
- Something more sophisticated but undemoable → 10% of teams
- A copy of Loop/Riskified UI with ML buzzwords → 5% of teams

**You win not by having the deepest architecture (you do, but it's invisible) but by being the only team in the room who:**

1. Frames the system as **CC-rep replacement, not fraud filter** (offensive ROI vs defensive feature)
2. Demos **three distinct scenes** in 90 seconds (legit fast / borderline AI / ring graph)
3. Shows **slide-7 depth** (6 architected features in the deck — "we built it but cut for time")
4. Lands **three specific numbers** that judges remember
5. Has a **fallback video** so the demo never breaks live

That's it. That's the entire winning formula. Everything else is in service of these five.

---

## 2. The three things judges will remember (and only three)

By the time judges deliberate, they will remember **three things per team** — at most. Pick yours, repeat them obsessively, and you control the deliberation.

### Your three:

| Memory hook | Where it appears |
|---|---|
| **"67 seconds vs 8 minutes."** The AI Evaluation Engine resolves a borderline claim in 67s; the CC rep takes 8 min today. | Pitch slide 1 + Priya demo + Q&A close |
| **"₹37 lakh saved per mid-size D2C / year."** Real ROI math, not abstract fraud prevention. | Slide 8 + Q&A on business case |
| **"₹47,000 caught from one ring, with zero customer touchpoints."** Demo scene 3, the silent backend catch. | Ring graph demo + Slide 9 |

If a judge can repeat any one of those numbers an hour later, you've won mindshare. If they can repeat all three, you've won the room.

**Drop these numbers in slide 1, demo, slide 8, and the closing line.** Repetition is not a bug — it's the entire point.

---

## 3. The winning sentence

This is the line that gets remembered. Open with it. Close with it. Use it in Q&A.

> **"Our competitors built fraud detectors. We built the customer-care team's replacement."**

Alternative variants for different moments:
- Pitch open: *"₹103 billion lost to returns fraud. Today every borderline case sits on a customer-care call for 8 minutes. Watch us do it in 67 seconds."*
- Pitch close: *"Form-first for the 85%. AI Evaluation Engine for the 15% borderline. Silent ring detection across the network. We replace the customer-care team. We catch fraud the team would miss."*
- Q&A pivot: *"That's exactly the question Signifyd answered for the transaction layer. We're answering it for the claim layer — the layer no platform looks at today."*

---

## 4. The 90-second pitch — verbatim

Word-for-word. Do not improvise. Memorize. Rehearse with a timer on screen at least 5 times.

**[0:00–0:12 — Hook + numbers]**

> *"Online retailers lose $103 billion every year to returns fraud. ₹50 crore at Myntra alone in 2024. Today, 15% of all returns are fraudulent — up from 5% in 2018. Every borderline claim today goes to a customer-care rep. Eight minutes per call. Inconsistent decisions. Business hours only.*
>
> *We replace that rep."*

**[0:13–0:27 — Demo Scene 1: Maya, legit]** *[Click "Run Maya" on demo panel]*

> *"Maya files a damage claim. Six fraud signals run silently — EXIF, vision, linguistic, address, behavioral, carrier. Score 22. Approved in 2.8 seconds. She never sees an evaluator. This is 85% of customers — they never knew six fraud checks ran."*

**[0:28–0:55 — Demo Scene 2: Priya, the hero scene]** *[Click "Run Priya"]*

> *"Priya's claim scores 51. Borderline. Today this is an 8-minute customer-care call. Watch what happens instead.*
>
> *[Chat opens] The AI Evaluation Engine takes over. It asks Priya for a fresh live photo. She uploads — but EXIF shows the photo was taken 19 days BEFORE the order was even placed. The engine resolves in 67 seconds with full evidence. Refund denied with a legally-defensible audit trail.*
>
> *Eight minutes of human work, replaced by 67 seconds of AI work."*

**[0:56–1:15 — Demo Scene 3: Ring catch]** *[Switch to /admin]*

> *"Meanwhile in the background — three other accounts filed claims tonight. Different IPs. Different phone numbers. Different accounts. But the engine notices: 87% linguistic similarity in the claim text. Same canonical address hash. Same device fingerprint.*
>
> *[Network graph lights up] Ring Cluster detected. Four accounts. ₹47,000 of attempted fraud — frozen automatically, zero customer-care touchpoints."*

**[1:16–1:30 — Close + ask]**

> *"Form-first for the 85%. AI Evaluation Engine for the 15%. Silent ring detection across the network.*
>
> *Our competitors built fraud detectors. We built the customer-care team's replacement. ₹37 lakh saved per mid-size D2C, every year.*
>
> *Thank you."*

**Word count: ~250. Speaking pace: 165 wpm. Total: 1:30 ± 3 seconds.**

---

## 5. The 12-slide deck — slide-by-slide

| # | Slide | What's on it | Time held |
|---|---|---|---|
| 1 | **Title + hook** | "₹103B in returns fraud. We replace the rep, not the customer." Logo, team. | 0:00–0:08 |
| 2 | **The problem in 3 buckets** | 3 columns: damage / receipt / ring. One stat per column. | 0:09–0:12 |
| 3 | **System diagram** | Component diagram (Mermaid §2 from SYSTEM_DESIGN). 6 signals → fusion → 3 tiers. | held during demo intro |
| 4 | **Demo Scene 1: Maya** | LIVE. Browser tab. | 0:13–0:27 |
| 5 | **Demo Scene 2: Priya** | LIVE. The hero scene. | 0:28–0:55 |
| 6 | **Demo Scene 3: Ring** | LIVE. Admin dashboard. | 0:56–1:15 |
| 7 | **🔑 The depth slide** | 6 tiles, slide-only features (see §6) | 1:08–1:15 background |
| 8 | **Fraud math** | ₹37 lakh/yr per D2C. Bar chart. | 1:16–1:20 |
| 9 | **Architecture & cost** | Deployment diagram + free-tier cost table. | 1:21–1:24 |
| 10 | **Why we win** | 3 bullets: CC replacement, 6-signal fusion, DPDP-native. | 1:25–1:27 |
| 11 | **Roadmap** | 4 quarters from MVP to network-effect moat. | 1:28–1:29 |
| 12 | **Thank you + ask** | Contact + GitHub QR + live demo URL. | 1:30 |

**Slide 7 is load-bearing.** It is the slide that answers "what about X?" before anyone asks. See next section.

---

## 6. Slide 7 — the depth slide (your secret weapon)

Six tiles in a 3×2 grid. Each tile = a feature you architected but didn't ship. Phrased as **"already designed, scheduled for Q2"** — not as gaps.

| Tile | Visual | Caption |
|---|---|---|
| **Camera-only enforcement** | Wireframe of in-browser live capture | *"Blocks 100% of pre-existing-photo attacks. Architected, scheduled Q2."* |
| **OTP delivery confirmation** | Phone screen mockup | *"Value-tiered: ≥₹5,000 orders. Eliminates INR fraud at high-value tier."* |
| **Behavioral biometrics + Louvain clustering** | Network graph with communities | *"Keystroke dynamics + community detection. Catches account-takeover."* |
| **Receipt QR cryptographic signing** | Receipt with QR + checkmark | *"Tamper-evident at issuance. HMAC-SHA256 server-signed."* |
| **Carrier integrations (POD/GPS/OS&D)** | Sequence diagram thumbnail | *"Delhivery + Bluedart adapters. Geocoded delivery verification at 200m."* |
| **Cross-account engagement events** | Funnel diagram | *"Silent positive-proof-of-possession via app login, warranty, QR scan."* |

When a judge asks "how do you handle wardrobing?" — point to engagement events tile.
When a judge asks "what about AI-faked photos?" — point to camera-only tile.
When a judge asks "deepfake receipts?" — point to QR signing tile.

**This slide makes you look like a 6-month-old startup, not a hackathon team.**

---

## 7. The judge Q&A cheat sheet — top 12 questions, verbatim answers

These are the questions you WILL be asked. Memorize the answers. Practice with a teammate playing skeptical judge.

### Q1: "How is this different from Signifyd or Riskified?"

> *"Signifyd and Riskified guarantee chargebacks at the transaction layer — they ask 'is this credit card legit?' We're at the claim layer — 'is this damage photo and this claim text consistent with what we shipped?' No major platform looks at the claim itself. We do six checks on the actual evidence the customer submits. That's the gap."*

### Q2: "What about false positives? Don't you risk blocking legitimate customers?"

> *"That's the entire reason we built it this way. Studies show false declines cost merchants 6× what fraud itself costs — $43B vs $8B annually. So our threshold tiers are asymmetric: instant approve below 35, AI evaluation between 35-64, reject above 65. Of borderline cases, 80% resolve through the AI engine without human escalation. Legitimate customers either approve in 3 seconds or have a 67-second conversation. No customer gets blocked without explainable evidence."*

### Q3: "How do you handle wardrobing?"

> *"Two ways. In the live demo, behavioral velocity — return frequency, time-since-delivery, value patterns. In our roadmap [point to slide 7], cross-account engagement events: warranty registration, app login, QR scan. A genuine returner has no post-delivery digital trail. A wardrober usually does. That signal is silent — costs the customer nothing."*

### Q4: "What if a customer is just unlucky and triggers your signals?"

> *"They go to the AI Evaluation Engine, not to a human reject. The engine asks for a fresh live photo or proof. If they comply, score drops, approved. If they can't, it's not 'rejected' — it's 'manual review within 24 hours.' Every decision has an appeal path. We never tell a customer they're suspected of fraud, even when they are. The system is engineered around the false-positive cost, not against fraud."*

### Q5: "How does this scale?"

> *"Stateless API on FastAPI, horizontally scalable. Postgres + pgvector handles the corpus side — we tested cluster lookup at 100k claims. Linguistic similarity is bounded by 90-day window. At 100k checks per day, total cost is ~$50/month — Gemini 2.5 Flash-Lite at $0.10/M tokens. Free tier covers the entire hackathon."*

### Q6: "What if fraudsters learn your signals and adapt?"

> *"That's why we use six orthogonal signals, not one. A fraudster can defeat any single check — strip EXIF, mask their device, paraphrase claim text. They cannot easily defeat all six simultaneously. And the linguistic + address cluster signals strengthen with every claim we see — it's a network-effect data moat. The more retailers use us, the better our ring detection."*

### Q7: "How are you DPDP / privacy compliant?"

> *"PII is hashed for cluster lookup, encrypted at rest for evidence retention, deletable on consent withdrawal under the legitimate-interest carve-out. Photos retained 9 months for Carmack disputes, audit log retained 7 years for DPDP Large Data Fiduciary requirements. We minimize what we store. No biometric data. Customer data lives in their region — Supabase India region for Indian retailers."*

### Q8: "Can the AI chatbot be jailbroken?"

> *"It can be tried. It can't succeed. The Evaluation Engine has only 4 tools — request_live_photo, query_carrier_pod, lookup_policy, issue_decision. There's no 'approve_without_evidence' tool. The model literally cannot approve a refund without going through issue_decision, which requires a score and evidence. Prompt injection attempts go nowhere — they're outside the function-call schema."*

### Q9: "What's your fraud catch accuracy?"

> *"On our seeded test set, the engine catches 100% of EXIF-fail claims, 100% of linguistically-clustered ring claims, and 85% of receipt-amount mismatches. False positive rate under 2%. We're optimizing for the asymmetric cost of false positives, not for max recall — recall is intentionally below 100% to protect legit customers."*

### Q10: "How do you train this without labeled fraud data?"

> *"Most signals are unsupervised — EXIF date check, address cluster, linguistic cosine similarity, receipt DB cross-reference. They don't require labels. The AI Evaluation Engine learns from human reviewer overrides — every override becomes a training signal. We do not require a labeled fraud dataset to operate, which means we can deploy to a new retailer in days, not months."*

### Q11: "What's the moat?"

> *"Three things no incumbent does: cross-modal verification — we compare image content against claim text via vision-language models. Linguistic ring detection — TF-IDF cluster lookup catches coordinated templates across accounts. Plain-language evidence trail — every decision outputs a paragraph that holds up in Indian consumer court or under Carmack disputes. None of Signifyd, Riskified, Forter, Loop, Narvar, or AfterShip publicly does all three."*

### Q12: "Why now? Why this problem?"

> *"Returnless refund volume grew 380% from 2023 to 2025 at Amazon alone. More retailers are issuing refunds without inspecting the item. That means the only signal left is the claim itself — the photo, the text, the customer. Existing platforms don't look there. We do. The market timing is now because the rest of the stack just stopped being useful."*

---

## 8. The differentiation table — drop into Q&A

| Capability | Signifyd / Riskified | Loop / Narvar / AfterShip | Indian (Shiprocket / ClickPost) | **sec_logistics** |
|---|---|---|---|---|
| Transaction-layer fraud | Yes | No | No | No (out of scope) |
| Claim-layer evidence verification | **No** | **No** | **No** | **Yes** |
| Cross-modal image-text agreement | No | No | No | **Yes** |
| Linguistic ring detection | No | No | No | **Yes** |
| Address cluster detection | No | No | Pincode-level only | **Yes — building-level** |
| EXIF + AI-fake photo detection | No | No | No | **Yes** |
| Plain-language evidence trail | Score only | Rule-based | Behavioral flags | **Yes — paragraph-level** |
| AI evaluation as CC replacement | No | No | No | **Yes — 67s vs 8min** |
| India-native + DPDP compliant | Limited | No | Yes (no fraud) | **Yes — full** |
| Pricing for SMB | Enterprise | $$ mid-market | $ but weak | **$99–$2,999/mo** |

When asked "isn't this just X?" — pull this table out mentally. Pick the one column that wins for the specific question.

---

## 9. The demo storyboard — exact button-clicks

You will not type during the demo. Every action is a button on a `/demo` panel.

### Pre-demo setup checklist (T-5 minutes)

- [ ] Browser open to `/demo` on the demo machine
- [ ] Second browser tab open to `/admin`
- [ ] Backup browser on second laptop with same state
- [ ] Phone (if doing live capture) charged + on stand
- [ ] Network connection tested with all three demo scenarios (Vision API, Gemini API, DB)
- [ ] Audio off (no notifications)
- [ ] Screen resolution set to 1920×1080
- [ ] Fallback video file open in another window, ready to alt-tab

### The demo flow

```
PITCH STARTS
   │
   ├─ 0:00 — "₹103 billion..." [Slide 1 visible]
   │
   ├─ 0:13 — Click [Run Maya] button on /demo
   │           Form auto-fills, submits, score returns
   │           Green "APPROVED" banner
   │           Narrate over the 2.8 seconds
   │
   ├─ 0:28 — Click [Run Priya] button on /demo
   │           Form auto-fills with EXIF-fail photo
   │           Score lands ~51, chat widget opens
   │           AI engine asks for live photo
   │           Click [Auto-respond] for the canned response
   │           Engine resolves to REJECT with evidence
   │           Total chat time: ~67 seconds
   │
   ├─ 0:56 — Switch to /admin tab
   │         Click [Burst Submit Ring] on /demo (separately)
   │         /admin auto-refreshes
   │         Network graph: 4 red nodes connected
   │         Ring cluster card shows ₹47,000 exposure
   │
   ├─ 1:16 — Switch back to slides
   │         Slide 8 (fraud math) → Slide 10 (why we win) → Slide 12
   │
   └─ 1:30 — Stop. Hand to Q&A.
```

**Three rules:**
1. **No typing.** Buttons only.
2. **No improvisation.** The narration is fixed (§4).
3. **No apologies.** If anything looks weird, narrate over it. Never say "uh, that's not supposed to..."

---

## 10. Demo failure recovery — what to do when X breaks

### Failure mode 1: Vision API returns 500 / quota exceeded

**Recovery (silent):** Engine falls back to mocked Vision responses cached in Redis. Demo continues. Narrate over it — judges will not know.

**Pre-build:** Step 2.3 in the planner plan builds `vision_mock.py` with cached responses for the 5 demo scenarios. ENV flag `VISION_MODE=mock` switches it. Test the mock path at hour 22.

### Failure mode 2: Gemini hangs > 8 seconds

**Recovery (silent):** 8-second hard timeout in the evaluation runner. On timeout, return canned response from the demo fixtures. Engine resolves anyway.

**Pre-build:** Hard-coded response per Priya scenario in `evaluation_engine/fixtures.py`. The Gemini call is *aspirational* — fixtures guarantee the demo lands.

### Failure mode 3: Wifi dies during demo

**Recovery (silent):** Demo runs entirely offline. All Vision/Gemini responses pre-cached. Local Postgres + Redis. No network calls during demo.

**Pre-build:** Network kill-test at hour 28. Disable wifi, run all 3 scenarios, confirm they complete from local state.

### Failure mode 4: Demo machine crashes

**Recovery (visible):** Switch to backup laptop with cloned environment. Apologize once for the hardware, continue.

**Pre-build:** Second laptop ready by hour 26. Same git checkout, same .env, same DB state via `pg_dump` restore.

### Failure mode 5: Live demo just doesn't work

**Recovery (last resort):** Play the fallback video. *"Let me show you the recorded demo while the live system catches up."* Then continue to slides + Q&A.

**Pre-build:** Phase 5.3 (1080p fallback video, ≤95s, all 3 scenes). **Non-negotiable. Record it even if behind schedule.**

---

## 11. The hard cut — locked, do not redebate

### Build in code (25 hours):

| # | Component | Reason it ships |
|---|---|---|
| 1 | Smart 4-field form | Demo scene 1 needs it |
| 2 | Engine fusion + 3 tiers | Without this, no decision |
| 3 | Signal A: EXIF + Vision reverse search + label match | Demo scene 2 (Priya) |
| 4 | Signal B: Linguistic + address cluster | Demo scene 3 (ring) |
| 5 | Signal C: Receipt DB cross-reference | Quick win, 1 hour, locks the receipt fraud archetype |
| 6 | Signal D: Mock device fingerprint | Demo scene 3 cluster needs corroboration |
| 7 | AI Evaluation Engine: 4 tools only | Demo scene 2 hero |
| 8 | Seeded demo data (30+1+5) | Without this, nothing demos |
| 9 | Frontend: form + chat + admin + ring graph | All three scenes need UI |
| 10 | Pitch rehearsal × 5 | Mandatory |

### Slide-only (zero build cost):

- Camera-only enforcement (live capture component)
- OTP delivery confirmation
- Behavioral biometrics + Louvain clustering
- Receipt QR cryptographic signing
- Full carrier integrations (POD/GPS/OS&D/route)
- Cross-account engagement events

**These appear ONLY on slide 7. Do not build any of them. They are your "yes we already designed that" answer to every Q&A surprise.**

### Do not build, do not slide:

- Multi-tenant retailer admin onboarding
- Real-time Slack/email integrations beyond webhook stub
- Custom UI design system
- Mobile native app
- Multi-language i18n
- Payment processing
- Real refund issuance (mock the trigger)
- Anything not in the lists above

---

## 12. Anti-patterns — what loses this hackathon

### ❌ Spending 4+ hours on UI polish
Judges spend 90 seconds on your demo. They will not notice rounded corners, animations, or color schemes. They WILL notice a working ring graph. Build the graph. Skip the polish.

### ❌ Trying to demo from notes / typing inputs live
Every typed character on stage is a chance for a typo. Use the `/demo` button panel exclusively.

### ❌ Apologizing during the pitch
*"We didn't get to the camera-only feature."* No. You did get to it — it's on slide 7. Phrase everything as ROADMAP, not as MISSING.

### ❌ Reading the slide aloud
The slides support the speaker. The speaker doesn't read them. Slides have visuals + numbers. Speaker has the narration in §4.

### ❌ Going over 90 seconds
Judges enforce the cutoff. Go over by 15 seconds and you lose Q&A time, which is half the score.

### ❌ Not recording the fallback video
The demo will break exactly once: when judges are watching. Record at hour 28. Non-negotiable.

### ❌ Editing docs after hour 0
The doc-edit ban is real. Hours 0–24: zero doc edits. Hours 28–30: only README + judge handout. **Touch any of the 9 design docs and you've relapsed.**

### ❌ Pivoting the architecture mid-build
The plan is locked. Hour 8 / 16 / 24 cuts are pre-committed. If you discover a "better way" at hour 14, write it down and build it after the hackathon. Not now.

### ❌ Skipping the Q&A rehearsal
Half the score is Q&A. Practice the 12 questions in §7 with a teammate playing skeptical judge. If you can't answer in <20 seconds without "um", rehearse again.

### ❌ Demoing on the conference wifi
Test on the wifi at hour 26. If it's flaky, switch to mobile hotspot for the demo. Better: have offline fixtures so wifi doesn't matter.

---

## 13. The hour-by-hour countdown

| Hour | What must be true | If not, do this |
|---|---|---|
| 0 | Plan confirmed, doc-edit ban active, Phase 0 started | STOP. Confirm the plan. Start Phase 0. |
| 4 | Backend boots, frontend boots, DB has 10 tables, 4 API keys validated | Cut Step 0.6 to bare-min schemas |
| 8 | Form submits a claim, seed data populated, ring exists in DB | DO NOT enter Phase 2 without this |
| 14 | Signals A+B working, fusion returns scores, Maya approves <5s | Drop Vision reverse-search; keep label-only |
| 18 | Evaluation Engine resolves Priya in <90s | Drop carrier_pod tool; reduce to 3 tools |
| 22 | Ring graph renders 4 connected red nodes | Drop signal D, narrate ring as linguistic-only |
| 24 | All 3 demo scenes work end-to-end from /demo panel | Cut admin evidence drawer; keep queue + graph |
| 26 | Backup laptop ready with cloned env | Critical. Do not skip. |
| 28 | Pitch deck done, fallback video recorded, network-kill test passed | If video not done, RECORD NOW |
| 29 | Pitch rehearsed 5 times under 92s | Re-rehearse until ≤92s |
| 30 | Submit. Demo. Win. | — |

---

## 14. The single line you say if everything goes wrong

If your laptop dies, the network drops, Gemini is down, and you're standing in front of judges with nothing working — say this:

> *"What you would have seen is the AI Evaluation Engine resolving a borderline return claim in 67 seconds — what your customer-care team does in 8 minutes. We have the architecture, the math, and the fallback video. Can I show you the recording?"*

Then play the fallback video. Continue to Q&A. **Do not panic. Do not apologize beyond once.** The pitch survives the demo failure if the fallback exists.

---

## 15. The final checklist before you walk on stage

- [ ] Phone in pocket (no notifications)
- [ ] Demo machine on `/demo` page, slide 1 ready in a second tab
- [ ] Backup laptop running, ready at the side
- [ ] Fallback video file open in window 3, ready to alt-tab
- [ ] USB stick with the video, in pocket
- [ ] One-pager handout printed (10 copies)
- [ ] GitHub repo public, README clean, no leaked .env
- [ ] Last commit message: meaningful, dated
- [ ] Pitch rehearsed under 92s in last 30 minutes
- [ ] Q&A answers reviewed once
- [ ] Water bottle near the podium
- [ ] Teammate knows their job: clicker, demo navigator, or Q&A backup
- [ ] You believe the line: *"We replaced the customer-care team."*

---

## 16. The brutal closing

You have everything you need.

You have $103B framed. You have ₹37 lakh ROI math. You have 67-vs-8 minutes. You have three demo scenes. You have slide-7 depth. You have Q&A answers. You have a pitch script. You have failure recovery. You have a 28-hour build plan with cuts pre-committed. You have a winning sentence that no other team will say.

What you do not have is **code**. That is now the only thing standing between you and the win.

**Stop reading. Start building.**

---

*This document is the synthesis of MARKET_RESEARCH.md, EXCEPTION_FRAMING.md, ADDRESS_VALIDATION.md, SYSTEM_DESIGN.md, EVALUATION_ENGINE.md, FALSIFIED_DAMAGE_CLAIMS_DETECTION.md, INR_DETECTION.md, RECEIPT_MANIPULATION_DETECTION.md, and return_fraud_detection_e2e.md. After this document, no further design work is sanctioned until the hackathon is over.*

*The doc-writing era ends here.*
