"""
Control node implementation for Lupine Engine
Base class for all UI elements with simplified positioning
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional
import math


class Control(Node2D):
    """
    Base class for all UI controls with simplified positioning.

    Features:
    - Standard position-based positioning (inherits from Node2D)
    - Size property for UI elements
    - Follow viewport option for screen-space positioning
    - Mouse input handling
    - Focus management
    - Theme and styling support
    """
    
    def __init__(self, name: str = "Control"):
        super().__init__(name)
        self.type = "Control"
        
        # Export variables for editor
        self.export_variables.update({
            "size": {
                "type": "vector2",
                "value": [100.0, 100.0],
                "min": 0.0,
                "description": "Size of the control in pixels"
            },
            "follow_viewport": {
                "type": "bool",
                "value": True,
                "description": "If true, position is relative to viewport; if false, position is in world space"
            },
            "mouse_filter": {
                "type": "enum",
                "value": "pass",
                "options": ["stop", "pass", "ignore"],
                "description": "How this control handles mouse events"
            },
            "focus_mode": {
                "type": "enum",
                "value": "none",
                "options": ["none", "click", "all"],
                "description": "How this control can receive focus"
            },
            "clip_contents": {
                "type": "bool",
                "value": False,
                "description": "If true, clip child controls to this control's bounds"
            },
            "modulate": {
                "type": "color",
                "value": [1.0, 1.0, 1.0, 1.0],
                "description": "Color modulation (RGBA)"
            }
        })
        
        # Control properties
        self.size: List[float] = [100.0, 100.0]  # Size in pixels
        self.follow_viewport: bool = True  # If true, position is viewport-relative
        self.clip_contents: bool = False  # Clip child controls to bounds
        self.modulate: List[float] = [1.0, 1.0, 1.0, 1.0]  # Color modulation

        # Input properties
        self.mouse_filter: str = "pass"  # stop, pass, ignore
        self.focus_mode: str = "none"  # none, click, all

        # State
        self._has_focus: bool = False
        self._mouse_inside: bool = False
        self._pressed: bool = False
        
        # Built-in signals
        self.add_signal("gui_input")
        self.add_signal("mouse_entered")
        self.add_signal("mouse_exited")
        self.add_signal("focus_entered")
        self.add_signal("focus_exited")
        self.add_signal("resized")
    
    def _ready(self):
        """Called when control enters the scene tree"""
        super()._ready()

    def set_size(self, width: float, height: float):
        """Set the size of the control"""
        old_size = self.size.copy()
        self.size = [max(0.0, width), max(0.0, height)]

        if old_size != self.size:
            self.emit_signal("resized")

    def get_size(self) -> List[float]:
        """Get the size of the control"""
        return self.size.copy()

    def get_rect(self) -> List[float]:
        """Get the rectangle as [x, y, width, height]"""
        return self.position + self.size

    def get_global_rect(self) -> List[float]:
        """Get the global rectangle"""
        # Simplified - always use global position
        global_pos = self.get_global_position()
        return global_pos + self.size
    
    def set_follow_viewport(self, follow: bool):
        """Set whether this control follows the viewport"""
        self.follow_viewport = follow

    def is_following_viewport(self) -> bool:
        """Check if this control follows the viewport"""
        return self.follow_viewport
    
    def set_mouse_filter(self, filter_mode: str):
        """Set the mouse filter mode"""
        if filter_mode in ["stop", "pass", "ignore"]:
            self.mouse_filter = filter_mode
    
    def get_mouse_filter(self) -> str:
        """Get the mouse filter mode"""
        return self.mouse_filter
    
    def set_focus_mode(self, mode: str):
        """Set the focus mode"""
        if mode in ["none", "click", "all"]:
            self.focus_mode = mode
    
    def get_focus_mode(self) -> str:
        """Get the focus mode"""
        return self.focus_mode
    
    def grab_focus(self):
        """Grab keyboard focus"""
        if self.focus_mode != "none":
            # In a full implementation, this would notify the scene tree
            self._has_focus = True
            self.emit_signal("focus_entered")
    
    def release_focus(self):
        """Release keyboard focus"""
        if self._has_focus:
            self._has_focus = False
            self.emit_signal("focus_exited")
    
    def has_focus(self) -> bool:
        """Check if this control has focus"""
        return self._has_focus
    
    def is_mouse_inside(self) -> bool:
        """Check if mouse is inside this control"""
        return self._mouse_inside
    
    def _handle_mouse_enter(self):
        """Handle mouse entering the control"""
        if not self._mouse_inside:
            self._mouse_inside = True
            self.emit_signal("mouse_entered")
    
    def _handle_mouse_exit(self):
        """Handle mouse exiting the control"""
        if self._mouse_inside:
            self._mouse_inside = False
            self.emit_signal("mouse_exited")
    
    def _handle_input_event(self, event: Dict[str, Any]):
        """Handle input events"""
        self.emit_signal("gui_input", event)
        
        # Handle focus on click
        if (event.get("type") == "mouse_button" and 
            event.get("pressed") and 
            self.focus_mode in ["click", "all"]):
            self.grab_focus()
    
    def contains_point(self, point: List[float]) -> bool:
        """Check if a point is inside this control"""
        rect = self.get_rect()
        return (rect[0] <= point[0] <= rect[0] + rect[2] and
                rect[1] <= point[1] <= rect[1] + rect[3])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "size": self.size.copy(),
            "follow_viewport": self.follow_viewport,
            "mouse_filter": self.mouse_filter,
            "focus_mode": self.focus_mode
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Control":
        """Create from dictionary"""
        control = cls(data.get("name", "Control"))
        cls._apply_node_properties(control, data)

        # Apply Node2D properties (Control inherits from Node2D)
        control.position = data.get("position", [0.0, 0.0])
        control.rotation = data.get("rotation", 0.0)
        control.scale = data.get("scale", [1.0, 1.0])
        control.z_index = data.get("z_index", 0)
        control.z_as_relative = data.get("z_as_relative", True)

        # Apply Control properties
        control.size = data.get("size", [100.0, 100.0])
        control.follow_viewport = data.get("follow_viewport", True)
        control.mouse_filter = data.get("mouse_filter", "pass")
        control.focus_mode = data.get("focus_mode", "none")

        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            control.add_child(child)

        return control

    def __str__(self) -> str:
        """String representation of the control"""
        return f"Control({self.name}, rect={self.get_rect()})"
