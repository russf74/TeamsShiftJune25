import calendar
import cv2
import numpy as np
import os


OPEN_ROW_TEMPLATE = "openshifts.png"
PERSONAL_ROW_TEMPLATE = "bookedshifts.png"
MIN_TEMPLATE_CONFIDENCE = 0.85


def _as_bgr(image):
    if image is None:
        return None
    if len(image.shape) == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image


def find_row_anchors(image, template_dir=None):
    """Locate the Open shifts and personal-row labels in a Teams screenshot."""
    template_dir = template_dir or os.path.dirname(__file__)
    search_image = _as_bgr(image)
    anchors = {}
    for name, filename in (("open", OPEN_ROW_TEMPLATE), ("personal", PERSONAL_ROW_TEMPLATE)):
        template = _as_bgr(cv2.imread(os.path.join(template_dir, filename), cv2.IMREAD_UNCHANGED))
        if template is None or search_image is None:
            return None
        result = cv2.matchTemplate(search_image, template, cv2.TM_CCOEFF_NORMED)
        _, confidence, _, location = cv2.minMaxLoc(result)
        if confidence < MIN_TEMPLATE_CONFIDENCE:
            return None
        anchors[name] = {
            "x": location[0],
            "y": location[1],
            "width": template.shape[1],
            "height": template.shape[0],
            "confidence": confidence,
        }
    if anchors["personal"]["y"] <= anchors["open"]["y"]:
        return None
    return anchors


def open_shift_region(anchors):
    """Return the tile area above the personal row; no tile color is considered."""
    return (
        anchors["open"]["y"],
        anchors["personal"]["y"],
    )


def personal_shift_region(anchors, image_height):
    """Return the personal-row tile area, excluding the rows above it."""
    y1 = anchors["personal"]["y"]
    return y1, min(image_height, y1 + 100)


def calendar_grid(anchors, image_width, days_in_month):
    """Derive the first day column and equal column width from the row-label anchor."""
    # The row label begins around x=124 in the standard 1920px capture; the first
    # day column begins at x=244. Deriving from the anchor keeps that 120px label
    # gutter stable across screenshots while avoiding the former one-day offset.
    grid_left = anchors["open"]["x"] + 120
    grid_left = max(0, min(grid_left, image_width - days_in_month))
    return grid_left, (image_width - grid_left) / float(days_in_month)


def date_for_tile(rect, anchors, image_width, year, month):
    """Map a tile center to the Teams month-view date column."""
    x, _, width, _ = rect
    days_in_month = calendar.monthrange(year, month)[1]
    grid_left, column_width = calendar_grid(anchors, image_width, days_in_month)
    day = int((x + width / 2 - grid_left) // column_width) + 1
    if not 1 <= day <= days_in_month:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def detect_tiles(image, y1, y2, min_width=18, min_height=18):
    """Find rectangular, non-background tiles in a row range without color classification."""
    height, width = image.shape[:2]
    y1 = max(0, y1)
    y2 = min(height, y2)
    if y2 <= y1:
        return []
    region = image[y1:y2]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    # Teams tile backgrounds are visibly darker than the white calendar canvas.
    # Grid lines may form border-connected contours and are excluded below.
    mask = cv2.inRange(gray, 0, 248)
    # Remove one-pixel calendar grid lines before contour extraction. Tile fills
    # remain intact regardless of whether they are orange, blue, purple, or grey.
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)),
    )
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    tiles = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if x == 0 or x + w >= width or w > width * 0.5 or h > (y2 - y1) * 0.9:
            continue
        if w < min_width or h < min_height:
            continue
        if w > 90 or h > 90:
            continue
        fill_ratio = cv2.contourArea(contour) / float(w * h)
        if fill_ratio < 0.20:
            continue
        tiles.append((x, y + y1, w, h))
    return sorted(tiles, key=lambda rect: (rect[1], rect[0]))
