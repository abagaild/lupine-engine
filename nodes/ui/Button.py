"""
Button node implementation for Lupine Engine
Interactive button control with text and styling
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class Button(Control):
    """
    Interactive button control with text, icons, and styling.
    
    Features:
    - Text display with alignment
    - Icon support
    - Multiple button states (normal, hover, pressed, disabled)
    - Toggle mode support
    - Keyboard shortcuts
    - Click and press signals
    - Flat and styled appearance modes
    """
    
    def __init__(self, name: str = "Button"):
        super().__init__(name)
        self.type = "Button"
        
        # Export variables for editor
        self.export_variables.update({
            "text": {
                "type": "string",
                "value": "Button",
                "description": "Text displayed on the button"
            },
            "icon": {
                "type": "path",
                "value": "",
                "filter": "*.png,*.jpg,*.jpeg,*.bmp,*.tga",
                "description": "Icon texture file"
            },
            "flat": {
                "type": "bool",
                "value": False,
                "description": "Flat appearance without background"
            },
            "toggle_mode": {
                "type": "bool",
                "value": False,
                "description": "Toggle button mode"
            },
            "pressed": {
                "type": "bool",
                "value": False,
                "description": "Whether button is pressed (toggle mode)"
            },
            "disabled": {
                "type": "bool",
                "value": False,
                "description": "Whether button is disabled"
            },
            "text_align": {
                "type": "enum",
                "value": "center",
                "options": ["left", "center", "right"],
                "description": "Text alignment"
            },
            "icon_align": {
                "type": "enum",
                "value": "left",
                "options": ["left", "center", "right"],
                "description": "Icon alignment"
            },
            "font_path": {
                "type": "path",
                "value": "",
                "filter": "*.ttf,*.otf",
                "description": "Custom font file path"
            },
            "font_size": {
                "type": "int",
                "value": 14,
                "min": 6,
                "max": 72,
                "description": "Font size in pixels"
            },
            "font_color": {
                "type": "color",
                "value": [1.0, 1.0, 1.0, 1.0],
                "description": "Text color (RGBA)"
            },
            "font_color_hover": {
                "type": "color",
                "value": [0.9, 0.9, 0.9, 1.0],
                "description": "Hover text color (RGBA)"
            },
            "font_color_pressed": {
                "type": "color",
                "value": [0.8, 0.8, 0.8, 1.0],
                "description": "Pressed text color (RGBA)"
            },
            "font_color_disabled": {
                "type": "color",
                "value": [0.5, 0.5, 0.5, 1.0],
                "description": "Disabled text color (RGBA)"
            },
            "bg_color": {
                "type": "color",
                "value": [0.3, 0.3, 0.3, 1.0],
                "description": "Background color (RGBA)"
            },
            "bg_color_hover": {
                "type": "color",
                "value": [0.4, 0.4, 0.4, 1.0],
                "description": "Hover background color (RGBA)"
            },
            "bg_color_pressed": {
                "type": "color",
                "value": [0.2, 0.2, 0.2, 1.0],
                "description": "Pressed background color (RGBA)"
            },
            "bg_color_disabled": {
                "type": "color",
                "value": [0.15, 0.15, 0.15, 1.0],
                "description": "Disabled background color (RGBA)"
            },
            "border_width": {
                "type": "float",
                "value": 1.0,
                "min": 0.0,
                "max": 10.0,
                "description": "Border width in pixels"
            },
            "border_color": {
                "type": "color",
                "value": [0.6, 0.6, 0.6, 1.0],
                "description": "Border color (RGBA)"
            },
            "border_radius": {
                "type": "float",
                "value": 4.0,
                "min": 0.0,
                "max": 50.0,
                "description": "Corner radius in pixels"
            }
        })
        
        # Button properties
        self.text: str = "Button"
        self.icon: str = ""
        self.flat: bool = False
        self.toggle_mode: bool = False
        self.pressed: bool = False
        self.disabled: bool = False
        self.text_align: str = "center"
        self.icon_align: str = "left"

        # Font properties
        self.font_path: str = ""  # Custom font file path
        self.font_size: int = 14
        self.font_color: List[float] = [1.0, 1.0, 1.0, 1.0]  # White
        self.font_color_hover: List[float] = [0.9, 0.9, 0.9, 1.0]  # Light gray
        self.font_color_pressed: List[float] = [0.8, 0.8, 0.8, 1.0]  # Gray
        self.font_color_disabled: List[float] = [0.5, 0.5, 0.5, 1.0]  # Dark gray
        
        # Background colors
        self.bg_color: List[float] = [0.3, 0.3, 0.3, 1.0]  # Dark gray
        self.bg_color_hover: List[float] = [0.4, 0.4, 0.4, 1.0]  # Lighter gray
        self.bg_color_pressed: List[float] = [0.2, 0.2, 0.2, 1.0]  # Darker gray
        self.bg_color_disabled: List[float] = [0.15, 0.15, 0.15, 1.0]  # Very dark gray
        
        # Border properties
        self.border_width: float = 1.0
        self.border_color: List[float] = [0.6, 0.6, 0.6, 1.0]  # Light gray
        self.border_radius: float = 4.0
        
        # State
        self._is_hovered: bool = False
        self._is_pressed: bool = False

        # Set default size for buttons
        self.size = [100.0, 30.0]

        # Set focus mode to click by default
        self.focus_mode = "click"
        
        # Built-in signals
        self.add_signal("button_down")
        self.add_signal("button_up")
        self.add_signal("pressed")
        self.add_signal("toggled")
    
    def _ready(self):
        """Called when button enters the scene tree"""
        super()._ready()
        
        # Connect mouse signals
        self.connect("mouse_entered", self, "_on_mouse_entered")
        self.connect("mouse_exited", self, "_on_mouse_exited")
        self.connect("gui_input", self, "_on_gui_input")
    
    def _on_mouse_entered(self):
        """Handle mouse entering the button"""
        if not self.disabled:
            print(f"Mouse entered button '{self.name}'")  # Debug output
            self._is_hovered = True
            self._update_visual_state()

    def _on_mouse_exited(self):
        """Handle mouse exiting the button"""
        print(f"Mouse exited button '{self.name}'")  # Debug output
        self._is_hovered = False
        self._is_pressed = False
        self._update_visual_state()
    
    def _on_gui_input(self, event: Dict[str, Any]):
        """Handle input events"""
        if self.disabled:
            return
        
        if event.get("type") == "mouse_button":
            button = event.get("button", 1)  # 1 = left mouse button
            pressed = event.get("pressed", False)
            
            if button == 1:  # Left mouse button
                if pressed:
                    self._handle_button_down()
                else:
                    self._handle_button_up()
        
        elif event.get("type") == "key":
            key = event.get("key", "")
            pressed = event.get("pressed", False)
            
            # Handle Enter and Space as button activation
            if key in ["Return", "space"] and pressed:
                self._handle_button_down()
                # Simulate immediate release for keyboard
                self._handle_button_up()
    
    def _handle_button_down(self):
        """Handle button press down"""
        if self.disabled:
            return

        self._is_pressed = True
        self.grab_focus()
        self._update_visual_state()
        self.emit_signal("button_down")

    def _handle_button_up(self):
        """Handle button press up"""
        if self.disabled:
            return

        was_pressed = self._is_pressed
        self._is_pressed = False
        self._update_visual_state()

        if was_pressed and self._is_hovered:
            # Button was clicked
            print(f"Button '{self.name}' clicked!")  # Debug output
            self.emit_signal("button_up")
            self.emit_signal("pressed")

            if self.toggle_mode:
                self.set_pressed(not self.pressed)
                self.emit_signal("toggled", self.pressed)
    
    def set_text(self, text: str):
        """Set the button text"""
        self.text = text
    
    def get_text(self) -> str:
        """Get the button text"""
        return self.text
    
    def set_icon(self, icon_path: str):
        """Set the button icon"""
        self.icon = icon_path
    
    def get_icon(self) -> str:
        """Get the button icon"""
        return self.icon
    
    def set_flat(self, flat: bool):
        """Set flat appearance mode"""
        self.flat = flat
    
    def is_flat(self) -> bool:
        """Check if button is flat"""
        return self.flat
    
    def set_toggle_mode(self, toggle: bool):
        """Set toggle mode"""
        self.toggle_mode = toggle
        if not toggle:
            self.pressed = False
    
    def is_toggle_mode(self) -> bool:
        """Check if button is in toggle mode"""
        return self.toggle_mode
    
    def set_pressed(self, pressed: bool):
        """Set pressed state (toggle mode)"""
        if self.toggle_mode:
            old_pressed = self.pressed
            self.pressed = pressed
            if old_pressed != pressed:
                self.emit_signal("toggled", self.pressed)
    
    def is_pressed(self) -> bool:
        """Check if button is pressed"""
        return self.pressed or self._is_pressed
    
    def set_disabled(self, disabled: bool):
        """Set disabled state"""
        self.disabled = disabled
        if disabled:
            self._is_hovered = False
            self._is_pressed = False
            self.release_focus()
    
    def is_disabled(self) -> bool:
        """Check if button is disabled"""
        return self.disabled
    
    def set_text_align(self, align: str):
        """Set text alignment"""
        if align in ["left", "center", "right"]:
            self.text_align = align
    
    def get_text_align(self) -> str:
        """Get text alignment"""
        return self.text_align
    
    def set_icon_align(self, align: str):
        """Set icon alignment"""
        if align in ["left", "center", "right"]:
            self.icon_align = align
    
    def get_icon_align(self) -> str:
        """Get icon alignment"""
        return self.icon_align
    
    def get_current_font_color(self) -> List[float]:
        """Get the current font color based on state"""
        if self.disabled:
            return self.font_color_disabled.copy()
        elif self.is_pressed():
            return self.font_color_pressed.copy()
        elif self._is_hovered:
            return self.font_color_hover.copy()
        else:
            return self.font_color.copy()
    
    def get_current_bg_color(self) -> List[float]:
        """Get the current background color based on state"""
        if self.flat:
            return [0.0, 0.0, 0.0, 0.0]  # Transparent for flat buttons
        
        if self.disabled:
            return self.bg_color_disabled.copy()
        elif self.is_pressed():
            return self.bg_color_pressed.copy()
        elif self._is_hovered:
            return self.bg_color_hover.copy()
        else:
            return self.bg_color.copy()
    
    def get_minimum_size(self) -> List[float]:
        """Get the minimum size needed for the button content"""
        # This would calculate based on text and icon size in a full implementation
        min_width = len(self.text) * 8 + 20  # Rough estimate
        min_height = self.font_size + 10
        
        if self.icon:
            min_width += 20  # Icon space
            min_height = max(min_height, 20)  # Icon height
        
        return [min_width, min_height]
    
    def click(self):
        """Programmatically click the button"""
        if not self.disabled:
            self._handle_button_down()
            self._handle_button_up()

    def _update_visual_state(self):
        """Update visual state for rendering"""
        # This method is called to sync the button's internal state
        # with any external rendering system that needs to know about
        # hover/pressed states for visual feedback

        # Update the UI data if this button is part of a game engine's UI system
        # This ensures the renderer gets the updated visual state
        if hasattr(self, '_ui_data_ref'):
            ui_data = self._ui_data_ref
            if ui_data:
                ui_data['_is_hovered'] = self._is_hovered
                ui_data['_is_pressed'] = self._is_pressed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "text": self.text,
            "icon": self.icon,
            "flat": self.flat,
            "toggle_mode": self.toggle_mode,
            "pressed": self.pressed,
            "disabled": self.disabled,
            "text_align": self.text_align,
            "icon_align": self.icon_align,
            "font_path": self.font_path,
            "font_size": self.font_size,
            "font_color": self.font_color.copy(),
            "font_color_hover": self.font_color_hover.copy(),
            "font_color_pressed": self.font_color_pressed.copy(),
            "font_color_disabled": self.font_color_disabled.copy(),
            "bg_color": self.bg_color.copy(),
            "bg_color_hover": self.bg_color_hover.copy(),
            "bg_color_pressed": self.bg_color_pressed.copy(),
            "bg_color_disabled": self.bg_color_disabled.copy(),
            "border_width": self.border_width,
            "border_color": self.border_color.copy(),
            "border_radius": self.border_radius,
            # Include visual state for rendering
            "_is_hovered": self._is_hovered,
            "_is_pressed": self._is_pressed
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Button":
        """Create from dictionary"""
        button = cls(data.get("name", "Button"))
        cls._apply_node_properties(button, data)
        
        # Apply Control properties
        button.size = data.get("size", [100.0, 30.0])
        button.follow_viewport = data.get("follow_viewport", True)
        button.mouse_filter = data.get("mouse_filter", "stop")
        button.focus_mode = data.get("focus_mode", "click")
        
        # Apply Button properties
        button.text = data.get("text", "Button")
        button.icon = data.get("icon", "")
        button.flat = data.get("flat", False)
        button.toggle_mode = data.get("toggle_mode", False)
        button.pressed = data.get("pressed", False)
        button.disabled = data.get("disabled", False)
        button.text_align = data.get("text_align", "center")
        button.icon_align = data.get("icon_align", "left")
        button.font_path = data.get("font_path", "")
        button.font_size = data.get("font_size", 14)
        button.font_color = data.get("font_color", [1.0, 1.0, 1.0, 1.0])
        button.bg_color = data.get("bg_color", [0.3, 0.3, 0.3, 1.0])
        button.border_width = data.get("border_width", 1.0)
        button.border_color = data.get("border_color", [0.6, 0.6, 0.6, 1.0])
        button.border_radius = data.get("border_radius", 4.0)
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            button.add_child(child)
        
        return button

    def __str__(self) -> str:
        """String representation of the button"""
        return f"Button({self.name}, text='{self.text}', disabled={self.disabled})"
