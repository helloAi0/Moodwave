"""
emotion_engine.py — Local emotion detection using DeepFace.
Used as fallback if backend is unreachable.
"""
import cv2
from deepface import DeepFace


class EmotionEngine:
    """
    Detects emotion from a frame using DeepFace.
    Used by the frontend app for local emotion detection.
    """

    def __init__(self):
        self.last_emotion = "neutral"
        self.transition_progress = 0.0
        self.current_track = "ambient 80bpm"

    def detect(self, frame) -> str:
        """
        Analyze a frame and return the dominant emotion.
        
        Args:
            frame: OpenCV frame (BGR)
            
        Returns:
            emotion string: one of {angry, disgust, fear, happy, neutral, sad, surprise}
        """
        try:
            # Resize for faster processing
            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            
            # Run DeepFace
            result = DeepFace.analyze(
                small,
                actions=["emotion"],
                enforce_detection=False,
                silent=True,
            )
            
            # Extract dominant emotion
            emotion = result[0]["dominant_emotion"]
            self.last_emotion = emotion
            return emotion
        except Exception as e:
            print(f"[EmotionEngine] Error: {e}")
            return self.last_emotion

    def get_next_track(self, mood: str) -> str:
        """
        Get the next recommended track for a mood.
        This is a simplified local version.
        """
        mood_tracks = {
            "angry": "ambient 60bpm",
            "disgust": "calm 70bpm",
            "fear": "grounding 75bpm",
            "sad": "slow 60bpm",
            "neutral": "lo-fi 80bpm",
            "surprise": "steady 90bpm",
            "happy": "upbeat 110bpm",
        }
        self.current_track = mood_tracks.get(mood, "ambient 80bpm")
        return self.current_track

    def get_transition_progress(self) -> float:
        """Return progress of current transition (0.0-1.0)."""
        self.transition_progress += 0.1
        if self.transition_progress > 1.0:
            self.transition_progress = 0.0
        return self.transition_progress