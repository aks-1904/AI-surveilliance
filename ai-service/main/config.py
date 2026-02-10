"""
Configuration settings for AI Video Processing Service
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# YOLO Model Configuration
YOLO_MODEL = "yolov8n.pt"  # nano model for speed, use yolov8m.pt for accuracy
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45

# Classes of interest (COCO dataset indices)
CLASSES_OF_INTEREST = {
    0: "person",
    24: "backpack",
    26: "handbag",
    28: "suitcase",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# Event Detection Settings
LOITERING_THRESHOLD = 300  # seconds (5 minutes)
CROWD_THRESHOLD = 10  # number of people
UNATTENDED_OBJECT_DISTANCE = 100  # pixels
UNATTENDED_OBJECT_TIME = 30  # seconds

# Restricted Zone (example polygon - customize per camera)
# Format: list of (x, y) coordinates
RESTRICTED_ZONES = [
    [(100, 100), (500, 100), (500, 400), (100, 400)]  # Example rectangle
]

# Risk Scoring
RISK_SCORES = {
    "restricted_zone": 8,
    "unattended_object": 7,
    "loitering": 6,
    "crowd_spike": 5,
    "weapon_detected": 10,
    "fall_detected": 7
}

# Privacy Settings
ENABLE_FACE_BLUR = True
BLUR_KERNEL_SIZE = (99, 99)
BLUR_SIGMA = 30

# Stream Settings
RTSP_RECONNECT_DELAY = 5  # seconds
FRAME_SKIP = 0  # process every frame (0), or skip frames (1 = every other frame)
MAX_FRAME_WIDTH = 1280  # resize if larger
MAX_FRAME_HEIGHT = 720

# Backend API
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
BACKEND_EVENT_ENDPOINT = f"{BACKEND_URL}/api/events"

# Flask Settings
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 8000
FLASK_DEBUG = False

# Tracking Settings
ENABLE_TRACKING = True
MAX_TRACKING_AGE = 30  # frames to keep lost tracks
MIN_HITS = 3  # minimum detections before tracking