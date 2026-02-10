#!/usr/bin/env python3
"""
Setup Validation Script
Checks if everything is properly installed and configured
"""

import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print("✅ Python version OK")
    return True

def check_pip():
    """Check if pip is available"""
    print_header("Checking pip")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        print(result.stdout.strip())
        print("✅ pip is available")
        return True
    except Exception as e:
        print(f"❌ pip not found: {e}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required = {
        'cv2': 'opencv-python',
        'flask': 'flask',
        'flask_cors': 'flask-cors',
        'numpy': 'numpy',
        'requests': 'requests',
        'ultralytics': 'ultralytics'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    print("\n✅ All dependencies installed")
    return True

def check_project_structure():
    """Check if all required files exist"""
    print_header("Checking Project Structure")
    
    required_files = [
        'core/config.py',
        'support/utils.py',
        'support/tracker.py',
        'support/event_detector.py',
        'support/privacy.py',
        'core/video_processor.py',
        'app.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing = []
    for filename in required_files:
        filepath = Path(filename)
        if filepath.exists():
            print(f"✅ {filename}")
        else:
            print(f"❌ {filename} - MISSING")
            missing.append(filename)
    
    if missing:
        print(f"\n⚠️  Missing files: {', '.join(missing)}")
        return False
    
    print("\n✅ All required files present")
    return True

def check_directories():
    """Check if required directories exist"""
    print_header("Checking Directories")
    
    required_dirs = ['uploads', 'outputs']
    
    for dirname in required_dirs:
        dirpath = Path(dirname)
        if dirpath.exists() and dirpath.is_dir():
            print(f"✅ {dirname}/")
        else:
            print(f"⚠️  {dirname}/ - Creating...")
            dirpath.mkdir(exist_ok=True)
            print(f"✅ {dirname}/ created")
    
    print("\n✅ All directories ready")
    return True

def check_opencv():
    """Check OpenCV installation"""
    print_header("Checking OpenCV")
    try:
        import cv2
        print(f"OpenCV version: {cv2.__version__}")
        
        # Check if Haar Cascade is available
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if Path(cascade_path).exists():
            print("✅ Haar Cascade for face detection available")
        else:
            print("⚠️  Haar Cascade not found, face detection may not work")
        
        print("✅ OpenCV OK")
        return True
    except ImportError:
        print("❌ OpenCV not installed")
        return False

def check_yolo_model():
    """Check if YOLO model can be loaded"""
    print_header("Checking YOLO Model")
    try:
        from ultralytics import YOLO
        import main.config as config
        
        model_path = Path(config.YOLO_MODEL)
        if model_path.exists():
            print(f"✅ Model file exists: {config.YOLO_MODEL}")
        else:
            print(f"⚠️  Model file not found: {config.YOLO_MODEL}")
            print("   It will be downloaded automatically on first run")
        
        print("✅ YOLO can be imported")
        return True
    except ImportError:
        print("❌ ultralytics package not installed")
        print("Install with: pip install ultralytics")
        return False
    except Exception as e:
        print(f"⚠️  Issue checking YOLO: {e}")
        return True  # Don't fail, model downloads on first use

def check_flask():
    """Check Flask installation"""
    print_header("Checking Flask")
    try:
        from flask import Flask
        from flask_cors import CORS
        
        app = Flask(__name__)
        CORS(app)
        
        print("✅ Flask and CORS working")
        return True
    except ImportError as e:
        print(f"❌ Flask setup issue: {e}")
        return False

def provide_next_steps(all_passed):
    """Provide next steps based on validation results"""
    print_header("Summary")
    
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("\nYou're ready to go! Next steps:")
        print("\n1. Configure your settings:")
        print("   nano config.py")
        print("\n2. Test with a video file:")
        print("   python example_file_processing.py")
        print("\n3. Or start the API server:")
        print("   python app.py")
        print("\n4. Then open in browser:")
        print("   http://localhost:8000/video")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("\nPlease fix the issues above, then run this script again:")
        print("   python setup_validation.py")

def main():
    """Run all checks"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║        AI SURVEILLANCE CO-PILOT - SETUP VALIDATION        ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    checks = [
        ("Python Version", check_python_version),
        ("pip", check_pip),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Directories", check_directories),
        ("OpenCV", check_opencv),
        ("YOLO", check_yolo_model),
        ("Flask", check_flask)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Check failed with error: {e}")
            results.append((name, False))
    
    all_passed = all(result for _, result in results)
    
    provide_next_steps(all_passed)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())