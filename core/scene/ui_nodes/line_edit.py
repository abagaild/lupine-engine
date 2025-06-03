"""
scene/ui_nodes/line_edit.py

Defines LineEdit (single-line text input).
"""

from typing import Dict, Any
from .control import Control


class LineEdit(Control):
    """LineEdit: single-line text input field."""

    def __init__(self, name: str = "LineEdit"):
        super().__init__(name)
        self.type = "LineEdit"

        # Text input fields
        self.text: str = ""
        self.placeholder_text: str = ""
        self.max_length: int = 0  # 0 for unlimited
        self.read_only: bool = False
        self.password_mode: bool = False
        self.align: str = "left"  # left, center, right
        self.valign: str = "center"  # top, center, bottom
        self.allow_reject_focus: bool = False
        self.caret_blink: bool = True
        self.caret_blink_speed: float = 1.0
        self.caret_color: [float, float, float, float] = [0.0, 0.0, 0.0, 1.0]
        self.selection_color: [float, float, float, float] = [0.5, 0.5, 1.0, 0.5]

        self.script_path = "nodes/ui/LineEdit.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "text": self.text,
            "placeholder_text": self.placeholder_text,
            "max_length": self.max_length,
            "read_only": self.read_only,
            "password_mode": self.password_mode,
            "align": self.align,
            "valign": self.valign,
            "allow_reject_focus": self.allow_reject_focus,
            "caret_blink": self.caret_blink,
            "caret_blink_speed": self.caret_blink_speed,
            "caret_color": self.caret_color,
            "selection_color": self.selection_color
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineEdit":
        node = cls(data.get("name", "LineEdit"))
        node.text = data.get("text", "")
        node.placeholder_text = data.get("placeholder_text", "")
        node.max_length = data.get("max_length", 0)
        node.read_only = data.get("read_only", False)
        node.password_mode = data.get("password_mode", False)
        node.align = data.get("align", "left")
        node.valign = data.get("valign", "center")
        node.allow_reject_focus = data.get("allow_reject_focus", False)
        node.caret_blink = data.get("caret_blink", True)
        node.caret_blink_speed = data.get("caret_blink_speed", 1.0)
        node.caret_color = data.get("caret_color", [0.0, 0.0, 0.0, 1.0])
        node.selection_color = data.get("selection_color", [0.5, 0.5, 1.0, 0.5])
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
