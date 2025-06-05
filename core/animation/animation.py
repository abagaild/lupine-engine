"""
Animation class for Lupine Engine
Manages animation tracks, playback, and timing
"""

from typing import Dict, List, Any, Optional, Callable
import time
import copy

from .animation_track import AnimationTrack, create_track_from_dict


class Animation:
    """
    Represents a complete animation with multiple tracks
    Handles playback, looping, and track management
    """
    
    def __init__(self, name: str = "New Animation"):
        self.name = name
        self.tracks: List[AnimationTrack] = []
        self.length = 1.0  # Duration in seconds
        self.loop = False
        self.autoplay = False
        self.speed_scale = 1.0
        
        # Playback state
        self.is_playing = False
        self.current_time = 0.0
        self.last_update_time = 0.0
        
        # Events
        self.on_animation_finished: Optional[Callable] = None
        self.on_animation_looped: Optional[Callable] = None
    
    def add_track(self, track: AnimationTrack):
        """Add an animation track"""
        self.tracks.append(track)
        self._update_length()
    
    def remove_track(self, track: AnimationTrack) -> bool:
        """Remove an animation track"""
        if track in self.tracks:
            self.tracks.remove(track)
            self._update_length()
            return True
        return False
    
    def get_track(self, target_path: str, property_name: str) -> Optional[AnimationTrack]:
        """Get track by target path and property name"""
        for track in self.tracks:
            if track.target_path == target_path and track.property_name == property_name:
                return track
        return None
    
    def get_tracks_for_target(self, target_path: str) -> List[AnimationTrack]:
        """Get all tracks for a specific target"""
        return [track for track in self.tracks if track.target_path == target_path]
    
    def _update_length(self):
        """Update animation length based on tracks"""
        if not self.tracks:
            self.length = 1.0
            return
        
        max_duration = 0.0
        for track in self.tracks:
            track_duration = track.get_duration()
            if track_duration > max_duration:
                max_duration = track_duration
        
        self.length = max(max_duration, 0.1)  # Minimum length of 0.1 seconds
    
    def play(self, from_time: float = 0.0):
        """Start playing the animation"""
        self.current_time = from_time
        self.is_playing = True
        self.last_update_time = time.time()
    
    def stop(self):
        """Stop the animation"""
        self.is_playing = False
        self.current_time = 0.0
    
    def pause(self):
        """Pause the animation"""
        self.is_playing = False
    
    def resume(self):
        """Resume the animation"""
        if not self.is_playing:
            self.is_playing = True
            self.last_update_time = time.time()
    
    def seek(self, time_position: float):
        """Seek to a specific time position"""
        self.current_time = max(0.0, min(time_position, self.length))
    
    def update(self, delta_time: float = None):
        """Update animation playback"""
        if not self.is_playing:
            return
        
        # Use provided delta or calculate from real time
        if delta_time is None:
            current_real_time = time.time()
            delta_time = current_real_time - self.last_update_time
            self.last_update_time = current_real_time
        
        # Update current time
        self.current_time += delta_time * self.speed_scale
        
        # Handle looping and completion
        if self.current_time >= self.length:
            if self.loop:
                self.current_time = self.current_time % self.length
                if self.on_animation_looped:
                    self.on_animation_looped()
            else:
                self.current_time = self.length
                self.is_playing = False
                if self.on_animation_finished:
                    self.on_animation_finished()
    
    def apply_to_scene(self, scene_root):
        """Apply current animation state to scene nodes"""
        for track in self.tracks:
            if not track.enabled:
                continue
            
            # Find target node
            target_node = self._find_node_by_path(scene_root, track.target_path)
            if target_node is None:
                continue
            
            # Get value at current time and apply it
            value = track.get_value_at_time(self.current_time)
            if value is not None:
                try:
                    track.apply_value(target_node, value)
                except Exception as e:
                    print(f"Error applying animation value: {e}")
    
    def _find_node_by_path(self, root_node, path: str):
        """Find node by path string (e.g., 'Player/Sprite')"""
        if not path:
            return root_node
        
        parts = path.split('/')
        current_node = root_node
        
        for part in parts:
            if not part:  # Skip empty parts
                continue
            
            # Look for child with matching name
            found = False
            if hasattr(current_node, 'children'):
                for child in current_node.children:
                    if hasattr(child, 'name') and child.name == part:
                        current_node = child
                        found = True
                        break
            
            if not found:
                return None
        
        return current_node
    
    def get_progress(self) -> float:
        """Get animation progress as a value from 0.0 to 1.0"""
        if self.length <= 0:
            return 0.0
        return min(1.0, self.current_time / self.length)
    
    def duplicate(self) -> "Animation":
        """Create a copy of this animation"""
        new_animation = Animation(f"{self.name}_copy")
        new_animation.length = self.length
        new_animation.loop = self.loop
        new_animation.autoplay = self.autoplay
        new_animation.speed_scale = self.speed_scale
        
        # Deep copy tracks
        for track in self.tracks:
            new_track = copy.deepcopy(track)
            new_animation.tracks.append(new_track)
        
        return new_animation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert animation to dictionary for serialization"""
        return {
            "name": self.name,
            "length": self.length,
            "loop": self.loop,
            "autoplay": self.autoplay,
            "speed_scale": self.speed_scale,
            "tracks": [track.to_dict() for track in self.tracks]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Animation":
        """Create animation from dictionary"""
        animation = cls(data.get("name", "Animation"))
        animation.length = data.get("length", 1.0)
        animation.loop = data.get("loop", False)
        animation.autoplay = data.get("autoplay", False)
        animation.speed_scale = data.get("speed_scale", 1.0)
        
        # Load tracks
        for track_data in data.get("tracks", []):
            track = create_track_from_dict(track_data)
            animation.tracks.append(track)
        
        return animation


class AnimationLibrary:
    """
    Container for multiple animations
    Manages animation storage and retrieval
    """
    
    def __init__(self):
        self.animations: Dict[str, Animation] = {}
        self.default_animation: Optional[str] = None
    
    def add_animation(self, animation: Animation):
        """Add an animation to the library"""
        self.animations[animation.name] = animation
        
        # Set as default if it's the first animation or marked as autoplay
        if not self.default_animation or animation.autoplay:
            self.default_animation = animation.name
    
    def remove_animation(self, name: str) -> bool:
        """Remove an animation from the library"""
        if name in self.animations:
            del self.animations[name]
            
            # Update default if removed
            if self.default_animation == name:
                self.default_animation = next(iter(self.animations.keys()), None)
            
            return True
        return False
    
    def get_animation(self, name: str) -> Optional[Animation]:
        """Get animation by name"""
        return self.animations.get(name)
    
    def get_animation_names(self) -> List[str]:
        """Get list of all animation names"""
        return list(self.animations.keys())
    
    def has_animation(self, name: str) -> bool:
        """Check if animation exists"""
        return name in self.animations
    
    def clear(self):
        """Remove all animations"""
        self.animations.clear()
        self.default_animation = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert library to dictionary for serialization"""
        return {
            "default_animation": self.default_animation,
            "animations": {name: anim.to_dict() for name, anim in self.animations.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationLibrary":
        """Create library from dictionary"""
        library = cls()
        library.default_animation = data.get("default_animation")
        
        for name, anim_data in data.get("animations", {}).items():
            animation = Animation.from_dict(anim_data)
            library.animations[name] = animation
        
        return library
