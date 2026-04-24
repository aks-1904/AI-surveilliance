"""
Zone Analyzer
Checks if persons enter restricted zones.

Fixes vs original
-----------------
* Grace period (ZONE_EXIT_GRACE_SEC, default 3 s): a person must be *absent*
  from a zone for at least this many seconds before their next entry is treated
  as a new intrusion.  Eliminates false re-alerts caused by detection flicker.
* active_intrusions now stores the exit timestamp so the grace period is enforced
  across the full re-entry cycle, not just within a single frame.
"""

import cv2
import numpy as np
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ZoneAnalyzer:
    """Analyzes person positions relative to restricted zones."""

    # Seconds a person must be *outside* a zone before re-entry triggers a new event.
    EXIT_GRACE_DEFAULT = 3.0

    def __init__(self, exit_grace_sec: float = EXIT_GRACE_DEFAULT):
        self.exit_grace_sec = exit_grace_sec

        # intrusion_key -> {'inside': bool, 'exit_time': float | None}
        self._state: Dict[str, Dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_intrusions(
        self,
        persons: List[Dict],
        zones: List[Dict],
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Check if any person has entered a restricted zone.

        Returns only *new* intrusion events (i.e. the leading edge of entry,
        subject to the grace period).
        """
        events: List[Dict[str, Any]] = []
        currently_inside: set = set()

        for person in persons:
            person_id = person['id']
            center    = person['center']

            for zone in zones:
                zone_id = zone['id']
                polygon = zone['polygon']
                key     = f"{person_id}_{zone_id}"

                inside = cv2.pointPolygonTest(polygon, center, False) >= 0

                if inside:
                    currently_inside.add(key)
                    state = self._state.get(key)

                    if state is None:
                        # First-ever detection for this pair
                        event = self._make_event(person, zone, timestamp)
                        events.append(event)
                        self._state[key] = {'inside': True, 'exit_time': None}
                        logger.warning(f"Zone intrusion (new): Person {person_id} in {zone['name']}")

                    elif not state['inside']:
                        # Person was outside — check grace period
                        exit_t = state.get('exit_time')
                        if exit_t is None or (time.monotonic() - exit_t) >= self.exit_grace_sec:
                            event = self._make_event(person, zone, timestamp)
                            events.append(event)
                            logger.warning(
                                f"Zone intrusion (re-entry): Person {person_id} in {zone['name']}"
                            )
                        else:
                            logger.debug(
                                f"Grace period active for Person {person_id} / {zone['name']} "
                                f"— suppressing re-entry alert"
                            )
                        state['inside']    = True
                        state['exit_time'] = None

                else:
                    # Person is outside this zone right now
                    state = self._state.get(key)
                    if state and state['inside']:
                        # Transition: just left — record exit time for grace period
                        state['inside']    = False
                        state['exit_time'] = time.monotonic()

        # ------------------------------------------------------------------
        # Garbage-collect state for persons no longer in the scene.
        # (We can't tell "left scene" vs "left zone" here, so we keep state
        #  indefinitely — it's O(persons × zones), which is tiny.)
        # ------------------------------------------------------------------
        return events

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_event(person: Dict, zone: Dict, timestamp: datetime) -> Dict[str, Any]:
        center = person['center']
        return {
            'type':      'RESTRICTED_ENTRY',
            'timestamp': timestamp.isoformat(),
            'person_id': person['id'],
            'zone_id':   zone['id'],
            'zone_name': zone['name'],
            'location':  {'x': center[0], 'y': center[1]},
            'details': {
                'message': f"Person {person['id']} entered restricted zone: {zone['name']}",
                'bbox':    person['bbox'],
            },
            'attributes': person['attributes'],
        }

    def is_point_in_zone(self, point: tuple, zone_polygon: np.ndarray) -> bool:
        return cv2.pointPolygonTest(zone_polygon, point, False) >= 0

    def get_zone_by_id(self, zones: List[Dict], zone_id: int) -> Optional[Dict]:
        for zone in zones:
            if zone['id'] == zone_id:
                return zone
        return None

    def reset(self):
        """Reset active intrusion state."""
        self._state.clear()