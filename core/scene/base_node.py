"""
scene/base_node.py

Defines the base Node class and shared serialization logic.
"""

import json
import copy
from typing import Dict, Any, List, Optional


class Node:
    """Base node class for scene hierarchy."""

    def __init__(self, name: str = "Node", node_type: str = "Node"):
        self.name = name
        self.type = node_type
        self.parent: Optional["Node"] = None
        self.children: List["Node"] = []
        self.properties: Dict[str, Any] = {}
        self.script_path: Optional[str] = None

        # Common properties
        self.visible: bool = True
        self.process_mode: str = "inherit"

    def add_child(self, child: "Node") -> None:
        """Add a child node, re-parenting if necessary."""
        if child.parent:
            child.parent.remove_child(child)

        child.parent = self
        self.children.append(child)

    def remove_child(self, child: "Node") -> None:
        """Remove a child node if present."""
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def get_child(self, name: str) -> Optional["Node"]:
        """Get a direct child by name."""
        for child in self.children:
            if child.name == name:
                return child
        return None

    def find_node(self, path: str) -> Optional["Node"]:
        """
        Recursively find a descendant node by slash-separated path
        (e.g. "Child/Grandchild").
        """
        if not path:
            return self

        if "/" not in path:
            return self.get_child(path)

        parts = path.split("/", 1)
        first, rest = parts[0], parts[1]
        child = self.get_child(first)
        if child:
            return child.find_node(rest)
        return None

    def get_path(self) -> str:
        """Return the full path from the root to this node."""
        if not self.parent:
            return self.name
        return f"{self.parent.get_path()}/{self.name}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert node into a JSON-serializable dict. Subclasses extend this.
        """
        data: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "visible": self.visible,
            "process_mode": self.process_mode,
            "properties": copy.deepcopy(self.properties),
            "children": [child.to_dict() for child in self.children]
        }
        if self.script_path:
            data["script"] = self.script_path
        return data

    @classmethod
    def _apply_node_properties(cls, node: "Node", data: Dict[str, Any]) -> None:
        """
        Apply common properties from a dict to an existing node instance
        (used during from_dict).
        """
        node.visible = data.get("visible", True)
        node.process_mode = data.get("process_mode", "inherit")
        node.properties = copy.deepcopy(data.get("properties", {}))
        script = data.get("script") or data.get("script_path")
        if script:
            node.script_path = str(script)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """
        Factory method: create a node (and its subtree) from a dict.
        Subclasses override this to handle type-specific fields.
        """
        # At the base level, instantiate a plain Node.
        node = cls(data.get("name", "Node"), data.get("type", "Node"))
        cls._apply_node_properties(node, data)

        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)

        return node
