"""Generate clean + tampered receipt PDFs for the demo.

Real product behaviour: when an order is placed, we issue a PDF receipt and
record its SHA-256 hash in `receipt_hashes`. Customers who want to file a
high-value return can verify their receipt against our records.

For the demo, every seeded order gets a generated receipt at seed time.
The /api/v1/demo/receipts/{order_id}/tampered endpoint returns a doctored
version (different amount) so judges can see the MISMATCH path live.
"""
from __future__ import annotations
import hashlib
from datetime import datetime
from io import BytesIO
from pathlib import Path

import fitz  # PyMuPDF


def _format_date(iso_str: str) -> str:
    try:
        return datetime.fromisoformat(iso_str).strftime("%d %B %Y")
    except (ValueError, TypeError):
        return iso_str or "—"


def generate_receipt_pdf(*, order_id: str, customer_id: str,
                         product_name: str, amount_inr: float,
                         ordered_at: str = "",
                         tampered: bool = False) -> bytes:
    """Generate a PDF receipt as raw bytes.

    Set `tampered=True` to produce a visibly-edited version with an inflated
    amount — used for the demo's MISMATCH scenario.
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    indigo = (0.345, 0.337, 0.835)
    grey   = (0.45, 0.45, 0.45)
    light_grey = (0.85, 0.85, 0.85)
    danger = (0.86, 0.15, 0.15)

    # ─── Header ──────────────────────────────────────────────────────
    page.insert_text((40, 70), "ReturnGuard AI",
                     fontname="hebo", fontsize=22, color=indigo)
    page.insert_text((40, 92), "Tax Invoice / Receipt",
                     fontname="helv", fontsize=12, color=grey)
    page.insert_text((430, 70), f"Receipt #",
                     fontname="helv", fontsize=10, color=grey)
    page.insert_text((430, 86), order_id,
                     fontname="hebo", fontsize=11, color=(0, 0, 0))

    # ─── Order details box ───────────────────────────────────────────
    box = fitz.Rect(40, 130, 555, 250)
    page.draw_rect(box, color=light_grey, width=0.5)

    page.insert_text((52, 152), "ORDER DETAILS",
                     fontname="hebo", fontsize=10, color=indigo)
    page.insert_text((52, 178), f"Order ID:", fontname="helv", fontsize=10, color=grey)
    page.insert_text((150, 178), order_id, fontname="helv", fontsize=10)
    page.insert_text((52, 198), f"Customer:", fontname="helv", fontsize=10, color=grey)
    page.insert_text((150, 198), customer_id, fontname="helv", fontsize=10)
    page.insert_text((52, 218), f"Order Date:", fontname="helv", fontsize=10, color=grey)
    page.insert_text((150, 218), _format_date(ordered_at), fontname="helv", fontsize=10)
    page.insert_text((52, 238), f"Status:", fontname="helv", fontsize=10, color=grey)
    page.insert_text((150, 238), "Delivered", fontname="hebo", fontsize=10,
                     color=(0.06, 0.5, 0.32))

    # ─── Items table ─────────────────────────────────────────────────
    page.insert_text((40, 300), "DESCRIPTION",
                     fontname="hebo", fontsize=10, color=indigo)
    page.insert_text((460, 300), "AMOUNT",
                     fontname="hebo", fontsize=10, color=indigo)
    page.draw_line((40, 310), (555, 310), color=indigo, width=1)

    page.insert_text((40, 340), product_name, fontname="helv", fontsize=11)
    page.insert_text((460, 340), f"Rs. {amount_inr:,.2f}",
                     fontname="helv", fontsize=11)
    page.draw_line((40, 360), (555, 360), color=light_grey, width=0.5)

    # ─── Total ──────────────────────────────────────────────────────
    page.insert_text((360, 400), "Total Amount:",
                     fontname="hebo", fontsize=12)
    total_color = danger if tampered else (0, 0, 0)
    page.insert_text((460, 400), f"Rs. {amount_inr:,.2f}",
                     fontname="hebo", fontsize=14, color=total_color)

    # ─── Tampered watermark (only for demo-tamper version) ──────────
    if tampered:
        page.insert_text((40, 440), "[ DEMO TAMPERED COPY — DO NOT TRUST ]",
                         fontname="hebo", fontsize=11, color=danger)

    # ─── Footer with hash promise ───────────────────────────────────
    page.insert_text((40, 750),
                     "This receipt is hash-recorded. Verify at /billing on returnguard.ai",
                     fontname="helv", fontsize=8, color=grey)
    page.insert_text((40, 765),
                     f"Issued: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}",
                     fontname="helv", fontsize=8, color=grey)

    buf = BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def hash_pdf_bytes(pdf_bytes: bytes) -> tuple[str, str]:
    """Returns (sha256_hex, md5_hex)."""
    return (hashlib.sha256(pdf_bytes).hexdigest(),
            hashlib.md5(pdf_bytes).hexdigest())


def write_receipt_to_disk(pdf_bytes: bytes, order_id: str,
                          base_dir: Path) -> Path:
    """Save a generated receipt PDF to disk and return its path."""
    out_dir = base_dir / "receipts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{order_id}.pdf"
    out_path.write_bytes(pdf_bytes)
    return out_path
