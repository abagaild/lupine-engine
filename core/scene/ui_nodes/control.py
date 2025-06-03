"""
scene/ui_nodes/control.py

Defines the base Control node (UI element with rectangular region).
"""

from typing import Dict, Any, List
from core.scene.base_node import Node


class Control(Node):
    """
    UI Control: requires rectangle-based layout (size/anchors/margins).
    """

    def __init__(self, name: str = "Control"):
        super().__init__(name, "Control")

        # Transform & layout properties
        self.position: [float, float] = [0.0, 0.0]
        self.rect_size: [float, float] = [100.0, 100.0]
        self.rect_min_size: [float, float] = [0.0, 0.0]

        # Anchors (0.0–1.0 normalized)
        self.anchor_left: float = 0.0
        self.anchor_top: float = 0.0
        self.anchor_right: float = 1.0
        self.anchor_bottom: float = 1.0

        # Margins (in pixels)
        self.margin_left: float = 0.0
        self.margin_top: float = 0.0
        self.margin_right: float = 0.0
        self.margin_bottom: float = 0.0

        # Behavior & styling
        self.size_flags: Dict[str, bool] = {"expand_h": False, "expand_v": False}
        self.clip_contents: bool = False
        self.mouse_filter: str = "pass"  # pass, ignore, stop
        self.focus_mode: str = "none"   # none, click, all
        self.theme: Any = None
        self.modulate: [float, float, float, float] = [1.0, 1.0, 1.0, 1.0]
        self.z_layer: int = 0

        self.script_path = "nodes/ui/Control.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "position": self.position,
            "rect_size": self.rect_size,
            "rect_min_size": self.rect_min_size,
            "anchor_left": self.anchor_left,
            "anchor_top": self.anchor_top,
            "anchor_right": self.anchor_right,
            "anchor_bottom": self.anchor_bottom,
            "margin_left": self.margin_left,
            "margin_top": self.margin_top,
            "margin_right": self.margin_right,
            "margin_bottom": self.margin_bottom,
            "size_flags": self.size_flags,
            "clip_contents": self.clip_contents,
            "mouse_filter": self.mouse_filter,
            "focus_mode": self.focus_mode,
            "theme": self.theme,
            "modulate": self.modulate,
            "z_layer": self.z_layer
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Control":
        node = cls(data.get("name", "Control"))
        node.position = data.get("position", [0.0, 0.0])
        node.rect_size = data.get("rect_size", [100.0, 100.0])
        node.rect_min_size = data.get("rect_min_size", [0.0, 0.0])
        node.anchor_left = data.get("anchor_left", 0.0)
        node.anchor_top = data.get("anchor_top", 0.0)
        node.anchor_right = data.get("anchor_right", 1.0)
        node.anchor_bottom = data.get("anchor_bottom", 1.0)
        node.margin_left = data.get("margin_left", 0.0)
        node.margin_top = data.get("margin_top", 0.0)
        node.margin_right = data.get("margin_right", 0.0)
        node.margin_bottom = data.get("margin_bottom", 0.0)
        node.size_flags = data.get("size_flags", {"expand_h": False, "expand_v": False})
        node.clip_contents = data.get("clip_contents", False)
        node.mouse_filter = data.get("mouse_filter", "pass")
        node.focus_mode = data.get("focus_mode", "none")
        node.theme = data.get("theme", None)
        node.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
        node.z_layer = data.get("z_layer", 0)
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
