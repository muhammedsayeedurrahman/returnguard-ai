"""FastAPI entry — sec_logistics Inconsistency Engine."""
from __future__ import annotations
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db, get_db
from .engine.fusion import score_claim
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
    photo: UploadFile | None = File(None),
):
    claim_id = f"claim_{uuid.uuid4().hex[:8]}"
    photo_path: str | None = None
    if photo and photo.filename:
        photo_path = str(UPLOAD_DIR / f"{claim_id}_{photo.filename}")
        with open(photo_path, "wb") as f:
            f.write(await photo.read())

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        raise HTTPException(404, "Order not found")

    conn.execute(
        "INSERT INTO claims (id, order_id, customer_id, reason_code, claim_text, photo_path) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (claim_id, order_id, order["customer_id"], reason_code, claim_text, photo_path),
    )
    conn.commit()

    score, decision, evidence = score_claim(claim_id, claim_text, photo_path, dict(order), conn)

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
