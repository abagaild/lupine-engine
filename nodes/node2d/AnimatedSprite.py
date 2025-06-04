"""
AnimatedSprite node implementation for Lupine Engine
2D sprite with animation support using sprite sheets
"""

from nodes.node2d.Sprite import Sprite
from typing import Dict, Any, List, Optional
import time


class AnimatedSprite(Sprite):
    """
    Animated sprite node for displaying sprite sheet animations.
    
    Features:
    - Sprite sheet animation support
    - Multiple animation sequences
    - Configurable frame rate and timing
    - Animation playback control (play, pause, stop)
    - Loop and one-shot animations
    - Frame change signals
    - Animation finished signals
    """
    
    def __init__(self, name: str = "AnimatedSprite"):
        super().__init__(name)
        self.type = "AnimatedSprite"
        
        # Export variables for editor
        self.export_variables.update({
            "frames": {
                "type": "int",
                "value": 1,
                "min": 1,
                "description": "Number of frames in the sprite sheet"
            },
            "hframes": {
                "type": "int",
                "value": 1,
                "min": 1,
                "description": "Number of horizontal frames"
            },
            "vframes": {
                "type": "int",
                "value": 1,
                "min": 1,
                "description": "Number of vertical frames"
            },
            "frame": {
                "type": "int",
                "value": 0,
                "min": 0,
                "description": "Current frame index"
            },
            "speed_scale": {
                "type": "float",
                "value": 1.0,
                "min": 0.0,
                "description": "Animation speed multiplier"
            },
            "playing": {
                "type": "bool",
                "value": False,
                "description": "Whether animation is playing"
            }
        })
        
        # Animation properties
        self.frames: int = 1
        self.hframes: int = 1
        self.vframes: int = 1
        self.frame: int = 0
        self.speed_scale: float = 1.0
        self.playing: bool = False
        
        # Animation sequences
        self._animations: Dict[str, Dict[str, Any]] = {}
        self._current_animation: str = ""
        self._default_animation: str = ""
        
        # Playback state
        self._frame_time: float = 0.0
        self._animation_time: float = 0.0
        self._last_frame_time: float = 0.0
        self._animation_finished: bool = False
        
        # Built-in signals
        self.add_signal("animation_finished")
        self.add_signal("animation_changed")
        self.add_signal("frame_changed")
    
    def _process(self, delta: float):
        """Process animation updates"""
        super()._process(delta)
        
        if self.playing and self._current_animation:
            self._update_animation(delta)
    
    def _update_animation(self, delta: float):
        """Update the current animation"""
        if not self._current_animation or self._current_animation not in self._animations:
            return
        
        animation = self._animations[self._current_animation]
        frame_count = len(animation.get("frames", []))
        
        if frame_count == 0:
            return
        
        # Calculate frame duration
        fps = animation.get("fps", 10.0)
        frame_duration = 1.0 / (fps * self.speed_scale) if fps > 0 else 0.1
        
        # Update animation time
        self._animation_time += delta
        
        # Check if we need to advance frame
        if self._animation_time >= frame_duration:
            self._animation_time -= frame_duration
            self._advance_frame()
    
    def _advance_frame(self):
        """Advance to the next frame"""
        if not self._current_animation or self._current_animation not in self._animations:
            return
        
        animation = self._animations[self._current_animation]
        frames = animation.get("frames", [])
        
        if not frames:
            return
        
        current_index = 0
        try:
            current_index = frames.index(self.frame)
        except ValueError:
            current_index = 0
        
        # Advance to next frame
        next_index = current_index + 1
        
        # Handle looping
        if next_index >= len(frames):
            if animation.get("loop", True):
                next_index = 0
            else:
                # Animation finished
                self.playing = False
                self._animation_finished = True
                self.emit_signal("animation_finished", self._current_animation)
                return
        
        # Set new frame
        old_frame = self.frame
        self.frame = frames[next_index]
        
        if old_frame != self.frame:
            self._update_region_for_frame()
            self.emit_signal("frame_changed", old_frame, self.frame)
    
    def _update_region_for_frame(self):
        """Update texture region based on current frame"""
        if not self._texture_loaded or self.frames <= 1:
            return
        
        # Calculate frame size
        frame_width = self._texture_size[0] / self.hframes
        frame_height = self._texture_size[1] / self.vframes
        
        # Calculate frame position
        frame_x = (self.frame % self.hframes) * frame_width
        frame_y = (self.frame // self.hframes) * frame_height
        
        # Update region
        self.region_enabled = True
        self.region_rect = [frame_x, frame_y, frame_width, frame_height]
    
    def add_animation(self, name: str, frames: List[int], fps: float = 10.0, loop: bool = True):
        """Add an animation sequence"""
        self._animations[name] = {
            "frames": frames.copy(),
            "fps": fps,
            "loop": loop
        }
        
        if not self._default_animation:
            self._default_animation = name
    
    def remove_animation(self, name: str):
        """Remove an animation sequence"""
        if name in self._animations:
            del self._animations[name]
            
            if self._current_animation == name:
                self.stop()
            
            if self._default_animation == name:
                self._default_animation = next(iter(self._animations.keys()), "")
    
    def has_animation(self, name: str) -> bool:
        """Check if an animation exists"""
        return name in self._animations
    
    def get_animation_names(self) -> List[str]:
        """Get all animation names"""
        return list(self._animations.keys())
    
    def play(self, name: str = "", backwards: bool = False):
        """Play an animation"""
        if not name:
            name = self._default_animation
        
        if not name or name not in self._animations:
            return
        
        old_animation = self._current_animation
        self._current_animation = name
        self.playing = True
        self._animation_time = 0.0
        self._animation_finished = False
        
        # Set to first frame
        animation = self._animations[name]
        frames = animation.get("frames", [])
        
        if frames:
            if backwards:
                self.frame = frames[-1]
            else:
                self.frame = frames[0]
            self._update_region_for_frame()
        
        if old_animation != name:
            self.emit_signal("animation_changed", old_animation, name)
    
    def stop(self):
        """Stop the current animation"""
        self.playing = False
        self._current_animation = ""
        self._animation_time = 0.0
        self._animation_finished = False
    
    def pause(self):
        """Pause the current animation"""
        self.playing = False
    
    def resume(self):
        """Resume the current animation"""
        if self._current_animation:
            self.playing = True
    
    def is_playing(self) -> bool:
        """Check if an animation is playing"""
        return self.playing
    
    def get_current_animation(self) -> str:
        """Get the current animation name"""
        return self._current_animation
    
    def set_frame(self, frame_index: int):
        """Set the current frame"""
        old_frame = self.frame
        self.frame = max(0, min(frame_index, self.frames - 1))
        
        if old_frame != self.frame:
            self._update_region_for_frame()
            self.emit_signal("frame_changed", old_frame, self.frame)
    
    def get_frame(self) -> int:
        """Get the current frame"""
        return self.frame
    
    def set_frames(self, frame_count: int):
        """Set the total number of frames"""
        self.frames = max(1, frame_count)
        self.frame = min(self.frame, self.frames - 1)
        self._update_region_for_frame()
    
    def get_frames(self) -> int:
        """Get the total number of frames"""
        return self.frames
    
    def set_hframes(self, hframes: int):
        """Set the number of horizontal frames"""
        self.hframes = max(1, hframes)
        self._update_region_for_frame()
    
    def get_hframes(self) -> int:
        """Get the number of horizontal frames"""
        return self.hframes
    
    def set_vframes(self, vframes: int):
        """Set the number of vertical frames"""
        self.vframes = max(1, vframes)
        self._update_region_for_frame()
    
    def get_vframes(self) -> int:
        """Get the number of vertical frames"""
        return self.vframes
    
    def set_speed_scale(self, scale: float):
        """Set the animation speed scale"""
        self.speed_scale = max(0.0, scale)
    
    def get_speed_scale(self) -> float:
        """Get the animation speed scale"""
        return self.speed_scale
    
    def is_animation_finished(self) -> bool:
        """Check if the current animation has finished"""
        return self._animation_finished
    
    def get_animation_fps(self, name: str) -> float:
        """Get the FPS of an animation"""
        if name in self._animations:
            return self._animations[name].get("fps", 10.0)
        return 10.0
    
    def set_animation_fps(self, name: str, fps: float):
        """Set the FPS of an animation"""
        if name in self._animations:
            self._animations[name]["fps"] = max(0.1, fps)
    
    def is_animation_looping(self, name: str) -> bool:
        """Check if an animation is set to loop"""
        if name in self._animations:
            return self._animations[name].get("loop", True)
        return True
    
    def set_animation_loop(self, name: str, loop: bool):
        """Set whether an animation should loop"""
        if name in self._animations:
            self._animations[name]["loop"] = loop
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "frames": self.frames,
            "hframes": self.hframes,
            "vframes": self.vframes,
            "frame": self.frame,
            "speed_scale": self.speed_scale,
            "playing": self.playing,
            "_animations": self._animations.copy(),
            "_current_animation": self._current_animation,
            "_default_animation": self._default_animation
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimatedSprite":
        """Create from dictionary"""
        sprite = cls(data.get("name", "AnimatedSprite"))
        cls._apply_node_properties(sprite, data)
        
        # Apply Node2D properties
        sprite.position = data.get("position", [0.0, 0.0])
        sprite.rotation = data.get("rotation", 0.0)
        sprite.scale = data.get("scale", [1.0, 1.0])
        sprite.z_index = data.get("z_index", 0)
        sprite.z_as_relative = data.get("z_as_relative", True)
        
        # Apply Sprite properties
        sprite.texture = data.get("texture", "")
        sprite.centered = data.get("centered", True)
        sprite.offset = data.get("offset", [0.0, 0.0])
        sprite.flip_h = data.get("flip_h", False)
        sprite.flip_v = data.get("flip_v", False)
        sprite.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
        sprite.region_enabled = data.get("region_enabled", False)
        sprite.region_rect = data.get("region_rect", [0.0, 0.0, 0.0, 0.0])
        sprite.filter = data.get("filter", True)
        sprite.normal_map = data.get("normal_map", "")
        
        # Apply AnimatedSprite properties
        sprite.frames = data.get("frames", 1)
        sprite.hframes = data.get("hframes", 1)
        sprite.vframes = data.get("vframes", 1)
        sprite.frame = data.get("frame", 0)
        sprite.speed_scale = data.get("speed_scale", 1.0)
        sprite.playing = data.get("playing", False)
        sprite._animations = data.get("_animations", {})
        sprite._current_animation = data.get("_current_animation", "")
        sprite._default_animation = data.get("_default_animation", "")
        
        # Load texture if specified
        if sprite.texture:
            sprite._load_texture()
            sprite._update_region_for_frame()
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            sprite.add_child(child)
        
        return sprite
