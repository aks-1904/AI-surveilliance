"""
Object tracking module for persistent object identification across frames
Uses simple centroid tracking - can be replaced with DeepSORT for better results
"""

import time
from typing import Dict, List, Tuple, Optional
from collections import OrderedDict
import numpy as np
from utils import calculate_distance, bbox_to_center


class ObjectTracker:
    """
    Simple centroid-based object tracker
    Assigns unique IDs to detected objects and tracks them across frames
    """
    
    def __init__(self, max_disappeared: int = 30, max_distance: int = 100):
        """
        Initialize tracker
        
        Args:
            max_disappeared: Maximum frames an object can be missing before removal
            max_distance: Maximum distance for matching objects between frames
        """
        self.next_object_id = 0
        self.objects = OrderedDict()  # {id: {bbox, center, class, last_seen}}
        self.disappeared = OrderedDict()  # {id: frames_disappeared}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        
        # Track object history for event detection
        self.object_history = OrderedDict()  # {id: [positions, timestamps]}
        
    def register(self, bbox: List[int], class_name: str) -> int:
        """
        Register a new object
        
        Args:
            bbox: [x1, y1, x2, y2]
            class_name: Object class
        
        Returns:
            Assigned object ID
        """
        object_id = self.next_object_id
        center = bbox_to_center(bbox)
        
        self.objects[object_id] = {
            'bbox': bbox,
            'center': center,
            'class': class_name,
            'first_seen': time.time(),
            'last_seen': time.time()
        }
        self.disappeared[object_id] = 0
        self.object_history[object_id] = {
            'positions': [center],
            'timestamps': [time.time()],
            'bboxes': [bbox]
        }
        
        self.next_object_id += 1
        return object_id
    
    def deregister(self, object_id: int):
        """
        Remove an object from tracking
        
        Args:
            object_id: ID to remove
        """
        del self.objects[object_id]
        del self.disappeared[object_id]
        # Keep history for analysis
    
    def update(self, detections: List[Dict]) -> Dict[int, Dict]:
        """
        Update tracker with new detections
        
        Args:
            detections: List of {bbox, class, confidence}
        
        Returns:
            Dictionary of {object_id: object_info}
        """
        # If no detections, increment disappeared counter for all objects
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            
            return self.objects
        
        # Extract centers from detections
        input_centers = [bbox_to_center(d['bbox']) for d in detections]
        
        # If no existing objects, register all detections
        if len(self.objects) == 0:
            for i, detection in enumerate(detections):
                self.register(detection['bbox'], detection['class'])
        else:
            # Match existing objects to new detections
            object_ids = list(self.objects.keys())
            object_centers = [self.objects[oid]['center'] for oid in object_ids]
            
            # Compute distance matrix
            distances = np.zeros((len(object_centers), len(input_centers)))
            
            for i, obj_center in enumerate(object_centers):
                for j, input_center in enumerate(input_centers):
                    distances[i, j] = calculate_distance(obj_center, input_center)
            
            # Match objects using Hungarian algorithm (simplified greedy approach)
            rows = distances.min(axis=1).argsort()
            cols = distances.argmin(axis=1)[rows]
            
            used_rows = set()
            used_cols = set()
            
            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                
                if distances[row, col] > self.max_distance:
                    continue
                
                object_id = object_ids[row]
                
                # Update object
                self.objects[object_id]['bbox'] = detections[col]['bbox']
                self.objects[object_id]['center'] = input_centers[col]
                self.objects[object_id]['last_seen'] = time.time()
                self.disappeared[object_id] = 0
                
                # Update history
                self.object_history[object_id]['positions'].append(input_centers[col])
                self.object_history[object_id]['timestamps'].append(time.time())
                self.object_history[object_id]['bboxes'].append(detections[col]['bbox'])
                
                # Limit history size
                if len(self.object_history[object_id]['positions']) > 100:
                    self.object_history[object_id]['positions'].pop(0)
                    self.object_history[object_id]['timestamps'].pop(0)
                    self.object_history[object_id]['bboxes'].pop(0)
                
                used_rows.add(row)
                used_cols.add(col)
            
            # Handle disappeared objects
            unused_rows = set(range(len(object_centers))) - used_rows
            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            
            # Register new objects
            unused_cols = set(range(len(input_centers))) - used_cols
            for col in unused_cols:
                self.register(detections[col]['bbox'], detections[col]['class'])
        
        return self.objects
    
    def get_object_duration(self, object_id: int) -> float:
        """
        Get how long an object has been tracked (in seconds)
        
        Args:
            object_id: Object ID
        
        Returns:
            Duration in seconds
        """
        if object_id not in self.objects:
            return 0.0
        
        obj = self.objects[object_id]
        return time.time() - obj['first_seen']
    
    def get_object_movement(self, object_id: int) -> float:
        """
        Calculate total movement distance of an object
        
        Args:
            object_id: Object ID
        
        Returns:
            Total distance moved in pixels
        """
        if object_id not in self.object_history:
            return 0.0
        
        positions = self.object_history[object_id]['positions']
        if len(positions) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(positions)):
            total_distance += calculate_distance(positions[i-1], positions[i])
        
        return total_distance
    
    def is_stationary(self, object_id: int, threshold: float = 50.0) -> bool:
        """
        Check if an object is stationary (loitering detection)
        
        Args:
            object_id: Object ID
            threshold: Maximum movement distance to consider stationary
        
        Returns:
            True if object is stationary
        """
        movement = self.get_object_movement(object_id)
        duration = self.get_object_duration(object_id)
        
        # Object must be tracked for at least 10 seconds
        if duration < 10:
            return False
        
        # Check if movement is below threshold
        return movement < threshold