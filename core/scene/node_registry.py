"""
scene/node_registry.py

Maintains a registry of all built-in and custom node definitions,
so that nodes can be instantiated by type name.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Type, Any

from .base_node import Node


class NodeRegistry:
    """
    Registry mapping node-type strings to their Python classes.
    Allows instantiating nodes by type name and loading custom script-based nodes.
    """

    def __init__(self):
        self._registry: Dict[str, Type[Node]] = {}

    def register_node(self, type_name: str, cls: Type[Node]) -> None:
        """
        Add or override a node-type mapping.  
        type_name: string used in serialized 'type' fields.  
        cls: the Python class implementing that node.
        """
        self._registry[type_name] = cls

    def unregister_node(self, type_name: str) -> None:
        """Remove a node type from the registry if present."""
        self._registry.pop(type_name, None)

    def create_node(self, type_name: str, name: Optional[str] = None) -> Optional[Node]:
        """
        Instantiate a node by type name.  
        If name is provided, set node.name accordingly; else default name from the class.
        """
        cls = self._registry.get(type_name)
        if not cls:
            return None
        node = cls(name or type_name)
        return node

    def get_registered_types(self) -> List[str]:
        """Return a list of all registered node-type strings."""
        return list(self._registry.keys())

    def load_custom_nodes(self, directory: Path) -> None:
        """
        Search for .py script files in `directory` (and subdirectories),
        parse their `class <ClassName>` declaration, and register them
        at runtime so that user-defined node types become available.
        """
        for root, _, files in os.walk(directory):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                script_path = Path(root) / fname
                with open(script_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                class_name = None
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("class "):
                        # e.g. "class Enemy(Node2D):"
                        parts = stripped.split()
                        if len(parts) >= 2:
                            class_name = parts[1]
                            if "(" in class_name:
                                class_name = class_name.split("(")[0]
                            if class_name.endswith(":"):
                                class_name = class_name[:-1]
                        break
                if class_name:
                    # For now, register a placeholder Node that records script path.
                    class PlaceholderNode(Node):
                        def __init__(self, name: str = class_name):
                            super().__init__(name, class_name)
                            self.script_path = str(script_path.relative_to(directory.parent))
                    self.register_node(class_name, PlaceholderNode)
