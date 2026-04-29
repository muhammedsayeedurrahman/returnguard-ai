CREATE TABLE IF NOT EXISTS customers (
  id TEXT PRIMARY KEY,
  email_hash TEXT,
  phone_hash TEXT,
  return_count_30d INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  customer_id TEXT REFERENCES customers(id),
  product_name TEXT,
  product_category TEXT,
  value_inr REAL,
  ordered_at TEXT,
  delivered_at TEXT,
  shipping_address TEXT,
  shipping_addr_hash TEXT,
  pincode TEXT,
  status TEXT DEFAULT 'delivered'
);

CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY,
  order_id TEXT REFERENCES orders(id),
  customer_id TEXT REFERENCES customers(id),
  reason_code TEXT,
  claim_text TEXT,
  photo_path TEXT,
  capture_method TEXT DEFAULT 'file_upload',
  fraud_context TEXT DEFAULT 'default',
  score INTEGER,
  decision TEXT,
  ring_cluster_id TEXT,
  filed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS claim_evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  claim_id TEXT REFERENCES claims(id),
  signal_name TEXT,
  verdict TEXT,
  detail TEXT,
  weight REAL,
  raw_json TEXT
);

CREATE TABLE IF NOT EXISTS address_signatures (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hash TEXT,
  customer_id TEXT,
  pincode TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ring_clusters (
  id TEXT PRIMARY KEY,
  customer_ids TEXT,
  shared_signal TEXT,
  exposure_inr REAL,
  status TEXT DEFAULT 'frozen',
  detected_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evaluation_sessions (
  id TEXT PRIMARY KEY,
  claim_id TEXT REFERENCES claims(id),
  initial_score INTEGER,
  final_score INTEGER,
  outcome TEXT,
  turn_count INTEGER DEFAULT 0,
  started_at TEXT DEFAULT (datetime('now')),
  ended_at TEXT
);

CREATE TABLE IF NOT EXISTS evaluation_turns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT REFERENCES evaluation_sessions(id),
  turn_number INTEGER,
  agent_message TEXT,
  customer_response TEXT,
  tool_called TEXT,
  tool_result TEXT,
  at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_addr_hash ON address_signatures(hash);
CREATE INDEX IF NOT EXISTS idx_claims_customer ON claims(customer_id);
CREATE INDEX IF NOT EXISTS idx_claims_decision ON claims(decision);

-- ─── Phase 4: Receipt verification ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS receipt_hashes (
  order_id        TEXT PRIMARY KEY,
  customer_id     TEXT,
  amount_inr      REAL,
  pdf_hash_sha256 TEXT NOT NULL,
  pdf_hash_md5    TEXT,
  issued_at       TEXT DEFAULT (datetime('now'))
);

-- ─── Phase 5: Friendly fraud (chargeback abuse) ───────────────────────
CREATE TABLE IF NOT EXISTS payment_risk_profiles (
  customer_id            TEXT PRIMARY KEY,
  risk_tier              TEXT NOT NULL DEFAULT 'LOW',
  claim_count_180d       INTEGER DEFAULT 0,
  chargeback_count       INTEGER DEFAULT 0,
  last_chargeback_at     TEXT,
  largest_chargeback_inr REAL DEFAULT 0,
  tier_set_at            TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chargeback_events (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id         TEXT,
  order_id            TEXT,
  payment_method      TEXT,
  amount_inr          REAL,
  chargeback_reason   TEXT,
  filed_at            TEXT DEFAULT (datetime('now')),
  resolution          TEXT
);

-- ─── Phase 6: Wardrobing ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS return_history (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id       TEXT,
  order_id          TEXT,
  claim_id          TEXT,
  product_category  TEXT,
  order_value_inr   REAL,
  days_held         INTEGER,
  wardrobing_score  INTEGER DEFAULT 0,
  filed_at          TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rh_customer_cat
  ON return_history(customer_id, product_category);

CREATE TABLE IF NOT EXISTS category_return_baselines (
  category                  TEXT PRIMARY KEY,
  median_return_gap_days    REAL,
  wardrobing_peak_months    TEXT,
  restocking_threshold_days INTEGER,
  high_value_threshold_inr  REAL
);

-- ─── Phase 7: INR (Item Not Received) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS shipment_deliveries (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id        TEXT,
  customer_id     TEXT,
  carrier         TEXT,
  shipment_id     TEXT,
  delivered_at    TEXT,
  gps_lat         REAL,
  gps_lng         REAL,
  otp_confirmed   INTEGER DEFAULT 0,
  scan_location   TEXT,
  created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS engagement_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id TEXT,
  order_id    TEXT,
  event_type  TEXT,
  occurred_at TEXT,
  created_at  TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_engagement_order ON engagement_events(order_id);

CREATE TABLE IF NOT EXISTS pincode_intelligence (
  pincode      TEXT PRIMARY KEY,
  rto_rate     REAL,
  inr_rate     REAL,
  tier         TEXT DEFAULT 'TIER2'
);

-- ─── Phase 8: Human review labels ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS review_labels (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  claim_id    TEXT,
  reviewer_id TEXT,
  outcome     TEXT,
  notes       TEXT,
  created_at  TEXT DEFAULT (datetime('now'))
);
