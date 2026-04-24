"""
Weapon Detector
Detects dangerous weapons like guns and knives.

Fixes vs original
-----------------
* Cooldown is now keyed on (weapon_type, screen_region) rather than just
  weapon_type — prevents a second overlapping bounding box on the same weapon
  from firing a duplicate alert.
* Screen is divided into coarse cells (WEAPON_GRID_CELL_PX × WEAPON_GRID_CELL_PX
  pixels, default 200×200).  Two detections in the same cell count as the same
  weapon location.
* Grenade/explosive re-labelling threshold raised to confidence 0.85 (was 0.8)
  to reduce false re-labels.
* All cooldown state lives inside this class; EventCooldownManager provides a
  second independent layer on top.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class WeaponDetector:
    """Detects dangerous weapons like guns and knives."""

    def __init__(self, config):
        self.config               = config
        self.confidence_threshold = float(getattr(config, 'WEAPON_CONFIDENCE', 0.6))
        self.cooldown_seconds     = float(getattr(config, 'WEAPON_COOLDOWN_SECONDS', 15))
        self.grid_cell_px         = int(  getattr(config, 'WEAPON_GRID_CELL_PX',    200))

        # (weapon_type, grid_x, grid_y) -> last_alert_epoch
        self._last_alert_times: Dict[tuple, float] = {}

        try:
            self.model = YOLO('weapon_detector.pt')
            logger.info("Weapon detection model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Weapon YOLO model: {e}")
            self.model = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame: np.ndarray, timestamp: datetime) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        if self.model is None:
            return events

        try:
            results      = self.model(frame, verbose=False)
            current_time = timestamp.timestamp()

            for result in results:
                for box in result.boxes:
                    confidence = float(box.conf[0])
                    if confidence < self.confidence_threshold:
                        continue

                    class_id    = int(box.cls[0])
                    weapon_type = self.model.names[class_id].upper()

                    # Re-label uncertain grenade/explosive detections
                    if weapon_type in ('GRENADE', 'EXPLOSIVE') and confidence < 0.85:
                        weapon_type = 'KNIFE'

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2

                    # Coarse grid cell
                    gx = cx // self.grid_cell_px
                    gy = cy // self.grid_cell_px
                    key = (weapon_type, gx, gy)

                    last = self._last_alert_times.get(key, 0.0)
                    if current_time - last < self.cooldown_seconds:
                        continue  # suppress duplicate

                    self._last_alert_times[key] = current_time

                    event = {
                        'type':      'WEAPON_DETECTED',
                        'timestamp': timestamp.isoformat(),
                        'location':  {'x': cx, 'y': cy},
                        'details': {
                            'message':     f"Lethal weapon ({weapon_type}) detected!",
                            'weapon_type': weapon_type,
                            'confidence':  round(confidence, 3),
                            'bbox':        [x1, y1, x2, y2],
                        },
                    }
                    events.append(event)
                    logger.critical(
                        f"CRITICAL: {weapon_type} detected with {confidence:.2f} confidence!"
                    )

            return events

        except Exception as e:
            logger.error(f"Error in weapon detection: {e}")
            return []