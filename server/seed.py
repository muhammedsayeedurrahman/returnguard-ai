"""Seed demo data — 30 legit claims + 1 four-account ring + Priya (EXIF fail).

Run: python seed.py
"""
from __future__ import annotations
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
from app.db import init_db, get_db
from app.engine.address import hash_address
from app.engine.address_intel import validate_address


def canonical_hash(raw_address: str) -> str:
    """Same canonical-hashing path as the live engine: Google validate → hash canonical."""
    v = validate_address(raw_address, region_code="IN")
    base = v.canonical if v.canonical else raw_address
    return hash_address(base)

random.seed(42)

# ─────────────────────────────────────────────────────────────────────────
# Realistic Indian customer + order seed data
# ─────────────────────────────────────────────────────────────────────────

PRODUCTS = [
    ("Boat Airdopes 141 Earbuds", "electronics", 1499),
    ("Samsung Galaxy M14 5G", "electronics", 13999),
    ("Mamaearth Vitamin C Face Wash", "beauty", 249),
    ("Levis Mens Slim Jeans 511", "apparel", 2199),
    ("Prestige Pressure Cooker 5L", "appliance", 1899),
    ("Lakme 9to5 Lipstick Coffee Command", "beauty", 599),
    ("Nike Revolution 6 Running Shoes", "apparel", 3995),
    ("Philips HD9216 Air Fryer", "appliance", 7999),
    ("Apple AirPods 3rd Gen", "electronics", 18900),
    ("Pampers Premium Diapers L Pack", "baby", 1399),
]

CITIES = [
    ("Bengaluru", "560001"), ("Mumbai", "400001"), ("Delhi", "110001"),
    ("Pune", "411001"), ("Chennai", "600001"), ("Hyderabad", "500001"),
    ("Kolkata", "700001"), ("Ahmedabad", "380001"),
]

LEGIT_REASONS = [
    ("damaged", "Box arrived crushed and the product had a small crack on the side panel"),
    ("damaged", "Screen flickering since the moment I powered it on, looks defective"),
    ("wrong_item", "I ordered the blue variant but received the black one"),
    ("wrong_item", "Wrong size delivered — ordered M, got XL"),
    ("not_received", "Package shows delivered but I was home all day, nothing arrived"),
    ("damaged", "Bottle leaked all over the box, half the product was wasted"),
    ("damaged", "The fabric has a tear near the seam, doesn't look like factory fault"),
]

RING_TEMPLATE_TEXT = (
    "Item arrived but it's not as described in the listing. The quality is poor "
    "and the packaging was tampered with. Please refund or replace urgently."
)

# Slight variations for ring members — same template, minor word swaps
RING_VARIATIONS = [
    "Item arrived but it's not as described in the listing. The quality is poor and the packaging was tampered with. Please refund or replace urgently.",
    "Product arrived but it's not as described in the listing. Quality is poor and packaging was tampered. Please refund or replace urgently.",
    "Item came but it is not as described in listing. Quality is bad and packaging was tampered with. Please process refund or replace urgently.",
    "The item arrived but it's not as described in the listing. Quality is poor and the package was tampered. Please refund or replace soon.",
]


def _insert_customer(conn: sqlite3.Connection, cust_id: str, days_old: int = 180,
                     return_count: int = 0) -> None:
    created = (datetime.now() - timedelta(days=days_old)).isoformat(sep=" ", timespec="seconds")
    conn.execute(
        "INSERT OR REPLACE INTO customers (id, email_hash, phone_hash, return_count_30d, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (cust_id, f"hash_{cust_id}", f"hash_{cust_id}", return_count, created),
    )


