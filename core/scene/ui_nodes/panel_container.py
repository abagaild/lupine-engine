"""
scene/ui_nodes/panel_container.py

Defines PanelContainer (holds a single control with clipping).
"""

from typing import Dict, Any
from .control import Control


class PanelContainer(Control):
    """PanelContainer: places a single child control with a panel background."""

    def __init__(self, name: str = "PanelContainer"):
        super().__init__(name)
        self.type = "PanelContainer"

        self.use_custom_minimum_size: bool = False
        self.custom_minimum_size: [float, float] = [0.0, 0.0]

        self.script_path = "nodes/ui/PanelContainer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "use_custom_minimum_size": self.use_custom_minimum_size,
            "custom_minimum_size": self.custom_minimum_size
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PanelContainer":
        node = cls(data.get("name", "PanelContainer"))
        node.use_custom_minimum_size = data.get("use_custom_minimum_size", False)
        node.custom_minimum_size = data.get("custom_minimum_size", [0.0, 0.0])
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
