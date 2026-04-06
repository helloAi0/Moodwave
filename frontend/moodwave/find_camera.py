"""
find_camera.py — Discover which camera index Iriun is on your system.
Run this FIRST to get the correct CAMERA_INDEX for sensor.py and app.py
"""
import cv2
import sys

def find_cameras():
    """Try all camera indices and report which ones work."""
    print("🔍 Scanning for available cameras...")
    print("-" * 50)
    
    available = []
    for i in range(10):  # Check indices 0-9
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"✅ Camera {i}: {w}x{h}")
                available.append(i)
                cap.release()
            else:
                cap.release()
    
    if not available:
        print("❌ No cameras found!")
        sys.exit(1)
    
    print("-" * 50)
    print(f"\n📌 IMPORTANT: Edit these files and set CAMERA_INDEX = {available[0]}")
    print(f"   Files to update:")
    print(f"     • sensor.py (line 24)")
    print(f"     • frontend/moodwave/app.py (line 44)")
    print(f"\n   Then run: python sensor.py")
    return available[0]

if __name__ == "__main__":
    idx = find_cameras()