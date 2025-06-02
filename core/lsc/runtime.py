"""
LSC Runtime Environment
Manages script execution, variable scopes, and game engine integration
"""

import time
from typing import Any, Dict, List, Optional, Callable, Union
from .export_system import ExportSystem
from .builtins import LSCBuiltins


class LSCScope:
    """Represents a variable scope in LSC"""
    
    def __init__(self, parent: Optional['LSCScope'] = None):
        self.parent = parent
        self.variables: Dict[str, Any] = {}
    
    def define(self, name: str, value: Any) -> None:
        """Define a variable in this scope"""
        self.variables[name] = value
    
    def get(self, name: str) -> Any:
        """Get a variable value"""
        if name in self.variables:
            return self.variables[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            raise NameError(f"Undefined variable '{name}'")
    
    def set(self, name: str, value: Any) -> None:
        """Set a variable value"""
        if name in self.variables:
            self.variables[name] = value
        elif self.parent and self.parent.has(name):
            self.parent.set(name, value)
        else:
            # Define in current scope if not found
            self.variables[name] = value
    
    def has(self, name: str) -> bool:
        """Check if variable exists"""
        return name in self.variables or (self.parent and self.parent.has(name))


class LSCRuntime:
    """Runtime environment for LSC scripts"""
    
    def __init__(self, game_runtime=None):
        self.game_runtime = game_runtime
        self.global_scope = LSCScope()
        self.current_scope = self.global_scope
        self.scope_stack: List[LSCScope] = [self.global_scope]
        
        # Systems
        self.export_system = ExportSystem()
        self.builtins = LSCBuiltins(self)
        
        # Runtime state
        self.start_time = time.time()
        self.last_frame_time = time.time()
        self.delta_time = 0.0
        self.frame_count = 0
        
        # Script instances
        self.script_instances: Dict[Any, 'LSCScriptInstance'] = {}
        
        # Initialize built-in variables
        self._initialize_builtins()
    
    def _initialize_builtins(self) -> None:
        """Initialize built-in functions and constants"""
        # Add built-in functions
        for name, func in self.builtins.functions.items():
            self.global_scope.define(name, func)
        
        # Add built-in constants
        for name, value in self.builtins.constants.items():
            self.global_scope.define(name, value)
    
    def push_scope(self) -> LSCScope:
        """Push a new scope onto the stack"""
        new_scope = LSCScope(self.current_scope)
        self.scope_stack.append(new_scope)
        self.current_scope = new_scope
        return new_scope
    
    def pop_scope(self) -> Optional[LSCScope]:
        """Pop the current scope from the stack"""
        if len(self.scope_stack) > 1:
            popped = self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]
            return popped
        return None
    
    def define_variable(self, name: str, value: Any) -> None:
        """Define a variable in current scope"""
        self.current_scope.define(name, value)
    
    def get_variable(self, name: str) -> Any:
        """Get a variable value"""
        return self.current_scope.get(name)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value"""
        self.current_scope.set(name, value)
    
    def has_variable(self, name: str) -> bool:
        """Check if variable exists"""
        return self.current_scope.has(name)
    
    def update_time(self, delta: float) -> None:
        """Update runtime timing"""
        self.delta_time = delta
        self.last_frame_time = time.time()
        self.frame_count += 1
    
    # Game engine integration methods (to be implemented by game runtime)
    def get_node(self, path: str) -> Any:
        """Get node by path"""
        if self.game_runtime:
            return self.game_runtime.get_node(path)
        return None
    
    def find_node(self, name: str) -> Any:
        """Find node by name"""
        if self.game_runtime:
            return self.game_runtime.find_node(name)
        return None
    
    def get_parent(self, node: Any) -> Any:
        """Get parent node"""
        if hasattr(node, 'parent'):
            return node.parent
        return None
    
    def get_children(self, node: Any) -> List[Any]:
        """Get child nodes"""
        if hasattr(node, 'children'):
            return list(node.children)
        return []
    
    def add_child(self, parent: Any, child: Any) -> None:
        """Add child node"""
        if hasattr(parent, 'add_child'):
            parent.add_child(child)
    
    def remove_child(self, parent: Any, child: Any) -> None:
        """Remove child node"""
        if hasattr(parent, 'remove_child'):
            parent.remove_child(child)
    
    def queue_free(self, node: Any) -> None:
        """Queue node for deletion"""
        if hasattr(node, 'queue_free'):
            node.queue_free()
    
    def duplicate(self, node: Any) -> Any:
        """Duplicate node"""
        if hasattr(node, 'duplicate'):
            return node.duplicate()
        return None
    
    def is_inside_tree(self, node: Any) -> bool:
        """Check if node is in scene tree"""
        if hasattr(node, 'is_inside_tree'):
            return node.is_inside_tree()
        return False
    
    def get_tree(self) -> Any:
        """Get scene tree"""
        if self.game_runtime:
            return self.game_runtime.get_tree()
        return None
    
    def change_scene(self, path: str) -> None:
        """Change to different scene"""
        if self.game_runtime:
            self.game_runtime.change_scene(path)
    
    def reload_scene(self) -> None:
        """Reload current scene"""
        if self.game_runtime:
            self.game_runtime.reload_scene()
    
    def get_scene(self) -> Any:
        """Get current scene"""
        if self.game_runtime:
            return self.game_runtime.get_scene()
        return None
    
    # Input methods
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is pressed"""
        if self.game_runtime and hasattr(self.game_runtime, 'input_manager'):
            return self.game_runtime.input_manager.is_action_pressed(action)
        return False
    
    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed"""
        if self.game_runtime and hasattr(self.game_runtime, 'input_manager'):
            return self.game_runtime.input_manager.is_action_just_pressed(action)
        return False
    
    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released"""
        if self.game_runtime and hasattr(self.game_runtime, 'input_manager'):
            return self.game_runtime.input_manager.is_action_just_released(action)
        return False
    
    def get_action_strength(self, action: str) -> float:
        """Get action strength"""
        if self.game_runtime and hasattr(self.game_runtime, 'input_manager'):
            return self.game_runtime.input_manager.get_action_strength(action)
        return 0.0
    
    def is_key_pressed(self, key) -> bool:
        """Check if key is pressed"""
        if self.game_runtime and hasattr(self.game_runtime, 'is_key_pressed'):
            return self.game_runtime.is_key_pressed(key)
        return False
    
    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if mouse button is pressed"""
        if self.game_runtime and hasattr(self.game_runtime, 'input_manager'):
            return self.game_runtime.input_manager.is_mouse_button_pressed(button)
        return False
    
    def get_mouse_position(self) -> tuple:
        """Get mouse position"""
        if self.game_runtime and hasattr(self.game_runtime, 'input_manager'):
            return self.game_runtime.input_manager.get_mouse_position()
        return (0, 0)
    
    def get_global_mouse_position(self) -> tuple:
        """Get global mouse position"""
        if self.game_runtime and hasattr(self.game_runtime, 'input_manager'):
            return self.game_runtime.input_manager.get_global_mouse_position()
        return (0, 0)
    
    # Time methods
    def get_time(self) -> float:
        """Get current time"""
        return time.time() - self.start_time
    
    def get_delta(self) -> float:
        """Get delta time"""
        return self.delta_time
    
    def get_fps(self) -> float:
        """Get current FPS"""
        if self.delta_time > 0:
            return 1.0 / self.delta_time
        return 0.0

    def get_runtime_time(self) -> float:
        """Get runtime time (alias for get_time for LSC scripts)"""
        return self.get_time()

    def wait(self, seconds: float) -> None:
        """Wait for specified time (placeholder - would need coroutine system)"""
        # This would need to be implemented with a proper coroutine/async system
        pass
    
    # Signal methods (placeholder implementations)
    def connect(self, signal_name: str, target: Any, method: str) -> None:
        """Connect signal to method"""
        # Would need proper signal system implementation
        pass
    
    def disconnect(self, signal_name: str, target: Any, method: str) -> None:
        """Disconnect signal from method"""
        # Would need proper signal system implementation
        pass
    
    def emit_signal(self, signal_name: str, *args) -> None:
        """Emit signal"""
        # Would need proper signal system implementation
        pass
    
    def is_connected(self, signal_name: str, target: Any, method: str) -> bool:
        """Check if signal is connected"""
        # Would need proper signal system implementation
        return False
    
    # Resource methods (placeholder implementations)
    def load_resource(self, path: str) -> Any:
        """Load resource"""
        # Would need proper resource loading system
        return None
    
    def preload_resource(self, path: str) -> Any:
        """Preload resource"""
        # Would need proper resource loading system
        return None
    
    def save_resource(self, resource: Any, path: str) -> None:
        """Save resource"""
        # Would need proper resource saving system
        pass


class LSCScriptInstance:
    """Represents an instance of an LSC script attached to a node"""
    
    def __init__(self, node: Any, script_path: str, runtime: LSCRuntime):
        self.node = node
        self.script_path = script_path
        self.runtime = runtime
        self.scope = LSCScope(runtime.global_scope)
        self.export_variables: Dict[str, Any] = {}
        
        # Lifecycle flags
        self.ready_called = False
        self.enabled = True
    
    def call_method(self, method_name: str, *args) -> Any:
        """Call a method on this script instance"""
        if not self.enabled:
            return None
        
        # Set up scope for method call
        old_scope = self.runtime.current_scope
        self.runtime.current_scope = self.scope
        
        try:
            # Get method from scope
            if self.scope.has(method_name):
                method = self.scope.get(method_name)
                if callable(method):
                    return method(*args)
        finally:
            # Restore scope
            self.runtime.current_scope = old_scope
        
        return None
    
    def set_export_variable(self, name: str, value: Any) -> None:
        """Set an export variable value"""
        self.export_variables[name] = value
        self.scope.set(name, value)
    
    def get_export_variable(self, name: str) -> Any:
        """Get an export variable value"""
        return self.export_variables.get(name)
    
    def get_all_export_variables(self) -> Dict[str, Any]:
        """Get all export variables"""
        return self.export_variables.copy()
