"""
Example: Process a video file and save events to JSON
"""

import time
import json
from pathlib import Path
from main.video_processor import VideoProcessor

def main():
    # Configuration
    VIDEO_FILE = "test_video.mp4"  # Change to your video file
    OUTPUT_FILE = "detected_events.json"
    
    # Check if video exists
    if not Path(VIDEO_FILE).exists():
        print(f"Error: Video file '{VIDEO_FILE}' not found")
        print("Please provide a valid video file path")
        return
    
    # Store detected events
    detected_events = []
    
    def handle_event(event):
        """Callback function for detected events"""
        print(f"\n🚨 EVENT DETECTED: {event['type']}")
        print(f"   Risk: {event['risk']}/10")
        print(f"   Description: {event['description']}")
        
        # Add to list
        detected_events.append(event)
    
    def handle_frame(frame, detections, events):
        """Callback function for each processed frame"""
        print(f"\rProcessed frames: {processor.stats['processed_frames']} | "
              f"Detections: {len(detections)} | "
              f"Events: {len(events)}", end='')
    
    # Create processor
    print(f"Initializing video processor for: {VIDEO_FILE}")
    processor = VideoProcessor(VIDEO_FILE, source_type="file")
    
    # Set callbacks
    processor.set_event_callback(handle_event)
    processor.set_frame_callback(handle_frame)
    
    # Start processing
    print("Starting video processing...")
    processor.start()
    
    # Wait for processing to complete
    try:
        while processor.is_running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        processor.stop()
    
    # Print summary
    stats = processor.get_stats()
    print("\n\n" + "="*50)
    print("PROCESSING COMPLETE")
    print("="*50)
    print(f"Total frames: {stats['total_frames']}")
    print(f"Processed frames: {stats['processed_frames']}")
    print(f"Total detections: {stats['detections']}")
    print(f"Total events: {stats['events']}")
    print(f"Average FPS: {stats['fps']:.2f}")
    
    # Save events to JSON
    if detected_events:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(detected_events, f, indent=2)
        print(f"\n✅ Events saved to: {OUTPUT_FILE}")
        
        # Print event summary
        print("\nEvent Summary:")
        event_types = {}
        for event in detected_events:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        for event_type, count in event_types.items():
            print(f"  - {event_type}: {count}")
    else:
        print("\n✅ No events detected")
    
    print("\nDone!")

if __name__ == "__main__":
    main()