"""
Utility functions for video processing and geometry operations
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from main.config import BLUR_KERNEL_SIZE, BLUR_SIGMA


def point_in_polygon(point: Tuple[int, int], polygon: List[Tuple[int, int]]) -> bool:
    """
    Check if a point is inside a polygon using ray casting algorithm
    
    Args:
        point: (x, y) coordinates
        polygon: List of (x, y) coordinates defining the polygon
    
    Returns:
        True if point is inside polygon, False otherwise
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def bbox_in_polygon(bbox: List[int], polygon: List[Tuple[int, int]], 
                    threshold: float = 0.5) -> bool:
    """
    Check if a bounding box intersects with a polygon
    
    Args:
        bbox: [x1, y1, x2, y2] bounding box coordinates
        polygon: List of (x, y) coordinates
        threshold: Minimum overlap ratio to consider as inside
    
    Returns:
        True if bbox is inside polygon
    """
    x1, y1, x2, y2 = bbox
    
    # Check center point
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    return point_in_polygon((int(center_x), int(center_y)), polygon)


def calculate_distance(point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
    """
    Calculate Euclidean distance between two points
    
    Args:
        point1: (x, y) coordinates
        point2: (x, y) coordinates
    
    Returns:
        Distance between points
    """
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def bbox_to_center(bbox: List[int]) -> Tuple[int, int]:
    """
    Convert bounding box to center point
    
    Args:
        bbox: [x1, y1, x2, y2]
    
    Returns:
        (center_x, center_y)
    """
    x1, y1, x2, y2 = bbox
    return (int((x1 + x2) / 2), int((y1 + y2) / 2))


def bbox_area(bbox: List[int]) -> int:
    """
    Calculate area of bounding box
    
    Args:
        bbox: [x1, y1, x2, y2]
    
    Returns:
        Area in pixels
    """
    x1, y1, x2, y2 = bbox
    return (x2 - x1) * (y2 - y1)


def blur_region(frame: np.ndarray, bbox: List[int]) -> np.ndarray:
    """
    Blur a region in the frame (for privacy)
    
    Args:
        frame: Input frame
        bbox: [x1, y1, x2, y2] region to blur
    
    Returns:
        Frame with blurred region
    """
    x1, y1, x2, y2 = bbox
    
    # Ensure coordinates are within frame bounds
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    
    if x2 > x1 and y2 > y1:
        roi = frame[y1:y2, x1:x2]
        blurred = cv2.GaussianBlur(roi, BLUR_KERNEL_SIZE, BLUR_SIGMA)
        frame[y1:y2, x1:x2] = blurred
    
    return frame


def draw_polygon(frame: np.ndarray, polygon: List[Tuple[int, int]], 
                 color: Tuple[int, int, int] = (0, 0, 255), 
                 thickness: int = 2) -> np.ndarray:
    """
    Draw a polygon on the frame
    
    Args:
        frame: Input frame
        polygon: List of (x, y) coordinates
        color: BGR color tuple
        thickness: Line thickness
    
    Returns:
        Frame with polygon drawn
    """
    pts = np.array(polygon, np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(frame, [pts], True, color, thickness)
    return frame


def draw_bbox(frame: np.ndarray, bbox: List[int], label: str, 
              confidence: float, color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
    """
    Draw bounding box with label on frame
    
    Args:
        frame: Input frame
        bbox: [x1, y1, x2, y2]
        label: Class label
        confidence: Detection confidence
        color: BGR color tuple
    
    Returns:
        Frame with bbox drawn
    """
    x1, y1, x2, y2 = map(int, bbox)
    
    # Draw rectangle
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
    # Draw label background
    label_text = f"{label}: {confidence:.2f}"
    (text_width, text_height), baseline = cv2.getTextSize(
        label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
    )
    
    cv2.rectangle(
        frame, 
        (x1, y1 - text_height - baseline - 5),
        (x1 + text_width, y1),
        color,
        -1
    )
    
    # Draw text
    cv2.putText(
        frame,
        label_text,
        (x1, y1 - baseline - 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )
    
    return frame


def resize_frame(frame: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
    """
    Resize frame while maintaining aspect ratio
    
    Args:
        frame: Input frame
        max_width: Maximum width
        max_height: Maximum height
    
    Returns:
        Resized frame
    """
    h, w = frame.shape[:2]
    
    if w <= max_width and h <= max_height:
        return frame
    
    # Calculate scaling factor
    scale = min(max_width / w, max_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)


def get_frame_timestamp(frame_count: int, fps: float) -> float:
    """
    Convert frame count to timestamp in seconds
    
    Args:
        frame_count: Current frame number
        fps: Frames per second
    
    Returns:
        Timestamp in seconds
    """
    return frame_count / fps if fps > 0 else 0