def _insert_order(conn: sqlite3.Connection, order_id: str, cust_id: str,
                  product: tuple, address: str, pincode: str,
                  ordered_days_ago: int = 7, delivered_days_ago: int = 3) -> None:
    name, category, value = product
    ordered = (datetime.now() - timedelta(days=ordered_days_ago)).isoformat(sep=" ", timespec="seconds")
    delivered = (datetime.now() - timedelta(days=delivered_days_ago)).isoformat(sep=" ", timespec="seconds")
    conn.execute(
        "INSERT OR REPLACE INTO orders (id, customer_id, product_name, product_category, "
        "value_inr, ordered_at, delivered_at, shipping_address, shipping_addr_hash, pincode, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'delivered')",
        (order_id, cust_id, name, category, value, ordered, delivered,
         address, canonical_hash(address), pincode),
    )


# ─────────────────────────────────────────────────────────────────────────
# Seed scenarios
# ─────────────────────────────────────────────────────────────────────────

def seed_maya_demo(conn: sqlite3.Connection) -> None:
    """Explicit Maya demo order — ord_legit_000 is hardcoded so the demo panel
    has deterministic product / address / customer-age. Used by DemoPanel.tsx.
    """
    _insert_customer(conn, "cust_maya_demo", days_old=500, return_count=0)
    _insert_order(
        conn, "ord_legit_000", "cust_maya_demo",
        ("Boat Airdopes 141 Earbuds", "electronics", 1499),
        "Flat 3A, MG Road, Bengaluru, 560001", "560001",
        ordered_days_ago=8, delivered_days_ago=4,
    )


def seed_legit_history(conn: sqlite3.Connection, n: int = 30) -> None:
    """30 legitimate historical claims spread across 90 days, varied products + reasons."""
    for i in range(n):
        cust_id = f"cust_legit_{i:03d}"
        order_id = f"ord_legit_{i:03d}"
        product = random.choice(PRODUCTS)
        city, pincode = random.choice(CITIES)
        addr = f"Flat {random.randint(101, 999)}, {random.choice(['MG Road','Nehru Place','Park Street','Brigade Road','Linking Road'])}, {city}, {pincode}"
        days_old = random.randint(60, 730)
        delivered_days_ago = random.randint(2, 90)
        ordered_days_ago = delivered_days_ago + random.randint(2, 7)

        _insert_customer(conn, cust_id, days_old=days_old)
        _insert_order(conn, order_id, cust_id, product, addr, pincode,
                      ordered_days_ago=ordered_days_ago,
                      delivered_days_ago=delivered_days_ago)

        # ~70% of these are historical resolved claims (for behavioural baseline)
        if random.random() < 0.7:
            reason, text = random.choice(LEGIT_REASONS)
            claim_id = f"claim_legit_{i:03d}"
            filed = (datetime.now() - timedelta(days=delivered_days_ago - 1)).isoformat(sep=" ", timespec="seconds")
            conn.execute(
                "INSERT OR REPLACE INTO claims (id, order_id, customer_id, reason_code, claim_text, score, decision, filed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 'APPROVE', ?)",
                (claim_id, order_id, cust_id, reason, text, random.randint(8, 28), filed),
            )


def seed_priya(conn: sqlite3.Connection) -> None:
    """Priya — borderline case driven by EXIF date fail (set up but claim not yet filed).

    Demo will submit the live claim via the form/demo panel.
    """
    cust_id = "cust_priya"
    order_id = "ord_priya_001"
    _insert_customer(conn, cust_id, days_old=420, return_count=1)
    _insert_order(
        conn, order_id, cust_id,
        ("Boat Airdopes 141 Earbuds", "electronics", 1499),
        "Flat 4B, 12 MG Road, Bengaluru, 560001", "560001",
        ordered_days_ago=5, delivered_days_ago=2,
    )


