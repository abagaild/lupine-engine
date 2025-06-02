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
        self.x = float(x)
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
        return LSCVector2(0, -1)

    @property
    def DOWN(self) -> LSCVector2:
        return LSCVector2(0, 1)

    @property
    def LEFT(self) -> LSCVector2:
        return LSCVector2(-1, 0)

    @property
    def RIGHT(self) -> LSCVector2:
        return LSCVector2(1, 0)


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


            
            # Color functions
            'Color': self.Color,
            'color_lerp': self.color_lerp,
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
    def get_node(self, path: str) -> Any:
        """Get node by path"""
        return self.runtime.get_node(path)

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

    # Input functions
    def is_action_pressed(self, action: str) -> bool:
        """Check if action is pressed"""
        return self.runtime.is_action_pressed(action)

    def is_action_just_pressed(self, action: str) -> bool:
        """Check if action was just pressed"""
        return self.runtime.is_action_just_pressed(action)

    def is_action_just_released(self, action: str) -> bool:
        """Check if action was just released"""
        return self.runtime.is_action_just_released(action)

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

    # Color functions
    def Color(self, r: float = 1, g: float = 1, b: float = 1, a: float = 1) -> tuple:
        """Create color"""
        return (r, g, b, a)

    def color_lerp(self, a: tuple, b: tuple, t: float) -> tuple:
        """Interpolate between colors"""
        return tuple(self.lerp(a[i], b[i], t) for i in range(len(a)))
