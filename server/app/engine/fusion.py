"""Inconsistency Engine — fusion scorer + decision tier mapping + ring trigger."""
from __future__ import annotations
import json
import sqlite3
import uuid
from . import exif, image_text, linguistic, address, behavioural


def _ring_check(claim_id: str, customer_id: str, evidence: list[dict],
                conn: sqlite3.Connection) -> str | None:
    """If linguistic OR address signal flagged shared customers, check for ring.
    Returns ring_cluster_id if a ring of >=3 distinct customers is detected.
    """
    candidates: set[str] = {customer_id}
    for ev in evidence:
        if ev["signal"] == "linguistic" and ev["verdict"] == "FAIL":
            candidates.update(ev["raw"].get("match_customers", []))
        if ev["signal"] == "address" and ev["verdict"] == "FAIL":
            candidates.update(ev["raw"].get("customers", []))

    if len(candidates) < 3:
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


def score_claim(claim_id: str, claim_text: str, photo_path: str | None,
                order: dict, conn: sqlite3.Connection) -> tuple[int, str, list[dict]]:
    """Run all signals, fuse, return (score, decision, evidence).

    Decision tiers:
      < 35  → APPROVE
      35-64 → BORDERLINE  (escalates to AI Evaluation Engine)
      >= 65 → REJECT
    """
    customer_id = order["customer_id"]

    evidence = [
        exif.score(photo_path, order),
        image_text.score(photo_path, claim_text, order),
        linguistic.score(claim_text, customer_id, conn),
        address.score(order, customer_id, conn),
        behavioural.score(customer_id, conn),
    ]

    raw = sum(ev["score"] * ev["weight"] for ev in evidence)
    high_signals = sum(1 for ev in evidence if ev["score"] >= 60)
    if high_signals >= 2:
        raw = min(raw * 1.25, 100.0)
    final = int(round(min(raw, 100.0)))

    ring_id = _ring_check(claim_id, customer_id, evidence, conn)
    if ring_id:
        evidence.append({
            "signal": "ring_cluster",
            "verdict": "FAIL",
            "score": 90,
            "weight": 0.0,
            "detail": f"Member of ring cluster {ring_id} — auto-frozen",
            "raw": {"ring_id": ring_id},
        })
        final = max(final, 80)

    if final < 35:
        decision = "APPROVE"
    elif final < 65:
        decision = "BORDERLINE"
    else:
        decision = "REJECT"

    return final, decision, evidence
