"""
Game Engine Interface for LSC Runtime

This module defines the interface that a game engine must implement
to integrate with the LSC runtime system.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Optional, Dict


class GameEngineInterface(ABC):
    """Abstract interface that game engines must implement for LSC integration"""
    
    # Node Management
    @abstractmethod
    def get_node(self, path: str) -> Any:
        """Get node by path"""
        pass
    
    @abstractmethod
    def find_node(self, name: str, recursive: bool = True) -> Any:
        """Find node by name"""
        pass
    
    @abstractmethod
    def get_parent(self, node: Any = None) -> Any:
        """Get parent of node"""
        pass
    
    @abstractmethod
    def get_children(self, node: Any = None) -> List[Any]:
        """Get children of node"""
        pass
    
    @abstractmethod
    def add_child(self, parent: Any, child: Any) -> None:
        """Add child to parent node"""
        pass
    
    @abstractmethod
    def remove_child(self, parent: Any, child: Any) -> None:
        """Remove child from parent node"""
        pass
    
    @abstractmethod
    def queue_free(self, node: Any) -> None:
        """Queue node for deletion"""
        pass
    
    @abstractmethod
    def duplicate(self, node: Any) -> Any:
        """Duplicate a node"""
        pass
    
    @abstractmethod
    def is_inside_tree(self, node: Any = None) -> bool:
        """Check if node is inside the scene tree"""
        pass
    
    # Scene Management
    @abstractmethod
    def get_tree(self) -> Any:
        """Get the scene tree"""
        pass
    
    @abstractmethod
    def change_scene(self, path: str) -> None:
        """Change to a different scene"""
        pass
    
    @abstractmethod
    def reload_scene(self) -> None:
        """Reload the current scene"""
        pass
    
    @abstractmethod
    def get_scene(self) -> Any:
        """Get the current scene"""
        pass
    
    # Input Management
    @abstractmethod
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is pressed"""
        pass
    
    @abstractmethod
    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed"""
        pass
    
    @abstractmethod
    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released"""
        pass
    
    @abstractmethod
    def get_action_strength(self, action: str) -> float:
        """Get action strength"""
        pass
    
    @abstractmethod
    def is_key_pressed(self, key) -> bool:
        """Check if key is pressed"""
        pass
    
    @abstractmethod
    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if mouse button is pressed"""
        pass
    
    @abstractmethod
    def get_mouse_position(self) -> Tuple[float, float]:
        """Get mouse position"""
        pass
    
    @abstractmethod
    def get_global_mouse_position(self) -> Tuple[float, float]:
        """Get global mouse position"""
        pass


class MockGameEngine(GameEngineInterface):
    """Mock implementation for testing and development"""
    
    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.scene_tree = None
        self.current_scene = None
        self.input_state = {}
        self.mouse_position = (0.0, 0.0)
    
    def get_node(self, path: str) -> Any:
        return self.nodes.get(path)
    
    def find_node(self, name: str, recursive: bool = True) -> Any:
        for node_path, node in self.nodes.items():
            if hasattr(node, 'name') and node.name == name:
                return node
        return None
    
    def get_parent(self, node: Any = None) -> Any:
        if node and hasattr(node, 'parent'):
            return node.parent
        return None
    
    def get_children(self, node: Any = None) -> List[Any]:
        if node and hasattr(node, 'children'):
            return list(node.children)
        return []
    
    def add_child(self, parent: Any, child: Any) -> None:
        if parent and hasattr(parent, 'add_child'):
            parent.add_child(child)
    
    def remove_child(self, parent: Any, child: Any) -> None:
        if parent and hasattr(parent, 'remove_child'):
            parent.remove_child(child)
    
    def queue_free(self, node: Any) -> None:
        # Mock implementation - just remove from nodes dict
        for path, stored_node in list(self.nodes.items()):
            if stored_node is node:
                del self.nodes[path]
                break
    
    def duplicate(self, node: Any) -> Any:
        # Mock implementation - return a copy-like object
        if hasattr(node, '__dict__'):
            import copy
            return copy.deepcopy(node)
        return node
    
    def is_inside_tree(self, node: Any = None) -> bool:
        return node is not None and str(id(node)) in self.nodes
    
    def get_tree(self) -> Any:
        return self.scene_tree
    
    def change_scene(self, path: str) -> None:
        print(f"Mock: Changing scene to {path}")
        self.current_scene = path
    
    def reload_scene(self) -> None:
        print("Mock: Reloading current scene")
    
    def get_scene(self) -> Any:
        return self.current_scene
    
    def is_action_pressed(self, action: str) -> bool:
        return self.input_state.get(f"action_{action}", False)
    
    def is_action_just_pressed(self, action: str) -> bool:
        return self.input_state.get(f"action_{action}_just_pressed", False)
    
    def is_action_just_released(self, action: str) -> bool:
        return self.input_state.get(f"action_{action}_just_released", False)
    
    def get_action_strength(self, action: str) -> float:
        return self.input_state.get(f"action_{action}_strength", 0.0)
    
    def is_key_pressed(self, key) -> bool:
        return self.input_state.get(f"key_{key}", False)
    
    def is_mouse_button_pressed(self, button: int) -> bool:
        return self.input_state.get(f"mouse_{button}", False)
    
    def get_mouse_position(self) -> Tuple[float, float]:
        return self.mouse_position
    
    def get_global_mouse_position(self) -> Tuple[float, float]:
        return self.mouse_position
    
    # Helper methods for testing
    def set_input_state(self, key: str, value: Any) -> None:
        """Set input state for testing"""
        self.input_state[key] = value
    
    def set_mouse_position(self, x: float, y: float) -> None:
        """Set mouse position for testing"""
        self.mouse_position = (x, y)
    
    def add_node(self, path: str, node: Any) -> None:
        """Add a node for testing"""
        self.nodes[path] = node
