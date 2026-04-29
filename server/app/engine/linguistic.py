"""Signal B1: Linguistic fingerprint via TF-IDF cosine similarity.

Catches coordinated rings using shared claim-text templates. Runs on
every submission against the last 90 days of claim text in the DB.
"""
from __future__ import annotations
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


SIMILARITY_THRESHOLD = 0.65


def score(claim_text: str, customer_id: str, conn: sqlite3.Connection) -> dict:
    weight = 0.20
    if not claim_text or len(claim_text.strip()) < 10:
        return {
            "signal": "linguistic",
            "verdict": "SKIP",
            "score": 0,
            "weight": weight,
            "detail": "Claim text too short to fingerprint",
            "raw": {},
        }

    rows = conn.execute(
        "SELECT id, customer_id, claim_text FROM claims "
        "WHERE customer_id != ? AND claim_text IS NOT NULL "
        "AND length(claim_text) > 10 "
        "AND filed_at >= datetime('now', '-90 days') "
        "ORDER BY filed_at DESC LIMIT 200",
        (customer_id,),
    ).fetchall()

    if not rows:
        return {
            "signal": "linguistic",
            "verdict": "OK",
            "score": 0,
            "weight": weight,
            "detail": "No comparable claims in last 90 days",
            "raw": {},
        }

    corpus = [r["claim_text"] for r in rows] + [claim_text]
    try:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vec.fit_transform(corpus)
        sims = cosine_similarity(matrix[-1], matrix[:-1])[0]
    except ValueError:
        return {
            "signal": "linguistic",
            "verdict": "SKIP",
            "score": 0,
            "weight": weight,
            "detail": "Vectorisation failed (empty vocabulary)",
            "raw": {},
        }

    above = [(rows[i]["customer_id"], rows[i]["id"], float(sims[i]))
             for i in range(len(rows)) if sims[i] >= SIMILARITY_THRESHOLD]

    if len(above) >= 2:
        top = sorted(above, key=lambda x: -x[2])[:5]
        match_customers = list({c for c, _, _ in top})
        return {
            "signal": "linguistic",
            "verdict": "FAIL",
            "score": 80,
            "weight": weight,
            "detail": f"Claim text {top[0][2]:.2f} cosine-similar to {len(match_customers)} other customers — possible ring template",
            "raw": {"matches": top, "match_customers": match_customers},
        }
    if len(above) == 1:
        return {
            "signal": "linguistic",
            "verdict": "WARN",
            "score": 35,
            "weight": weight,
            "detail": f"Claim text {above[0][2]:.2f} cosine-similar to one other customer",
            "raw": {"matches": above},
        }

    return {
        "signal": "linguistic",
        "verdict": "OK",
        "score": 0,
        "weight": weight,
        "detail": f"Linguistic fingerprint unique (top similarity {float(np.max(sims)):.2f})",
        "raw": {"top_sim": float(np.max(sims))},
    }
