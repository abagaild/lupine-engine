"""
scene/scene_manager.py

Defines Scene and SceneManager for loading/saving entire scenes.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base_node import Node
from .node2d import Node2D


class Scene:
    """Represents a complete scene (collection of root nodes)."""

    def __init__(self, name: str = "Scene"):
        self.name: str = name
        self.root_nodes: List[Node] = []
        self.metadata: Dict[str, Any] = {}

    def add_root_node(self, node: Node) -> None:
        """Add a node as a new root in the scene."""
        self.root_nodes.append(node)

    def remove_root_node(self, node: Node) -> None:
        """Remove a root node if present."""
        if node in self.root_nodes:
            self.root_nodes.remove(node)

    def find_node(self, path: str) -> Optional[Node]:
        """
        Find a node by path, where path is either a single root name
        or "Root/Child/Subchild".
        """
        if "/" not in path:
            for root in self.root_nodes:
                if root.name == path:
                    return root
            return None

        parts = path.split("/", 1)
        root_name, remainder = parts[0], parts[1]
        for root in self.root_nodes:
            if root.name == root_name:
                return root.find_node(remainder)
        return None

    def get_all_nodes(self) -> List[Node]:
        """Return a flattened list of all nodes in the scene."""
        nodes: List[Node] = []

        def collect(n: Node):
            nodes.append(n)
            for c in n.children:
                collect(c)

        for r in self.root_nodes:
            collect(r)
        return nodes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "metadata": self.metadata,
            "nodes": [root.to_dict() for root in self.root_nodes]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scene":
        scene = cls(data.get("name", "Scene"))
        scene.metadata = data.get("metadata", {})
        for node_data in data.get("nodes", []):
            node = Node.from_dict(node_data)
            scene.add_root_node(node)
        return scene

    def save_to_file(self, file_path: str) -> None:
        from ..json_utils import safe_json_dump

        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            safe_json_dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: str) -> Optional["Scene"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Failed to load scene from {file_path}: {e}")
            return None


class SceneManager:
    """Manages loading, caching, saving, and switching between Scene files."""

    def __init__(self, project: Any):
        self.project = project
        self.current_scene: Optional[Scene] = None
        self.loaded_scenes: Dict[str, Scene] = {}  # maps scene‐path → Scene instance

    def load_scene(self, scene_path: str) -> Optional[Scene]:
        """
        Load a scene from the given project‐relative path (e.g. "scenes/Main.scene").
        Caches loaded scenes.
        """
        if scene_path in self.loaded_scenes:
            return self.loaded_scenes[scene_path]

        full_path = self.project.get_absolute_path(scene_path)
        scene = Scene.load_from_file(str(full_path))
        if scene:
            self.loaded_scenes[scene_path] = scene
        return scene

    def save_scene(self, scene: Scene, scene_path: str) -> None:
        """Save the given Scene instance to the given path (project‐relative)."""
        full_path = self.project.get_absolute_path(scene_path)
        scene.save_to_file(str(full_path))
        self.loaded_scenes[scene_path] = scene

    def set_current_scene(self, scene_path: str) -> bool:
        """Set (and load, if necessary) the current active scene."""
        scene = self.load_scene(scene_path)
        if scene:
            self.current_scene = scene
            return True
        return False

    def get_current_scene(self) -> Optional[Scene]:
        """Return the active Scene, or None if none set."""
        return self.current_scene

    def create_new_scene(self, name: str) -> Scene:
        """Create a new, empty scene with a default Node2D root."""
        scene = Scene(name)
        root = Node2D(name)
        scene.add_root_node(root)
        return scene
