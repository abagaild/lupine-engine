"""
Tween and interpolation utilities for Lupine Engine animation system
"""

import math
from enum import Enum
from typing import Any, Union, List


class TweenType(Enum):
    """Types of tween interpolation"""
    LINEAR = "linear"
    SMOOTH = "smooth"
    SMOOTHER = "smoother"
    BEZIER = "bezier"
    SPRING = "spring"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


class EaseType(Enum):
    """Easing types for tweens"""
    LINEAR = "linear"
    IN = "in"
    OUT = "out"
    IN_OUT = "in_out"
    OUT_IN = "out_in"


class Tween:
    """
    Tween utility class for interpolating between values
    Supports various interpolation types and easing functions
    """
    
    @staticmethod
    def interpolate(start: Any, end: Any, progress: float, tween_type: TweenType = TweenType.LINEAR, 
                   ease_type: EaseType = EaseType.IN_OUT) -> Any:
        """
        Interpolate between start and end values with given progress (0.0 to 1.0)
        
        Args:
            start: Starting value
            end: Ending value  
            progress: Progress from 0.0 to 1.0
            tween_type: Type of interpolation curve
            ease_type: Easing function to apply
            
        Returns:
            Interpolated value
        """
        # Clamp progress
        progress = max(0.0, min(1.0, progress))
        
        # Apply easing
        eased_progress = Tween._apply_easing(progress, ease_type, tween_type)
        
        # Apply tween curve
        curved_progress = Tween._apply_tween_curve(eased_progress, tween_type)
        
        # Interpolate based on value type
        return Tween._lerp_value(start, end, curved_progress)
    
    @staticmethod
    def _apply_easing(progress: float, ease_type: EaseType, tween_type: TweenType) -> float:
        """Apply easing function to progress"""
        if ease_type == EaseType.LINEAR or tween_type == TweenType.LINEAR:
            return progress
        elif ease_type == EaseType.IN:
            return progress * progress
        elif ease_type == EaseType.OUT:
            return 1.0 - (1.0 - progress) * (1.0 - progress)
        elif ease_type == EaseType.IN_OUT:
            if progress < 0.5:
                return 2.0 * progress * progress
            else:
                return 1.0 - 2.0 * (1.0 - progress) * (1.0 - progress)
        elif ease_type == EaseType.OUT_IN:
            if progress < 0.5:
                return 0.5 * (1.0 - (1.0 - 2.0 * progress) * (1.0 - 2.0 * progress))
            else:
                return 0.5 + 0.5 * (2.0 * progress - 1.0) * (2.0 * progress - 1.0)

        return progress
    
    @staticmethod
    def _apply_tween_curve(progress: float, tween_type: TweenType) -> float:
        """Apply tween curve to progress"""
        if tween_type == TweenType.LINEAR:
            return progress
        elif tween_type == TweenType.SMOOTH:
            return progress * progress * (3.0 - 2.0 * progress)
        elif tween_type == TweenType.SMOOTHER:
            return progress * progress * progress * (progress * (progress * 6.0 - 15.0) + 10.0)
        elif tween_type == TweenType.SPRING:
            return 1.0 - math.cos(progress * math.pi * 0.5)
        elif tween_type == TweenType.BOUNCE:
            if progress < 1.0 / 2.75:
                return 7.5625 * progress * progress
            elif progress < 2.0 / 2.75:
                progress -= 1.5 / 2.75
                return 7.5625 * progress * progress + 0.75
            elif progress < 2.5 / 2.75:
                progress -= 2.25 / 2.75
                return 7.5625 * progress * progress + 0.9375
            else:
                progress -= 2.625 / 2.75
                return 7.5625 * progress * progress + 0.984375
        elif tween_type == TweenType.ELASTIC:
            if progress == 0.0 or progress == 1.0:
                return progress
            return -(2.0 ** (10.0 * (progress - 1.0))) * math.sin((progress - 1.1) * 5.0 * math.pi)
        
        return progress
    
    @staticmethod
    def _lerp_value(start: Any, end: Any, progress: float) -> Any:
        """Interpolate between values based on their type"""
        # Handle numeric types
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            return start + (end - start) * progress
        
        # Handle lists/tuples (vectors, colors, etc.)
        if isinstance(start, (list, tuple)) and isinstance(end, (list, tuple)):
            if len(start) != len(end):
                raise ValueError("Cannot interpolate between sequences of different lengths")
            
            result = []
            for i in range(len(start)):
                result.append(Tween._lerp_value(start[i], end[i], progress))
            
            return type(start)(result)
        
        # Handle dictionaries (for complex properties)
        if isinstance(start, dict) and isinstance(end, dict):
            result = {}
            for key in start:
                if key in end:
                    result[key] = Tween._lerp_value(start[key], end[key], progress)
                else:
                    result[key] = start[key]
            return result
        
        # Handle strings (for discrete values)
        if isinstance(start, str) and isinstance(end, str):
            return start if progress < 0.5 else end
        
        # Handle booleans (discrete)
        if isinstance(start, bool) and isinstance(end, bool):
            return start if progress < 0.5 else end
        
        # Default: return start or end based on progress
        return start if progress < 0.5 else end


def lerp(start: float, end: float, progress: float) -> float:
    """Simple linear interpolation function"""
    return start + (end - start) * progress


def lerp_color(start: List[float], end: List[float], progress: float) -> List[float]:
    """Linear interpolation for RGBA color values"""
    if len(start) != len(end):
        raise ValueError("Color arrays must have same length")
    
    result = []
    for i in range(len(start)):
        result.append(lerp(start[i], end[i], progress))
    
    return result


def lerp_vector(start: List[float], end: List[float], progress: float) -> List[float]:
    """Linear interpolation for vector values"""
    if len(start) != len(end):
        raise ValueError("Vector arrays must have same length")
    
    result = []
    for i in range(len(start)):
        result.append(lerp(start[i], end[i], progress))
    
    return result


def smooth_step(edge0: float, edge1: float, x: float) -> float:
    """Smooth step function for smooth transitions"""
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def smoother_step(edge0: float, edge1: float, x: float) -> float:
    """Smoother step function for very smooth transitions"""
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
