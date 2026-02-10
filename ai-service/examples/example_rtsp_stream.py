"""
Example: Process RTSP camera stream
"""

import time
import requests
from main.video_processor import VideoProcessor

def main():
    # Configuration
    RTSP_URL = "rtsp://username:password@192.168.1.100:554/stream1"
    BACKEND_URL = "http://localhost:5000/api/events"
    
    print("="*60)
    print("RTSP CAMERA SURVEILLANCE")
    print("="*60)
    print(f"Camera URL: {RTSP_URL}")
    print(f"Backend: {BACKEND_URL}")
    print("="*60)
    
    def send_to_backend(event):
        """Send event to backend API"""
        try:
            # Add camera metadata
            event['camera_id'] = 'camera_001'
            event['location'] = 'Main Entrance'
            
            # Send to backend
            response = requests.post(BACKEND_URL, json=event, timeout=5)
            
            if response.status_code == 200:
                print(f"\n✅ Event sent to backend: {event['type']}")
            else:
                print(f"\n❌ Failed to send event: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n⚠️  Backend not available - Event logged locally")
            print(f"   Type: {event['type']}, Risk: {event['risk']}")
        except Exception as e:
            print(f"\n❌ Error sending event: {e}")
    
    # Create processor
    print("\nConnecting to RTSP camera...")
    processor = VideoProcessor(RTSP_URL, source_type="rtsp")
    
    # Set event callback
    processor.set_event_callback(send_to_backend)
    
    # Start processing
    print("Starting video processing...")
    processor.start()
    
    # Monitor processing
    try:
        print("\n📹 Camera is live! Press Ctrl+C to stop")
        print("="*60)
        
        while processor.is_running:
            stats = processor.get_stats()
            
            # Print live stats every 5 seconds
            print(f"\r[{time.strftime('%H:%M:%S')}] "
                  f"FPS: {stats['fps']:.1f} | "
                  f"Frames: {stats['processed_frames']} | "
                  f"Events: {stats['events']}", end='')
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\nStopping camera surveillance...")
        processor.stop()
    
    # Print final stats
    stats = processor.get_stats()
    print("\n" + "="*60)
    print("SESSION SUMMARY")
    print("="*60)
    print(f"Total frames processed: {stats['processed_frames']}")
    print(f"Total events detected: {stats['events']}")
    print(f"Average FPS: {stats['fps']:.2f}")
    print("="*60)
    print("Done!")

if __name__ == "__main__":
    main()