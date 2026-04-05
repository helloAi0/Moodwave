from collections import deque

class IsoEngine:
    def __init__(self):
        self.emotion_window = deque(maxlen=10)
        self.current_state = "neutral"
        self.target_state = "calm"

    def update_emotion(self, emotion: str):
        self.emotion_window.append(emotion)

        return self._compute_state()

    def _compute_state(self):
        if not self.emotion_window:
            return self.current_state

        dominant = max(set(self.emotion_window), key=self.emotion_window.count)

        # Smooth transition logic
        if dominant == "angry":
            return "high_energy"
        elif dominant == "sad":
            return "low_energy"
        elif dominant == "happy":
            return "uplifting"
        else:
            return "neutral"

    def get_audio_params(self):
        mapping = {
            "high_energy": {"bpm": 120, "freq": 440},
            "low_energy": {"bpm": 60, "freq": 174},
            "uplifting": {"bpm": 100, "freq": 528},
            "neutral": {"bpm": 80, "freq": 396}
        }

        return mapping.get(self.current_state, mapping["neutral"])