"""
Animation player utilities for Lupine Engine
Provides helper functions and utilities for animation playback
"""

from typing import Dict, Any, List, Optional, Union
from .animation import Animation, AnimationLibrary
from .animation_track import AnimationTrack, PropertyTrack, TransformTrack, ColorTrack, SpriteFrameTrack


def create_simple_tween_animation(name: str, target_path: str, property_name: str, 
                                start_value: Any, end_value: Any, duration: float = 1.0,
                                loop: bool = False) -> Animation:
    """
    Create a simple tween animation between two values
    
    Args:
        name: Animation name
        target_path: Path to target node (e.g., "Player/Sprite")
        property_name: Property to animate (e.g., "position")
        start_value: Starting value
        end_value: Ending value
        duration: Animation duration in seconds
        loop: Whether to loop the animation
        
    Returns:
        Animation object
    """
    animation = Animation(name)
    animation.length = duration
    animation.loop = loop
    
    # Create appropriate track type
    if property_name in ["position", "rotation", "scale"]:
        track = TransformTrack(target_path, property_name)
    elif property_name in ["modulate", "color"]:
        track = ColorTrack(target_path, property_name)
    elif property_name == "frame":
        track = SpriteFrameTrack(target_path)
    else:
        track = PropertyTrack(target_path, property_name)
    
    # Add keyframes
    track.add_keyframe(0.0, start_value)
    track.add_keyframe(duration, end_value)
    
    animation.add_track(track)
    return animation


def create_fade_animation(name: str, target_path: str, fade_in: bool = True, 
                         duration: float = 1.0) -> Animation:
    """
    Create a fade in/out animation
    
    Args:
        name: Animation name
        target_path: Path to target node
        fade_in: True for fade in, False for fade out
        duration: Animation duration
        
    Returns:
        Animation object
    """
    start_alpha = 0.0 if fade_in else 1.0
    end_alpha = 1.0 if fade_in else 0.0
    
    return create_simple_tween_animation(
        name, target_path, "modulate", 
        [1.0, 1.0, 1.0, start_alpha], 
        [1.0, 1.0, 1.0, end_alpha], 
        duration
    )


def create_move_animation(name: str, target_path: str, start_pos: List[float], 
                         end_pos: List[float], duration: float = 1.0) -> Animation:
    """
    Create a movement animation
    
    Args:
        name: Animation name
        target_path: Path to target node
        start_pos: Starting position [x, y]
        end_pos: Ending position [x, y]
        duration: Animation duration
        
    Returns:
        Animation object
    """
    return create_simple_tween_animation(
        name, target_path, "position", start_pos, end_pos, duration
    )


def create_scale_animation(name: str, target_path: str, start_scale: List[float], 
                          end_scale: List[float], duration: float = 1.0) -> Animation:
    """
    Create a scale animation
    
    Args:
        name: Animation name
        target_path: Path to target node
        start_scale: Starting scale [x, y]
        end_scale: Ending scale [x, y]
        duration: Animation duration
        
    Returns:
        Animation object
    """
    return create_simple_tween_animation(
        name, target_path, "scale", start_scale, end_scale, duration
    )


def create_rotation_animation(name: str, target_path: str, start_rotation: float, 
                             end_rotation: float, duration: float = 1.0) -> Animation:
    """
    Create a rotation animation
    
    Args:
        name: Animation name
        target_path: Path to target node
        start_rotation: Starting rotation in degrees
        end_rotation: Ending rotation in degrees
        duration: Animation duration
        
    Returns:
        Animation object
    """
    return create_simple_tween_animation(
        name, target_path, "rotation", start_rotation, end_rotation, duration
    )


def create_sprite_frame_animation(name: str, target_path: str, frames: List[int], 
                                 fps: float = 10.0, loop: bool = True) -> Animation:
    """
    Create a sprite frame animation
    
    Args:
        name: Animation name
        target_path: Path to sprite node
        frames: List of frame indices
        fps: Frames per second
        loop: Whether to loop the animation
        
    Returns:
        Animation object
    """
    if not frames:
        raise ValueError("Frame list cannot be empty")
    
    duration = len(frames) / fps
    animation = Animation(name)
    animation.length = duration
    animation.loop = loop
    
    track = SpriteFrameTrack(target_path)
    
    # Add keyframes for each frame
    for i, frame in enumerate(frames):
        time = i / fps
        track.add_keyframe(time, frame)
    
    animation.add_track(track)
    return animation


def create_bounce_animation(name: str, target_path: str, property_name: str = "scale",
                           bounce_scale: float = 1.2, duration: float = 0.5) -> Animation:
    """
    Create a bounce animation (useful for UI feedback)
    
    Args:
        name: Animation name
        target_path: Path to target node
        property_name: Property to animate (usually "scale")
        bounce_scale: Maximum scale during bounce
        duration: Total animation duration
        
    Returns:
        Animation object
    """
    animation = Animation(name)
    animation.length = duration
    animation.loop = False
    
    track = PropertyTrack(target_path, property_name)
    
    # Bounce keyframes
    track.add_keyframe(0.0, [1.0, 1.0])
    track.add_keyframe(duration * 0.3, [bounce_scale, bounce_scale])
    track.add_keyframe(duration * 0.6, [0.9, 0.9])
    track.add_keyframe(duration, [1.0, 1.0])
    
    animation.add_track(track)
    return animation


def create_pulse_animation(name: str, target_path: str, min_alpha: float = 0.3,
                          max_alpha: float = 1.0, duration: float = 1.0) -> Animation:
    """
    Create a pulsing alpha animation
    
    Args:
        name: Animation name
        target_path: Path to target node
        min_alpha: Minimum alpha value
        max_alpha: Maximum alpha value
        duration: Animation duration
        
    Returns:
        Animation object
    """
    animation = Animation(name)
    animation.length = duration
    animation.loop = True
    
    track = ColorTrack(target_path, "modulate")
    
    # Pulse keyframes
    track.add_keyframe(0.0, [1.0, 1.0, 1.0, max_alpha])
    track.add_keyframe(duration * 0.5, [1.0, 1.0, 1.0, min_alpha])
    track.add_keyframe(duration, [1.0, 1.0, 1.0, max_alpha])
    
    animation.add_track(track)
    return animation


# Preset animation library for common UI animations
PRESET_ANIMATIONS = {
    "bounce": lambda target: create_bounce_animation("bounce", target),
    "fade_in": lambda target: create_fade_animation("fade_in", target, True),
    "fade_out": lambda target: create_fade_animation("fade_out", target, False),
    "pulse": lambda target: create_pulse_animation("pulse", target),
    "scale_up": lambda target: create_scale_animation("scale_up", target, [1.0, 1.0], [1.2, 1.2]),
    "scale_down": lambda target: create_scale_animation("scale_down", target, [1.0, 1.0], [0.8, 0.8]),
}


def get_preset_animation(preset_name: str, target_path: str) -> Optional[Animation]:
    """
    Get a preset animation for a target
    
    Args:
        preset_name: Name of preset animation
        target_path: Path to target node
        
    Returns:
        Animation object or None if preset not found
    """
    if preset_name in PRESET_ANIMATIONS:
        return PRESET_ANIMATIONS[preset_name](target_path)
    return None


def get_preset_animation_names() -> List[str]:
    """Get list of available preset animation names"""
    return list(PRESET_ANIMATIONS.keys())
