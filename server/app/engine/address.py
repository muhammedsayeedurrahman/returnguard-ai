"""Signal: Address Intelligence — Google validation + cluster detection.

Two sub-checks fused into one signal:
  1. Google Address Validation API (with mock fallback) — verdict, sub-premise
     confidence, geocode, residential/commercial flag.
  2. Cluster lookup — SHA-256 hash of the *canonical* form, count distinct
     customers in the last 90 days.

Hashing the canonical form (post-Google standardisation) defeats minor input
variations: "12 MG Road" / "12, m.g. road" / "12  M G  Road" all land on the
same hash because Google normalises them to the same canonical string.
"""
from __future__ import annotations
import hashlib
import re
import sqlite3

from ..config import ADDRESS_HASH_PEPPER
from .address_intel import validate_address, AddressValidation


def _normalise(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def hash_address(address: str) -> str:
    """SHA-256 hash of the (cheaply) canonicalised address.

    Kept identical for backward-compat (seed.py, tests, ring detection in fusion).
    For new claims we prefer hashing Google's standardised canonical via
    `_canonical_hash` below, but if the validator falls back, this is the floor.
    """
    return hashlib.sha256(
        (_normalise(address) + ADDRESS_HASH_PEPPER).encode("utf-8")
    ).hexdigest()


def _canonical_hash(validation: AddressValidation, raw: str) -> str:
    """Prefer the Google-canonical form when available; fall back to raw."""
    base = validation.canonical if validation.canonical else raw
    return hash_address(base)


def score(order: dict, customer_id: str, conn: sqlite3.Connection) -> dict:
    weight = 0.20
    raw_addr = order.get("shipping_address")
    if not raw_addr:
        return {
            "signal": "address",
            "verdict": "SKIP",
            "score": 0,
            "weight": weight,
            "detail": "No shipping address on order",
            "raw": {},
        }

    # ─── Step 1: Google validation (or mock) ────────────────────────────
    validation = validate_address(raw_addr, region_code="IN")

    # ─── Step 2: cluster lookup on the canonical hash ───────────────────
    addr_hash = _canonical_hash(validation, raw_addr)
    pincode = validation.pincode or order.get("pincode") or ""

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
    distinct: list[str] = [r["customer_id"] for r in rows]

    # ─── Step 3: combine sub-signals ────────────────────────────────────
    score_value = 0
    detail_parts: list[str] = []

    # Sub-signal A: Google verdict
    if validation.verdict == "UNRESOLVED":
        score_value += 60
        detail_parts.append("Google verdict: UNRESOLVED — address could not be validated")
    elif validation.verdict == "UNCONFIRMED_AND_SUSPICIOUS":
        score_value += 40
        detail_parts.append("Google verdict: SUSPICIOUS — components inferred or unconfirmed")
    elif validation.verdict == "UNCONFIRMED_BUT_PLAUSIBLE":
        score_value += 15
        detail_parts.append("Google verdict: PLAUSIBLE but some components unconfirmed")

    # Sub-signal B: sub-premise confidence (apartment-level fakery)
    sub_conf = validation.component_confidence.get("sub_premise") or \
               validation.component_confidence.get("premise")
    if sub_conf is not None and sub_conf < 0.5:
        score_value += 25
        detail_parts.append(f"Sub-premise confidence low ({sub_conf:.2f}) — apartment may not exist")

    # Sub-signal C: cluster (the strongest fraud signal)
    cluster_signal_score = 0
    if len(distinct) >= 3:
        cluster_signal_score = 75
        detail_parts.append(
            f"Shared by {len(distinct)} distinct customers in 90 days — ring address"
        )
    elif len(distinct) == 2:
        cluster_signal_score = 25
        detail_parts.append("Shared with 1 other customer (mild)")

    # Cluster dominates when high — overlay rather than sum, to avoid
    # double-counting unresolved + cluster which would over-fire
    final_score = max(score_value, cluster_signal_score)

    # ─── Step 4: verdict mapping ────────────────────────────────────────
    if final_score >= 60:
        verdict = "FAIL"
    elif final_score >= 25:
        verdict = "WARN"
    else:
        verdict = "OK"
        if not detail_parts:
            detail_parts.append("Address validated and unique to this customer")

    return {
        "signal": "address",
        "verdict": verdict,
        "score": final_score,
        "weight": weight,
        "detail": "; ".join(detail_parts),
        "raw": {
            "hash": addr_hash,
            "customers": distinct,
            "google_verdict": validation.verdict,
            "google_canonical": validation.canonical,
            "geocode": [validation.geocode_lat, validation.geocode_lng]
                       if validation.geocode_lat else None,
            "is_residential": validation.is_residential,
            "component_confidence": validation.component_confidence,
            "used_real_api": validation.used_real_api,
        },
    }
