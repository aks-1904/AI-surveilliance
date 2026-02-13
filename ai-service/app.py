"""
AI Surveillance Co-Pilot - Main Application
Real-time video intelligence service with person detection, zone intrusion, loitering, and unattended object detection.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import cv2
import threading
import time
import logging
from datetime import datetime

from detection.person_detector import PersonDetector
from detection.face_blur import FaceBlurrer
from analysis.zone_analyzer import ZoneAnalyzer
from analysis.loitering_detector import LoiteringDetector
from analysis.object_detector import UnattendedObjectDetector
from risk.risk_engine import RiskEngine
from utils.config import Config
from utils.event_publisher import EventPublisher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global state
camera = None
is_running = False
processing_thread = None
restricted_zones = []

# Initialize components
config = Config()
person_detector = PersonDetector(config)
face_blurrer = FaceBlurrer(config)
zone_analyzer = ZoneAnalyzer()
loitering_detector = LoiteringDetector(config)
unattended_object_detector = UnattendedObjectDetector(config)
risk_engine = RiskEngine(config)
event_publisher = EventPublisher(config)


def video_processing_loop():
    """Main video processing loop - runs in separate thread"""
    global camera, is_running
    
    logger.info("Starting video processing loop...")
    frame_count = 0
    
    while is_running:
        ret, frame = camera.read()
        if not ret:
            logger.error("Failed to read frame from camera")
            time.sleep(0.1)
            continue
        
        frame_count += 1
        timestamp = datetime.now()
        
        try:
            # Step 1: Detect persons
            persons = person_detector.detect(frame)
            
            # Step 2: Check zone intrusions
            zone_events = zone_analyzer.check_intrusions(
                persons, 
                restricted_zones, 
                timestamp
            )
            
            # Step 3: Detect loitering
            loitering_events = loitering_detector.detect(
                persons, 
                timestamp
            )
            
            # Step 4: Detect unattended objects
            unattended_events = unattended_object_detector.detect(
                frame,
                persons,
                timestamp
            )
            
            # Step 5: Calculate risk score
            all_events = zone_events + loitering_events + unattended_events
            risk_score, risk_level = risk_engine.calculate_risk(all_events)
            
            # Step 6: Publish events to backend
            if all_events:
                for event in all_events:
                    event_publisher.publish_event(event, risk_score, risk_level)
                    logger.info(f"Event detected: {event['type']} - Risk: {risk_level}")
            
            # Step 7: Apply face blur for privacy
            frame = face_blurrer.blur_faces(frame)
            
            # Optional: Display for debugging (disable in production)
            if config.DEBUG_MODE:
                # Draw bounding boxes and zones
                display_frame = frame.copy()
                
                # Draw persons
                for person in persons:
                    x1, y1, x2, y2 = person['bbox']
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        display_frame, 
                        f"ID: {person['id']}", 
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.5, 
                        (0, 255, 0), 
                        2
                    )
                
                # Draw restricted zones
                for zone in restricted_zones:
                    pts = zone['polygon']
                    cv2.polylines(display_frame, [pts], True, (0, 0, 255), 2)
                
                # Show risk level
                color = (0, 255, 0) if risk_level == "LOW" else (0, 165, 255) if risk_level == "MEDIUM" else (0, 0, 255)
                cv2.putText(
                    display_frame,
                    f"Risk: {risk_level} ({risk_score})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    color,
                    2
                )
                
                cv2.imshow('AI Surveillance Co-Pilot', display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Control frame rate
            time.sleep(0.03)  # ~30 FPS
            
        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}", exc_info=True)
            continue
    
    logger.info("Video processing loop stopped")
    if config.DEBUG_MODE:
        cv2.destroyAllWindows()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Surveillance Co-Pilot',
        'camera_active': is_running,
        'zones_configured': len(restricted_zones)
    })


@app.route('/start', methods=['POST'])
def start_camera():
    """Start camera and video processing"""
    global camera, is_running, processing_thread
    
    if is_running:
        return jsonify({'error': 'Camera already running'}), 400
    
    try:
        camera = cv2.VideoCapture(config.CAMERA_INDEX)
        
        if not camera.isOpened():
            return jsonify({'error': 'Failed to open camera'}), 500
        
        # Set camera properties
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, config.FPS)
        
        is_running = True
        processing_thread = threading.Thread(target=video_processing_loop, daemon=True)
        processing_thread.start()
        
        logger.info("Camera started successfully")
        return jsonify({'message': 'Camera started successfully'})
        
    except Exception as e:
        logger.error(f"Error starting camera: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/stop', methods=['POST'])
def stop_camera():
    """Stop camera and video processing"""
    global camera, is_running, processing_thread
    
    if not is_running:
        return jsonify({'error': 'Camera not running'}), 400
    
    is_running = False
    
    if processing_thread:
        processing_thread.join(timeout=5)
    
    if camera:
        camera.release()
        camera = None
    
    logger.info("Camera stopped successfully")
    return jsonify({'message': 'Camera stopped successfully'})


@app.route('/zones', methods=['POST'])
def add_zone():
    """Add a restricted zone"""
    global restricted_zones
    
    data = request.json
    
    if 'polygon' not in data or 'name' not in data:
        return jsonify({'error': 'Missing polygon or name'}), 400
    
    import numpy as np
    polygon = np.array(data['polygon'], dtype=np.int32)
    
    if len(polygon) < 3:
        return jsonify({'error': 'Polygon must have at least 3 points'}), 400
    
    zone = {
        'id': len(restricted_zones) + 1,
        'name': data['name'],
        'polygon': polygon,
        'created_at': datetime.now().isoformat()
    }
    
    restricted_zones.append(zone)
    logger.info(f"Zone added: {zone['name']} with {len(polygon)} points")
    
    return jsonify({
        'message': 'Zone added successfully',
        'zone': {
            'id': zone['id'],
            'name': zone['name'],
            'points': len(polygon)
        }
    })


@app.route('/zones', methods=['GET'])
def get_zones():
    """Get all restricted zones"""
    zones_data = [
        {
            'id': z['id'],
            'name': z['name'],
            'polygon': z['polygon'].tolist(),
            'created_at': z['created_at']
        }
        for z in restricted_zones
    ]
    return jsonify({'zones': zones_data})


@app.route('/zones/<int:zone_id>', methods=['DELETE'])
def delete_zone(zone_id):
    """Delete a restricted zone"""
    global restricted_zones
    
    restricted_zones = [z for z in restricted_zones if z['id'] != zone_id]
    logger.info(f"Zone {zone_id} deleted")
    
    return jsonify({'message': 'Zone deleted successfully'})


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get current statistics"""
    return jsonify({
        'loitering_tracked': loitering_detector.get_tracked_count(),
        'unattended_objects': unattended_object_detector.get_tracked_count(),
        'current_risk': risk_engine.get_current_risk(),
        'zones_count': len(restricted_zones)
    })


@app.route('/reset', methods=['POST'])
def reset_system():
    """Reset all tracking and statistics"""
    loitering_detector.reset()
    unattended_object_detector.reset()
    risk_engine.reset()
    
    logger.info("System reset completed")
    return jsonify({'message': 'System reset successfully'})


if __name__ == '__main__':
    logger.info("Starting AI Surveillance Co-Pilot Service...")
    logger.info(f"Backend URL: {config.BACKEND_URL}")
    logger.info(f"Debug Mode: {config.DEBUG_MODE}")
    
    app.run(
        host='0.0.0.0',
        port=config.PORT,
        debug=False,  # Never use debug=True with camera
        threaded=True
    )