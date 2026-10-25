"""SQLite persistence for the AI Security Assistant demonstration."""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "security_assistant.db"


def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS reviews (
            alert_id TEXT PRIMARY KEY,
            alert_name TEXT NOT NULL,
            reviewed_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS detected_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            severity TEXT NOT NULL,
            explanation TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            failed_attempts INTEGER NOT NULL,
            detected_at TEXT NOT NULL
        )""")


def save_review(alert_id, alert_name):
    """Return True only if this review is newly inserted."""
    with connect() as db:
        result = db.execute(
            "INSERT OR IGNORE INTO reviews (alert_id, alert_name, reviewed_at) VALUES (?, ?, ?)",
            (str(alert_id), alert_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        return result.rowcount > 0


def get_reviews():
    with connect() as db:
        return [tuple(row) for row in db.execute(
            "SELECT alert_id, alert_name, reviewed_at FROM reviews ORDER BY reviewed_at DESC"
        ).fetchall()]


def save_detected_alert(alert):
    with connect() as db:
        cursor = db.execute("""INSERT INTO detected_alerts
            (title, severity, explanation, recommendation, failed_attempts, detected_at)
            VALUES (?, ?, ?, ?, ?, ?)""", (
                alert["title"], alert["severity"], alert["explanation"],
                alert["recommendation"], alert["failed_attempts"],
                alert.get("detected_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ))
        return cursor.lastrowid


def get_detected_alerts():
    with connect() as db:
        return [tuple(row) for row in db.execute("""SELECT id, title, severity,
            explanation, recommendation, failed_attempts, detected_at
            FROM detected_alerts ORDER BY id DESC""").fetchall()]


def seed_demo_alerts():
    """Seed sample records only when the detected-alert table is empty."""
    if get_detected_alerts():
        return False
    examples = [
        ("Someone may be trying to guess a password", "High",
         "Several failed sign-in attempts were recorded for an employee account. This could indicate someone trying to guess a password.",
         "Check the account, reset its password if needed, and turn on multi-factor authentication.", 9),
        ("Unusual sign-in activity", "Medium",
         "A demonstration sign-in pattern appears unusual. Confirm whether the employee recognizes the activity.",
         "Ask the employee to verify the sign-in and review account access.", 4),
        ("A program needs a security update", "Medium",
         "This sample alert represents software that may need an important update.",
         "Check the software vendor's official update instructions.", 0),
        ("New employee account added", "Low",
         "This sample alert represents a new employee account being created.",
         "Confirm that the new account was authorized.", 0),
    ]
    for index, (title, severity, explanation, recommendation, attempts) in enumerate(examples):
        save_detected_alert({
            "title": title, "severity": severity, "explanation": explanation,
            "recommendation": recommendation, "failed_attempts": attempts,
            "detected_at": (datetime.now() - timedelta(hours=index * 3)).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return True


# --- Synthetic event database support (additive migration) ---
def create_event_tables():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_time TEXT NOT NULL,
            event_type TEXT NOT NULL,
            account TEXT NOT NULL,
            source_ip TEXT NOT NULL,
            outcome TEXT NOT NULL,
            details TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS detection_keys (
            detection_key TEXT PRIMARY KEY
        )""")


def get_security_events(limit=500):
    limit = max(1, min(int(limit), 2000))
    with connect() as db:
        return [tuple(r) for r in db.execute(
            "SELECT id,event_time,event_type,account,source_ip,outcome,details "
            "FROM security_events ORDER BY event_time DESC,id DESC LIMIT ?", (limit,)
        ).fetchall()]


def seed_security_events():
    """Seed once; do not overwrite existing user records."""
    from demo_data import generate_demo_events
    create_event_tables()
    with connect() as db:
        existing = db.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
        if existing:
            return 0
        rows = generate_demo_events()
        db.executemany("""INSERT INTO security_events
            (event_time,event_type,account,source_ip,outcome,details)
            VALUES (:event_time,:event_type,:account,:source_ip,:outcome,:details)""", rows)
        return len(rows)


def record_detection_key(key):
    with connect() as db:
        cursor = db.execute("INSERT OR IGNORE INTO detection_keys(detection_key) VALUES (?)", (key,))
        return cursor.rowcount == 1
