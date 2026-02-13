"""
Event Publisher
Sends detected events to the backend via HTTP
"""

import requests
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes events to the backend"""
    
    def __init__(self, config):
        self.config = config
        self.backend_url = config.BACKEND_EVENT_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Surveillance-Service/1.0'
        })
    
    def publish_event(self, event: Dict[str, Any], risk_score: int, risk_level: str) -> bool:
        """
        Publish an event to the backend
        
        Args:
            event: Event dictionary with type, location, etc.
            risk_score: Current risk score
            risk_level: Current risk level (LOW, MEDIUM, HIGH)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = {
                'event_type': event['type'],
                'timestamp': event['timestamp'],
                'location': event.get('location', {}),
                'details': event.get('details', {}),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'metadata': {
                    'person_id': event.get('person_id'),
                    'object_id': event.get('object_id'),
                    'zone_id': event.get('zone_id'),
                    'duration': event.get('duration')
                }
            }
            
            response = self.session.post(
                self.backend_url,
                json=payload,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logger.debug(f"Event published successfully: {event['type']}")
                return True
            else:
                logger.warning(
                    f"Failed to publish event. Status: {response.status_code}, "
                    f"Response: {response.text}"
                )
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout while publishing event to backend")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Connection error while publishing event to backend")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing event: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to backend"""
        try:
            # Try to reach backend health endpoint
            health_url = f"{self.config.BACKEND_URL}/api/health"
            response = self.session.get(health_url, timeout=5)
            return response.status_code == 200
        except:
            return False