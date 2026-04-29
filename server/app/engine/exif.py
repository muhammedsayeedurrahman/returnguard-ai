"""Signal A1: EXIF date + GPS + device check on uploaded photo.

Extracts DateTimeOriginal, GPS coordinates, and camera Make/Model.
Compares against the order's delivery_at and shipping address (when available).

For live-camera-captured frames (capture_method='live_camera'), missing EXIF is
treated as SKIP rather than MISSING — most browsers strip metadata on canvas
toBlob(). Server timestamp is the proof in that case.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
import math
import exifread


@dataclass
class ExifData:
    date: date | None = None
    lat: float | None = None
    lng: float | None = None
    device_model: str | None = None


def _dms_to_decimal(values, ref) -> float:
    d, m, s = [v.num / v.den for v in values.values]
    dd = d + m / 60.0 + s / 3600.0
    return -dd if str(ref) in ("S", "W") else dd


def parse_exif_full(photo_path: str | None) -> ExifData:
    """Returns ExifData with date / lat / lng / device_model populated where available."""
    out = ExifData()
    if not photo_path or not Path(photo_path).exists():
        return out
    with open(photo_path, "rb") as f:
        tags = exifread.process_file(f, details=True)

    for key in ("EXIF DateTimeOriginal", "Image DateTimeOriginal",
                "EXIF DateTimeDigitized", "Image DateTime"):
        tag = tags.get(key)
        if tag:
            try:
                out.date = datetime.strptime(str(tag), "%Y:%m:%d %H:%M:%S").date()
                break
            except ValueError:
                continue

    lat_ref = tags.get("GPS GPSLatitudeRef")
    lat_val = tags.get("GPS GPSLatitude")
    lng_ref = tags.get("GPS GPSLongitudeRef")
    lng_val = tags.get("GPS GPSLongitude")
    if lat_val and lng_val and lat_ref and lng_ref:
        try:
            out.lat = _dms_to_decimal(lat_val, lat_ref)
            out.lng = _dms_to_decimal(lng_val, lng_ref)
        except (AttributeError, ZeroDivisionError, ValueError):
            pass

    model = tags.get("Image Model") or tags.get("EXIF LensModel")
    if model:
        out.device_model = str(model).strip()

    return out


def parse_exif_date(photo_path: str | None) -> date | None:
    """Backward-compat shim — older callers used this directly."""
    return parse_exif_full(photo_path).date


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def score(photo_path: str | None, order: dict,
          capture_method: str = "file_upload") -> dict:
    """Return signal verdict for the EXIF check.

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

    exif = parse_exif_full(photo_path)
    delivered = order.get("delivered_at")
    delivered_date = None
    if delivered:
        try:
            delivered_date = datetime.fromisoformat(delivered).date()
        except ValueError:
            pass

    score_value = 0
    detail_parts: list[str] = []
    raw: dict = {
        "photo_date": str(exif.date) if exif.date else None,
        "lat": exif.lat,
        "lng": exif.lng,
        "device_model": exif.device_model,
        "capture_method": capture_method,
    }

    # ─── Date check ──────────────────────────────────────────────────
    if exif.date is None:
        if capture_method == "live_camera":
            # Live-camera captures often strip EXIF — server-timestamp is authoritative
            return {
                "signal": "exif",
                "verdict": "SKIP",
                "score": 5,
                "weight": weight,
                "detail": "Live capture — EXIF not embedded by browser (expected)",
                "raw": raw,
            }
        score_value += 15
        detail_parts.append("No EXIF DateTimeOriginal — metadata stripped or non-camera image")
    elif delivered_date and exif.date < delivered_date:
        days_before = (delivered_date - exif.date).days
        score_value += 90
        detail_parts.append(
            f"Photo taken {days_before} days BEFORE delivery ({exif.date} vs {delivered_date})"
        )

    # ─── GPS distance check ──────────────────────────────────────────
    # If both photo GPS and order pincode geocode are available, check distance.
    if exif.lat is not None and exif.lng is not None:
        from .address_intel import geocode_from_pincode
        order_geo = geocode_from_pincode(order.get("pincode") or "")
        if order_geo:
            dist_km = _haversine_km(exif.lat, exif.lng, order_geo[0], order_geo[1])
            raw["gps_distance_km"] = round(dist_km, 1)
            if dist_km > 500:
                score_value += 50
                detail_parts.append(f"Photo GPS {dist_km:.0f}km from delivery pincode")
            elif dist_km > 100:
                score_value += 25
                detail_parts.append(f"Photo GPS {dist_km:.0f}km from delivery pincode")

    # ─── Verdict mapping ─────────────────────────────────────────────
    if score_value >= 60:
        verdict = "FAIL"
    elif score_value >= 25:
        verdict = "WARN"
    elif score_value > 0:
        verdict = "MISSING" if exif.date is None else "WARN"
    else:
        verdict = "OK"
        if exif.date:
            detail_parts.append(f"EXIF clean — photo dated {exif.date}")
        else:
            detail_parts.append("EXIF clean")

    return {
        "signal": "exif",
        "verdict": verdict,
        "score": min(score_value, 100),
        "weight": weight,
        "detail": "; ".join(detail_parts),
        "raw": raw,
    }
