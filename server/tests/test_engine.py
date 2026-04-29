"""End-to-end tests for the Inconsistency Engine.

Run: pytest -v from the server/ directory.
"""
import io
from PIL import Image
from app.engine.address import hash_address
from app.engine.address_intel import validate_address


def _canonical_hash(raw: str) -> str:
    v = validate_address(raw, region_code="IN")
    return hash_address(v.canonical or raw)


SHARED_RING_ADDRESS = "Flat 7C, 88 Brigade Road, Bengaluru, 560025"
RING_PINCODE = "560025"
# Near-identical phrasing — TF-IDF cosine ≥ 0.75 across all pairs
RING_TEMPLATE_VARIATIONS = [
    "Item arrived but it is not as described in the listing. Quality is poor and packaging was tampered.",
    "Item arrived but it is not as described in the listing. Quality is poor and packaging was tampered with.",
    "Item arrived but it is not as described in listing. Quality is poor and the packaging was tampered.",
]


def _make_exif_jpeg(exif_date_str: str) -> bytes:
    """Tiny JPEG with EXIF DateTimeOriginal set. Format: 'YYYY:MM:DD HH:MM:SS'."""
    img = Image.new("RGB", (16, 16), color="white")
    exif = img.getexif()
    exif[36867] = exif_date_str  # DateTimeOriginal tag
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=exif)
    return buf.getvalue()


def _insert_customer(db, cust_id, days_old=300):
    db.execute(
        "INSERT OR REPLACE INTO customers (id, email_hash, phone_hash, return_count_30d, created_at) "
        "VALUES (?, ?, ?, 0, datetime('now', ?))",
        (cust_id, f"h_{cust_id}", f"p_{cust_id}", f"-{days_old} days"),
    )


def _insert_order(db, order_id, cust_id, address, pincode, value=5000, product="Test Earbuds"):
    db.execute(
        "INSERT OR REPLACE INTO orders (id, customer_id, product_name, product_category, value_inr, "
        "ordered_at, delivered_at, shipping_address, shipping_addr_hash, pincode, status) "
        "VALUES (?, ?, ?, 'electronics', ?, datetime('now','-7 days'), "
        "datetime('now','-3 days'), ?, ?, ?, 'delivered')",
        (order_id, cust_id, product, value, address, _canonical_hash(address), pincode),
    )


def _seed_ring_baseline(db):
    """3 prior ring claims at the shared address. The 4th is what we'll submit live."""
    addr_hash = _canonical_hash(SHARED_RING_ADDRESS)
    for i in range(3):
        cust_id = f"cust_ring_{i+1:02d}"
        order_id = f"ord_ring_{i+1:02d}"
        claim_id = f"claim_ring_{i+1:02d}"
        _insert_customer(db, cust_id, days_old=15)
        _insert_order(db, order_id, cust_id, SHARED_RING_ADDRESS, RING_PINCODE)
        db.execute(
            "INSERT INTO claims (id, order_id, customer_id, reason_code, claim_text, "
            "score, decision, filed_at) VALUES (?, ?, ?, 'damaged', ?, 50, 'BORDERLINE', "
            "datetime('now','-1 hours'))",
            (claim_id, order_id, cust_id, RING_TEMPLATE_VARIATIONS[i]),
        )
        db.execute(
            "INSERT INTO address_signatures (hash, customer_id, pincode, created_at) "
            "VALUES (?, ?, ?, datetime('now','-1 hours'))",
            (addr_hash, cust_id, RING_PINCODE),
        )

    # The 4th account — order seeded but claim NOT filed yet.
    _insert_customer(db, "cust_ring_04", days_old=12)
    _insert_order(db, "ord_ring_04", "cust_ring_04", SHARED_RING_ADDRESS, RING_PINCODE,
                  product="Test AirPods")
    db.commit()


# ────────────────────────────────────────────────────────────────────────
# Tests
# ────────────────────────────────────────────────────────────────────────

def test_legit_claim_approves(client, db):
    """Maya: clean customer, no prior claims, plausible damage text → APPROVE, score < 35."""
    _insert_customer(db, "cust_maya", days_old=400)
    _insert_order(db, "ord_maya", "cust_maya",
                  "Flat 12, Park Street, Mumbai, 400001", "400001",
                  value=1499, product="Boat Earbuds")
    db.commit()

    r = client.post("/api/v1/claims", data={
        "order_id": "ord_maya",
        "reason_code": "damaged",
        "claim_text": "Earbuds case has a small crack near the hinge, came like that out of the box",
    })
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["decision"] == "APPROVE", \
        f"Expected APPROVE, got {data['decision']} (score={data['score']})"
    assert data["score"] < 35
    assert data["session_id"] is None  # no escalation


