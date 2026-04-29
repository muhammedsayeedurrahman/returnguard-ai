"""Signal B2: Address cluster detection via SHA-256 hash + 90-day lookup."""
from __future__ import annotations
import hashlib
import sqlite3
import re
from ..config import ADDRESS_HASH_PEPPER


def normalize(address: str) -> str:
    """Cheap canonicalisation — lower, collapse whitespace, strip punctuation."""
    s = (address or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def hash_address(address: str) -> str:
    canonical = normalize(address)
    return hashlib.sha256((canonical + ADDRESS_HASH_PEPPER).encode("utf-8")).hexdigest()


def score(order: dict, customer_id: str, conn: sqlite3.Connection) -> dict:
    weight = 0.20
    addr = order.get("shipping_address")
    if not addr:
        return {
            "signal": "address",
            "verdict": "SKIP",
            "score": 0,
            "weight": weight,
            "detail": "No shipping address on order",
            "raw": {},
        }

    addr_hash = hash_address(addr)
    pincode = order.get("pincode") or ""

    conn.execute(
        "INSERT INTO address_signatures (hash, customer_id, pincode) VALUES (?, ?, ?)",
        (addr_hash, customer_id, pincode),
    )
    conn.commit()

    rows = conn.execute(
        "SELECT DISTINCT customer_id FROM address_signatures "
        "WHERE hash = ? AND created_at >= datetime('now', '-90 days')",
        (addr_hash,),
    ).fetchall()
    distinct = [r["customer_id"] for r in rows]

    if len(distinct) >= 3:
        return {
            "signal": "address",
            "verdict": "FAIL",
            "score": 75,
            "weight": weight,
            "detail": f"Shipping address used by {len(distinct)} distinct customers in last 90 days — possible ring address",
            "raw": {"hash": addr_hash, "customers": distinct},
        }
    if len(distinct) == 2:
        return {
            "signal": "address",
            "verdict": "WARN",
            "score": 25,
            "weight": weight,
            "detail": f"Shipping address shared with 1 other customer",
            "raw": {"hash": addr_hash, "customers": distinct},
        }

    return {
        "signal": "address",
        "verdict": "OK",
        "score": 0,
        "weight": weight,
        "detail": "Shipping address unique to this customer",
        "raw": {"hash": addr_hash},
    }
