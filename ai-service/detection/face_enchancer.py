import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FaceEnhancer:
    """
    Enhances blurred or low-res faces using Lanczos Upscaling, 
    Bilateral Filtering, CLAHE, and Multi-stage Sharpening Kernels.
    """
    def __init__(self):
        pass

    def enhance(self, person_id, crop: np.ndarray) -> np.ndarray:
        if crop is None or crop.size == 0:
            return crop
            
        # 1. High-Quality Upscaling (Lanczos4 is sharper and more precise than Bicubic)
        height, width = crop.shape[:2]
        scaled = cv2.resize(crop, (width * 2, height * 2), interpolation=cv2.INTER_LANCZOS4)

        # 2. Noise Reduction (Bilateral filtering smooths skin but preserves hard edges)
        # If we don't do this, the sharpening steps will just amplify ugly pixel noise.
        smoothed = cv2.bilateralFilter(scaled, d=9, sigmaColor=75, sigmaSpace=75)

        # 3. Enhance Contrast and Lighting (CLAHE)
        lab = cv2.cvtColor(smoothed, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)) # Slightly lowered clipLimit to prevent blowout
        cl = clahe.apply(l)

        limg = cv2.merge((cl, a, b))
        enhanced_contrast = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # 4. "Overlapping" / High-Pass Sharpening (Your suggestion)
        # We blur a copy, subtract it to find the edges, and overlap those edges back.
        gaussian = cv2.GaussianBlur(enhanced_contrast, (0, 0), 2.0)
        
        # 1.5 weight to original, -0.5 weight to blurred to extract and boost edges
        sharp_image = cv2.addWeighted(enhanced_contrast, 1.5, gaussian, -0.5, 0)
        
        # 5. Final Micro-Contrast Edge Kernel
        # This is a classic overlapping kernel that forces individual pixels to stand out
        # against their neighbors, eliminating the "soft" look of a blur.
        kernel = np.array([[ 0, -1,  0],
                           [-1,  5, -1],
                           [ 0, -1,  0]])
        final_crisp = cv2.filter2D(sharp_image, -1, kernel)

        return final_crisp

    def reset_person(self, person_id):
        pass