"""
LSC Built-in Functions and Game Engine Integration
Provides all the built-in functions available in LSC scripts
"""

import math
import random
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .runtime import LSCRuntime


class LSCVector2:
    """2D Vector class for LSC with Godot-like methods"""

    def __init__(self, x: float = 0, y: float = 0):
        # Handle case where x or y might be Vector2 objects
        if hasattr(x, 'x'):
            self.x = float(x.x)
        else:
            self.x = float(x)

        if hasattr(y, 'y'):
            self.y = float(y.y)
        else:
            self.y = float(y)

    def __repr__(self):
        return f"Vector2({self.x}, {self.y})"

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __getitem__(self, index):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Vector2 index out of range")

    def __setitem__(self, index, value):
        if index == 0:
            self.x = float(value)
        elif index == 1:
            self.y = float(value)
        else:
            raise IndexError("Vector2 index out of range")

    def __add__(self, other):
        if isinstance(other, (LSCVector2, tuple, list)):
            return LSCVector2(self.x + other[0], self.y + other[1])
        return LSCVector2(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, (LSCVector2, tuple, list)):
            return LSCVector2(self.x - other[0], self.y - other[1])
        return LSCVector2(self.x - other, self.y - other)

    def __mul__(self, other):
        if isinstance(other, (LSCVector2, tuple, list)):
            return LSCVector2(self.x * other[0], self.y * other[1])
        return LSCVector2(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, (LSCVector2, tuple, list)):
            return LSCVector2(self.x / other[0], self.y / other[1])
        return LSCVector2(self.x / other, self.y / other)

    def __eq__(self, other):
        if isinstance(other, (LSCVector2, tuple, list)):
            return abs(self.x - other[0]) < 1e-6 and abs(self.y - other[1]) < 1e-6
        return False

    def length(self) -> float:
        """Get the length of the vector"""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_squared(self) -> float:
        """Get the squared length of the vector"""
        return self.x * self.x + self.y * self.y

    def normalized(self) -> 'LSCVector2':
        """Get normalized vector"""
        length = self.length()
        if length == 0:
            return LSCVector2(0, 0)
        return LSCVector2(self.x / length, self.y / length)

    def normalize(self) -> 'LSCVector2':
        """Normalize this vector in place"""
        length = self.length()
        if length != 0:
            self.x /= length
            self.y /= length
        return self

    def distance_to(self, other) -> float:
        """Get distance to another vector"""
        dx = self.x - other[0]
        dy = self.y - other[1]
        return math.sqrt(dx * dx + dy * dy)

    def distance_squared_to(self, other) -> float:
        """Get squared distance to another vector"""
        dx = self.x - other[0]
        dy = self.y - other[1]
        return dx * dx + dy * dy

    def dot(self, other) -> float:
        """Dot product with another vector"""
        return self.x * other[0] + self.y * other[1]

    def cross(self, other) -> float:
        """Cross product with another vector (returns scalar for 2D)"""
        return self.x * other[1] - self.y * other[0]

    def angle(self) -> float:
        """Get angle of vector in radians"""
        return math.atan2(self.y, self.x)

    def angle_to(self, other) -> float:
        """Get angle to another vector"""
        return math.atan2(self.cross(other), self.dot(other))

    def angle_to_point(self, other) -> float:
        """Get angle to a point"""
        return math.atan2(other[1] - self.y, other[0] - self.x)

    def lerp(self, other, t: float) -> 'LSCVector2':
        """Linear interpolation to another vector"""
        return LSCVector2(
            self.x + (other[0] - self.x) * t,
            self.y + (other[1] - self.y) * t
        )

    def move_toward(self, target, delta: float) -> 'LSCVector2':
        """Move toward target by delta amount"""
        if isinstance(target, (LSCVector2, tuple, list)):
            target_vec = LSCVector2(target[0], target[1])
        else:
            target_vec = target

        diff = target_vec - self
        distance = diff.length()

        if distance <= delta:
            return target_vec
        else:
            return self + diff.normalized() * delta

    def slide(self, normal) -> 'LSCVector2':
        """Slide along a surface normal"""
        normal_vec = LSCVector2(normal[0], normal[1]) if not isinstance(normal, LSCVector2) else normal
        return self - normal_vec * self.dot(normal_vec)

    def reflect(self, normal) -> 'LSCVector2':
        """Reflect off a surface normal"""
        normal_vec = LSCVector2(normal[0], normal[1]) if not isinstance(normal, LSCVector2) else normal
        return self - normal_vec * 2 * self.dot(normal_vec)

    def rotated(self, angle: float) -> 'LSCVector2':
        """Get rotated vector"""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return LSCVector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )

    def abs(self) -> 'LSCVector2':
        """Get absolute value vector"""
        return LSCVector2(abs(self.x), abs(self.y))

    def sign(self) -> 'LSCVector2':
        """Get sign vector"""
        return LSCVector2(
            1 if self.x > 0 else -1 if self.x < 0 else 0,
            1 if self.y > 0 else -1 if self.y < 0 else 0
        )

    def floor(self) -> 'LSCVector2':
        """Get floor vector"""
        return LSCVector2(math.floor(self.x), math.floor(self.y))

    def ceil(self) -> 'LSCVector2':
        """Get ceiling vector"""
        return LSCVector2(math.ceil(self.x), math.ceil(self.y))

    def round(self) -> 'LSCVector2':
        """Get rounded vector"""
        return LSCVector2(round(self.x), round(self.y))


