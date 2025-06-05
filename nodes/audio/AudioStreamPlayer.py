"""
AudioStreamPlayer node implementation for Lupine Engine
Audio playback with streaming support and effects
"""

from nodes.base.Node import Node
from typing import Dict, Any, List, Optional
import os
import time
import math


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
            },
            "loop": {
                "type": "bool",
                "value": False,
                "description": "Whether to loop the audio"
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
        self.loop: bool = False  # Whether to loop the audio
        
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
            import traceback
            traceback.print_exc()
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
        if not self.stream:
            self._audio_loaded = False
            return

        if not os.path.exists(self.stream):
            print(f"[AudioStreamPlayer] Stream file does not exist: {self.stream}")
            self._audio_loaded = False
            return

        try:
            # Get the audio system from the global game engine
            from core.game_engine import get_global_game_engine
            game_engine = get_global_game_engine()

            if game_engine and hasattr(game_engine, 'systems') and game_engine.systems.audio_system:
                audio_system = game_engine.systems.audio_system

                # Pre-load the audio buffer
                audio_buffer = audio_system.load_sound(self.stream)

                if audio_buffer:
                    self._audio_loaded = True
                    self._stream_length = audio_buffer.duration
                    print(f"[AudioStreamPlayer] Loaded stream: {self.stream} (duration: {self._stream_length:.2f}s)")
                else:
                    self._audio_loaded = False
                    print(f"[AudioStreamPlayer] Failed to load audio buffer for: {self.stream}")
            else:
                # Fallback - just mark as loaded for compatibility
                self._audio_loaded = True
                print(f"[AudioStreamPlayer] Audio system not available, marking as loaded: {self.stream}")

        except Exception as e:
            print(f"Error loading audio stream {self.stream}: {e}")
            import traceback
            traceback.print_exc()
            self._audio_loaded = False
            # Add error handling to prevent crash
            self.stream = ""  # Reset stream to prevent further errors
            self.emit_signal("stream_changed")

    def play(self, from_position: float = 0.0):
        """Start or resume playback"""
        if not self._audio_loaded:
            return

        try:
            # Get the audio system from the global game engine
            from core.game_engine import get_global_game_engine
            game_engine = get_global_game_engine()

            if game_engine and hasattr(game_engine, 'systems') and game_engine.systems.audio_system:
                audio_system = game_engine.systems.audio_system

                if self.stream_paused and self._audio_source:
                    # Resume from pause
                    self._audio_source.play()
                    self.stream_paused = False
                else:
                    # Start new playback
                    # Convert volume from dB to linear
                    linear_volume = self._db_to_linear(self.volume_db)

                    # Play the sound through OpenAL
                    self._audio_source = audio_system.play_sound(
                        self.stream,
                        volume=linear_volume,
                        pitch=self.pitch_scale,
                        loop=self.loop
                    )

                    if self._audio_source:
                        self._stream_position = from_position
                        self.playing = True
                        print(f"[AudioStreamPlayer] Playing: {self.stream}")
                    else:
                        print(f"[AudioStreamPlayer] Failed to play: {self.stream}")
                        return
            else:
                # Fallback behavior
                if self.stream_paused:
                    self.stream_paused = False
                else:
                    self._stream_position = from_position
                self.playing = True
                print(f"[AudioStreamPlayer] Playing (no audio system): {self.stream}")

        except Exception as e:
            print(f"Error playing audio stream {self.stream}: {e}")
            import traceback
            traceback.print_exc()

    def stop(self):
        """Stop playback"""
        try:
            if self._audio_source:
                self._audio_source.stop()
                self._audio_source = None

            self.playing = False
            self.stream_paused = False
            self._stream_position = 0.0
            print(f"[AudioStreamPlayer] Stopped: {self.stream}")
        except Exception as e:
            print(f"Error stopping audio stream {self.stream}: {e}")

    def pause(self):
        """Pause playback"""
        try:
            if self.playing:
                if self._audio_source:
                    self._audio_source.pause()

                self.playing = False
                self.stream_paused = True
                print(f"[AudioStreamPlayer] Paused: {self.stream}")
        except Exception as e:
            print(f"Error pausing audio stream {self.stream}: {e}")

    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        # Update playing state from audio source if available
        if self._audio_source:
            try:
                self._audio_source.update_state()
                actual_playing = self._audio_source.is_playing
                if self.playing != actual_playing:
                    self.playing = actual_playing
                    if not actual_playing and not self.stream_paused:
                        # Audio finished playing
                        self.emit_signal("finished")
                        self._audio_source = None
            except Exception as e:
                print(f"Error updating audio state for {self.stream}: {e}")

        return self.playing

    def _db_to_linear(self, db: float) -> float:
        """Convert decibel volume to linear volume (0.0 to 1.0)"""
        if db <= -80.0:
            return 0.0
        return math.pow(10.0, db / 20.0)

    def set_volume_db(self, volume_db: float):
        """Set volume in decibels"""
        self.volume_db = max(-80.0, min(24.0, volume_db))
        if self._audio_source:
            linear_volume = self._db_to_linear(self.volume_db)
            self._audio_source.set_volume(linear_volume)

    def get_volume_db(self) -> float:
        """Get volume in decibels"""
        return self.volume_db

    def set_pitch_scale(self, pitch_scale: float):
        """Set pitch scaling factor"""
        self.pitch_scale = max(0.01, min(4.0, pitch_scale))
        if self._audio_source:
            self._audio_source.set_pitch(self.pitch_scale)

    def get_pitch_scale(self) -> float:
        """Get pitch scaling factor"""
        return self.pitch_scale

    def get_playback_position(self) -> float:
        """Get current playback position in seconds"""
        return self._stream_position

    def get_stream_length(self) -> float:
        """Get total stream length in seconds"""
        return self._stream_length

    def set_stream_position(self, position: float):
        """Set playback position in seconds"""
        self._stream_position = max(0.0, position)

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
            "mix_target": self.mix_target,
            "loop": self.loop
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
        player.loop = data.get("loop", False)
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            player.add_child(child)
        
        return player

    def __str__(self) -> str:
        """String representation of the audio player"""
        return f"AudioStreamPlayer({self.name}, stream='{self.stream}', playing={self.playing})"
