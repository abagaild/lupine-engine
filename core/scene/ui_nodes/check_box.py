"""
scene/ui_nodes/check_box.py

Defines CheckBox (toggleable boolean box with label).
"""

from typing import Dict, Any
from .control import Control


class CheckBox(Control):
    """CheckBox: a labeled checkbox (boolean toggle)."""

    def __init__(self, name: str = "CheckBox"):
        super().__init__(name)
        self.type = "CheckBox"

        self.text: str = ""
        self.pressed: bool = False
        self.focus_mode: str = "click"  # none, click, all
        self.allow_focus: bool = True
        self.allow_reject_focus: bool = False

        self.script_path = "nodes/ui/CheckBox.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "text": self.text,
            "pressed": self.pressed,
            "focus_mode": self.focus_mode,
            "allow_focus": self.allow_focus,
            "allow_reject_focus": self.allow_reject_focus
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckBox":
        node = cls(data.get("name", "CheckBox"))
        node.text = data.get("text", "")
        node.pressed = data.get("pressed", False)
        node.focus_mode = data.get("focus_mode", "click")
        node.allow_focus = data.get("allow_focus", True)
        node.allow_reject_focus = data.get("allow_reject_focus", False)
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
