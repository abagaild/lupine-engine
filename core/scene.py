"""
Scene Management System for Lupine Engine
Handles scene loading, saving, and node management
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.project import LupineProject


class Node:
    """Base node class for scene hierarchy"""
    
    def __init__(self, name: str = "Node", node_type: str = "Node"):
        self.name = name
        self.type = node_type
        self.parent = None
        self.children = []
        self.properties = {}
        self.script_path = None
        
        # Common properties
        self.visible = True
        self.process_mode = "inherit"
    
    def add_child(self, child: 'Node'):
        """Add a child node"""
        if child.parent:
            child.parent.remove_child(child)
        
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'Node'):
        """Remove a child node"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def get_child(self, name: str) -> Optional['Node']:
        """Get child by name"""
        for child in self.children:
            if child.name == name:
                return child
        return None
    
    def find_node(self, path: str) -> Optional['Node']:
        """Find node by path (e.g., "Child/Grandchild")"""
        if not path:
            return self
        
        parts = path.split('/', 1)
        child_name = parts[0]
        remaining_path = parts[1] if len(parts) > 1 else ""
        
        child = self.get_child(child_name)
        if child:
            return child.find_node(remaining_path)
        
        return None
    
    def get_path(self) -> str:
        """Get path from root to this node"""
        if not self.parent:
            return self.name
        return f"{self.parent.get_path()}/{self.name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization"""
        data = {
            "name": self.name,
            "type": self.type,
            "visible": self.visible,
            "process_mode": self.process_mode,
            "properties": self.properties.copy(),
            "children": [child.to_dict() for child in self.children]
        }
        
        if self.script_path:
            data["script"] = self.script_path
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create node from dictionary"""
        node_type = data.get("type", "Node")
        
        # Create appropriate node type
        if node_type == "Node2D":
            node = Node2D(data.get("name", "Node2D"))
        elif node_type == "Sprite":
            node = Sprite(data.get("name", "Sprite"))
            # Set Sprite-specific properties
            node.texture = data.get("texture", None)
            node.normal_map = data.get("normal_map", None)
            node.centered = data.get("centered", True)
            node.offset = data.get("offset", [0.0, 0.0])
            node.flip_h = data.get("flip_h", False)
            node.flip_v = data.get("flip_v", False)
            node.region_enabled = data.get("region_enabled", False)
            node.region_rect = data.get("region_rect", [0, 0, 0, 0])
            node.region_filter_clip = data.get("region_filter_clip", False)
            node.hframes = data.get("hframes", 1)
            node.vframes = data.get("vframes", 1)
            node.frame = data.get("frame", 0)
            node.frame_coords = data.get("frame_coords", [0, 0])
            node.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
            node.self_modulate = data.get("self_modulate", [1.0, 1.0, 1.0, 1.0])
        elif node_type == "Camera2D":
            node = Camera2D(data.get("name", "Camera2D"))
        elif node_type == "Area2D":
            node = Area2D(data.get("name", "Area2D"))
        else:
            node = Node(data.get("name", "Node"), node_type)
        
        # Set properties
        node.visible = data.get("visible", True)
        node.process_mode = data.get("process_mode", "inherit")
        node.properties = data.get("properties", {})
        node.script_path = data.get("script") or ""
        
        # Add children
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        
        return node


class Node2D(Node):
    """2D node with transform properties"""
    
    def __init__(self, name: str = "Node2D"):
        super().__init__(name, "Node2D")
        self.position = [0.0, 0.0]
        self.rotation = 0.0
        self.scale = [1.0, 1.0]
        self.z_index = 0
        self.z_as_relative = True
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "z_index": self.z_index,
            "z_as_relative": self.z_as_relative
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node2D':
        node = cls(data.get("name", "Node2D"))
        node.position = data.get("position", [0.0, 0.0])
        node.rotation = data.get("rotation", 0.0)
        node.scale = data.get("scale", [1.0, 1.0])
        node.z_index = data.get("z_index", 0)
        node.z_as_relative = data.get("z_as_relative", True)
        return node


class Sprite(Node2D):
    """Sprite node for displaying textures - equivalent to Godot's Sprite2D"""

    def __init__(self, name: str = "Sprite"):
        super().__init__(name)
        self.type = "Sprite"

        # Texture properties
        self.texture = None
        self.normal_map = None

        # Transform properties
        self.centered = True
        self.offset = [0.0, 0.0]
        self.flip_h = False
        self.flip_v = False

        # Region properties
        self.region_enabled = False
        self.region_rect = [0, 0, 0, 0]  # x, y, width, height
        self.region_filter_clip = False

        # Animation properties
        self.hframes = 1
        self.vframes = 1
        self.frame = 0
        self.frame_coords = [0, 0]

        # Rendering properties
        self.modulate = [1.0, 1.0, 1.0, 1.0]  # RGBA
        self.self_modulate = [1.0, 1.0, 1.0, 1.0]  # RGBA

        # Set default script
        self.script_path = "nodes/Sprite.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            # Texture properties
            "texture": self.texture,
            "normal_map": self.normal_map,

            # Transform properties
            "centered": self.centered,
            "offset": self.offset,
            "flip_h": self.flip_h,
            "flip_v": self.flip_v,

            # Region properties
            "region_enabled": self.region_enabled,
            "region_rect": self.region_rect,
            "region_filter_clip": self.region_filter_clip,

            # Animation properties
            "hframes": self.hframes,
            "vframes": self.vframes,
            "frame": self.frame,
            "frame_coords": self.frame_coords,

            # Rendering properties
            "modulate": self.modulate,
            "self_modulate": self.self_modulate
        })
        return data


