"""Module F — Wardrobing Detection.

Customer buys an item, uses it briefly, returns it in 'unused' condition. The
return intent was present at purchase. Detected via days-held vs category
restocking threshold + seasonal peak + repeat-category history.
"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime


WARDROBING_CATEGORIES = {"apparel", "shoes", "jewellery", "fashion", "accessories"}


def _days_held(order: dict) -> int:
    delivered = order.get("delivered_at")
    if not delivered:
        return 999
    try:
        d = datetime.fromisoformat(delivered)
        return max(0, (datetime.now() - d).days)
    except ValueError:
        return 999


def score(customer_id: str, order: dict, reason_code: str,
          conn: sqlite3.Connection) -> dict:
    weight = 0.15
    category = (order.get("product_category") or "").lower()
    value = float(order.get("value_inr") or 0)
    days_held = _days_held(order)

    baseline = conn.execute(
        "SELECT * FROM category_return_baselines WHERE category = ?",
        (category,),
    ).fetchone()

    signal_score = 0
    detail_parts: list[str] = []

    # Signal 1 — days held vs threshold
    if baseline:
        threshold = baseline["restocking_threshold_days"]
        if days_held <= threshold:
            if category in WARDROBING_CATEGORIES:
                signal_score += 60
            else:
                signal_score += 30
            detail_parts.append(
                f"Returned {days_held}d after delivery (threshold: {threshold}d)"
            )

    # Signal 2 — high-value wearable
    if baseline and category in WARDROBING_CATEGORIES:
        hv_threshold = baseline["high_value_threshold_inr"]
        if value >= hv_threshold and days_held <= 5:
            signal_score += 25
            detail_parts.append(
                f"High-value {category} (₹{value:.0f}) returned in {days_held}d"
            )

    # Signal 3 — seasonal peak
    if baseline:
        peak_months_raw = baseline["wardrobing_peak_months"] or "[]"
        try:
            peak_months = json.loads(peak_months_raw)
            current_month = str(datetime.now().month)
            if current_month in peak_months and category in WARDROBING_CATEGORIES:
                signal_score += 15
                detail_parts.append(f"Peak wardrobing month for {category}")
        except (json.JSONDecodeError, TypeError):
            pass

    # Signal 4 — repeat-category in 180 days
    prior_same_cat = conn.execute(
        "SELECT COUNT(*) AS c FROM return_history "
        "WHERE customer_id = ? AND product_category = ? "
        "AND filed_at >= datetime('now', '-180 days')",
        (customer_id, category),
    ).fetchone()
    prior_count = prior_same_cat["c"] if prior_same_cat else 0

    if prior_count >= 2:
        signal_score += 30
        detail_parts.append(f"{prior_count + 1} returns in same category in 180 days")
    elif prior_count == 1:
        signal_score += 15

    signal_score = min(signal_score, 100)
    if signal_score >= 60:
        verdict = "FAIL"
    elif signal_score >= 25:
        verdict = "WARN"
    else:
        verdict = "OK"

    return {
        "signal": "wardrobing",
        "verdict": verdict,
        "score": signal_score,
        "weight": weight,
        "detail": "; ".join(detail_parts) if detail_parts else "No wardrobing indicators",
        "raw": {
            "days_held": days_held,
            "category": category,
            "value_inr": value,
            "prior_same_category_returns": prior_count,
        },
    }


def record_return_history(customer_id: str, order_id: str, claim_id: str,
                          order: dict, wardrobing_score_value: int,
                          conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO return_history (customer_id, order_id, claim_id, "
        "product_category, order_value_inr, days_held, wardrobing_score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (customer_id, order_id, claim_id,
         order.get("product_category", ""), order.get("value_inr", 0),
         _days_held(order), wardrobing_score_value),
    )
