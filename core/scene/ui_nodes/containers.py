"""
scene/ui_nodes/containers.py

Defines container nodes: VBoxContainer, HBoxContainer, CenterContainer, GridContainer.
"""

from typing import Dict, Any
from .control import Control


class VBoxContainer(Control):
    """Vertical box container: auto‐arranges children vertically."""

    def __init__(self, name: str = "VBoxContainer"):
        super().__init__(name)
        self.type = "VBoxContainer"

        self.align: str = "fill"  # begin, center, end, fill
        self.separation: float = 4.0
        self.padding_top: float = 4.0
        self.padding_bottom: float = 4.0
        self.padding_left: float = 4.0
        self.padding_right: float = 4.0

        self.script_path = "nodes/ui/VBoxContainer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "align": self.align,
            "separation": self.separation,
            "padding_top": self.padding_top,
            "padding_bottom": self.padding_bottom,
            "padding_left": self.padding_left,
            "padding_right": self.padding_right
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VBoxContainer":
        node = cls(data.get("name", "VBoxContainer"))
        node.align = data.get("align", "fill")
        node.separation = data.get("separation", 4.0)
        node.padding_top = data.get("padding_top", 4.0)
        node.padding_bottom = data.get("padding_bottom", 4.0)
        node.padding_left = data.get("padding_left", 4.0)
        node.padding_right = data.get("padding_right", 4.0)
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class HBoxContainer(Control):
    """Horizontal box container: auto‐arranges children horizontally."""

    def __init__(self, name: str = "HBoxContainer"):
        super().__init__(name)
        self.type = "HBoxContainer"

        self.align: str = "fill"  # begin, center, end, fill
        self.separation: float = 4.0
        self.padding_top: float = 4.0
        self.padding_bottom: float = 4.0
        self.padding_left: float = 4.0
        self.padding_right: float = 4.0

        self.script_path = "nodes/ui/HBoxContainer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "align": self.align,
            "separation": self.separation,
            "padding_top": self.padding_top,
            "padding_bottom": self.padding_bottom,
            "padding_left": self.padding_left,
            "padding_right": self.padding_right
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HBoxContainer":
        node = cls(data.get("name", "HBoxContainer"))
        node.align = data.get("align", "fill")
        node.separation = data.get("separation", 4.0)
        node.padding_top = data.get("padding_top", 4.0)
        node.padding_bottom = data.get("padding_bottom", 4.0)
        node.padding_left = data.get("padding_left", 4.0)
        node.padding_right = data.get("padding_right", 4.0)
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class CenterContainer(Control):
    """Centers children within its bounds (both axes)."""

    def __init__(self, name: str = "CenterContainer"):
        super().__init__(name)
        self.type = "CenterContainer"

        self.preserve_top: bool = True
        self.preserve_bottom: bool = True
        self.preserve_left: bool = True
        self.preserve_right: bool = True

        self.script_path = "nodes/ui/CenterContainer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "preserve_top": self.preserve_top,
            "preserve_bottom": self.preserve_bottom,
            "preserve_left": self.preserve_left,
            "preserve_right": self.preserve_right
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CenterContainer":
        node = cls(data.get("name", "CenterContainer"))
        node.preserve_top = data.get("preserve_top", True)
        node.preserve_bottom = data.get("preserve_bottom", True)
        node.preserve_left = data.get("preserve_left", True)
        node.preserve_right = data.get("preserve_right", True)
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node


class GridContainer(Control):
    """Grid container: arranges children in a grid pattern."""

    def __init__(self, name: str = "GridContainer"):
        super().__init__(name)
        self.type = "GridContainer"

        self.columns: int = 1
        self.h_separation: float = 4.0
        self.v_separation: float = 4.0

        self.container_margin_left: float = 0.0
        self.container_margin_top: float = 0.0
        self.container_margin_right: float = 0.0
        self.container_margin_bottom: float = 0.0

        self.background_color: [float, float, float, float] = [0.0, 0.0, 0.0, 0.0]
        self.border_color: [float, float, float, float] = [0.5, 0.5, 0.5, 1.0]
        self.border_width: float = 0.0
        self.corner_radius: float = 0.0

        self.script_path = "nodes/ui/GridContainer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "columns": self.columns,
            "h_separation": self.h_separation,
            "v_separation": self.v_separation,
            "container_margin_left": self.container_margin_left,
            "container_margin_top": self.container_margin_top,
            "container_margin_right": self.container_margin_right,
            "container_margin_bottom": self.container_margin_bottom,
            "background_color": self.background_color,
            "border_color": self.border_color,
            "border_width": self.border_width,
            "corner_radius": self.corner_radius
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridContainer":
        node = cls(data.get("name", "GridContainer"))
        node.columns = data.get("columns", 1)
        node.h_separation = data.get("h_separation", 4.0)
        node.v_separation = data.get("v_separation", 4.0)
        node.container_margin_left = data.get("container_margin_left", 0.0)
        node.container_margin_top = data.get("container_margin_top", 0.0)
        node.container_margin_right = data.get("container_margin_right", 0.0)
        node.container_margin_bottom = data.get("container_margin_bottom", 0.0)
        node.background_color = data.get("background_color", [0.0, 0.0, 0.0, 0.0])
        node.border_color = data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        node.border_width = data.get("border_width", 0.0)
        node.corner_radius = data.get("corner_radius", 0.0)
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
