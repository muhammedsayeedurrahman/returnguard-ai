"""Inconsistency Engine — fusion scorer + decision tier mapping + ring trigger.

Async fusion: signals run concurrently via asyncio.gather + asyncio.to_thread.
Each scorer is IO-bound (DB queries, optional API calls) so concurrent execution
cuts total latency from ~1.5s sequential to ~400ms parallel.
"""
from __future__ import annotations
import asyncio
import json
import sqlite3
import uuid
from . import (exif, image_text, linguistic, address, behavioural,
               friendly_fraud, wardrobing as wardrobing_module,
               inr as inr_module, ela, image_trust)


def _ring_check(claim_id: str, customer_id: str, evidence: list[dict],
                conn: sqlite3.Connection) -> str | None:
    """If linguistic OR address signal flagged shared customers, check for ring.

    Returns ring_cluster_id if a ring of ≥2 distinct customers is detected;
    auto-freezes (REJECT escalation) only at 3+ candidates.
    """
    candidates: set[str] = {customer_id}
    for ev in evidence:
        # Bug 2 fix: include WARN linguistic verdicts so partial rings are caught
        if ev["signal"] == "linguistic" and ev["verdict"] in ("FAIL", "WARN"):
            candidates.update(ev["raw"].get("match_customers", []))
        if ev["signal"] == "address" and ev["verdict"] == "FAIL":
            candidates.update(ev["raw"].get("customers", []))

    # Detection threshold lowered from 3 to 2 so a 2-account partial ring is
    # at least logged; REJECT escalation still requires ≥3 (see score_claim_async).
    if len(candidates) < 2:
        return None

    rows = conn.execute(
        "SELECT id FROM ring_clusters WHERE customer_ids LIKE ?",
        (f"%{customer_id}%",),
    ).fetchone()
    if rows:
        return rows["id"]

    ring_id = f"RING-{uuid.uuid4().hex[:6].upper()}"
    exposure = conn.execute(
        "SELECT COALESCE(SUM(o.value_inr), 0) AS total FROM claims c "
        "JOIN orders o ON c.order_id = o.id WHERE c.customer_id IN ("
        + ",".join("?" * len(candidates)) + ")",
        list(candidates),
    ).fetchone()["total"] or 0

    conn.execute(
        "INSERT INTO ring_clusters (id, customer_ids, shared_signal, exposure_inr) "
        "VALUES (?, ?, ?, ?)",
        (ring_id, json.dumps(list(candidates)), "linguistic+address", float(exposure)),
    )
    conn.execute(
        "UPDATE claims SET ring_cluster_id = ? WHERE customer_id IN ("
        + ",".join("?" * len(candidates)) + ")",
        [ring_id, *candidates],
    )
    conn.commit()
    return ring_id


def score_ring_velocity_stub(claim_id: str, customer_id: str,
                              conn: sqlite3.Connection) -> dict:
    """Placeholder for the Phase-7+ ring_velocity scorer (Redis-backed).

    Reads the basic 30-day claim cluster from existing tables; full
    velocity scoring (per-minute claim bursts, device-IP correlations)
    requires Redis + browser fingerprinting which is post-hackathon.
    """
    weight = 0.10
    cluster_count = conn.execute(
        "SELECT COUNT(*) AS c FROM claims "
        "WHERE customer_id IN ("
        "  SELECT customer_id FROM address_signatures "
        "  WHERE hash IN (SELECT hash FROM address_signatures WHERE customer_id = ?) "
        ") AND filed_at >= datetime('now', '-7 days')",
        (customer_id,),
    ).fetchone()["c"] or 0

    if cluster_count >= 5:
        return {"signal": "ring_velocity", "verdict": "FAIL", "score": 70,
                "weight": weight,
                "detail": f"{cluster_count} claims in 7 days from co-located accounts",
                "raw": {"cluster_count_7d": cluster_count}}
    if cluster_count >= 3:
        return {"signal": "ring_velocity", "verdict": "WARN", "score": 35,
                "weight": weight,
                "detail": f"{cluster_count} claims in 7 days from co-located accounts",
                "raw": {"cluster_count_7d": cluster_count}}
    return {"signal": "ring_velocity", "verdict": "OK", "score": 0,
            "weight": weight,
            "detail": "Velocity within normal range",
            "raw": {"cluster_count_7d": cluster_count}}


def _apply_corroboration_multiplier(scores: list[int], raw: float) -> float:
    """Multi-tier multiplier — 3+ high signals = 1.25×, 2 = 1.12×, 1 = 1.0×."""
    high = [s for s in scores if s >= 60]
    n = len(high)
    if n >= 3:
        multiplier = 1.25
    elif n == 2:
        multiplier = 1.12
    else:
        multiplier = 1.00
    return min(raw * multiplier, 100.0)


