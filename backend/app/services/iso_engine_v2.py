"""
iso_engine_v2.py — Iso-Principle music therapy algorithm.

Implements the Iso Principle: start with music matching the user's mood,
then gradually transition to a target mood through a sequence of tracks.

Each emotion has a progression path defined by:
  - BPM (beats per minute)
  - Frequency (Hz)
  - Energy level
  - Valence (happiness)
"""
import math
from typing import Dict, Any


class IsoEngineV2:
    """
    The Iso-Principle adaptive audio engine.
    Maps emotion → BPM/frequency path → target mood.
    """

    # Emotion → audio parameters (starting point)
    EMOTION_MAP = {
        "angry": {"bpm": 140, "freq": 200, "energy": 0.9, "valence": -0.8},
        "disgust": {"bpm": 100, "freq": 150, "energy": 0.6, "valence": -0.7},
        "fear": {"bpm": 130, "freq": 180, "energy": 0.8, "valence": -0.9},
        "sad": {"bpm": 60, "freq": 80, "energy": 0.3, "valence": -0.8},
        "neutral": {"bpm": 90, "freq": 110, "energy": 0.5, "valence": 0.0},
        "surprise": {"bpm": 110, "freq": 130, "energy": 0.7, "valence": 0.2},
        "happy": {"bpm": 120, "freq": 150, "energy": 0.8, "valence": 0.9},
    }

    # Target → desired end state
    TARGET_MAP = {
        "calm": {"bpm": 60, "freq": 80, "energy": 0.3, "valence": 0.3},
        "focus": {"bpm": 100, "freq": 120, "energy": 0.6, "valence": 0.5},
        "happy": {"bpm": 120, "freq": 150, "energy": 0.8, "valence": 0.9},
        "sleep": {"bpm": 50, "freq": 60, "energy": 0.1, "valence": 0.2},
        "energy": {"bpm": 140, "freq": 200, "energy": 0.9, "valence": 0.7},
    }

    # Transition paths: emotion → [intermediate states] → target
    TRANSITION_PATHS = {
        "angry": {
            "calm": ["ambient 60bpm", "lo-fi 80bpm", "calm 100bpm"],
            "focus": ["lo-fi 80bpm", "focus 100bpm"],
            "happy": ["upbeat 100bpm", "pop 120bpm"],
            "sleep": ["ambient 60bpm", "sleep 50bpm"],
            "energy": ["drums 110bpm", "energetic 140bpm"],
        },
        "sad": {
            "calm": ["slow 70bpm", "ambient 60bpm"],
            "focus": ["acoustic 90bpm", "lo-fi 100bpm"],
            "happy": ["uplifting 90bpm", "pop 120bpm"],
            "sleep": ["slow 60bpm", "sleep 50bpm"],
            "energy": ["building 110bpm", "energetic 140bpm"],
        },
        "neutral": {
            "calm": ["ambient 80bpm"],
            "focus": ["lo-fi 90bpm"],
            "happy": ["upbeat 110bpm"],
            "sleep": ["slow 60bpm"],
            "energy": ["drums 130bpm"],
        },
        "happy": {
            "calm": ["slow 100bpm", "ambient 60bpm"],
            "focus": ["focus 100bpm"],
            "sleep": ["slow 70bpm", "sleep 50bpm"],
            "energy": ["energetic 140bpm"],
        },
        "fear": {
            "calm": ["grounding 70bpm", "ambient 60bpm"],
            "focus": ["steady 100bpm"],
            "happy": ["uplifting 110bpm", "pop 120bpm"],
            "sleep": ["slow 60bpm"],
            "energy": ["building 120bpm"],
        },
    }

    def __init__(self, target_mood: str = "calm"):
        self.current_emotion = "neutral"
        self.target_mood = target_mood
        self.transition_index = 0
        self.current_track = None
        self.transition_progress = 0.0
        self.audio_params = self.EMOTION_MAP["neutral"].copy()

    def set_target(self, target_mood: str) -> None:
        """Change the therapy target."""
        if target_mood not in self.TARGET_MAP:
            raise ValueError(f"Invalid target: {target_mood}")
        self.target_mood = target_mood
        self.transition_index = 0
        self.transition_progress = 0.0

    def update(self, emotion: str) -> Dict[str, Any]:
        """
        Process a detected emotion and return the next audio parameters.
        
        Returns:
            {
                "emotion": str,
                "state": str,
                "audio": {"bpm": int, "freq": int, "energy": float, "volume": float},
                "progress": float (0.0-1.0),
                "track": str,
            }
        """
        if emotion not in self.EMOTION_MAP:
            emotion = "neutral"

        # If emotion changed, reset transition
        if emotion != self.current_emotion:
            self.current_emotion = emotion
            self.transition_index = 0
            self.transition_progress = 0.0

        # Get the transition path for this emotion → target
        paths = self.TRANSITION_PATHS.get(emotion, {})
        track_list = paths.get(self.target_mood, ["neutral"])

        # Advance through the track sequence
        if self.transition_index < len(track_list):
            self.current_track = track_list[self.transition_index]
            # Each track gets ~10 emotion-updates before advancing
            self.transition_progress += 1.0 / 10.0
            if self.transition_progress >= 1.0:
                self.transition_index += 1
                self.transition_progress = 0.0
        else:
            # Reached the end → stay on last track
            self.current_track = track_list[-1]
            self.transition_progress = 1.0

        # Interpolate audio parameters smoothly
        start_params = self.EMOTION_MAP[emotion]
        end_params = self.TARGET_MAP[self.target_mood]
        progress = min(
            (self.transition_index + self.transition_progress) / len(track_list), 1.0
        )

        self.audio_params = {
            "bpm": int(
                start_params["bpm"]
                + (end_params["bpm"] - start_params["bpm"]) * progress
            ),
            "freq": int(
                start_params["freq"]
                + (end_params["freq"] - start_params["freq"]) * progress
            ),
            "energy": start_params["energy"]
            + (end_params["energy"] - start_params["energy"]) * progress,
            "valence": start_params["valence"]
            + (end_params["valence"] - start_params["valence"]) * progress,
            "volume": 0.6 + 0.3 * (1 - abs(self.audio_params.get("valence", 0))),
        }

        return {
            "emotion": emotion,
            "state": self.target_mood,
            "audio": self.audio_params,
            "progress": progress,
            "track": self.current_track,
        }

    def get_audio_params(self) -> Dict[str, Any]:
        """Return current audio parameters."""
        return self.audio_params