import time
from collections import deque, Counter

class IsoEngineV2:
    def __init__(self):
        self.emotion_window = deque(maxlen=20)
        self.current_state = "neutral"
        self.target_state = "calm"
        self.last_update = time.time()
        self.transition_progress = 0.0  # 0 → 1

    def update(self, raw_emotion: str):
        self._add_emotion(raw_emotion)
        stable_emotion = self._get_stable_emotion()
        self._update_state(stable_emotion)
        audio = self._compute_audio()

        return {
            "state": self.current_state,
            "progress": round(self.transition_progress, 2),
            "audio": audio
        }

    def set_target(self, target_name):
        """Allows the UI to change the therapy goal."""
        self.target_state = target_name

    def get_audio_params(self):
        """Helper for the initial state."""
        return self._compute_audio()

    def _add_emotion(self, emotion):
        self.emotion_window.append(emotion)

    def _get_stable_emotion(self):
        if not self.emotion_window:
            return "neutral"
        if len(self.emotion_window) < 5:
            return self.emotion_window[-1]
        counts = Counter(self.emotion_window)
        return counts.most_common(1)[0][0]

    def _update_state(self, emotion):
        mapping = {
            "angry": "high_energy",
            "fear": "high_energy",
            "sad": "low_energy",
            "neutral": "neutral",
            "happy": "uplifting",
            "surprise": "uplifting"
        }

        detected_state = mapping.get(emotion, "neutral")

        # 🚀 SPEED BOOST: Increased transition speed from 0.05 to 0.25
        if detected_state != self.current_state:
            self.transition_progress += 0.25 
        else:
            self.transition_progress = max(0, self.transition_progress - 0.02)

        # when stable enough → switch state
        if self.transition_progress >= 1.0:
            self.current_state = detected_state
            self.transition_progress = 0.0

    def _compute_audio(self):
        base = {
            "high_energy": {"bpm": 120, "freq": 440},
            "low_energy": {"bpm": 60, "freq": 174},
            "uplifting": {"bpm": 100, "freq": 528},
            "neutral": {"bpm": 80, "freq": 396}
        }

        target = {
            "calm": {"bpm": 60, "freq": 174},
            "focus": {"bpm": 90, "freq": 432},
            "happy": {"bpm": 105, "freq": 528}
        }

        current_audio = base.get(self.current_state, base["neutral"])
        target_audio = target.get(self.target_state, current_audio)

        t = self.transition_progress
        bpm = int(current_audio["bpm"] * (1 - t) + target_audio["bpm"] * t)
        freq = int(current_audio["freq"] * (1 - t) + target_audio["freq"] * t)

        return {"bpm": bpm, "freq": freq}