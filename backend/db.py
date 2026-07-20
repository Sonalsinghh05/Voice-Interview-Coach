"""
db.py
Lightweight SQLite session history tracking — no external DB needed.
"""

import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "sessions.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            question_id TEXT,
            question TEXT,
            role TEXT,
            transcript TEXT,
            words_per_minute REAL,
            score INTEGER,
            feedback_json TEXT,
            created_at REAL
        )
        """
    )
    conn.commit()
    conn.close()


def save_attempt(session_id, question_id, question, role, transcript, wpm, score, feedback_json):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO attempts
        (session_id, question_id, question, role, transcript, words_per_minute, score, feedback_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (session_id, question_id, question, role, transcript, wpm, score, feedback_json, time.time()),
    )
    conn.commit()
    conn.close()


def get_session_history(session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM attempts WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_session_summary(session_id):
    history = get_session_history(session_id)
    scores = [h["score"] for h in history if h["score"] is not None]
    return {
        "total_questions": len(history),
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
        "average_wpm": round(
            sum(h["words_per_minute"] for h in history if h["words_per_minute"]) / len(history), 1
        )
        if history
        else None,
    }