class Vector2Factory:
    """Factory class for Vector2 with constants as properties"""

    def __call__(self, x: float = 0, y: float = 0) -> LSCVector2:
        """Create a new Vector2"""
        return LSCVector2(x, y)

    @property
    def ZERO(self) -> LSCVector2:
        return LSCVector2(0, 0)

    @property
    def ONE(self) -> LSCVector2:
        return LSCVector2(1, 1)

    @property
    def UP(self) -> LSCVector2:
        return LSCVector2(0, 1)  # Y+ is up in our coordinate system

    @property
    def DOWN(self) -> LSCVector2:
        return LSCVector2(0, -1)  # Y- is down in our coordinate system

    @property
    def LEFT(self) -> LSCVector2:
        return LSCVector2(-1, 0)

    @property
    def RIGHT(self) -> LSCVector2:
        return LSCVector2(1, 0)


class LSCRect2:
    """2D Rectangle class for LSC with Godot-like methods"""

    def __init__(self, x=0, y=0, width=0, height=0):
        # Handle case where x might be a Vector2 (position) and y might be a Vector2 (size)
        if hasattr(x, 'x') and hasattr(x, 'y') and hasattr(y, 'x') and hasattr(y, 'y'):
            # Called as Rect2(position_vector, size_vector)
            self.position = LSCVector2(x.x, x.y)
            self.size = LSCVector2(y.x, y.y)
        else:
            # Called as Rect2(x, y, width, height)
            self.position = LSCVector2(float(x), float(y))
            self.size = LSCVector2(float(width), float(height))

    def __repr__(self):
        return f"Rect2({self.position.x}, {self.position.y}, {self.size.x}, {self.size.y})"

    def __str__(self):
        return f"({self.position.x}, {self.position.y}, {self.size.x}, {self.size.y})"

    @property
    def x(self) -> float:
        return self.position.x

    @x.setter
    def x(self, value: float):
        self.position.x = value

    @property
    def y(self) -> float:
        return self.position.y

    @y.setter
    def y(self, value: float):
        self.position.y = value

    @property
    def width(self) -> float:
        return self.size.x

    @width.setter
    def width(self, value: float):
        self.size.x = value

    @property
    def height(self) -> float:
        return self.size.y

    @height.setter
    def height(self, value: float):
        self.size.y = value

    def get_area(self) -> float:
        """Get the area of the rectangle"""
        return self.size.x * self.size.y

    def has_point(self, point) -> bool:
        """Check if point is inside rectangle"""
        px, py = point[0], point[1]
        return (px >= self.position.x and px <= self.position.x + self.size.x and
                py >= self.position.y and py <= self.position.y + self.size.y)

    def intersects(self, other) -> bool:
        """Check if this rectangle intersects with another"""
        return not (self.position.x + self.size.x < other.position.x or
                   other.position.x + other.size.x < self.position.x or
                   self.position.y + self.size.y < other.position.y or
                   other.position.y + other.size.y < self.position.y)


