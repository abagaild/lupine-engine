"""
AudioStreamPlayer node implementation for Lupine Engine
Audio playback with streaming support and effects
"""

from nodes.base.Node import Node
from typing import Dict, Any, List, Optional
import os
import time


class AudioStreamPlayer(Node):
    """
    Audio stream player for playing sound effects and music.
    
    Features:
    - Stream audio files (WAV, OGG, MP3, FLAC)
    - Volume and pitch control
    - Looping support
    - Autoplay functionality
    - Signal emission for audio events
    """

    def __init__(self, name: str = "AudioStreamPlayer"):
        super().__init__(name)
        self.type = "AudioStreamPlayer"
        
        # Export variables for editor
        self.export_variables = {
            "stream": {
                "type": "path",
                "value": "",
                "filter": "*.wav,*.ogg,*.mp3,*.flac",
                "description": "Audio file to play"
            },
            "volume_db": {
                "type": "float",
                "value": 0.0,
                "min": -80.0,
                "max": 24.0,
                "description": "Volume in decibels"
            },
            "pitch_scale": {
                "type": "float",
                "value": 1.0,
                "min": 0.01,
                "max": 4.0,
                "description": "Pitch scaling factor"
            },
            "playing": {
                "type": "bool",
                "value": False,
                "description": "Whether audio is currently playing"
            },
            "autoplay": {
                "type": "bool",
                "value": False,
                "description": "Start playing automatically when entering tree"
            },
            "stream_paused": {
                "type": "bool",
                "value": False,
                "description": "Whether the stream is paused"
            },
            "mix_target": {
                "type": "enum",
                "value": "stereo",
                "options": ["stereo", "surround", "center"],
                "description": "Audio mix target"
            }
        }
        
        # Audio properties
        self.stream: str = ""  # Path to audio file
        self.volume_db: float = 0.0  # Volume in decibels
        self.pitch_scale: float = 1.0  # Pitch scaling factor
        self.playing: bool = False  # Currently playing
        self.autoplay: bool = False  # Auto-start when entering tree
        self.stream_paused: bool = False  # Stream is paused
        self.mix_target: str = "stereo"  # Audio mix target
        
        # Internal state
        self._audio_loaded: bool = False
        self._audio_source = None  # Reference to audio system source
        self._stream_position: float = 0.0  # Current playback position
        self._stream_length: float = 0.0  # Total stream length
        
        # Built-in signals
        self.add_signal("finished")  # Emitted when playback finishes
        self.add_signal("stream_changed")  # Emitted when stream changes

    def _ready(self):
        """Called when audio player enters the scene tree"""
        try:
            # Call parent _ready if it exists
            if hasattr(super(), '_ready'):
                super()._ready()

            if self.stream:
                self._load_stream()

            if self.autoplay and self._audio_loaded:
                self.play()
        except Exception as e:
            print(f"Error in AudioStreamPlayer._ready(): {e}")
            # Don't re-raise to prevent crash

    def set_stream(self, stream_path: str):
        """Set the audio stream file"""
        if self.stream != stream_path:
            self.stop()  # Stop current playback
            self.stream = stream_path
            self._load_stream()
            self.emit_signal("stream_changed")

    def get_stream(self) -> str:
        """Get the current stream file path"""
        return self.stream

    def _load_stream(self):
        """Load the audio stream"""
        if not self.stream or not os.path.exists(self.stream):
            self._audio_loaded = False
            return
        
        try:
            # In a full implementation, this would load the audio file
            # For now, just mark as loaded
            self._audio_loaded = True
            print(f"[AudioStreamPlayer] Loaded stream: {self.stream}")
        except Exception as e:
            print(f"Error loading audio stream {self.stream}: {e}")
            self._audio_loaded = False

    def play(self, from_position: float = 0.0):
        """Start or resume playback"""
        if not self._audio_loaded:
            return
        
        if self.stream_paused:
            # Resume from pause
            self.stream_paused = False
        else:
            # Start from beginning or specified position
            self._stream_position = from_position
        
        self.playing = True
        print(f"[AudioStreamPlayer] Playing: {self.stream}")

    def stop(self):
        """Stop playback"""
        self.playing = False
        self.stream_paused = False
        self._stream_position = 0.0
        print(f"[AudioStreamPlayer] Stopped: {self.stream}")

    def pause(self):
        """Pause playback"""
        if self.playing:
            self.playing = False
            self.stream_paused = True
            print(f"[AudioStreamPlayer] Paused: {self.stream}")

    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        return self.playing

    def set_volume_db(self, volume_db: float):
        """Set volume in decibels"""
        self.volume_db = max(-80.0, min(24.0, volume_db))

    def get_volume_db(self) -> float:
        """Get volume in decibels"""
        return self.volume_db

    def set_pitch_scale(self, pitch: float):
        """Set pitch scale factor"""
        self.pitch_scale = max(0.01, min(4.0, pitch))

    def get_pitch_scale(self) -> float:
        """Get pitch scale factor"""
        return self.pitch_scale

    def set_stream_position(self, position: float):
        """Set playback position in seconds"""
        self._stream_position = max(0.0, position)

    def get_stream_position(self) -> float:
        """Get current playback position in seconds"""
        return self._stream_position

    def get_stream_length(self) -> float:
        """Get total stream length in seconds"""
        return self._stream_length

    def set_autoplay(self, autoplay: bool):
        """Set autoplay mode"""
        self.autoplay = autoplay

    def is_autoplay_enabled(self) -> bool:
        """Check if autoplay is enabled"""
        return self.autoplay

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "stream": self.stream,
            "volume_db": self.volume_db,
            "pitch_scale": self.pitch_scale,
            "playing": self.playing,
            "autoplay": self.autoplay,
            "stream_paused": self.stream_paused,
            "mix_target": self.mix_target
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioStreamPlayer":
        """Create from dictionary"""
        player = cls(data.get("name", "AudioStreamPlayer"))
        cls._apply_node_properties(player, data)
        
        # Apply AudioStreamPlayer properties
        player.stream = data.get("stream", "")
        player.volume_db = data.get("volume_db", 0.0)
        player.pitch_scale = data.get("pitch_scale", 1.0)
        player.playing = data.get("playing", False)
        player.autoplay = data.get("autoplay", False)
        player.stream_paused = data.get("stream_paused", False)
        player.mix_target = data.get("mix_target", "stereo")
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            player.add_child(child)
        
        return player

    def __str__(self) -> str:
        """String representation of the audio player"""
        return f"AudioStreamPlayer({self.name}, stream='{self.stream}', playing={self.playing})"
