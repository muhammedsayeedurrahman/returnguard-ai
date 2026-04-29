"""FastAPI entry — sec_logistics Inconsistency Engine."""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from .db import init_db, get_db
from .engine.fusion import score_claim_async
from .evaluation_engine.runner import open_session, take_turn

app = FastAPI(title="sec_logistics Inconsistency Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/v1/orders/{order_id}")
def get_order(order_id: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Order not found")
    return {"ok": True, "data": dict(row)}


@app.post("/api/v1/claims")
async def submit_claim(
    order_id: str = Form(...),
    reason_code: str = Form(...),
    claim_text: str = Form(""),
    capture_method: str = Form("file_upload"),
    photo: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
):
    claim_id = f"claim_{uuid.uuid4().hex[:8]}"
    photo_path: str | None = None
    if photo and photo.filename:
        photo_path = str(UPLOAD_DIR / f"{claim_id}_{photo.filename}")
        with open(photo_path, "wb") as f:
            f.write(await photo.read())
    video_path: str | None = None
    if video and video.filename:
        video_dir = UPLOAD_DIR / "videos"
        video_dir.mkdir(parents=True, exist_ok=True)
        video_path = str(video_dir / f"{claim_id}.webm")
        with open(video_path, "wb") as f:
            f.write(await video.read())

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        raise HTTPException(404, "Order not found")

    # Bug 3: increment rolling 30-day return count
    conn.execute(
        "UPDATE customers SET return_count_30d = return_count_30d + 1 WHERE id = ?",
        (order["customer_id"],),
    )

    conn.execute(
        "INSERT INTO claims (id, order_id, customer_id, reason_code, claim_text, "
        "photo_path, video_path, capture_method) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (claim_id, order_id, order["customer_id"], reason_code, claim_text,
         photo_path, video_path, capture_method),
    )
    conn.commit()

    # Pass reason_code via order dict so wardrobing/INR scorers can branch on it
    order_dict = dict(order)
    order_dict["reason_code"] = reason_code

    # Bug 1: async fusion runs signals concurrently
    score, decision, evidence = await score_claim_async(
        claim_id, claim_text, photo_path, order_dict, conn, capture_method,
    )

    conn.execute(
        "UPDATE claims SET score = ?, decision = ? WHERE id = ?",
        (score, decision, claim_id),
    )
    for ev in evidence:
        conn.execute(
            "INSERT INTO claim_evidence (claim_id, signal_name, verdict, detail, weight, raw_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (claim_id, ev["signal"], ev["verdict"], ev["detail"], ev["weight"],
             json.dumps(ev.get("raw", {}))),
        )
    conn.commit()

    # Phase 6: write return_history row for wardrobing future-detection
    from .engine.wardrobing import record_return_history
    wardrobing_ev = next((e for e in evidence if e["signal"] == "wardrobing"), None)
    record_return_history(
        order["customer_id"], order_id, claim_id, dict(order),
        wardrobing_ev["score"] if wardrobing_ev else 0, conn,
    )
    conn.commit()

    session_id: str | None = None
    if decision == "BORDERLINE":
        session_id = open_session(claim_id, score, conn)

    conn.close()
    return {
        "ok": True,
        "data": {
            "claim_id": claim_id,
            "score": score,
            "decision": decision,
            "session_id": session_id,
            "evidence": evidence,
        },
    }


