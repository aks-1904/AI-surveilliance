"""
Loitering Detection
Detects when persons stay in the same area for too long
"""

import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class LoiteringDetector:
    """Detects loitering behavior"""
    
    def __init__(self, config):
        self.config = config
        self.threshold_seconds = config.LOITERING_THRESHOLD_SECONDS
        self.distance_threshold = config.LOITERING_DISTANCE_THRESHOLD
        
        # Track person positions over time
        self.person_history = {}
        
        # Track active loitering events
        self.active_loitering = {}
    
    def detect(
        self, 
        persons: List[Dict],
        timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """
        Detect loitering behavior
        
        Args:
            persons: List of detected persons
            timestamp: Current timestamp
        
        Returns:
            List of loitering events
        """
        events = []
        current_person_ids = set()
        
        for person in persons:
            person_id = person['id']
            center = person['center']
            current_person_ids.add(person_id)
            
            # Initialize tracking for new persons
            if person_id not in self.person_history:
                self.person_history[person_id] = {
                    'first_seen': timestamp,
                    'positions': [center],
                    'last_position': center,
                    'last_update': timestamp
                }
                continue
            
            # Update existing person
            history = self.person_history[person_id]
            history['positions'].append(center)
            history['last_position'] = center
            history['last_update'] = timestamp
            
            # Keep only recent positions (last 100)
            if len(history['positions']) > 100:
                history['positions'] = history['positions'][-100:]
            
            # Calculate time spent in area
            time_spent = (timestamp - history['first_seen']).total_seconds()
            
            # Check if person has moved significantly
            has_moved = self._has_moved_significantly(history['positions'])
            
            # Detect loitering if:
            # 1. Person has been present for longer than threshold
            # 2. Person has not moved significantly
            if time_spent >= self.threshold_seconds and not has_moved:
                # Check if this is a new loitering event
                if person_id not in self.active_loitering:
                    event = {
                        'type': 'LOITERING',
                        'timestamp': timestamp.isoformat(),
                        'person_id': person_id,
                        'location': {
                            'x': center[0],
                            'y': center[1]
                        },
                        'duration': int(time_spent),
                        'details': {
                            'message': f"Person {person_id} loitering for {int(time_spent)} seconds",
                            'bbox': person['bbox'],
                            'start_time': history['first_seen'].isoformat()
                        }
                    }
                    
                    events.append(event)
                    self.active_loitering[person_id] = timestamp
                    logger.warning(f"Loitering detected: Person {person_id} for {int(time_spent)}s")
        
        # Clean up persons no longer visible
        to_remove = []
        for person_id in self.person_history:
            if person_id not in current_person_ids:
                # Remove if not seen for 5 seconds
                last_update = self.person_history[person_id]['last_update']
                if (timestamp - last_update).total_seconds() > 5:
                    to_remove.append(person_id)
        
        for person_id in to_remove:
            del self.person_history[person_id]
            if person_id in self.active_loitering:
                del self.active_loitering[person_id]
        
        return events
    
    def _has_moved_significantly(self, positions: List[tuple]) -> bool:
        """
        Check if person has moved significantly based on position history
        
        Args:
            positions: List of (x, y) positions
        
        Returns:
            True if person has moved significantly, False otherwise
        """
        if len(positions) < 2:
            return False
        
        # Calculate average position
        positions_array = np.array(positions)
        avg_position = np.mean(positions_array, axis=0)
        
        # Calculate maximum distance from average
        max_distance = 0
        for pos in positions:
            distance = np.sqrt(
                (pos[0] - avg_position[0])**2 + 
                (pos[1] - avg_position[1])**2
            )
            max_distance = max(max_distance, distance)
        
        # Person has moved significantly if max distance exceeds threshold
        return max_distance > self.distance_threshold
    
    def get_tracked_count(self) -> int:
        """Get number of currently tracked persons"""
        return len(self.person_history)
    
    def get_loitering_count(self) -> int:
        """Get number of active loitering events"""
        return len(self.active_loitering)
    
    def reset(self):
        """Reset all tracking"""
        self.person_history = {}
        self.active_loitering = {}