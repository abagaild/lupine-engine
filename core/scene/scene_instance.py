"""
Scene Instance Node for Lupine Engine
Represents an instance of another scene that can be embedded in the current scene
"""

import uuid
from typing import Dict, Any, Optional, List
from .base_node import Node


class SceneInstance(Node):
    """
    A node that represents an instance of another scene.
    Similar to Godot's scene instancing system.
    """

    def __init__(self, name: str = "SceneInstance"):
        super().__init__(name, "SceneInstance")
        
        # Scene instance properties
        self.scene_path: str = ""  # Path to the scene file to instance
        self.original_scene = None  # Reference to the original scene object
        self.instance_id: str = str(uuid.uuid4())  # Unique identifier for this instance
        self.property_overrides: Dict[str, Any] = {}  # Properties that override the original scene
        self.editable_children: bool = False  # Whether children can be edited in this instance
        
        # Export variables for editor
        self.export_variables = {
            "scene_path": {
                "type": "path",
                "value": "",
                "description": "Path to the scene file to instance",
                "filter": "*.scene"
            },
            "editable_children": {
                "type": "bool",
                "value": False,
                "description": "Allow editing children of this scene instance"
            }
        }

    def get_instance_id(self) -> str:
        """Get the unique instance ID."""
        return self.instance_id

    def set_scene_path(self, path: str) -> None:
        """Set the path to the scene to instance."""
        self.scene_path = path
        self.export_variables["scene_path"]["value"] = path

    def get_scene_path(self) -> str:
        """Get the path to the instanced scene."""
        return self.scene_path

    def set_property_override(self, node_path: str, property_name: str, value: Any) -> None:
        """
        Set a property override for a specific node in the instanced scene.
        node_path: Path to the node within the instance (e.g., "Player/Sprite")
        property_name: Name of the property to override
        value: New value for the property
        """
        if node_path not in self.property_overrides:
            self.property_overrides[node_path] = {}
        self.property_overrides[node_path][property_name] = value

    def get_property_override(self, node_path: str, property_name: str) -> Any:
        """Get a property override value, or None if not overridden."""
        return self.property_overrides.get(node_path, {}).get(property_name)

    def has_property_override(self, node_path: str, property_name: str) -> bool:
        """Check if a property is overridden for a specific node."""
        return node_path in self.property_overrides and property_name in self.property_overrides[node_path]

    def clear_property_overrides(self) -> None:
        """Clear all property overrides."""
        self.property_overrides.clear()

    def apply_property_overrides(self) -> None:
        """Apply property overrides to the instanced nodes."""
        for node_path, overrides in self.property_overrides.items():
            target_node = self._find_node_by_path(node_path)
            if target_node:
                for property_name, value in overrides.items():
                    if hasattr(target_node, property_name):
                        setattr(target_node, property_name, value)

    def _find_node_by_path(self, node_path: str) -> Optional[Node]:
        """Find a node by its path within this instance."""
        if not node_path:
            return self
        
        path_parts = node_path.split("/")
        current_node = self
        
        for part in path_parts:
            found = False
            for child in current_node.children:
                if child.name == part:
                    current_node = child
                    found = True
                    break
            if not found:
                return None
        
        return current_node

    def get_original_scene_root(self) -> Optional[Node]:
        """Get the root node of the original scene."""
        if self.original_scene and self.original_scene.root_nodes:
            return self.original_scene.root_nodes[0]
        return None

    def is_scene_instance(self) -> bool:
        """Check if this node is a scene instance."""
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        data = super().to_dict()
        data.update({
            "scene_path": self.scene_path,
            "instance_id": self.instance_id,
            "property_overrides": dict(self.property_overrides),  # Ensure it's a plain dict
            "editable_children": self.editable_children
        })
        # Note: We don't serialize original_scene as it would cause circular references
        # Remove the original_scene from properties if it exists to avoid circular references
        if "original_scene" in data.get("properties", {}):
            del data["properties"]["original_scene"]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneInstance":
        """Create SceneInstance from dictionary data."""
        instance = cls(data.get("name", "SceneInstance"))
        
        # Apply base node properties
        cls._apply_node_properties(instance, data)
        
        # Apply scene instance specific properties
        instance.scene_path = data.get("scene_path", "")
        instance.instance_id = data.get("instance_id", str(uuid.uuid4()))
        instance.property_overrides = data.get("property_overrides", {})
        instance.editable_children = data.get("editable_children", False)
        
        # Update export variables
        instance.export_variables["scene_path"]["value"] = instance.scene_path
        instance.export_variables["editable_children"]["value"] = instance.editable_children
        
        return instance

    def reload_from_scene(self, scene_manager) -> bool:
        """
        Reload this instance from its original scene file.
        Returns True if successful, False otherwise.
        """
        if not self.scene_path:
            return False
        
        # Clear existing children
        self.children.clear()
        
        # Load the scene again
        scene = scene_manager.load_scene(self.scene_path)
        if not scene:
            return False
        
        self.original_scene = scene
        
        # Clone the scene's root nodes as children
        for root_node in scene.root_nodes:
            cloned_node = scene_manager._clone_node_tree(root_node)
            self.add_child(cloned_node)
        
        # Reapply property overrides
        self.apply_property_overrides()
        
        return True

    # ========== ADVANCED SCENE INSTANCE FEATURES ==========

    def create_variant(self, variant_name: str) -> "SceneInstance":
        """Create a variant of this scene instance with the same overrides"""
        variant = SceneInstance(variant_name)
        variant.scene_path = self.scene_path
        variant.property_overrides = self.property_overrides.copy()
        variant.editable_children = self.editable_children

        # Load the scene content
        if self.scene_path:
            variant.reload_from_scene(self._get_scene_manager())

        return variant

    def merge_overrides(self, other_overrides: Dict[str, Any]) -> None:
        """Merge additional property overrides into this instance"""
        for node_path, overrides in other_overrides.items():
            if node_path not in self.property_overrides:
                self.property_overrides[node_path] = {}
            self.property_overrides[node_path].update(overrides)

        # Apply the merged overrides
        self.apply_property_overrides()

    def get_override_diff(self) -> Dict[str, Any]:
        """Get a diff of all property overrides compared to the original scene"""
        diff = {}

        if not self.original_scene:
            return diff

        # Compare current state with original scene
        for node_path, overrides in self.property_overrides.items():
            target_node = self._find_node_by_path(node_path)
            if target_node:
                node_diff = {}
                for prop_name, override_value in overrides.items():
                    # Get original value from scene
                    original_value = self._get_original_property_value(node_path, prop_name)
                    if original_value != override_value:
                        node_diff[prop_name] = {
                            'original': original_value,
                            'override': override_value
                        }

                if node_diff:
                    diff[node_path] = node_diff

        return diff

    def _get_original_property_value(self, node_path: str, property_name: str) -> Any:
        """Get the original property value from the source scene"""
        if not self.original_scene:
            return None

        # Find the corresponding node in the original scene
        original_node = self._find_original_node(node_path)
        if original_node and hasattr(original_node, property_name):
            return getattr(original_node, property_name)

        return None

    def _find_original_node(self, node_path: str) -> Optional[Node]:
        """Find a node in the original scene by path"""
        if not self.original_scene or not node_path:
            return None

        # Start from root nodes
        path_parts = node_path.split("/")
        current_nodes = self.original_scene.root_nodes

        for part in path_parts:
            found = False
            for node in current_nodes:
                if node.name == part:
                    if part == path_parts[-1]:  # Last part
                        return node
                    current_nodes = node.children
                    found = True
                    break
            if not found:
                return None

        return None

    def reset_to_default_state(self) -> None:
        """Reset the instance to its default state (for pooling)"""
        # Clear property overrides
        self.property_overrides.clear()

        # Reset to original scene state
        if self.scene_path:
            self.reload_from_scene(self._get_scene_manager())

        # Reset instance-specific properties
        self.editable_children = False

    def _get_scene_manager(self):
        """Get the scene manager from the current project"""
        try:
            from core.project import get_current_project
            project = get_current_project()
            return project.scene_manager if project else None
        except:
            return None

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics for this instance"""
        import sys

        stats = {
            'instance_size': sys.getsizeof(self),
            'children_count': len(self.children),
            'override_count': len(self.property_overrides),
            'total_nodes': self._count_total_nodes(),
            'scene_path': self.scene_path,
            'is_pooled': getattr(self, '_is_pooled', False),
            'is_active': getattr(self, '_is_active', True)
        }

        return stats

    def _count_total_nodes(self) -> int:
        """Count total nodes in this instance hierarchy"""
        count = 1  # Self
        for child in self.children:
            count += self._count_nodes_recursive(child)
        return count

    def _count_nodes_recursive(self, node: Node) -> int:
        """Recursively count nodes"""
        count = 1
        for child in node.children:
            count += self._count_nodes_recursive(child)
        return count

    def validate_integrity(self) -> List[str]:
        """Validate the integrity of this scene instance"""
        issues = []

        # Check if scene file exists
        if self.scene_path:
            try:
                from core.project import get_current_project
                project = get_current_project()
                if project:
                    scene_file = project.get_absolute_path(self.scene_path)
                    if not scene_file.exists():
                        issues.append(f"Scene file not found: {self.scene_path}")
            except:
                issues.append("Could not validate scene file existence")
        else:
            issues.append("No scene path specified")

        # Check property overrides
        for node_path, overrides in self.property_overrides.items():
            target_node = self._find_node_by_path(node_path)
            if not target_node:
                issues.append(f"Override target node not found: {node_path}")
                continue

            for prop_name in overrides.keys():
                if not hasattr(target_node, prop_name):
                    issues.append(f"Override property not found: {node_path}.{prop_name}")

        # Check for circular references
        if self._has_circular_references():
            issues.append("Circular references detected in node hierarchy")

        return issues

    def _has_circular_references(self, visited: Optional[set] = None) -> bool:
        """Check for circular references in the node hierarchy"""
        if visited is None:
            visited = set()

        if id(self) in visited:
            return True

        visited.add(id(self))

        for child in self.children:
            if hasattr(child, '_has_circular_references'):
                if child._has_circular_references(visited.copy()):
                    return True

        return False

    def break_instance(self) -> List[Node]:
        """
        Break the scene instance, converting it to regular nodes.
        Returns the list of nodes that were children of this instance.
        """
        # Remove scene instance metadata
        self.scene_path = ""
        self.original_scene = None
        self.property_overrides.clear()
        
        # Change type to regular Node
        self.type = "Node"
        
        # Return children for re-parenting
        children = self.children.copy()
        return children

    def __repr__(self) -> str:
        return f"SceneInstance(name='{self.name}', scene_path='{self.scene_path}', instance_id='{self.instance_id}')"
