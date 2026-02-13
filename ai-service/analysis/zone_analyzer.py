"""
Zone Analyzer
Checks if persons enter restricted zones
"""

import cv2
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ZoneAnalyzer:
    """Analyzes person positions relative to restricted zones"""
    
    def __init__(self):
        self.active_intrusions = {}  # Track ongoing intrusions
    
    def check_intrusions(
        self, 
        persons: List[Dict], 
        zones: List[Dict],
        timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """
        Check if any person has entered a restricted zone
        
        Args:
            persons: List of detected persons with centers
            zones: List of restricted zones with polygons
            timestamp: Current timestamp
        
        Returns:
            List of intrusion events
        """
        events = []
        current_intrusions = set()
        
        for person in persons:
            person_id = person['id']
            center = person['center']
            
            for zone in zones:
                zone_id = zone['id']
                polygon = zone['polygon']
                
                # Check if person center is inside zone polygon
                result = cv2.pointPolygonTest(
                    polygon,
                    center,
                    False
                )
                
                if result >= 0:  # Inside or on boundary
                    intrusion_key = f"{person_id}_{zone_id}"
                    current_intrusions.add(intrusion_key)
                    
                    # Create event only if it's a new intrusion
                    if intrusion_key not in self.active_intrusions:
                        event = {
                            'type': 'RESTRICTED_ENTRY',
                            'timestamp': timestamp.isoformat(),
                            'person_id': person_id,
                            'zone_id': zone_id,
                            'zone_name': zone['name'],
                            'location': {
                                'x': center[0],
                                'y': center[1]
                            },
                            'details': {
                                'message': f"Person {person_id} entered restricted zone: {zone['name']}",
                                'bbox': person['bbox']
                            }
                        }
                        
                        events.append(event)
                        logger.warning(f"Zone intrusion: Person {person_id} in {zone['name']}")
                    
                    self.active_intrusions[intrusion_key] = timestamp
        
        # Clean up intrusions that are no longer active
        to_remove = []
        for key in self.active_intrusions:
            if key not in current_intrusions:
                to_remove.append(key)
        
        for key in to_remove:
            del self.active_intrusions[key]
        
        return events
    
    def is_point_in_zone(self, point: tuple, zone_polygon: np.ndarray) -> bool:
        """
        Check if a point is inside a zone
        
        Args:
            point: (x, y) coordinates
            zone_polygon: Zone polygon as numpy array
        
        Returns:
            True if point is inside zone, False otherwise
        """
        result = cv2.pointPolygonTest(zone_polygon, point, False)
        return result >= 0
    
    def get_zone_by_id(self, zones: List[Dict], zone_id: int) -> Dict:
        """Get zone by ID"""
        for zone in zones:
            if zone['id'] == zone_id:
                return zone
        return None
    
    def reset(self):
        """Reset active intrusions"""
        self.active_intrusions = {}