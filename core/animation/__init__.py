"""
Animation system for Lupine Engine
Provides comprehensive animation support for properties, sprites, and UI elements
"""

from .animation import Animation, AnimationLibrary
from .animation_track import (
    AnimationTrack, PropertyTrack, SpriteFrameTrack,
    TransformTrack, ColorTrack, AudioTrack
)
from .tween import Tween, TweenType, EaseType
from .animation_player import (
    create_simple_tween_animation, create_fade_animation, create_move_animation,
    create_scale_animation, create_rotation_animation, create_sprite_frame_animation,
    create_bounce_animation, create_pulse_animation, get_preset_animation,
    get_preset_animation_names
)

__all__ = [
    'Animation',
    'AnimationLibrary',
    'AnimationTrack',
    'PropertyTrack',
    'SpriteFrameTrack',
    'TransformTrack',
    'ColorTrack',
    'AudioTrack',
    'Tween',
    'TweenType',
    'EaseType',
    'create_simple_tween_animation',
    'create_fade_animation',
    'create_move_animation',
    'create_scale_animation',
    'create_rotation_animation',
    'create_sprite_frame_animation',
    'create_bounce_animation',
    'create_pulse_animation',
    'get_preset_animation',
    'get_preset_animation_names'
]
