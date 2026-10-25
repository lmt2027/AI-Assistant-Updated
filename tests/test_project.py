import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from ai_assistant import build_database_context
from event_detection import analyze_database_events
from securitychecker import check_failed_logins


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = database.DB_PATH
        database.DB_PATH = Path(self.temp.name) / "test.db"
        database.create_database()
        database.create_event_tables()

    def tearDown(self):
        database.DB_PATH = self.original
        self.temp.cleanup()

    def test_seed_once(self):
        self.assertGreater(database.seed_security_events(), 100)
        self.assertEqual(database.seed_security_events(), 0)

    def test_detection_idempotent(self):
        database.seed_security_events()
        first = analyze_database_events()
        second = analyze_database_events()
        self.assertTrue(first)
        self.assertEqual(second, [])

    def test_manual_checker(self):
        self.assertIsNone(check_failed_logins(4))
        self.assertEqual(check_failed_logins(9)["severity"], "High")

    def test_ai_context_mentions_synthetic(self):
        database.seed_security_events()
        context = build_database_context()
        self.assertIn("synthetic", context.lower())
        self.assertIn("login", context)

if __name__ == "__main__":
    unittest.main()
