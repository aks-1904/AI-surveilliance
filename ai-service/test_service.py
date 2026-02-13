#!/usr/bin/env python3
"""
AI Service Test Suite
Validates all endpoints and core functionality
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:5000"
BACKEND_URL = "http://localhost:3000"

def print_test(name):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def test_health():
    """Test health check endpoint"""
    print_test("Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Service is healthy")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Camera Active: {data.get('camera_active')}")
            print_info(f"Zones Configured: {data.get('zones_configured')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False

def test_camera_start():
    """Test camera start"""
    print_test("Camera Start")
    
    try:
        response = requests.post(f"{BASE_URL}/start")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Camera started: {data.get('message')}")
            return True
        else:
            print_error(f"Failed to start camera: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Camera start failed: {str(e)}")
        return False

def test_zone_creation():
    """Test zone creation"""
    print_test("Zone Creation")
    
    zone_data = {
        "name": "Test Restricted Area",
        "polygon": [
            {"x": 100, "y": 100},
            {"x": 400, "y": 100},
            {"x": 400, "y": 400},
            {"x": 100, "y": 400}
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/zones",
            json=zone_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Zone created successfully")
            print_info(f"Zone ID: {data.get('zone', {}).get('id')}")
            print_info(f"Zone Name: {data.get('zone', {}).get('name')}")
            print_info(f"Points: {data.get('zone', {}).get('points')}")
            return True
        else:
            print_error(f"Failed to create zone: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Zone creation failed: {str(e)}")
        return False

def test_get_zones():
    """Test getting all zones"""
    print_test("Get All Zones")
    
    try:
        response = requests.get(f"{BASE_URL}/zones")
        
        if response.status_code == 200:
            data = response.json()
            zones = data.get('zones', [])
            print_success(f"Retrieved {len(zones)} zones")
            
            for zone in zones:
                print_info(f"  - {zone.get('name')} (ID: {zone.get('id')})")
            
            return True
        else:
            print_error(f"Failed to get zones: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Get zones failed: {str(e)}")
        return False

def test_stats():
    """Test statistics endpoint"""
    print_test("Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/stats")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Statistics retrieved")
            print_info(f"Loitering Tracked: {data.get('loitering_tracked')}")
            print_info(f"Unattended Objects: {data.get('unattended_objects')}")
            print_info(f"Current Risk: {data.get('current_risk')}")
            print_info(f"Zones Count: {data.get('zones_count')}")
            return True
        else:
            print_error(f"Failed to get stats: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Stats failed: {str(e)}")
        return False

def test_backend_connection():
    """Test connection to backend"""
    print_test("Backend Connection")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        
        if response.status_code == 200:
            print_success("Backend is reachable")
            return True
        else:
            print_error(f"Backend returned: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Backend is not running or not reachable")
        print_info("This is expected if you haven't built the backend yet")
        return False
    except Exception as e:
        print_error(f"Backend connection test failed: {str(e)}")
        return False

def test_camera_stop():
    """Test camera stop"""
    print_test("Camera Stop")
    
    try:
        response = requests.post(f"{BASE_URL}/stop")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Camera stopped: {data.get('message')}")
            return True
        else:
            print_error(f"Failed to stop camera: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Camera stop failed: {str(e)}")
        return False

def test_invalid_zone():
    """Test invalid zone data"""
    print_test("Invalid Zone Handling")
    
    invalid_zone = {
        "name": "Invalid",
        "polygon": [
            {"x": 100, "y": 100}
        ]  # Only 1 point (invalid)
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/zones",
            json=invalid_zone,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            print_success("Correctly rejected invalid zone")
            return True
        else:
            print_error(f"Should have rejected invalid zone, got: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Invalid zone test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI SURVEILLANCE CO-PILOT - TEST SUITE")
    print("="*60)
    
    results = {
        "Health Check": test_health(),
        "Camera Start": test_camera_start(),
        "Zone Creation": test_zone_creation(),
        "Get Zones": test_get_zones(),
        "Statistics": test_stats(),
        "Invalid Zone Handling": test_invalid_zone(),
        "Backend Connection": test_backend_connection(),
        "Camera Stop": test_camera_stop()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    print_info("Make sure the AI service is running on port 5000")
    print_info("Run: python app.py")
    print_info("")
    
    time.sleep(1)
    
    sys.exit(run_all_tests())