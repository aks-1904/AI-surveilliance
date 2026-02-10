"""
Privacy Module - Face detection and blurring
"""

import cv2
import numpy as np
from typing import List
from utils import blur_region


class FaceBlurrer:
    """
    Detects and blurs faces for privacy protection
    Uses Haar Cascade for speed (can be replaced with DNN for accuracy)
    """
    
    def __init__(self):
        """Initialize face detector"""
        # Load Haar Cascade classifier
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        if self.face_cascade.empty():
            print("Warning: Could not load face cascade classifier")
    
    def detect_faces(self, frame: np.ndarray) -> List[List[int]]:
        """
        Detect faces in frame
        
        Args:
            frame: Input frame
        
        Returns:
            List of face bounding boxes [x, y, w, h]
        """
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return faces.tolist() if len(faces) > 0 else []
    
    def blur_faces(self, frame: np.ndarray) -> np.ndarray:
        """
        Detect and blur all faces in frame
        
        Args:
            frame: Input frame
        
        Returns:
            Frame with blurred faces
        """
        faces = self.detect_faces(frame)
        
        for (x, y, w, h) in faces:
            # Convert [x, y, w, h] to [x1, y1, x2, y2]
            bbox = [x, y, x + w, y + h]
            frame = blur_region(frame, bbox)
        
        return frame