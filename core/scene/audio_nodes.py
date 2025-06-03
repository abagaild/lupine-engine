"""
scene/audio_nodes.py

Defines AudioStreamPlayer and AudioStreamPlayer2D nodes for sound playback.
"""

from typing import Dict, Any
from .node2d import Node2D
from .base_node import Node


class AudioStreamPlayer(Node):
    """Audio player for non-positional sound effects and music."""

    def __init__(self, name: str = "AudioStreamPlayer"):
        super().__init__(name, "AudioStreamPlayer")

        # Audio properties
        self.stream: Any = None  # Reference to an AudioStream resource
        self.volume_db: float = 0.0
        self.pitch_scale: float = 1.0
        self.playing: bool = False
        self.autoplay: bool = False
        self.stream_paused: bool = False
        self.loop: bool = False

        # Bus / mixing
        self.bus: str = "Master"
        self.mix_target: str = "stereo"  # stereo, surround, center

        # Internal playback state
        self._audio_source_id: Any = None
        self._playback_position: float = 0.0

        self.script_path = "nodes/AudioStreamPlayer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "stream": self.stream,
            "volume_db": self.volume_db,
            "pitch_scale": self.pitch_scale,
            "playing": self.playing,
            "autoplay": self.autoplay,
            "stream_paused": self.stream_paused,
            "loop": self.loop,
            "bus": self.bus,
            "mix_target": self.mix_target,
            "_audio_source_id": self._audio_source_id,
            "_playback_position": self._playback_position
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioStreamPlayer":
        node = cls(data.get("name", "AudioStreamPlayer"))
        node.stream = data.get("stream")
        node.volume_db = data.get("volume_db", 0.0)
        node.pitch_scale = data.get("pitch_scale", 1.0)
        node.playing = data.get("playing", False)
        node.autoplay = data.get("autoplay", False)
        node.stream_paused = data.get("stream_paused", False)
        node.loop = data.get("loop", False)
        node.bus = data.get("bus", "Master")
        node.mix_target = data.get("mix_target", "stereo")
        node._audio_source_id = data.get("_audio_source_id")
        node._playback_position = data.get("_playback_position", 0.0)
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class AudioStreamPlayer2D(Node2D):
    """2D positional audio player (distance attenuation, panning)."""

    def __init__(self, name: str = "AudioStreamPlayer2D"):
        super().__init__(name)
        self.type = "AudioStreamPlayer2D"

        self.stream: Any = None
        self.volume_db: float = 0.0
        self.pitch_scale: float = 1.0
        self.playing: bool = False
        self.autoplay: bool = False
        self.stream_paused: bool = False
        self.loop: bool = False

        # Positional properties
        self.attenuation: float = 1.0
        self.max_distance: float = 2000.0
        self.area_mask: int = 1
        self.doppler_tracking: str = "disabled"

        # Internal playback state
        self._audio_source_id: Any = None
        self._playback_position: float = 0.0
        self._last_position: [float, float] = [0.0, 0.0]

        self.script_path = "nodes/AudioStreamPlayer2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "stream": self.stream,
            "volume_db": self.volume_db,
            "pitch_scale": self.pitch_scale,
            "playing": self.playing,
            "autoplay": self.autoplay,
            "stream_paused": self.stream_paused,
            "loop": self.loop,
            "attenuation": self.attenuation,
            "max_distance": self.max_distance,
            "area_mask": self.area_mask,
            "doppler_tracking": self.doppler_tracking,
            "_audio_source_id": self._audio_source_id,
            "_playback_position": self._playback_position,
            "_last_position": self._last_position
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioStreamPlayer2D":
        node = cls(data.get("name", "AudioStreamPlayer2D"))
        node.stream = data.get("stream")
        node.volume_db = data.get("volume_db", 0.0)
        node.pitch_scale = data.get("pitch_scale", 1.0)
        node.playing = data.get("playing", False)
        node.autoplay = data.get("autoplay", False)
        node.stream_paused = data.get("stream_paused", False)
        node.loop = data.get("loop", False)
        node.attenuation = data.get("attenuation", 1.0)
        node.max_distance = data.get("max_distance", 2000.0)
        node.area_mask = data.get("area_mask", 1)
        node.doppler_tracking = data.get("doppler_tracking", "disabled")
        node._audio_source_id = data.get("_audio_source_id")
        node._playback_position = data.get("_playback_position", 0.0)
        node._last_position = data.get("_last_position", [0.0, 0.0])
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
