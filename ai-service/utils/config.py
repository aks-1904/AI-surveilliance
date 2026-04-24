"""
Configuration Management
Centralized configuration for the AI service.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # ------------------------------------------------------------------ #
    # Service
    # ------------------------------------------------------------------ #
    PORT       = int(os.getenv('PORT', 5000))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

    # ------------------------------------------------------------------ #
    # Backend integration
    # ------------------------------------------------------------------ #
    BACKEND_URL             = os.getenv('BACKEND_URL', 'http://localhost:3000')
    BACKEND_EVENT_ENDPOINT  = f"{BACKEND_URL}/api/events"

    # ------------------------------------------------------------------ #
    # Camera
    # ------------------------------------------------------------------ #
    CAMERA_INDEX  = int(os.getenv('CAMERA_INDEX', 0))
    FRAME_WIDTH   = int(os.getenv('FRAME_WIDTH',  640))
    FRAME_HEIGHT  = int(os.getenv('FRAME_HEIGHT', 480))
    FPS           = int(os.getenv('FPS', 30))

    # ------------------------------------------------------------------ #
    # YOLO
    # ------------------------------------------------------------------ #
    YOLO_MODEL              = os.getenv('YOLO_MODEL',              'yolov8n.pt')
    YOLO_MASK_DETECTOR_MODEL= os.getenv('YOLO_MASK_DETECTOR_MODEL','mask_detector.pt')
    CONFIDENCE_THRESHOLD    = float(os.getenv('CONFIDENCE_THRESHOLD', 0.5))

    # ------------------------------------------------------------------ #
    # Face blur
    # ------------------------------------------------------------------ #
    FACE_DETECTION_METHOD = os.getenv('FACE_DETECTION_METHOD', 'haar')
    BLUR_KERNEL_SIZE      = int(os.getenv('BLUR_KERNEL_SIZE', 50))

    # ------------------------------------------------------------------ #
    # Loitering detection
    # ------------------------------------------------------------------ #
    LOITERING_THRESHOLD_SECONDS  = int(  os.getenv('LOITERING_THRESHOLD_SECONDS',  30))
    LOITERING_DISTANCE_THRESHOLD = int(  os.getenv('LOITERING_DISTANCE_THRESHOLD', 50))
    # How long (s) a person must be absent before a fresh loitering episode starts.
    LOITERING_REAPPEAR_SECONDS   = float(os.getenv('LOITERING_REAPPEAR_SECONDS',  120))

    # ------------------------------------------------------------------ #
    # Unattended object detection
    # ------------------------------------------------------------------ #
    UNATTENDED_THRESHOLD_SECONDS      = int(os.getenv('UNATTENDED_THRESHOLD_SECONDS',      30))
    OBJECT_PERSON_DISTANCE_THRESHOLD  = int(os.getenv('OBJECT_PERSON_DISTANCE_THRESHOLD', 100))

    # ------------------------------------------------------------------ #
    # Weapon detection
    # ------------------------------------------------------------------ #
    WEAPON_CONFIDENCE      = float(os.getenv('WEAPON_CONFIDENCE',       0.6))
    WEAPON_COOLDOWN_SECONDS= float(os.getenv('WEAPON_COOLDOWN_SECONDS', 15))
    # Pixel size of the coarse dedup grid (same weapon, nearby boxes → same cell)
    WEAPON_GRID_CELL_PX    = int(  os.getenv('WEAPON_GRID_CELL_PX',    200))

    # ------------------------------------------------------------------ #
    # Zone analyzer
    # ------------------------------------------------------------------ #
    # Seconds a person must be outside a zone before re-entry counts as new.
    ZONE_EXIT_GRACE_SEC = float(os.getenv('ZONE_EXIT_GRACE_SEC', 3.0))

    # ------------------------------------------------------------------ #
    # Global event cooldowns (EventCooldownManager)
    # These are a second independent layer on top of per-component guards.
    # ------------------------------------------------------------------ #
    # Min gap (s) between repeated RESTRICTED_ENTRY alerts for same (person, zone).
    COOLDOWN_RESTRICTED_ENTRY    = float(os.getenv('COOLDOWN_RESTRICTED_ENTRY',   60))
    # Min absence (s) before a new loitering episode is counted by the cooldown layer.
    COOLDOWN_LOITERING_REAPPEAR  = float(os.getenv('COOLDOWN_LOITERING_REAPPEAR', 120))
    # Absolute minimum gap (s) between any two loitering alerts for the same person.
    COOLDOWN_LOITERING_MIN_GAP   = float(os.getenv('COOLDOWN_LOITERING_MIN_GAP',  60))
    # Min gap (s) between UNATTENDED_OBJECT alerts for the same object id.
    COOLDOWN_UNATTENDED_MIN_GAP  = float(os.getenv('COOLDOWN_UNATTENDED_MIN_GAP', 90))
    # Min gap (s) between WEAPON_DETECTED alerts (safety net on top of WeaponDetector).
    COOLDOWN_WEAPON              = float(os.getenv('COOLDOWN_WEAPON',             15))

    # ------------------------------------------------------------------ #
    # Risk scoring
    # ------------------------------------------------------------------ #
    RISK_SCORES = {
        'RESTRICTED_ENTRY':  int(os.getenv('RISK_RESTRICTED_ENTRY',  8)),
        'UNATTENDED_OBJECT': int(os.getenv('RISK_UNATTENDED_OBJECT', 7)),
        'LOITERING':         int(os.getenv('RISK_LOITERING',         6)),
    }
    RISK_LEVEL_LOW    = 4
    RISK_LEVEL_MEDIUM = 8

    # ------------------------------------------------------------------ #
    # Paths
    # ------------------------------------------------------------------ #
    MODELS_PATH       = os.getenv('MODELS_PATH', './models')
    HAAR_CASCADE_PATH = os.path.join(MODELS_PATH, 'haarcascade_frontalface_default.xml')
    WHITELIST_DIR     = os.getenv('WHITELIST_DIR', 'whitelist_images/')

    UNATTENDED_TIME = 10    # legacy alias kept for compatibility
    IST_THRESHOLD   = 120   # legacy alias

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #
    @classmethod
    def validate(cls):
        errors = []
        if cls.CAMERA_INDEX < 0:
            errors.append("CAMERA_INDEX must be >= 0")
        if not 0 <= cls.CONFIDENCE_THRESHOLD <= 1:
            errors.append("CONFIDENCE_THRESHOLD must be between 0 and 1")
        if cls.LOITERING_THRESHOLD_SECONDS < 1:
            errors.append("LOITERING_THRESHOLD_SECONDS must be > 0")
        if cls.UNATTENDED_THRESHOLD_SECONDS < 1:
            errors.append("UNATTENDED_THRESHOLD_SECONDS must be > 0")
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        return True