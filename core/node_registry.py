"""
Node Registry System for Lupine Engine
Manages dynamic node registration and categorization for extensible node system
"""


import json
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class NodeCategory(Enum):
    """Node categories for organization"""
    BASE = "Base"
    NODE_2D = "2D"
    UI = "UI"
    PREFABS = "Prefabs"


@dataclass
class NodeDefinition:
    """Definition of a registered node type"""
    name: str
    category: NodeCategory
    class_name: str
    script_path: Optional[str] = None
    icon_path: Optional[str] = None
    description: str = ""
    is_builtin: bool = True
    factory_func: Optional[Callable] = None


class NodeRegistry:
    """Registry for all available node types"""

    def __init__(self, project_path: Optional[Path] = None):
        self._nodes: Dict[str, NodeDefinition] = {}
        self._categories: Dict[NodeCategory, List[str]] = {
            NodeCategory.BASE: [],
            NodeCategory.NODE_2D: [],
            NodeCategory.UI: [],
            NodeCategory.PREFABS: []
        }
        self._project_path = project_path
        self._register_builtin_nodes()

        # Load project-specific nodes if project path is provided
        if self._project_path:
            self.load_project_nodes()
    
    def _register_builtin_nodes(self):
        """Register built-in node types"""
        # Base nodes
        self.register_node(NodeDefinition(
            name="Node",
            category=NodeCategory.BASE,
            class_name="Node",
            description="Base node for all other nodes"
        ))
        
        self.register_node(NodeDefinition(
            name="Node2D",
            category=NodeCategory.BASE,
            class_name="Node2D",
            description="Base node for 2D scenes with transform"
        ))
        
        # 2D nodes
        self.register_node(NodeDefinition(
            name="Sprite",
            category=NodeCategory.NODE_2D,
            class_name="Sprite",
            script_path="nodes/Sprite.lsc",
            description="2D sprite for displaying textures"
        ))

        self.register_node(NodeDefinition(
            name="AnimatedSprite",
            category=NodeCategory.NODE_2D,
            class_name="AnimatedSprite",
            script_path="nodes/AnimatedSprite.lsc",
            description="2D animated sprite with frame-based animation support - equivalent to Godot's AnimatedSprite2D"
        ))

        self.register_node(NodeDefinition(
            name="Camera2D",
            category=NodeCategory.NODE_2D,
            class_name="Camera2D",
            script_path="nodes/Camera2D.lsc",
            description="2D camera with viewport control, following, limits, and effects - equivalent to Godot's Camera2D"
        ))

        # Base nodes
        self.register_node(NodeDefinition(
            name="Timer",
            category=NodeCategory.BASE,
            class_name="Timer",
            script_path="nodes/Timer.lsc",
            description="Fires timeout signal after set interval, optionally repeating. Great for delays, cooldowns, and scheduled events."
        ))

        # UI nodes
        self.register_node(NodeDefinition(
            name="Control",
            category=NodeCategory.UI,
            class_name="Control",
            description="Base UI node with rect, layout, anchors, and margins"
        ))

        self.register_node(NodeDefinition(
            name="Panel",
            category=NodeCategory.UI,
            class_name="Panel",
            script_path="nodes/Panel.lsc",
            description="Simple rectangular container with background"
        ))

        self.register_node(NodeDefinition(
            name="Label",
            category=NodeCategory.UI,
            class_name="Label",
            script_path="nodes/Label.lsc",
            description="UI node that displays text on screen"
        ))

        self.register_node(NodeDefinition(
            name="Button",
            category=NodeCategory.UI,
            class_name="Button",
            script_path="nodes/Button.lsc",
            description="Interactive button UI node with click, hover, and press states"
        ))

        self.register_node(NodeDefinition(
            name="CanvasLayer",
            category=NodeCategory.UI,
            class_name="CanvasLayer",
            script_path="nodes/CanvasLayer.lsc",
            description="Canvas layer for UI and effects with independent rendering"
        ))

    def load_project_nodes(self):
        """Load nodes from project's local node directories"""
        if not self._project_path:
            return

        nodes_dir = self._project_path / "nodes"
        if not nodes_dir.exists():
            return

        # Clear existing non-builtin nodes to avoid duplicates
        nodes_to_remove = [name for name, node_def in self._nodes.items() if not node_def.is_builtin]
        for node_name in nodes_to_remove:
            self.unregister_node(node_name)

        # Also clear built-in nodes that will be replaced by project versions
        builtin_nodes_to_replace = ["Node", "Node2D", "Control", "Sprite", "AnimatedSprite", "Timer", "Panel", "Label", "Button", "CanvasLayer", "Camera2D"]
        for node_name in builtin_nodes_to_replace:
            if node_name in self._nodes and self._nodes[node_name].is_builtin:
                self.unregister_node(node_name)

        # Load nodes from each category directory
        category_mapping = {
            "base": NodeCategory.BASE,
            "node2d": NodeCategory.NODE_2D,
            "ui": NodeCategory.UI,
            "prefabs": NodeCategory.PREFABS
        }

        for dir_name, category in category_mapping.items():
            category_dir = nodes_dir / dir_name
            if category_dir.exists():
                self._load_nodes_from_directory(category_dir, category)

    def _load_nodes_from_directory(self, directory: Path, category: NodeCategory):
        """Load all .lsc files from a directory as nodes"""
        for lsc_file in directory.glob("*.lsc"):
            try:
                node_name = lsc_file.stem

                # Determine class name from node name or content
                class_name = self._determine_class_name(lsc_file, node_name)

                # Create relative script path from project root
                if self._project_path:
                    script_path = str(lsc_file.relative_to(self._project_path))
                else:
                    script_path = str(lsc_file)

                # Register the node
                self.register_node(NodeDefinition(
                    name=node_name,
                    category=category,
                    class_name=class_name,
                    script_path=script_path,
                    description=f"Project {category.value} node: {node_name}",
                    is_builtin=False
                ))

                print(f"Loaded project node: {node_name} ({category.value})")

            except Exception as e:
                print(f"Error loading node {lsc_file}: {e}")

    def _determine_class_name(self, lsc_file: Path, node_name: str) -> str:
        """Determine the class name for a node from its LSC file"""
        try:
            # First, check if this is a known specific node type
            if node_name in ["Sprite", "AnimatedSprite", "Camera2D", "Timer", "Panel", "Label", "Button", "CanvasLayer", "Area2D", "CollisionShape2D", "CollisionPolygon2D", "RigidBody2D", "StaticBody2D", "KinematicBody2D"]:
                return node_name

            # For other nodes, check the extends clause
            with open(lsc_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for extends clause to determine base class
            if "extends Control" in content:
                return "Control"
            elif "extends Node2D" in content:
                return "Node2D"
            elif "extends Node" in content:
                return "Node"
            else:
                return "Node"  # Fallback

        except Exception:
            return "Node"  # Safe fallback


    def register_node(self, node_def: NodeDefinition):
        """Register a new node type"""
        self._nodes[node_def.name] = node_def
        self._categories[node_def.category].append(node_def.name)
    
    def unregister_node(self, name: str):
        """Unregister a node type"""
        if name in self._nodes:
            node_def = self._nodes[name]
            self._categories[node_def.category].remove(name)
            del self._nodes[name]
    
    def get_node_definition(self, name: str) -> Optional[NodeDefinition]:
        """Get node definition by name"""
        return self._nodes.get(name)
    
    def get_nodes_by_category(self, category: NodeCategory) -> List[NodeDefinition]:
        """Get all nodes in a category"""
        node_names = self._categories.get(category, [])
        return [self._nodes[name] for name in node_names if name in self._nodes]
    
    def get_all_categories(self) -> List[NodeCategory]:
        """Get all available categories"""
        return list(NodeCategory)
    
    def get_all_nodes(self) -> Dict[str, NodeDefinition]:
        """Get all registered nodes"""
        return self._nodes.copy()
    
    def create_node_instance(self, node_name: str, instance_name: Optional[str] = None):
        """Create an instance of a registered node"""
        node_def = self.get_node_definition(node_name)
        if not node_def:
            raise ValueError(f"Unknown node type: {node_name}")
        
        # Use factory function if available
        if node_def.factory_func:
            return node_def.factory_func(instance_name or node_name)
        
        # Import and create node using class name
        from core.scene import (Node, Node2D, Sprite, AnimatedSprite, Timer, Control, Panel, Label, Button,
                               CanvasLayer, Camera2D, Area2D, CollisionShape2D, CollisionPolygon2D,
                               RigidBody2D, StaticBody2D, KinematicBody2D)

        class_map = {
            "Node": Node,
            "Node2D": Node2D,
            "Sprite": Sprite,
            "AnimatedSprite": AnimatedSprite,
            "Timer": Timer,
            "Control": Control,
            "Panel": Panel,
            "Label": Label,
            "Button": Button,
            "CanvasLayer": CanvasLayer,
            "Camera2D": Camera2D,
            "Area2D": Area2D,
            "CollisionShape2D": CollisionShape2D,
            "CollisionPolygon2D": CollisionPolygon2D,
            "RigidBody2D": RigidBody2D,
            "StaticBody2D": StaticBody2D,
            "KinematicBody2D": KinematicBody2D,
        }
        
        node_class = class_map.get(node_def.class_name)
        if not node_class:
            # Fallback to generic Node
            node_class = Node
        
        instance = node_class(instance_name or node_name)
        
        # Set script path if available
        if node_def.script_path:
            instance.script_path = str(node_def.script_path)
        
        return instance
    
    def load_prefabs_from_directory(self, prefabs_dir: Path):
        """Load prefab nodes from directory"""
        if not prefabs_dir.exists():
            return
        
        for prefab_file in prefabs_dir.glob("*.json"):
            try:
                with open(prefab_file, 'r', encoding='utf-8') as f:
                    prefab_data = json.load(f)
                
                # Register prefab as a node type
                prefab_name = prefab_file.stem
                self.register_node(NodeDefinition(
                    name=prefab_name,
                    category=NodeCategory.PREFABS,
                    class_name="Prefab",
                    script_path=prefab_data.get("script"),
                    description=f"Prefab: {prefab_name}",
                    is_builtin=False,
                    factory_func=lambda name, data=prefab_data: self._create_prefab_instance(name, data)
                ))
                
            except Exception as e:
                print(f"Error loading prefab {prefab_file}: {e}")
    
    def _create_prefab_instance(self, instance_name: str, prefab_data: Dict[str, Any]):
        """Create an instance from prefab data"""
        from core.scene import Node
        
        # Create node from prefab data
        root_node = Node.from_dict(prefab_data)
        root_node.name = instance_name
        return root_node
    
    def register_custom_node(self, name: str, category: NodeCategory, 
                           script_path: str, description: str = ""):
        """Register a custom node from script"""
        self.register_node(NodeDefinition(
            name=name,
            category=category,
            class_name="CustomNode",
            script_path=script_path,
            description=description,
            is_builtin=False
        ))
    
    def scan_for_custom_nodes(self, nodes_dir: Path):
        """Scan directory for custom node scripts"""
        if not nodes_dir.exists():
            return
        
        for script_file in nodes_dir.glob("*.lsc"):
            try:
                # Parse script to determine node type and category
                with open(script_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract extends clause to determine category
                if "extends Control" in content:
                    category = NodeCategory.UI
                elif "extends Node2D" in content:
                    category = NodeCategory.NODE_2D
                else:
                    category = NodeCategory.BASE
                
                node_name = script_file.stem
                
                # Don't register if already exists (builtin takes precedence)
                if node_name not in self._nodes:
                    self.register_custom_node(
                        name=node_name,
                        category=category,
                        script_path=str(script_file.relative_to(nodes_dir.parent)),
                        description=f"Custom {category.value} node"
                    )
                    
            except Exception as e:
                print(f"Error scanning custom node {script_file}: {e}")


# Global registry instance
_node_registry = None

def get_node_registry(project_path: Optional[Path] = None) -> NodeRegistry:
    """Get the global node registry instance"""
    global _node_registry
    if _node_registry is None or (project_path and _node_registry._project_path != project_path):
        _node_registry = NodeRegistry(project_path)
    return _node_registry

def set_project_path(project_path: Path):
    """Set the project path for the global registry"""
    global _node_registry
    _node_registry = NodeRegistry(project_path)

def register_node(node_def: NodeDefinition):
    """Register a node in the global registry"""
    get_node_registry().register_node(node_def)

def get_available_nodes() -> Dict[str, NodeDefinition]:
    """Get all available nodes"""
    return get_node_registry().get_all_nodes()

def create_node(node_type: str, name: Optional[str] = None):
    """Create a node instance"""
    return get_node_registry().create_node_instance(node_type, name)
