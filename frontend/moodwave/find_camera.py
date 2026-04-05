"""
find_camera.py  —  Run this ONCE to find your Iriun camera index.
Usage:  python find_camera.py

It prints every available camera index and opens a preview window for each.
The one showing your phone = the index to put in app.py.
Press any key to move to the next camera. Close the window when done.
"""
import cv2

print("Scanning camera indices 0-5...\n")

for index in range(6):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)   # CAP_DSHOW = Windows DirectShow
    if not cap.isOpened():
        print(f"  Index {index}: not found")
        continue

    ret, frame = cap.read()
    if ret and frame is not None:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"  Index {index}: FOUND  ({w}x{h}) — showing preview, press any key...")
        cv2.imshow(f"Camera {index} — press any key", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print(f"  Index {index}: opened but no frame")

    cap.release()

print("\nDone. Use the index that showed your phone in app.py -> CAMERA_SOURCE")