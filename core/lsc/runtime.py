"""
LSC Runtime Environment
Manages script execution, variable scopes, and game engine integration
"""

import time
from typing import Any, Dict, List, Optional, Callable, Union, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .game_engine_interface import GameEngineInterface
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
        return name in self.variables or (self.parent is not None and self.parent.has(name))


class LSCRuntime:
    """Runtime environment for LSC scripts"""
    
    def __init__(self, game_runtime: Optional["GameEngineInterface"] = None):
        """Initialize LSC runtime"""
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

        # Inheritance system
        self.current_extends: Optional[str] = None
        self.inheritance_manager = None  # Will be initialized later

        # Signal system
        self.signals: Dict[str, List[Tuple[Any, str]]] = {}  # signal_name -> [(target, method), ...]
        self.signal_queue: List[Tuple[str, tuple]] = []  # For deferred signal emission

        # Resource cache
        self.resource_cache: Dict[str, Any] = {}

        # Timer system for wait functionality
        self.timers: List[Dict[str, Any]] = []

        # Initialize built-in variables
        self._initialize_builtins()

    def initialize_inheritance_manager(self, project_path=None):
        """Initialize the inheritance manager with project path"""
        from .inheritance import LSCInheritanceManager
        self.inheritance_manager = LSCInheritanceManager(self)
        if project_path:
            self.inheritance_manager.set_project_path(project_path)
    
    def _initialize_builtins(self) -> None:
        """Initialize built-in functions and constants"""
        # Add built-in functions
        for name, func in self.builtins.functions.items():
            self.global_scope.define(name, func)

        # Add built-in constants
        for name, value in self.builtins.constants.items():
            self.global_scope.define(name, value)

        # Add super object for inheritance
        self.global_scope.define('super', self._create_super_object())

        # Add common default values for export variables
        self._add_default_export_values()

    def _add_default_export_values(self) -> None:
        """Add common default values for export variables"""
        from .builtins import Vector2, Rect2, Color, Texture

        # Add base node class placeholders for extends statements
        base_classes = {
            'Node': self._create_node_class_placeholder('Node'),
            'Node2D': self._create_node_class_placeholder('Node2D'),
            'KinematicBody2D': self._create_node_class_placeholder('KinematicBody2D'),
            'StaticBody2D': self._create_node_class_placeholder('StaticBody2D'),
            'RigidBody2D': self._create_node_class_placeholder('RigidBody2D'),
            'Area2D': self._create_node_class_placeholder('Area2D'),
            'Control': self._create_node_class_placeholder('Control'),
            'Sprite': self._create_node_class_placeholder('Sprite'),
            'AnimatedSprite': self._create_node_class_placeholder('AnimatedSprite'),
            'Camera2D': self._create_node_class_placeholder('Camera2D'),
            'CollisionShape2D': self._create_node_class_placeholder('CollisionShape2D'),
            'CollisionPolygon2D': self._create_node_class_placeholder('CollisionPolygon2D'),
        }

        for name, class_obj in base_classes.items():
            self.global_scope.define(name, class_obj)

        # Add Input object for Godot-like input access
        input_obj = self._create_input_object()
        self.global_scope.define('Input', input_obj)

        # Add common default values that scripts might expect
        defaults = {
            'current': False,
            'collision_mask': 1,
            'collision_layer': 1,
            'enable_animations': True,
            'texture': None,
            'null': None,

            # PlayerController specific defaults
            'controller_type': "topdown_8dir",
            'base_speed': 200.0,
            'acceleration': 800.0,
            'friction': 1000.0,
            'max_speed': 400.0,
            'can_sprint': True,
            'sprint_speed_multiplier': 1.5,
            'sprint_acceleration_multiplier': 1.2,
            'sprint_stamina_enabled': False,
            'max_stamina': 100.0,
            'current_stamina': 100.0,
            'stamina_drain_rate': 20.0,
            'stamina_regen_rate': 15.0,
            'gravity': 980.0,
            'jump_height': 400.0,
            'max_fall_speed': 1000.0,
            'coyote_time': 0.1,
            'jump_buffer_time': 0.1,
            'is_on_ground': False,
            'coyote_timer': 0.0,
            'jump_buffer_timer': 0.0,
            'is_sprinting': False,
            'last_direction': Vector2(1, 0),
            'input_vector': Vector2(0, 0),
            'velocity': Vector2(0, 0),

            # Animation defaults
            'idle_animation': "idle",
            'walk_animation': "walk",
            'run_animation': "run",
            'jump_animation': "jump",
            'fall_animation': "fall",

            # Node references
            'animated_sprite_node': None,
            'sprite_node': None,
            'collision_shape_node': None,
            'interaction_area': None,
            'interaction_shape': None,

            # Sprite defaults
            'frame_x': 0,
            'frame_y': 0,
            'hframes': 1,
            'vframes': 1,
            'region_rect': Rect2(0, 0, 0, 0),

            # Camera defaults
            'enabled': True,
        }

        for name, value in defaults.items():
            if not self.global_scope.has(name):
                self.global_scope.define(name, value)

    def _create_node_class_placeholder(self, class_name: str):
        """Create a placeholder class for node inheritance"""
        class NodeClassPlaceholder:
            def __init__(self):
                self.class_name = class_name

            def __call__(self, *args, **kwargs):
                # Return a simple object that can be used for inheritance
                return self

            def __repr__(self):
                return f"<class '{self.class_name}'>"

        return NodeClassPlaceholder()

    def _create_input_object(self):
        """Create an Input object for Godot-like input access"""
        class InputObject:
            def __init__(self, runtime):
                self.runtime = runtime

            def is_action_pressed(self, action: str) -> bool:
                return self.runtime.builtins.is_action_pressed(action)

            def is_action_just_pressed(self, action: str) -> bool:
                return self.runtime.builtins.is_action_just_pressed(action)

            def is_action_just_released(self, action: str) -> bool:
                return self.runtime.builtins.is_action_just_released(action)

            def get_action_strength(self, action: str) -> float:
                return self.runtime.builtins.get_action_strength(action)

        return InputObject(self)

    def _create_super_object(self):
        """Create a super object for calling parent class methods"""
        class SuperObject:
            def __init__(self, runtime):
                self.runtime = runtime

            def _ready(self):
                """Call parent _ready method - placeholder implementation"""
                # In a full implementation, this would call the actual parent class method
                # For now, just provide a no-op implementation
                pass

            def on_ready(self):
                """Call parent on_ready method - placeholder implementation"""
                # In a full implementation, this would call the actual parent class method
                # For now, just provide a no-op implementation
                pass

            def _process(self, delta: float):
                """Call parent _process method - placeholder implementation"""
                pass

            def _physics_process(self, delta: float):
                """Call parent _physics_process method - placeholder implementation"""
                pass

            def __getattr__(self, name):
                """Handle any other super method calls"""
                def super_method(*args, **kwargs):
                    # Placeholder - in a full implementation this would call the parent method
                    pass
                return super_method

        return SuperObject(self)

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

    def get_node_or_null(self, path: str) -> Any:
        """Get node by path or return None if not found"""
        try:
            return self.get_node(path)
        except:
            return None

    def find_node(self, name: str, recursive: bool = True) -> Any:
        """Find node by name"""
        if self.game_runtime:
            return self.game_runtime.find_node(name, recursive)
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
        if self.game_runtime:
            return self.game_runtime.is_action_pressed(action)
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed"""
        if self.game_runtime:
            return self.game_runtime.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released"""
        if self.game_runtime:
            return self.game_runtime.is_action_just_released(action)
        return False

    def get_action_strength(self, action: str) -> float:
        """Get action strength"""
        if self.game_runtime:
            return self.game_runtime.get_action_strength(action)
        return 0.0

    def is_key_pressed(self, key) -> bool:
        """Check if key is pressed"""
        if self.game_runtime:
            return self.game_runtime.is_key_pressed(key)
        return False

    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if mouse button is pressed"""
        if self.game_runtime:
            return self.game_runtime.is_mouse_button_pressed(button)
        return False

    def get_mouse_position(self) -> tuple:
        """Get mouse position"""
        if self.game_runtime:
            return self.game_runtime.get_mouse_position()
        return (0, 0)

    def get_global_mouse_position(self) -> tuple:
        """Get global mouse position"""
        if self.game_runtime:
            return self.game_runtime.get_global_mouse_position()
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
        """Wait for specified time using timer system"""
        # Create a timer for this wait
        timer = {
            'start_time': time.time(),
            'duration': seconds,
            'callback': None,
            'completed': False
        }
        self.timers.append(timer)

        # For now, this is a simple blocking wait
        # In a real game engine, this would yield control back to the main loop
        time.sleep(seconds)

    def create_timer(self, seconds: float, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Create a non-blocking timer"""
        timer = {
            'start_time': time.time(),
            'duration': seconds,
            'callback': callback,
            'completed': False
        }
        self.timers.append(timer)
        return timer

    def update_timers(self) -> None:
        """Update all active timers (should be called each frame)"""
        current_time = time.time()
        completed_timers = []

        for timer in self.timers:
            if not timer['completed']:
                elapsed = current_time - timer['start_time']
                if elapsed >= timer['duration']:
                    timer['completed'] = True
                    if timer['callback'] and callable(timer['callback']):
                        try:
                            timer['callback']()
                        except Exception as e:
                            print(f"Error in timer callback: {e}")
                    completed_timers.append(timer)

        # Remove completed timers
        for timer in completed_timers:
            if timer in self.timers:
                self.timers.remove(timer)

    def clear_timers(self) -> None:
        """Clear all timers"""
        self.timers.clear()
    
    # Signal methods (full implementation)
    def connect(self, signal_name: str, target: Any, method: str) -> None:
        """Connect signal to method"""
        if signal_name not in self.signals:
            self.signals[signal_name] = []

        # Check if already connected
        connection = (target, method)
        if connection not in self.signals[signal_name]:
            self.signals[signal_name].append(connection)

    def disconnect(self, signal_name: str, target: Any, method: str) -> None:
        """Disconnect signal from method"""
        if signal_name in self.signals:
            connection = (target, method)
            if connection in self.signals[signal_name]:
                self.signals[signal_name].remove(connection)

                # Clean up empty signal lists
                if not self.signals[signal_name]:
                    del self.signals[signal_name]

    def emit_signal(self, signal_name: str, *args) -> None:
        """Emit signal"""
        if signal_name in self.signals:
            for target, method_name in self.signals[signal_name]:
                try:
                    if hasattr(target, method_name):
                        method = getattr(target, method_name)
                        if callable(method):
                            method(*args)
                    else:
                        print(f"Warning: Method '{method_name}' not found on target {target}")
                except Exception as e:
                    print(f"Error calling signal handler {method_name}: {e}")

    def is_connected(self, signal_name: str, target: Any, method: str) -> bool:
        """Check if signal is connected"""
        if signal_name not in self.signals:
            return False
        return (target, method) in self.signals[signal_name]

    def disconnect_all(self, signal_name: str) -> None:
        """Disconnect all connections for a signal"""
        if signal_name in self.signals:
            del self.signals[signal_name]

    def get_signal_connections(self, signal_name: str) -> List[Tuple[Any, str]]:
        """Get all connections for a signal"""
        return self.signals.get(signal_name, []).copy()
    
    # Resource methods (basic implementation with caching)
    def load_resource(self, path: str) -> Any:
        """Load resource with caching"""
        # Check cache first
        if path in self.resource_cache:
            return self.resource_cache[path]

        # Try to load the resource
        try:
            from pathlib import Path

            file_path = Path(path)
            if not file_path.exists():
                print(f"Warning: Resource not found: {path}")
                return None

            # Basic file type detection and loading
            extension = file_path.suffix.lower()

            if extension in ['.txt', '.lsc', '.json', '.xml']:
                # Text-based files
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.resource_cache[path] = content
                return content

            elif extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                # Image files - return path for now (actual loading would need PIL/pygame)
                from .builtins import Texture
                texture = Texture(str(file_path))
                self.resource_cache[path] = texture
                return texture

            elif extension in ['.wav', '.mp3', '.ogg']:
                # Audio files - return path for now (actual loading would need pygame/pydub)
                audio_resource = {'type': 'audio', 'path': str(file_path)}
                self.resource_cache[path] = audio_resource
                return audio_resource

            else:
                # Unknown file type - return path
                self.resource_cache[path] = str(file_path)
                return str(file_path)

        except Exception as e:
            print(f"Error loading resource {path}: {e}")
            return None

    def preload_resource(self, path: str) -> Any:
        """Preload resource (same as load for now)"""
        return self.load_resource(path)

    def save_resource(self, resource: Any, path: str) -> None:
        """Save resource to file"""
        try:
            from pathlib import Path

            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Basic saving based on resource type
            if isinstance(resource, str):
                # Text content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(resource)

            elif isinstance(resource, dict):
                # JSON-like data
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(resource, f, indent=2)

            else:
                # Try to convert to string
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(resource))

            # Update cache
            self.resource_cache[path] = resource

        except Exception as e:
            print(f"Error saving resource to {path}: {e}")

    def clear_resource_cache(self) -> None:
        """Clear the resource cache"""
        self.resource_cache.clear()

    def get_cached_resources(self) -> List[str]:
        """Get list of cached resource paths"""
        return list(self.resource_cache.keys())

    def load(self, path: str) -> Any:
        """Load resource (alias for load_resource)"""
        return self.load_resource(path)

    def preload(self, path: str) -> Any:
        """Preload resource (alias for preload_resource)"""
        return self.preload_resource(path)

    def save(self, resource: Any, path: str) -> None:
        """Save resource (alias for save_resource)"""
        self.save_resource(resource, path)


