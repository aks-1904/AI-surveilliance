import cv2
import os
from datetime import datetime, timedelta
from typing import List, Dict

# Import all detection and analysis modules
from analysis.loitering_detector import LoiteringDetector
from analysis.object_detector import UnattendedObjectDetector
from detection.person_detector import PersonDetector
from detection.weapon_detector import WeaponDetector
from detection.face_enchancer import FaceEnhancer
from risk.risk_engine import RiskEngine

class JudgeShowcase:
    def __init__(self, config):
        self.config = config
        
        # Initialize all modules
        self.person_detector = PersonDetector(config)
        self.loitering_detector = LoiteringDetector(config)
        self.object_detector = UnattendedObjectDetector(config)
        self.weapon_detector = WeaponDetector(config)
        self.face_enchancer = FaceEnhancer()
        self.risk_engine = RiskEngine(config)

    def draw_styled_text(self, img, text, pos, color, scale=0.5, thickness=2):
        """Draws text with a filled background rectangle for maximum readability."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
        x, y = pos
        
        # Keep text within frame bounds
        y = max(y, text_h + 10)
        
        cv2.rectangle(img, (x, y - text_h - 10), (x + text_w, y + baseline), color, -1)
        cv2.putText(img, text, (x, y - 5), font, scale, (255, 255, 255), thickness)

    # ==========================================
    # FEATURE 1: FACE ENHANCEMENT (PHOTOS)
    # ==========================================
    def test_face_enhancement(self, image_path: str):
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Error: Could not read image at {image_path}")
            return
            
        print(f"--- Testing Face Enhancement: {os.path.basename(image_path)} ---")

        frame = cv2.resize(frame, (frame.shape[1] * 2, frame.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
        
        # 1. Detect persons to find the face bounding boxes
        persons = self.person_detector.detect(frame)
        
        crop_idx = 0
        
        for p in persons:
            x1, y1, x2, y2 = p['bbox']
            
            # Ensure coordinates are within image bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
            
            # Crop the blurry face
            crop = frame[y1:y2, x1:x2]
            
            if crop.size > 0:
                # 2. Call FaceEnhancer class
                enhanced_crop = self.face_enchancer.enhance(p['id'], crop)
                
                # 3. Save the 2x upscaled high-resolution isolated crop
                crop_path = f"showcase_highres_face_{crop_idx}_{os.path.basename(image_path)}"
                cv2.imwrite(crop_path, enhanced_crop)
                print(f"Saved 2x High-Res isolated face to: {crop_path}")
                crop_idx += 1
                
                # 4. Resize back to the original box dimensions to paste back into the main frame
                enhanced_resized = cv2.resize(enhanced_crop, (x2 - x1, y2 - y1))
                frame[y1:y2, x1:x2] = enhanced_resized
                
                # Draw a Cyan box to indicate the face was enhanced
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2) 
                self.draw_styled_text(frame, "ENHANCED", (x1, y1), (255, 255, 0))

        output_path = f"showcase_enhanced_full_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, frame)
        print(f"Full enhanced image saved as: {output_path}\n")

    # ==========================================
    # FEATURE 2: WEAPON DETECTION (PHOTOS)
    # ==========================================
    def test_weapon_detection(self, image_path: str):
        frame = cv2.imread(image_path)
        if frame is None: return
        
        print(f"--- Testing Weapon Detection: {os.path.basename(image_path)} ---")
        timestamp = datetime.now()
        events = self.weapon_detector.detect(frame, timestamp)
        
        for ev in events:
            if ev['type'] == 'WEAPON_DETECTED':
                x1, y1, x2, y2 = ev['details']['bbox']
                weapon = ev['details']['weapon_type']
                conf = ev['details']['confidence']
                
                # Draw red bounding box for weapons
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                label = f"THREAT: {weapon} ({conf:.2f})"
                self.draw_styled_text(frame, label, (x1, y1), (0, 0, 255))
        
        output_path = f"showcase_weapon_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, frame)
        print(f"Weapon detection image saved as: {output_path}\n")

    # ==========================================
    # FEATURE 3: MASK DETECTION (PHOTOS)
    # ==========================================
    def test_mask_detection(self, image_path: str):
        frame = cv2.imread(image_path)
        if frame is None: return
        
        print(f"--- Testing Mask Detection: {os.path.basename(image_path)} ---")
        persons = self.person_detector.detect(frame)
        
        for p in persons:
            x1, y1, x2, y2 = p['bbox']
            is_masked = p.get('is_masked', False)
            
            color = (0, 255, 0) if is_masked else (0, 0, 255)
            text = "Mask: YES" if is_masked else "Mask: NO"
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            self.draw_styled_text(frame, text, (x1, y1), color)
            
        output_path = f"showcase_mask_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, frame)
        print(f"Mask detection image saved as: {output_path}\n")

    # ==========================================
    # FEATURE 4: WHITELIST DETECTION (PHOTOS)
    # ==========================================
    def test_whitelist(self, image_path: str):
        frame = cv2.imread(image_path)
        if frame is None: return
        
        print(f"--- Testing Whitelist: {os.path.basename(image_path)} ---")
        persons = self.person_detector.detect(frame)
        
        for p in persons:
            x1, y1, x2, y2 = p['bbox']
            is_white = p.get('is_whitelisted', False)
            
            color = (0, 255, 0) if is_white else (0, 165, 255) # Green for known, Orange for unknown
            text = "Whitelisted: YES" if is_white else "Unknown Person"
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            self.draw_styled_text(frame, text, (x1, y1), color)
            
        output_path = f"showcase_whitelist_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, frame)
        print(f"Whitelist detection image saved as: {output_path}\n")

    # ==========================================
    # FEATURE 5: LOITERING & UNATTENDED (VIDEO)
    # ==========================================
    def test_behavior_video(self, video_path: str):
        """Processes video specifically for time-based events like loitering and unattended objects."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = 0
        all_events = []
        
        print(f"--- Testing Behavior Tracking Video: {os.path.basename(video_path)} ---")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            timestamp = datetime.now() + timedelta(seconds=frame_count/fps)
            persons = self.person_detector.detect(frame)
            
            loiter_events = self.loitering_detector.detect(persons, timestamp)
            object_events = self.object_detector.detect(frame, persons, timestamp)
            
            all_events.extend(loiter_events + object_events)
            frame_count += 1
            
        cap.release()
        
        # Generate Text Report
        report_name = f"report_{os.path.basename(video_path)}.txt"
        with open(report_name, "w") as f:
            f.write("AI SURVEILLANCE JUDGE'S REPORT\n")
            f.write("="*30 + "\n")
            if not all_events:
                f.write("No suspicious behavior detected.\n")
            for ev in all_events:
                f.write(f"[{ev['timestamp']}] TYPE: {ev['type']}\n")
                f.write(f"DETAILS: {ev['details']['message']}\n")
                f.write("-" * 20 + "\n")
        print(f"Behavior report generated: {report_name}\n")


