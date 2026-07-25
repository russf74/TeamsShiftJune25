import os
import unittest

import cv2
import numpy as np

from personal_shift_ocr import _classify_personal_tile, _is_availability_tile
from personal_shift_ocr import detect_personal_assignments
from row_shift_ocr import detect_open_shifts_by_row
from shift_geometry import date_for_tile, detect_tiles


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

    def test_color_neutral_tile_detection_keeps_different_tile_colours(self):
        image = np.full((120, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(image, (40, 20), (80, 70), (255, 220, 180), -1)  # blue-ish BGR
        cv2.rectangle(image, (120, 20), (160, 70), (180, 240, 255), -1)  # orange-ish BGR
        cv2.rectangle(image, (200, 20), (238, 70), (230, 230, 230), -1)  # grey BGR
        tiles = detect_tiles(image, 10, 100)
        self.assertEqual(len(tiles), 3)

    def test_only_explicit_a_code_means_personal_availability(self):
        self.assertTrue(_is_availability_tile(": A..."))
        self.assertTrue(_is_availability_tile("A"))
        self.assertFalse(_is_availability_tile(": PL."))
        self.assertFalse(_is_availability_tile(""))

    def test_personal_assignment_requires_positive_evidence(self):
        self.assertEqual(_classify_personal_tile([": A..."]), "availability")
        self.assertEqual(_classify_personal_tile([": PL."]), "assignment")
        self.assertEqual(_classify_personal_tile(["TRAINING"]), "assignment")
        self.assertEqual(_classify_personal_tile([""]), "unknown")
        self.assertEqual(_classify_personal_tile([]), "unknown")
        self.assertEqual(_classify_personal_tile(["UNKNOWN"]), "unknown")

    def test_retained_august_capture_detects_training_and_all_open_rows(self):
        screenshot = "screenshots/1-shifts_screenshot_20260724_072541.png"
        if not os.path.exists(screenshot):
            self.skipTest("Retained August screenshot is unavailable")
        image = cv2.imread(screenshot)
        open_shifts = detect_open_shifts_by_row(image, screenshot, 2026, 8)
        personal_assignments = detect_personal_assignments(image, screenshot, 2026, 8)
        for date_str in ("2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20"):
            self.assertIn(date_str, open_shifts)
        self.assertIn("2026-08-04", personal_assignments)
        self.assertEqual(personal_assignments["2026-08-04"]["evidence"]["classification"], "positive-assignment-evidence")


if __name__ == "__main__":
    unittest.main()
