"""Google Address Validation API client (with mock fallback).

Real API: https://addressvalidation.googleapis.com/v1:validateAddress
- Free tier: $200/mo credit (~11,700 calls at $0.017/call)
- India ML model launched preview July 2024 — auto-applied for IN region
- Returns: standardised address, per-component confidence, geocode,
  residential/commercial flag, granularity, verdict

To enable real path:
  1. Create Google Cloud project: https://console.cloud.google.com
  2. Enable "Address Validation API" in APIs & Services
  3. Create API key in Credentials
  4. Paste in .env: GOOGLE_MAPS_API_KEY=AIza...
  5. Set USE_MOCK_ADDRESS=false
  6. Restart uvicorn

Mock fallback runs identical signal extraction from filename hints / address
patterns so the demo works offline. See `_mock_validate` below.
"""
from __future__ import annotations
import re
import json
from dataclasses import dataclass, field, asdict
from typing import Any
import httpx

from ..config import GOOGLE_MAPS_API_KEY, USE_MOCK_ADDRESS

API_URL = "https://addressvalidation.googleapis.com/v1:validateAddress"
TIMEOUT_SECONDS = 6.0


@dataclass
class AddressValidation:
    """Normalised result from Google API or mock — same shape either way."""
    verdict: str  # CONFIRMED | UNCONFIRMED_BUT_PLAUSIBLE | UNCONFIRMED_AND_SUSPICIOUS | UNRESOLVED
    canonical: str  # standardised address string
    pincode: str
    geocode_lat: float | None = None
    geocode_lng: float | None = None
    is_residential: bool | None = None
    component_confidence: dict[str, float] = field(default_factory=dict)
    inferred_components: list[str] = field(default_factory=list)
    used_real_api: bool = False
    raw_excerpt: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────
# Real API path
# ─────────────────────────────────────────────────────────────────────────

def _real_validate(raw_address: str, region_code: str = "IN") -> AddressValidation:
    """Call Google Address Validation API. Raises on failure."""
    payload = {
        "address": {
            "regionCode": region_code,
            "addressLines": [raw_address],
        },
        "enableUspsCass": False,
    }
    params = {"key": GOOGLE_MAPS_API_KEY}
    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        r = client.post(API_URL, params=params, json=payload)
        r.raise_for_status()
        data = r.json()

    result = data.get("result", {})
    verdict_obj = result.get("verdict", {})
    address_obj = result.get("address", {})
    geocode_obj = result.get("geocode", {})
    metadata = result.get("metadata", {})

    # Verdict — Google returns booleans + granularity, we map to a single string
    if verdict_obj.get("hasUnconfirmedComponents") and verdict_obj.get("hasInferredComponents"):
        verdict = "UNCONFIRMED_AND_SUSPICIOUS"
    elif verdict_obj.get("hasUnconfirmedComponents"):
        verdict = "UNCONFIRMED_BUT_PLAUSIBLE"
    elif verdict_obj.get("addressComplete") and not verdict_obj.get("hasReplacedComponents"):
        verdict = "CONFIRMED"
    elif address_obj.get("formattedAddress"):
        verdict = "UNCONFIRMED_BUT_PLAUSIBLE"
    else:
        verdict = "UNRESOLVED"

    # Per-component confidence: 1.0 if confirmed, 0.5 if inferred, 0.2 if unconfirmed
    component_confidence: dict[str, float] = {}
    inferred: list[str] = []
    for comp in address_obj.get("addressComponents", []):
        comp_type = comp.get("componentType", "unknown")
        confirmation = comp.get("confirmationLevel", "")
        if confirmation == "CONFIRMED":
            component_confidence[comp_type] = 1.0
        elif confirmation == "UNCONFIRMED_BUT_PLAUSIBLE":
            component_confidence[comp_type] = 0.5
            inferred.append(comp_type)
        else:
            component_confidence[comp_type] = 0.2
            inferred.append(comp_type)

    canonical = address_obj.get("formattedAddress", raw_address)
    pincode = ""
    for comp in address_obj.get("addressComponents", []):
        if comp.get("componentType") == "postal_code":
            pincode = comp.get("componentName", {}).get("text", "")

    location = geocode_obj.get("location", {})
    return AddressValidation(
        verdict=verdict,
        canonical=canonical,
        pincode=pincode,
        geocode_lat=location.get("latitude"),
        geocode_lng=location.get("longitude"),
        is_residential=metadata.get("residential"),
        component_confidence=component_confidence,
        inferred_components=inferred,
        used_real_api=True,
        raw_excerpt={
            "place_id": result.get("geocode", {}).get("placeId"),
            "verdict": verdict_obj,
        },
    )


# ─────────────────────────────────────────────────────────────────────────
# Mock fallback — for hackathon demo without Google Cloud key
# ─────────────────────────────────────────────────────────────────────────

# Demo addresses with curated mock outputs (so the demo behaves predictably)
_MOCK_KNOWN_ADDRESSES: dict[str, dict[str, Any]] = {
    # The 4-account ring address — looks valid, but the cluster signal will catch it
    "flat 7c 88 brigade road bengaluru 560025": {
        "verdict": "CONFIRMED",
        "canonical": "Flat 7C, 88 Brigade Road, Ashok Nagar, Bengaluru, Karnataka 560025, India",
        "pincode": "560025",
        "geocode_lat": 12.9716, "geocode_lng": 77.5946,
        "is_residential": True,
        "component_confidence": {"premise": 0.95, "route": 0.98, "locality": 1.0,
                                 "postal_code": 1.0, "sub_premise": 0.65},
    },
    "flat 4b 12 mg road bengaluru 560001": {
        "verdict": "CONFIRMED",
        "canonical": "Flat 4B, 12 MG Road, Bengaluru, Karnataka 560001, India",
        "pincode": "560001",
        "geocode_lat": 12.9755, "geocode_lng": 77.6055,
        "is_residential": True,
        "component_confidence": {"premise": 0.92, "route": 0.99, "locality": 1.0,
                                 "postal_code": 1.0, "sub_premise": 0.55},
    },
}


