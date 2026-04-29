"""Signal: behavioural — return velocity + account-age check."""
from __future__ import annotations
import sqlite3


def score(customer_id: str, conn: sqlite3.Connection) -> dict:
    weight = 0.10
    row = conn.execute(
        "SELECT created_at, return_count_30d FROM customers WHERE id = ?",
        (customer_id,),
    ).fetchone()
    if not row:
        return {
            "signal": "behavioural",
            "verdict": "SKIP",
            "score": 0,
            "weight": weight,
            "detail": "Customer not found",
            "raw": {},
        }

    cnt = row["return_count_30d"] or 0
    s = 0
    detail_parts = []
    if cnt >= 5:
        s += 50
        detail_parts.append(f"{cnt} returns in last 30 days")
    elif cnt >= 3:
        s += 25
        detail_parts.append(f"{cnt} returns in last 30 days (elevated)")

    days_old = conn.execute(
        "SELECT cast(julianday('now') - julianday(created_at) as integer) AS d FROM customers WHERE id = ?",
        (customer_id,),
    ).fetchone()["d"] or 9999
    if days_old < 14:
        s += 25
        detail_parts.append(f"account only {days_old} days old")

    if s == 0:
        return {
            "signal": "behavioural",
            "verdict": "OK",
            "score": 0,
            "weight": weight,
            "detail": "Account history clean",
            "raw": {"return_count_30d": cnt, "days_old": days_old},
        }

    return {
        "signal": "behavioural",
        "verdict": "WARN" if s < 50 else "FAIL",
        "score": min(s, 100),
        "weight": weight,
        "detail": "; ".join(detail_parts),
        "raw": {"return_count_30d": cnt, "days_old": days_old},
    }
