"""
Person Detection using YOLOv8
Detects persons in video frames and tracks them
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging
from typing import List, Dict, Any
import face_recognition
import os

from .face_enchancer import FaceEnhancer

logger = logging.getLogger(__name__)


class PersonDetector:
    """Detects and tracks persons using YOLOv8"""
    
    def __init__(self, config):
        self.config = config
        self.confidence_threshold = config.CONFIDENCE_THRESHOLD
        
        # Load YOLO model
        try:
            self.model = YOLO(config.YOLO_MODEL)
            logger.info(f"YOLO model loaded: {config.YOLO_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {str(e)}")
            raise
        
        # Person class ID in COCO dataset
        self.PERSON_CLASS_ID = 0
        
        # Tracking
        self.next_id = 1
        self.tracked_persons = {}
        self.max_tracking_distance = 100

        # For mask peoples
        try:
            self.mask_model = YOLO(config.YOLO_MASK_DETECTOR_MODEL)
            logger.info(f"YOLO Mask Detector model loaded: ${config.YOLO_MASK_DETECTOR_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load YOLO Mask Detector model: {str(e)}")
            raise

        # To save whitelisted peoples
        self.known_face_encodings = []
        self.known_face_names = []
        self._load_whitelisted_faces()

        # For face enhancing (For blur images)
        self.face_enhancer = FaceEnhancer(history_size=10)

    def _check_if_masked(self, crop: np.ndarray) -> bool:
        if crop.size == 0:
            return False
        
        results = self.mask_model(crop, verbose = False)

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                if class_id == 0 and confidence > 0.5:
                    return True
        
        return False

    def _load_whitelisted_faces(self):
        """Load known faces from a directory (e.g., 'whitelist_images/')"""
        whitelist_dir = getattr(self.config, 'WHITELIST_DIR', 'whitelist_images/')
        if not os.path.exists(whitelist_dir):
            os.makedirs(whitelist_dir)
            logger.warning(f"Created {whitelist_dir}. Please add images of whitelisted people here.")
            return

        for filename in os.listdir(whitelist_dir):
            if filename.endswith((".jpg", ".png", ".jpeg")):
                image_path = os.path.join(whitelist_dir, filename)
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_names.append(os.path.splitext(filename)[0])
        logger.info(f"Loaded {len(self.known_face_names)} whitelisted faces.")
    
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect persons in frame
        
        Args:
            frame: Input video frame
        
        Returns:
            List of detected persons with bounding boxes and IDs
        """
        try:
            # Run YOLO detection
            results = self.model(frame, verbose=False)
            
            detected_persons = []
            current_detections = []
            
            # Process results
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Get class ID
                    class_id = int(box.cls[0])
                    
                    # Only process persons
                    if class_id != self.PERSON_CLASS_ID:
                        continue
                    
                    # Get confidence
                    confidence = float(box.conf[0])
                    
                    if confidence < self.confidence_threshold:
                        continue
                    
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Calculate center point
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    current_detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'center': (center_x, center_y),
                        'confidence': confidence
                    })
            
            # Assign IDs using simple tracking
            detected_persons = self._track_persons(current_detections, frame)
            
            return detected_persons
            
        except Exception as e:
            logger.error(f"Error in person detection: {str(e)}")
            return []
    
    def _track_persons(self, detections: List[Dict], frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Simple tracking algorithm to maintain person IDs across frames
        
        Args:
            detections: Current frame detections
        
        Returns:
            Detections with assigned IDs
        """
        tracked = []
        matched_ids = set()
        
        # Match current detections with tracked persons
        for detection in detections:
            center = detection['center']
            best_match_id = None
            best_distance = float('inf')
            
            # Find closest tracked person
            for person_id, person_data in self.tracked_persons.items():
                if person_id in matched_ids:
                    continue
                
                prev_center = person_data['center']
                distance = np.sqrt(
                    (center[0] - prev_center[0])**2 + 
                    (center[1] - prev_center[1])**2
                )
                
                if distance < best_distance and distance < self.max_tracking_distance:
                    best_distance = distance
                    best_match_id = person_id
            
            # Assign ID
            if best_match_id is not None:
                person_id = best_match_id
                matched_ids.add(person_id)
            else:
                person_id = self.next_id
                self.next_id += 1

            is_whitelisted = False

            # Extract the person's image crop
            x1, y1, x2, y2 = detection['bbox']
            person_crop = frame[y1:y2, x1:x2]

            # Enhancement logic
            if person_crop.size > 0:
                # Enhance the crop using the overlapping algorithm
                enhanced_crop = self.face_enhancer.enhance(person_id, person_crop)
            else:
                enhanced_crop = person_crop

            # Only run face recognition if we have a valid crop and known faces
            if person_crop.size > 0 and self.known_face_encodings:
                # Convert BGR (OpenCV) to RGB (face_recognition)
                rgb_crop = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
                
                # Find faces in this specific person's crop
                face_locations = face_recognition.face_locations(rgb_crop)
                face_encodings = face_recognition.face_encodings(rgb_crop, face_locations)
                
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
                    if True in matches:
                        is_whitelisted = True
                        break # Found a match, stop checking

            is_masked = False
            if person_crop.size > 0:
                is_masked = self._check_if_masked(person_crop)
            
            # Create person object
            person = {
                'id': person_id,
                'bbox': detection['bbox'],
                'center': center,
                'confidence': detection['confidence'],
                'is_whitelisted': is_whitelisted,
                'is_masked': is_masked
            }
            
            tracked.append(person)
            
            # Update tracking
            self.tracked_persons[person_id] = {
                'center': center,
                'last_seen': cv2.getTickCount()
            }
        
        # Remove old tracked persons (not seen for 3 seconds)
        current_time = cv2.getTickCount()
        freq = cv2.getTickFrequency()
        to_remove = []
        
        for person_id, data in self.tracked_persons.items():
            time_diff = (current_time - data['last_seen']) / freq
            if time_diff > 3.0:
                to_remove.append(person_id)
        
        for person_id in to_remove:
            del self.tracked_persons[person_id]
            self.face_enhancer.reset_person(person_id)
        
        return tracked
    
    def reset(self):
        """Reset tracking"""
        self.next_id = 1
        self.tracked_persons = {}