class Camera2D(Node2D):
    """2D camera node"""
    
    def __init__(self, name: str = "Camera2D"):
        super().__init__(name)
        self.type = "Camera2D"
        self.current = False
        self.zoom = [1.0, 1.0]
        self.limit_left = -10000000
        self.limit_top = -10000000
        self.limit_right = 10000000
        self.limit_bottom = 10000000
        self.smoothing_enabled = False
        self.smoothing_speed = 5.0
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "current": self.current,
            "zoom": self.zoom,
            "limit_left": self.limit_left,
            "limit_top": self.limit_top,
            "limit_right": self.limit_right,
            "limit_bottom": self.limit_bottom,
            "smoothing_enabled": self.smoothing_enabled,
            "smoothing_speed": self.smoothing_speed
        })
        return data


class Area2D(Node2D):
    """2D area for collision detection"""
    
    def __init__(self, name: str = "Area2D"):
        super().__init__(name)
        self.type = "Area2D"
        self.monitoring = True
        self.monitorable = True
        self.collision_layer = 1
        self.collision_mask = 1
        self.gravity_space_override = "disabled"
        self.gravity = [0, 98]
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "monitoring": self.monitoring,
            "monitorable": self.monitorable,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "gravity_space_override": self.gravity_space_override,
            "gravity": self.gravity
        })
        return data


class Scene:
    """Represents a complete scene with nodes"""
    
    def __init__(self, name: str = "Scene"):
        self.name = name
        self.root_nodes = []
        self.metadata = {}
    
    def add_root_node(self, node: Node):
        """Add a root node to the scene"""
        self.root_nodes.append(node)
    
    def remove_root_node(self, node: Node):
        """Remove a root node from the scene"""
        if node in self.root_nodes:
            self.root_nodes.remove(node)
    
    def find_node(self, path: str) -> Optional[Node]:
        """Find a node by path"""
        if '/' not in path:
            # Search in all root nodes
            for root in self.root_nodes:
                if root.name == path:
                    return root
            return None
        
        # Split path and search
        parts = path.split('/', 1)
        root_name = parts[0]
        remaining_path = parts[1]
        
        for root in self.root_nodes:
            if root.name == root_name:
                return root.find_node(remaining_path)
        
        return None
    
    def get_all_nodes(self) -> List[Node]:
        """Get all nodes in the scene (flattened)"""
        nodes = []
        
        def collect_nodes(node: Node):
            nodes.append(node)
            for child in node.children:
                collect_nodes(child)
        
        for root in self.root_nodes:
            collect_nodes(root)
        
        return nodes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scene to dictionary for serialization"""
        return {
            "name": self.name,
            "metadata": self.metadata,
            "nodes": [node.to_dict() for node in self.root_nodes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scene':
        """Create scene from dictionary"""
        scene = cls(data.get("name", "Scene"))
        scene.metadata = data.get("metadata", {})
        
        for node_data in data.get("nodes", []):
            node = Node.from_dict(node_data)
            scene.add_root_node(node)
        
        return scene
    
    def save_to_file(self, file_path: str):
        """Save scene to file"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['Scene']:
        """Load scene from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Failed to load scene from {file_path}: {e}")
            return None


class SceneManager:
    """Manages scene loading and switching"""
    
    def __init__(self, project: LupineProject):
        self.project = project
        self.current_scene = None
        self.loaded_scenes = {}  # path -> Scene
    
    def load_scene(self, scene_path: str) -> Optional[Scene]:
        """Load a scene from file"""
        if scene_path in self.loaded_scenes:
            return self.loaded_scenes[scene_path]
        
        full_path = self.project.get_absolute_path(scene_path)
        scene = Scene.load_from_file(str(full_path))
        
        if scene:
            self.loaded_scenes[scene_path] = scene
        
        return scene
    
    def save_scene(self, scene: Scene, scene_path: str):
        """Save a scene to file"""
        full_path = self.project.get_absolute_path(scene_path)
        scene.save_to_file(str(full_path))
        
        # Update loaded scenes cache
        self.loaded_scenes[scene_path] = scene
    
    def set_current_scene(self, scene_path: str) -> bool:
        """Set the current active scene"""
        scene = self.load_scene(scene_path)
        if scene:
            self.current_scene = scene
            return True
        return False
    
    def get_current_scene(self) -> Optional[Scene]:
        """Get the current active scene"""
        return self.current_scene
    
    def create_new_scene(self, name: str) -> Scene:
        """Create a new empty scene"""
        scene = Scene(name)
        
        # Add default root node
        root_node = Node2D(name)
        scene.add_root_node(root_node)
        
        return scene