def seed_ring(conn: sqlite3.Connection) -> None:
    """4-account ring sharing one address + linguistic template.

    All 4 file claims with near-identical text on the same product variant.
    The 4th claim triggers the ring-cluster detection in fusion.
    """
    shared_address = "Flat 7C, 88 Brigade Road, Bengaluru, 560025"
    pincode = "560025"

    for idx in range(4):
        cust_id = f"cust_ring_{idx + 1:02d}"
        order_id = f"ord_ring_{idx + 1:02d}"
        days_old = random.randint(8, 22)  # all accounts created within ~3 weeks
        _insert_customer(conn, cust_id, days_old=days_old, return_count=0)
        _insert_order(
            conn, order_id, cust_id,
            random.choice([
                ("Apple AirPods 3rd Gen", "electronics", 18900),
                ("Samsung Galaxy M14 5G", "electronics", 13999),
                ("Nike Revolution 6 Running Shoes", "apparel", 3995),
                ("Philips HD9216 Air Fryer", "appliance", 7999),
            ]),
            shared_address, pincode,
            ordered_days_ago=random.randint(4, 9),
            delivered_days_ago=random.randint(1, 4),
        )

        # First 3 ring members have already filed claims (for the cluster to fire on the 4th)
        if idx < 3:
            claim_id = f"claim_ring_{idx + 1:02d}"
            filed = (datetime.now() - timedelta(hours=random.randint(2, 36))).isoformat(sep=" ", timespec="seconds")
            conn.execute(
                "INSERT OR REPLACE INTO claims (id, order_id, customer_id, reason_code, claim_text, score, decision, filed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (claim_id, order_id, cust_id, "damaged", RING_VARIATIONS[idx],
                 random.randint(40, 58), "BORDERLINE", filed),
            )
            # Also seed address_signatures for cluster lookup
            conn.execute(
                "INSERT INTO address_signatures (hash, customer_id, pincode, created_at) "
                "VALUES (?, ?, ?, ?)",
                (canonical_hash(shared_address), cust_id, pincode, filed),
            )


def seed_anjali_wrong_product(conn: sqlite3.Connection) -> None:
    """Anjali — wrong-product photo archetype (image-text fail).
    The photo file (when uploaded with 'wrong_product' in name) triggers the mock vision verdict.
    """
    cust_id = "cust_anjali"
    order_id = "ord_anjali_001"
    _insert_customer(conn, cust_id, days_old=300, return_count=0)
    _insert_order(
        conn, order_id, cust_id,
        ("Samsung Galaxy M14 5G", "electronics", 13999),
        "Plot 12, Sector 21, Pune, 411001", "411001",
        ordered_days_ago=6, delivered_days_ago=3,
    )


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main():
    print("Initialising database…")
    init_db()
    conn = get_db()

    print("Clearing prior seed data…")
    for table in ["claim_evidence", "claims", "evaluation_turns", "evaluation_sessions",
                  "ring_clusters", "address_signatures", "orders", "customers"]:
        conn.execute(f"DELETE FROM {table}")
    conn.commit()

    print("Seeding 30 legitimate customers + history…")
    seed_legit_history(conn, n=30)

    print("Seeding Maya demo order (ord_legit_000)…")
    seed_maya_demo(conn)

    print("Seeding Priya (EXIF-fail borderline scenario)…")
    seed_priya(conn)

    print("Seeding Anjali (wrong-product image-text scenario)…")
    seed_anjali_wrong_product(conn)

    print("Seeding 4-account ring at shared Bengaluru address…")
    seed_ring(conn)

    conn.commit()
    counts = {}
    for table in ["customers", "orders", "claims", "address_signatures"]:
        counts[table] = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
    conn.close()

    print("\n[OK] Seed complete:")
    for t, c in counts.items():
        print(f"  {t}: {c}")
    print("\nDemo order IDs:")
    print("  ord_priya_001 — Priya (EXIF-fail demo, upload photo with 'priya_exif_fail' in filename)")
    print("  ord_anjali_001 — Anjali (wrong-product demo, upload photo with 'wrong_product' in filename)")
    print("  ord_ring_04 — Ring 4th claim (submit to trigger ring-cluster detection)")
    print("  Any ord_legit_NNN — legit baseline (use for Maya scenario)")


if __name__ == "__main__":
    main()
