import cv2
import requests
from deepface import DeepFace

# --- CONFIGURATION ---
API_BASE_URL = "http://localhost:8000/api/sessions"
# 📸 CHANGE THIS: 0 is usually built-in webcam, 1 or 2 is usually Iriun
CAMERA_INDEX = 0

def run_sensor():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    # Check if Iriun is actually connected
    if not cap.isOpened():
        print(f"❌ Error: Could not find camera at index {CAMERA_INDEX}.")
        print("💡 Hint: Try changing CAMERA_INDEX to 0, 1, or 2.")
        return

    print("🎥 Iriun Cam Connected. Sending emotions to Production Backend...")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # Run detection every 15 frames to save CPU
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        
        # --- AI LOGIC ---
        try:
            # We use a smaller frame size to make DeepFace faster
            small_frame = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
            result = DeepFace.analyze(small_frame, actions=['emotion'], enforce_detection=False)
            emotion = result[0]['dominant_emotion']

            # --- SEND TO BACKEND ---
            # NOTE: If you locked /analyze with JWT, you must add headers={"Authorization": f"Bearer {token}"}
            requests.post(f"{API_BASE_URL}/analyze", params={"raw_emotion": emotion})
            
            print(f"Sent to Backend: {emotion}")
        except:
            continue

        cv2.imshow('MoodWave - Iriun Feed', frame)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_sensor()