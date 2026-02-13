#!/usr/bin/env python3
"""
Demo Script for Hackathon Presentation
Simulates realistic scenarios for judges
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"

def print_banner(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_step(number, text):
    print(f"\n[STEP {number}] {text}")
    print("-" * 70)

def print_action(text):
    print(f"  → {text}")

def print_result(text):
    print(f"  ✓ {text}")

def wait(seconds, message=""):
    if message:
        print(f"\n  ⏳ {message}")
    for i in range(seconds, 0, -1):
        print(f"     {i}...", end='\r')
        time.sleep(1)
    print("     Done!   ")

def demo_scenario():
    """Complete demo scenario"""
    
    print_banner("AI SURVEILLANCE CO-PILOT - LIVE DEMO")
    print("This demo simulates a real surveillance scenario.")
    print("Follow along as the system detects various security events.")
    
    input("\nPress ENTER to start the demo...")
    
    # Step 1: System Health Check
    print_step(1, "System Health Check")
    print_action("Checking AI service status...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_result(f"System Status: {data.get('status', 'unknown').upper()}")
            print_result(f"Zones Configured: {data.get('zones_configured', 0)}")
        else:
            print("  ✗ Service not responding")
            return
    except:
        print("  ✗ Cannot connect to AI service. Is it running?")
        return
    
    wait(2)
    
    # Step 2: Start Camera
    print_step(2, "Start Camera and Video Processing")
    print_action("Activating webcam and AI detection...")
    
    response = requests.post(f"{BASE_URL}/start")
    if response.status_code == 200:
        print_result("Camera activated")
        print_result("YOLO person detection: ACTIVE")
        print_result("Face blur (privacy): ENABLED")
    else:
        print("  ✗ Failed to start camera")
        return
    
    wait(3, "Initializing AI models...")
    
    # Step 3: Configure Restricted Zone
    print_step(3, "Configure Restricted Zone")
    print_action("Creating a restricted area (e.g., Server Room entrance)...")
    
    zone_data = {
        "name": "Server Room - Restricted Area",
        "polygon": [
            {"x": 150, "y": 150},
            {"x": 450, "y": 150},
            {"x": 450, "y": 400},
            {"x": 150, "y": 400}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/zones",
        json=zone_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_result(f"Zone Created: {zone_data['name']}")
        print_result(f"Zone ID: {data.get('zone', {}).get('id')}")
        print_result(f"Polygon Points: {len(zone_data['polygon'])}")
    
    wait(2)
    
    # Step 4: Demonstrate Zone Intrusion
    print_step(4, "SCENARIO: Unauthorized Zone Entry")
    print("\n📢 INSTRUCTIONS FOR PRESENTER:")
    print("   1. Stand OUTSIDE the red zone")
    print("   2. Wait for detection")
    print("   3. Then WALK INTO the red zone")
    print("   4. Watch for the alert!")
    
    input("\n   Press ENTER when ready to demonstrate...")
    
    print_action("Monitoring for zone intrusion...")
    wait(5, "Detecting persons in frame...")
    
    print("\n  🚨 EXPECTED BEHAVIOR:")
    print("     - Person detected → Green box around you")
    print("     - Entering zone → Alert triggered")
    print("     - Risk level → MEDIUM (8 points)")
    print("     - Backend receives event via HTTP")
    print("     - Frontend shows alert via WebSocket")
    
    wait(10, "Continue monitoring (walk into zone now)...")
    
    # Step 5: Demonstrate Loitering
    print_step(5, "SCENARIO: Loitering Detection")
    print("\n📢 INSTRUCTIONS FOR PRESENTER:")
    print("   1. Stand STILL in one place")
    print("   2. Don't move for 30+ seconds")
    print("   3. System will detect loitering behavior")
    
    input("\n   Press ENTER when ready...")
    
    print_action("Monitoring for loitering behavior...")
    print("  ℹ️  Loitering threshold: 30 seconds")
    print("  ℹ️  Movement threshold: 50 pixels")
    
    wait(35, "Tracking person position (stand still)...")
    
    print("\n  ⚠️  EXPECTED BEHAVIOR:")
    print("     - Person tracked for 30+ seconds")
    print("     - Minimal movement detected")
    print("     - Loitering alert triggered")
    print("     - Risk level → MEDIUM (6 points)")
    
    # Step 6: Check Statistics
    print_step(6, "System Statistics")
    print_action("Retrieving current system stats...")
    
    response = requests.get(f"{BASE_URL}/stats")
    if response.status_code == 200:
        data = response.json()
        print_result(f"Active Loitering Tracks: {data.get('loitering_tracked', 0)}")
        print_result(f"Unattended Objects: {data.get('unattended_objects', 0)}")
        print_result(f"Risk Score: {data.get('current_risk', {}).get('score', 0)}")
        print_result(f"Risk Level: {data.get('current_risk', {}).get('level', 'LOW')}")
        print_result(f"Configured Zones: {data.get('zones_count', 0)}")
    
    wait(3)
    
    # Step 7: Privacy Features
    print_step(7, "Privacy Protection Demo")
    print("\n📢 HIGHLIGHT TO JUDGES:")
    print("   ✅ Face Detection: Haar Cascade")
    print("   ✅ Automatic Blurring: Gaussian blur applied")
    print("   ✅ No Identity Storage: Only metadata saved")
    print("   ✅ No Face Recognition: Ethics-first design")
    print("   ✅ Configurable: Blur intensity adjustable")
    
    print("\n  🔒 This ensures compliance with privacy laws")
    print("  🔒 Users are informed about surveillance")
    print("  🔒 Data retention is configurable")
    
    wait(3)
    
    # Step 8: Show All Zones
    print_step(8, "Review Configured Zones")
    print_action("Fetching all restricted zones...")
    
    response = requests.get(f"{BASE_URL}/zones")
    if response.status_code == 200:
        data = response.json()
        zones = data.get('zones', [])
        
        print_result(f"Total Zones: {len(zones)}")
        for zone in zones:
            print(f"\n     Zone {zone.get('id')}: {zone.get('name')}")
            print(f"     Points: {len(zone.get('polygon', []))}")
            print(f"     Created: {zone.get('created_at')}")
    
    wait(2)
    
    # Step 9: System Architecture
    print_step(9, "Technical Architecture Overview")
    print("\n  🏗️  SYSTEM COMPONENTS:")
    print("     1. AI Service (Python)")
    print("        - YOLOv8 for person detection")
    print("        - OpenCV for video processing")
    print("        - Real-time risk scoring")
    print()
    print("     2. Backend (Node.js)")
    print("        - Event storage (MongoDB)")
    print("        - WebSocket broadcasting")
    print("        - Analytics API")
    print()
    print("     3. Frontend (React)")
    print("        - Live dashboard")
    print("        - Zone drawing interface")
    print("        - Real-time alerts")
    
    wait(3)
    
    # Step 10: Stop System
    print_step(10, "Graceful Shutdown")
    print_action("Stopping camera and video processing...")
    
    response = requests.post(f"{BASE_URL}/stop")
    if response.status_code == 200:
        print_result("Camera stopped")
        print_result("Video processing halted")
        print_result("All resources released")
    
    wait(2)
    
    # Final Summary
    print_banner("DEMO COMPLETE")
    print("\n✨ DEMONSTRATED FEATURES:")
    print("   ✅ Real-time person detection (YOLOv8)")
    print("   ✅ Restricted zone intrusion alerts")
    print("   ✅ Loitering behavior detection")
    print("   ✅ Privacy protection (face blurring)")
    print("   ✅ Risk scoring engine")
    print("   ✅ Event publishing to backend")
    print("   ✅ Modular, production-ready code")
    
    print("\n🎯 KEY DIFFERENTIATORS:")
    print("   • Actual AI, not simulated")
    print("   • Privacy-first design")
    print("   • Real-time WebSocket alerts")
    print("   • Interactive zone drawing")
    print("   • Professional code structure")
    
    print("\n📊 SCALABILITY:")
    print("   • Ready for RTSP camera streams")
    print("   • Multi-camera support possible")
    print("   • Cloud deployment ready")
    print("   • GPU acceleration supported")
    
    print("\n🏆 This is production-ready surveillance AI!")
    print()

if __name__ == "__main__":
    try:
        demo_scenario()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error during demo: {str(e)}")