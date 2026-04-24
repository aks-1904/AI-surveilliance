"""
Event Cooldown Manager
Centralised deduplication layer — prevents the same alert from firing too often.

Cooldown rules (all tunable via Config):

  RESTRICTED_ENTRY   — per (person_id, zone_id)
      • First entry fires immediately.
      • Re-entry fires only after COOLDOWN_RESTRICTED_ENTRY_REVISIT seconds
        of the person being *outside* the zone (handled by ZoneAnalyzer) AND
        the cooldown having expired.
      • If the person never leaves, no repeat alert (ZoneAnalyzer already
        suppresses that with active_intrusions).

  LOITERING /        — per person_id
  MASKED_LOITERING     • Fires once per "loitering episode".
                       • A new episode starts only after the person has left
                         the scene for >= COOLDOWN_LOITERING_REAPPEAR seconds.
                       • Hard minimum gap between any two loitering alerts for
                         the same person: COOLDOWN_LOITERING_MIN_GAP seconds.

  UNATTENDED_OBJECT  — per object_id
      • Fires once when the object first crosses the threshold.
      • Re-fires only after the object has been picked up (removed from tracking)
        and reappears, with a minimum gap of COOLDOWN_UNATTENDED_MIN_GAP seconds.

  WEAPON_DETECTED    — per weapon_type (already handled in WeaponDetector,
                       but we add a second safety layer here per bounding-box
                       region to avoid duplicate labels from overlapping boxes).
                       Cooldown: COOLDOWN_WEAPON seconds (default 15 s).

Usage
-----
    cooldown = EventCooldownManager(config)

    # returns True if the event should be published, False if suppressed
    if cooldown.should_fire(event):
        event_publisher.publish_event(event, risk_score, risk_level)
"""

import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default cooldown values (seconds).  Override in Config if needed.
# ---------------------------------------------------------------------------
_DEFAULTS = {
    # How long after a zone-entry alert before the SAME person can trigger
    # another alert for the SAME zone (even after re-entry).
    'COOLDOWN_RESTRICTED_ENTRY':    60,

    # Minimum gap before a person who re-appears can trigger a loitering alert.
    'COOLDOWN_LOITERING_REAPPEAR':  120,

    # Absolute minimum gap between any two loitering alerts for the same person.
    'COOLDOWN_LOITERING_MIN_GAP':   60,

    # Gap before an unattended-object alert can re-fire for the same object id.
    'COOLDOWN_UNATTENDED_MIN_GAP':  90,

    # Weapon alert cooldown (on top of WeaponDetector's own cooldown).
    'COOLDOWN_WEAPON':              15,
}


class EventCooldownManager:
    """
    Stateful cooldown tracker.  One instance lives for the lifetime of the
    Flask application and is shared by every component.
    """

    def __init__(self, config):
        self._cfg = config

        def _get(key: str) -> float:
            return float(getattr(config, key, _DEFAULTS[key]))

        self._cd_zone        = _get('COOLDOWN_RESTRICTED_ENTRY')
        self._cd_loit_reapp  = _get('COOLDOWN_LOITERING_REAPPEAR')
        self._cd_loit_gap    = _get('COOLDOWN_LOITERING_MIN_GAP')
        self._cd_unatt       = _get('COOLDOWN_UNATTENDED_MIN_GAP')
        self._cd_weapon      = _get('COOLDOWN_WEAPON')

        # { key -> last_fired_epoch }
        self._last_fired: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def should_fire(self, event: Dict[str, Any]) -> bool:
        """
        Return True if this event should be published right now.
        Call this before event_publisher.publish_event().
        """
        etype = event.get('type', '')

        if etype == 'RESTRICTED_ENTRY':
            return self._check('zone', event)

        if etype in ('LOITERING', 'MASKED_LOITERING'):
            return self._check('loit', event)

        if etype == 'UNATTENDED_OBJECT':
            return self._check('unatt', event)

        if etype == 'WEAPON_DETECTED':
            return self._check('weapon', event)

        # Unknown types — allow through
        return True

    def notify_person_left(self, person_id: int):
        """
        Call this when a person disappears from the scene.
        Resets loitering cooldown *if* the minimum reappear window has passed,
        so returning after a long absence is treated as a fresh episode.
        This is called by LoiteringDetector when it cleans up a person.
        """
        key = f"loit:{person_id}"
        last = self._last_fired.get(key, 0.0)
        if time.monotonic() - last >= self._cd_loit_reapp:
            # Enough time has passed — clear the record so a future alert fires immediately.
            self._last_fired.pop(key, None)
            logger.debug(f"Cooldown cleared for loitering person {person_id} (long absence)")

    def notify_object_removed(self, object_id: int):
        """
        Call this when an unattended object disappears from tracking.
        Clears the cooldown so a genuinely new object at the same id slot is fresh.
        """
        key = f"unatt:{object_id}"
        self._last_fired.pop(key, None)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _make_key(self, category: str, event: Dict[str, Any]) -> str:
        etype = event.get('type', '')

        if category == 'zone':
            pid   = event.get('person_id', 'unk')
            zid   = event.get('zone_id',   'unk')
            return f"zone:{pid}:{zid}"

        if category == 'loit':
            pid = event.get('person_id', 'unk')
            return f"loit:{pid}"

        if category == 'unatt':
            oid = event.get('object_id', 'unk')
            return f"unatt:{oid}"

        if category == 'weapon':
            wtype = event.get('details', {}).get('weapon_type', 'UNK')
            # Also bucket by screen region (coarse 3×3 grid) to suppress
            # duplicate detections from overlapping boxes.
            loc   = event.get('location', {})
            gx    = int(loc.get('x', 0)) // 200
            gy    = int(loc.get('y', 0)) // 200
            return f"weapon:{wtype}:{gx}:{gy}"

        return f"generic:{etype}"

    def _cooldown_for(self, category: str) -> float:
        if category == 'zone':    return self._cd_zone
        if category == 'loit':   return self._cd_loit_gap
        if category == 'unatt':  return self._cd_unatt
        if category == 'weapon': return self._cd_weapon
        return 0.0

    def _check(self, category: str, event: Dict[str, Any]) -> bool:
        key      = self._make_key(category, event)
        cooldown = self._cooldown_for(category)
        now      = time.monotonic()
        last     = self._last_fired.get(key, 0.0)

        if now - last >= cooldown:
            self._last_fired[key] = now
            logger.debug(f"Event ALLOWED  [{key}]  (gap={now-last:.1f}s >= cd={cooldown}s)")
            return True

        remaining = cooldown - (now - last)
        logger.debug(f"Event SUPPRESSED [{key}]  (cooldown {remaining:.1f}s remaining)")
        return False