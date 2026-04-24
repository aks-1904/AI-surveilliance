"""
Loitering Detection
Detects when persons stay in the same area for too long.

Fixes vs original
-----------------
* "Episode" model: a loitering alert fires ONCE per episode.  A new episode
  only begins when the person reappears after being absent for at least
  LOITERING_REAPPEAR_SECONDS (default 120 s).  If they leave briefly
  (< reappear window) and come back, the original first_seen time is
  preserved so the timer keeps accumulating — no double-alert on flicker.
* Notifies EventCooldownManager when a person leaves so the global cooldown
  can be reset appropriately for long absences.
* Masked persons retain the faster threshold (15 s) from the original code.
"""

import numpy as np
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# How long (seconds) a person must be absent before their return
# is treated as a brand-new loitering episode.
_DEFAULT_REAPPEAR_SEC = 120.0


class LoiteringDetector:
    """Detects loitering behaviour."""

    def __init__(self, config, cooldown_manager=None):
        self.config = config
        self.threshold_seconds   = config.LOITERING_THRESHOLD_SECONDS
        self.distance_threshold  = config.LOITERING_DISTANCE_THRESHOLD
        self.reappear_seconds    = float(
            getattr(config, 'LOITERING_REAPPEAR_SECONDS', _DEFAULT_REAPPEAR_SEC)
        )
        self._cooldown = cooldown_manager  # optional EventCooldownManager

        # person_id -> tracking dict
        self._history: Dict[int, Dict] = {}

        # person_id -> monotonic time of last alert (to avoid duplicate fires
        # within a single continuous episode — belt-and-braces guard)
        self._alerted: Dict[int, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(
        self,
        persons: List[Dict],
        timestamp: datetime,
    ) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        current_ids = {p['id'] for p in persons}

        for person in persons:
            pid       = person['id']
            center    = person['center']
            is_masked = person.get('is_masked', False)

            if pid not in self._history:
                self._history[pid] = self._new_record(timestamp, center)
                continue

            rec = self._history[pid]

            # --- Reappearance logic ---
            absent_sec = (timestamp - rec['last_seen']).total_seconds()
            if absent_sec > 0.5:
                # Person was missing for at least half a second between frames
                if absent_sec >= self.reappear_seconds:
                    # Long absence → fresh episode
                    logger.debug(f"Person {pid} reappeared after {absent_sec:.0f}s — new episode")
                    self._history[pid] = self._new_record(timestamp, center)
                    self._alerted.pop(pid, None)
                    if self._cooldown:
                        self._cooldown.notify_person_left(pid)
                    continue
                # Short absence (flicker/occlusion) → resume accumulating, don't reset

            # Update record
            rec['last_seen'] = timestamp
            rec['positions'].append(center)
            if len(rec['positions']) > 100:
                rec['positions'] = rec['positions'][-100:]

            time_spent = (timestamp - rec['first_seen']).total_seconds()
            has_moved  = self._has_moved_significantly(rec['positions'])

            active_threshold = 15 if is_masked else self.threshold_seconds

            if time_spent >= active_threshold and not has_moved:
                # Only fire if not already alerted this episode
                if pid not in self._alerted:
                    event_type = 'MASKED_LOITERING' if is_masked else 'LOITERING'
                    event = {
                        'type':      event_type,
                        'timestamp': timestamp.isoformat(),
                        'person_id': pid,
                        'location':  {'x': center[0], 'y': center[1]},
                        'duration':  int(time_spent),
                        'details': {
                            'message':    (
                                f"Person {pid} loitering for {int(time_spent)}s. "
                                f"Masked: {is_masked}"
                            ),
                            'bbox':       person['bbox'],
                            'start_time': rec['first_seen'].isoformat(),
                        },
                    }
                    events.append(event)
                    self._alerted[pid] = time.monotonic()
                    logger.warning(
                        f"{event_type} detected: Person {pid} for {int(time_spent)}s"
                    )

        # ------------------------------------------------------------------
        # Clean up persons no longer visible
        # ------------------------------------------------------------------
        to_remove = []
        for pid, rec in self._history.items():
            if pid not in current_ids:
                absent = (timestamp - rec['last_seen']).total_seconds()
                if absent > 5:
                    to_remove.append(pid)

        for pid in to_remove:
            del self._history[pid]
            if self._cooldown:
                self._cooldown.notify_person_left(pid)
            self._alerted.pop(pid, None)

        return events

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _new_record(timestamp: datetime, center: tuple) -> Dict:
        return {
            'first_seen':    timestamp,
            'last_seen':     timestamp,
            'positions':     [center],
        }

    def _has_moved_significantly(self, positions: List[tuple]) -> bool:
        if len(positions) < 2:
            return False
        arr  = np.array(positions)
        avg  = np.mean(arr, axis=0)
        dists = np.sqrt(((arr - avg) ** 2).sum(axis=1))
        return float(dists.max()) > self.distance_threshold

    # ------------------------------------------------------------------
    # Stat helpers (unchanged API)
    # ------------------------------------------------------------------

    def get_tracked_count(self) -> int:
        return len(self._history)

    def get_loitering_count(self) -> int:
        return len(self._alerted)

    def reset(self):
        self._history.clear()
        self._alerted.clear()
