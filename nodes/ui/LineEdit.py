"""
LineEdit node implementation for Lupine Engine
Single-line text input control with editing capabilities
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class LineEdit(Control):
    """
    Single-line text input control with editing capabilities.
    
    Features:
    - Text input and editing
    - Placeholder text support
    - Password mode (hidden text)
    - Text selection and clipboard operations
    - Input validation and character limits
    - Cursor positioning and blinking
    - Keyboard navigation (Home, End, arrows)
    - Undo/redo functionality
    """
    
    def __init__(self, name: str = "LineEdit"):
        super().__init__(name)
        self.type = "LineEdit"
        
        # Text properties
        self.text = ""
        self.placeholder_text = "Enter text..."
        self.max_length = 0  # 0 = unlimited
        
        # Display properties
        self.secret = False  # Password mode
        self.secret_character = "*"
        self.editable = True
        self.selecting_enabled = True
        
        # Cursor and selection
        self.cursor_position = 0
        self.selection_start = 0
        self.selection_end = 0
        self.cursor_blink_enabled = True
        self.cursor_blink_speed = 1.0  # Blinks per second
        self._cursor_visible = True
        self._cursor_blink_timer = 0.0
        
        # Text styling
        self.font_path = None
        self.font_size = 14
        self.text_color = [0.9, 0.9, 0.9, 1.0]  # Light gray
        self.placeholder_color = [0.5, 0.5, 0.5, 1.0]  # Darker gray
        self.selection_color = [0.3, 0.5, 0.8, 0.5]  # Blue with transparency
        self.cursor_color = [1.0, 1.0, 1.0, 1.0]  # White
        
        # Background styling
        self.background_color = [0.1, 0.1, 0.1, 1.0]  # Dark background
        self.border_color = [0.4, 0.4, 0.4, 1.0]  # Gray border
        self.border_width = 1.0
        self.corner_radius = 2.0
        
        # Focus styling
        self.focus_border_color = [0.3, 0.6, 1.0, 1.0]  # Blue when focused
        
        # Text alignment
        self.align = "left"  # left, center, right
        
        # Input validation
        self.input_filter = None  # Function to filter input characters
        
        # History for undo/redo
        self._text_history = [""]
        self._history_position = 0
        self._max_history = 50
        
        # Built-in signals
        self.add_signal("text_changed")
        self.add_signal("text_entered")  # When Enter is pressed
        self.add_signal("text_change_rejected")  # When input is rejected
    
    def _ready(self):
        """Called when line edit enters the scene tree"""
        super()._ready()
        
        # Connect input signals
        self.connect("gui_input", self, "_on_gui_input")
        self.connect("focus_entered", self, "_on_focus_entered")
        self.connect("focus_exited", self, "_on_focus_exited")
    
    def _process(self, delta: float):
        """Process cursor blinking"""
        super()._process(delta)
        
        if self.cursor_blink_enabled and self.has_focus():
            self._cursor_blink_timer += delta
            if self._cursor_blink_timer >= 1.0 / self.cursor_blink_speed:
                self._cursor_visible = not self._cursor_visible
                self._cursor_blink_timer = 0.0
    
    def _on_focus_entered(self):
        """Handle gaining focus"""
        self._cursor_visible = True
        self._cursor_blink_timer = 0.0
    
    def _on_focus_exited(self):
        """Handle losing focus"""
        self.clear_selection()
    
    def _on_gui_input(self, event: Dict[str, Any]):
        """Handle input events"""
        if not self.editable:
            return
        
        event_type = event.get("type", "")
        
        if event_type == "key":
            key = event.get("key", "")
            pressed = event.get("pressed", False)
            modifiers = event.get("modifiers", set())
            
            if pressed:
                self._handle_key_input(key, modifiers)
        
        elif event_type == "text":
            text = event.get("text", "")
            self._handle_text_input(text)
    
    def _handle_key_input(self, key: str, modifiers: set):
        """Handle key input"""
        if key == "Return" or key == "Enter":
            self.emit_signal("text_entered", self.text)
        
        elif key == "Backspace":
            self._handle_backspace()
        
        elif key == "Delete":
            self._handle_delete()
        
        elif key == "Left":
            self._handle_cursor_left(modifiers)
        
        elif key == "Right":
            self._handle_cursor_right(modifiers)
        
        elif key == "Home":
            self._handle_home(modifiers)
        
        elif key == "End":
            self._handle_end(modifiers)
        
        elif key == "a" and "ctrl" in modifiers:
            self.select_all()
        
        elif key == "c" and "ctrl" in modifiers:
            self.copy_to_clipboard()
        
        elif key == "v" and "ctrl" in modifiers:
            self.paste_from_clipboard()
        
        elif key == "x" and "ctrl" in modifiers:
            self.cut_to_clipboard()
        
        elif key == "z" and "ctrl" in modifiers:
            if "shift" in modifiers:
                self.redo()
            else:
                self.undo()
    
    def _handle_text_input(self, text: str):
        """Handle text input"""
        if not text:
            return
        
        # Filter input if filter function is set
        if self.input_filter:
            text = self.input_filter(text)
            if not text:
                self.emit_signal("text_change_rejected")
                return
        
        # Check max length
        if self.max_length > 0:
            remaining = self.max_length - len(self.text)
            if remaining <= 0:
                self.emit_signal("text_change_rejected")
                return
            text = text[:remaining]
        
        # Insert text at cursor position
        self.insert_text_at_cursor(text)
    
    def insert_text_at_cursor(self, text: str):
        """Insert text at current cursor position"""
        if self.has_selection():
            self.delete_selection()
        
        # Insert text
        old_text = self.text
        self.text = self.text[:self.cursor_position] + text + self.text[self.cursor_position:]
        self.cursor_position += len(text)
        
        # Add to history
        self._add_to_history()
        
        if old_text != self.text:
            self.emit_signal("text_changed", self.text)
    
    def set_text(self, text: str):
        """Set the text content"""
        old_text = self.text
        self.text = text
        self.cursor_position = min(self.cursor_position, len(self.text))
        self.clear_selection()
        
        # Add to history
        self._add_to_history()
        
        if old_text != self.text:
            self.emit_signal("text_changed", self.text)
    
    def get_text(self) -> str:
        """Get the text content"""
        return self.text
    
    def clear(self):
        """Clear all text"""
        self.set_text("")
    
    def select_all(self):
        """Select all text"""
        self.selection_start = 0
        self.selection_end = len(self.text)
        self.cursor_position = self.selection_end
    
    def clear_selection(self):
        """Clear text selection"""
        self.selection_start = 0
        self.selection_end = 0
    
    def has_selection(self) -> bool:
        """Check if there is selected text"""
        return self.selection_start != self.selection_end
    
    def get_selected_text(self) -> str:
        """Get the selected text"""
        if not self.has_selection():
            return ""
        
        start = min(self.selection_start, self.selection_end)
        end = max(self.selection_start, self.selection_end)
        return self.text[start:end]
    
    def delete_selection(self):
        """Delete selected text"""
        if not self.has_selection():
            return
        
        start = min(self.selection_start, self.selection_end)
        end = max(self.selection_start, self.selection_end)
        
        self.text = self.text[:start] + self.text[end:]
        self.cursor_position = start
        self.clear_selection()
        
        self._add_to_history()
        self.emit_signal("text_changed", self.text)
    
    def _add_to_history(self):
        """Add current text to history for undo/redo"""
        # Remove any history after current position
        self._text_history = self._text_history[:self._history_position + 1]
        
        # Add new state
        self._text_history.append(self.text)
        self._history_position += 1
        
        # Limit history size
        if len(self._text_history) > self._max_history:
            self._text_history.pop(0)
            self._history_position -= 1
    
    def undo(self):
        """Undo last text change"""
        if self._history_position > 0:
            self._history_position -= 1
            self.text = self._text_history[self._history_position]
            self.cursor_position = min(self.cursor_position, len(self.text))
            self.clear_selection()
            self.emit_signal("text_changed", self.text)
    
    def redo(self):
        """Redo last undone text change"""
        if self._history_position < len(self._text_history) - 1:
            self._history_position += 1
            self.text = self._text_history[self._history_position]
            self.cursor_position = min(self.cursor_position, len(self.text))
            self.clear_selection()
            self.emit_signal("text_changed", self.text)
    
    def copy_to_clipboard(self):
        """Copy selected text to clipboard"""
        # This would need to be implemented with actual clipboard access
        selected = self.get_selected_text()
        if selected:
            print(f"[LineEdit] Copy to clipboard: {selected}")  # Debug placeholder
    
    def paste_from_clipboard(self):
        """Paste text from clipboard"""
        # This would need to be implemented with actual clipboard access
        # For now, just a placeholder
        print("[LineEdit] Paste from clipboard")  # Debug placeholder
    
    def cut_to_clipboard(self):
        """Cut selected text to clipboard"""
        self.copy_to_clipboard()
        self.delete_selection()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        
        # Add LineEdit-specific properties
        data.update({
            "text": self.text,
            "placeholder_text": self.placeholder_text,
            "max_length": self.max_length,
            "secret": self.secret,
            "secret_character": self.secret_character,
            "editable": self.editable,
            "selecting_enabled": self.selecting_enabled,
            "font_path": self.font_path,
            "font_size": self.font_size,
            "text_color": self.text_color,
            "placeholder_color": self.placeholder_color,
            "selection_color": self.selection_color,
            "cursor_color": self.cursor_color,
            "background_color": self.background_color,
            "border_color": self.border_color,
            "border_width": self.border_width,
            "corner_radius": self.corner_radius,
            "focus_border_color": self.focus_border_color,
            "align": self.align,
            "cursor_blink_enabled": self.cursor_blink_enabled,
            "cursor_blink_speed": self.cursor_blink_speed,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineEdit":
        """Create from dictionary"""
        line_edit = cls(data.get("name", "LineEdit"))
        cls._apply_node_properties(line_edit, data)
        
        # Apply LineEdit properties
        line_edit.text = data.get("text", "")
        line_edit.placeholder_text = data.get("placeholder_text", "Enter text...")
        line_edit.max_length = data.get("max_length", 0)
        line_edit.secret = data.get("secret", False)
        line_edit.secret_character = data.get("secret_character", "*")
        line_edit.editable = data.get("editable", True)
        line_edit.selecting_enabled = data.get("selecting_enabled", True)
        line_edit.font_path = data.get("font_path", None)
        line_edit.font_size = data.get("font_size", 14)
        line_edit.text_color = data.get("text_color", [0.9, 0.9, 0.9, 1.0])
        line_edit.placeholder_color = data.get("placeholder_color", [0.5, 0.5, 0.5, 1.0])
        line_edit.selection_color = data.get("selection_color", [0.3, 0.5, 0.8, 0.5])
        line_edit.cursor_color = data.get("cursor_color", [1.0, 1.0, 1.0, 1.0])
        line_edit.background_color = data.get("background_color", [0.1, 0.1, 0.1, 1.0])
        line_edit.border_color = data.get("border_color", [0.4, 0.4, 0.4, 1.0])
        line_edit.border_width = data.get("border_width", 1.0)
        line_edit.corner_radius = data.get("corner_radius", 2.0)
        line_edit.focus_border_color = data.get("focus_border_color", [0.3, 0.6, 1.0, 1.0])
        line_edit.align = data.get("align", "left")
        line_edit.cursor_blink_enabled = data.get("cursor_blink_enabled", True)
        line_edit.cursor_blink_speed = data.get("cursor_blink_speed", 1.0)
        
        # Initialize state
        line_edit.cursor_position = min(len(line_edit.text), data.get("cursor_position", 0))
        line_edit._text_history = [line_edit.text]
        line_edit._history_position = 0
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            line_edit.add_child(child)
        
        return line_edit
    
    def __str__(self) -> str:
        """String representation of the line edit"""
        return f"LineEdit({self.name}, rect={self.get_rect()}, text='{self.text}')"
