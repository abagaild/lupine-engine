"""
scene/camera.py

Defines Camera2D node for viewport control and transforms.
"""

from typing import Dict, Any
from .node2d import Node2D


class Camera2D(Node2D):
    """2D camera node to control viewport and transforms."""

    def __init__(self, name: str = "Camera2D"):
        super().__init__(name)
        self.type = "Camera2D"

        # Camera state
        self.current: bool = False
        self.enabled: bool = True

        self.offset: [float, float] = [0.0, 0.0]
        self.zoom: float = 1.0
        self.smoothing_enabled: bool = False
        self.smoothing_speed: float = 5.0

        self.limit_left: float = -float("inf")
        self.limit_top: float = -float("inf")
        self.limit_right: float = float("inf")
        self.limit_bottom: float = float("inf")

        self.drag_margin_h_enabled: bool = False
        self.drag_margin_top_enabled: bool = False
        self.drag_margin_right_enabled: bool = False
        self.drag_margin_bottom_enabled: bool = False
        self.drag_margin_left: float = 0.0
        self.drag_margin_top: float = 0.0
        self.drag_margin_right: float = 0.0
        self.drag_margin_bottom: float = 0.0

        self.follow_smoothing: float = 0.0
        self.follow_h_offset: float = 0.0
        self.follow_v_offset: float = 0.0

        self.custom_viewport: Any = None

        self.script_path = "nodes/Camera2D.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "current": self.current,
            "enabled": self.enabled,
            "offset": self.offset,
            "zoom": self.zoom,
            "smoothing_enabled": self.smoothing_enabled,
            "smoothing_speed": self.smoothing_speed,
            "limit_left": self.limit_left,
            "limit_top": self.limit_top,
            "limit_right": self.limit_right,
            "limit_bottom": self.limit_bottom,
            "drag_margin_h_enabled": self.drag_margin_h_enabled,
            "drag_margin_top_enabled": self.drag_margin_top_enabled,
            "drag_margin_right_enabled": self.drag_margin_right_enabled,
            "drag_margin_bottom_enabled": self.drag_margin_bottom_enabled,
            "drag_margin_left": self.drag_margin_left,
            "drag_margin_top": self.drag_margin_top,
            "drag_margin_right": self.drag_margin_right,
            "drag_margin_bottom": self.drag_margin_bottom,
            "follow_smoothing": self.follow_smoothing,
            "follow_h_offset": self.follow_h_offset,
            "follow_v_offset": self.follow_v_offset,
            "custom_viewport": self.custom_viewport
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Camera2D":
        node = cls(data.get("name", "Camera2D"))
        node.current = data.get("current", False)
        node.enabled = data.get("enabled", True)
        node.offset = data.get("offset", [0.0, 0.0])
        node.zoom = data.get("zoom", 1.0)
        node.smoothing_enabled = data.get("smoothing_enabled", False)
        node.smoothing_speed = data.get("smoothing_speed", 5.0)
        node.limit_left = data.get("limit_left", -float("inf"))
        node.limit_top = data.get("limit_top", -float("inf"))
        node.limit_right = data.get("limit_right", float("inf"))
        node.limit_bottom = data.get("limit_bottom", float("inf"))
        node.drag_margin_h_enabled = data.get("drag_margin_h_enabled", False)
        node.drag_margin_top_enabled = data.get("drag_margin_top_enabled", False)
        node.drag_margin_right_enabled = data.get("drag_margin_right_enabled", False)
        node.drag_margin_bottom_enabled = data.get("drag_margin_bottom_enabled", False)
        node.drag_margin_left = data.get("drag_margin_left", 0.0)
        node.drag_margin_top = data.get("drag_margin_top", 0.0)
        node.drag_margin_right = data.get("drag_margin_right", 0.0)
        node.drag_margin_bottom = data.get("drag_margin_bottom", 0.0)
        node.follow_smoothing = data.get("follow_smoothing", 0.0)
        node.follow_h_offset = data.get("follow_h_offset", 0.0)
        node.follow_v_offset = data.get("follow_v_offset", 0.0)
        node.custom_viewport = data.get("custom_viewport")
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
