"""Transparent detection rules applied to SQLite demo events."""
from datetime import datetime, timedelta
from database import get_security_events, save_detected_alert, record_detection_key


def analyze_database_events():
    """Check failed sign-ins over 24h; save one warning per account per day."""
    cutoff = datetime.now() - timedelta(hours=24)
    grouped = {}
    for event in get_security_events(limit=2000):
        event_id, event_time, event_type, account, source_ip, outcome, details = event
        try:
            when = datetime.fromisoformat(event_time)
        except ValueError:
            continue
        if when >= cutoff and event_type == "login" and outcome == "failure":
            grouped.setdefault(account, []).append(event)
    created = []
    for account, events in grouped.items():
        if len(events) < 5:
            continue
        key = f"failed-login:{account}:{datetime.now().date().isoformat()}"
        if not record_detection_key(key):
            continue
        attempts = len(events)
        severity = "High" if attempts >= 8 else "Medium"
        alert = {
            "title": "Possible Password Attack",
            "severity": severity,
            "explanation": f"The sample event database contains {attempts} failed sign-ins for {account} in the last 24 hours.",
            "recommendation": "Confirm whether these attempts are expected. If suspicious, reset credentials, review access and enable multi-factor authentication.",
            "failed_attempts": attempts,
        }
        alert_id = save_detected_alert(alert)
        created.append((alert_id, account, attempts))
    return created
