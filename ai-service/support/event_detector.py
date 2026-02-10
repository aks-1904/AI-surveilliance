"""
Event Detection Engine
Analyzes tracked objects and frame data to detect security events
"""

import time
from typing import List, Dict, Optional, Tuple
import numpy as np
from main.config import (
    RESTRICTED_ZONES, LOITERING_THRESHOLD, CROWD_THRESHOLD,
    UNATTENDED_OBJECT_DISTANCE, UNATTENDED_OBJECT_TIME, RISK_SCORES
)
from utils import bbox_in_polygon, calculate_distance, bbox_to_center


class EventDetector:
    """
    Detects security events based on object tracking and scene analysis
    """
    
    def __init__(self):
        """Initialize event detector"""
        self.events = []
        self.unattended_objects = {}  # {object_id: first_unattended_time}
        self.crowd_history = []  # Track crowd count over time
        self.previous_person_count = 0
        
    def detect_restricted_zone(self, tracked_objects: Dict, frame_shape: Tuple) -> List[Dict]:
        """
        Detect objects entering restricted zones
        
        Args:
            tracked_objects: Dictionary of tracked objects
            frame_shape: (height, width) of frame
        
        Returns:
            List of event dictionaries
        """
        events = []
        
        for zone_idx, zone in enumerate(RESTRICTED_ZONES):
            for obj_id, obj_info in tracked_objects.items():
                if obj_info['class'] == 'person':
                    if bbox_in_polygon(obj_info['bbox'], zone):
                        events.append({
                            'type': 'restricted_zone',
                            'object_id': obj_id,
                            'object_class': obj_info['class'],
                            'bbox': obj_info['bbox'],
                            'zone_id': zone_idx,
                            'timestamp': time.time(),
                            'risk': RISK_SCORES['restricted_zone'],
                            'description': f"Person detected in restricted zone {zone_idx}"
                        })
        
        return events
    
    def detect_loitering(self, tracker, tracked_objects: Dict) -> List[Dict]:
        """
        Detect people loitering in one area
        
        Args:
            tracker: ObjectTracker instance
            tracked_objects: Dictionary of tracked objects
        
        Returns:
            List of event dictionaries
        """
        events = []
        
        for obj_id, obj_info in tracked_objects.items():
            if obj_info['class'] == 'person':
                duration = tracker.get_object_duration(obj_id)
                is_stationary = tracker.is_stationary(obj_id)
                
                if duration > LOITERING_THRESHOLD and is_stationary:
                    events.append({
                        'type': 'loitering',
                        'object_id': obj_id,
                        'object_class': obj_info['class'],
                        'bbox': obj_info['bbox'],
                        'duration': duration,
                        'timestamp': time.time(),
                        'risk': RISK_SCORES['loitering'],
                        'description': f"Person loitering for {duration:.0f} seconds"
                    })
        
        return events
    
    def detect_unattended_object(self, tracked_objects: Dict) -> List[Dict]:
        """
        Detect unattended bags/objects
        
        Args:
            tracked_objects: Dictionary of tracked objects
        
        Returns:
            List of event dictionaries
        """
        events = []
        current_time = time.time()
        
        # Get all bags and people
        bags = {oid: info for oid, info in tracked_objects.items() 
                if info['class'] in ['backpack', 'handbag', 'suitcase']}
        people = {oid: info for oid, info in tracked_objects.items() 
                  if info['class'] == 'person'}
        
        # Check each bag
        for bag_id, bag_info in bags.items():
            bag_center = bbox_to_center(bag_info['bbox'])
            
            # Find nearest person
            min_distance = float('inf')
            for person_id, person_info in people.items():
                person_center = bbox_to_center(person_info['bbox'])
                distance = calculate_distance(bag_center, person_center)
                min_distance = min(min_distance, distance)
            
            # If no person nearby
            if min_distance > UNATTENDED_OBJECT_DISTANCE:
                if bag_id not in self.unattended_objects:
                    self.unattended_objects[bag_id] = current_time
                else:
                    unattended_duration = current_time - self.unattended_objects[bag_id]
                    
                    if unattended_duration > UNATTENDED_OBJECT_TIME:
                        events.append({
                            'type': 'unattended_object',
                            'object_id': bag_id,
                            'object_class': bag_info['class'],
                            'bbox': bag_info['bbox'],
                            'duration': unattended_duration,
                            'timestamp': current_time,
                            'risk': RISK_SCORES['unattended_object'],
                            'description': f"Unattended {bag_info['class']} for {unattended_duration:.0f} seconds"
                        })
            else:
                # Person nearby, remove from unattended list
                if bag_id in self.unattended_objects:
                    del self.unattended_objects[bag_id]
        
        # Clean up unattended objects that are no longer tracked
        tracked_ids = set(tracked_objects.keys())
        unattended_ids = set(self.unattended_objects.keys())
        for obj_id in (unattended_ids - tracked_ids):
            del self.unattended_objects[obj_id]
        
        return events
    
    def detect_crowd(self, tracked_objects: Dict) -> List[Dict]:
        """
        Detect crowd formation or sudden crowd spikes
        
        Args:
            tracked_objects: Dictionary of tracked objects
        
        Returns:
            List of event dictionaries
        """
        events = []
        current_time = time.time()
        
        # Count people
        person_count = sum(1 for obj in tracked_objects.values() 
                          if obj['class'] == 'person')
        
        # Track crowd history (keep last 30 seconds)
        self.crowd_history.append({
            'count': person_count,
            'timestamp': current_time
        })
        
        # Remove old entries
        self.crowd_history = [
            entry for entry in self.crowd_history 
            if current_time - entry['timestamp'] < 30
        ]
        
        # Detect crowd spike (sudden increase)
        if len(self.crowd_history) > 10:
            avg_count = np.mean([entry['count'] for entry in self.crowd_history[:-5]])
            if person_count > avg_count * 1.5 and person_count > CROWD_THRESHOLD:
                events.append({
                    'type': 'crowd_spike',
                    'person_count': person_count,
                    'previous_avg': avg_count,
                    'timestamp': current_time,
                    'risk': RISK_SCORES['crowd_spike'],
                    'description': f"Sudden crowd increase: {person_count} people (avg: {avg_count:.0f})"
                })
        
        # Detect high crowd density
        if person_count > CROWD_THRESHOLD:
            events.append({
                'type': 'crowd_detected',
                'person_count': person_count,
                'timestamp': current_time,
                'risk': RISK_SCORES['crowd_spike'],
                'description': f"High crowd density: {person_count} people"
            })
        
        self.previous_person_count = person_count
        return events
    
    def detect_all_events(self, tracker, tracked_objects: Dict, 
                         frame_shape: Tuple) -> List[Dict]:
        """
        Run all event detection algorithms
        
        Args:
            tracker: ObjectTracker instance
            tracked_objects: Dictionary of tracked objects
            frame_shape: (height, width) of frame
        
        Returns:
            List of all detected events
        """
        all_events = []
        
        # Run all detectors
        all_events.extend(self.detect_restricted_zone(tracked_objects, frame_shape))
        all_events.extend(self.detect_loitering(tracker, tracked_objects))
        all_events.extend(self.detect_unattended_object(tracked_objects))
        all_events.extend(self.detect_crowd(tracked_objects))
        
        return all_events
    
    def calculate_overall_risk(self, events: List[Dict]) -> int:
        """
        Calculate overall risk score from detected events
        
        Args:
            events: List of events
        
        Returns:
            Overall risk score (0-10)
        """
        if not events:
            return 0
        
        # Get maximum risk from current events
        max_risk = max(event.get('risk', 0) for event in events)
        
        # Cap at 10
        return min(max_risk, 10)