"""
Base Node implementation for Lupine Engine
The fundamental building block of the scene tree system
"""

from core.scene.base_node import Node as BaseNode
from typing import Dict, Any, List, Optional


class Node(BaseNode):
    """
    Base node class - the fundamental building block of the scene tree.
    All other nodes inherit from this class.
    
    Features:
    - Scene tree hierarchy management
    - Signal system for communication
    - Script attachment and execution
    - Property system with export variables
    - Group management
    - Process and physics process callbacks
    """
    
    def __init__(self, name: str = "Node"):
        super().__init__(name, "Node")
        
        # Export variables for editor
        self.export_variables = {
            "process_priority": {
                "type": "int",
                "value": 0,
                "description": "Process priority for this node"
            },
            "pause_mode": {
                "type": "enum",
                "value": "inherit",
                "options": ["inherit", "stop", "process"],
                "description": "How this node behaves when the scene is paused"
            }
        }
        
        # Node-specific properties
        self.process_priority: int = 0
        self.pause_mode: str = "inherit"
        
        # Internal state
        self._paused: bool = False
        self._can_process: bool = True
        
        # Built-in signals
        self.add_signal("tree_entered")
        self.add_signal("tree_exiting")
        self.add_signal("ready")
        self.add_signal("renamed")
    
    def _ready(self):
        """Called when the node enters the scene tree for the first time"""
        if not self._ready_called:
            self._ready_called = True
            self.emit_signal("ready")

            # Call _ready method on all script instances
            script_instances = getattr(self, 'script_instances', [])
            if script_instances:
                for script_instance in script_instances:
                    if hasattr(script_instance, 'call_method'):
                        try:
                            if script_instance.has_method('_ready'):
                                script_instance.call_method('_ready')
                            elif script_instance.has_method('on_ready'):
                                script_instance.call_method('on_ready')
                        except Exception as e:
                            print(f"Error calling _ready in {script_instance.script_path}: {e}")
                            import traceback
                            traceback.print_exc()

            # Backward compatibility: handle single script_instance
            elif self.script_instance and hasattr(self.script_instance, 'call_method'):
                try:
                    if self.script_instance.has_method('_ready'):
                        self.script_instance.call_method('_ready')
                    elif self.script_instance.has_method('on_ready'):
                        self.script_instance.call_method('on_ready')
                except Exception as e:
                    print(f"Error calling _ready in {self.script_path}: {e}")
                    import traceback
                    traceback.print_exc()
    
    def _enter_tree(self):
        """Called when the node enters the scene tree"""
        super()._enter_tree()
        self.emit_signal("tree_entered")

        # Call _enter_tree method on all script instances
        script_instances = getattr(self, 'script_instances', [])
        if script_instances:
            for script_instance in script_instances:
                if hasattr(script_instance, 'call_method'):
                    try:
                        if script_instance.has_method('_enter_tree'):
                            script_instance.call_method('_enter_tree')
                    except Exception as e:
                        print(f"Error calling _enter_tree in {script_instance.script_path}: {e}")
                        import traceback
                        traceback.print_exc()

        # Backward compatibility: handle single script_instance
        elif self.script_instance and hasattr(self.script_instance, 'call_method'):
            try:
                if self.script_instance.has_method('_enter_tree'):
                    self.script_instance.call_method('_enter_tree')
            except Exception as e:
                print(f"Error calling _enter_tree in {self.script_path}: {e}")
                import traceback
                traceback.print_exc()
    
    def _exit_tree(self):
        """Called when the node exits the scene tree"""
        self.emit_signal("tree_exiting")
        
        # Call script's _exit_tree method if available
        if self.script_instance and hasattr(self.script_instance, 'call_method'):
            try:
                if self.script_instance.has_method('_exit_tree'):
                    self.script_instance.call_method('_exit_tree')
            except Exception as e:
                print(f"Error calling _exit_tree in {self.script_path}: {e}")
                import traceback
                traceback.print_exc()
        
        super()._exit_tree()
    
    def set_name(self, new_name: str):
        """Set the node's name and emit renamed signal"""
        old_name = self.name
        self.name = new_name
        self.emit_signal("renamed", old_name, new_name)
    
    def get_node(self, path: str) -> Optional["Node"]:
        """Get a node by path (alias for find_node)"""
        return self.find_node(path)
    
    def has_node(self, path: str) -> bool:
        """Check if a node exists at the given path"""
        return self.find_node(path) is not None
    
    def get_children(self) -> List["Node"]:
        """Get all direct children of this node"""
        return self.children.copy()
    
    def get_child_count(self) -> int:
        """Get the number of direct children"""
        return len(self.children)
    
    def get_index(self) -> int:
        """Get this node's index in its parent's children list"""
        if self.parent:
            try:
                return self.parent.children.index(self)
            except ValueError:
                return -1
        return 0
    
    def move_child(self, child: "Node", to_index: int):
        """Move a child to a specific index"""
        if child in self.children:
            self.children.remove(child)
            to_index = max(0, min(to_index, len(self.children)))
            self.children.insert(to_index, child)
    
    def duplicate(self, flags: int = 0) -> "Node":
        """Create a duplicate of this node and its subtree"""
        # Convert to dict and back to create a deep copy
        data = self.to_dict()
        duplicate = Node.from_dict(data)
        
        # Clear parent reference for the duplicate
        duplicate.parent = None
        
        return duplicate
    
    def queue_free(self):
        """Mark this node for deletion at the end of the frame"""
        # In a full implementation, this would add to a deletion queue
        if self.parent:
            self.parent.remove_child(self)
    
    def set_process(self, enable: bool):
        """Enable or disable process calls for this node"""
        self._can_process = enable
    
    def is_processing(self) -> bool:
        """Check if this node is currently processing"""
        return self._can_process and not self._paused
    
    def set_physics_process(self, enable: bool):
        """Enable or disable physics process calls for this node"""
        # This would be implemented in a full physics system
        pass
    
    def is_physics_processing(self) -> bool:
        """Check if this node is currently physics processing"""
        return self._can_process and not self._paused
    
    def set_process_priority(self, priority: int):
        """Set the process priority for this node"""
        self.process_priority = priority
    
    def get_process_priority(self) -> int:
        """Get the process priority for this node"""
        return self.process_priority
    
    def add_to_group(self, group: str):
        """Add this node to a group"""
        if group not in self._groups:
            self._groups.append(group)
    
    def remove_from_group(self, group: str):
        """Remove this node from a group"""
        if group in self._groups:
            self._groups.remove(group)
    
    def is_in_group(self, group: str) -> bool:
        """Check if this node is in a specific group"""
        return group in self._groups
    
    def get_groups(self) -> List[str]:
        """Get all groups this node belongs to"""
        return self._groups.copy()
    
    def get_tree_string(self, indent: int = 0) -> str:
        """Get a string representation of this node's subtree"""
        result = "  " * indent + f"{self.name} ({self.type})\n"
        for child in self.children:
            if hasattr(child, 'get_tree_string'):
                result += child.get_tree_string(indent + 1)
            else:
                result += "  " * (indent + 1) + f"{child.name} ({child.type})\n"
        return result
    
    def print_tree(self):
        """Print the tree structure starting from this node"""
        print(self.get_tree_string())
    
    def _process(self, delta: float):
        """Process this node and its children"""
        if self.is_processing():
            super()._process(delta)
    
    def _physics_process(self, delta: float):
        """Physics process this node and its children"""
        if self.is_physics_processing():
            super()._physics_process(delta)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "process_priority": self.process_priority,
            "pause_mode": self.pause_mode
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """Create from dictionary"""
        node = cls(data.get("name", "Node"))
        cls._apply_node_properties(node, data)
        
        # Apply Node specific properties
        node.process_priority = data.get("process_priority", 0)
        node.pause_mode = data.get("pause_mode", "inherit")
        
        # Create children
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        
        return node