class LSCColor:
    """Color class for LSC with Godot-like methods"""

    def __init__(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1):
        self.r = float(r)
        self.g = float(g)
        self.b = float(b)
        self.a = float(a)

    def __repr__(self):
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"

    def __str__(self):
        return f"({self.r}, {self.g}, {self.b}, {self.a})"

    def __getitem__(self, index):
        if index == 0: return self.r
        elif index == 1: return self.g
        elif index == 2: return self.b
        elif index == 3: return self.a
        else: raise IndexError("Color index out of range")

    def __setitem__(self, index, value):
        if index == 0: self.r = float(value)
        elif index == 1: self.g = float(value)
        elif index == 2: self.b = float(value)
        elif index == 3: self.a = float(value)
        else: raise IndexError("Color index out of range")

    def lerp(self, other, t: float) -> 'LSCColor':
        """Linear interpolation to another color"""
        return LSCColor(
            self.r + (other.r - self.r) * t,
            self.g + (other.g - self.g) * t,
            self.b + (other.b - self.b) * t,
            self.a + (other.a - self.a) * t
        )


class LSCTexture:
    """Placeholder texture class for LSC"""

    def __init__(self, path: str = ""):
        self.path = path
        self._size = LSCVector2(64, 64)  # Default size

    def get_size(self) -> LSCVector2:
        """Get texture size"""
        return self._size

    def __repr__(self):
        return f"Texture('{self.path}')"


