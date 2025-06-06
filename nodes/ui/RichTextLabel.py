"""
RichTextLabel node implementation for Lupine Engine
Rich text display control with BBCode formatting support
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional
import re


class RichTextLabel(Control):
    """
    Rich text display control with BBCode formatting support.
    
    Features:
    - BBCode text formatting ([b], [i], [color], [size], etc.)
    - Scrollable text content
    - Custom text effects
    - Link support with signals
    - Table support
    - Image embedding
    - Custom fonts and styles
    """
    
    def __init__(self, name: str = "RichTextLabel"):
        super().__init__(name)
        self.type = "RichTextLabel"

        # Export variables for editor
        self.export_variables.update({
            "text": {
                "type": "string",
                "value": "",
                "multiline": True,
                "description": "Rich text content with BBCode support"
            },
            "bbcode_enabled": {
                "type": "bool",
                "value": True,
                "description": "Enable BBCode parsing"
            },
            "scroll_active": {
                "type": "bool",
                "value": True,
                "description": "Enable scrolling for overflow content"
            },
            "scroll_following": {
                "type": "bool",
                "value": False,
                "description": "Auto-scroll to bottom when new content is added"
            },
            "background_color": {
                "type": "color",
                "value": [0.0, 0.0, 0.0, 0.0],
                "description": "Background color (RGBA)"
            },
            "border_color": {
                "type": "color",
                "value": [0.5, 0.5, 0.5, 1.0],
                "description": "Border color (RGBA)"
            },
            "border_width": {
                "type": "float",
                "value": 0.0,
                "min": 0.0,
                "max": 10.0,
                "description": "Border width in pixels"
            },
            "default_color": {
                "type": "color",
                "value": [1.0, 1.0, 1.0, 1.0],
                "description": "Default text color (RGBA)"
            },
            "default_font_size": {
                "type": "int",
                "value": 14,
                "min": 1,
                "description": "Default font size"
            }
        })

        # Text properties
        self.text = ""
        self.bbcode_enabled = True
        self.parsed_text = ""  # Processed text without BBCode tags
        
        # Scrolling properties
        self.scroll_active = True
        self.scroll_following = False
        self.scroll_position = 0.0
        self.max_scroll = 0.0
        
        # Visual properties
        self.background_color = [0.0, 0.0, 0.0, 0.0]  # Transparent by default
        self.border_color = [0.5, 0.5, 0.5, 1.0]
        self.border_width = 0.0
        
        # Text formatting
        self.default_color = [1.0, 1.0, 1.0, 1.0]
        self.default_font_size = 14
        self.default_font_path = ""
        
        # Text effects
        self.selection_enabled = True
        self.context_menu_enabled = True
        
        # Internal state
        self._formatted_lines = []  # Processed text lines with formatting
        self._line_height = 16
        self._needs_reparse = True
        
        # Built-in signals
        self.add_signal("text_changed")
        self.add_signal("link_clicked")
        self.add_signal("meta_clicked")
        self.add_signal("meta_hover_started")
        self.add_signal("meta_hover_ended")
    
    def _ready(self):
        """Called when rich text label enters the scene tree"""
        super()._ready()
        self._parse_text()
    
    def _parse_text(self):
        """Parse BBCode text and prepare for rendering"""
        if not self.bbcode_enabled:
            self.parsed_text = self.text
            self._formatted_lines = [{"text": line, "color": self.default_color, "size": self.default_font_size} 
                                   for line in self.text.split('\n')]
        else:
            # Simple BBCode parsing (can be expanded)
            self.parsed_text = self._strip_bbcode(self.text)
            self._formatted_lines = self._parse_bbcode_lines(self.text)
        
        self._needs_reparse = False
        self._calculate_scroll_bounds()
    
    def _strip_bbcode(self, text: str) -> str:
        """Remove BBCode tags from text"""
        # Simple regex to remove common BBCode tags
        bbcode_pattern = r'\[/?(?:b|i|u|s|color|size|font|url|img|center|right|left)\]|\[color=[^\]]+\]|\[size=[^\]]+\]|\[font=[^\]]+\]'
        return re.sub(bbcode_pattern, '', text, flags=re.IGNORECASE)
    
    def _parse_bbcode_lines(self, text: str) -> List[Dict[str, Any]]:
        """Parse BBCode text into formatted lines"""
        lines = []
        current_color = self.default_color.copy()
        current_size = self.default_font_size
        
        for line in text.split('\n'):
            # Simple parsing - can be expanded for full BBCode support
            processed_line = self._strip_bbcode(line)
            
            # Extract color tags
            color_match = re.search(r'\[color=([^\]]+)\]', line, re.IGNORECASE)
            if color_match:
                color_str = color_match.group(1)
                if color_str.startswith('#'):
                    # Hex color
                    try:
                        hex_color = color_str[1:]
                        if len(hex_color) == 6:
                            r = int(hex_color[0:2], 16) / 255.0
                            g = int(hex_color[2:4], 16) / 255.0
                            b = int(hex_color[4:6], 16) / 255.0
                            current_color = [r, g, b, 1.0]
                    except ValueError:
                        pass
            
            # Extract size tags
            size_match = re.search(r'\[size=(\d+)\]', line, re.IGNORECASE)
            if size_match:
                try:
                    current_size = int(size_match.group(1))
                except ValueError:
                    pass
            
            lines.append({
                "text": processed_line,
                "color": current_color.copy(),
                "size": current_size
            })
        
        return lines
    
    def _calculate_scroll_bounds(self):
        """Calculate maximum scroll position"""
        total_height = len(self._formatted_lines) * self._line_height
        visible_height = self.size[1]
        self.max_scroll = max(0.0, total_height - visible_height)
    
    def set_text(self, text: str):
        """Set the text content"""
        old_text = self.text
        self.text = text
        self._needs_reparse = True
        
        if old_text != text:
            self.emit_signal("text_changed", text)
            
        if self.scroll_following:
            self.scroll_to_bottom()
    
    def get_text(self) -> str:
        """Get the text content"""
        return self.text
    
    def append_text(self, text: str):
        """Append text to existing content"""
        self.set_text(self.text + text)
    
    def clear(self):
        """Clear all text content"""
        self.set_text("")
    
    def set_bbcode_enabled(self, enabled: bool):
        """Enable or disable BBCode parsing"""
        if self.bbcode_enabled != enabled:
            self.bbcode_enabled = enabled
            self._needs_reparse = True
    
    def scroll_to_line(self, line: int):
        """Scroll to a specific line"""
        if self.scroll_active:
            target_scroll = line * self._line_height
            self.scroll_position = max(0.0, min(self.max_scroll, target_scroll))
    
    def scroll_to_bottom(self):
        """Scroll to the bottom of the content"""
        if self.scroll_active:
            self.scroll_position = self.max_scroll
    
    def get_line_count(self) -> int:
        """Get the number of lines in the text"""
        return len(self._formatted_lines)
    
    def get_visible_line_count(self) -> int:
        """Get the number of visible lines"""
        return int(self.size[1] / self._line_height)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        
        # Add RichTextLabel-specific properties
        data.update({
            "text": self.text,
            "bbcode_enabled": self.bbcode_enabled,
            "scroll_active": self.scroll_active,
            "scroll_following": self.scroll_following,
            "background_color": self.background_color,
            "border_color": self.border_color,
            "border_width": self.border_width,
            "default_color": self.default_color,
            "default_font_size": self.default_font_size,
            "selection_enabled": self.selection_enabled,
            "context_menu_enabled": self.context_menu_enabled,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RichTextLabel":
        """Create from dictionary"""
        rich_text_label = cls(data.get("name", "RichTextLabel"))
        cls._apply_node_properties(rich_text_label, data)
        
        # Apply RichTextLabel properties
        rich_text_label.text = data.get("text", "")
        rich_text_label.bbcode_enabled = data.get("bbcode_enabled", True)
        rich_text_label.scroll_active = data.get("scroll_active", True)
        rich_text_label.scroll_following = data.get("scroll_following", False)
        rich_text_label.background_color = data.get("background_color", [0.0, 0.0, 0.0, 0.0])
        rich_text_label.border_color = data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        rich_text_label.border_width = data.get("border_width", 0.0)
        rich_text_label.default_color = data.get("default_color", [1.0, 1.0, 1.0, 1.0])
        rich_text_label.default_font_size = data.get("default_font_size", 14)
        rich_text_label.selection_enabled = data.get("selection_enabled", True)
        rich_text_label.context_menu_enabled = data.get("context_menu_enabled", True)
        
        # Parse text after loading
        rich_text_label._parse_text()
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            rich_text_label.add_child(child)
        
        return rich_text_label
    
    def __str__(self) -> str:
        """String representation of the rich text label"""
        return f"RichTextLabel({self.name}, text_length={len(self.text)}, bbcode={self.bbcode_enabled})"
