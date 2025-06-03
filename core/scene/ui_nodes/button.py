"""
scene/ui_nodes/button.py

Defines Button (clickable UI element with text).
"""

from typing import Dict, Any
from .label import Label
from .panel import Panel


class Button(Panel):
    """Button node: a Panel with a Label child to display text."""

    def __init__(self, name: str = "Button"):
        super().__init__(name)
        self.type = "Button"

        # Button-specific fields
        self.text: str = "Button"
        self.toggle_mode: bool = False
        self.pressed: bool = False
        self.focus_mode: str = "all"

        # Styling for up / down states
        self.normal_color: [float, float, float, float] = [0.8, 0.8, 0.8, 1.0]
        self.pressed_color: [float, float, float, float] = [0.6, 0.6, 0.6, 1.0]
        self.hover_color: [float, float, float, float] = [0.9, 0.9, 0.9, 1.0]
        self.text_label = Label("ButtonLabel")
        self.add_child(self.text_label)

        self.script_path = "nodes/ui/Button.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "text": self.text,
            "toggle_mode": self.toggle_mode,
            "pressed": self.pressed,
            "focus_mode": self.focus_mode,
            "normal_color": self.normal_color,
            "pressed_color": self.pressed_color,
            "hover_color": self.hover_color
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Button":
        node = cls(data.get("name", "Button"))
        node.text = data.get("text", "Button")
        node.toggle_mode = data.get("toggle_mode", False)
        node.pressed = data.get("pressed", False)
        node.focus_mode = data.get("focus_mode", "all")
        node.normal_color = data.get("normal_color", [0.8, 0.8, 0.8, 1.0])
        node.pressed_color = data.get("pressed_color", [0.6, 0.6, 0.6, 1.0])
        node.hover_color = data.get("hover_color", [0.9, 0.9, 0.9, 1.0])

        # Label text override
        if data.get("child"):
            label_data = data.get("child")
            node.text_label = Label.from_dict(label_data)

        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