@app.get("/api/v1/claims/{claim_id}")
def get_claim(claim_id: str):
    conn = get_db()
    claim = conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
    if not claim:
        conn.close()
        raise HTTPException(404, "Claim not found")
    evidence = conn.execute(
        "SELECT * FROM claim_evidence WHERE claim_id = ? ORDER BY id",
        (claim_id,),
    ).fetchall()
    session = conn.execute(
        "SELECT * FROM evaluation_sessions WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    turns = []
    if session:
        rows = conn.execute(
            "SELECT * FROM evaluation_turns WHERE session_id = ? ORDER BY turn_number",
            (session["id"],),
        ).fetchall()
        turns = [dict(r) for r in rows]
    conn.close()
    return {
        "ok": True,
        "data": {
            "claim": dict(claim),
            "evidence": [dict(e) for e in evidence],
            "session": dict(session) if session else None,
            "turns": turns,
        },
    }


@app.post("/api/v1/evaluation/{session_id}/turn")
async def evaluation_turn(
    session_id: str,
    message: str = Form(""),
    photo: UploadFile | None = File(None),
):
    conn = get_db()
    photo_path: str | None = None
    if photo and photo.filename:
        photo_path = str(UPLOAD_DIR / f"turn_{uuid.uuid4().hex[:8]}_{photo.filename}")
        with open(photo_path, "wb") as f:
            f.write(await photo.read())
    result = take_turn(session_id, message, photo_path, conn)
    conn.close()
    return {"ok": True, "data": result}


@app.get("/api/v1/admin/queue")
def admin_queue():
    conn = get_db()
    rows = conn.execute(
        "SELECT c.*, o.product_name, o.value_inr FROM claims c "
        "JOIN orders o ON c.order_id = o.id "
        "ORDER BY c.filed_at DESC LIMIT 100"
    ).fetchall()
    conn.close()
    return {"ok": True, "data": [dict(r) for r in rows]}


@app.get("/api/v1/admin/rings")
def admin_rings():
    conn = get_db()
    rings = conn.execute(
        "SELECT * FROM ring_clusters ORDER BY detected_at DESC"
    ).fetchall()
    out = []
    for r in rings:
        d = dict(r)
        d["customer_ids"] = json.loads(d["customer_ids"])
        out.append(d)
    conn.close()
    return {"ok": True, "data": out}


@app.post("/api/v1/webhooks/chargeback")
async def chargeback_webhook(
    customer_id: str = Form(...),
    order_id: str = Form(...),
    amount_inr: float = Form(...),
    payment_method: str = Form("credit_card"),
    reason: str = Form("unauthorised"),
):
    from .engine.friendly_fraud import record_chargeback
    conn = get_db()
    result = record_chargeback(customer_id, order_id, amount_inr,
                                payment_method, reason, conn)
    conn.close()
    return {"ok": True, "data": result}


@app.post("/api/v1/webhooks/carrier")
async def carrier_webhook(
    order_id: str = Form(...),
    carrier: str = Form(...),
    event_type: str = Form(...),
    shipment_id: str = Form(""),
    gps_lat: float | None = Form(None),
    gps_lng: float | None = Form(None),
    otp_confirmed: bool = Form(False),
    delivered_at: str = Form(""),
):
    conn = get_db()
    if event_type == "SHIPMENT_DELIVERED":
        order = conn.execute("SELECT customer_id FROM orders WHERE id = ?",
                             (order_id,)).fetchone()
        cust = order["customer_id"] if order else ""
        conn.execute(
            "INSERT INTO shipment_deliveries "
            "(order_id, customer_id, carrier, shipment_id, delivered_at, "
            " gps_lat, gps_lng, otp_confirmed) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (order_id, cust, carrier, shipment_id,
             delivered_at or datetime.now().isoformat(),
             gps_lat, gps_lng, int(otp_confirmed)),
        )
    conn.commit()
    conn.close()
    return {"ok": True, "data": {"event_recorded": event_type}}


@app.get("/api/v1/claims/{claim_id}/video")
def stream_claim_video(claim_id: str):
    """Return the proof-video the customer recorded with their claim."""
    conn = get_db()
    row = conn.execute(
        "SELECT video_path FROM claims WHERE id = ?", (claim_id,),
    ).fetchone()
    conn.close()
    if not row or not row["video_path"]:
        raise HTTPException(404, "No video on file for this claim")
    path = Path(row["video_path"])
    if not path.exists():
        raise HTTPException(404, "Video file missing")
    return FileResponse(str(path), media_type="video/webm",
                        filename=f"{claim_id}.webm")


@app.get("/api/v1/receipts/{order_id}/download")
def download_receipt(order_id: str):
    """Return the original receipt PDF generated at order time."""
    pdf_path = UPLOAD_DIR / "receipts" / f"{order_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(404, "Receipt not found for this order")
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=f"receipt_{order_id}.pdf",
    )


@app.get("/api/v1/demo/receipts/{order_id}/tampered")
def download_tampered_receipt(order_id: str):
    """Demo helper — returns a doctored version of the receipt with an inflated
    amount. Hash differs from the stored original, so verification will FAIL.
    """
    from .engine.receipt_generator import generate_receipt_pdf
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    if not order:
        raise HTTPException(404, "Order not found")
    inflated = max(order["value_inr"] * 2.5, 99999.0)
    pdf_bytes = generate_receipt_pdf(
        order_id=order_id, customer_id=order["customer_id"],
        product_name=order["product_name"], amount_inr=inflated,
        ordered_at=order["ordered_at"], tampered=True,
    )
    return Response(
        pdf_bytes, media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{order_id}_tampered.pdf"',
        },
    )


@app.post("/api/v1/receipts/verify")
async def verify_receipt(
    order_id: str = Form(...),
    receipt: UploadFile = File(...),
):
    """Standalone receipt verification endpoint — used by Receipt Check page."""
    path = str(UPLOAD_DIR / f"receipt_{uuid.uuid4().hex[:8]}_{receipt.filename}")
    with open(path, "wb") as f:
        f.write(await receipt.read())

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        raise HTTPException(404, "Order not found")
    from .engine.receipt import score as receipt_score
    result = receipt_score(path, order_id, order["value_inr"], conn)
    conn.close()
    return {"ok": True, "data": result}


