"""Module B — Item Not Received (INR) Abuse Detection.

Customer claims a delivered package was never received. At low volume often
genuine; at scale a pattern.

Signals:
1. OTP / GPS delivery confirmation
2. Post-delivery engagement events (app login, QR scan = received it)
3. Prior INR claim history
4. Delivery scan-to-claim timing gap (< 2h = suspicious)
5. Pincode INR rate
"""
from __future__ import annotations
import sqlite3
from datetime import datetime


def _hours_gap(ts1: str, ts2: str) -> float | None:
    try:
        d1 = datetime.fromisoformat(ts1)
        d2 = datetime.fromisoformat(ts2)
        return abs((d2 - d1).total_seconds() / 3600)
    except (ValueError, TypeError):
        return None


def score(customer_id: str, order_id: str, order: dict,
          claim_filed_at: str | None,
          conn: sqlite3.Connection) -> dict:
    weight = 0.20
    signal_score = 0
    detail_parts: list[str] = []
    raw: dict = {}

    # Signal 1 — OTP / GPS delivery confirmation
    delivery = conn.execute(
        "SELECT * FROM shipment_deliveries WHERE order_id = ? "
        "ORDER BY delivered_at DESC LIMIT 1",
        (order_id,),
    ).fetchone()

    if delivery:
        if delivery["otp_confirmed"]:
            return {
                "signal": "inr",
                "verdict": "FAIL",
                "score": 90,
                "weight": weight,
                "detail": "OTP delivery confirmation on record — receipt verified",
                "raw": {"otp_confirmed": True,
                        "delivered_at": delivery["delivered_at"]},
            }
        if delivery["gps_lat"] and delivery["gps_lng"]:
            signal_score += 30
            detail_parts.append("GPS delivery scan on record")
            raw["delivery_gps"] = [delivery["gps_lat"], delivery["gps_lng"]]

    # Signal 2 — Post-delivery engagement
    delivered_at = order.get("delivered_at", "")
    if delivered_at:
        engagement = conn.execute(
            "SELECT COUNT(*) AS c FROM engagement_events "
            "WHERE customer_id = ? AND order_id = ? AND occurred_at > ?",
            (customer_id, order_id, delivered_at),
        ).fetchone()
        eng_count = engagement["c"] if engagement else 0
        if eng_count > 0:
            signal_score += 50
            detail_parts.append(f"{eng_count} post-delivery app events recorded")
            raw["post_delivery_events"] = eng_count

    # Signal 3 — Prior INR history
    prior_inr = conn.execute(
        "SELECT COUNT(*) AS c FROM claims "
        "WHERE customer_id = ? AND reason_code = 'not_received' "
        "AND filed_at >= datetime('now', '-365 days')",
        (customer_id,),
    ).fetchone()
    prior_count = prior_inr["c"] if prior_inr else 0
    if prior_count >= 3:
        signal_score += 50
        detail_parts.append(f"{prior_count} prior INR claims in 12 months")
    elif prior_count == 2:
        signal_score += 25
    elif prior_count == 1:
        signal_score += 10
    raw["prior_inr_count"] = prior_count

    # Signal 4 — Claim timing gap
    if delivery and delivery["delivered_at"] and claim_filed_at:
        gap_hours = _hours_gap(delivery["delivered_at"], claim_filed_at)
        if gap_hours is not None:
            raw["delivery_to_claim_hours"] = round(gap_hours, 1)
            if gap_hours < 2:
                signal_score += 40
                detail_parts.append(f"INR claim filed {gap_hours:.1f}h after delivery")
            elif gap_hours < 12:
                signal_score += 15

    # Signal 5 — Pincode INR rate
    pincode = order.get("pincode", "")
    if pincode:
        pin_intel = conn.execute(
            "SELECT inr_rate FROM pincode_intelligence WHERE pincode = ?",
            (pincode,),
        ).fetchone()
        if pin_intel and pin_intel["inr_rate"] and pin_intel["inr_rate"] >= 15:
            signal_score += 20
            detail_parts.append(f"High-INR pincode ({pin_intel['inr_rate']:.0f}%)")

    signal_score = min(signal_score, 100)
    if signal_score >= 60:
        verdict = "FAIL"
    elif signal_score >= 25:
        verdict = "WARN"
    else:
        verdict = "OK"

    return {
        "signal": "inr",
        "verdict": verdict,
        "score": signal_score,
        "weight": weight,
        "detail": "; ".join(detail_parts) if detail_parts else "No INR indicators",
        "raw": raw,
    }
