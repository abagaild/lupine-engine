"""
CheckBox node implementation for Lupine Engine
Checkbox control with text label and toggle functionality
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class CheckBox(Control):
    """
    Checkbox control with text label and toggle functionality.
    
    Features:
    - Toggle state (checked/unchecked)
    - Text label with alignment
    - Custom checkbox size and styling
    - Keyboard support (Space to toggle)
    - Visual states (normal, hover, pressed, disabled)
    - Custom check mark styling
    - Group functionality for radio-like behavior
    """
    
    def __init__(self, name: str = "CheckBox"):
        super().__init__(name)
        self.type = "CheckBox"
        
        # State properties
        self.button_pressed = False  # Current checked state
        self.disabled = False
        
        # Text properties
        self.text = "CheckBox"
        self.font_path = None
        self.font_size = 14
        self.text_color = [0.9, 0.9, 0.9, 1.0]  # Light gray
        self.text_color_disabled = [0.5, 0.5, 0.5, 1.0]  # Darker gray when disabled
        
        # Checkbox styling
        self.checkbox_size = 16.0  # Size of the checkbox square
        self.checkbox_offset = 4.0  # Space between checkbox and text
        
        # Checkbox colors
        self.checkbox_bg_color = [0.2, 0.2, 0.2, 1.0]  # Dark background
        self.checkbox_bg_color_hover = [0.3, 0.3, 0.3, 1.0]  # Lighter when hovered
        self.checkbox_bg_color_pressed = [0.1, 0.1, 0.1, 1.0]  # Darker when pressed
        self.checkbox_bg_color_disabled = [0.15, 0.15, 0.15, 1.0]  # Disabled background
        
        self.checkbox_border_color = [0.5, 0.5, 0.5, 1.0]  # Gray border
        self.checkbox_border_color_hover = [0.7, 0.7, 0.7, 1.0]  # Lighter border on hover
        self.checkbox_border_color_focus = [0.3, 0.6, 1.0, 1.0]  # Blue when focused
        self.checkbox_border_width = 1.0
        
        # Check mark styling
        self.check_color = [0.2, 0.8, 0.2, 1.0]  # Green check mark
        self.check_color_disabled = [0.3, 0.5, 0.3, 1.0]  # Darker green when disabled
        self.check_style = "checkmark"  # checkmark, cross, dot, custom
        
        # Layout
        self.text_align = "left"  # left, right (checkbox position relative to text)
        
        # Group functionality (for radio-like behavior)
        self.button_group = None  # Group name for exclusive selection
        
        # Visual state
        self._is_hovered = False
        self._is_pressed = False
        
        # Built-in signals
        self.add_signal("toggled")  # Emitted when state changes
        self.add_signal("pressed")  # Emitted when clicked (regardless of state change)
    
    def _ready(self):
        """Called when checkbox enters the scene tree"""
        super()._ready()
        
        # Connect mouse signals
        self.connect("mouse_entered", self, "_on_mouse_entered")
        self.connect("mouse_exited", self, "_on_mouse_exited")
        self.connect("gui_input", self, "_on_gui_input")
    
    def _on_mouse_entered(self):
        """Handle mouse entering the checkbox"""
        if not self.disabled:
            self._is_hovered = True
    
    def _on_mouse_exited(self):
        """Handle mouse leaving the checkbox"""
        self._is_hovered = False
        self._is_pressed = False
    
    def _on_gui_input(self, event: Dict[str, Any]):
        """Handle input events"""
        if self.disabled:
            return
        
        event_type = event.get("type", "")
        
        if event_type == "mouse_button":
            button = event.get("button", 1)  # 1 = left mouse button
            pressed = event.get("pressed", False)
            
            if button == 1:  # Left mouse button
                if pressed:
                    self._is_pressed = True
                    self.grab_focus()
                else:
                    if self._is_pressed and self._is_hovered:
                        self.toggle()
                    self._is_pressed = False
        
        elif event_type == "key":
            key = event.get("key", "")
            pressed = event.get("pressed", False)
            
            # Handle Space key to toggle
            if key == "space" and pressed:
                self.toggle()
    
    def toggle(self):
        """Toggle the checkbox state"""
        if self.disabled:
            return
        
        # Handle group exclusivity
        if self.button_group and not self.button_pressed:
            # Uncheck other checkboxes in the same group
            self._uncheck_group_siblings()
        
        old_state = self.button_pressed
        self.button_pressed = not self.button_pressed
        
        self.emit_signal("pressed")
        
        if old_state != self.button_pressed:
            self.emit_signal("toggled", self.button_pressed)
    
    def set_pressed(self, pressed: bool):
        """Set the pressed state directly"""
        if self.disabled:
            return
        
        old_state = self.button_pressed
        
        # Handle group exclusivity
        if self.button_group and pressed and not self.button_pressed:
            self._uncheck_group_siblings()
        
        self.button_pressed = pressed
        
        if old_state != self.button_pressed:
            self.emit_signal("toggled", self.button_pressed)
    
    def is_pressed(self) -> bool:
        """Get the pressed state"""
        return self.button_pressed
    
    def set_disabled(self, disabled: bool):
        """Set the disabled state"""
        self.disabled = disabled
        if disabled:
            self._is_hovered = False
            self._is_pressed = False
    
    def is_disabled(self) -> bool:
        """Get the disabled state"""
        return self.disabled
    
    def set_text(self, text: str):
        """Set the checkbox text"""
        self.text = text
    
    def get_text(self) -> str:
        """Get the checkbox text"""
        return self.text
    
    def set_button_group(self, group: Optional[str]):
        """Set the button group for radio-like behavior"""
        self.button_group = group
    
    def get_button_group(self) -> Optional[str]:
        """Get the button group"""
        return self.button_group
    
    def _uncheck_group_siblings(self):
        """Uncheck other checkboxes in the same group"""
        if not self.button_group or not self.parent:
            return
        
        # Find siblings with the same group
        def find_group_siblings(node):
            siblings = []
            if hasattr(node, 'children'):
                for child in node.children:
                    if (hasattr(child, 'button_group') and 
                        child.button_group == self.button_group and 
                        child != self):
                        siblings.append(child)
                    siblings.extend(find_group_siblings(child))
            return siblings
        
        # Start search from root to find all group members
        root = self
        while root.parent:
            root = root.parent
        
        siblings = find_group_siblings(root)
        for sibling in siblings:
            if hasattr(sibling, 'set_pressed'):
                sibling.set_pressed(False)
    
    def get_checkbox_rect(self) -> List[float]:
        """Get the checkbox rectangle [x, y, width, height] relative to control"""
        if self.text_align == "right":
            # Checkbox on the right side
            checkbox_x = self.size[0] - self.checkbox_size
        else:
            # Checkbox on the left side
            checkbox_x = 0
        
        checkbox_y = (self.size[1] - self.checkbox_size) / 2
        return [checkbox_x, checkbox_y, self.checkbox_size, self.checkbox_size]
    
    def get_text_rect(self) -> List[float]:
        """Get the text rectangle [x, y, width, height] relative to control"""
        checkbox_rect = self.get_checkbox_rect()
        
        if self.text_align == "right":
            # Text on the left, checkbox on the right
            text_x = 0
            text_width = checkbox_rect[0] - self.checkbox_offset
        else:
            # Text on the right, checkbox on the left
            text_x = checkbox_rect[0] + checkbox_rect[2] + self.checkbox_offset
            text_width = self.size[0] - text_x
        
        text_y = 0
        text_height = self.size[1]
        
        return [text_x, text_y, text_width, text_height]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        
        # Add CheckBox-specific properties
        data.update({
            "button_pressed": self.button_pressed,
            "disabled": self.disabled,
            "text": self.text,
            "font_path": self.font_path,
            "font_size": self.font_size,
            "text_color": self.text_color,
            "text_color_disabled": self.text_color_disabled,
            "checkbox_size": self.checkbox_size,
            "checkbox_offset": self.checkbox_offset,
            "checkbox_bg_color": self.checkbox_bg_color,
            "checkbox_bg_color_hover": self.checkbox_bg_color_hover,
            "checkbox_bg_color_pressed": self.checkbox_bg_color_pressed,
            "checkbox_bg_color_disabled": self.checkbox_bg_color_disabled,
            "checkbox_border_color": self.checkbox_border_color,
            "checkbox_border_color_hover": self.checkbox_border_color_hover,
            "checkbox_border_color_focus": self.checkbox_border_color_focus,
            "checkbox_border_width": self.checkbox_border_width,
            "check_color": self.check_color,
            "check_color_disabled": self.check_color_disabled,
            "check_style": self.check_style,
            "text_align": self.text_align,
            "button_group": self.button_group,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckBox":
        """Create from dictionary"""
        checkbox = cls(data.get("name", "CheckBox"))
        cls._apply_node_properties(checkbox, data)
        
        # Apply CheckBox properties
        checkbox.button_pressed = data.get("button_pressed", False)
        checkbox.disabled = data.get("disabled", False)
        checkbox.text = data.get("text", "CheckBox")
        checkbox.font_path = data.get("font_path", None)
        checkbox.font_size = data.get("font_size", 14)
        checkbox.text_color = data.get("text_color", [0.9, 0.9, 0.9, 1.0])
        checkbox.text_color_disabled = data.get("text_color_disabled", [0.5, 0.5, 0.5, 1.0])
        checkbox.checkbox_size = data.get("checkbox_size", 16.0)
        checkbox.checkbox_offset = data.get("checkbox_offset", 4.0)
        checkbox.checkbox_bg_color = data.get("checkbox_bg_color", [0.2, 0.2, 0.2, 1.0])
        checkbox.checkbox_bg_color_hover = data.get("checkbox_bg_color_hover", [0.3, 0.3, 0.3, 1.0])
        checkbox.checkbox_bg_color_pressed = data.get("checkbox_bg_color_pressed", [0.1, 0.1, 0.1, 1.0])
        checkbox.checkbox_bg_color_disabled = data.get("checkbox_bg_color_disabled", [0.15, 0.15, 0.15, 1.0])
        checkbox.checkbox_border_color = data.get("checkbox_border_color", [0.5, 0.5, 0.5, 1.0])
        checkbox.checkbox_border_color_hover = data.get("checkbox_border_color_hover", [0.7, 0.7, 0.7, 1.0])
        checkbox.checkbox_border_color_focus = data.get("checkbox_border_color_focus", [0.3, 0.6, 1.0, 1.0])
        checkbox.checkbox_border_width = data.get("checkbox_border_width", 1.0)
        checkbox.check_color = data.get("check_color", [0.2, 0.8, 0.2, 1.0])
        checkbox.check_color_disabled = data.get("check_color_disabled", [0.3, 0.5, 0.3, 1.0])
        checkbox.check_style = data.get("check_style", "checkmark")
        checkbox.text_align = data.get("text_align", "left")
        checkbox.button_group = data.get("button_group", None)
        
        # Initialize visual state
        checkbox._is_hovered = False
        checkbox._is_pressed = False
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            checkbox.add_child(child)
        
        return checkbox
    
    def __str__(self) -> str:
        """String representation of the checkbox"""
        return f"CheckBox({self.name}, rect={self.get_rect()}, text='{self.text}', checked={self.button_pressed})"
