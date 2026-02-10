"""
Video Processor - Core AI processing module
Handles both RTSP streams and recorded video files
"""

import cv2
import time
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, List
import numpy as np
from ultralytics import YOLO

from config import (
    YOLO_MODEL, CONFIDENCE_THRESHOLD, CLASSES_OF_INTEREST,
    ENABLE_FACE_BLUR, ENABLE_TRACKING, FRAME_SKIP,
    MAX_FRAME_WIDTH, MAX_FRAME_HEIGHT, RTSP_RECONNECT_DELAY, RESTRICTED_ZONES
)
from support.tracker import ObjectTracker
from support.event_detector import EventDetector
from support.utils import resize_frame, draw_bbox, draw_polygon, blur_region
from support.privacy import FaceBlurrer


class VideoProcessor:
    """
    Main video processing class
    Handles detection, tracking, and event detection for both live and recorded video
    """
    
    def __init__(self, source: str, source_type: str = "auto"):
        """
        Initialize video processor
        
        Args:
            source: Video source (RTSP URL or file path)
            source_type: "rtsp", "file", or "auto" (auto-detect)
        """
        self.source = source
        self.source_type = self._detect_source_type(source) if source_type == "auto" else source_type
        
        # Video capture
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Frame info
        self.fps = 30
        self.frame_width = 0
        self.frame_height = 0
        self.frame_count = 0
        
        # AI Models
        self.model = None
        self.tracker = ObjectTracker() if ENABLE_TRACKING else None
        self.event_detector = EventDetector()
        self.face_blurrer = FaceBlurrer() if ENABLE_FACE_BLUR else None
        
        # Callbacks
        self.on_event_callback = None
        self.on_frame_callback = None
        
        # Stats
        self.stats = {
            'total_frames': 0,
            'processed_frames': 0,
            'detections': 0,
            'events': 0,
            'fps': 0,
            'processing_time': 0
        }
        
    def _detect_source_type(self, source: str) -> str:
        """
        Auto-detect source type
        
        Args:
            source: Video source
        
        Returns:
            "rtsp" or "file"
        """
        if source.startswith("rtsp://") or source.startswith("rtmp://"):
            return "rtsp"
        elif Path(source).is_file():
            return "file"
        else:
            # Assume RTSP if not a file
            return "rtsp"
    
    def load_model(self):
        """Load YOLO model"""
        print(f"Loading YOLO model: {YOLO_MODEL}")
        self.model = YOLO(YOLO_MODEL)
        print("Model loaded successfully")
    
    def connect(self) -> bool:
        """
        Connect to video source
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Connecting to {self.source_type} source: {self.source}")
            self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                print(f"Failed to open video source: {self.source}")
                return False
            
            # Get video properties
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"Connected: {self.frame_width}x{self.frame_height} @ {self.fps:.2f} FPS")
            return True
            
        except Exception as e:
            print(f"Error connecting to video source: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from video source"""
        if self.cap:
            self.cap.release()
            self.cap = None
            print("Disconnected from video source")
    
    def set_event_callback(self, callback: Callable):
        """
        Set callback function for events
        
        Args:
            callback: Function to call when events are detected
        """
        self.on_event_callback = callback
    
    def set_frame_callback(self, callback: Callable):
        """
        Set callback function for processed frames
        
        Args:
            callback: Function to call with each processed frame
        """
        self.on_frame_callback = callback
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict], List[Dict]]:
        """
        Process a single frame
        
        Args:
            frame: Input frame
        
        Returns:
            Tuple of (processed_frame, detections, events)
        """
        start_time = time.time()
        
        # Resize if needed
        frame = resize_frame(frame, MAX_FRAME_WIDTH, MAX_FRAME_HEIGHT)
        
        # Run YOLO detection
        results = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
        
        # Extract detections
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                
                # Filter by classes of interest
                if cls_id in CLASSES_OF_INTEREST:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = float(box.conf[0])
                    class_name = CLASSES_OF_INTEREST[cls_id]
                    
                    detection = {
                        'bbox': [x1, y1, x2, y2],
                        'class': class_name,
                        'confidence': confidence
                    }
                    detections.append(detection)
                    
                    # Draw on frame
                    color = (0, 255, 0) if class_name == "person" else (255, 0, 0)
                    frame = draw_bbox(frame, [x1, y1, x2, y2], class_name, confidence, color)
        
        # Update tracker
        tracked_objects = {}
        if self.tracker and detections:
            tracked_objects = self.tracker.update(detections)
            
            # Draw tracking IDs
            for obj_id, obj_info in tracked_objects.items():
                x1, y1, x2, y2 = obj_info['bbox']
                cv2.putText(
                    frame, f"ID: {obj_id}", (x1, y1 - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2
                )
        
        # Detect events
        events = []
        if tracked_objects:
            events = self.event_detector.detect_all_events(
                self.tracker, tracked_objects, frame.shape[:2]
            )
        
        # Apply face blur for privacy
        if self.face_blurrer:
            frame = self.face_blurrer.blur_faces(frame)
        
        # Draw restricted zones
        for zone in RESTRICTED_ZONES:
            frame = draw_polygon(frame, zone, (0, 0, 255), 2)
        
        # Add stats overlay
        processing_time = time.time() - start_time
        self.stats['processing_time'] = processing_time
        self.stats['fps'] = 1.0 / processing_time if processing_time > 0 else 0
        
        cv2.putText(
            frame, f"FPS: {self.stats['fps']:.1f} | Objects: {len(tracked_objects)} | Events: {len(events)}",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )
        
        return frame, detections, events
    
    def start(self):
        """Start processing video in a separate thread"""
        if self.is_running:
            print("Processor already running")
            return
        
        # Load model if not loaded
        if self.model is None:
            self.load_model()
        
        # Connect to source
        if not self.connect():
            print("Failed to connect to video source")
            return
        
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        print("Video processing started")
    
    def _processing_loop(self):
        """Main processing loop"""
        consecutive_failures = 0
        max_failures = 10 if self.source_type == "rtsp" else 3
        
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    consecutive_failures += 1
                    print(f"Failed to read frame ({consecutive_failures}/{max_failures})")
                    
                    if consecutive_failures >= max_failures:
                        if self.source_type == "rtsp":
                            # Try to reconnect for RTSP
                            print(f"Attempting to reconnect in {RTSP_RECONNECT_DELAY}s...")
                            time.sleep(RTSP_RECONNECT_DELAY)
                            self.disconnect()
                            if not self.connect():
                                print("Reconnection failed")
                                break
                            consecutive_failures = 0
                        else:
                            # End of file for recorded video
                            print("End of video file")
                            break
                    continue
                
                consecutive_failures = 0
                self.stats['total_frames'] += 1
                self.frame_count += 1
                
                # Skip frames if configured
                if FRAME_SKIP > 0 and self.frame_count % (FRAME_SKIP + 1) != 0:
                    continue
                
                # Process frame
                processed_frame, detections, events = self.process_frame(frame)
                
                self.stats['processed_frames'] += 1
                self.stats['detections'] += len(detections)
                self.stats['events'] += len(events)
                
                # Update current frame
                with self.frame_lock:
                    self.current_frame = processed_frame.copy()
                
                # Trigger callbacks
                if events and self.on_event_callback:
                    for event in events:
                        self.on_event_callback(event)
                
                if self.on_frame_callback:
                    self.on_frame_callback(processed_frame, detections, events)
                
            except Exception as e:
                print(f"Error in processing loop: {e}")
                consecutive_failures += 1
                time.sleep(0.1)
        
        self.is_running = False
        self.disconnect()
        print("Video processing stopped")
    
    def stop(self):
        """Stop processing"""
        print("Stopping video processor...")
        self.is_running = False
        
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join(timeout=5)
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the current processed frame
        
        Returns:
            Current frame or None
        """
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def get_stats(self) -> Dict:
        """
        Get processing statistics
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()