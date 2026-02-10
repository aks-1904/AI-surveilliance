"""
Test Suite for AI Video Processing Service
Run this to test all components
"""

import sys
import time
from pathlib import Path

def test_imports():
    """Test all required imports"""
    print("\n" + "="*60)
    print("TEST 1: Checking Python packages...")
    print("="*60)
    
    packages = {
        'cv2': 'opencv-python',
        'flask': 'flask',
        'ultralytics': 'ultralytics',
        'numpy': 'numpy',
        'requests': 'requests'
    }
    
    failed = []
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            failed.append(package)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All packages installed")
    return True


def test_modules():
    """Test custom modules"""
    print("\n" + "="*60)
    print("TEST 2: Checking custom modules...")
    print("="*60)
    
    modules = [
        'config',
        'utils',
        'tracker',
        'event_detector',
        'privacy',
        'video_processor'
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}.py")
        except Exception as e:
            print(f"❌ {module}.py - {str(e)[:50]}")
            failed.append(module)
    
    if failed:
        print(f"\n❌ Failed modules: {', '.join(failed)}")
        return False
    
    print("\n✅ All modules loaded successfully")
    return True


def test_config():
    """Test configuration"""
    print("\n" + "="*60)
    print("TEST 3: Checking configuration...")
    print("="*60)
    
    try:
        import config
        
        print(f"✅ YOLO Model: {config.YOLO_MODEL}")
        print(f"✅ Confidence: {config.CONFIDENCE_THRESHOLD}")
        print(f"✅ Backend URL: {config.BACKEND_URL}")
        print(f"✅ Face Blur: {config.ENABLE_FACE_BLUR}")
        print(f"✅ Tracking: {config.ENABLE_TRACKING}")
        
        # Check directories
        if config.UPLOAD_DIR.exists():
            print(f"✅ Upload dir: {config.UPLOAD_DIR}")
        else:
            print(f"⚠️  Upload dir missing: {config.UPLOAD_DIR}")
        
        if config.OUTPUT_DIR.exists():
            print(f"✅ Output dir: {config.OUTPUT_DIR}")
        else:
            print(f"⚠️  Output dir missing: {config.OUTPUT_DIR}")
        
        print("\n✅ Configuration OK")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        return False


def test_yolo_model():
    """Test YOLO model loading"""
    print("\n" + "="*60)
    print("TEST 4: Testing YOLO model...")
    print("="*60)
    
    try:
        from ultralytics import YOLO
        import config
        
        print(f"Loading model: {config.YOLO_MODEL}")
        model = YOLO(config.YOLO_MODEL)
        print(f"✅ Model loaded: {model.model_name}")
        
        # Test prediction on dummy image
        import numpy as np
        dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
        
        print("Running test prediction...")
        results = model(dummy_image, verbose=False)
        print(f"✅ Prediction successful")
        
        return True
        
    except Exception as e:
        print(f"\n❌ YOLO model error: {e}")
        print("The model will download on first use")
        return False


def test_tracker():
    """Test object tracker"""
    print("\n" + "="*60)
    print("TEST 5: Testing object tracker...")
    print("="*60)
    
    try:
        from support.tracker import ObjectTracker
        
        tracker = ObjectTracker()
        print("✅ Tracker initialized")
        
        # Test with dummy detection
        detections = [
            {'bbox': [100, 100, 200, 200], 'class': 'person', 'confidence': 0.9}
        ]
        
        tracked = tracker.update(detections)
        print(f"✅ Tracking working - {len(tracked)} objects tracked")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Tracker error: {e}")
        return False


def test_event_detector():
    """Test event detector"""
    print("\n" + "="*60)
    print("TEST 6: Testing event detector...")
    print("="*60)
    
    try:
        from support.event_detector import EventDetector
        from support.tracker import ObjectTracker
        
        detector = EventDetector()
        tracker = ObjectTracker()
        
        print("✅ Event detector initialized")
        
        # Test with dummy tracked objects
        tracked_objects = {
            0: {
                'bbox': [100, 100, 200, 200],
                'center': (150, 150),
                'class': 'person',
                'first_seen': time.time(),
                'last_seen': time.time()
            }
        }
        
        events = detector.detect_all_events(tracker, tracked_objects, (720, 1280))
        print(f"✅ Event detection working - {len(events)} events detected")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Event detector error: {e}")
        return False


def test_privacy():
    """Test privacy module"""
    print("\n" + "="*60)
    print("TEST 7: Testing privacy module...")
    print("="*60)
    
    try:
        from support.privacy import FaceBlurrer
        import numpy as np
        
        blurrer = FaceBlurrer()
        print("✅ Face blurrer initialized")
        
        # Test with dummy image
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        blurred = blurrer.blur_faces(dummy_image)
        print(f"✅ Face blurring working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Privacy module error: {e}")
        return False


def test_video_processor():
    """Test video processor initialization"""
    print("\n" + "="*60)
    print("TEST 8: Testing video processor...")
    print("="*60)
    
    try:
        from main.video_processor import VideoProcessor
        
        # Test with dummy source (won't connect, but will initialize)
        processor = VideoProcessor("test.mp4", "file")
        print("✅ Video processor initialized")
        
        print(f"   Source: {processor.source}")
        print(f"   Type: {processor.source_type}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Video processor error: {e}")
        return False


def test_flask_app():
    """Test Flask app initialization"""
    print("\n" + "="*60)
    print("TEST 9: Testing Flask app...")
    print("="*60)
    
    try:
        from app import app
        
        print("✅ Flask app initialized")
        
        # Test client
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"⚠️  Health endpoint returned {response.status_code}")
            
            response = client.get('/config')
            if response.status_code == 200:
                print("✅ Config endpoint working")
            else:
                print(f"⚠️  Config endpoint returned {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Flask app error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI VIDEO PROCESSING SERVICE - TEST SUITE")
    print("="*60)
    
    tests = [
        ("Package Dependencies", test_imports),
        ("Custom Modules", test_modules),
        ("Configuration", test_config),
        ("YOLO Model", test_yolo_model),
        ("Object Tracker", test_tracker),
        ("Event Detector", test_event_detector),
        ("Privacy Module", test_privacy),
        ("Video Processor", test_video_processor),
        ("Flask App", test_flask_app),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print("\nYou're ready to run:")
        print("  python app.py")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Please fix the issues above before running the service")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())