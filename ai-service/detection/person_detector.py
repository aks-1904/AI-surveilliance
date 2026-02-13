"""
Person Detection using YOLOv8
Detects persons in video frames and tracks them
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PersonDetector:
    """Detects and tracks persons using YOLOv8"""
    
    def __init__(self, config):
        self.config = config
        self.confidence_threshold = config.CONFIDENCE_THRESHOLD
        
        # Load YOLO model
        try:
            self.model = YOLO(config.YOLO_MODEL)
            logger.info(f"YOLO model loaded: {config.YOLO_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {str(e)}")
            raise
        
        # Person class ID in COCO dataset
        self.PERSON_CLASS_ID = 0
        
        # Tracking
        self.next_id = 1
        self.tracked_persons = {}
        self.max_tracking_distance = 100
    
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect persons in frame
        
        Args:
            frame: Input video frame
        
        Returns:
            List of detected persons with bounding boxes and IDs
        """
        try:
            # Run YOLO detection
            results = self.model(frame, verbose=False)
            
            detected_persons = []
            current_detections = []
            
            # Process results
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Get class ID
                    class_id = int(box.cls[0])
                    
                    # Only process persons
                    if class_id != self.PERSON_CLASS_ID:
                        continue
                    
                    # Get confidence
                    confidence = float(box.conf[0])
                    
                    if confidence < self.confidence_threshold:
                        continue
                    
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Calculate center point
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    current_detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'center': (center_x, center_y),
                        'confidence': confidence
                    })
            
            # Assign IDs using simple tracking
            detected_persons = self._track_persons(current_detections)
            
            return detected_persons
            
        except Exception as e:
            logger.error(f"Error in person detection: {str(e)}")
            return []
    
    def _track_persons(self, detections: List[Dict]) -> List[Dict[str, Any]]:
        """
        Simple tracking algorithm to maintain person IDs across frames
        
        Args:
            detections: Current frame detections
        
        Returns:
            Detections with assigned IDs
        """
        tracked = []
        matched_ids = set()
        
        # Match current detections with tracked persons
        for detection in detections:
            center = detection['center']
            best_match_id = None
            best_distance = float('inf')
            
            # Find closest tracked person
            for person_id, person_data in self.tracked_persons.items():
                if person_id in matched_ids:
                    continue
                
                prev_center = person_data['center']
                distance = np.sqrt(
                    (center[0] - prev_center[0])**2 + 
                    (center[1] - prev_center[1])**2
                )
                
                if distance < best_distance and distance < self.max_tracking_distance:
                    best_distance = distance
                    best_match_id = person_id
            
            # Assign ID
            if best_match_id is not None:
                person_id = best_match_id
                matched_ids.add(person_id)
            else:
                person_id = self.next_id
                self.next_id += 1
            
            # Create person object
            person = {
                'id': person_id,
                'bbox': detection['bbox'],
                'center': center,
                'confidence': detection['confidence']
            }
            
            tracked.append(person)
            
            # Update tracking
            self.tracked_persons[person_id] = {
                'center': center,
                'last_seen': cv2.getTickCount()
            }
        
        # Remove old tracked persons (not seen for 3 seconds)
        current_time = cv2.getTickCount()
        freq = cv2.getTickFrequency()
        to_remove = []
        
        for person_id, data in self.tracked_persons.items():
            time_diff = (current_time - data['last_seen']) / freq
            if time_diff > 3.0:
                to_remove.append(person_id)
        
        for person_id in to_remove:
            del self.tracked_persons[person_id]
        
        return tracked
    
    def reset(self):
        """Reset tracking"""
        self.next_id = 1
        self.tracked_persons = {}