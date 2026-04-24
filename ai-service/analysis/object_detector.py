"""
Unattended Object Detection
Detects objects (bags, packages) that are left unattended.

Fixes vs original
-----------------
* Alert fires ONCE per object tracking lifetime.  If the object disappears
  (picked up / leaves frame) and reappears, it gets a fresh object_id via
  the existing proximity tracker — so re-appearing is automatically treated
  as a new object.
* Notifies EventCooldownManager when an object is removed so the global
  cooldown record is also cleared.
* Whitelisted-owner logic preserved: if a whitelisted person is ever seen
  near the object, the object is permanently flagged as attended.
"""

import cv2
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class UnattendedObjectDetector:
    """Detects unattended objects."""

    # COCO class IDs: 24=backpack, 25=umbrella, 26=handbag, 28=suitcase
    OBJECT_CLASS_IDS = [24, 25, 26, 28]

    def __init__(self, config, cooldown_manager=None):
        self.config                    = config
        self.threshold_seconds         = config.UNATTENDED_THRESHOLD_SECONDS
        self.person_distance_threshold = config.OBJECT_PERSON_DISTANCE_THRESHOLD
        self._cooldown                 = cooldown_manager  # optional

        self.tracked_objects: Dict[int, Dict] = {}
        # object_id -> True  (one-shot: fired, will not fire again this lifetime)
        self._alerted: Dict[int, bool]         = {}
        self.next_object_id = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(
        self,
        frame: np.ndarray,
        persons: List[Dict],
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []

        detected_objects  = self._detect_objects(frame)
        current_object_ids: set = set()

        for obj in detected_objects:
            obj_center = obj['center']

            closest_distance    = float('inf')
            has_nearby_person   = False
            owner_whitelisted   = False

            for person in persons:
                dist = float(np.linalg.norm(
                    np.array(obj_center) - np.array(person['center'])
                ))
                if dist < closest_distance:
                    closest_distance = dist
                if dist <= self.person_distance_threshold:
                    has_nearby_person = True
                    if person.get('is_whitelisted', False):
                        owner_whitelisted = True

            object_id = self._get_or_create_object_id(obj)
            current_object_ids.add(object_id)

            if object_id not in self.tracked_objects:
                self.tracked_objects[object_id] = {
                    'first_seen':       timestamp,
                    'position':         obj_center,
                    'bbox':             obj['bbox'],
                    'class_name':       obj['class_name'],
                    'last_update':      timestamp,
                    'owner_whitelisted': owner_whitelisted,
                }
            else:
                rec = self.tracked_objects[object_id]
                rec['last_update'] = timestamp
                # Latch whitelisted status permanently for this object lifetime
                if has_nearby_person and owner_whitelisted:
                    rec['owner_whitelisted'] = True

            rec = self.tracked_objects[object_id]

            # Skip if a whitelisted owner was ever nearby
            if rec.get('owner_whitelisted', False):
                continue

            if not has_nearby_person:
                time_unattended = (timestamp - rec['first_seen']).total_seconds()

                if (time_unattended >= self.threshold_seconds
                        and object_id not in self._alerted):
                    event = {
                        'type':      'UNATTENDED_OBJECT',
                        'timestamp': timestamp.isoformat(),
                        'object_id': object_id,
                        'location':  {'x': obj_center[0], 'y': obj_center[1]},
                        'duration':  int(time_unattended),
                        'details': {
                            'message': (
                                f"Unattended {obj['class_name']} detected "
                                f"for {int(time_unattended)}s"
                            ),
                            'object_type':             obj['class_name'],
                            'bbox':                    obj['bbox'],
                            'closest_person_distance': int(closest_distance),
                        },
                    }
                    events.append(event)
                    self._alerted[object_id] = True
                    logger.warning(
                        f"Unattended object: {obj['class_name']} (ID {object_id})"
                    )

        # ------------------------------------------------------------------
        # Clean up objects no longer visible
        # ------------------------------------------------------------------
        to_remove = []
        for oid, rec in self.tracked_objects.items():
            if oid not in current_object_ids:
                absent = (timestamp - rec['last_update']).total_seconds()
                if absent > 5:
                    to_remove.append(oid)

        for oid in to_remove:
            del self.tracked_objects[oid]
            self._alerted.pop(oid, None)
            if self._cooldown:
                self._cooldown.notify_object_removed(oid)

        return events

    # ------------------------------------------------------------------
    # Internal helpers (unchanged from original)
    # ------------------------------------------------------------------

    def _detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """
        Stub — replace with real YOLO inference.
        In production:
            results = self.model(frame)
            for result in results:
                for box in result.boxes:
                    if int(box.cls[0]) in self.OBJECT_CLASS_IDS:
                        ...
        """
        return []

    def _get_or_create_object_id(self, obj: Dict) -> int:
        obj_center = obj['center']
        closest_id: Optional[int]  = None
        closest_dist = float('inf')

        for oid, data in self.tracked_objects.items():
            dist = float(np.linalg.norm(
                np.array(obj_center) - np.array(data['position'])
            ))
            if dist < closest_dist and dist < 50:
                closest_dist = dist
                closest_id   = oid

        if closest_id is not None:
            return closest_id

        new_id = self.next_object_id
        self.next_object_id += 1
        return new_id

    # ------------------------------------------------------------------
    # Stat helpers
    # ------------------------------------------------------------------

    def get_tracked_count(self) -> int:
        return len(self.tracked_objects)

    def get_unattended_count(self) -> int:
        return len(self._alerted)

    def reset(self):
        self.tracked_objects.clear()
        self._alerted.clear()
        self.next_object_id = 1