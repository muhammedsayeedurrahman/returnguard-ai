"""Module E — Friendly Fraud (Chargeback Abuse) Detection.

Customer receives goods, keeps them, then files a chargeback with their bank
claiming the transaction was unauthorised. Retailer loses both goods and money.

Signals:
1. Prior chargeback count (highest weight)
2. Payment method risk profile (BNPL > credit-card > UPI > COD-zero)
3. Risk tier from `payment_risk_profiles` (BLOCKED auto-rejects)
4. Claim frequency in the last 180 days
"""
from __future__ import annotations
import sqlite3

PAYMENT_METHOD_RISK = {
    "cod":          0,   # No chargeback possible
    "upi":         10,
    "netbanking":  15,
    "debit_card":  20,
    "wallet":      20,
    "credit_card": 40,
    "bnpl":        60,
}


def get_risk_tier(chargeback_count: int) -> str:
    if chargeback_count == 0:
        return "LOW"
    if chargeback_count == 1:
        return "MEDIUM"
    if chargeback_count <= 3:
        return "HIGH"
    return "BLOCKED"


def score(customer_id: str, payment_method: str,
          conn: sqlite3.Connection) -> dict:
    weight = 0.15
    row = conn.execute(
        "SELECT * FROM payment_risk_profiles WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()

    chargeback_count = row["chargeback_count"] if row else 0
    claim_count_180d = row["claim_count_180d"] if row else 0
    risk_tier = row["risk_tier"] if row else "LOW"

    signal_score = 0
    detail_parts: list[str] = []

    if chargeback_count >= 3:
        signal_score += 80
        detail_parts.append(f"{chargeback_count} prior chargebacks")
    elif chargeback_count == 2:
        signal_score += 50
        detail_parts.append(f"{chargeback_count} prior chargebacks")
    elif chargeback_count == 1:
        signal_score += 25
        detail_parts.append("1 prior chargeback")

    pm_risk = PAYMENT_METHOD_RISK.get((payment_method or "").lower(), 20)
    if pm_risk >= 40:
        signal_score += pm_risk // 2
        detail_parts.append(f"High-risk payment method: {payment_method}")

    if claim_count_180d >= 5:
        signal_score += 30
        detail_parts.append(f"{claim_count_180d} claims in 180 days")

    if risk_tier == "BLOCKED":
        return {
            "signal": "friendly_fraud", "verdict": "FAIL", "score": 95,
            "weight": weight,
            "detail": f"Customer in BLOCKED tier ({chargeback_count} prior chargebacks)",
            "raw": {"risk_tier": risk_tier, "chargeback_count": chargeback_count},
        }

    signal_score = min(signal_score, 100)
    if signal_score >= 60:
        verdict = "FAIL"
    elif signal_score >= 25:
        verdict = "WARN"
    else:
        verdict = "OK"

    return {
        "signal": "friendly_fraud",
        "verdict": verdict,
        "score": signal_score,
        "weight": weight,
        "detail": "; ".join(detail_parts) if detail_parts else "No prior chargeback history",
        "raw": {
            "chargeback_count": chargeback_count,
            "risk_tier": risk_tier,
            "payment_method_risk": pm_risk,
            "claim_count_180d": claim_count_180d,
        },
    }


def record_chargeback(customer_id: str, order_id: str, amount_inr: float,
                      payment_method: str, reason: str,
                      conn: sqlite3.Connection) -> dict:
    """Insert chargeback event + update payment risk profile + tier."""
    conn.execute(
        "INSERT INTO chargeback_events "
        "(customer_id, order_id, payment_method, amount_inr, chargeback_reason) "
        "VALUES (?, ?, ?, ?, ?)",
        (customer_id, order_id, payment_method, amount_inr, reason),
    )
    existing = conn.execute(
        "SELECT chargeback_count, largest_chargeback_inr FROM payment_risk_profiles "
        "WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()

    new_count = (existing["chargeback_count"] + 1) if existing else 1
    largest = max(existing["largest_chargeback_inr"] if existing else 0, amount_inr)
    new_tier = get_risk_tier(new_count)

    if existing:
        conn.execute(
            "UPDATE payment_risk_profiles SET "
            "  chargeback_count = ?, risk_tier = ?, "
            "  last_chargeback_at = datetime('now'), "
            "  largest_chargeback_inr = ? "
            "WHERE customer_id = ?",
            (new_count, new_tier, largest, customer_id),
        )
    else:
        conn.execute(
            "INSERT INTO payment_risk_profiles "
            "(customer_id, chargeback_count, risk_tier, last_chargeback_at, "
            " largest_chargeback_inr) "
            "VALUES (?, ?, ?, datetime('now'), ?)",
            (customer_id, new_count, new_tier, largest),
        )
    conn.commit()
    return {"chargeback_count": new_count, "risk_tier": new_tier}
