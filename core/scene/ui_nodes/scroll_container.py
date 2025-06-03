"""
scene/ui_nodes/scroll_container.py

Defines ScrollContainer (enables scrolling for its single child).
"""

from typing import Dict, Any
from .control import Control


class ScrollContainer(Control):
    """ScrollContainer: provides scrollbars for its single child control."""

    def __init__(self, name: str = "ScrollContainer"):
        super().__init__(name)
        self.type = "ScrollContainer"

        self.scroll_v_enabled: bool = True
        self.scroll_h_enabled: bool = False
        self.scroll_speed: float = 1.0
        self.scroll_offset: [float, float] = [0.0, 0.0]

        self.script_path = "nodes/ui/ScrollContainer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "scroll_v_enabled": self.scroll_v_enabled,
            "scroll_h_enabled": self.scroll_h_enabled,
            "scroll_speed": self.scroll_speed,
            "scroll_offset": self.scroll_offset
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScrollContainer":
        node = cls(data.get("name", "ScrollContainer"))
        node.scroll_v_enabled = data.get("scroll_v_enabled", True)
        node.scroll_h_enabled = data.get("scroll_h_enabled", False)
        node.scroll_speed = data.get("scroll_speed", 1.0)
        node.scroll_offset = data.get("scroll_offset", [0.0, 0.0])
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
