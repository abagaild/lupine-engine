"""
scene/ui_nodes/item_list.py

Defines ItemList (scrollable list of selectable items).
"""

from typing import Dict, Any, List
from .control import Control


class ItemList(Control):
    """ItemList: displays a vertical list of items, single/multi-select."""

    def __init__(self, name: str = "ItemList"):
        super().__init__(name)
        self.type = "ItemList"

        self.items: List[str] = []
        self.select_mode: str = "single"   # single, multi
        self.allow_reselect: bool = False
        self.allow_rmb_select: bool = False
        self.max_text_lines: int = 1
        self.selected_items: List[int] = []
        self.icon_mode: str = "none"       # none, icon, bitmap
        self.icon_scale: float = 1.0
        self.fixed_icon_size: [float, float] = [16.0, 16.0]
        self.max_columns: int = 1
        self.same_column_width: bool = True
        self.fixed_column_width: float = 0.0
        self.item_spacing: float = 4.0
        self.line_separation: float = 4.0
        self.auto_height: bool = False
        self.scroll_position: float = 0.0
        self.background_color: [float, float, float, float] = [1.0, 1.0, 1.0, 1.0]
        self.item_color_normal: [float, float, float, float] = [0.0, 0.0, 0.0, 1.0]
        self.item_color_selected: [float, float, float, float] = [1.0, 1.0, 1.0, 1.0]
        self.item_color_hover: [float, float, float, float] = [0.8, 0.8, 0.8, 1.0]
        self.font: Any = None
        self.font_size: int = 14
        self.font_color: [float, float, float, float] = [0.0, 0.0, 0.0, 1.0]
        self.font_color_selected: [float, float, float, float] = [1.0, 1.0, 1.0, 1.0]

        self.script_path = "nodes/ui/ItemList.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "items": self.items,
            "select_mode": self.select_mode,
            "allow_reselect": self.allow_reselect,
            "allow_rmb_select": self.allow_rmb_select,
            "max_text_lines": self.max_text_lines,
            "selected_items": self.selected_items,
            "icon_mode": self.icon_mode,
            "icon_scale": self.icon_scale,
            "fixed_icon_size": self.fixed_icon_size,
            "max_columns": self.max_columns,
            "same_column_width": self.same_column_width,
            "fixed_column_width": self.fixed_column_width,
            "item_spacing": self.item_spacing,
            "line_separation": self.line_separation,
            "auto_height": self.auto_height,
            "scroll_position": self.scroll_position,
            "background_color": self.background_color,
            "item_color_normal": self.item_color_normal,
            "item_color_selected": self.item_color_selected,
            "item_color_hover": self.item_color_hover,
            "font": self.font,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "font_color_selected": self.font_color_selected
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemList":
        node = cls(data.get("name", "ItemList"))
        node.items = data.get("items", [])
        node.select_mode = data.get("select_mode", "single")
        node.allow_reselect = data.get("allow_reselect", False)
        node.allow_rmb_select = data.get("allow_rmb_select", False)
        node.max_text_lines = data.get("max_text_lines", 1)
        node.selected_items = data.get("selected_items", [])
        node.icon_mode = data.get("icon_mode", "none")
        node.icon_scale = data.get("icon_scale", 1.0)
        node.fixed_icon_size = data.get("fixed_icon_size", [16.0, 16.0])
        node.max_columns = data.get("max_columns", 1)
        node.same_column_width = data.get("same_column_width", True)
        node.fixed_column_width = data.get("fixed_column_width", 0.0)
        node.item_spacing = data.get("item_spacing", 4.0)
        node.line_separation = data.get("line_separation", 4.0)
        node.auto_height = data.get("auto_height", False)
        node.scroll_position = data.get("scroll_position", 0.0)
        node.background_color = data.get("background_color", [1.0, 1.0, 1.0, 1.0])
        node.item_color_normal = data.get("item_color_normal", [0.0, 0.0, 0.0, 1.0])
        node.item_color_selected = data.get("item_color_selected", [1.0, 1.0, 1.0, 1.0])
        node.item_color_hover = data.get("item_color_hover", [0.8, 0.8, 0.8, 1.0])
        node.font = data.get("font")
        node.font_size = data.get("font_size", 14)
        node.font_color = data.get("font_color", [0.0, 0.0, 0.0, 1.0])
        node.font_color_selected = data.get("font_color_selected", [1.0, 1.0, 1.0, 1.0])
        Control._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
