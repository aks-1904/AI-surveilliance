"""
AI Surveillance Co-Pilot - Main Application
Real-time video intelligence service.
"""

from flask import Flask, jsonify, request, Response, send_file
import cv2
import threading
import time
import logging
import os
import uuid
from datetime import datetime

from detection.person_detector   import PersonDetector
from analysis.zone_analyzer      import ZoneAnalyzer
from analysis.loitering_detector import LoiteringDetector
from analysis.object_detector    import UnattendedObjectDetector
from analysis.footage_analyzer   import FootageAnalyzer
from detection.weapon_detector   import WeaponDetector
from risk.risk_engine            import RiskEngine
from utils.config                import Config
from utils.event_publisher       import EventPublisher
from utils.events_cooldown        import EventCooldownManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# ------------------------------------------------------------------ #
# Global state
# ------------------------------------------------------------------ #
camera            = None
is_running        = False
processing_thread = None
restricted_zones  = []
footage_jobs: dict = {}
OUTPUT_DIR = os.getenv('FOOTAGE_OUTPUT_DIR', './footage_output')

# ------------------------------------------------------------------ #
# Component initialisation
# ------------------------------------------------------------------ #
config = Config()

# Cooldown manager — shared by all components that need it
cooldown_manager = EventCooldownManager(config)

person_detector          = PersonDetector(config)
zone_analyzer            = ZoneAnalyzer(
    exit_grace_sec=config.ZONE_EXIT_GRACE_SEC
)
loitering_detector       = LoiteringDetector(config, cooldown_manager=cooldown_manager)
unattended_object_detector = UnattendedObjectDetector(config, cooldown_manager=cooldown_manager)
weapon_detector          = WeaponDetector(config)
risk_engine              = RiskEngine(config)
event_publisher          = EventPublisher(config)
footage_analyzer         = FootageAnalyzer(
    config, person_detector, zone_analyzer,
    loitering_detector, unattended_object_detector, risk_engine
)


# ------------------------------------------------------------------ #
# Streaming helper
# ------------------------------------------------------------------ #
def generate_frames():
    global camera, is_running
    while is_running:
        success, frame = camera.read()
        if not success:
            continue
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
        )


# ------------------------------------------------------------------ #
# Main processing loop
# ------------------------------------------------------------------ #
def video_processing_loop():
    global camera, is_running

    logger.info("Starting video processing loop…")

    while is_running:
        ret, frame = camera.read()
        if not ret:
            logger.error("Failed to read frame from camera")
            time.sleep(0.1)
            continue

        timestamp = datetime.now()

        try:
            # 1. Detect persons
            persons            = person_detector.detect(frame)
            suspicious_persons = [p for p in persons if not p.get('is_whitelisted', False)]

            # 2. Zone intrusions
            zone_events = zone_analyzer.check_intrusions(
                suspicious_persons, restricted_zones, timestamp
            )

            # 3. Loitering
            loitering_events = loitering_detector.detect(suspicious_persons, timestamp)

            # 4. Unattended objects
            unattended_events = unattended_object_detector.detect(frame, persons, timestamp)

            # 5. Weapons
            weapon_events = weapon_detector.detect(frame, timestamp)

            # 6. Risk score
            all_events = zone_events + loitering_events + unattended_events + weapon_events
            risk_score, risk_level = risk_engine.calculate_risk(all_events)

            # 7. Publish — filtered through the global cooldown manager
            for event in all_events:
                if cooldown_manager.should_fire(event):
                    event_publisher.publish_event(event, risk_score, risk_level)
                    logger.info(f"Event published: {event['type']} — Risk: {risk_level}")
                else:
                    logger.debug(f"Event suppressed by cooldown: {event['type']}")

            # 8. Optional debug display
            if config.DEBUG_MODE:
                _draw_debug(frame, persons, risk_score, risk_level)

            time.sleep(0.03)  # ~30 fps

        except Exception as e:
            logger.error(f"Error processing frame: {e}", exc_info=True)

    logger.info("Video processing loop stopped")
    if config.DEBUG_MODE:
        cv2.destroyAllWindows()


