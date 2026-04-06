"""
music_player.py — Music playback simulator.
For now, just logs what would play. In production, integrate with:
- Spotify API
- YouTube Music
- Local audio files
- Web Audio API
"""
import threading


class MusicPlayer:
    """Manages music playback (demo version)."""

    def __init__(self):
        self.current_track = None
        self.is_playing = False
        self.track_history = []

    def play(self, track_name: str) -> None:
        """Play a track (logged for demo)."""
        if self.current_track != track_name:
            self.current_track = track_name
            self.is_playing = True
            self.track_history.append(track_name)
            print(f"🎵 Now playing: {track_name}")
            
            # In production, play actual audio here
            # For now: this would integrate with Spotify, YouTube Music, etc.

    def stop(self) -> None:
        """Stop playback."""
        self.is_playing = False
        print("⏹ Music stopped")
    
    def get_history(self):
        """Return play history."""
        return self.track_history