class LSCScriptInstance:
    """Represents an instance of an LSC script attached to a node"""

    def __init__(self, node: Any, script_path: str, runtime: LSCRuntime, base_class: Optional[str] = None):
        self.node = node
        self.script_path = script_path
        self.runtime = runtime
        self.base_class = base_class
        self.lsc_class = None

        # Create scope with inheritance support
        if runtime.inheritance_manager and base_class:
            self.scope = runtime.inheritance_manager.create_instance_scope(base_class)
            self.lsc_class = runtime.inheritance_manager.get_class(base_class)
        else:
            self.scope = LSCScope(runtime.global_scope)

        if not self.scope:
            self.scope = LSCScope(runtime.global_scope)

        self.export_variables: Dict[str, Any] = {}

        # Lifecycle flags
        self.ready_called = False
        self.enabled = True

        # Setup proper super object if we have inheritance
        if self.lsc_class and runtime.inheritance_manager:
            super_obj = runtime.inheritance_manager.create_super_object(self.lsc_class, self.scope)
            self.scope.define('super', super_obj)
    
    def call_method(self, method_name: str, *args) -> Any:
        """Call a method on this script instance"""
        if not self.enabled or not self.scope:
            return None

        # Set up scope for method call
        old_scope = self.runtime.current_scope
        self.runtime.current_scope = self.scope

        try:
            # Get method from scope
            if self.scope.has(method_name):
                method = self.scope.get(method_name)
                if callable(method):
                    # Debug output for _physics_process
                    if method_name == "_physics_process":
                        print(f"Calling {method_name} with args: {args} in scope: {self.scope} on node: {self.node}")

                    return method(*args)
            else:
                # Debug output for missing methods
                if method_name == "_physics_process":
                    all_vars = list(self.scope.variables.keys())
                    callable_vars = [k for k in self.scope.variables.keys() if callable(self.scope.variables.get(k, None))]
                    print(f"Method {method_name} not found in scope: {self.scope} on node: {self.node}")
                    print(f"All variables in scope: {all_vars}")
                    print(f"Callable variables in scope: {callable_vars}")
                    print(f"Node: {self.node}")
        finally:
            # Restore scope
            self.runtime.current_scope = old_scope

        return None
    
    def set_export_variable(self, name: str, value: Any) -> None:
        """Set an export variable value"""
        self.export_variables[name] = value
        if self.scope:
            self.scope.set(name, value)
    
    def get_export_variable(self, name: str) -> Any:
        """Get an export variable value"""
        return self.export_variables.get(name)
    
    def get_all_export_variables(self) -> Dict[str, Any]:
        """Get all export variables"""
        return self.export_variables.copy()
