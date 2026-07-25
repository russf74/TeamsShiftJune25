import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import database


class ShiftLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "shifts.db")
        self.db_path_patch = patch.object(database, "get_db_path", return_value=self.db_path)
        self.db_path_patch.start()
        database.init_db()

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def fetchone(self, query, params=()):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(query, params).fetchone()
        finally:
            conn.close()

    def test_booked_shift_requires_two_healthy_observations(self):
        date_str = "2030-01-15"

        first = database.reconcile_month_observations(2030, 1, set(), {date_str})
        self.assertEqual(first["new_bookings"], [])
        self.assertEqual(self.fetchone("SELECT detection_count FROM booked_shift_candidates WHERE date = ?", (date_str,))[0], 1)
        self.assertIsNone(self.fetchone("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,)))

        second = database.reconcile_month_observations(2030, 1, set(), {date_str})
        self.assertEqual(second["new_bookings"], [date_str])
        row = self.fetchone("SELECT email_status, missing_scan_count FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))
        self.assertEqual(row, ("pending", 0))
        self.assertIsNone(self.fetchone("SELECT 1 FROM booked_shift_candidates WHERE date = ?", (date_str,)))

    def test_confirmed_booking_survives_one_healthy_miss_then_expires(self):
        date_str = "2030-02-10"
        database.reconcile_month_observations(2030, 2, set(), {date_str})
        database.reconcile_month_observations(2030, 2, set(), {date_str})

        database.reconcile_month_observations(2030, 2, set(), set())
        self.assertEqual(self.fetchone("SELECT missing_scan_count FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,))[0], 1)

        database.reconcile_month_observations(2030, 2, set(), set())
        self.assertIsNone(self.fetchone("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,)))

    def test_healthy_empty_scan_removes_open_shift(self):
        date_str = "2030-03-12"
        database.reconcile_month_observations(2030, 3, {date_str}, set())
        self.assertIsNotNone(self.fetchone("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'open'", (date_str,)))

        database.reconcile_month_observations(2030, 3, set(), set())
        self.assertIsNone(self.fetchone("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'open'", (date_str,)))

    def test_unhealthy_scan_never_removes_existing_shift(self):
        date_str = "2030-04-02"
        database.reconcile_month_observations(2030, 4, {date_str}, set())

        database.reconcile_month_observations(2030, 4, set(), set(), scan_healthy=False)
        self.assertIsNotNone(self.fetchone("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'open'", (date_str,)))

    def test_reappearing_open_shift_preserves_alert_history(self):
        date_str = "2030-05-21"
        database.reconcile_month_observations(2030, 5, {date_str}, set())
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("UPDATE shifts SET alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
            conn.execute("UPDATE shift_history SET last_alerted = 1 WHERE date = ? AND shift_type = 'open'", (date_str,))
            conn.commit()
        finally:
            conn.close()

        database.reconcile_month_observations(2030, 5, set(), set())
        database.reconcile_month_observations(2030, 5, {date_str}, set())
        self.assertEqual(self.fetchone("SELECT alerted FROM shifts WHERE date = ? AND shift_type = 'open'", (date_str,))[0], 1)

    def test_verified_false_booking_is_removed_and_audited(self):
        date_str = "2030-06-14"
        database.reconcile_month_observations(2030, 6, set(), {date_str})
        database.reconcile_month_observations(2030, 6, set(), {date_str})
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("UPDATE shifts SET confirmed_email_sent = 1, email_status = 'sent' WHERE date = ? AND shift_type = 'booked'", (date_str,))
            conn.execute("UPDATE shift_history SET confirmed_email_sent = 1 WHERE date = ? AND shift_type = 'booked'", (date_str,))
            conn.commit()
        finally:
            conn.close()

        corrected = database.remove_incorrect_bookings([date_str], "test correction")
        self.assertEqual(corrected, [date_str])
        self.assertIsNone(self.fetchone("SELECT 1 FROM shifts WHERE date = ? AND shift_type = 'booked'", (date_str,)))
        self.assertEqual(self.fetchone("SELECT confirmed_email_sent FROM shift_history WHERE date = ? AND shift_type = 'booked'", (date_str,))[0], 0)
        self.assertEqual(self.fetchone("SELECT reason FROM shift_corrections WHERE date = ?", (date_str,))[0], "test correction")


if __name__ == "__main__":
    unittest.main()
