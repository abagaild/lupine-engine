"""
scene/ui_nodes/rich_text_label.py

Defines RichTextLabel (multi-line, stylable text).
"""

from typing import Dict, Any
from .control import Control


class RichTextLabel(Control):
    """RichTextLabel: displays rich text with BBCode-like styling."""

    def __init__(self, name: str = "RichTextLabel"):
        super().__init__(name)
        self.type = "RichTextLabel"

        self.bbcode_enabled: bool = False
        self.text: str = ""
        self.percent_visible: float = 1.0
        self.visible_characters: int = -1
        self.max_visible_lines: int = -1
        self.scroll_active: bool = True
        self.fit_content: bool = False
        self.font: Any = None
        self.font_size: int = 14
        self.default_color: [float, float, float, float] = [0.0, 0.0, 0.0, 1.0]

        self.script_path = "nodes/ui/RichTextLabel.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "bbcode_enabled": self.bbcode_enabled,
            "text": self.text,
            "percent_visible": self.percent_visible,
            "visible_characters": self.visible_characters,
            "max_visible_lines": self.max_visible_lines,
            "scroll_active": self.scroll_active,
            "fit_content": self.fit_content,
            "font": self.font,
            "font_size": self.font_size,
            "default_color": self.default_color
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RichTextLabel":
        node = cls(data.get("name", "RichTextLabel"))
        node.bbcode_enabled = data.get("bbcode_enabled", False)
        node.text = data.get("text", "")
        node.percent_visible = data.get("percent_visible", 1.0)
        node.visible_characters = data.get("visible_characters", -1)
        node.max_visible_lines = data.get("max_visible_lines", -1)
        node.scroll_active = data.get("scroll_active", True)
        node.fit_content = data.get("fit_content", False)
        node.font = data.get("font")
        node.font_size = data.get("font_size", 14)
        node.default_color = data.get("default_color", [0.0, 0.0, 0.0, 1.0])
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
