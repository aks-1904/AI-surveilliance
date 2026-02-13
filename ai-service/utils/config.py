"""
Configuration Management
Centralized configuration for the AI service
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # Service Configuration
    PORT = int(os.getenv('PORT', 5000))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    
    # Backend Integration
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:3000')
    BACKEND_EVENT_ENDPOINT = f"{BACKEND_URL}/api/events"
    
    # Camera Configuration
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
    FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', 640))
    FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', 480))
    FPS = int(os.getenv('FPS', 30))
    
    # YOLO Configuration
    YOLO_MODEL = os.getenv('YOLO_MODEL', 'yolov8n.pt')  # n=nano, s=small, m=medium
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.5))
    
    # Face Blur Configuration
    FACE_DETECTION_METHOD = os.getenv('FACE_DETECTION_METHOD', 'haar')  # haar or dnn
    BLUR_KERNEL_SIZE = int(os.getenv('BLUR_KERNEL_SIZE', 50))
    
    # Loitering Detection
    LOITERING_THRESHOLD_SECONDS = int(os.getenv('LOITERING_THRESHOLD_SECONDS', 30))
    LOITERING_DISTANCE_THRESHOLD = int(os.getenv('LOITERING_DISTANCE_THRESHOLD', 50))
    
    # Unattended Object Detection
    UNATTENDED_THRESHOLD_SECONDS = int(os.getenv('UNATTENDED_THRESHOLD_SECONDS', 30))
    OBJECT_PERSON_DISTANCE_THRESHOLD = int(os.getenv('OBJECT_PERSON_DISTANCE_THRESHOLD', 100))
    
    # Risk Scoring
    RISK_SCORES = {
        'RESTRICTED_ENTRY': int(os.getenv('RISK_RESTRICTED_ENTRY', 8)),
        'UNATTENDED_OBJECT': int(os.getenv('RISK_UNATTENDED_OBJECT', 7)),
        'LOITERING': int(os.getenv('RISK_LOITERING', 6))
    }
    
    # Risk Levels
    RISK_LEVEL_LOW = 4
    RISK_LEVEL_MEDIUM = 8
    
    # Paths
    MODELS_PATH = os.getenv('MODELS_PATH', './models')
    HAAR_CASCADE_PATH = os.path.join(
        MODELS_PATH,
        'haarcascade_frontalface_default.xml'
    )
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        if cls.CAMERA_INDEX < 0:
            errors.append("CAMERA_INDEX must be >= 0")
        
        if cls.CONFIDENCE_THRESHOLD < 0 or cls.CONFIDENCE_THRESHOLD > 1:
            errors.append("CONFIDENCE_THRESHOLD must be between 0 and 1")
        
        if cls.LOITERING_THRESHOLD_SECONDS < 1:
            errors.append("LOITERING_THRESHOLD_SECONDS must be > 0")
        
        if cls.UNATTENDED_THRESHOLD_SECONDS < 1:
            errors.append("UNATTENDED_THRESHOLD_SECONDS must be > 0")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True