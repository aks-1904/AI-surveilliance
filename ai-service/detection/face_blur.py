"""
Face Blur for Privacy Protection
Automatically blurs faces in video frames to protect privacy
"""

import cv2
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)


class FaceBlurrer:
    """Blurs faces in video frames for privacy protection"""
    
    def __init__(self, config):
        self.config = config
        self.blur_kernel_size = config.BLUR_KERNEL_SIZE
        self.method = config.FACE_DETECTION_METHOD
        
        # Load Haar Cascade for face detection
        if self.method == 'haar':
            cascade_path = config.HAAR_CASCADE_PATH
            
            # If custom path doesn't exist, use OpenCV default
            if not os.path.exists(cascade_path):
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                logger.error("Failed to load Haar Cascade")
                raise ValueError("Failed to load face detection model")
            
            logger.info("Haar Cascade face detector loaded")
        
        else:
            raise ValueError(f"Unsupported face detection method: {self.method}")
    
    def blur_faces(self, frame: np.ndarray) -> np.ndarray:
        """
        Blur all detected faces in the frame
        
        Args:
            frame: Input video frame
        
        Returns:
            Frame with blurred faces
        """
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Blur each detected face
            for (x, y, w, h) in faces:
                # Extract face region
                face_region = frame[y:y+h, x:x+w]
                
                # Apply Gaussian blur
                blurred_face = cv2.GaussianBlur(
                    face_region,
                    (self.blur_kernel_size, self.blur_kernel_size),
                    0
                )
                
                # Replace face region with blurred version
                frame[y:y+h, x:x+w] = blurred_face
            
            return frame
            
        except Exception as e:
            logger.error(f"Error blurring faces: {str(e)}")
            return frame
    
    def detect_faces_count(self, frame: np.ndarray) -> int:
        """
        Count number of faces in frame
        
        Args:
            frame: Input video frame
        
        Returns:
            Number of faces detected
        """
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            return len(faces)
        except:
            return 0