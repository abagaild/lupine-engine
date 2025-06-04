"""
ProgressBar node implementation for Lupine Engine
Visual progress indicator with customizable appearance
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class ProgressBar(Control):
    """
    Progress bar control for displaying progress values.
    
    Features:
    - Configurable min/max values
    - Step-based or continuous progress
    - Horizontal and vertical orientations
    - Customizable fill and background colors
    - Text display options
    - Animation and easing support
    """
    
    def __init__(self, name: str = "ProgressBar"):
        super().__init__(name)
        self.type = "ProgressBar"
        
        # Export variables for editor
        self.export_variables.update({
            "min_value": {
                "type": "float",
                "value": 0.0,
                "description": "Minimum value"
            },
            "max_value": {
                "type": "int",
                "value": 100,
                "description": "Maximum value"
            },
            "value": {
                "type": "float",
                "value": 0.0,
                "description": "Current value"
            },
            "step": {
                "type": "float",
                "value": 1.0,
                "min": 0.0,
                "description": "Step size (0 for continuous)"
            },
            "percent_visible": {
                "type": "bool",
                "value": True,
                "description": "Show percentage text"
            },
            "fill_mode": {
                "type": "enum",
                "value": "begin_to_end",
                "options": ["begin_to_end", "end_to_begin", "top_to_bottom", "bottom_to_top"],
                "description": "Fill direction"
            }
        })
        
        # Progress properties
        self.min_value: float = 0.0
        self.max_value: float = 100.0
        self.value: float = 0.0
        self.step: float = 1.0
        self.percent_visible: bool = True
        self.fill_mode: str = "begin_to_end"
        
        # Appearance properties
        self.bg_color: List[float] = [0.2, 0.2, 0.2, 1.0]  # Dark gray background
        self.fill_color: List[float] = [0.3, 0.7, 0.3, 1.0]  # Green fill
        self.border_color: List[float] = [0.5, 0.5, 0.5, 1.0]  # Gray border
        self.text_color: List[float] = [1.0, 1.0, 1.0, 1.0]  # White text
        
        self.border_width: float = 1.0
        self.border_radius: float = 2.0
        
        # Text properties
        self.font_size: int = 12
        self.show_percentage: bool = True
        self.custom_text: str = ""
        
        # Animation properties
        self.animated: bool = False
        self.animation_speed: float = 2.0
        self._target_value: float = 0.0
        self._display_value: float = 0.0
        
        # Mouse filter is ignore by default for progress bars
        self.mouse_filter = "ignore"
        
        # Built-in signals
        self.add_signal("value_changed")
        self.add_signal("progress_completed")
    
    def _process(self, delta: float):
        """Process progress bar updates"""
        super()._process(delta)
        
        if self.animated and abs(self._display_value - self._target_value) > 0.01:
            # Animate towards target value
            diff = self._target_value - self._display_value
            move_amount = self.animation_speed * delta * abs(diff)
            
            if diff > 0:
                self._display_value = min(self._target_value, self._display_value + move_amount)
            else:
                self._display_value = max(self._target_value, self._display_value - move_amount)
    
    def set_min(self, min_value: float):
        """Set minimum value"""
        old_min = self.min_value
        self.min_value = min_value
        
        # Ensure max is greater than min
        if self.max_value <= self.min_value:
            self.max_value = self.min_value + 1.0
        
        # Clamp current value
        self.set_value(self.value)
    
    def get_min(self) -> float:
        """Get minimum value"""
        return self.min_value
    
    def set_max(self, max_value: float):
        """Set maximum value"""
        old_max = self.max_value
        self.max_value = max_value
        
        # Ensure min is less than max
        if self.min_value >= self.max_value:
            self.min_value = self.max_value - 1.0
        
        # Clamp current value
        self.set_value(self.value)
    
    def get_max(self) -> float:
        """Get maximum value"""
        return self.max_value
    
    def set_value(self, value: float):
        """Set current value"""
        # Apply step if specified
        if self.step > 0:
            value = round((value - self.min_value) / self.step) * self.step + self.min_value
        
        # Clamp to range
        old_value = self.value
        self.value = max(self.min_value, min(self.max_value, value))
        
        if self.animated:
            self._target_value = self.value
        else:
            self._display_value = self.value
        
        if old_value != self.value:
            self.emit_signal("value_changed", self.value)
            
            # Check if progress is complete
            if self.value >= self.max_value:
                self.emit_signal("progress_completed")
    
    def get_value(self) -> float:
        """Get current value"""
        return self.value
    
    def get_display_value(self) -> float:
        """Get the displayed value (for animation)"""
        return self._display_value if self.animated else self.value
    
    def set_step(self, step: float):
        """Set step size"""
        self.step = max(0.0, step)
    
    def get_step(self) -> float:
        """Get step size"""
        return self.step
    
    def get_as_ratio(self) -> float:
        """Get value as ratio (0.0 to 1.0)"""
        if self.max_value <= self.min_value:
            return 0.0
        
        display_value = self.get_display_value()
        return (display_value - self.min_value) / (self.max_value - self.min_value)
    
    def set_as_ratio(self, ratio: float):
        """Set value as ratio (0.0 to 1.0)"""
        ratio = max(0.0, min(1.0, ratio))
        value = self.min_value + ratio * (self.max_value - self.min_value)
        self.set_value(value)
    
    def get_percentage(self) -> float:
        """Get value as percentage (0.0 to 100.0)"""
        return self.get_as_ratio() * 100.0
    
    def set_percentage(self, percentage: float):
        """Set value as percentage (0.0 to 100.0)"""
        self.set_as_ratio(percentage / 100.0)
    
    def set_fill_mode(self, mode: str):
        """Set fill direction mode"""
        if mode in ["begin_to_end", "end_to_begin", "top_to_bottom", "bottom_to_top"]:
            self.fill_mode = mode
    
    def get_fill_mode(self) -> str:
        """Get fill direction mode"""
        return self.fill_mode
    
    def set_percent_visible(self, visible: bool):
        """Set whether percentage text is visible"""
        self.percent_visible = visible
    
    def is_percent_visible(self) -> bool:
        """Check if percentage text is visible"""
        return self.percent_visible
    
    def set_show_percentage(self, show: bool):
        """Set whether to show percentage"""
        self.show_percentage = show
    
    def is_showing_percentage(self) -> bool:
        """Check if showing percentage"""
        return self.show_percentage
    
    def set_custom_text(self, text: str):
        """Set custom text to display"""
        self.custom_text = text
    
    def get_custom_text(self) -> str:
        """Get custom text"""
        return self.custom_text
    
    def get_display_text(self) -> str:
        """Get the text to display on the progress bar"""
        if self.custom_text:
            return self.custom_text
        elif self.show_percentage and self.percent_visible:
            return f"{self.get_percentage():.1f}%"
        else:
            return f"{self.get_display_value():.1f}"
    
    def set_animated(self, animated: bool):
        """Set whether progress changes are animated"""
        self.animated = animated
        if not animated:
            self._display_value = self.value
    
    def is_animated(self) -> bool:
        """Check if progress changes are animated"""
        return self.animated
    
    def set_animation_speed(self, speed: float):
        """Set animation speed"""
        self.animation_speed = max(0.1, speed)
    
    def get_animation_speed(self) -> float:
        """Get animation speed"""
        return self.animation_speed
    
    def get_fill_rect(self) -> List[float]:
        """Get the rectangle for the filled portion"""
        ratio = self.get_as_ratio()
        rect = self.get_rect()
        
        # Account for border
        fill_x = rect[0] + self.border_width
        fill_y = rect[1] + self.border_width
        fill_width = rect[2] - 2 * self.border_width
        fill_height = rect[3] - 2 * self.border_width
        
        if self.fill_mode == "begin_to_end":
            fill_width *= ratio
        elif self.fill_mode == "end_to_begin":
            fill_width *= ratio
            fill_x += (rect[2] - 2 * self.border_width) * (1.0 - ratio)
        elif self.fill_mode == "top_to_bottom":
            fill_height *= ratio
        elif self.fill_mode == "bottom_to_top":
            fill_height *= ratio
            fill_y += (rect[3] - 2 * self.border_width) * (1.0 - ratio)
        
        return [fill_x, fill_y, max(0, fill_width), max(0, fill_height)]
    
    def increment(self, amount: float = 1.0):
        """Increment the value"""
        self.set_value(self.value + amount)
    
    def decrement(self, amount: float = 1.0):
        """Decrement the value"""
        self.set_value(self.value - amount)
    
    def reset(self):
        """Reset to minimum value"""
        self.set_value(self.min_value)
    
    def complete(self):
        """Set to maximum value"""
        self.set_value(self.max_value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "min_value": self.min_value,
            "max_value": self.max_value,
            "value": self.value,
            "step": self.step,
            "percent_visible": self.percent_visible,
            "fill_mode": self.fill_mode,
            "bg_color": self.bg_color.copy(),
            "fill_color": self.fill_color.copy(),
            "border_color": self.border_color.copy(),
            "text_color": self.text_color.copy(),
            "border_width": self.border_width,
            "border_radius": self.border_radius,
            "font_size": self.font_size,
            "show_percentage": self.show_percentage,
            "custom_text": self.custom_text,
            "animated": self.animated,
            "animation_speed": self.animation_speed
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressBar":
        """Create from dictionary"""
        progress_bar = cls(data.get("name", "ProgressBar"))
        cls._apply_node_properties(progress_bar, data)
        
        # Apply Control properties
        progress_bar.position = data.get("position", [0.0, 0.0])
        progress_bar.size = data.get("size", [200.0, 20.0])
        progress_bar.follow_viewport = data.get("follow_viewport", True)
        progress_bar.mouse_filter = data.get("mouse_filter", "ignore")
        progress_bar.focus_mode = data.get("focus_mode", "none")
        progress_bar.clip_contents = data.get("clip_contents", False)
        progress_bar.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
        
        # Apply ProgressBar properties
        progress_bar.min_value = data.get("min_value", 0.0)
        progress_bar.max_value = data.get("max_value", 100.0)
        progress_bar.value = data.get("value", 0.0)
        progress_bar.step = data.get("step", 1.0)
        progress_bar.percent_visible = data.get("percent_visible", True)
        progress_bar.fill_mode = data.get("fill_mode", "begin_to_end")
        progress_bar.bg_color = data.get("bg_color", [0.2, 0.2, 0.2, 1.0])
        progress_bar.fill_color = data.get("fill_color", [0.3, 0.7, 0.3, 1.0])
        progress_bar.border_color = data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        progress_bar.text_color = data.get("text_color", [1.0, 1.0, 1.0, 1.0])
        progress_bar.border_width = data.get("border_width", 1.0)
        progress_bar.border_radius = data.get("border_radius", 2.0)
        progress_bar.font_size = data.get("font_size", 12)
        progress_bar.show_percentage = data.get("show_percentage", True)
        progress_bar.custom_text = data.get("custom_text", "")
        progress_bar.animated = data.get("animated", False)
        progress_bar.animation_speed = data.get("animation_speed", 2.0)
        
        # Initialize display value
        progress_bar._display_value = progress_bar.value
        progress_bar._target_value = progress_bar.value
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            progress_bar.add_child(child)
        
        return progress_bar
    
    def __str__(self) -> str:
        """String representation of the progress bar"""
        return f"ProgressBar({self.name}, value={self.value:.1f}/{self.max_value:.1f}, {self.get_percentage():.1f}%)"