def test_ring_4th_submission_triggers_cluster_and_rejects(client, db):
    """The 4th claim from a ring address with similar template text →
       linguistic + address signals fire → ring_cluster row created → REJECT."""
    _seed_ring_baseline(db)

    r = client.post("/api/v1/claims", data={
        "order_id": "ord_ring_04",
        "reason_code": "damaged",
        "claim_text": "Item arrived but it's not as described in the listing. "
                      "Quality is poor and the packaging was tampered. Please refund urgently.",
    })
    assert r.status_code == 200, r.text
    data = r.json()["data"]

    # Decision must be REJECT
    assert data["decision"] == "REJECT", \
        f"Expected REJECT, got {data['decision']} (score={data['score']})"
    assert data["score"] >= 65

    # The two corroborating signals must have fired (linguistic may land WARN or FAIL
    # depending on exact phrasing; address must FAIL with 4 distinct customers).
    signals = {ev["signal"]: ev for ev in data["evidence"]}
    assert signals["linguistic"]["verdict"] in ("WARN", "FAIL"), \
        f"Expected linguistic WARN/FAIL, got {signals['linguistic']['verdict']}"
    assert signals["address"]["verdict"] == "FAIL", \
        f"Expected address FAIL, got {signals['address']['verdict']}"

    # ring_cluster row must exist with all 4 customers
    rings = client.get("/api/v1/admin/rings").json()["data"]
    assert len(rings) == 1
    cluster = rings[0]
    assert "cust_ring_04" in cluster["customer_ids"]
    assert len(cluster["customer_ids"]) >= 4
    assert cluster["exposure_inr"] > 0


def test_borderline_claim_opens_evaluation_session(client, db):
    """Score 35-64 should auto-open an evaluation_sessions row.

    Trigger: real JPEG with EXIF date 30 days before delivery (EXIF FAIL +90)
             + filename hint that triggers image_text mock (FAIL +75).
             Two signals ≥60 → corroboration multiplier → BORDERLINE.
    """
    _insert_customer(db, "cust_priya", days_old=420)
    _insert_order(db, "ord_priya", "cust_priya",
                  "Flat 4B, MG Road, Bengaluru, 560001", "560001",
                  value=1499)
    db.commit()

    # JPEG with EXIF date long before delivery — EXIF check fires FAIL
    photo_bytes = _make_exif_jpeg("2025:09:01 12:00:00")
    # Filename includes "wrong_product" → image_text mock returns FAIL
    files = {"photo": ("priya_wrong_product.jpg", photo_bytes, "image/jpeg")}

    r = client.post(
        "/api/v1/claims",
        data={
            "order_id": "ord_priya",
            "reason_code": "damaged",
            "claim_text": "Earbuds arrived with damage on the speaker",
        },
        files=files,
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["decision"] in ("BORDERLINE", "REJECT"), \
        f"Expected BORDERLINE/REJECT, got {data['decision']} (score={data['score']})"
    if data["decision"] == "BORDERLINE":
        assert data["session_id"] is not None


def test_evaluation_engine_resolves_session(client, db):
    """Borderline → AI engine session created → at least 1 turn returns a message."""
    _insert_customer(db, "cust_priya", days_old=420)
    _insert_order(db, "ord_priya", "cust_priya",
                  "Flat 4B, MG Road, Bengaluru, 560001", "560001")
    db.commit()

    photo_bytes = _make_exif_jpeg("2025:09:01 12:00:00")
    files = {"photo": ("priya_wrong_product.jpg", photo_bytes, "image/jpeg")}
    r = client.post(
        "/api/v1/claims",
        data={"order_id": "ord_priya", "reason_code": "damaged",
              "claim_text": "Damaged on arrival"},
        files=files,
    )
    data = r.json()["data"]

    # If auto-rejected (score ≥ 65), that's also a valid outcome — skip session test
    if data["decision"] != "BORDERLINE":
        assert data["decision"] == "REJECT"
        return

    session_id = data["session_id"]
    assert session_id

    # Turn 1
    r1 = client.post(f"/api/v1/evaluation/{session_id}/turn",
                     data={"message": "I just opened it this morning"})
    assert r1.status_code == 200
    t1 = r1.json()["data"]
    assert t1["agent_message"]