# ==========================================
# CONFIGURATION MOCKUP
# ==========================================
class Config:
    # General YOLO
    YOLO_MODEL = 'yolov8n.pt'
    CONFIDENCE_THRESHOLD = 0.5
    
    # Face & Mask
    WHITELIST_DIR = 'whitelist_images/'
    YOLO_MASK_DETECTOR_MODEL = 'mask_detector.pt'
    
    # Face Blur
    BLUR_KERNEL_SIZE = 45 # Increased for heavier blur
    FACE_DETECTION_METHOD = "haar"
    HAAR_CASCADE_PATH = "" 
    
    # Weapons
    WEAPON_CONFIDENCE = 0.50
    WEAPON_COOLDOWN_SECONDS = 10
    
    # Behavior & Tracking
    LOITERING_THRESHOLD_SECONDS = 30
    LOITERING_DISTANCE_THRESHOLD = 50
    UNATTENDED_THRESHOLD_SECONDS = 60
    OBJECT_PERSON_DISTANCE_THRESHOLD = 100
    
    # Risk Engine
    RISK_SCORES = {'LOITERING': 5, 'UNATTENDED_OBJECT': 10, 'RESTRICTED_ENTRY': 15, 'WEAPON_DETECTED': 100}
    RISK_LEVEL_LOW = 10
    RISK_LEVEL_MEDIUM = 20

# ==========================================
# EXECUTION (Uncomment what you want to test)
# ==========================================
if __name__ == "__main__":
    showcase = JudgeShowcase(Config())
    
    # 1. Test Weapons on a Photo
    # showcase.test_weapon_detection("test_image_with_knife.jpg")
    
    # 2. Test Face Blur on a Photo
    showcase.test_face_enhancement("image.avif")
    
    # 3. Test Mask Detection on a Photo
    # showcase.test_mask_detection("test_mask.jpg")
    
    # 4. Test Whitelisting on a Photo
    # showcase.test_whitelist("Akshay.jpg")
    
    # 5. Test Loitering & Unattended Objects on a Video
    # showcase.test_behavior_video("29a2b450-80c5-4e99-ab68-f08e37ca5905_vtc.mp4")