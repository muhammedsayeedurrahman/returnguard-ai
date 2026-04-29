"""Unit tests for the unified image_trust verdict."""
from app.engine.image_trust import derive_image_trust


def _ev(signal: str, verdict: str) -> dict:
    return {"signal": signal, "verdict": verdict, "score": 0, "weight": 0.0,
            "detail": "", "raw": {}}


def test_no_photo_returns_unknown():
    evidence = [_ev("exif", "SKIP"), _ev("ela", "SKIP"), _ev("image_text", "SKIP")]
    out = derive_image_trust(evidence)
    assert out["verdict"] == "UNKNOWN"
    assert out["weight"] == 0.0


def test_ela_fail_no_exif_returns_ai_generated():
    evidence = [
        _ev("exif", "MISSING"),
        _ev("ela", "FAIL"),
        _ev("image_text", "OK"),
    ]
    out = derive_image_trust(evidence)
    assert out["verdict"] == "AI_GENERATED"


def test_ela_fail_with_exif_returns_edited():
    evidence = [
        _ev("exif", "OK"),
        _ev("ela", "FAIL"),
        _ev("image_text", "OK"),
    ]
    out = derive_image_trust(evidence)
    assert out["verdict"] == "EDITED"


def test_exif_fail_with_clean_ela_returns_suspicious():
    evidence = [
        _ev("exif", "FAIL"),
        _ev("ela", "OK"),
        _ev("image_text", "OK"),
    ]
    out = derive_image_trust(evidence)
    assert out["verdict"] == "SUSPICIOUS"


def test_image_text_fail_returns_suspicious():
    evidence = [
        _ev("exif", "OK"),
        _ev("ela", "OK"),
        _ev("image_text", "FAIL"),
    ]
    out = derive_image_trust(evidence)
    assert out["verdict"] == "SUSPICIOUS"


def test_all_clean_returns_genuine():
    evidence = [
        _ev("exif", "OK"),
        _ev("ela", "OK"),
        _ev("image_text", "OK"),
    ]
    out = derive_image_trust(evidence)
    assert out["verdict"] == "GENUINE"


def test_warn_signals_return_suspicious():
    evidence = [
        _ev("exif", "WARN"),
        _ev("ela", "OK"),
        _ev("image_text", "OK"),
    ]
    out = derive_image_trust(evidence)
    assert out["verdict"] == "SUSPICIOUS"
