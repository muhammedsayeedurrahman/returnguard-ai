"""ELA — Error Level Analysis for image manipulation detection.

Re-saves the image at known JPEG quality and compares the per-pixel difference
against the original. Edited regions (clone-stamp, text overlays, copy-paste)
re-compress at a different rate than untouched pixels and show as bright spots.

Reference: Krawetz, "A Picture's Worth..." (2007).

Limitations:
- High false-positive rate on scanned images and low-quality originals.
- Caps single-signal contribution at 40 to enforce the corroboration rule
  (no damage claim blocks on ELA alone).
"""
from __future__ import annotations
import io
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops

ELA_QUALITY = 75
SCALE_FACTOR = 10


def compute_ela_score(photo_path: str) -> tuple[int, dict]:
    """Returns (score 0-100, evidence_dict). >=50 likely manipulated."""
    if not Path(photo_path).exists():
        return 0, {"error": "file not found"}
    try:
        original = Image.open(photo_path).convert("RGB")
        buf = io.BytesIO()
        original.save(buf, "JPEG", quality=ELA_QUALITY)
        buf.seek(0)
        resaved = Image.open(buf).convert("RGB")

        diff = ImageChops.difference(original, resaved)
        extrema = diff.getextrema()
        max_diff = max(ex[1] for ex in extrema)
        if max_diff == 0:
            return 0, {"max_diff": 0, "mean_diff": 0.0}

        arr = np.array(diff).astype(float)
        arr = (arr / max_diff) * 255 * SCALE_FACTOR
        arr = np.clip(arr, 0, 255)
        mean_diff = float(np.mean(arr))
        score_value = min(int(mean_diff * 0.6), 100)

        return score_value, {
            "mean_diff": round(mean_diff, 2),
            "max_diff": int(max_diff),
            "ela_score": score_value,
        }
    except Exception as exc:
        return 0, {"error": str(exc)}


def score(photo_path: str | None) -> dict:
    """Standalone ELA signal — used as sub-signal of image_text or directly."""
    weight = 0.10
    if not photo_path:
        return {"signal": "ela", "verdict": "SKIP", "score": 0,
                "weight": weight, "detail": "No photo provided", "raw": {}}

    ela_score_value, evidence = compute_ela_score(photo_path)

    if ela_score_value >= 70:
        return {"signal": "ela", "verdict": "FAIL", "score": min(ela_score_value, 85),
                "weight": weight,
                "detail": f"ELA detected likely image manipulation (score {ela_score_value}/100)",
                "raw": evidence}
    if ela_score_value >= 40:
        return {"signal": "ela", "verdict": "WARN", "score": 40,
                "weight": weight,
                "detail": f"ELA detected possible re-compression artifacts (score {ela_score_value}/100)",
                "raw": evidence}
    return {"signal": "ela", "verdict": "OK", "score": 0,
            "weight": weight,
            "detail": f"ELA clean (score {ela_score_value}/100)",
            "raw": evidence}
