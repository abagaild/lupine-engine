"""
Label node implementation for Lupine Engine
Text display control with formatting and alignment
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class Label(Control):
    """
    Text display control with formatting, alignment, and wrapping.
    
    Features:
    - Text display with multiple alignment options
    - Word wrapping and clipping
    - Rich text formatting support
    - Auto-sizing based on content
    - Multiple font styles and colors
    - Text effects (shadow, outline)
    """
    
    def __init__(self, name: str = "Label"):
        super().__init__(name)
        self.type = "Label"
        
        # Export variables for editor
        self.export_variables.update({
            "text": {
                "type": "string",
                "value": "Label",
                "description": "Text to display"
            },
            "align": {
                "type": "enum",
                "value": "left",
                "options": ["left", "center", "right"],
                "description": "Horizontal text alignment"
            },
            "valign": {
                "type": "enum",
                "value": "top",
                "options": ["top", "center", "bottom"],
                "description": "Vertical text alignment"
            },
            "autowrap": {
                "type": "bool",
                "value": False,
                "description": "Enable automatic word wrapping"
            },
            "clip_contents": {
                "type": "bool",
                "value": False,
                "description": "Clip text that exceeds the label bounds"
            },
            "uppercase": {
                "type": "bool",
                "value": False,
                "description": "Convert text to uppercase"
            },
            "percent_visible": {
                "type": "float",
                "value": 1.0,
                "min": 0.0,
                "max": 1.0,
                "description": "Percentage of text visible (for animations)"
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
                "min": 1,
                "description": "Font size in pixels"
            },
            "font_color": {
                "type": "color",
                "value": [1.0, 1.0, 1.0, 1.0],
                "description": "Text color (RGBA)"
            }
        })
        
        # Text properties
        self.text: str = "Label"
        self.align: str = "left"  # left, center, right
        self.valign: str = "top"  # top, center, bottom
        self.autowrap: bool = False
        self.clip_contents: bool = False
        self.uppercase: bool = False
        self.percent_visible: float = 1.0
        
        # Font properties
        self.font_path: str = ""  # Custom font file path
        self.font_size: int = 14
        self.font_color: List[float] = [1.0, 1.0, 1.0, 1.0]  # White
        self.font_family: str = "default"
        self.font_bold: bool = False
        self.font_italic: bool = False
        
        # Text effects
        self.shadow_enabled: bool = False
        self.shadow_color: List[float] = [0.0, 0.0, 0.0, 0.5]  # Semi-transparent black
        self.shadow_offset: List[float] = [1.0, 1.0]
        
        self.outline_enabled: bool = False
        self.outline_color: List[float] = [0.0, 0.0, 0.0, 1.0]  # Black
        self.outline_size: float = 1.0
        
        # Internal state
        self._visible_characters: int = -1  # -1 means all characters
        self._line_height: float = 16.0
        self._text_size: List[float] = [0.0, 0.0]
        
        # Mouse filter is ignore by default for labels
        self.mouse_filter = "ignore"
    
    def set_text(self, text: str):
        """Set the label text"""
        old_text = self.text
        self.text = text
        
        if old_text != text:
            self._calculate_text_size()
            self._update_visible_characters()
    
    def get_text(self) -> str:
        """Get the label text"""
        return self.text
    
    def get_displayed_text(self) -> str:
        """Get the text as it will be displayed (with uppercase, etc.)"""
        display_text = self.text
        
        if self.uppercase:
            display_text = display_text.upper()
        
        # Apply percent_visible
        if 0.0 <= self.percent_visible < 1.0:
            visible_chars = int(len(display_text) * self.percent_visible)
            display_text = display_text[:visible_chars]
        
        return display_text
    
    def set_align(self, align: str):
        """Set horizontal text alignment"""
        if align in ["left", "center", "right"]:
            self.align = align
    
    def get_align(self) -> str:
        """Get horizontal text alignment"""
        return self.align
    
    def set_valign(self, valign: str):
        """Set vertical text alignment"""
        if valign in ["top", "center", "bottom"]:
            self.valign = valign
    
    def get_valign(self) -> str:
        """Get vertical text alignment"""
        return self.valign
    
    def set_autowrap(self, autowrap: bool):
        """Set automatic word wrapping"""
        self.autowrap = autowrap
        self._calculate_text_size()
    
    def is_autowrap_enabled(self) -> bool:
        """Check if autowrap is enabled"""
        return self.autowrap
    
    def set_clip_contents(self, clip: bool):
        """Set content clipping"""
        self.clip_contents = clip
    
    def is_clipping_contents(self) -> bool:
        """Check if content clipping is enabled"""
        return self.clip_contents
    
    def set_uppercase(self, uppercase: bool):
        """Set uppercase conversion"""
        self.uppercase = uppercase
    
    def is_uppercase(self) -> bool:
        """Check if uppercase conversion is enabled"""
        return self.uppercase
    
    def set_percent_visible(self, percent: float):
        """Set percentage of text visible"""
        self.percent_visible = max(0.0, min(1.0, percent))
        self._update_visible_characters()
    
    def get_percent_visible(self) -> float:
        """Get percentage of text visible"""
        return self.percent_visible
    
    def set_visible_characters(self, characters: int):
        """Set number of visible characters"""
        self._visible_characters = max(-1, characters)
        if characters >= 0 and len(self.text) > 0:
            self.percent_visible = characters / len(self.text)
        else:
            self.percent_visible = 1.0
    
    def get_visible_characters(self) -> int:
        """Get number of visible characters"""
        if self._visible_characters >= 0:
            return self._visible_characters
        return len(self.get_displayed_text())
    
    def _update_visible_characters(self):
        """Update visible characters based on percent_visible"""
        if 0.0 <= self.percent_visible < 1.0:
            self._visible_characters = int(len(self.text) * self.percent_visible)
        else:
            self._visible_characters = -1
    
    def set_font_size(self, size: int):
        """Set font size"""
        self.font_size = max(1, size)
        self._line_height = self.font_size * 1.2  # Rough line height calculation
        self._calculate_text_size()
    
    def get_font_size(self) -> int:
        """Get font size"""
        return self.font_size
    
    def set_font_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Set font color"""
        self.font_color = [r, g, b, a]
    
    def get_font_color(self) -> List[float]:
        """Get font color"""
        return self.font_color.copy()
    
    def set_font_bold(self, bold: bool):
        """Set font bold"""
        self.font_bold = bold
        self._calculate_text_size()
    
    def is_font_bold(self) -> bool:
        """Check if font is bold"""
        return self.font_bold
    
    def set_font_italic(self, italic: bool):
        """Set font italic"""
        self.font_italic = italic
    
    def is_font_italic(self) -> bool:
        """Check if font is italic"""
        return self.font_italic
    
    def set_shadow_enabled(self, enabled: bool):
        """Enable or disable text shadow"""
        self.shadow_enabled = enabled
    
    def is_shadow_enabled(self) -> bool:
        """Check if text shadow is enabled"""
        return self.shadow_enabled
    
    def set_shadow_color(self, r: float, g: float, b: float, a: float = 0.5):
        """Set shadow color"""
        self.shadow_color = [r, g, b, a]
    
    def get_shadow_color(self) -> List[float]:
        """Get shadow color"""
        return self.shadow_color.copy()
    
    def set_shadow_offset(self, x: float, y: float):
        """Set shadow offset"""
        self.shadow_offset = [x, y]
    
    def get_shadow_offset(self) -> List[float]:
        """Get shadow offset"""
        return self.shadow_offset.copy()
    
    def set_outline_enabled(self, enabled: bool):
        """Enable or disable text outline"""
        self.outline_enabled = enabled
    
    def is_outline_enabled(self) -> bool:
        """Check if text outline is enabled"""
        return self.outline_enabled
    
    def set_outline_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Set outline color"""
        self.outline_color = [r, g, b, a]
    
    def get_outline_color(self) -> List[float]:
        """Get outline color"""
        return self.outline_color.copy()
    
    def set_outline_size(self, size: float):
        """Set outline size"""
        self.outline_size = max(0.0, size)
    
    def get_outline_size(self) -> float:
        """Get outline size"""
        return self.outline_size
    
    def _calculate_text_size(self):
        """Calculate the size needed for the text"""
        # This is a simplified calculation - a full implementation would use actual font metrics
        display_text = self.get_displayed_text()
        
        if not display_text:
            self._text_size = [0.0, 0.0]
            return
        
        # Rough character width calculation
        char_width = self.font_size * 0.6
        
        if self.autowrap and self.size[0] > 0:
            # Calculate wrapped text size
            max_chars_per_line = max(1, int(self.size[0] / char_width))
            lines = []
            words = display_text.split(' ')
            current_line = ""
            
            for word in words:
                if len(current_line + word) <= max_chars_per_line:
                    current_line += word + " "
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            
            if current_line:
                lines.append(current_line.strip())
            
            width = min(self.size[0], max(len(line) * char_width for line in lines) if lines else 0)
            height = len(lines) * self._line_height
        else:
            # Single line or no wrapping
            lines = display_text.split('\n')
            width = max(len(line) * char_width for line in lines) if lines else 0
            height = len(lines) * self._line_height
        
        self._text_size = [width, height]
    
    def get_text_size(self) -> List[float]:
        """Get the calculated text size"""
        return self._text_size.copy()
    
    def get_minimum_size(self) -> List[float]:
        """Get the minimum size needed for the text"""
        return self.get_text_size()
    
    def auto_resize(self):
        """Automatically resize the label to fit the text"""
        text_size = self.get_text_size()
        self.set_size(text_size[0], text_size[1])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "text": self.text,
            "align": self.align,
            "valign": self.valign,
            "autowrap": self.autowrap,
            "clip_contents": self.clip_contents,
            "uppercase": self.uppercase,
            "percent_visible": self.percent_visible,
            "font_path": self.font_path,
            "font_size": self.font_size,
            "font_color": self.font_color.copy(),
            "font_family": self.font_family,
            "font_bold": self.font_bold,
            "font_italic": self.font_italic,
            "shadow_enabled": self.shadow_enabled,
            "shadow_color": self.shadow_color.copy(),
            "shadow_offset": self.shadow_offset.copy(),
            "outline_enabled": self.outline_enabled,
            "outline_color": self.outline_color.copy(),
            "outline_size": self.outline_size
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Label":
        """Create from dictionary"""
        label = cls(data.get("name", "Label"))
        cls._apply_node_properties(label, data)
        
        # Apply Control properties
        label.position = data.get("position", [0.0, 0.0])
        label.size = data.get("size", [100.0, 20.0])
        label.follow_viewport = data.get("follow_viewport", True)
        label.mouse_filter = data.get("mouse_filter", "ignore")
        label.focus_mode = data.get("focus_mode", "none")
        label.clip_contents = data.get("clip_contents", False)
        label.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
        
        # Apply Label properties
        label.text = data.get("text", "Label")
        label.align = data.get("align", "left")
        label.valign = data.get("valign", "top")
        label.autowrap = data.get("autowrap", False)
        label.clip_contents = data.get("clip_contents", False)
        label.uppercase = data.get("uppercase", False)
        label.percent_visible = data.get("percent_visible", 1.0)
        label.font_path = data.get("font_path", "")
        label.font_size = data.get("font_size", 14)
        label.font_color = data.get("font_color", [1.0, 1.0, 1.0, 1.0])
        label.font_family = data.get("font_family", "default")
        label.font_bold = data.get("font_bold", False)
        label.font_italic = data.get("font_italic", False)
        label.shadow_enabled = data.get("shadow_enabled", False)
        label.shadow_color = data.get("shadow_color", [0.0, 0.0, 0.0, 0.5])
        label.shadow_offset = data.get("shadow_offset", [1.0, 1.0])
        label.outline_enabled = data.get("outline_enabled", False)
        label.outline_color = data.get("outline_color", [0.0, 0.0, 0.0, 1.0])
        label.outline_size = data.get("outline_size", 1.0)
        
        # Calculate text size
        label._calculate_text_size()
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            label.add_child(child)
        
        return label
    
    def __str__(self) -> str:
        """String representation of the label"""
        return f"Label({self.name}, text='{self.text[:20]}{'...' if len(self.text) > 20 else ''}')"
