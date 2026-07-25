import cv2
import logging
from datetime import datetime

from shift_geometry import date_for_tile, detect_tiles, find_row_anchors, open_shift_region


def detect_open_shifts_by_row(image, image_path, year, month):
    """Detect every shift tile above the personal row, independent of tile color."""
    anchors = find_row_anchors(image)
    if anchors is None:
        logging.warning("[OpenShifts] Could not locate both row anchors; ignoring this month rather than guessing.")
        return {}

    tiles = detect_tiles(image, *open_shift_region(anchors))
    result = {}
    debug_image = image.copy()
    for index, rect in enumerate(tiles):
        date_str = date_for_tile(rect, anchors, image.shape[1], year, month)
        if date_str is None:
            logging.warning("[OpenShifts] Ignoring tile outside calendar columns: %s", rect)
            continue
        x, y, w, h = rect
        cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 180, 0), 2)
        entry = result.setdefault(
            date_str,
            {
                "type": "open",
                "coords": [],
                "date": datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %b"),
                "day": int(date_str[-2:]),
                "month": month,
                "year": year,
                "count": 0,
                "evidence": {"detector": "open-row-geometry", "anchor_confidence": anchors["open"]["confidence"]},
            },
        )
        entry["coords"].append(rect)
        entry["count"] += 1

    debug_path = image_path.replace(".png", "_open_row_geometry.png")
    cv2.imwrite(debug_path, debug_image)
    logging.info(
        "[OpenShifts] Geometry detector found %d tile(s) on %s",
        sum(entry["count"] for entry in result.values()),
        ", ".join(entry["date"] for entry in result.values()) or "no dates",
    )
    return result
