from collections import deque
import numpy as np

class EmotionEngineV2:
    def __init__(self, window_size=15):
        # 1. Emotional Space Definitions
        self.EMOTION_MAP = {
            "angry":    {"valence": -0.8, "arousal": 0.9},
            "sad":      {"valence": -0.9, "arousal": 0.2},
            "fear":     {"valence": -0.7, "arousal": 0.8},
            "neutral":  {"valence":  0.0, "arousal": 0.5},
            "happy":    {"valence":  0.9, "arousal": 0.7},
            "surprise": {"valence":  0.2, "arousal": 0.9},
        }

        self.TARGET_STATES = {
            "sleep":  {"valence": 0.2, "arousal": 0.1},
            "focus":  {"valence": 0.3, "arousal": 0.6},
            "calm":   {"valence": 0.6, "arousal": 0.2},
            "energy": {"valence": 0.9, "arousal": 0.9},
        }

        # 2. State Tracking
        self.window = deque(maxlen=window_size)
        self.target_state = self.TARGET_STATES["calm"] # Default target
        
        # Where the audio is CURRENTLY playing
        self.iso_state = {"valence": 0.0, "arousal": 0.5} 
        self.progress = 0.0

    def ease_in_out(self, t):
        """Smooths the transition curve."""
        # Ensure t stays between 0 and 1
        t = max(0.0, min(1.0, t))
        return t * t * (3 - 2 * t)

    def set_target(self, target_name):
        """Allows the user to change their therapy goal from the UI."""
        if target_name in self.TARGET_STATES:
            self.target_state = self.TARGET_STATES[target_name]
            self.progress = 0.0 # Reset progress for the new journey

    def process_frame(self, raw_emotion: str):
        """
        The main pipeline: Raw Emotion -> Smoothed -> Iso Progress -> Audio Params
        Call this every time DeepFace spits out a new emotion.
        """
        # 1. Map raw string to vector
        raw_vec = self.EMOTION_MAP.get(raw_emotion, self.EMOTION_MAP["neutral"])
        self.window.append(raw_vec)

        # 2. Smooth the data
        smoothed_valence = np.mean([v["valence"] for v in self.window])
        smoothed_arousal = np.mean([v["arousal"] for v in self.window])

        # Check stability: Is the standard deviation low enough?
        valences = [v["valence"] for v in self.window]
        is_stable = np.std(valences) < 0.3 if len(self.window) == self.window.maxlen else False

        # 3. Apply the Stability Gate & Progress
        if is_stable:
            self.progress += 0.01
        else:
            self.progress -= 0.02
        
        # Clamp progress between 0 and 1
        self.progress = max(0.0, min(1.0, self.progress))

        # 4. Calculate Iso-State using the Ease Curve
        curve = self.ease_in_out(self.progress)
        
        self.iso_state["valence"] = smoothed_valence + (self.target_state["valence"] - smoothed_valence) * curve
        self.iso_state["arousal"] = smoothed_arousal + (self.target_state["arousal"] - smoothed_arousal) * curve

        # 5. Map to final Audio Parameters
        audio_params = self.map_to_audio(self.iso_state)
        
        return {
            "raw_emotion": raw_emotion,
            "smoothed": {"valence": smoothed_valence, "arousal": smoothed_arousal, "stable": is_stable},
            "iso_state": self.iso_state,
            "audio_params": audio_params,
            "progress_pct": round(self.progress * 100, 1)
        }

    def map_to_audio(self, state):
        """Converts the math into physical sound constraints."""
        # Clamp arousal between 0 and 1, valence between -1 and 1
        arousal = max(0.0, min(1.0, state["arousal"]))
        valence = max(-1.0, min(1.0, state["valence"]))

        return {
            "bpm": int(60 + arousal * 80),          # Scales from 60 to 140 BPM
            "energy_level": round(arousal, 2),      # 0.0 to 1.0 (useful for Spotify API)
            "valence_level": round(valence, 2),     # -1.0 to 1.0
            "volume": round(0.5 + (valence * 0.5), 2) # Sad = quieter, Happy = louder
        }