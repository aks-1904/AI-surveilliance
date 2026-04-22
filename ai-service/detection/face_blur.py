import cv2
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)


class FaceBlurrer:
    """
    Blurs faces in video frames for privacy protection
    """

    def __init__(self, config):
        self.config = config

        # Default fallback
        self.blur_kernel_size = getattr(config, "BLUR_KERNEL_SIZE", 21)
        self.method = getattr(config, "FACE_DETECTION_METHOD", "haar")

        if self.method != "haar":
            raise ValueError("Only haar supported right now")

        cascade_path = getattr(config, "HAAR_CASCADE_PATH", "")

        if not cascade_path or not os.path.exists(cascade_path):
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            raise RuntimeError("Failed to load Haar cascade")

        logger.info("Face blurrer initialized")

    def _safe_kernel(self, w, h):
        """
        Dynamically compute safe kernel per face
        """

        k = int(self.blur_kernel_size)

        # must be odd
        if k % 2 == 0:
            k += 1

        # must fit ROI
        k = min(k, w - 1, h - 1)

        # must still be odd
        if k % 2 == 0:
            k -= 1

        # absolute minimum
        if k < 3:
            k = 3

        return k

    def blur_faces(self, frame: np.ndarray) -> np.ndarray:
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
            )

            for (x, y, w, h) in faces:
                face = frame[y:y + h, x:x + w]

                if face.size == 0:
                    continue

                fh, fw = face.shape[:2]

                k = self._safe_kernel(fw, fh)

                blurred = cv2.GaussianBlur(face, (k, k), 0)

                frame[y:y + h, x:x + w] = blurred

            return frame

        except Exception as e:
            logger.exception("Face blur failed")
            return frame

    def detect_faces_count(self, frame: np.ndarray) -> int:
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
            return len(faces)
        except Exception:
            return 0
