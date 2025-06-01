"""
Node Registry System for Lupine Engine
Manages dynamic node registration and categorization for extensible node system
"""

import os
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
    
    def __init__(self):
        self._nodes: Dict[str, NodeDefinition] = {}
        self._categories: Dict[NodeCategory, List[str]] = {
            NodeCategory.BASE: [],
            NodeCategory.NODE_2D: [],
            NodeCategory.UI: [],
            NodeCategory.PREFABS: []
        }
        self._register_builtin_nodes()
    
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
            name="Camera2D",
            category=NodeCategory.NODE_2D,
            class_name="Camera2D",
            description="2D camera for viewing scenes"
        ))
        
        self.register_node(NodeDefinition(
            name="Area2D",
            category=NodeCategory.NODE_2D,
            class_name="Area2D",
            description="2D area for collision detection"
        ))
        
        self.register_node(NodeDefinition(
            name="RigidBody2D",
            category=NodeCategory.NODE_2D,
            class_name="RigidBody2D",
            description="2D physics body"
        ))
        
        self.register_node(NodeDefinition(
            name="StaticBody2D",
            category=NodeCategory.NODE_2D,
            class_name="StaticBody2D",
            description="2D static physics body"
        ))
        
        self.register_node(NodeDefinition(
            name="KinematicBody2D",
            category=NodeCategory.NODE_2D,
            class_name="KinematicBody2D",
            description="2D kinematic physics body"
        ))
        
        self.register_node(NodeDefinition(
            name="CollisionShape2D",
            category=NodeCategory.NODE_2D,
            class_name="CollisionShape2D",
            description="2D collision shape"
        ))
        
        self.register_node(NodeDefinition(
            name="AnimatedSprite2D",
            category=NodeCategory.NODE_2D,
            class_name="AnimatedSprite2D",
            description="2D animated sprite"
        ))
        
        # UI nodes
        self.register_node(NodeDefinition(
            name="Control",
            category=NodeCategory.UI,
            class_name="Control",
            description="Base UI control node"
        ))
        
        self.register_node(NodeDefinition(
            name="CanvasLayer",
            category=NodeCategory.UI,
            class_name="CanvasLayer",
            description="Canvas layer for UI rendering"
        ))
        
        self.register_node(NodeDefinition(
            name="Button",
            category=NodeCategory.UI,
            class_name="Button",
            description="UI button control"
        ))
        
        self.register_node(NodeDefinition(
            name="Label",
            category=NodeCategory.UI,
            class_name="Label",
            description="UI text label"
        ))
        
        self.register_node(NodeDefinition(
            name="Panel",
            category=NodeCategory.UI,
            class_name="Panel",
            description="UI panel container"
        ))
        
        self.register_node(NodeDefinition(
            name="LineEdit",
            category=NodeCategory.UI,
            class_name="LineEdit",
            description="UI text input field"
        ))
    
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
    
    def create_node_instance(self, node_name: str, instance_name: str = None):
        """Create an instance of a registered node"""
        node_def = self.get_node_definition(node_name)
        if not node_def:
            raise ValueError(f"Unknown node type: {node_name}")
        
        # Use factory function if available
        if node_def.factory_func:
            return node_def.factory_func(instance_name or node_name)
        
        # Import and create node using class name
        from core.scene import Node, Node2D, Sprite, Camera2D, Area2D

        class_map = {
            "Node": Node,
            "Node2D": Node2D,
            "Sprite": Sprite,
            "Camera2D": Camera2D,
            "Area2D": Area2D,
            "Control": Node2D,  # Use Node2D as base for UI nodes for now
            "Button": Node2D,
            "Label": Node2D,
            "Panel": Node2D,
            "LineEdit": Node2D,
            "CanvasLayer": Node2D,
            "RigidBody2D": Node2D,
            "StaticBody2D": Node2D,
            "KinematicBody2D": Node2D,
            "CollisionShape2D": Node2D,
            "AnimatedSprite2D": Node2D,
            # Add more as needed
        }
        
        node_class = class_map.get(node_def.class_name)
        if not node_class:
            # Fallback to generic Node
            node_class = Node
        
        instance = node_class(instance_name or node_name)
        
        # Set script path if available
        if node_def.script_path:
            instance.script_path = node_def.script_path
        
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

def get_node_registry() -> NodeRegistry:
    """Get the global node registry instance"""
    global _node_registry
    if _node_registry is None:
        _node_registry = NodeRegistry()
    return _node_registry

def register_node(node_def: NodeDefinition):
    """Register a node in the global registry"""
    get_node_registry().register_node(node_def)

def get_available_nodes() -> Dict[str, NodeDefinition]:
    """Get all available nodes"""
    return get_node_registry().get_all_nodes()

def create_node(node_type: str, name: str = None):
    """Create a node instance"""
    return get_node_registry().create_node_instance(node_type, name)
