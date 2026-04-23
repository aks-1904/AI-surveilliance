import cv2
import os
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict

# Assuming your classes are in these paths
from analysis.loitering_detector import LoiteringDetector
from analysis.object_detector import UnattendedObjectDetector
from detection.person_detector import PersonDetector
from risk.risk_engine import RiskEngine

class JudgeShowcase:
    def __init__(self, config):
        self.config = config
        self.person_detector = PersonDetector(config)
        self.loitering_detector = LoiteringDetector(config)
        self.object_detector = UnattendedObjectDetector(config)
        self.risk_engine = RiskEngine(config)

    def draw_styled_text(self, img, text, pos, color, scale=0.5, thickness=2):
        """Draws text with a filled background rectangle for maximum readability."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        # Get the width and height of the text box
        (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
        x, y = pos
        
        # Draw the background rectangle (slightly larger than the text)
        cv2.rectangle(img, (x, y - text_h - 10), (x + text_w, y + baseline), color, -1)
        
        # Draw the white text on top of the colored background
        cv2.putText(img, text, (x, y - 5), font, scale, (255, 255, 255), thickness)

    def analyze_behavior_video(self, video_path: str):
        """Processes video for loitering and unattended objects."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = 0
        all_events = []
        
        print(f"--- Analyzing Video: {os.path.basename(video_path)} ---")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            # Synthetic timestamp for the report
            timestamp = datetime.now() + timedelta(seconds=frame_count/fps)
            
            # 1. Detect Persons
            persons = self.person_detector.detect(frame)
            
            # 2. Check Loitering (Masked loitering has a 15s threshold)
            loiter_events = self.loitering_detector.detect(persons, timestamp)
            
            # 3. Check Unattended Objects
            object_events = self.object_detector.detect(frame, persons, timestamp)
            
            all_events.extend(loiter_events + object_events)
            frame_count += 1
            
        cap.release()
        self._generate_video_report(all_events)

    def analyze_identity_image(self, image_path: str):
        """Processes a single image for Mask Detection and Whitelist status."""
        frame = cv2.imread(image_path)
        if frame is None: 
            print(f"Error: Could not read image at {image_path}")
            return

        print(f"--- Analyzing Image: {os.path.basename(image_path)} ---")
        
        # Runs YOLOv8 and face_recognition
        persons = self.person_detector.detect(frame)
        
        for p in persons:
            x1, y1, x2, y2 = p['bbox']
            # Determine status colors based on detector output
            is_white = p.get('is_whitelisted', False)
            is_masked = p.get('is_masked', False)
            
            # Color coding: Green for whitelisted, Red for suspicious/unknown
            status_color = (0, 255, 0) if is_white else (0, 0, 255)
            
            # Draw the bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), status_color, 2)
            
            # Construct and draw the high-visibility label
            label = f"ID:{p['id']} | Mask:{is_masked} | Whitelist:{is_white}"
            self.draw_styled_text(frame, label, (x1, y1), status_color)

        output_path = f"showcase_result_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, frame)
        print(f"Identity report image saved as: {output_path}")

    def _generate_video_report(self, events: List[Dict]):
        """Generates a text-based summary for the judges."""
        with open("judge_behavior_report.txt", "w") as f:
            f.write("AI SURVEILLANCE JUDGE'S REPORT\n")
            f.write("="*30 + "\n")
            for ev in events:
                f.write(f"[{ev['timestamp']}] TYPE: {ev['type']}\n")
                f.write(f"DETAILS: {ev['details']['message']}\n")
                f.write("-" * 20 + "\n")
        print("Behavior report generated: judge_behavior_report.txt")

# Configuration Mockup
class Config:
    YOLO_MODEL = 'yolov8n.pt'
    CONFIDENCE_THRESHOLD = 0.5
    LOITERING_THRESHOLD_SECONDS = 30
    LOITERING_DISTANCE_THRESHOLD = 50
    UNATTENDED_THRESHOLD_SECONDS = 60
    OBJECT_PERSON_DISTANCE_THRESHOLD = 100
    RISK_SCORES = {'LOITERING': 5, 'UNATTENDED_OBJECT': 10, 'RESTRICTED_ENTRY': 15}
    RISK_LEVEL_LOW = 10
    RISK_LEVEL_MEDIUM = 20
    WHITELIST_DIR = 'whitelist_images/'
    YOLO_MASK_DETECTOR_MODEL = 'mask_detector.pt'

if __name__ == "__main__":
    showcase = JudgeShowcase(Config())
    showcase.analyze_behavior_video("29a2b450-80c5-4e99-ab68-f08e37ca5905_vtc.mp4")
    # showcase.analyze_identity_image("Akshay.jpg")