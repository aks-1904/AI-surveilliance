import cv2
import numpy as np
from ultralytics import YOLO
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class WeaponDetector:
    """Detects dangerous weapons like guns and knives"""
    
    def __init__(self, config):
        self.config = config
        self.confidence_threshold = getattr(config, 'WEAPON_CONFIDENCE', 0.6)

        # Cooldown Mechanism
        self.cooldown_seconds = getattr(config, 'WEAPON_COOLDOWN_SECONDS', 10)
        self.last_alert_times = {}
        
        try:
            # Load your custom trained weapon detection model
            self.model = YOLO('weapon_detector.pt')
            logger.info("Weapon detection model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Weapon YOLO model: {str(e)}")
            self.model = None

    def detect(self, frame: np.ndarray, timestamp: datetime) -> List[Dict[str, Any]]:
        events = []
        if self.model is None:
            return events

        try:
            results = self.model(frame, verbose=False)
            current_time = timestamp.timestamp()
            
            for result in results:
                for box in result.boxes:
                    confidence = float(box.conf[0])
                    
                    if confidence >= self.confidence_threshold:
                        class_id = int(box.cls[0])
                        weapon_type = self.model.names[class_id].upper() # 'GUN', 'KNIFE', etc.

                        if (weapon_type == 'GRENADE' or weapon_type == 'EXPLOSIVE') and confidence < 0.8:
                            weapon_type = 'KNIFE'
                        
                        last_alert = self.last_alert_times.get(weapon_type, 0)
                        if(current_time - last_alert) < self.cooldown_seconds:
                            continue # Skip generating this event
                            
                        self.last_alert_times[weapon_type] = current_time

                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        event = {
                            'type': 'WEAPON_DETECTED',
                            'timestamp': timestamp.isoformat(),
                            'location': {'x': (x1+x2)//2, 'y': (y1+y2)//2},
                            'details': {
                                'message': f"Lethal weapon ({weapon_type}) detected!",
                                'weapon_type': weapon_type,
                                'confidence': confidence,
                                'bbox': [x1, y1, x2, y2]
                            }
                        }
                        events.append(event)
                        logger.critical(f"CRITICAL: {weapon_type} detected with {confidence:.2f} confidence!")
                        
            return events
            
        except Exception as e:
            logger.error(f"Error in weapon detection: {str(e)}")
            return []