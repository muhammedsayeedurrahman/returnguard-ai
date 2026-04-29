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
