import cv2
import logging
import pytesseract
from datetime import datetime

from shift_geometry import date_for_tile, detect_tiles, find_row_anchors, personal_shift_region

ASSIGNMENT_PREFIXES = ("PL", "TRN", "TR", "SH", "WK", "WORK")


def _normalise_tile_text(text):
    return "".join(character for character in text.upper() if character.isalpha())


def _personal_tile_readings(image, rect):
    x, y, width, height = rect
    # The Teams assignment/availability code appears at the left of the tile.
    crop = image[y:y + height, x:x + max(1, int(width * 0.60))]
    if crop.size == 0:
        return []
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    _, threshold = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    readings = []
    for image_variant in (scaled, threshold, cv2.bitwise_not(threshold)):
        for psm in (7, 8):
            text = pytesseract.image_to_string(image_variant, config=f"--psm {psm}").strip().upper()
            if text and text not in readings:
                readings.append(text)
    return readings


def _is_availability_tile(text):
    """Only a personal-row tile explicitly beginning with A means availability."""
    normalized = _normalise_tile_text(text)
    return normalized.startswith("A")


def _classify_personal_tile(readings):
    """Classify only positively identified personal assignments as booked."""
    if any(_is_availability_tile(reading) for reading in readings):
        return "availability"
    for reading in readings:
        normalized = _normalise_tile_text(reading)
        if normalized.startswith(ASSIGNMENT_PREFIXES):
            return "assignment"
    return "unknown"


def detect_personal_assignments(image, image_path, year, month):
    """Detect booked/training assignments in the personal row without using tile color."""
    anchors = find_row_anchors(image)
    if anchors is None:
        logging.warning("[PersonalShifts] Could not locate the personal row anchor.")
        return {}

    result = {}
    unknown_count = 0
    debug_image = image.copy()
    for index, rect in enumerate(detect_tiles(image, *personal_shift_region(anchors, image.shape[0]))):
        readings = _personal_tile_readings(image, rect)
        text = readings[0] if readings else ""
        classification = _classify_personal_tile(readings)
        x, y, width, height = rect
        if classification == "availability":
            cv2.rectangle(debug_image, (x, y), (x + width, y + height), (128, 128, 128), 2)
            logging.info("[PersonalShifts] Ignoring availability tile %s at %s", text or "A", rect)
            continue
        if classification != "assignment":
            unknown_count += 1
            cv2.rectangle(debug_image, (x, y), (x + width, y + height), (0, 215, 255), 2)
            logging.warning(
                "[PersonalShifts] Ignoring unknown personal-row tile at %s; OCR readings=%s",
                rect,
                readings or ["<empty>"],
            )
            continue
        date_str = date_for_tile(rect, anchors, image.shape[1], year, month)
        if date_str is None:
            continue
        cv2.rectangle(debug_image, (x, y), (x + width, y + height), (255, 0, 0), 2)
        result[date_str] = {
            "type": "booked",
            "coords": rect,
            "date": datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %b"),
            "day": int(date_str[-2:]),
            "month": month,
            "year": year,
            "evidence": {
                "detector": "personal-row-geometry",
                "personal_tile_text": text,
                "personal_tile_readings": readings,
                "classification": "positive-assignment-evidence",
                "anchor_confidence": anchors["personal"]["confidence"],
            },
        }

    cv2.imwrite(image_path.replace(".png", "_personal_row_geometry.png"), debug_image)
    logging.info("[PersonalShifts] Geometry detector found %d assignment/training tile(s); ignored %d unknown tile(s)", len(result), unknown_count)
    return result
