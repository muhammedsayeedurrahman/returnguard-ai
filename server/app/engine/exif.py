"""Signal A1: EXIF date check on uploaded photo."""
from __future__ import annotations
from datetime import datetime, date
from pathlib import Path
import exifread


def parse_exif_date(photo_path: str | None) -> date | None:
    if not photo_path or not Path(photo_path).exists():
        return None
    with open(photo_path, "rb") as f:
        tags = exifread.process_file(f, details=False)
    # Cameras write DateTimeOriginal to either ExifIFD or IFD0 depending on firmware.
    for key in ("EXIF DateTimeOriginal", "Image DateTimeOriginal",
                "EXIF DateTimeDigitized", "Image DateTime"):
        tag = tags.get(key)
        if tag:
            try:
                return datetime.strptime(str(tag), "%Y:%m:%d %H:%M:%S").date()
            except ValueError:
                continue
    return None


def score(photo_path: str | None, order: dict) -> dict:
    """Return signal verdict for the EXIF date check.

    Output schema:
      {signal, verdict, score, weight, detail, raw}
    """
    weight = 0.20
    if not photo_path:
        return {
            "signal": "exif",
            "verdict": "SKIP",
            "score": 0,
            "weight": weight,
            "detail": "No photo provided",
            "raw": {},
        }

    photo_date = parse_exif_date(photo_path)
    delivered = order.get("delivered_at")
    delivered_date = None
    if delivered:
        try:
            delivered_date = datetime.fromisoformat(delivered).date()
        except ValueError:
            pass

    if photo_date is None:
        return {
            "signal": "exif",
            "verdict": "MISSING",
            "score": 15,
            "weight": weight,
            "detail": "No EXIF DateTimeOriginal found — metadata stripped or non-camera image",
            "raw": {"photo_date": None},
        }

    if delivered_date and photo_date < delivered_date:
        days_before = (delivered_date - photo_date).days
        return {
            "signal": "exif",
            "verdict": "FAIL",
            "score": 90,
            "weight": weight,
            "detail": f"Photo taken {days_before} days BEFORE delivery ({photo_date} vs {delivered_date})",
            "raw": {"photo_date": str(photo_date), "delivered": str(delivered_date)},
        }

    return {
        "signal": "exif",
        "verdict": "OK",
        "score": 0,
        "weight": weight,
        "detail": f"EXIF clean — photo dated {photo_date}",
        "raw": {"photo_date": str(photo_date)},
    }