class LSCBuiltins:
    """Built-in functions for LSC language"""

    def __init__(self, runtime: 'LSCRuntime'):
        self.runtime = runtime
        self.vector2_factory = Vector2Factory()
        self.functions = self._create_builtin_functions()
        self.constants = self._create_constants()

    def _create_builtin_functions(self) -> Dict[str, Callable]:
        """Create dictionary of all built-in functions"""
        return {
            # Math functions
            'abs': abs,
            'min': min,
            'max': max,
            'round': round,
            'floor': math.floor,
            'ceil': math.ceil,
            'sqrt': math.sqrt,
            'pow': pow,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'atan2': math.atan2,
            'deg2rad': math.radians,
            'rad2deg': math.degrees,
            'lerp': self.lerp,
            'clamp': self.clamp,
            'sign': self.sign,
            'move_toward': self.move_toward,
            'smoothstep': self.smoothstep,

            # Debug functions
            'print': self.lsc_print,
            'print_error': self.lsc_print_error,

            # Type conversion
            'bool': bool,
            'int': int,
            'float': float,

            # Vector operations
            'Vector2': self.vector2_factory,
            'vec2': self.vector2_factory,

            # Random functions
            'rand_range': self.rand_range,
            'rand_int': self.rand_int,
            'randf': random.random,
            'randi': self.randi,
            'rand_seed': random.seed,
            
            # String functions
            'str': str,
            'len': len,
            'substr': self.substr,
            'find': self.find,
            'replace': self.replace,
            'split': self.split,
            'join': self.join,
            'to_upper': str.upper,
            'to_lower': str.lower,
            'strip': str.strip,
            
            # Array functions
            'append': self.append,
            'insert': self.insert,
            'remove': self.remove,
            'pop': self.pop,
            'size': len,
            'empty': self.empty,
            'has': self.has,
            'find_index': self.find_index,
            'sort': self.sort,
            'reverse': self.reverse,
            
            # Type functions
            'typeof': type,
            'is_instance': isinstance,
            'int': int,
            'float': float,
            'bool': bool,
            
            # Print and debug
            'print': self.print,
            'print_debug': self.print_debug,
            'print_error': self.print_error,
            'assert': self.assert_func,
            
            # Node functions
            'get_node': self.get_node,
            'find_node': self.find_node,
            'get_parent': self.get_parent,
            'get_children': self.get_children,
            'add_child': self.add_child,
            'remove_child': self.remove_child,
            'queue_free': self.queue_free,
            'duplicate': self.duplicate,
            'is_inside_tree': self.is_inside_tree,
            'get_tree': self.get_tree,
            
            # Scene functions
            'change_scene': self.change_scene,
            'reload_scene': self.reload_scene,
            'get_scene': self.get_scene,
            
            # Input functions
            'is_action_pressed': self.is_action_pressed,
            'is_action_just_pressed': self.is_action_just_pressed,
            'is_action_just_released': self.is_action_just_released,
            'get_action_strength': self.get_action_strength,
            'is_key_pressed': self.is_key_pressed,
            'is_mouse_button_pressed': self.is_mouse_button_pressed,
            'get_mouse_position': self.get_mouse_position,
            'get_global_mouse_position': self.get_global_mouse_position,

            # Time functions
            'get_time': self.get_time,
            'get_runtime_time': self.get_runtime_time,
            'get_delta': self.get_delta,
            'get_fps': self.get_fps,
            'wait': self.wait,

            # Physics functions
            '_physics_process': self._physics_process,

            # Signal functions
            'connect': self.connect,
            'disconnect': self.disconnect,
            'emit_signal': self.emit_signal,
            'is_connected': self.is_connected,

            # Resource functions
            'load': self.load_resource,
            'preload': self.preload_resource,
            'save': self.save_resource,

            # Vector functions
            'Vector2': self.vector2_factory,
            'Vector3': self.Vector3,
            'distance': self.distance,
            'dot_product': self.dot_product,
            'cross_product': self.cross_product,
            'normalize': self.normalize,
            'move_toward': self.move_toward,

            # Geometry functions
            'Rect2': self.Rect2,
            'Color': self.Color,
            'Texture': self.Texture,
            'color_lerp': self.color_lerp,

            # Node functions
            'get_node': self.get_node,
            'get_node_or_null': self.get_node_or_null,
            'get_path_to': self.get_path_to,
            'has_method': self.has_method,
            'has_property': self.has_property,
            'has_signal': self.has_signal,
            'hasattr': self.hasattr,

            # Engine functions
            'get_viewport_rect': self.get_viewport_rect,
            'get_process_delta_time': self.get_process_delta_time,
            'is_on_floor': self.is_on_floor,
            'move_and_slide': self.move_and_slide,
        }

    def _create_constants(self) -> Dict[str, Any]:
        """Create dictionary of constants"""
        return {
            'PI': math.pi,
            'TAU': math.tau,
            'E': math.e,
            'INF': math.inf,
            'NAN': math.nan,
        }

    def get_function(self, name: str) -> Optional[Callable]:
        """Get built-in function by name"""
        return self.functions.get(name)

    def get_constant(self, name: str) -> Optional[Any]:
        """Get built-in constant by name"""
        return self.constants.get(name)
    
    # Math utility functions
    def lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation"""
        return a + (b - a) * t
    
    def clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max"""
        return max(min_val, min(max_val, value))
    
    def sign(self, value: float) -> int:
        """Return sign of value"""
        if value > 0:
            return 1
        elif value < 0:
            return -1
        else:
            return 0
    
    # Random functions
    def rand_range(self, min_val: float, max_val: float) -> float:
        """Random float in range"""
        return random.uniform(min_val, max_val)
    
    def rand_int(self, min_val: int, max_val: int) -> int:
        """Random integer in range"""
        return random.randint(min_val, max_val)
    
    def randi(self) -> int:
        """Random 32-bit integer"""
        return random.randint(0, 2**31 - 1)
    
    # String functions
    def substr(self, string: str, start: int, length: int = -1) -> str:
        """Get substring"""
        if length == -1:
            return string[start:]
        return string[start:start + length]
    
    def find(self, string: str, substring: str) -> int:
        """Find substring index"""
        try:
            return string.index(substring)
        except ValueError:
            return -1
    
    def replace(self, string: str, old: str, new: str) -> str:
        """Replace substring"""
        return string.replace(old, new)
    
    def split(self, string: str, delimiter: str = " ") -> List[str]:
        """Split string"""
        return string.split(delimiter)
    
    def join(self, array: List[str], delimiter: str = "") -> str:
        """Join array into string"""
        return delimiter.join(array)
    
    # Array functions
    def append(self, array: List[Any], item: Any) -> None:
        """Append item to array"""
        array.append(item)
    
    def insert(self, array: List[Any], index: int, item: Any) -> None:
        """Insert item at index"""
        array.insert(index, item)
    
    def remove(self, array: List[Any], item: Any) -> None:
        """Remove item from array"""
        if item in array:
            array.remove(item)
    
    def pop(self, array: List[Any], index: int = -1) -> Any:
        """Remove and return item at index"""
        return array.pop(index)
    
    def empty(self, array: List[Any]) -> bool:
        """Check if array is empty"""
        return len(array) == 0
    
    def has(self, array: List[Any], item: Any) -> bool:
        """Check if array contains item"""
        return item in array
    
    def find_index(self, array: List[Any], item: Any) -> int:
        """Find index of item in array"""
        try:
            return array.index(item)
        except ValueError:
            return -1
    
    def sort(self, array: List[Any]) -> None:
        """Sort array in place"""
        array.sort()
    
    def reverse(self, array: List[Any]) -> None:
        """Reverse array in place"""
        array.reverse()
    
    # Print and debug functions
    def print(self, *args) -> None:
        """Print to console"""
        print(*args)
    
    def print_debug(self, *args) -> None:
        """Print debug message"""
        print("[DEBUG]", *args)
    
    def print_error(self, *args) -> None:
        """Print error message"""
        print("[ERROR]", *args)
    
    def assert_func(self, condition: bool, message: str = "Assertion failed") -> None:
        """Assert condition"""
        if not condition:
            raise AssertionError(message)

    # Node functions (these will be implemented by the runtime)

    def find_node(self, name: str) -> Any:
        """Find node by name"""
        return self.runtime.find_node(name)

    def get_parent(self, node: Any) -> Any:
        """Get parent node"""
        return self.runtime.get_parent(node)

    def get_children(self, node: Any) -> List[Any]:
        """Get child nodes"""
        return self.runtime.get_children(node)

    def add_child(self, parent: Any, child: Any) -> None:
        """Add child node"""
        self.runtime.add_child(parent, child)

    def remove_child(self, parent: Any, child: Any) -> None:
        """Remove child node"""
        self.runtime.remove_child(parent, child)

    def queue_free(self, node: Any) -> None:
        """Queue node for deletion"""
        self.runtime.queue_free(node)

    def duplicate(self, node: Any) -> Any:
        """Duplicate node"""
        return self.runtime.duplicate(node)

    def is_inside_tree(self, node: Any) -> bool:
        """Check if node is in scene tree"""
        return self.runtime.is_inside_tree(node)

    def get_tree(self) -> Any:
        """Get scene tree"""
        return self.runtime.get_tree()

    # Scene functions
    def change_scene(self, path: str) -> None:
        """Change to different scene"""
        self.runtime.change_scene(path)

    def reload_scene(self) -> None:
        """Reload current scene"""
        self.runtime.reload_scene()

    def get_scene(self) -> Any:
        """Get current scene"""
        return self.runtime.get_scene()

    # Node functions
    def get_node(self, path: str):
        """Get node by path"""
        # Placeholder implementation - would need proper node tree
        return None

    def get_node_or_null(self, path: str):
        """Get node by path or return null"""
        return self.get_node(path)



    def get_path_to(self, node) -> str:
        """Get path to node"""
        # Placeholder implementation
        return ""

    def has_method(self, obj, method_name: str) -> bool:
        """Check if object has method"""
        return hasattr(obj, method_name) and callable(getattr(obj, method_name))

    def has_property(self, obj, property_name: str) -> bool:
        """Check if object has property"""
        return hasattr(obj, property_name)

    def hasattr(self, obj, name: str) -> bool:
        """Check if object has attribute (Python hasattr equivalent)"""
        return hasattr(obj, name)

    def has_signal(self, obj, signal_name: str) -> bool:
        """Check if object has signal"""
        # Placeholder implementation
        return hasattr(obj, signal_name)

    # Engine functions
    def get_viewport_rect(self):
        """Get viewport rectangle"""
        # Return default viewport size
        return LSCRect2(0, 0, 1280, 720)

    def get_process_delta_time(self) -> float:
        """Get process delta time"""
        if self.runtime:
            return self.runtime.delta_time
        return 0.016  # Default 60 FPS

    def is_on_floor(self) -> bool:
        """Check if on floor (placeholder)"""
        return False

    def move_and_slide(self, velocity, up_direction=None):
        """Move and slide - applies velocity to node position"""
        # Debug: Check if move_and_slide is being called
        if hasattr(velocity, 'x') and hasattr(velocity, 'y') and (velocity.x != 0 or velocity.y != 0):
            print(f"DEBUG: move_and_slide called with velocity: ({velocity.x}, {velocity.y})")

        # Get the current node from the scope
        if hasattr(self.runtime, 'current_scope') and self.runtime.current_scope:
            scope = self.runtime.current_scope
            if scope.has('node'):
                node = scope.get('node')
                if hasattr(node, 'position') and hasattr(velocity, 'x') and hasattr(velocity, 'y'):
                    # Apply velocity to position (velocity is in pixels per second, so multiply by delta)
                    delta = 1.0/60.0  # Default delta time

                    # Ensure position is persistent - use a special attribute to store the actual position
                    if not hasattr(node, '_runtime_position'):
                        # Initialize runtime position from current position
                        if hasattr(node.position, 'x'):  # Vector2
                            node._runtime_position = LSCVector2(node.position.x, node.position.y)
                        elif isinstance(node.position, (list, tuple)) and len(node.position) >= 2:
                            node._runtime_position = LSCVector2(node.position[0], node.position[1])
                        else:
                            node._runtime_position = LSCVector2(0.0, 0.0)

                    old_pos = (node._runtime_position.x, node._runtime_position.y)

                    # Apply movement to runtime position
                    node._runtime_position.x += velocity.x * delta
                    node._runtime_position.y += velocity.y * delta

                    # Update the node's position to match runtime position
                    # IMPORTANT: Always create a new Vector2 to ensure the position is properly updated
                    node.position = LSCVector2(node._runtime_position.x, node._runtime_position.y)

                    if velocity.x != 0 or velocity.y != 0:
                        print(f"DEBUG: Updated node.position to ({node.position.x}, {node.position.y})")

                    if velocity.x != 0 or velocity.y != 0:
                        new_pos = (node._runtime_position.x, node._runtime_position.y)
                        print(f"DEBUG: {node.name} position: {old_pos} -> {new_pos}")
                        print(f"DEBUG: Runtime position object ID: {id(node._runtime_position)}, Position type: {type(node._runtime_position)}")

                    # Check if node has physics body and sync position if needed
                    if hasattr(node, 'physics_body') and node.physics_body:
                        if hasattr(node.physics_body, 'pymunk_body') and node.physics_body.pymunk_body:
                            # Sync position from physics body
                            node.position = (node.physics_body.pymunk_body.position.x,
                                            node.physics_body.pymunk_body.position.y)
                            if velocity.x != 0 or velocity.y != 0:
                                print(f"DEBUG: Synced position from physics body: ({node.position[0]}, {node.position[1]})")
                        else:
                            if velocity.x != 0 or velocity.y != 0:
                                print(f"DEBUG: Node {node.name} has physics_body but no pymunk_body")
                    else:
                        if velocity.x != 0 or velocity.y != 0:
                            print(f"DEBUG: Node {node.name} has no physics_body")

                    # Update any associated arcade sprite
                    if hasattr(node, 'arcade_sprite') and node.arcade_sprite:
                        old_sprite_pos = (node.arcade_sprite.center_x, node.arcade_sprite.center_y)

                        # Handle both Vector2 and list positions
                        if hasattr(node.position, 'x'):  # Vector2
                            new_x, new_y = node.position.x, node.position.y
                        else:  # List/tuple
                            new_x, new_y = node.position[0], node.position[1]

                        node.arcade_sprite.center_x = new_x
                        node.arcade_sprite.center_y = new_y

                        # Debug output for movement
                        if velocity.x != 0 or velocity.y != 0:
                            print(f"MOVE: Updated parent sprite {node.name} from {old_sprite_pos} to ({new_x}, {new_y})")
                    else:
                        if velocity.x != 0 or velocity.y != 0:
                            print(f"DEBUG: Node {node.name} has no arcade_sprite")

                    # Also update child sprites (for KinematicBody2D with child Sprite nodes)
                    if hasattr(node, 'children'):
                        for child in node.children:
                            if hasattr(child, 'arcade_sprite') and child.arcade_sprite:
                                old_child_pos = (child.arcade_sprite.center_x, child.arcade_sprite.center_y)
                                # Child sprites should be positioned relative to their parent
                                child_world_x = node.position[0] + child.position[0]
                                child_world_y = node.position[1] + child.position[1]
                                child.arcade_sprite.center_x = child_world_x
                                child.arcade_sprite.center_y = child_world_y

                                if velocity.x != 0 or velocity.y != 0:
                                    print(f"MOVE: Updated child sprite {child.name} from {old_child_pos} to ({child_world_x}, {child_world_y})")

        return velocity

    def get_action_strength(self, action: str) -> float:
        """Get action strength (for analog inputs)"""
        return self.runtime.get_action_strength(action)

    def is_key_pressed(self, key: str) -> bool:
        """Check if key is pressed"""
        return self.runtime.is_key_pressed(key)

    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if mouse button is pressed"""
        return self.runtime.is_mouse_button_pressed(button)

    def get_mouse_position(self) -> tuple:
        """Get mouse position relative to viewport"""
        return self.runtime.get_mouse_position()

    def get_global_mouse_position(self) -> tuple:
        """Get global mouse position"""
        return self.runtime.get_global_mouse_position()

    # Time functions
    def get_time(self) -> float:
        """Get current time"""
        return self.runtime.get_time()

    def get_runtime_time(self) -> float:
        """Get runtime time (alias for get_time)"""
        return self.runtime.get_runtime_time()

    def get_delta(self) -> float:
        """Get delta time"""
        return self.runtime.get_delta()

    def get_fps(self) -> float:
        """Get current FPS"""
        return self.runtime.get_fps()

    def wait(self, seconds: float) -> None:
        """Wait for specified time"""
        self.runtime.wait(seconds)

    def _physics_process(self, delta: float) -> None:
        """Physics process method (placeholder)"""
        pass

    # Signal functions
    def connect(self, signal_name: str, target: Any, method: str) -> None:
        """Connect signal to method"""
        self.runtime.connect(signal_name, target, method)

    def disconnect(self, signal_name: str, target: Any, method: str) -> None:
        """Disconnect signal from method"""
        self.runtime.disconnect(signal_name, target, method)

    def emit_signal(self, signal_name: str, *args) -> None:
        """Emit signal"""
        self.runtime.emit_signal(signal_name, *args)

    def is_connected(self, signal_name: str, target: Any, method: str) -> bool:
        """Check if signal is connected"""
        return self.runtime.is_connected(signal_name, target, method)

    # Resource functions
    def load_resource(self, path: str) -> Any:
        """Load resource"""
        return self.runtime.load_resource(path)

    def preload_resource(self, path: str) -> Any:
        """Preload resource"""
        return self.runtime.preload_resource(path)

    def save_resource(self, resource: Any, path: str) -> None:
        """Save resource"""
        self.runtime.save_resource(resource, path)

    # Vector functions
    def Vector3(self, x: float = 0, y: float = 0, z: float = 0) -> tuple:
        """Create 3D vector"""
        return (x, y, z)

    def distance(self, a: tuple, b: tuple) -> float:
        """Calculate distance between vectors"""
        if len(a) == 2 and len(b) == 2:
            return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
        elif len(a) == 3 and len(b) == 3:
            return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)
        else:
            raise ValueError("Vectors must be same dimension")

    def dot_product(self, a: tuple, b: tuple) -> float:
        """Calculate dot product"""
        return sum(x * y for x, y in zip(a, b))

    def cross_product(self, a: tuple, b: tuple) -> tuple:
        """Calculate cross product (3D only)"""
        if len(a) != 3 or len(b) != 3:
            raise ValueError("Cross product requires 3D vectors")
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        )

    def normalize(self, vector: tuple) -> tuple:
        """Normalize vector"""
        length = math.sqrt(sum(x**2 for x in vector))
        if length == 0:
            return vector
        return tuple(x / length for x in vector)

    def move_toward(self, current: float, target: float, delta: float) -> float:
        """Move toward target by delta amount"""
        if abs(target - current) <= delta:
            return target
        else:
            return current + (1 if target > current else -1) * delta

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                # Debug output for movement actions
                if result and action in ['move_left', 'move_right', 'move_up', 'move_down']:
                    print(f"DEBUG: is_action_pressed('{action}') = {result}")
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def move_toward(self, current: float, target: float, max_delta: float) -> float:
        """Move towards target value"""
        if abs(target - current) <= max_delta:
            return target
        return current + math.copysign(max_delta, target - current)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """Smooth interpolation between values"""
        t = clamp((t - start) / (end - start), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def lsc_print(self, *args):
        """Built-in print function with LSC runtime logging"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC] {message}")

    def lsc_print_error(self, *args):
        """Error-level print function"""
        message = ' '.join(str(arg) for arg in args)
        print(f"[LSC ERROR] {message}", file=sys.stderr)

    # Geometry functions
    def Rect2(self, x: float = 0, y: float = 0, width: float = 0, height: float = 0) -> LSCRect2:
        """Create Rect2"""
        return LSCRect2(x, y, width, height)

    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> LSCColor:
        """Create color"""
        return LSCColor(r, g, b, a)

    def Texture(self, path: str = "") -> LSCTexture:
        """Create texture"""
        return LSCTexture(path)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is currently pressed"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                result = input_manager.is_action_pressed(action)
                return result
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_pressed(action)
        return False

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released this frame"""
        if self.runtime.game_runtime and hasattr(self.runtime.game_runtime, 'input_manager'):
            input_manager = self.runtime.game_runtime.input_manager
            if input_manager:
                return input_manager.is_action_just_released(action)
        return False

    def get_action_strength(self, action: str) -> float:
        """Get action strength (for analog inputs)"""
        return self.runtime.get_action_strength(action)
