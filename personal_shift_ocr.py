import cv2
import logging
import pytesseract
from datetime import datetime

from shift_geometry import date_for_tile, detect_tiles, find_row_anchors, personal_shift_region

# Personal assignments use short schedule labels (for example PL, L, and E).
# A is reserved for availability and I is a recurring OCR artefact from grey A
# tiles, so neither can create a booked observation.
NON_ASSIGNMENT_LABELS = {"A", "I"}
KNOWN_ASSIGNMENT_LABELS = {"L", "E", "P", "PL", "LP", "EL", "LE", "EP", "PE"}
ASSIGNMENT_WORD_PREFIXES = ("TRAIN", "SHIFT", "WORK")


def _normalise_tile_text(text):
    return "".join(character for character in text.upper() if character.isalpha())


def _personal_tile_variants(gray):
    """Build high-contrast OCR variants for pastel personal-row tiles."""
    scaled = cv2.resize(gray, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(scaled)
    _, otsu = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, otsu_clahe = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    normalized = cv2.normalize(clahe, None, 0, 255, cv2.NORM_MINMAX)
    _, hard = cv2.threshold(normalized, 180, 255, cv2.THRESH_BINARY)
    return (
        scaled,
        clahe,
        otsu,
        cv2.bitwise_not(otsu),
        otsu_clahe,
        cv2.bitwise_not(otsu_clahe),
        hard,
        cv2.bitwise_not(hard),
    )


def _personal_tile_readings(image, rect):
    x, y, width, height = rect
    # The Teams assignment/availability code appears at the left of the tile.
    crop = image[y:y + height, x:x + max(1, int(width * 0.70))]
    if crop.size == 0:
        return []
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    readings = []
    seen = set()
    for image_variant in _personal_tile_variants(gray):
        for psm in (6, 7, 8, 10):
            for use_whitelist in (True, False):
                config = f"--psm {psm}"
                if use_whitelist:
                    config += " -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                text = pytesseract.image_to_string(image_variant, config=config).strip().upper()
                if text and text not in seen:
                    seen.add(text)
                    readings.append(text)
    return readings


def _is_availability_tile(text):
    """Only a personal-row tile explicitly beginning with A means availability."""
    normalized = _normalise_tile_text(text)
    return normalized.startswith("A")


def _assignment_label(text):
    """Return a cleaned assignment label when OCR yields positive evidence."""
    normalized = _normalise_tile_text(text)
    if not normalized or normalized in NON_ASSIGNMENT_LABELS:
        return None
    if normalized.startswith(ASSIGNMENT_WORD_PREFIXES):
        return normalized
    if normalized in KNOWN_ASSIGNMENT_LABELS:
        return normalized
    # Short multi-letter codes that are not pure I-noise remain accepted.
    if 2 <= len(normalized) <= 3 and set(normalized) != {"I"}:
        return normalized
    return None


def _classify_personal_tile(readings):
    """Classify only positively identified personal assignments as booked.

    Weak availability OCR artefacts (stray A) must not override clearer L/E/P
    assignment labels collected from alternate preprocessing passes.
    """
    if not readings:
        return "unknown"

    availability_votes = 0
    assignment_votes = 0

    for reading in readings:
        normalized = _normalise_tile_text(reading)
        if not normalized:
            continue
        if _is_availability_tile(reading):
            availability_votes += 1
            continue
        if _assignment_label(reading):
            assignment_votes += 1

    # Any positive assignment label wins. Multiple A/I preprocessing artefacts
    # must not outvote a real L/E/P reading from a booked personal tile.
    if assignment_votes > 0:
        return "assignment"
    if availability_votes > 0:
        return "availability"
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
        for reading in readings:
            if _assignment_label(reading):
                text = reading
                break
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
            logging.warning("[PersonalShifts] Ignoring assignment tile outside calendar columns: %s", rect)
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
    logging.info(
        "[PersonalShifts] Geometry detector found %d assignment/training tile(s); ignored %d unknown tile(s)",
        len(result),
        unknown_count,
    )
    return result
