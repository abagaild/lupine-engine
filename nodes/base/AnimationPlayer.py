"""
AnimationPlayer node implementation for Lupine Engine
Node for playing and managing animations on other nodes
"""

from typing import Dict, Any, List, Optional
import os
import json
from pathlib import Path

from .Node import Node
from core.animation import Animation, AnimationLibrary


class AnimationPlayer(Node):
    """
    AnimationPlayer node for playing animations on other nodes.
    
    Features:
    - Multiple animation management
    - Animation playback control
    - Autoplay support
    - Animation blending and transitions
    - Save/load animation data
    - Integration with scene tree
    """
    
    def __init__(self, name: str = "AnimationPlayer"):
        super().__init__(name)
        self.type = "AnimationPlayer"
        
        # Animation library
        self.animation_library = AnimationLibrary()
        
        # Playback state
        self.current_animation: Optional[Animation] = None
        self.autoplay_animation: str = ""
        self.playback_speed: float = 1.0
        
        # Animation file path (relative to project)
        self.animation_file: str = ""
        
        # Signals
        self.add_signal("animation_finished")
        self.add_signal("animation_changed") 
        self.add_signal("animation_started")
        
        # Export variables for editor
        self.export_variables.update({
            "autoplay_animation": {
                "type": "string",
                "value": "",
                "description": "Animation to play automatically when scene starts"
            },
            "playback_speed": {
                "type": "number",
                "value": 1.0,
                "min": 0.1,
                "max": 5.0,
                "description": "Global playback speed multiplier"
            },
            "animation_file": {
                "type": "path",
                "value": "",
                "description": "Path to animation file (.anim)"
            }
        })
    
    def _ready(self):
        """Called when node enters scene tree"""
        super()._ready()
        
        # Load animation file if specified
        if self.animation_file:
            self.load_animation_file(self.animation_file)
        
        # Start autoplay animation
        if self.autoplay_animation and self.has_animation(self.autoplay_animation):
            self.play(self.autoplay_animation)
    
    def _process(self, delta: float):
        """Update animation playback"""
        super()._process(delta)
        
        if self.current_animation and self.current_animation.is_playing:
            # Update animation with scaled delta time
            self.current_animation.update(delta * self.playback_speed)
            
            # Apply animation to scene
            scene_root = self.get_scene_root()
            if scene_root:
                self.current_animation.apply_to_scene(scene_root)
    
    def get_scene_root(self):
        """Get the root node of the current scene"""
        current = self
        while current.parent:
            current = current.parent
        return current
    
    # Animation Management
    def add_animation(self, animation: Animation):
        """Add an animation to the library"""
        self.animation_library.add_animation(animation)
        
        # Set up animation callbacks
        animation.on_animation_finished = lambda: self._on_animation_finished(animation.name)
        animation.on_animation_looped = lambda: self._on_animation_looped(animation.name)
    
    def remove_animation(self, name: str) -> bool:
        """Remove an animation from the library"""
        if self.current_animation and self.current_animation.name == name:
            self.stop()
        
        return self.animation_library.remove_animation(name)
    
    def has_animation(self, name: str) -> bool:
        """Check if animation exists"""
        return self.animation_library.has_animation(name)
    
    def get_animation(self, name: str) -> Optional[Animation]:
        """Get animation by name"""
        return self.animation_library.get_animation(name)
    
    def get_animation_names(self) -> List[str]:
        """Get list of all animation names"""
        return self.animation_library.get_animation_names()
    
    # Playback Control
    def play(self, name: str = "", from_position: float = 0.0):
        """Play an animation"""
        if not name:
            name = self.animation_library.default_animation or ""

        if not name:
            return
        
        animation = self.animation_library.get_animation(name)
        if not animation:
            return
        
        # Stop current animation
        if self.current_animation:
            self.current_animation.stop()
        
        # Start new animation
        self.current_animation = animation
        self.current_animation.speed_scale = self.playback_speed
        self.current_animation.play(from_position)
        
        self.emit_signal("animation_started", name)
        self.emit_signal("animation_changed", name)
    
    def stop(self):
        """Stop current animation"""
        if self.current_animation:
            self.current_animation.stop()
            self.current_animation = None
    
    def pause(self):
        """Pause current animation"""
        if self.current_animation:
            self.current_animation.pause()
    
    def resume(self):
        """Resume current animation"""
        if self.current_animation:
            self.current_animation.resume()
    
    def seek(self, position: float):
        """Seek to position in current animation"""
        if self.current_animation:
            self.current_animation.seek(position)
    
    def is_playing(self) -> bool:
        """Check if an animation is currently playing"""
        return self.current_animation is not None and self.current_animation.is_playing
    
    def get_current_animation_name(self) -> str:
        """Get name of currently playing animation"""
        return self.current_animation.name if self.current_animation else ""
    
    def get_current_animation_position(self) -> float:
        """Get current position in animation"""
        return self.current_animation.current_time if self.current_animation else 0.0
    
    def get_current_animation_length(self) -> float:
        """Get length of current animation"""
        return self.current_animation.length if self.current_animation else 0.0
    
    # File Operations
    def save_animation_file(self, file_path: str):
        """Save animations to file"""
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save animation library
            data = self.animation_library.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.animation_file = file_path
            
        except Exception as e:
            print(f"Error saving animation file: {e}")
    
    def load_animation_file(self, file_path: str):
        """Load animations from file"""
        try:
            if not os.path.exists(file_path):
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load animation library
            self.animation_library = AnimationLibrary.from_dict(data)
            
            # Set up callbacks for all animations
            for animation in self.animation_library.animations.values():
                animation.on_animation_finished = lambda name=animation.name: self._on_animation_finished(name)
                animation.on_animation_looped = lambda name=animation.name: self._on_animation_looped(name)
            
            self.animation_file = file_path
            
        except Exception as e:
            print(f"Error loading animation file: {e}")
    
    # Event Handlers
    def _on_animation_finished(self, animation_name: str):
        """Called when an animation finishes"""
        self.emit_signal("animation_finished", animation_name)
    
    def _on_animation_looped(self, animation_name: str):
        """Called when an animation loops"""
        # Could emit a loop signal if needed
        pass
    
    # Serialization
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for scene saving"""
        data = super().to_dict()
        
        # Add AnimationPlayer specific data
        data.update({
            "autoplay_animation": self.autoplay_animation,
            "playback_speed": self.playback_speed,
            "animation_file": self.animation_file,
            "animation_library": self.animation_library.to_dict()
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationPlayer":
        """Create from dictionary"""
        node = cls(data.get("name", "AnimationPlayer"))

        # Apply base node properties
        cls._apply_node_properties(node, data)

        # Load AnimationPlayer specific data
        node.autoplay_animation = data.get("autoplay_animation", "")
        node.playback_speed = data.get("playback_speed", 1.0)
        node.animation_file = data.get("animation_file", "")
        
        # Load animation library
        if "animation_library" in data:
            node.animation_library = AnimationLibrary.from_dict(data["animation_library"])
            
            # Set up callbacks
            for animation in node.animation_library.animations.values():
                animation.on_animation_finished = lambda name=animation.name: node._on_animation_finished(name)
                animation.on_animation_looped = lambda name=animation.name: node._on_animation_looped(name)
        
        return node