def _normalise_for_lookup(s: str) -> str:
    s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _heuristic_pincode(s: str) -> str:
    m = re.search(r"\b(\d{6})\b", s)
    return m.group(1) if m else ""


# Indian pincode-prefix → (city, lat, lng). Used by the mock to assign realistic
# geocodes for arbitrary seeded addresses so the map view shows legit customers
# scattered across India and the ring members tightly clustered.
INDIA_CITY_GEOCODES: dict[str, tuple[str, float, float]] = {
    "560": ("Bengaluru", 12.9716, 77.5946),
    "400": ("Mumbai",    19.0760, 72.8777),
    "110": ("Delhi",     28.6139, 77.2090),
    "411": ("Pune",      18.5204, 73.8567),
    "600": ("Chennai",   13.0827, 80.2707),
    "500": ("Hyderabad", 17.3850, 78.4867),
    "700": ("Kolkata",   22.5726, 88.3639),
    "380": ("Ahmedabad", 23.0225, 72.5714),
    "302": ("Jaipur",    26.9124, 75.7873),
    "682": ("Kochi",      9.9312, 76.2673),
}


def geocode_from_pincode(pincode: str) -> tuple[float, float] | None:
    """Approximate lat/lng for an Indian pincode based on the city prefix.

    Adds small deterministic jitter so multiple addresses in the same city
    don't all stack on the city center.
    """
    import math
    if not pincode or len(pincode) < 3:
        return None
    entry = INDIA_CITY_GEOCODES.get(pincode[:3])
    if not entry:
        return None
    _, lat, lng = entry
    seed_val = sum(ord(c) for c in pincode)
    jitter_lat = math.sin(seed_val) * 0.04   # ~4km
    jitter_lng = math.cos(seed_val * 1.3) * 0.04
    return (lat + jitter_lat, lng + jitter_lng)


def _looks_like_real_address(s: str) -> bool:
    """Cheap heuristic — has digits, has comma, has pincode, length > 20."""
    has_pincode = bool(re.search(r"\b\d{6}\b", s))
    has_digits = bool(re.search(r"\d", s))
    return len(s) > 20 and has_digits and has_pincode


def _mock_validate(raw_address: str, region_code: str = "IN") -> AddressValidation:
    """Deterministic mock that reproduces real-API verdict behaviour for demo addresses."""
    if not raw_address or not raw_address.strip():
        return AddressValidation(
            verdict="UNRESOLVED",
            canonical=raw_address or "",
            pincode="",
            used_real_api=False,
            raw_excerpt={"reason": "empty input"},
        )

    key = _normalise_for_lookup(raw_address)
    if key in _MOCK_KNOWN_ADDRESSES:
        m = _MOCK_KNOWN_ADDRESSES[key]
        return AddressValidation(
            verdict=m["verdict"],
            canonical=m["canonical"],
            pincode=m["pincode"],
            geocode_lat=m["geocode_lat"],
            geocode_lng=m["geocode_lng"],
            is_residential=m["is_residential"],
            component_confidence=m["component_confidence"],
            inferred_components=[],
            used_real_api=False,
            raw_excerpt={"mock": True, "matched": "known"},
        )

    # Generic fallback for arbitrary addresses
    if not _looks_like_real_address(raw_address):
        return AddressValidation(
            verdict="UNCONFIRMED_AND_SUSPICIOUS",
            canonical=raw_address,
            pincode=_heuristic_pincode(raw_address),
            component_confidence={"sub_premise": 0.3, "route": 0.4},
            inferred_components=["sub_premise", "route"],
            used_real_api=False,
            raw_excerpt={"mock": True, "matched": "heuristic_low"},
        )

    pincode = _heuristic_pincode(raw_address)
    geo = geocode_from_pincode(pincode)
    return AddressValidation(
        verdict="CONFIRMED",
        canonical=raw_address,
        pincode=pincode,
        geocode_lat=geo[0] if geo else None,
        geocode_lng=geo[1] if geo else None,
        is_residential=True,
        component_confidence={"premise": 0.85, "route": 0.95, "locality": 0.95,
                              "postal_code": 0.99, "sub_premise": 0.7},
        used_real_api=False,
        raw_excerpt={"mock": True, "matched": "heuristic_ok"},
    )


# ─────────────────────────────────────────────────────────────────────────
# Public entry point — chooses real or mock
# ─────────────────────────────────────────────────────────────────────────

def validate_address(raw_address: str, region_code: str = "IN") -> AddressValidation:
    """Validate via Google API if configured + healthy; else mock fallback.

    Always returns a fully-populated AddressValidation. Never raises.
    """
    if USE_MOCK_ADDRESS or not GOOGLE_MAPS_API_KEY:
        return _mock_validate(raw_address, region_code)
    try:
        return _real_validate(raw_address, region_code)
    except Exception as exc:
        # Network/quota/auth/schema issues all fall back silently.
        print(f"[address] real API failed: {type(exc).__name__}: {exc}; falling back to mock")
        result = _mock_validate(raw_address, region_code)
        result.raw_excerpt["fallback_reason"] = str(exc)
        return result
