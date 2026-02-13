"""
Risk Scoring Engine
Calculates overall risk score based on detected events
"""

import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class RiskEngine:
    """Calculates risk scores based on detected events"""
    
    def __init__(self, config):
        self.config = config
        self.risk_scores = config.RISK_SCORES
        self.risk_level_low = config.RISK_LEVEL_LOW
        self.risk_level_medium = config.RISK_LEVEL_MEDIUM
        
        # Track current risk
        self.current_risk_score = 0
        self.current_risk_level = "LOW"
        self.active_events = []
    
    def calculate_risk(self, events: List[Dict]) -> Tuple[int, str]:
        """
        Calculate risk score based on events
        
        Args:
            events: List of detected events
        
        Returns:
            Tuple of (risk_score, risk_level)
        """
        if not events:
            self.current_risk_score = 0
            self.current_risk_level = "LOW"
            return 0, "LOW"
        
        # Calculate total risk
        total_risk = 0
        
        for event in events:
            event_type = event['type']
            
            if event_type == 'RESTRICTED_ENTRY':
                total_risk += self.risk_scores['RESTRICTED_ENTRY']
            elif event_type == 'UNATTENDED_OBJECT':
                total_risk += self.risk_scores['UNATTENDED_OBJECT']
            elif event_type == 'LOITERING':
                total_risk += self.risk_scores['LOITERING']
        
        # Determine risk level
        if total_risk <= self.risk_level_low:
            risk_level = "LOW"
        elif total_risk <= self.risk_level_medium:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Update current state
        self.current_risk_score = total_risk
        self.current_risk_level = risk_level
        self.active_events = events
        
        return total_risk, risk_level
    
    def get_current_risk(self) -> Dict:
        """Get current risk information"""
        return {
            'score': self.current_risk_score,
            'level': self.current_risk_level,
            'event_count': len(self.active_events)
        }
    
    def get_risk_breakdown(self) -> Dict:
        """Get detailed risk breakdown by event type"""
        breakdown = {
            'RESTRICTED_ENTRY': 0,
            'UNATTENDED_OBJECT': 0,
            'LOITERING': 0
        }
        
        for event in self.active_events:
            event_type = event['type']
            if event_type in breakdown:
                breakdown[event_type] += 1
        
        return breakdown
    
    def get_risk_color(self) -> str:
        """Get color code for current risk level"""
        colors = {
            'LOW': '#22C55E',      # Green
            'MEDIUM': '#F59E0B',   # Orange
            'HIGH': '#EF4444'      # Red
        }
        return colors.get(self.current_risk_level, '#6B7280')
    
    def is_high_risk(self) -> bool:
        """Check if current risk is high"""
        return self.current_risk_level == "HIGH"
    
    def reset(self):
        """Reset risk tracking"""
        self.current_risk_score = 0
        self.current_risk_level = "LOW"
        self.active_events = []