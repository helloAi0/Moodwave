"""
music_player.py
Pygame-backed audio manager with 3-second crossfade between tracks.
"""
import pygame
import threading


class MusicPlayer:
    FADE_MS = 3000        # crossfade duration in milliseconds
    ASSETS  = "assets/music/"

    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(2)  # ch0=current, ch1=incoming
        self.current_track = None
        self._ch = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
        self._active_ch = 0   # index of the channel currently playing

    def play(self, track_key):
        """Crossfade to a new track.  No-op if track is already playing."""
        if track_key == self.current_track:
            return

        path = f"{self.ASSETS}{track_key}.mp3"
        try:
            new_sound = pygame.mixer.Sound(path)
        except FileNotFoundError:
            print(f"[MusicPlayer] Missing file: {path}")
            return

        incoming_ch = 1 - self._active_ch   # the idle channel

        # Fade out the active channel, fade in the new one
        self._ch[self._active_ch].fadeout(self.FADE_MS)
        self._ch[incoming_ch].play(new_sound, fade_ms=self.FADE_MS, loops=-1)

        # After fade completes, mark incoming as the new active
        def _switch():
            self._active_ch = incoming_ch
        threading.Timer(self.FADE_MS / 1000.0, _switch).start()

        self.current_track = track_key

    def stop(self):
        pygame.mixer.fadeout(self.FADE_MS)
        self.current_track = None