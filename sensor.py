"""
sensor.py — MoodWave face-emotion sensor.

Captures frames from a webcam (or Iriun virtual cam), runs DeepFace
emotion detection at a configurable interval, and POSTs results to
the FastAPI backend which broadcasts them via Socket.IO.

Usage:
    python sensor.py

Configuration:
    Edit the constants below or set the matching environment variables.
"""
import os
import time
import threading
import cv2
import requests
from deepface import DeepFace

# ── Configuration ─────────────────────────────────────────────────────────
API_BASE_URL = os.getenv(
    "API_BASE_URL", "http://localhost:8000/api/sessions"
)
APP_TOKEN = os.getenv("APP_TOKEN", "")  # paste your JWT here if /analyze requires auth

# 👇 UPDATED: Hardcoded to Camera Index 0
CAMERA_INDEX = 0

DETECT_EVERY_N = int(os.getenv("DETECT_EVERY_N", "15"))  # run AI every N frames
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "75"))
WINDOW_TITLE = "MoodWave Sensor — press Q to quit"
# ────────────────────────────────────────────────────────────────────────

_headers = {"Content-Type": "application/json"}
if APP_TOKEN:
    _headers["Authorization"] = f"Bearer {APP_TOKEN}"


def send_emotion(emotion: str) -> None:
    """
    POST the detected emotion to the backend in a daemon thread so the
    video loop is never blocked by network latency.
    """

    def _post():
        try:
            resp = requests.post(
                f"{API_BASE_URL}/analyze",
                json={"emotion": emotion},  # ← uses request BODY, not query param
                headers=_headers,
                timeout=3.0,
            )
            resp.raise_for_status()
            print(f"  → Sent: {emotion}  ({resp.status_code})")
        except requests.exceptions.RequestException as exc:
            print(f"  ⚠ Backend unreachable: {exc}")

    threading.Thread(target=_post, daemon=True).start()


def run_sensor() -> None:
    backend_flag = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
    cap = cv2.VideoCapture(CAMERA_INDEX, backend_flag)

    if not cap.isOpened():
        print(f"❌ Cannot open camera index {CAMERA_INDEX}.")
        print("   Run  python find_camera.py  to discover the correct index.")
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # always grab the freshest frame
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"🎥 Camera {CAMERA_INDEX} opened at {w}×{h}")
    print(
        f"   Analysing every {DETECT_EVERY_N} frames — press Q to quit."
    )

    frame_n = 0
    last_emotion = "neutral"

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            frame_n += 1

            # ── AI detection (every N frames) ─────────────────────────────
            if frame_n % DETECT_EVERY_N == 0:
                try:
                    small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                    result = DeepFace.analyze(
                        small,
                        actions=["emotion"],
                        enforce_detection=False,
                        silent=True,
                    )
                    # DeepFace returns a list when enforce_detection=False
                    dominant = result[0]["dominant_emotion"]
                    if dominant != last_emotion:
                        last_emotion = dominant
                        send_emotion(dominant)
                except Exception as exc:
                    print(f"  ⚠ DeepFace error: {exc}")

            # ── Overlay emotion label ──────────────────────────────────────
            cv2.putText(
                frame,
                f"Emotion: {last_emotion}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )
            cv2.imshow(WINDOW_TITLE, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("🛑 Sensor stopped.")


if __name__ == "__main__":
    run_sensor()