"""
Flask API Server
Provides HTTP endpoints for video streaming and control
"""

import cv2
import json
import requests
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import numpy as np
from pathlib import Path

from main.config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, BACKEND_EVENT_ENDPOINT, UPLOAD_DIR
from main.video_processor import VideoProcessor

app = Flask(__name__)
CORS(app)

# Global video processor instance
processor = None


def generate_frames():
    """
    Generator function for video streaming
    Yields MJPEG frames
    """
    global processor
    
    while True:
        if processor is None or not processor.is_running:
            # Send blank frame
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank, "No video source", (200, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank)
        else:
            frame = processor.get_current_frame()
            if frame is None:
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank, "Loading...", (250, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', blank)
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
        
        if ret:
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


def send_event_to_backend(event: dict):
    """
    Send detected event to backend API
    
    Args:
        event: Event dictionary
    """
    try:
        # Add metadata
        event['camera_id'] = 'camera_001'  # TODO: make configurable
        event['source'] = processor.source if processor else 'unknown'
        
        # Send to backend
        response = requests.post(
            BACKEND_EVENT_ENDPOINT,
            json=event,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"Event sent: {event['type']}")
        else:
            print(f"Failed to send event: {response.status_code}")
            
    except Exception as e:
        print(f"Error sending event to backend: {e}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'processor_running': processor.is_running if processor else False
    })


@app.route('/video', methods=['GET'])
def video_feed():
    """
    Video streaming endpoint
    Returns MJPEG stream
    """
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/start', methods=['POST'])
def start_processing():
    """
    Start video processing
    
    Request body:
    {
        "source": "rtsp://camera_url" or "/path/to/video.mp4",
        "source_type": "rtsp" or "file" (optional, auto-detected)
    }
    """
    global processor
    
    try:
        data = request.get_json()
        source = data.get('source')
        source_type = data.get('source_type', 'auto')
        
        if not source:
            return jsonify({'error': 'Source is required'}), 400
        
        # Stop existing processor if running
        if processor and processor.is_running:
            processor.stop()
        
        # Create new processor
        processor = VideoProcessor(source, source_type)
        processor.set_event_callback(send_event_to_backend)
        processor.start()
        
        return jsonify({
            'status': 'started',
            'source': source,
            'source_type': processor.source_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stop', methods=['POST'])
def stop_processing():
    """Stop video processing"""
    global processor
    
    if processor:
        processor.stop()
        return jsonify({'status': 'stopped'})
    
    return jsonify({'status': 'not running'})


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get processing statistics"""
    if processor:
        stats = processor.get_stats()
        stats['running'] = processor.is_running
        stats['source'] = processor.source
        return jsonify(stats)
    
    return jsonify({'error': 'No processor active'}), 404


@app.route('/upload', methods=['POST'])
def upload_video():
    """
    Upload video file for processing
    
    Form data:
        file: Video file
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Save file
        filename = Path(file.filename).name
        filepath = UPLOAD_DIR / filename
        file.save(filepath)
        
        # Start processing the uploaded file
        global processor
        
        if processor and processor.is_running:
            processor.stop()
        
        processor = VideoProcessor(str(filepath), 'file')
        processor.set_event_callback(send_event_to_backend)
        processor.start()
        
        return jsonify({
            'status': 'uploaded and processing',
            'filename': filename,
            'filepath': str(filepath)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    from config import (
        CONFIDENCE_THRESHOLD, CLASSES_OF_INTEREST,
        LOITERING_THRESHOLD, CROWD_THRESHOLD,
        ENABLE_FACE_BLUR, ENABLE_TRACKING
    )
    
    return jsonify({
        'confidence_threshold': CONFIDENCE_THRESHOLD,
        'classes': list(CLASSES_OF_INTEREST.values()),
        'loitering_threshold': LOITERING_THRESHOLD,
        'crowd_threshold': CROWD_THRESHOLD,
        'face_blur_enabled': ENABLE_FACE_BLUR,
        'tracking_enabled': ENABLE_TRACKING
    })


if __name__ == '__main__':
    print(f"Starting AI Video Processing Service on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, threaded=True)