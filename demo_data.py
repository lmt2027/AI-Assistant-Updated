"""Deterministic, synthetic security event data for safe demonstrations."""
from datetime import datetime, timedelta
import random


def generate_demo_events(now=None):
    rng = random.Random(440)
    now = (now or datetime.now()).replace(microsecond=0)
    accounts = ["owner@sample-business.test", "sales@sample-business.test", "support@sample-business.test", "admin@sample-business.test"]
    events = []
    for day in range(14, -1, -1):
        for i in range(rng.randint(5, 10)):
            timestamp = now - timedelta(days=day, hours=rng.randint(0, 11), minutes=rng.randint(0, 59))
            account = rng.choice(accounts)
            outcome = rng.choices(["success", "failure"], weights=[9, 1])[0]
            events.append({"event_time": timestamp.strftime("%Y-%m-%d %H:%M:%S"), "event_type": "login", "account": account,
                           "source_ip": f"192.0.2.{rng.randint(10, 90)}", "outcome": outcome, "details": "Synthetic sign-in event"})
    # A concentrated series of failed attempts on the demo admin account.
    for i in range(9):
        timestamp = now - timedelta(minutes=70-i*4)
        events.append({"event_time": timestamp.strftime("%Y-%m-%d %H:%M:%S"), "event_type": "login", "account": "admin@sample-business.test",
                       "source_ip": "198.51.100.77", "outcome": "failure", "details": "Synthetic repeated failed sign-in"})
    # Other event types for dashboard and AI context.
    for kind, outcome, detail in [
        ("software_update", "pending", "Demo accounting software update pending"),
        ("account_created", "success", "Demo employee account created; authorization not yet confirmed"),
        ("device_scan", "success", "Demo device scan completed"),
    ]:
        events.append({"event_time": (now-timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), "event_type": kind,
                       "account": "system@sample-business.test", "source_ip": "203.0.113.20", "outcome": outcome, "details": detail})
    return sorted(events, key=lambda x:x["event_time"])