def _draw_debug(frame, persons, risk_score, risk_level):
    display = frame.copy()
    for person in persons:
        x1, y1, x2, y2 = person['bbox']
        cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(display, f"ID:{person['id']}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        logger.info(person)
        if 'attributes' in person and person['attributes']:
            logger.info("HELLO")
            attr = person['attributes']
            info_text = f"Top: {attr.get('upper_clothing_color', 'N/A')} | Build: {attr.get('body_type', 'N/A')}"

            # Draw a tiny black background box for readability
            cv2.rectangle(display, (x1, y2 + 5), (x1 + 250, y2 + 25), (0, 0, 0), -1)
            cv2.putText(display, info_text, (x1 + 5, y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    for zone in restricted_zones:
        cv2.polylines(display, [zone['polygon']], True, (0, 0, 255), 2)
    color = (0, 255, 0) if risk_level == 'LOW' else (0, 165, 255) if risk_level == 'MEDIUM' else (0, 0, 255)
    cv2.putText(display, f"Risk: {risk_level} ({risk_score})", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow('AI Surveillance Co-Pilot', display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        pass


# ------------------------------------------------------------------ #
# Footage analysis jobs
# ------------------------------------------------------------------ #
def _run_footage_job(job_id: str, input_path: str, zones: list):
    footage_jobs[job_id]['status'] = 'running'
    output_video = os.path.join(OUTPUT_DIR, f"{job_id}_highlight.mp4")
    summary_file = os.path.join(OUTPUT_DIR, f"{job_id}_summary.txt")

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
            'result': {
                'total_events':       result['stats']['total_events'],
                'risk_segment_count': result['stats']['risk_segment_count'],
                'total_risk_seconds': result['stats']['total_risk_seconds'],
                'event_counts':       result['stats']['event_counts'],
                'output_video':       output_video,
                'summary_file':       summary_file,
                'duration_seconds':   result['duration_seconds'],
            },
        })
    except Exception as exc:
        logger.error(f"Footage job {job_id} failed: {exc}", exc_info=True)
        footage_jobs[job_id].update({'status': 'error', 'error': str(exc)})


# ------------------------------------------------------------------ #
# Routes
# ------------------------------------------------------------------ #
@app.route('/health')
def health_check():
    return jsonify({
        'status':            'healthy',
        'service':           'AI Surveillance Co-Pilot',
        'camera_active':     is_running,
        'zones_configured':  len(restricted_zones),
    })


@app.route('/start', methods=['POST'])
def start_camera():
    global camera, is_running, processing_thread
    if is_running:
        return jsonify({'error': 'Camera already running'}), 400
    try:
        camera = cv2.VideoCapture(config.CAMERA_INDEX)
        if not camera.isOpened():
            return jsonify({'error': 'Failed to open camera'}), 500
        camera.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS,          config.FPS)
        is_running = True
        processing_thread = threading.Thread(target=video_processing_loop, daemon=True)
        processing_thread.start()
        return jsonify({'message': 'Camera started successfully'})
    except Exception as e:
        logger.error(f"Error starting camera: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/stop', methods=['POST'])
def stop_camera():
    global camera, is_running, processing_thread
    if not is_running:
        return jsonify({'error': 'Camera not running'}), 400
    is_running = False
    if processing_thread:
        processing_thread.join(timeout=5)
    if camera:
        camera.release()
        camera = None
    return jsonify({'message': 'Camera stopped successfully'})


@app.route('/zones', methods=['POST'])
def add_zone():
    global restricted_zones
    data = request.json
    if 'polygon' not in data or 'name' not in data:
        return jsonify({'error': 'Missing polygon or name'}), 400
    import numpy as np
    polygon = np.array([[p['x'], p['y']] for p in data['polygon']], np.int32)
    if len(polygon) < 3:
        return jsonify({'error': 'Polygon must have at least 3 points'}), 400
    zone = {
        'id':         len(restricted_zones) + 1,
        'name':       data['name'],
        'polygon':    polygon,
        'created_at': datetime.now().isoformat(),
    }
    restricted_zones.append(zone)
    return jsonify({'message': 'Zone added successfully',
                    'zone': {'id': zone['id'], 'name': zone['name'], 'points': len(polygon)}})


@app.route('/zones', methods=['GET'])
def get_zones():
    return jsonify({'zones': [
        {'id': z['id'], 'name': z['name'],
         'polygon': z['polygon'].tolist(), 'created_at': z['created_at']}
        for z in restricted_zones
    ]})


@app.route('/zones/<int:zone_id>', methods=['DELETE'])
def delete_zone(zone_id):
    global restricted_zones
    restricted_zones = [z for z in restricted_zones if z['id'] != zone_id]
    return jsonify({'message': 'Zone deleted successfully'})


@app.route('/stats')
def get_stats():
    return jsonify({
        'loitering_tracked':  loitering_detector.get_tracked_count(),
        'unattended_objects': unattended_object_detector.get_tracked_count(),
        'current_risk':       risk_engine.get_current_risk(),
        'zones_count':        len(restricted_zones),
    })


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/reset', methods=['POST'])
def reset_system():
    loitering_detector.reset()
    unattended_object_detector.reset()
    risk_engine.reset()
    zone_analyzer.reset()
    return jsonify({'message': 'System reset successfully'})


# ---- Footage analysis ---- #

@app.route('/footage/analyze', methods=['POST'])
def analyze_footage():
    input_path = None
    use_zones  = True

    if 'file' in request.files:
        f = request.files['file']
        if f.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        upload_dir = os.path.join(OUTPUT_DIR, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        safe_name  = f"{uuid.uuid4()}_{f.filename}"
        input_path = os.path.join(upload_dir, safe_name)
        f.save(input_path)
        use_zones = request.form.get('use_zones', 'true').lower() == 'true'

    elif request.is_json:
        data       = request.json
        input_path = data.get('filepath')
        use_zones  = data.get('use_zones', True)
        if not input_path or not os.path.exists(input_path):
            return jsonify({'error': 'filepath missing or not found'}), 400
    else:
        return jsonify({'error': 'Send a video file (multipart) or JSON {filepath}'}), 400

    zones  = restricted_zones if use_zones else []
    job_id = str(uuid.uuid4())
    footage_jobs[job_id] = {'status': 'queued', 'progress': 0, 'result': None, 'error': None}
    threading.Thread(target=_run_footage_job, args=(job_id, input_path, zones), daemon=True).start()
    return jsonify({'job_id': job_id, 'status': 'queued'}), 202


@app.route('/footage/status/<job_id>')
def footage_job_status(job_id):
    job = footage_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({'job_id': job_id, **job})


@app.route('/footage/download/<job_id>/video')
def download_highlight_video(job_id):
    job = footage_jobs.get(job_id)
    if not job or job['status'] != 'done':
        return jsonify({'error': 'Job not ready'}), 404
    path = job['result']['output_video']
    if not os.path.exists(path):
        return jsonify({'error': 'File not found on disk'}), 404
    return send_file(path, mimetype='video/mp4', as_attachment=True,
                     download_name=f"highlights_{job_id}.mp4")


@app.route('/footage/download/<job_id>/summary')
def download_summary(job_id):
    job = footage_jobs.get(job_id)
    if not job or job['status'] != 'done':
        return jsonify({'error': 'Job not ready'}), 404
    path = job['result']['summary_file']
    if not os.path.exists(path):
        return jsonify({'error': 'File not found on disk'}), 404
    return send_file(path, mimetype='text/plain', as_attachment=True,
                     download_name=f"summary_{job_id}.txt")


@app.route('/footage/jobs')
def list_footage_jobs():
    slim = {jid: {k: v for k, v in info.items() if k != 'result'}
            for jid, info in footage_jobs.items()}
    return jsonify({'jobs': slim})


# ------------------------------------------------------------------ #
# Entry point
# ------------------------------------------------------------------ #
if __name__ == '__main__':
    logger.info("Starting AI Surveillance Co-Pilot Service…")
    app.run(host='0.0.0.0', port=config.PORT, debug=False, threaded=True)