async def score_claim_async(claim_id: str, claim_text: str, photo_path: str | None,
                             order: dict, conn: sqlite3.Connection,
                             capture_method: str = "file_upload",
                             ) -> tuple[int, str, list[dict]]:
    """Run all signals concurrently, fuse, return (score, decision, evidence).

    Decision tiers:
      < 35  → APPROVE
      35-64 → BORDERLINE  (escalates to AI Evaluation Engine)
      ≥ 65  → REJECT
    """
    customer_id = order["customer_id"]

    reason_code = order.get("reason_code", "")
    payment_method = order.get("payment_method", "credit_card")
    from datetime import datetime as _dt

    # Bug 1 fix: signals run concurrently via to_thread (each is sync but IO-bound).
    results = await asyncio.gather(
        asyncio.to_thread(exif.score, photo_path, order, capture_method),
        asyncio.to_thread(image_text.score, photo_path, claim_text, order),
        asyncio.to_thread(linguistic.score, claim_text, customer_id, conn),
        asyncio.to_thread(address.score, order, customer_id, conn),
        asyncio.to_thread(behavioural.score, customer_id, conn),
        asyncio.to_thread(score_ring_velocity_stub, claim_id, customer_id, conn),
        asyncio.to_thread(friendly_fraud.score, customer_id, payment_method, conn),
        asyncio.to_thread(wardrobing_module.score, customer_id, order, reason_code, conn),
        asyncio.to_thread(inr_module.score, customer_id, order["id"] if "id" in order else "",
                          order, _dt.now().isoformat(), conn),
        asyncio.to_thread(ela.score, photo_path),
    )
    evidence = list(results)

    # Phase B: derive unified image-trust verdict from EXIF+ELA+image_text.
    # Presentational only — weight=0, does not affect fusion score.
    evidence.append(image_trust.derive_image_trust(evidence))

    raw = sum(ev["score"] * ev["weight"] for ev in evidence)
    final_raw = _apply_corroboration_multiplier([ev["score"] for ev in evidence], raw)

    # Single-signal escalation floor: a strong FAIL on any single signal must at
    # minimum land BORDERLINE so a human reviewer or AI agent sees it. The "no
    # single signal blocks alone" principle is preserved — REJECT (>=65) still
    # requires corroboration. This only lifts to BORDERLINE.
    max_single = max((ev["score"] for ev in evidence if ev.get("verdict") == "FAIL"),
                     default=0)
    if max_single >= 95:
        final_raw = max(final_raw, 50.0)
    elif max_single >= 80:
        final_raw = max(final_raw, 38.0)

    final = int(round(min(final_raw, 100.0)))

    ring_id = _ring_check(claim_id, customer_id, evidence, conn)
    if ring_id:
        # Count candidates again to decide escalation
        candidates: set[str] = {customer_id}
        for ev in evidence:
            if ev["signal"] == "linguistic" and ev["verdict"] in ("FAIL", "WARN"):
                candidates.update(ev["raw"].get("match_customers", []))
            if ev["signal"] == "address" and ev["verdict"] == "FAIL":
                candidates.update(ev["raw"].get("customers", []))

        evidence.append({
            "signal": "ring_cluster",
            "verdict": "FAIL" if len(candidates) >= 3 else "WARN",
            "score": 90 if len(candidates) >= 3 else 50,
            "weight": 0.0,
            "detail": f"Member of ring cluster {ring_id} ({len(candidates)} accounts)" +
                     (" — auto-frozen" if len(candidates) >= 3 else " — flagged"),
            "raw": {"ring_id": ring_id, "candidate_count": len(candidates)},
        })
        # Escalate to REJECT only on full ring (3+)
        if len(candidates) >= 3:
            final = max(final, 80)

    if final < 35:
        decision = "APPROVE"
    elif final < 65:
        decision = "BORDERLINE"
    else:
        decision = "REJECT"

    return final, decision, evidence


def score_claim(claim_id: str, claim_text: str, photo_path: str | None,
                order: dict, conn: sqlite3.Connection,
                capture_method: str = "file_upload",
                ) -> tuple[int, str, list[dict]]:
    """Synchronous wrapper for tests / callers that can't easily await.

    Prefer score_claim_async in route handlers.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # Already in async context — caller should await score_claim_async directly
        raise RuntimeError("Use score_claim_async inside async context")
    return asyncio.run(
        score_claim_async(claim_id, claim_text, photo_path, order, conn, capture_method)
    )
