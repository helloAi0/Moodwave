"""
emotion_engine.py — Simplified emotion detection (no DeepFace needed).
Works with or without ML libraries.
"""
import random


class EmotionEngine:
    """Simplified emotion engine for quick deployment."""

    def __init__(self):
        self.last_emotion = "neutral"
        self.transition_progress = 0.0
        self.current_track = "ambient 80bpm"
        self.frame_count = 0

    def detect(self, frame) -> str:
        """
        Simplified emotion detection.
        Returns a random emotion for demo purposes.
        In production: integrate with DeepFace or backend API.
        """
        try:
            # Try to use DeepFace if available
            from deepface import DeepFace
            import cv2
            
            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            result = DeepFace.analyze(
                small,
                actions=["emotion"],
                enforce_detection=False,
                silent=True,
            )
            emotion = result[0]["dominant_emotion"]
            self.last_emotion = emotion
            return emotion
        except:
            # Fallback: cycle through emotions for demo
            self.frame_count += 1
            emotions = ["neutral", "happy", "sad", "calm", "angry"]
            idx = (self.frame_count // 50) % len(emotions)
            self.last_emotion = emotions[idx]
            return self.last_emotion

    def get_next_track(self, mood: str) -> str:
        """Get the next recommended track for a mood."""
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