@app.post("/api/v1/admin/review")
async def submit_review(
    claim_id: str = Form(...),
    reviewer_id: str = Form("admin"),
    outcome: str = Form(...),
    notes: str = Form(""),
):
    """Human reviewer override — CONFIRMED_LEGIT / CONFIRMED_FRAUD / ESCALATED."""
    if outcome not in ("CONFIRMED_LEGIT", "CONFIRMED_FRAUD", "ESCALATED"):
        raise HTTPException(400, "Invalid outcome")
    conn = get_db()
    conn.execute(
        "INSERT INTO review_labels (claim_id, reviewer_id, outcome, notes) "
        "VALUES (?, ?, ?, ?)",
        (claim_id, reviewer_id, outcome, notes),
    )
    if outcome == "CONFIRMED_FRAUD":
        conn.execute("UPDATE claims SET decision = 'REJECT' WHERE id = ?", (claim_id,))
    elif outcome == "CONFIRMED_LEGIT":
        conn.execute("UPDATE claims SET decision = 'APPROVE' WHERE id = ?", (claim_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "data": {"outcome": outcome}}


@app.get("/api/v1/customers/{customer_id}/payment-methods")
def get_allowed_payment_methods(customer_id: str):
    conn = get_db()
    row = conn.execute(
        "SELECT risk_tier FROM payment_risk_profiles WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()
    conn.close()
    tier = row["risk_tier"] if row else "LOW"
    restrictions = {
        "LOW":     ["cod","upi","netbanking","debit_card","credit_card","bnpl","wallet"],
        "MEDIUM":  ["cod","upi","netbanking","debit_card","credit_card","wallet"],
        "HIGH":    ["cod","upi","netbanking"],
        "BLOCKED": ["cod"],
    }
    return {"ok": True, "data": {"risk_tier": tier,
                                 "allowed_methods": restrictions.get(tier, [])}}


@app.get("/api/v1/admin/map")
def admin_map():
    """Return all claims with geographic data for map visualisation.

    Each point includes lat/lng (from address validation evidence or
    pincode lookup fallback), decision tier, and ring membership.
    """
    from .engine.address_intel import geocode_from_pincode
    conn = get_db()
    rows = conn.execute(
        "SELECT c.id AS claim_id, c.customer_id, c.decision, c.score, "
        "c.ring_cluster_id, c.filed_at, "
        "o.product_name, o.value_inr, o.shipping_address, o.pincode, "
        "ce.raw_json AS addr_evidence "
        "FROM claims c "
        "JOIN orders o ON c.order_id = o.id "
        "LEFT JOIN claim_evidence ce ON ce.claim_id = c.id "
        "  AND ce.signal_name = 'address' "
        "ORDER BY c.filed_at DESC "
        "LIMIT 200"
    ).fetchall()

    points: list[dict] = []
    for r in rows:
        d = dict(r)
        lat: float | None = None
        lng: float | None = None
        canonical = d.get("shipping_address")
        if d.get("addr_evidence"):
            try:
                ev = json.loads(d["addr_evidence"])
                gc = ev.get("geocode")
                if gc and gc[0] is not None:
                    lat, lng = float(gc[0]), float(gc[1])
                canonical = ev.get("google_canonical") or canonical
            except (json.JSONDecodeError, TypeError, ValueError, KeyError):
                pass
        if lat is None:
            g = geocode_from_pincode(d.get("pincode") or "")
            if g:
                lat, lng = g
        if lat is None:
            continue
        points.append({
            "claim_id": d["claim_id"],
            "customer_id": d["customer_id"],
            "decision": d["decision"] or "PENDING",
            "score": d["score"] or 0,
            "ring_cluster_id": d["ring_cluster_id"],
            "product_name": d["product_name"],
            "value_inr": d["value_inr"],
            "address": canonical,
            "pincode": d["pincode"],
            "lat": lat,
            "lng": lng,
        })
    conn.close()
    return {"ok": True, "data": points}


@app.get("/api/v1/admin/stats")
def admin_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS c FROM claims").fetchone()["c"]
    approved = conn.execute(
        "SELECT COUNT(*) AS c FROM claims WHERE decision = 'APPROVE'"
    ).fetchone()["c"]
    rejected = conn.execute(
        "SELECT COUNT(*) AS c FROM claims WHERE decision = 'REJECT'"
    ).fetchone()["c"]
    borderline = conn.execute(
        "SELECT COUNT(*) AS c FROM claims WHERE decision = 'BORDERLINE'"
    ).fetchone()["c"]
    rings = conn.execute("SELECT COUNT(*) AS c FROM ring_clusters").fetchone()["c"]
    exposure = conn.execute(
        "SELECT COALESCE(SUM(exposure_inr), 0) AS s FROM ring_clusters"
    ).fetchone()["s"]
    conn.close()
    return {
        "ok": True,
        "data": {
            "total_claims": total,
            "approved": approved,
            "rejected": rejected,
            "borderline": borderline,
            "rings": rings,
            "exposure_inr": exposure,
        },
    }
