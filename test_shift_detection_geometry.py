import os
import unittest

import cv2
import numpy as np

from personal_shift_ocr import _classify_personal_tile, _is_availability_tile
from personal_shift_ocr import detect_personal_assignments
from row_shift_ocr import detect_open_shifts_by_row
from shift_geometry import date_for_tile, detect_tiles
from ocr_processing import _parse_month_year_text


class ShiftGeometryTests(unittest.TestCase):
    def setUp(self):
        self.anchors = {
            "open": {"x": 124, "y": 344, "width": 82, "height": 21, "confidence": 1.0},
            "personal": {"x": 126, "y": 490, "width": 73, "height": 20, "confidence": 1.0},
        }

    def test_calendar_mapping_uses_header_aligned_first_column(self):
        # In the retained August 2026 capture, the blue PL tile starts at x=410
        # and belongs to Tuesday 4 August, not the following column.
        self.assertEqual(
            date_for_tile((410, 490, 46, 60), self.anchors, 1920, 2026, 8),
            "2026-08-04",
        )

    def test_month_label_parser_finds_month_after_weekday_and_day(self):
        self.assertEqual(_parse_month_year_text("Tuesday, 3 Nov 2026 Y"), (11, 2026))

    def test_month_label_parser_tolerates_single_character_ocr_errors(self):
        self.assertEqual(_parse_month_year_text("Yctober 2026 V"), (10, 2026))
        self.assertEqual(_parse_month_year_text("Jecember 2026 Y"), (12, 2026))

    def test_month_label_parser_rejects_unverifiable_label(self):
        self.assertIsNone(_parse_month_year_text("Xqzwv 2026 V"))
        self.assertIsNone(_parse_month_year_text(""))

    def test_late_month_columns_map_september_26(self):
        # 30-day September: day 26 sits near the right of a 1920px capture.
        self.assertEqual(
            date_for_tile((1640, 490, 46, 60), self.anchors, 1920, 2026, 9),
            "2026-09-26",
        )
        # A tile whose center lands just past the last column still belongs to
        # the final day rather than being discarded.
        self.assertEqual(
            date_for_tile((1900, 490, 40, 60), self.anchors, 1920, 2026, 9),
            "2026-09-30",
        )

    def test_color_neutral_tile_detection_keeps_different_tile_colours(self):
        image = np.full((120, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(image, (40, 20), (80, 70), (255, 220, 180), -1)  # blue-ish BGR
        cv2.rectangle(image, (120, 20), (160, 70), (180, 240, 255), -1)  # orange-ish BGR
        cv2.rectangle(image, (200, 20), (238, 70), (230, 230, 230), -1)  # grey BGR
        tiles = detect_tiles(image, 10, 100)
        self.assertEqual(len(tiles), 3)

    def test_compact_right_edge_tiles_are_kept(self):
        image = np.full((120, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(image, (200, 20), (239, 70), (180, 240, 255), -1)
        tiles = detect_tiles(image, 10, 100)
        self.assertEqual(len(tiles), 1)
        self.assertGreaterEqual(tiles[0][0] + tiles[0][2], 240)

    def test_only_explicit_a_code_means_personal_availability(self):
        self.assertTrue(_is_availability_tile(": A..."))
        self.assertTrue(_is_availability_tile("A"))
        self.assertFalse(_is_availability_tile(": PL."))
        self.assertFalse(_is_availability_tile(""))

    def test_personal_assignment_requires_positive_evidence(self):
        self.assertEqual(_classify_personal_tile([": A..."]), "availability")
        self.assertEqual(_classify_personal_tile([": PL."]), "assignment")
        self.assertEqual(_classify_personal_tile(["TRAINING"]), "assignment")
        self.assertEqual(_classify_personal_tile(["L..."]), "assignment")
        self.assertEqual(_classify_personal_tile(["E..."]), "assignment")
        self.assertEqual(_classify_personal_tile(["P"]), "assignment")
        self.assertEqual(_classify_personal_tile([""]), "unknown")
        self.assertEqual(_classify_personal_tile(["I"]), "unknown")
        self.assertEqual(_classify_personal_tile(["*"]), "unknown")
        self.assertEqual(_classify_personal_tile([]), "unknown")
        self.assertEqual(_classify_personal_tile(["UNKNOWN"]), "unknown")
        # Spurious A noise must not override clearer assignment labels.
        self.assertEqual(_classify_personal_tile(["A", "L", "I", '"']), "assignment")
        self.assertEqual(_classify_personal_tile(["I", "E", "S", "A"]), "assignment")
        self.assertEqual(_classify_personal_tile(["A", "A", "A", "L"]), "assignment")
        self.assertEqual(_classify_personal_tile(["A", "I", "*"]), "availability")

    def test_retained_august_capture_detects_training_and_all_open_rows(self):
        candidates = [
            "screenshots/1-shifts_screenshot_20260724_072541.png",
            "screenshots/shifts_screenshot_20260731_212330.png",
        ]
        screenshot = next((path for path in candidates if os.path.exists(path)), None)
        if screenshot is None:
            self.skipTest("Retained August screenshot is unavailable")
        image = cv2.imread(screenshot)
        open_shifts = detect_open_shifts_by_row(image, screenshot, 2026, 8)
        personal_assignments = detect_personal_assignments(image, screenshot, 2026, 8)
        for date_str in ("2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20"):
            self.assertIn(date_str, open_shifts)
        # Current August capture: PL/P on 4th, L on 8th, E on 15th; A on 1/22/29.
        self.assertIn("2026-08-04", personal_assignments)
        self.assertEqual(
            personal_assignments["2026-08-04"]["evidence"]["classification"],
            "positive-assignment-evidence",
        )
        if "20260731" in screenshot:
            self.assertIn("2026-08-08", personal_assignments)
            self.assertIn("2026-08-15", personal_assignments)
            self.assertNotIn("2026-08-01", personal_assignments)
            self.assertNotIn("2026-08-22", personal_assignments)
            self.assertNotIn("2026-08-29", personal_assignments)


if __name__ == "__main__":
    unittest.main()
