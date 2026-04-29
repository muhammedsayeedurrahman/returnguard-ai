"""Module C — Receipt manipulation detection.

Local-only: SHA-256 of the submitted PDF, PDF metadata extracted via PyMuPDF,
date-tamper heuristic, amount-vs-order cross-reference. No Supabase dependency
— hashes are stored in the local `receipt_hashes` table.

For a production hash store across regions, swap _lookup_local_hash with a
Supabase REST call (commented out below — keys go in .env).
"""
from __future__ import annotations
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


_EDIT_TOOLS = {"adobe acrobat", "foxit", "ilovepdf", "smallpdf",
               "libreoffice", "inkscape", "pdfescape", "sejda"}


def _hash_file(path: str) -> tuple[str, str]:
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest(), hashlib.md5(data).hexdigest()


def _extract_pdf_metadata(path: str) -> dict:
    if not PYMUPDF_AVAILABLE:
        return {"error": "PyMuPDF not installed"}
    try:
        doc = fitz.open(path)
        meta = doc.metadata or {}
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "creator": meta.get("creator", ""),
            "producer": meta.get("producer", ""),
            "creation_date": meta.get("creationDate", ""),
            "mod_date": meta.get("modDate", ""),
            "text_length": len(text),
            "text_excerpt": text[:500],
        }
    except Exception as exc:
        return {"error": str(exc)}


def _check_date_tamper(metadata: dict) -> dict:
    signals = []
    creation = metadata.get("creation_date", "")
    mod = metadata.get("mod_date", "")
    if creation and mod and mod > creation:
        try:
            c_clean = creation[2:16] if creation.startswith("D:") else creation[:14]
            m_clean = mod[2:16] if mod.startswith("D:") else mod[:14]
            c_dt = datetime.strptime(c_clean, "%Y%m%d%H%M%S")
            m_dt = datetime.strptime(m_clean, "%Y%m%d%H%M%S")
            diff = (m_dt - c_dt).total_seconds()
            if diff > 60:
                signals.append({
                    "type": "DATE_MODIFIED",
                    "detail": f"PDF modified {int(diff)}s after creation",
                })
        except (ValueError, IndexError):
            pass

    producer = (metadata.get("producer") or "").lower()
    for tool in _EDIT_TOOLS:
        if tool in producer:
            signals.append({
                "type": "EDIT_TOOL",
                "detail": f"Producer field: {metadata.get('producer')}",
            })
            break

    return {"signals": signals, "tampered": bool(signals)}


def _amount_match(text: str, expected_inr: float) -> dict:
    """Look for the order amount in the receipt text. Naive but useful."""
    import re
    if not text:
        return {"checked": False}
    amount_str_int = f"{int(expected_inr)}"
    amount_str_dec = f"{expected_inr:.2f}"
    found_int = amount_str_int in text
    found_dec = amount_str_dec in text
    return {
        "checked": True,
        "expected": expected_inr,
        "found_in_text": found_int or found_dec,
    }


def score(receipt_path: str | None, order_id: str, order_value_inr: float,
          conn: sqlite3.Connection) -> dict:
    weight = 0.20
    if not receipt_path:
        return {"signal": "receipt", "verdict": "SKIP", "score": 0,
                "weight": weight, "detail": "No receipt submitted", "raw": {}}

    sha256, md5 = _hash_file(receipt_path)
    metadata = _extract_pdf_metadata(receipt_path)
    date_check = _check_date_tamper(metadata)
    amount_check = _amount_match(metadata.get("text_excerpt", ""), order_value_inr)

    raw = {
        "sha256": sha256,
        "md5": md5,
        "metadata": {k: v for k, v in metadata.items() if k != "text_excerpt"},
        "tamper_signals": date_check["signals"],
        "amount_check": amount_check,
    }

    # Lookup against locally stored hashes (from prior receipts we issued)
    stored = conn.execute(
        "SELECT pdf_hash_sha256, amount_inr FROM receipt_hashes WHERE order_id = ?",
        (order_id,),
    ).fetchone() if _has_receipt_table(conn) else None

    if stored and stored["pdf_hash_sha256"] != sha256:
        return {"signal": "receipt", "verdict": "FAIL", "score": 90, "weight": weight,
                "detail": "Receipt SHA-256 differs from issued copy — tampering detected",
                "raw": {**raw, "stored_amount": stored["amount_inr"]}}

    if date_check["tampered"]:
        return {"signal": "receipt", "verdict": "FAIL", "score": 75, "weight": weight,
                "detail": f"PDF tamper signals: {', '.join(s['type'] for s in date_check['signals'])}",
                "raw": raw}

    if amount_check["checked"] and not amount_check["found_in_text"]:
        return {"signal": "receipt", "verdict": "WARN", "score": 35, "weight": weight,
                "detail": f"Order amount ₹{order_value_inr:.0f} not found in receipt text",
                "raw": raw}

    if stored:
        return {"signal": "receipt", "verdict": "OK", "score": 0, "weight": weight,
                "detail": "Receipt SHA-256 matches issued copy", "raw": raw}

    return {"signal": "receipt", "verdict": "OK", "score": 10, "weight": weight,
            "detail": "Receipt metadata clean (no stored hash to compare)", "raw": raw}


def _has_receipt_table(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='receipt_hashes'"
    ).fetchone()
    return row is not None
