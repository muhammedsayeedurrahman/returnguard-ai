"""Unified image trust verdict — combines EXIF + ELA + image_text signals
into a single classification: GENUINE / AI_GENERATED / EDITED / SUSPICIOUS / UNKNOWN.

This is presentational only — it does NOT add to the fusion score (weight=0).
The underlying signals are already counted; this surfaces the meta-verdict
prominently in the retailer report.
"""
from __future__ import annotations
from typing import Literal

ImageTrustVerdict = Literal[
    "GENUINE", "AI_GENERATED", "EDITED", "SUSPICIOUS", "UNKNOWN"
]


def derive_image_trust(evidence: list[dict]) -> dict:
    """Consume the existing evidence list and emit one image_trust evidence row.

    Returns a row in the same shape as other engine signals so it slots into
    `evidence` alongside exif/ela/etc.

    Logic (in priority order):
      - No photo at all (every image signal is SKIP) → UNKNOWN
      - ELA FAIL + EXIF MISSING (no metadata) → AI_GENERATED
      - ELA FAIL + EXIF OK/WARN/MISSING → EDITED
      - EXIF FAIL (date or GPS contradicts delivery) + ELA OK → SUSPICIOUS
      - image_text FAIL (vision says wrong product / stock photo) → SUSPICIOUS
      - ELA WARN or EXIF WARN → SUSPICIOUS
      - All clean → GENUINE
    """
    by_signal = {ev["signal"]: ev for ev in evidence}
    exif = by_signal.get("exif")
    ela = by_signal.get("ela")
    image_text = by_signal.get("image_text")

    # If no photo was provided, all three return SKIP
    all_skipped = all(
        (s is None or s.get("verdict") == "SKIP") for s in (exif, ela, image_text)
    )
    if all_skipped:
        return {
            "signal": "image_trust",
            "verdict": "UNKNOWN",
            "score": 0,
            "weight": 0.0,
            "detail": "No photo to analyse",
            "raw": {"reasons": ["no_photo"]},
        }

    exif_v = (exif or {}).get("verdict", "SKIP")
    ela_v = (ela or {}).get("verdict", "SKIP")
    img_v = (image_text or {}).get("verdict", "SKIP")
    reasons: list[str] = []

    # AI_GENERATED — ELA fires AND no EXIF metadata at all
    if ela_v == "FAIL" and exif_v in ("MISSING", "SKIP"):
        reasons.append("ELA detected re-compression artifacts")
        reasons.append("Photo has no EXIF metadata (typical of AI-generated images)")
        return {
            "signal": "image_trust",
            "verdict": "AI_GENERATED",
            "score": 0,
            "weight": 0.0,
            "detail": "Photo appears to be AI-generated or fully synthetic",
            "raw": {"reasons": reasons},
        }

    # EDITED — ELA fires regardless of EXIF presence
    if ela_v == "FAIL":
        reasons.append("ELA detected re-compression artifacts")
        if exif_v in ("OK", "WARN"):
            reasons.append("Photo has real EXIF but pixel-level edits detected")
        return {
            "signal": "image_trust",
            "verdict": "EDITED",
            "score": 0,
            "weight": 0.0,
            "detail": "Photo shows pixel-level manipulation",
            "raw": {"reasons": reasons},
        }

    # SUSPICIOUS — strong EXIF or vision contradiction
    if exif_v == "FAIL":
        reasons.append("EXIF metadata contradicts the order")
    if img_v == "FAIL":
        reasons.append("Photo content doesn't match the claimed product")
    if reasons:
        return {
            "signal": "image_trust",
            "verdict": "SUSPICIOUS",
            "score": 0,
            "weight": 0.0,
            "detail": "Photo metadata or content contradicts the claim",
            "raw": {"reasons": reasons},
        }

    # SUSPICIOUS — soft signals
    if ela_v == "WARN" or exif_v in ("WARN", "MISSING") or img_v == "WARN":
        if ela_v == "WARN":
            reasons.append("ELA shows minor anomalies")
        if exif_v == "MISSING":
            reasons.append("EXIF metadata missing")
        if exif_v == "WARN":
            reasons.append("EXIF metadata partially valid")
        return {
            "signal": "image_trust",
            "verdict": "SUSPICIOUS",
            "score": 0,
            "weight": 0.0,
            "detail": "Photo passes most checks but has minor anomalies",
            "raw": {"reasons": reasons},
        }

    # All clean
    return {
        "signal": "image_trust",
        "verdict": "GENUINE",
        "score": 0,
        "weight": 0.0,
        "detail": "Photo appears genuine — EXIF, ELA, and content checks all clean",
        "raw": {"reasons": ["EXIF clean", "ELA clean", "Content matches claim"]},
    }
