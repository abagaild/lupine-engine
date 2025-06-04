"""
scene/base_node.py

Defines the base Node class and shared serialization logic.
"""

import json
import copy
from typing import Dict, Any, List, Optional, Union


class Node:
    """Base node class for scene hierarchy."""

    def __init__(self, name: str = "Node", node_type: str = "Node"):
        self.name = name
        self.type = node_type
        self.parent: Optional["Node"] = None
        self.children: List["Node"] = []
        self.properties: Dict[str, Any] = {}
        self.script_path: Optional[str] = None
        self.script_instance = None

        # Common properties
        self.visible: bool = True
        self.process_mode: str = "inherit"

        # Tree state
        self._in_tree: bool = False
        self._ready_called: bool = False

        # Signals system
        self._signals: Dict[str, List] = {}

        # Groups
        self._groups: List[str] = []

    def add_child(self, child: "Node") -> None:
        """Add a child node, re-parenting if necessary."""
        if child.parent:
            child.parent.remove_child(child)

        child.parent = self
        self.children.append(child)

        # If this node is in the tree, add the child to the tree too
        if self._in_tree:
            child._enter_tree()

    def remove_child(self, child: "Node") -> None:
        """Remove a child node if present."""
        if child in self.children:
            if child._in_tree:
                child._exit_tree()
            child.parent = None
            self.children.remove(child)

    def _enter_tree(self) -> None:
        """Called when node enters the scene tree."""
        self._in_tree = True

        # Call _ready if not already called
        if not self._ready_called:
            self._ready()
            self._ready_called = True

        # Recursively enter children
        for child in self.children:
            child._enter_tree()

    def _exit_tree(self) -> None:
        """Called when node exits the scene tree."""
        self._in_tree = False

        # Recursively exit children
        for child in self.children:
            child._exit_tree()

    def _ready(self) -> None:
        """Called when the node is ready. Override in subclasses."""
        # Call _ready method on all script instances
        script_instances = getattr(self, 'script_instances', [])
        if script_instances:
            for script_instance in script_instances:
                if hasattr(script_instance, 'call_method'):
                    try:
                        if script_instance.has_method('_ready'):
                            script_instance.call_method('_ready')
                    except Exception as e:
                        print(f"Error calling _ready in {script_instance.script_path}: {e}")

        # Backward compatibility: handle single script_instance
        elif self.script_instance and hasattr(self.script_instance, 'call_method'):
            try:
                if self.script_instance.has_method('_ready'):
                    self.script_instance.call_method('_ready')
            except Exception as e:
                print(f"Error calling _ready in {self.script_path}: {e}")

    def _process(self, delta: float) -> None:
        """Called every frame. Override in subclasses."""
        # Call _process method on all script instances
        script_instances = getattr(self, 'script_instances', [])
        if script_instances:
            for script_instance in script_instances:
                if hasattr(script_instance, 'call_method'):
                    try:
                        if script_instance.has_method('_process'):
                            script_instance.call_method('_process', delta)
                    except Exception as e:
                        print(f"Error calling _process in {script_instance.script_path}: {e}")

        # Backward compatibility: handle single script_instance
        elif self.script_instance and hasattr(self.script_instance, 'call_method'):
            try:
                if self.script_instance.has_method('_process'):
                    self.script_instance.call_method('_process', delta)
            except Exception as e:
                print(f"Error calling _process in {self.script_path}: {e}")

        # Process children
        for child in self.children:
            if child.visible and child.process_mode != "disabled":
                child._process(delta)

    def _physics_process(self, delta: float) -> None:
        """Called for physics updates. Override in subclasses."""
        # Call _physics_process method on all script instances
        script_instances = getattr(self, 'script_instances', [])
        if script_instances:
            for script_instance in script_instances:
                if hasattr(script_instance, 'call_method'):
                    try:
                        if script_instance.has_method('_physics_process'):
                            script_instance.call_method('_physics_process', delta)
                    except Exception as e:
                        print(f"Error calling _physics_process in {script_instance.script_path}: {e}")

        # Backward compatibility: handle single script_instance
        elif self.script_instance and hasattr(self.script_instance, 'call_method'):
            try:
                if self.script_instance.has_method('_physics_process'):
                    self.script_instance.call_method('_physics_process', delta)
            except Exception as e:
                print(f"Error calling _physics_process in {self.script_path}: {e}")

        # Process children
        for child in self.children:
            if child.visible and child.process_mode != "disabled":
                child._physics_process(delta)

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

    def is_in_tree(self) -> bool:
        """Check if node is in the scene tree."""
        return self._in_tree

    def get_tree(self) -> Optional["SceneTree"]:
        """Get the scene tree this node belongs to."""
        # This would return the actual scene tree in a full implementation
        return None

    # Signal system
    def add_signal(self, signal_name: str) -> None:
        """Add a signal to this node."""
        if signal_name not in self._signals:
            self._signals[signal_name] = []

    def connect(self, signal_name: str, target_node: "Node", method_name: str) -> None:
        """Connect a signal to a method on another node."""
        if signal_name not in self._signals:
            self.add_signal(signal_name)

        self._signals[signal_name].append({
            'target': target_node,
            'method': method_name
        })

    def disconnect(self, signal_name: str, target_node: "Node", method_name: str) -> None:
        """Disconnect a signal from a method."""
        if signal_name in self._signals:
            self._signals[signal_name] = [
                conn for conn in self._signals[signal_name]
                if not (conn['target'] == target_node and conn['method'] == method_name)
            ]

    def emit_signal(self, signal_name: str, *args, **kwargs) -> None:
        """Emit a signal with optional arguments."""
        if signal_name in self._signals:
            for connection in self._signals[signal_name]:
                target = connection['target']
                method = connection['method']

                # Try to call the method on the target
                if hasattr(target, method):
                    try:
                        getattr(target, method)(*args, **kwargs)
                    except Exception as e:
                        print(f"Error calling {method} on {target.name}: {e}")
                else:
                    # Try to call the method on all script instances
                    script_instances = getattr(target, 'script_instances', [])
                    method_called = False

                    if script_instances:
                        for script_instance in script_instances:
                            if hasattr(script_instance, 'call_method'):
                                try:
                                    if script_instance.has_method(method):
                                        script_instance.call_method(method, *args, **kwargs)
                                        method_called = True
                                except Exception as e:
                                    print(f"Error calling script method {method} on {target.name}: {e}")

                    # Backward compatibility: try single script_instance
                    elif target.script_instance and hasattr(target.script_instance, 'call_method'):
                        try:
                            if target.script_instance.has_method(method):
                                target.script_instance.call_method(method, *args, **kwargs)
                                method_called = True
                        except Exception as e:
                            print(f"Error calling script method {method} on {target.name}: {e}")

                    if not method_called:
                        print(f"Warning: Method {method} not found on {target.name} or its scripts")

    # Group system
    def add_to_group(self, group_name: str) -> None:
        """Add this node to a group."""
        if group_name not in self._groups:
            self._groups.append(group_name)

    def remove_from_group(self, group_name: str) -> None:
        """Remove this node from a group."""
        if group_name in self._groups:
            self._groups.remove(group_name)

    def is_in_group(self, group_name: str) -> bool:
        """Check if this node is in a group."""
        return group_name in self._groups

    def get_groups(self) -> List[str]:
        """Get all groups this node belongs to."""
        return self._groups.copy()

    # Property access with fallback to script variables
    def __getattr__(self, name: str) -> Any:
        """Get attribute with fallback to script variables."""
        # First check if it's in properties
        if name in self.properties:
            return self.properties[name]

        # Then check script instance export variables
        if self.script_instance and hasattr(self.script_instance, 'export_variables'):
            if name in self.script_instance.export_variables:
                return self.script_instance.export_variables[name]['value']

        # Then check script namespace
        if self.script_instance and hasattr(self.script_instance, 'namespace'):
            if name in self.script_instance.namespace:
                return self.script_instance.namespace[name]

        # If not found, raise AttributeError
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute with fallback to script variables."""
        # Handle special internal attributes normally
        if name.startswith('_') or name in ['name', 'type', 'parent', 'children', 'properties',
                                           'script_path', 'script_instance', 'visible', 'process_mode']:
            super().__setattr__(name, value)
            return

        # Check if it's a script export variable
        if self.script_instance and hasattr(self.script_instance, 'export_variables'):
            if name in self.script_instance.export_variables:
                self.script_instance.export_variables[name]['value'] = value
                # Also update in namespace if it exists
                if hasattr(self.script_instance, 'namespace') and name in self.script_instance.namespace:
                    self.script_instance.namespace[name] = value
                return

        # Check if it's in script namespace
        if self.script_instance and hasattr(self.script_instance, 'namespace'):
            if name in self.script_instance.namespace:
                self.script_instance.namespace[name] = value
                return

        # Otherwise store in properties or as regular attribute
        if hasattr(self, 'properties'):
            self.properties[name] = value
        else:
            super().__setattr__(name, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a property value with default fallback."""
        try:
            return getattr(self, key)
        except AttributeError:
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a property value."""
        setattr(self, key, value)

    def has_property(self, key: str) -> bool:
        """Check if node has a property."""
        try:
            getattr(self, key)
            return True
        except AttributeError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert node into a JSON-serializable dict. Subclasses extend this.
        """
        from ..json_utils import convert_to_json_serializable

        data: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "visible": self.visible,
            "process_mode": self.process_mode,
            "properties": convert_to_json_serializable(copy.deepcopy(self.properties)),
            "children": [child.to_dict() for child in self.children]
        }
        if self.script_path:
            data["script"] = self.script_path
        if self._groups:
            data["groups"] = self._groups.copy()

        # Ensure all data is JSON serializable
        return convert_to_json_serializable(data)

    @classmethod
    def _apply_node_properties(cls, node: "Node", data: Dict[str, Any]) -> None:
        """
        Apply common properties from a dict to an existing node instance
        (used during from_dict).
        """
        node.visible = data.get("visible", True)
        node.process_mode = data.get("process_mode", "inherit")
        node.properties = copy.deepcopy(data.get("properties", {}))

        # Handle multiple scripts (new format)
        scripts = data.get("scripts", [])
        if scripts:
            # Store scripts array in properties for the game engine to find
            node.properties["scripts"] = scripts

        # Handle legacy single script (backward compatibility)
        script = data.get("script") or data.get("script_path")
        if script:
            node.script_path = str(script)

        # Load groups
        groups = data.get("groups", [])
        for group in groups:
            node.add_to_group(group)

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
