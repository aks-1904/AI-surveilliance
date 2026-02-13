"""
Unattended Object Detection
Detects objects (bags, packages) that are left unattended
"""

import cv2
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class UnattendedObjectDetector:
    """Detects unattended objects"""
    
    def __init__(self, config):
        self.config = config
        self.threshold_seconds = config.UNATTENDED_THRESHOLD_SECONDS
        self.person_distance_threshold = config.OBJECT_PERSON_DISTANCE_THRESHOLD
        
        # Classes that are considered as potential unattended objects
        # COCO class IDs: 24=backpack, 25=umbrella, 26=handbag, 28=suitcase
        self.OBJECT_CLASS_IDS = [24, 25, 26, 28]
        
        # Track detected objects
        self.tracked_objects = {}
        self.active_alerts = {}
        self.next_object_id = 1
    
    def detect(
        self,
        frame: np.ndarray,
        persons: List[Dict],
        timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """
        Detect unattended objects
        
        Args:
            frame: Current video frame
            persons: List of detected persons
            timestamp: Current timestamp
        
        Returns:
            List of unattended object events
        """
        events = []
        
        # Detect objects using background subtraction or YOLO
        # For simplicity, using YOLO from person_detector's model
        # In production, you'd want a separate YOLO instance
        detected_objects = self._detect_objects(frame)
        
        current_object_ids = set()
        
        for obj in detected_objects:
            # Find closest person
            closest_distance = float('inf')
            has_nearby_person = False
            
            obj_center = obj['center']
            
            for person in persons:
                person_center = person['center']
                distance = np.sqrt(
                    (obj_center[0] - person_center[0])**2 + 
                    (obj_center[1] - person_center[1])**2
                )
                
                closest_distance = min(closest_distance, distance)
                
                if distance <= self.person_distance_threshold:
                    has_nearby_person = True
                    break
            
            # Track object
            object_id = self._get_or_create_object_id(obj)
            current_object_ids.add(object_id)
            
            # Update tracking
            if object_id not in self.tracked_objects:
                self.tracked_objects[object_id] = {
                    'first_seen': timestamp,
                    'position': obj_center,
                    'bbox': obj['bbox'],
                    'class_name': obj['class_name'],
                    'last_update': timestamp,
                    'has_person': has_nearby_person
                }
            else:
                self.tracked_objects[object_id]['last_update'] = timestamp
                self.tracked_objects[object_id]['has_person'] = has_nearby_person
            
            # Check if object is unattended
            if not has_nearby_person:
                obj_data = self.tracked_objects[object_id]
                time_unattended = (timestamp - obj_data['first_seen']).total_seconds()
                
                # Alert if unattended for too long
                if time_unattended >= self.threshold_seconds:
                    if object_id not in self.active_alerts:
                        event = {
                            'type': 'UNATTENDED_OBJECT',
                            'timestamp': timestamp.isoformat(),
                            'object_id': object_id,
                            'location': {
                                'x': obj_center[0],
                                'y': obj_center[1]
                            },
                            'duration': int(time_unattended),
                            'details': {
                                'message': f"Unattended {obj['class_name']} detected for {int(time_unattended)} seconds",
                                'object_type': obj['class_name'],
                                'bbox': obj['bbox'],
                                'closest_person_distance': int(closest_distance)
                            }
                        }
                        
                        events.append(event)
                        self.active_alerts[object_id] = timestamp
                        logger.warning(f"Unattended object detected: {obj['class_name']} (ID: {object_id})")
        
        # Clean up objects no longer visible
        to_remove = []
        for object_id in self.tracked_objects:
            if object_id not in current_object_ids:
                last_update = self.tracked_objects[object_id]['last_update']
                if (timestamp - last_update).total_seconds() > 5:
                    to_remove.append(object_id)
        
        for object_id in to_remove:
            del self.tracked_objects[object_id]
            if object_id in self.active_alerts:
                del self.active_alerts[object_id]
        
        return events
    
    def _detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in frame
        This is a simplified implementation. In production, use YOLO.
        
        Args:
            frame: Video frame
        
        Returns:
            List of detected objects
        """
        # For demo purposes, returning empty list
        # In production, you would use YOLO to detect bags, backpacks, etc.
        # Example:
        # results = self.model(frame)
        # for result in results:
        #     for box in result.boxes:
        #         if int(box.cls[0]) in self.OBJECT_CLASS_IDS:
        #             # Process object...
        
        return []
    
    def _get_or_create_object_id(self, obj: Dict) -> int:
        """
        Get existing object ID or create new one
        Simple tracking based on position proximity
        
        Args:
            obj: Object dictionary with center point
        
        Returns:
            Object ID
        """
        obj_center = obj['center']
        
        # Find closest tracked object
        closest_id = None
        closest_distance = float('inf')
        
        for obj_id, data in self.tracked_objects.items():
            tracked_center = data['position']
            distance = np.sqrt(
                (obj_center[0] - tracked_center[0])**2 + 
                (obj_center[1] - tracked_center[1])**2
            )
            
            if distance < closest_distance and distance < 50:
                closest_distance = distance
                closest_id = obj_id
        
        if closest_id is not None:
            return closest_id
        else:
            new_id = self.next_object_id
            self.next_object_id += 1
            return new_id
    
    def get_tracked_count(self) -> int:
        """Get number of currently tracked objects"""
        return len(self.tracked_objects)
    
    def get_unattended_count(self) -> int:
        """Get number of active unattended object alerts"""
        return len(self.active_alerts)
    
    def reset(self):
        """Reset all tracking"""
        self.tracked_objects = {}
        self.active_alerts = {}
        self.next_object_id = 1