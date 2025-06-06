"""
scene/scene_manager.py

Defines Scene and SceneManager for loading/saving entire scenes.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from .base_node import Node


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
            node = cls._create_node_from_dict(node_data)
            scene.add_root_node(node)
        return scene

    @classmethod
    def _create_node_from_dict(cls, data: Dict[str, Any]) -> Node:
        """Create a node from dictionary data using proper node definitions"""
        node_type = data.get("type", "Node")
        node_name = data.get("name", "Node")

        # Check if this node has a script that should replace the node type
        script_path = data.get('script_path', '')
        if script_path:
            # Check if the script is one of our player controllers
            if 'TopDown4DirPlayerController.py' in script_path:
                try:
                    from nodes.prefabs.TopDown4DirPlayerController import TopDown4DirPlayerController
                    print(f"[DEBUG] Creating TopDown4DirPlayerController instance for {node_name}")
                    return TopDown4DirPlayerController.from_dict(data)
                except ImportError as e:
                    print(f"[WARNING] Failed to import TopDown4DirPlayerController: {e}")
                    pass
            elif 'TopDown8DirPlayerController.py' in script_path:
                try:
                    from nodes.prefabs.TopDown8DirPlayerController import TopDown8DirPlayerController
                    print(f"[DEBUG] Creating TopDown8DirPlayerController instance for {node_name}")
                    return TopDown8DirPlayerController.from_dict(data)
                except ImportError as e:
                    print(f"[WARNING] Failed to import TopDown8DirPlayerController: {e}")
                    pass
            elif 'PlatformerPlayerController.py' in script_path:
                try:
                    from nodes.prefabs.PlatformerPlayerController import PlatformerPlayerController
                    print(f"[DEBUG] Creating PlatformerPlayerController instance for {node_name}")
                    return PlatformerPlayerController.from_dict(data)
                except ImportError as e:
                    print(f"[WARNING] Failed to import PlatformerPlayerController: {e}")
                    pass

        # Try to use the proper node class from the nodes directory
        try:
            # Import the specific node class based on type
            if node_type == "Sprite":
                from nodes.node2d.Sprite import Sprite
                return Sprite.from_dict(data)
            elif node_type == "Sprite2D":
                from nodes.node2d.Sprite import Sprite
                return Sprite.from_dict(data)
            elif node_type == "Node2D":
                from core.scene.node2d import Node2D
                return Node2D.from_dict(data)
            elif node_type == "Camera2D":
                from nodes.node2d.Camera2D import Camera2D
                return Camera2D.from_dict(data)
            elif node_type == "AnimatedSprite":
                from nodes.node2d.AnimatedSprite import AnimatedSprite
                return AnimatedSprite.from_dict(data)
            elif node_type == "AnimationPlayer":
                from nodes.base.AnimationPlayer import AnimationPlayer
                return AnimationPlayer.from_dict(data)
            elif node_type == "KinematicBody2D":
                from nodes.node2d.KinematicBody2D import KinematicBody2D
                return KinematicBody2D.from_dict(data)
            elif node_type == "TopDown4DirPlayerController":
                from nodes.prefabs.TopDown4DirPlayerController import TopDown4DirPlayerController
                return TopDown4DirPlayerController.from_dict(data)
            elif node_type == "TopDown8DirPlayerController":
                from nodes.prefabs.TopDown8DirPlayerController import TopDown8DirPlayerController
                return TopDown8DirPlayerController.from_dict(data)
            elif node_type == "PlatformerPlayerController":
                from nodes.prefabs.PlatformerPlayerController import PlatformerPlayerController
                return PlatformerPlayerController.from_dict(data)
            elif node_type == "StaticBody2D":
                from nodes.node2d.StaticBody2D import StaticBody2D
                return StaticBody2D.from_dict(data)
            elif node_type == "RigidBody2D":
                from nodes.node2d.Rigidbody2D import RigidBody2D
                return RigidBody2D.from_dict(data)
            elif node_type == "Area2D":
                from nodes.node2d.Area2D import Area2D
                return Area2D.from_dict(data)
            elif node_type == "CollisionShape2D":
                from nodes.node2d.CollisionShape2D import CollisionShape2D
                return CollisionShape2D.from_dict(data)
            elif node_type == "CollisionPolygon2D":
                from nodes.node2d.CollisionPolygon2D import CollisionPolygon2D
                return CollisionPolygon2D.from_dict(data)
            # UI node types
            elif node_type == "Button":
                from nodes.ui.Button import Button
                return Button.from_dict(data)
            elif node_type == "Label":
                from nodes.ui.Label import Label
                return Label.from_dict(data)
            elif node_type == "Control":
                from nodes.ui.Control import Control
                return Control.from_dict(data)
            elif node_type == "Panel":
                from nodes.ui.Panel import Panel
                return Panel.from_dict(data)
            elif node_type == "ColorRect":
                from nodes.ui.ColorRect import ColorRect
                return ColorRect.from_dict(data)
            elif node_type == "TextureRect":
                from nodes.ui.TextureRect import TextureRect
                return TextureRect.from_dict(data)
            elif node_type == "NinePatchRect":
                from nodes.ui.NinePatchRect import NinePatchRect
                return NinePatchRect.from_dict(data)
            elif node_type == "VBoxContainer":
                from nodes.ui.VBoxContainer import VBoxContainer
                return VBoxContainer.from_dict(data)
            elif node_type == "HBoxContainer":
                from nodes.ui.HBoxContainer import HBoxContainer
                return HBoxContainer.from_dict(data)
            elif node_type == "ProgressBar":
                from nodes.ui.ProgressBar import ProgressBar
                return ProgressBar.from_dict(data)
            elif node_type == "CenterContainer":
                from nodes.ui.CenterContainer import CenterContainer
                return CenterContainer.from_dict(data)
            elif node_type == "LineEdit":
                from nodes.ui.LineEdit import LineEdit
                return LineEdit.from_dict(data)
            elif node_type == "CheckBox":
                from nodes.ui.CheckBox import CheckBox
                return CheckBox.from_dict(data)
            elif node_type == "AudioStreamPlayer":
                from nodes.audio.AudioStreamPlayer import AudioStreamPlayer
                return AudioStreamPlayer.from_dict(data)
            elif node_type == "SceneInstance":
                from .scene_instance import SceneInstance
                return SceneInstance.from_dict(data)
            elif node_type == "CollisionShape2D":
                from nodes.node2d.CollisionShape2D import CollisionShape2D
                return CollisionShape2D.from_dict(data)
            elif node_type == "CollisionPolygon2D":
                from nodes.node2d.CollisionPolygon2D import CollisionPolygon2D
                return CollisionPolygon2D.from_dict(data)
            elif node_type == "StaticBody2D":
                from nodes.node2d.StaticBody2D import StaticBody2D
                return StaticBody2D.from_dict(data)
            elif node_type == "KinematicBody2D":
                from nodes.node2d.KinematicBody2D import KinematicBody2D
                return KinematicBody2D.from_dict(data)
            elif node_type == "RigidBody2D":
                from nodes.node2d.Rigidbody2D import RigidBody2D
                return RigidBody2D.from_dict(data)
            elif node_type == "Area2D":
                from nodes.node2d.Area2D import Area2D
                return Area2D.from_dict(data)
            # Add more node types as needed
            else:
                # Fallback to base Node class
                node = Node(node_name, node_type)
                Node._apply_node_properties(node, data)

                # Handle children recursively
                for child_data in data.get("children", []):
                    child = cls._create_node_from_dict(child_data)
                    node.add_child(child)

                return node

        except ImportError as e:
            print(f"Could not import node class {node_type}: {e}")

            # Try to use the node registry for dynamic node creation
            try:
                from core.node_registry import get_node_registry
                registry = get_node_registry()
                node = registry.create_node_instance(node_type, node_name)
                if node:
                    # Apply properties from the data
                    Node._apply_node_properties(node, data)

                    # Handle children recursively
                    for child_data in data.get("children", []):
                        child = cls._create_node_from_dict(child_data)
                        node.add_child(child)

                    return node
            except Exception as registry_error:
                print(f"Node registry failed for {node_type}: {registry_error}")

            # Final fallback to base Node class
            node = Node(node_name, node_type)
            Node._apply_node_properties(node, data)

            # Handle children recursively
            for child_data in data.get("children", []):
                child = cls._create_node_from_dict(child_data)
                node.add_child(child)

            return node

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
        self.scene_instances: Dict[str, List[str]] = {}  # maps scene‐path → list of instance paths (for change tracking)

        # Enhanced caching and optimization
        self.scene_cache: Dict[str, Dict[str, Any]] = {}  # Cached scene metadata
        self.instance_pool: Dict[str, List[Any]] = {}  # Pooled instances for reuse
        self.dependency_graph: Dict[str, set] = {}  # Scene dependency tracking
        self.file_watchers: Dict[str, Any] = {}  # File system watchers for auto-reload
        self.loading_queue: List[str] = []  # Async loading queue
        self.performance_metrics: Dict[str, Any] = {}  # Performance tracking

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
        from .node2d import Node2D
        scene = Scene(name)
        root = Node2D(name)
        scene.add_root_node(root)
        return scene

    def instantiate_scene(self, scene_path: str, instance_name: Optional[str] = None) -> Optional[Node]:
        """
        Instantiate a scene as a node that can be added to another scene.
        Returns the root node of the instantiated scene with scene instance metadata.
        """
        # Load the scene
        scene = self.load_scene(scene_path)
        if not scene:
            return None

        # Check for circular dependencies
        if self._has_circular_dependency(scene_path):
            print(f"Warning: Circular dependency detected for scene {scene_path}")
            return None

        # Create a scene instance node
        from .scene_instance import SceneInstance
        instance = SceneInstance(instance_name or scene.name)
        instance.scene_path = scene_path
        instance.original_scene = scene

        # Clone the scene's root nodes as children of the instance
        for root_node in scene.root_nodes:
            cloned_node = self._clone_node_tree(root_node)
            instance.add_child(cloned_node)

        # Track this instance for change detection
        if scene_path not in self.scene_instances:
            self.scene_instances[scene_path] = []
        self.scene_instances[scene_path].append(instance.get_instance_id())

        return instance

    def _has_circular_dependency(self, scene_path: str, visited: Optional[set] = None) -> bool:
        """Check if loading this scene would create a circular dependency."""
        if visited is None:
            visited = set()

        if scene_path in visited:
            return True

        visited.add(scene_path)

        # Load scene and check for scene instances
        scene = self.load_scene(scene_path)
        if not scene:
            return False

        # Recursively check all scene instances in this scene
        for root_node in scene.root_nodes:
            if self._check_node_for_scene_instances(root_node, visited):
                return True

        visited.remove(scene_path)
        return False

    def _check_node_for_scene_instances(self, node: Node, visited: set) -> bool:
        """Recursively check a node tree for scene instances that could cause circular dependencies."""
        # Check if this node is a scene instance
        if hasattr(node, 'scene_path') and node.scene_path:
            if self._has_circular_dependency(node.scene_path, visited.copy()):
                return True

        # Check children
        for child in node.children:
            if self._check_node_for_scene_instances(child, visited):
                return True

        return False

    def _clone_node_tree(self, node: Node) -> Node:
        """Create a deep copy of a node and its entire subtree."""
        # Convert to dict and back to create a deep copy
        node_data = node.to_dict()
        cloned_node = Scene._create_node_from_dict(node_data)
        return cloned_node

    def get_available_scenes(self) -> List[str]:
        """Get a list of all available scene files in the project."""
        scenes_dir = self.project.get_absolute_path("scenes")
        if not scenes_dir.exists():
            return []

        scene_files = []
        for scene_file in scenes_dir.glob("*.scene"):
            # Get relative path from project root
            relative_path = f"scenes/{scene_file.name}"
            scene_files.append(relative_path)

        return sorted(scene_files)

    def reload_scene_instances(self, scene_path: str) -> None:
        """Reload all instances of a scene when the original scene changes."""
        if scene_path not in self.scene_instances:
            return

        # Reload the original scene
        if scene_path in self.loaded_scenes:
            del self.loaded_scenes[scene_path]

        updated_scene = self.load_scene(scene_path)
        if not updated_scene:
            return

        # TODO: Update all instances of this scene
        # This would require tracking actual instance objects, not just IDs
        print(f"Scene {scene_path} changed, instances should be updated")

    # ========== ENHANCED SCENE MANAGEMENT ==========

    def preload_scene(self, scene_path: str, priority: int = 0) -> bool:
        """
        Preload a scene into cache without instantiating it.
        Higher priority scenes are loaded first.
        """
        if scene_path in self.loaded_scenes:
            return True

        try:
            # Add to loading queue with priority
            if scene_path not in self.loading_queue:
                self.loading_queue.append(scene_path)
                self.loading_queue.sort(key=lambda x: self.get_scene_priority(x), reverse=True)

            # Load scene metadata first
            metadata = self._load_scene_metadata(scene_path)
            if metadata:
                self.scene_cache[scene_path] = metadata

            # Load the actual scene
            scene = self.load_scene(scene_path)
            return scene is not None

        except Exception as e:
            print(f"Error preloading scene {scene_path}: {e}")
            return False

    def get_scene_priority(self, scene_path: str) -> int:
        """Get loading priority for a scene (higher = more important)"""
        # Main scene gets highest priority
        if scene_path == self.project.get_main_scene():
            return 100

        # Frequently used scenes get higher priority
        usage_count = self.performance_metrics.get(scene_path, {}).get('usage_count', 0)
        return min(50 + usage_count, 99)

    def _load_scene_metadata(self, scene_path: str) -> Optional[Dict[str, Any]]:
        """Load lightweight scene metadata without full scene loading"""
        try:
            full_path = self.project.get_absolute_path(scene_path)
            if not full_path.exists():
                return None

            # Read just the header of the scene file for metadata
            with open(full_path, 'r') as f:
                import json
                data = json.load(f)

            metadata = {
                'name': data.get('name', ''),
                'node_count': self._count_nodes_recursive(data.get('nodes', [])),
                'dependencies': self._extract_scene_dependencies(data),
                'file_size': full_path.stat().st_size,
                'modified_time': full_path.stat().st_mtime,
                'complexity_score': self._calculate_complexity_score(data)
            }

            return metadata

        except Exception as e:
            print(f"Error loading metadata for {scene_path}: {e}")
            return None

    def _count_nodes_recursive(self, nodes: List[Dict]) -> int:
        """Count total nodes in a scene hierarchy"""
        count = len(nodes)
        for node in nodes:
            count += self._count_nodes_recursive(node.get('children', []))
        return count

    def _extract_scene_dependencies(self, scene_data: Dict) -> List[str]:
        """Extract scene dependencies (other scenes referenced by this scene)"""
        dependencies = []

        def find_scene_instances(nodes):
            for node in nodes:
                if node.get('type') == 'SceneInstance':
                    scene_path = node.get('scene_path', '')
                    if scene_path and scene_path not in dependencies:
                        dependencies.append(scene_path)

                # Recursively check children
                find_scene_instances(node.get('children', []))

        find_scene_instances(scene_data.get('nodes', []))
        return dependencies

    def _calculate_complexity_score(self, scene_data: Dict) -> int:
        """Calculate a complexity score for the scene (for optimization decisions)"""
        score = 0

        # Base score from node count
        node_count = self._count_nodes_recursive(scene_data.get('nodes', []))
        score += node_count

        # Additional score for complex node types
        def add_complexity(nodes):
            nonlocal score
            for node in nodes:
                node_type = node.get('type', '')
                if node_type in ['SceneInstance', 'AnimationPlayer', 'ParticleSystem']:
                    score += 5
                elif node_type in ['Sprite', 'AudioStreamPlayer']:
                    score += 2

                add_complexity(node.get('children', []))

        add_complexity(scene_data.get('nodes', []))
        return score

    def build_dependency_graph(self) -> None:
        """Build a dependency graph of all scenes in the project"""
        self.dependency_graph.clear()

        # Get all scene files
        scenes = self.get_available_scenes()

        for scene_path in scenes:
            metadata = self.scene_cache.get(scene_path)
            if not metadata:
                metadata = self._load_scene_metadata(scene_path)
                if metadata:
                    self.scene_cache[scene_path] = metadata

            if metadata:
                dependencies = metadata.get('dependencies', [])
                self.dependency_graph[scene_path] = set(dependencies)

    def get_scene_dependents(self, scene_path: str) -> List[str]:
        """Get all scenes that depend on the given scene"""
        dependents = []
        for scene, deps in self.dependency_graph.items():
            if scene_path in deps:
                dependents.append(scene)
        return dependents

    def validate_scene_dependencies(self) -> Dict[str, List[str]]:
        """Validate all scene dependencies and return any issues"""
        issues = {}

        for scene_path, dependencies in self.dependency_graph.items():
            scene_issues = []

            # Check for missing dependencies
            for dep in dependencies:
                if not self.project.get_absolute_path(dep).exists():
                    scene_issues.append(f"Missing dependency: {dep}")

            # Check for circular dependencies
            if self._has_circular_dependency(scene_path):
                scene_issues.append("Circular dependency detected")

            if scene_issues:
                issues[scene_path] = scene_issues

        return issues

    # ========== ADVANCED INSTANCE MANAGEMENT ==========

    def create_instance_pool(self, scene_path: str, pool_size: int = 5) -> bool:
        """Create a pool of pre-instantiated scene instances for performance"""
        try:
            if scene_path not in self.instance_pool:
                self.instance_pool[scene_path] = []

            # Create pool instances
            for _ in range(pool_size):
                instance = self.instantiate_scene(scene_path, f"pooled_instance_{len(self.instance_pool[scene_path])}")
                if instance:
                    instance._is_pooled = True
                    instance._is_active = False
                    self.instance_pool[scene_path].append(instance)

            return True

        except Exception as e:
            print(f"Error creating instance pool for {scene_path}: {e}")
            return False

    def get_pooled_instance(self, scene_path: str, instance_name: Optional[str] = None) -> Optional[Node]:
        """Get an instance from the pool or create a new one"""
        # Try to get from pool first
        if scene_path in self.instance_pool and self.instance_pool[scene_path]:
            instance = self.instance_pool[scene_path].pop()
            instance._is_active = True
            if instance_name:
                instance.name = instance_name
            return instance

        # Create new instance if pool is empty
        return self.instantiate_scene(scene_path, instance_name)

    def return_to_pool(self, instance: Node) -> bool:
        """Return an instance to the pool for reuse"""
        if not hasattr(instance, '_is_pooled') or not instance._is_pooled:
            return False

        try:
            scene_path = getattr(instance, 'scene_path', '')
            if scene_path and scene_path in self.instance_pool:
                # Reset instance state
                instance._is_active = False
                instance.reset_to_default_state()

                # Return to pool
                self.instance_pool[scene_path].append(instance)
                return True

        except Exception as e:
            print(f"Error returning instance to pool: {e}")

        return False

    def instantiate_scene_async(self, scene_path: str, callback=None, instance_name: Optional[str] = None) -> str:
        """
        Asynchronously instantiate a scene and call callback when complete.
        Returns a request ID for tracking.
        """
        import threading
        import uuid

        request_id = str(uuid.uuid4())

        def load_async():
            try:
                instance = self.instantiate_scene(scene_path, instance_name)
                if callback:
                    callback(instance, None, request_id)
            except Exception as e:
                if callback:
                    callback(None, e, request_id)

        thread = threading.Thread(target=load_async)
        thread.daemon = True
        thread.start()

        return request_id

    def batch_instantiate_scenes(self, scene_requests: List[Dict[str, Any]]) -> List[Optional[Node]]:
        """
        Batch instantiate multiple scenes efficiently.
        scene_requests: List of dicts with 'scene_path' and optional 'instance_name'
        """
        # Group by scene path for optimization
        grouped_requests = {}
        for i, request in enumerate(scene_requests):
            scene_path = request['scene_path']
            if scene_path not in grouped_requests:
                grouped_requests[scene_path] = []
            grouped_requests[scene_path].append((i, request))

        # Process each scene type
        results: List[Optional[Node]] = [None] * len(scene_requests)

        for scene_path, requests in grouped_requests.items():
            # Preload scene once for all instances
            scene = self.load_scene(scene_path)
            if not scene:
                continue

            # Create instances
            for original_index, request in requests:
                instance_name = request.get('instance_name')
                instance = self.instantiate_scene(scene_path, instance_name)
                results[original_index] = instance

        return results

    def get_instance_statistics(self) -> Dict[str, Any]:
        """Get statistics about scene instances"""
        stats = {
            'total_loaded_scenes': len(self.loaded_scenes),
            'total_instance_pools': len(self.instance_pool),
            'scene_usage': {},
            'memory_usage': {},
            'performance_metrics': self.performance_metrics.copy()
        }

        # Calculate usage statistics
        for scene_path, instances in self.scene_instances.items():
            stats['scene_usage'][scene_path] = {
                'instance_count': len(instances),
                'pool_size': len(self.instance_pool.get(scene_path, [])),
                'dependencies': len(self.dependency_graph.get(scene_path, set())),
                'dependents': len(self.get_scene_dependents(scene_path))
            }

        return stats

    def optimize_memory_usage(self) -> Dict[str, Any]:
        """Optimize memory usage by cleaning up unused scenes and instances"""
        optimization_report = {
            'scenes_unloaded': 0,
            'instances_pooled': 0,
            'memory_freed': 0
        }

        # Unload rarely used scenes
        current_time = time.time()
        for scene_path in list(self.loaded_scenes.keys()):
            last_used = self.performance_metrics.get(scene_path, {}).get('last_used', 0)
            if current_time - last_used > 300:  # 5 minutes
                del self.loaded_scenes[scene_path]
                optimization_report['scenes_unloaded'] += 1

        # Trim oversized instance pools
        for scene_path, pool in self.instance_pool.items():
            if len(pool) > 10:  # Keep max 10 pooled instances
                excess = pool[10:]
                self.instance_pool[scene_path] = pool[:10]
                optimization_report['instances_pooled'] += len(excess)

        return optimization_report
