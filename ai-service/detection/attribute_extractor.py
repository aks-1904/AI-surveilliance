import cv2
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)


class AttributeExtractor:
    """Extracts real soft biometrics (clothing colors, body type) using OpenCV."""

    def __init__(self, config):
        self.config = config

        # Load OpenCV's built-in lightweight Haar cascade for glasses/eyes detection
        # This requires the haarcascade_eye_tree_eyeglasses.xml file.
        # OpenCV usually comes with it, or you can download it from the OpenCV GitHub.
        cascade_path = cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml'
        if os.path.exists(cascade_path):
            self.glasses_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            self.glasses_cascade = None
            logger.warning("Glasses Haar cascade not found. Glasses detection disabled.")

        # Standard RGB Color Palette for matching
        self.COLORS = {
            "Black": (0, 0, 0),
            "White": (255, 255, 255),
            "Gray": (128, 128, 128),
            "Red": (255, 0, 0),
            "Dark Red": (139, 0, 0),
            "Green": (0, 255, 0),
            "Dark Green": (0, 100, 0),
            "Blue": (0, 0, 255),
            "Dark Blue": (0, 0, 139),
            "Yellow": (255, 255, 0),
            "Cyan": (0, 255, 255),
            "Magenta": (255, 0, 255),
            "Orange": (255, 165, 0),
            "Brown": (139, 69, 19),
            "Pink": (255, 192, 203)
        }

    def extract_features(self, person_crop, bbox) -> dict:
        """
        Analyzes the crop and returns actual extracted attributes.
        """
        if person_crop is None or person_crop.size == 0:
            return {}

        height, width = person_crop.shape[:2]

        # 1. Calculate Body Type based on Bounding Box Aspect Ratio
        x1, y1, x2, y2 = bbox
        bbox_width = x2 - x1
        bbox_height = y2 - y1
        aspect_ratio = bbox_width / float(bbox_height) if bbox_height > 0 else 0

        if aspect_ratio < 0.35:
            body_type = "Slim"
        elif aspect_ratio > 0.55:
            body_type = "Broad"
        else:
            body_type = "Average"

        # 2. Extract Clothing Colors
        # Upper torso (roughly 15% to 50% from the top)
        upper_torso = person_crop[int(height * 0.15):int(height * 0.50), :]
        upper_color = self._get_dominant_color_name(upper_torso)

        # Lower body (roughly 50% to 90% from the top)
        lower_body = person_crop[int(height * 0.50):int(height * 0.90), :]
        lower_color = self._get_dominant_color_name(lower_body)

        # 3. Detect Glasses (Check the top 30% of the crop for a face/eyes)
        wearing_glasses = False
        if self.glasses_cascade is not None:
            head_crop = person_crop[0:int(height * 0.30), :]
            if head_crop.size > 0:
                gray_head = cv2.cvtColor(head_crop, cv2.COLOR_BGR2GRAY)
                # Detect eyes/glasses
                eyes = self.glasses_cascade.detectMultiScale(gray_head, scaleFactor=1.1, minNeighbors=3)
                if len(eyes) > 0:
                    wearing_glasses = True

        return {
            "upper_clothing_color": upper_color,
            "lower_clothing_color": lower_color,
            "wearing_glasses": wearing_glasses,
            "body_type": body_type
        }

    def _get_dominant_color_name(self, image_crop) -> str:
        """Uses K-Means clustering to find the dominant color in an image region."""
        if image_crop.size == 0:
            return "Unknown"

        # Convert image to RGB (OpenCV uses BGR by default)
        image_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)

        # Reshape the image to be a list of pixels
        pixels = image_rgb.reshape((-1, 3))

        # Convert to float32 for K-Means
        pixels = np.float32(pixels)

        # Define criteria, number of clusters(K) and apply kmeans()
        # We use K=2 to separate the clothing color from the background color
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = 2
        _, labels, centers = cv2.kmeans(pixels, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # Convert back to 8 bit values
        centers = np.uint8(centers)

        # Find the most frequent cluster (ignoring the exact center point which might be background)
        # To do this robustly, we count the labels
        counts = np.bincount(labels.flatten())
        dominant_center = centers[np.argmax(counts)]

        return self._closest_color_name(dominant_center)

    def _closest_color_name(self, rgb_tuple) -> str:
        """Finds the closest human-readable color name using Euclidean distance."""
        min_distance = float('inf')
        closest_name = "Unknown"

        r, g, b = rgb_tuple

        for name, (cr, cg, cb) in self.COLORS.items():
            # Calculate Euclidean distance between the detected color and our palette
            distance = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_name = name

        return closest_name