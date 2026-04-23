import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FaceEnhancer:
    """
    Enhances blurred or low-res faces by overlapping multiple 
    historical frames of the same person and applying sharpening.
    """
    def __init__(self, history_size=15):
        self.history_size = history_size
        self.person_history = {}
        self.target_size = (150, 150) # Standardize size for overlapping

    def enhance(self, person_id, crop: np.ndarray) -> np.ndarray:
        if crop is None or crop.size == 0:
            return crop
            
        # Resize to common dimensions so matrices can be overlapped
        resized = cv2.resize(crop, self.target_size)
        
        if person_id not in self.person_history:
            self.person_history[person_id] = []
            
        # Append to history
        self.person_history[person_id].append(resized)
        
        # Keep only the most recent N frames
        if len(self.person_history[person_id]) > self.history_size:
            self.person_history[person_id].pop(0)
            
        # Overlap (average) the frames to cancel out noise and temporal blur
        float_images = [img.astype(np.float32) for img in self.person_history[person_id]]
        avg_image = np.mean(float_images, axis=0).astype(np.uint8)
        
        # Apply a sharpening filter to make it crisp
        sharpen_kernel = np.array([
            [-1, -1, -1], 
            [-1,  9, -1], 
            [-1, -1, -1]
        ])
        sharp_image = cv2.filter2D(avg_image, -1, sharpen_kernel)
        
        return sharp_image

    def reset_person(self, person_id):
        if person_id in self.person_history:
            del self.person_history[person_id]