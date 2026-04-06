"""
music_player.py — Simple music playback simulation.
In production, you'd integrate with Spotify API or local audio files.
"""
import threading


class MusicPlayer:
    """
    Manages music playback.
    Currently simulated; can be extended with real audio playback.
    """

    def __init__(self):
        self.current_track = None
        self.is_playing = False

    def play(self, track_name: str) -> None:
        """Play a track (simulated)."""
        if self.current_track != track_name:
            self.current_track = track_name
            self.is_playing = True
            print(f"🎵 Now playing: {track_name}")
            # In production: integrate with audio library here

    def stop(self) -> None:
        """Stop playback."""
        self.is_playing = False
        print("⏹ Music stopped")