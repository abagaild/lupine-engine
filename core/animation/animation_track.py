"""
Animation track classes for Lupine Engine
Handles different types of animated properties and keyframes
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from abc import ABC, abstractmethod
import copy

from .tween import Tween, TweenType, EaseType


class Keyframe:
    """
    Represents a single keyframe in an animation track
    """
    
    def __init__(self, time: float, value: Any, tween_type: TweenType = TweenType.LINEAR, 
                 ease_type: EaseType = EaseType.IN_OUT):
        self.time = time
        self.value = value
        self.tween_type = tween_type
        self.ease_type = ease_type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert keyframe to dictionary for serialization"""
        return {
            "time": self.time,
            "value": self.value,
            "tween_type": self.tween_type.value,
            "ease_type": self.ease_type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Keyframe":
        """Create keyframe from dictionary"""
        return cls(
            time=data["time"],
            value=data["value"],
            tween_type=TweenType(data.get("tween_type", "linear")),
            ease_type=EaseType(data.get("ease_type", "in_out"))
        )


class AnimationTrack(ABC):
    """
    Base class for animation tracks
    Handles keyframes and interpolation for a specific property
    """
    
    def __init__(self, target_path: str, property_name: str):
        self.target_path = target_path  # Node path (e.g., "Player/Sprite")
        self.property_name = property_name  # Property name (e.g., "position")
        self.keyframes: List[Keyframe] = []
        self.enabled = True
    
    def add_keyframe(self, time: float, value: Any, tween_type: TweenType = TweenType.LINEAR,
                    ease_type: EaseType = EaseType.IN_OUT) -> Keyframe:
        """Add a keyframe to the track"""
        keyframe = Keyframe(time, value, tween_type, ease_type)
        
        # Insert keyframe in chronological order
        inserted = False
        for i, existing_kf in enumerate(self.keyframes):
            if existing_kf.time > time:
                self.keyframes.insert(i, keyframe)
                inserted = True
                break
            elif existing_kf.time == time:
                # Replace existing keyframe at same time
                self.keyframes[i] = keyframe
                inserted = True
                break
        
        if not inserted:
            self.keyframes.append(keyframe)
        
        return keyframe
    
    def remove_keyframe(self, time: float) -> bool:
        """Remove keyframe at specific time"""
        for i, keyframe in enumerate(self.keyframes):
            if abs(keyframe.time - time) < 0.001:  # Small tolerance for float comparison
                del self.keyframes[i]
                return True
        return False
    
    def get_keyframe_at_time(self, time: float) -> Optional[Keyframe]:
        """Get keyframe at specific time"""
        for keyframe in self.keyframes:
            if abs(keyframe.time - time) < 0.001:
                return keyframe
        return None
    
    def get_value_at_time(self, time: float) -> Any:
        """Get interpolated value at specific time"""
        if not self.keyframes:
            return None
        
        # Find surrounding keyframes
        before_kf = None
        after_kf = None
        
        for keyframe in self.keyframes:
            if keyframe.time <= time:
                before_kf = keyframe
            elif keyframe.time > time and after_kf is None:
                after_kf = keyframe
                break
        
        # Handle edge cases
        if before_kf is None:
            return self.keyframes[0].value
        if after_kf is None:
            return before_kf.value
        if before_kf.time == after_kf.time:
            return before_kf.value
        
        # Interpolate between keyframes
        progress = (time - before_kf.time) / (after_kf.time - before_kf.time)
        return self._interpolate_value(before_kf, after_kf, progress)
    
    def _interpolate_value(self, start_kf: Keyframe, end_kf: Keyframe, progress: float) -> Any:
        """Interpolate between two keyframes"""
        return Tween.interpolate(
            start_kf.value, 
            end_kf.value, 
            progress, 
            start_kf.tween_type, 
            start_kf.ease_type
        )
    
    def get_duration(self) -> float:
        """Get total duration of the track"""
        if not self.keyframes:
            return 0.0
        return max(kf.time for kf in self.keyframes)
    
    def clear_keyframes(self):
        """Remove all keyframes"""
        self.keyframes.clear()
    
    @abstractmethod
    def apply_value(self, target_node: Any, value: Any):
        """Apply the animated value to the target node"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert track to dictionary for serialization"""
        return {
            "type": self.__class__.__name__,
            "target_path": self.target_path,
            "property_name": self.property_name,
            "enabled": self.enabled,
            "keyframes": [kf.to_dict() for kf in self.keyframes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationTrack":
        """Create track from dictionary"""
        track = cls(data["target_path"], data["property_name"])
        track.enabled = data.get("enabled", True)
        
        for kf_data in data.get("keyframes", []):
            keyframe = Keyframe.from_dict(kf_data)
            track.keyframes.append(keyframe)
        
        return track


class PropertyTrack(AnimationTrack):
    """
    Track for animating generic node properties
    """
    
    def apply_value(self, target_node: Any, value: Any):
        """Apply the animated value to the target node property"""
        if hasattr(target_node, self.property_name):
            setattr(target_node, self.property_name, value)


class SpriteFrameTrack(AnimationTrack):
    """
    Track for animating sprite frames (frame-by-frame animation)
    """
    
    def __init__(self, target_path: str):
        super().__init__(target_path, "frame")
    
    def apply_value(self, target_node: Any, value: Any):
        """Apply frame value to sprite node"""
        if hasattr(target_node, 'frame'):
            target_node.frame = int(value)
            if hasattr(target_node, '_update_region_for_frame'):
                target_node._update_region_for_frame()


class TransformTrack(AnimationTrack):
    """
    Track for animating transform properties (position, rotation, scale)
    """
    
    def apply_value(self, target_node: Any, value: Any):
        """Apply transform value to node"""
        if self.property_name == "position" and hasattr(target_node, 'position'):
            target_node.position = list(value) if isinstance(value, (list, tuple)) else value
        elif self.property_name == "rotation" and hasattr(target_node, 'rotation'):
            target_node.rotation = float(value)
        elif self.property_name == "scale" and hasattr(target_node, 'scale'):
            target_node.scale = list(value) if isinstance(value, (list, tuple)) else value


class ColorTrack(AnimationTrack):
    """
    Track for animating color properties (modulate, color, etc.)
    """
    
    def apply_value(self, target_node: Any, value: Any):
        """Apply color value to node"""
        if hasattr(target_node, self.property_name):
            # Ensure value is a list for color properties
            color_value = list(value) if isinstance(value, (list, tuple)) else value
            setattr(target_node, self.property_name, color_value)


class AudioTrack(AnimationTrack):
    """
    Track for animating audio properties and triggering audio events
    """
    
    def apply_value(self, target_node: Any, value: Any):
        """Apply audio value or trigger audio event"""
        if self.property_name == "volume" and hasattr(target_node, 'volume'):
            target_node.volume = float(value)
        elif self.property_name == "pitch" and hasattr(target_node, 'pitch'):
            target_node.pitch = float(value)
        elif self.property_name == "play" and value and hasattr(target_node, 'play'):
            target_node.play()
        elif self.property_name == "stop" and value and hasattr(target_node, 'stop'):
            target_node.stop()


# Track type registry for deserialization
TRACK_TYPES = {
    "PropertyTrack": PropertyTrack,
    "SpriteFrameTrack": SpriteFrameTrack,
    "TransformTrack": TransformTrack,
    "ColorTrack": ColorTrack,
    "AudioTrack": AudioTrack
}


def create_track_from_dict(data: Dict[str, Any]) -> AnimationTrack:
    """Create appropriate track type from dictionary data"""
    track_type = data.get("type", "PropertyTrack")
    track_class = TRACK_TYPES.get(track_type, PropertyTrack)
    return track_class.from_dict(data)
