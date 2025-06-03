"""
scene/ui_nodes/canvas_layer.py

Defines CanvasLayer (independent UI/effects layer).
"""

from typing import Dict, Any
from .control import Control


class CanvasLayer(Control):
    """
    CanvasLayer: a separate drawing layer for UI or effects,
    can follow or not follow the main viewport.
    """

    def __init__(self, name: str = "CanvasLayer"):
        super().__init__(name)
        self.type = "CanvasLayer"

        # Layer properties
        self.layer: int = 1  # Z-order index

        # Transform for the entire layer
        self.offset: [float, float] = [0.0, 0.0]
        self.rotation: float = 0.0
        self.scale: [float, float] = [1.0, 1.0]

        # Viewport following
        self.follow_viewport_enable: bool = False
        self.follow_viewport_scale: float = 1.0

        # Custom viewport definition (if not following)
        self.custom_viewport: Any = None

        self.script_path = "nodes/ui/CanvasLayer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "layer": self.layer,
            "offset": self.offset,
            "rotation": self.rotation,
            "scale": self.scale,
            "follow_viewport_enable": self.follow_viewport_enable,
            "follow_viewport_scale": self.follow_viewport_scale,
            "custom_viewport": self.custom_viewport
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanvasLayer":
        node = cls(data.get("name", "CanvasLayer"))
        node.layer = data.get("layer", 1)
        node.offset = data.get("offset", [0.0, 0.0])
        node.rotation = data.get("rotation", 0.0)
        node.scale = data.get("scale", [1.0, 1.0])
        node.follow_viewport_enable = data.get("follow_viewport_enable", False)
        node.follow_viewport_scale = data.get("follow_viewport_scale", 1.0)
        node.custom_viewport = data.get("custom_viewport")
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
