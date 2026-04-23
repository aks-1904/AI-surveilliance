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
import os
import uuid
from datetime import datetime

from detection.person_detector import PersonDetector
# from detection.face_blur import FaceBlurrer
from analysis.zone_analyzer import ZoneAnalyzer
from analysis.loitering_detector import LoiteringDetector
from analysis.object_detector import UnattendedObjectDetector
from risk.risk_engine import RiskEngine
from utils.config import Config
from utils.event_publisher import EventPublisher
from analysis.footage_analyzer import FootageAnalyzer

from flask import Response

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
footage_analyzer = None
footage_jobs = {}
OUTPUT_DIR = os.getenv('FOOTAGE_OUTPUT_DIR', './footage_output')

# Initialize components
config = Config()
person_detector = PersonDetector(config)
# face_blurrer = FaceBlurrer(config)
zone_analyzer = ZoneAnalyzer()
loitering_detector = LoiteringDetector(config)
unattended_object_detector = UnattendedObjectDetector(config)
risk_engine = RiskEngine(config)
event_publisher = EventPublisher(config)
footage_analyzer = FootageAnalyzer(
    config, person_detector, zone_analyzer,
    loitering_detector, unattended_object_detector, risk_engine
)
footage_jobs = {}   # job_id -> status dict

def generate_frames():
    global camera, is_running

    while is_running:
        success, frame = camera.read()
        if not success:
            continue

        # frame = face_blurrer.blur_faces(frame)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


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

            # Separate whitelisted and suspecious persons
            suspicious_persons = [p for p in persons if not p.get('is_whitelisted', False)]
            whitelisted_persons = [p for p in persons if p.get('is_whitelisted', False)]
            
            # Step 2: Check zone intrusions
            zone_events = zone_analyzer.check_intrusions(
                suspicious_persons, 
                restricted_zones, 
                timestamp
            )
            
            # Step 3: Detect loitering
            loitering_events = loitering_detector.detect(
                suspicious_persons, 
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
            # frame = face_blurrer.blur_faces(frame)
            
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

def _run_footage_job(job_id: str, input_path: str, zones: list):
    """Background worker for footage analysis."""
    footage_jobs[job_id]['status'] = 'running'
 
    output_video   = os.path.join(OUTPUT_DIR, f"{job_id}_highlight.mp4")
    summary_file   = os.path.join(OUTPUT_DIR, f"{job_id}_summary.txt")
 
    def _progress(pct):
        footage_jobs[job_id]['progress'] = pct
 
    try:
        result = footage_analyzer.analyze(
            input_video_path  = input_path,
            output_video_path = output_video,
            summary_path      = summary_file,
            restricted_zones  = zones,
            progress_callback = _progress,
        )
        footage_jobs[job_id].update({
            'status':   'done',
            'progress': 100,
            'result':   {
                'total_events':       result['stats']['total_events'],
                'risk_segment_count': result['stats']['risk_segment_count'],
                'total_risk_seconds': result['stats']['total_risk_seconds'],
                'event_counts':       result['stats']['event_counts'],
                'output_video':       output_video,
                'summary_file':       summary_file,
                'duration_seconds':   result['duration_seconds'],
            }
        })
    except Exception as exc:
        logger.error(f"Footage job {job_id} failed: {exc}", exc_info=True)
        footage_jobs[job_id].update({'status': 'error', 'error': str(exc)})


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
    polygon = np.array([[p["x"], p["y"]] for p in data["polygon"]], np.int32)
    
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

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame")



@app.route('/reset', methods=['POST'])
def reset_system():
    """Reset all tracking and statistics"""
    loitering_detector.reset()
    unattended_object_detector.reset()
    risk_engine.reset()
    
    logger.info("System reset completed")
    return jsonify({'message': 'System reset successfully'})

@app.route('/footage/analyze', methods=['POST'])
def analyze_footage():
    """
    Start a footage analysis job.
 
    Accepts multipart/form-data:
        file      – the video file (required)
        use_zones – "true"/"false" — whether to apply currently configured zones (default true)
 
    OR application/json:
        { "filepath": "/absolute/path/to/video.mp4", "use_zones": true }
 
    Returns: { job_id, status }
    """
    use_zones = True
    input_path = None
 
    # -- Uploaded file --
    if 'file' in request.files:
        f = request.files['file']
        if f.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
 
        upload_dir = os.path.join(OUTPUT_DIR, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        safe_name  = f"{uuid.uuid4()}_{f.filename}"
        input_path = os.path.join(upload_dir, safe_name)
        f.save(input_path)
        use_zones  = request.form.get('use_zones', 'true').lower() == 'true'
 
    # -- JSON body with filepath --
    elif request.is_json:
        data = request.json
        input_path = data.get('filepath')
        use_zones  = data.get('use_zones', True)
        if not input_path or not os.path.exists(input_path):
            return jsonify({'error': 'filepath missing or file not found'}), 400
    else:
        return jsonify({'error': 'Send a video file (multipart) or JSON {filepath}'}), 400
 
    zones = restricted_zones if use_zones else []
    job_id = str(uuid.uuid4())
    footage_jobs[job_id] = {'status': 'queued', 'progress': 0, 'result': None, 'error': None}
 
    t = threading.Thread(target=_run_footage_job, args=(job_id, input_path, zones), daemon=True)
    t.start()
 
    logger.info(f"Footage job {job_id} started for: {input_path}")
    return jsonify({'job_id': job_id, 'status': 'queued'}), 202

@app.route('/footage/status/<job_id>', methods=['GET'])
def footage_job_status(job_id: str):
    """Poll analysis progress.  Returns { job_id, status, progress, result?, error? }"""
    job = footage_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({'job_id': job_id, **job})

@app.route('/footage/download/<job_id>/video', methods=['GET'])
def download_highlight_video(job_id: str):
    """Download the highlight reel for a completed job."""
    from flask import send_file
    job = footage_jobs.get(job_id)
    if not job or job['status'] != 'done':
        return jsonify({'error': 'Job not ready'}), 404
    path = job['result']['output_video']
    if not os.path.exists(path):
        return jsonify({'error': 'File not found on disk'}), 404
    return send_file(path, mimetype='video/mp4', as_attachment=True,
                     download_name=f"highlights_{job_id}.mp4")

@app.route('/footage/download/<job_id>/summary', methods=['GET'])
def download_summary(job_id: str):
    """Download the text summary for a completed job."""
    from flask import send_file
    job = footage_jobs.get(job_id)
    if not job or job['status'] != 'done':
        return jsonify({'error': 'Job not ready'}), 404
    path = job['result']['summary_file']
    if not os.path.exists(path):
        return jsonify({'error': 'File not found on disk'}), 404
    return send_file(path, mimetype='text/plain', as_attachment=True,
                     download_name=f"summary_{job_id}.txt")

@app.route('/footage/jobs', methods=['GET'])
def list_footage_jobs():
    """List all jobs (without heavy result data)."""
    slim = {
        jid: {k: v for k, v in info.items() if k != 'result'}
        for jid, info in footage_jobs.items()
    }
    return jsonify({'jobs': slim})


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