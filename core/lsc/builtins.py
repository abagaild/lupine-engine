"""
builtins.py

LSC Built-in Functions and Game Engine Integration
Provides all the built-in classes, functions, and constants available
to Lupine Script (LSC) at runtime.
"""

import math
import random
import sys
import builtins
from typing import Any, Dict, List, Optional, Tuple, Callable, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .runtime import LSCRuntime


# ------------------------------------------------------------------------------
# Fundamental Data Types
# ------------------------------------------------------------------------------

class Vector2:
    """
    Simple 2D vector class for LSC.
    Supports basic arithmetic, magnitude, normalization, and utility methods.
    """
    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)

    def __add__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: Union["Vector2", float]) -> "Vector2":
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other: Union["Vector2", float]) -> "Vector2":
        if isinstance(other, Vector2):
            return Vector2(self.x / other.x, self.y / other.y)
        return Vector2(self.x / other, self.y / other)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2):
            return False
        return math.isclose(self.x, other.x, rel_tol=1e-6) and math.isclose(self.y, other.y, rel_tol=1e-6)

    def __neg__(self) -> "Vector2":
        return Vector2(-self.x, -self.y)

    def __repr__(self) -> str:
        return f"Vector2({self.x}, {self.y})"

    def __iter__(self):
        yield self.x
        yield self.y

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        raise IndexError("Vector2 index out of range")

    @property
    def length(self) -> float:
        """Return the Euclidean length (magnitude)."""
        return math.hypot(self.x, self.y)

    @property
    def length_squared(self) -> float:
        """Return the squared length (avoids sqrt)."""
        return self.x * self.x + self.y * self.y

    def normalized(self) -> "Vector2":
        """Return a new Vector2 normalized to length 1 (or zero-vector if length == 0)."""
        mag = self.length
        if mag == 0:
            return Vector2(0.0, 0.0)
        return Vector2(self.x / mag, self.y / mag)

    def normalize(self) -> None:
        """Normalize this vector in place."""
        mag = self.length
        if mag != 0:
            self.x /= mag
            self.y /= mag

    def distance_to(self, other: "Vector2") -> float:
        """Compute Euclidean distance to another Vector2."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.hypot(dx, dy)

    def dot(self, other: "Vector2") -> float:
        """Dot product with another Vector2."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vector2") -> float:
        """
        2D “cross product” returning a scalar (z-component of 3D cross).
        Equivalent to (self.x * other.y - self.y * other.x).
        """
        return self.x * other.y - self.y * other.x

    def angle(self) -> float:
        """Return angle (in radians) relative to the X-axis."""
        return math.atan2(self.y, self.x)

    def lerp(self, other: "Vector2", t: float) -> "Vector2":
        """Linearly interpolate toward another vector by factor t ∈ [0, 1]."""
        return Vector2(self.x + (other.x - self.x) * t,
                       self.y + (other.y - self.y) * t)

    def rotated(self, angle: float) -> "Vector2":
        """Return a new Vector2 rotated by `angle` radians about the origin."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )


class Rect2:
    """
    Simple 2D rectangle class for LSC.
    Stores position (top-left) and size.
    """
    __slots__ = ("position", "size")

    def __init__(self,
                 x: float = 0.0,
                 y: float = 0.0,
                 width: float = 0.0,
                 height: float = 0.0) -> None:
        self.position = Vector2(x, y)
        self.size = Vector2(width, height)

    @property
    def x(self) -> float:
        return self.position.x

    @x.setter
    def x(self, value: float) -> None:
        self.position.x = value

    @property
    def y(self) -> float:
        return self.position.y

    @y.setter
    def y(self, value: float) -> None:
        self.position.y = value

    @property
    def width(self) -> float:
        return self.size.x

    @width.setter
    def width(self, value: float) -> None:
        self.size.x = value

    @property
    def height(self) -> float:
        return self.size.y

    @height.setter
    def height(self, value: float) -> None:
        self.size.y = value

    def area(self) -> float:
        """Return the area (width * height)."""
        return self.size.x * self.size.y

    def contains_point(self, point: Union[Vector2, Tuple[float, float]]) -> bool:
        """
        Return True if `point` (Vector2 or (x, y) tuple) lies within this Rect2.
        """
        px, py = (point.x, point.y) if isinstance(point, Vector2) else (point[0], point[1])
        return (
            self.x <= px <= self.x + self.width
            and self.y <= py <= self.y + self.height
        )

    def intersects(self, other: "Rect2") -> bool:
        """Return True if this rectangle intersects with `other`."""
        return not (
            other.x + other.width < self.x
            or other.x > self.x + self.width
            or other.y + other.height < self.y
            or other.y > self.y + self.height
        )

    def __repr__(self) -> str:
        return f"Rect2({self.x}, {self.y}, {self.width}, {self.height})"


class Color:
    """
    Simple RGBA color class for LSC.
    Each component (r, g, b, a) is a float in [0.0, 1.0].
    """
    __slots__ = ("r", "g", "b", "a")

    def __init__(self,
                 r: float = 1.0,
                 g: float = 1.0,
                 b: float = 1.0,
                 a: float = 1.0) -> None:
        self.r = float(r)
        self.g = float(g)
        self.b = float(b)
        self.a = float(a)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return False
        return (
            math.isclose(self.r, other.r, rel_tol=1e-6) and
            math.isclose(self.g, other.g, rel_tol=1e-6) and
            math.isclose(self.b, other.b, rel_tol=1e-6) and
            math.isclose(self.a, other.a, rel_tol=1e-6)
        )

    def __repr__(self) -> str:
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"

    def __iter__(self):
        yield self.r
        yield self.g
        yield self.b
        yield self.a

    def lerp(self, other: "Color", t: float) -> "Color":
        """
        Linearly interpolate this color toward `other` by factor t ∈ [0, 1].
        """
        return Color(
            self.r + (other.r - self.r) * t,
            self.g + (other.g - self.g) * t,
            self.b + (other.b - self.b) * t,
            self.a + (other.a - self.a) * t
        )

    @classmethod
    def RED(cls) -> "Color":
        return Color(1.0, 0.0, 0.0, 1.0)

    @classmethod
    def GREEN(cls) -> "Color":
        return Color(0.0, 1.0, 0.0, 1.0)

    @classmethod
    def BLUE(cls) -> "Color":
        return Color(0.0, 0.0, 1.0, 1.0)

    @classmethod
    def WHITE(cls) -> "Color":
        return Color(1.0, 1.0, 1.0, 1.0)

    @classmethod
    def BLACK(cls) -> "Color":
        return Color(0.0, 0.0, 0.0, 1.0)

    @classmethod
    def YELLOW(cls) -> "Color":
        return Color(1.0, 1.0, 0.0, 1.0)

    @classmethod
    def CYAN(cls) -> "Color":
        return Color(0.0, 1.0, 1.0, 1.0)

    @classmethod
    def MAGENTA(cls) -> "Color":
        return Color(1.0, 0.0, 1.0, 1.0)

    @classmethod
    def TRANSPARENT(cls) -> "Color":
        return Color(1.0, 1.0, 1.0, 0.0)


class Texture:
    """
    Simple texture placeholder class for LSC.
    Stores a file path; actual loading/updating is done by the game engine.
    """
    __slots__ = ("path",)

    def __init__(self, path: str = "") -> None:
        self.path = str(path)

    def get_size(self) -> Vector2:
        """
        Return a default size as a Vector2.
        In a real engine, this would query the actual image dimensions.
        """
        return Vector2(64.0, 64.0)

    def __repr__(self) -> str:
        return f"Texture('{self.path}')"


# ------------------------------------------------------------------------------
# Built-in Functions & Constants Container
# ------------------------------------------------------------------------------

class LSCBuiltins:
    """
    Container for all global built-in functions, constants, and types
    exposed to LSC scripts. Relies on a reference to LSCRuntime to
    delegate engine-specific operations (scene, input, time, etc.).
    """

    def __init__(self, runtime: "LSCRuntime") -> None:
        self.runtime = runtime
        # Math Constants
        self.PI = math.pi
        self.TAU = 2 * math.pi
        self.E = math.e
        self.INF = float("inf")
        self.NAN = float("nan")

        # Initialize function and constant dictionaries for runtime access
        self.functions = self._get_builtin_functions()
        self.constants = self._get_builtin_constants()

    def _get_builtin_functions(self) -> Dict[str, Callable]:
        """Get dictionary of all built-in functions"""
        return {
            # Type constructors
            'Vector2': self.Vector2,
            'Rect2': self.Rect2,
            'Color': self.Color,
            'Texture': self.Texture,

            # Math functions
            'abs': self.abs,
            'min': self.min,
            'max': self.max,
            'round': self.round,
            'floor': self.floor,
            'ceil': self.ceil,
            'sqrt': self.sqrt,
            'pow': self.pow,
            'sin': self.sin,
            'cos': self.cos,
            'tan': self.tan,
            'asin': self.asin,
            'acos': self.acos,
            'atan': self.atan,
            'atan2': self.atan2,
            'deg2rad': self.deg2rad,
            'rad2deg': self.rad2deg,
            'lerp': self.lerp,
            'clamp': self.clamp,
            'sign': self.sign,
            'move_toward': self.move_toward,
            'smoothstep': self.smoothstep,

            # Random functions
            'rand_seed': self.rand_seed,
            'randf': self.randf,
            'randi': self.randi,
            'rand_range': self.rand_range,
            'rand_int': self.rand_int,

            # String functions
            'str': self.str,
            'len': self.len,
            'substr': self.substr,
            'find': self.find,
            'replace': self.replace,
            'split': self.split,
            'join': self.join,
            'to_upper': self.to_upper,
            'to_lower': self.to_lower,
            'strip': self.strip,

            # Array functions
            'append': self.append,
            'insert': self.insert,
            'remove': self.remove,
            'pop': self.pop,
            'size': self.size,
            'empty': self.empty,
            'has': self.has,
            'find_index': self.find_index,
            'sort': self.sort,
            'reverse': self.reverse,

            # Dictionary functions
            'has_key': self.has_key,
            'keys': self.keys,
            'values': self.values,
            'items': self.items,

            # Type and debug functions
            'typeof': self.typeof,
            'is_instance': self.is_instance,
            'assert': self.assert_,
            'print': self.print,
            'print_debug': self.print_debug,
            'print_error': self.print_error,

            # Node and scene functions
            'get_node': self.get_node,
            'get_node_or_null': self.get_node_or_null,
            'find_node': self.find_node,
            'get_parent': self.get_parent,
            'get_children': self.get_children,
            'add_child': self.add_child,
            'remove_child': self.remove_child,
            'queue_free': self.queue_free,
            'duplicate': self.duplicate,
            'is_inside_tree': self.is_inside_tree,
            'get_tree': self.get_tree,
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
            'load': self.load,
            'preload': self.preload,
            'save': self.save,

            # Geometry functions
            'Vector3': self.Vector3,
            'distance': self.distance,
            'dot_product': self.dot_product,
            'cross_product': self.cross_product,
            'normalize': self.normalize,

            # Camera and viewport functions
            'get_viewport_rect': self.get_viewport_rect,
            'get_process_delta_time': self.get_process_delta_time,
            'get_path_to': self.get_path_to,

            # Node property and method checking
            'has_method': self.has_method,
            'has_property': self.has_property,
            'get_global_position': self.get_global_position,
            'get_script': self.get_script,
            'get_path': self.get_path,
        }

    def _get_builtin_constants(self) -> Dict[str, Any]:
        """Get dictionary of all built-in constants"""
        return {
            # Math constants
            'PI': self.PI,
            'TAU': self.TAU,
            'E': self.E,
            'INF': self.INF,
            'NAN': self.NAN,

            # Color constants
            'RED': Color.RED(),
            'GREEN': Color.GREEN(),
            'BLUE': Color.BLUE(),
            'WHITE': Color.WHITE(),
            'BLACK': Color.BLACK(),
            'YELLOW': Color.YELLOW(),
            'CYAN': Color.CYAN(),
            'MAGENTA': Color.MAGENTA(),
            'TRANSPARENT': Color.TRANSPARENT(),
        }

    # --------------------------------------------------------------------------
    # Primitive Type Constructors
    # --------------------------------------------------------------------------
    def Vector2(self, x: float = 0.0, y: float = 0.0) -> Vector2:
        """Construct a new Vector2(x, y)."""
        return Vector2(x, y)

    def Rect2(self, x: float = 0.0, y: float = 0.0,
              width: float = 0.0, height: float = 0.0) -> Rect2:
        """Construct a new Rect2(x, y, width, height)."""
        return Rect2(x, y, width, height)

    def Color(self, r: float = 1.0, g: float = 1.0,
              b: float = 1.0, a: float = 1.0) -> Color:
        """Construct a new Color(r, g, b, a)."""
        return Color(r, g, b, a)

    def Texture(self, path: str = "") -> Texture:
        """Construct a new Texture(path)."""
        return Texture(path)

    # --------------------------------------------------------------------------
    # Math Functions
    # --------------------------------------------------------------------------
    def abs(self, x: Union[int, float]) -> Union[int, float]:
        return abs(x)

    def min(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        return a if a < b else b

    def max(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        return a if a > b else b

    def round(self, x: float) -> int:
        return builtins.round(x)

    def floor(self, x: float) -> int:
        return math.floor(x)

    def ceil(self, x: float) -> int:
        return math.ceil(x)

    def sqrt(self, x: float) -> float:
        return math.sqrt(x)

    def pow(self, a: float, b: float) -> float:
        return math.pow(a, b)

    def sin(self, x: float) -> float:
        return math.sin(x)

    def cos(self, x: float) -> float:
        return math.cos(x)

    def tan(self, x: float) -> float:
        return math.tan(x)

    def asin(self, x: float) -> float:
        return math.asin(x)

    def acos(self, x: float) -> float:
        return math.acos(x)

    def atan(self, x: float) -> float:
        return math.atan(x)

    def atan2(self, y: float, x: float) -> float:
        return math.atan2(y, x)

    def deg2rad(self, x: float) -> float:
        return math.radians(x)

    def rad2deg(self, x: float) -> float:
        return math.degrees(x)

    def lerp(self, a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    def clamp(self, value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))

    def sign(self, x: float) -> int:
        if x > 0:
            return 1
        if x < 0:
            return -1
        return 0

    def move_toward(self, current: float, target: float, delta: float) -> float:
        """
        Move `current` toward `target` by at most `delta`.
        """
        difference = target - current
        if abs(difference) <= delta:
            return target
        return current + delta * (1 if difference > 0 else -1)

    def smoothstep(self, start: float, end: float, t: float) -> float:
        """
        Smooth cubic interpolation between `start` and `end` by `t` in [0, 1].
        """
        t = self.clamp((t - start) / (end - start) if end != start else 0.0, 0.0, 1.0)
        return t * t * (3 - 2 * t)

    # --------------------------------------------------------------------------
    # Random Number Functions
    # --------------------------------------------------------------------------
    def rand_seed(self, seed: int) -> None:
        random.seed(seed)

    def randf(self) -> float:
        return random.random()

    def randi(self) -> int:
        return random.getrandbits(31)

    def rand_range(self, minimum: float, maximum: float) -> float:
        return random.uniform(minimum, maximum)

    def rand_int(self, minimum: int, maximum: int) -> int:
        return random.randint(minimum, maximum)

    # --------------------------------------------------------------------------
    # String Functions
    # --------------------------------------------------------------------------
    def str(self, x: Any) -> str:
        return builtins.str(x)

    def len(self, x: Union[str, List[Any], Dict[Any, Any]]) -> int:
        return builtins.len(x)

    def substr(self, s: str, start: int, length: Optional[int] = None) -> str:
        if length is None:
            return s[start:]
        return s[start : start + length]

    def find(self, s: str, substr: str) -> int:
        return s.find(substr)

    def replace(self, s: str, old: str, new: str) -> str:
        return s.replace(old, new)

    def split(self, s: str, delimiter: Optional[str] = None) -> List[str]:
        return s.split(delimiter) if delimiter is not None else s.split()

    def join(self, array: List[str], delimiter: Optional[str] = None) -> str:
        sep = delimiter if delimiter is not None else ""
        return sep.join(array)

    def to_upper(self, s: str) -> str:
        return s.upper()

    def to_lower(self, s: str) -> str:
        return s.lower()

    def strip(self, s: str) -> str:
        return s.strip()

    # --------------------------------------------------------------------------
    # Array Functions
    # --------------------------------------------------------------------------
    def append(self, array: List[Any], item: Any) -> None:
        array.append(item)

    def insert(self, array: List[Any], index: int, item: Any) -> None:
        array.insert(index, item)

    def remove(self, array: List[Any], item: Any) -> None:
        array.remove(item)

    def pop(self, array: List[Any], index: Optional[int] = None) -> Any:
        if index is None:
            return array.pop()
        return array.pop(index)

    def size(self, array: List[Any]) -> int:
        return len(array)

    def empty(self, array: List[Any]) -> bool:
        return len(array) == 0

    def has(self, array: List[Any], item: Any) -> bool:
        return item in array

    def find_index(self, array: List[Any], item: Any) -> int:
        try:
            return array.index(item)
        except ValueError:
            return -1

    def sort(self, array: List[Any]) -> None:
        array.sort()

    def reverse(self, array: List[Any]) -> None:
        array.reverse()

    # --------------------------------------------------------------------------
    # Dictionary Functions
    # --------------------------------------------------------------------------
    def has_key(self, dictionary: Dict[Any, Any], key: Any) -> bool:
        return key in dictionary

    def keys(self, dictionary: Dict[Any, Any]) -> List[Any]:
        return list(dictionary.keys())

    def values(self, dictionary: Dict[Any, Any]) -> List[Any]:
        return list(dictionary.values())

    def items(self, dictionary: Dict[Any, Any]) -> List[Tuple[Any, Any]]:
        return list(dictionary.items())

    # --------------------------------------------------------------------------
    # Type & Debug Functions
    # --------------------------------------------------------------------------
    def typeof(self, x: Any) -> type:
        return type(x)

    def is_instance(self, x: Any, cls: type) -> bool:
        return isinstance(x, cls)

    def assert_(self, condition: bool, message: str = "") -> None:
        if not condition:
            raise AssertionError(message)

    def print(self, *args: Any) -> None:
        """Standard output print (newline-terminated)."""
        builtins.print(*args)

    def print_debug(self, *args: Any) -> None:
        """Debug print with [DEBUG] prefix."""
        builtins.print("[DEBUG]", *args, file=sys.stdout)

    def print_error(self, *args: Any) -> None:
        """Error print with [ERROR] prefix to stderr."""
        builtins.print("[ERROR]", *args, file=sys.stderr)

    # --------------------------------------------------------------------------
    # Node & Scene Functions (Delegated to Runtime / Engine)
    # --------------------------------------------------------------------------
    def get_node(self, path: str) -> Any:
        """Return the node at `path` or raise if not found."""
        return self.runtime.get_node(path)

    def get_node_or_null(self, path: str) -> Any:
        """Return the node at `path` or None if not found."""
        return self.runtime.get_node_or_null(path)

    def find_node(self, name: str) -> Any:
        """Recursively search descendants for a node named `name`."""
        return self.runtime.find_node(name)

    def get_parent(self, node: Any) -> Any:
        """Return the parent of `node`, or None if no parent."""
        return self.runtime.get_parent(node)

    def get_children(self, node: Any) -> List[Any]:
        """Return a list of direct children of `node`."""
        return self.runtime.get_children(node)

    def add_child(self, parent: Any, child: Any) -> None:
        """Add `child` as a child of `parent`."""
        self.runtime.add_child(parent, child)

    def remove_child(self, parent: Any, child: Any) -> None:
        """Remove `child` from `parent`."""
        self.runtime.remove_child(parent, child)

    def queue_free(self, node: Any) -> None:
        """Queue `node` for deletion at end of frame."""
        self.runtime.queue_free(node)

    def duplicate(self, node: Any) -> Any:
        """Return a deep clone of `node`."""
        return self.runtime.duplicate(node)

    def is_inside_tree(self, node: Any) -> bool:
        """Return True if `node` is in the scene tree."""
        return self.runtime.is_inside_tree(node)

    def get_tree(self) -> Any:
        """Return the top-level scene tree."""
        return self.runtime.get_tree()

    def change_scene(self, path: str) -> None:
        """Immediately change current scene to `path`."""
        self.runtime.change_scene(path)

    def reload_scene(self) -> None:
        """Reload the current scene."""
        self.runtime.reload_scene()

    def get_scene(self) -> Any:
        """Return the root node of the current scene."""
        return self.runtime.get_scene()

    # --------------------------------------------------------------------------
    # Input Functions (Delegated to Runtime / Engine)
    # --------------------------------------------------------------------------
    def is_action_pressed(self, action: str) -> bool:
        """Return True if the named action is currently pressed."""
        return self.runtime.is_action_pressed(action)

    def is_action_just_pressed(self, action: str) -> bool:
        """Return True if the named action was pressed this frame."""
        return self.runtime.is_action_just_pressed(action)

    def is_action_just_released(self, action: str) -> bool:
        """Return True if the named action was released this frame."""
        return self.runtime.is_action_just_released(action)

    def get_action_strength(self, action: str) -> float:
        """Return analog strength of the named action (0.0–1.0)."""
        return self.runtime.get_action_strength(action)

    def is_key_pressed(self, key: str) -> bool:
        """Return True if the physical key `key` is currently down."""
        return self.runtime.is_key_pressed(key)

    def is_mouse_button_pressed(self, button: int) -> bool:
        """Return True if mouse button (0=left,1=right...) is down."""
        return self.runtime.is_mouse_button_pressed(button)

    def get_mouse_position(self) -> Tuple[float, float]:
        """Return mouse position relative to viewport."""
        return self.runtime.get_mouse_position()

    def get_global_mouse_position(self) -> Tuple[float, float]:
        """Return mouse position in global coordinates."""
        return self.runtime.get_global_mouse_position()

    # --------------------------------------------------------------------------
    # Camera and Viewport Functions
    # --------------------------------------------------------------------------
    def get_viewport_rect(self) -> Rect2:
        """Get viewport rectangle."""
        # Default viewport size - should be overridden by game engine
        return Rect2(0, 0, 1024, 600)

    def get_process_delta_time(self) -> float:
        """Get delta time for current process frame."""
        return self.runtime.get_delta()

    def get_path_to(self, node: Any) -> str:
        """Get path from current node to target node."""
        if hasattr(node, 'name'):
            return node.name
        return str(id(node))

    # --------------------------------------------------------------------------
    # Node Property and Method Checking
    # --------------------------------------------------------------------------
    def has_method(self, obj: Any, method_name: str) -> bool:
        """Check if object has a method."""
        return hasattr(obj, method_name) and callable(getattr(obj, method_name, None))

    def has_property(self, obj: Any, property_name: str) -> bool:
        """Check if object has a property."""
        return hasattr(obj, property_name)

    def get_global_position(self, node: Any = None) -> Vector2:
        """Get global position of node."""
        if node is None:
            # Return current node's global position
            return Vector2(0, 0)  # Default

        if hasattr(node, 'global_position'):
            pos = node.global_position
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                return Vector2(pos[0], pos[1])
            elif hasattr(pos, 'x') and hasattr(pos, 'y'):
                return Vector2(pos.x, pos.y)

        if hasattr(node, 'position'):
            pos = node.position
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                return Vector2(pos[0], pos[1])
            elif hasattr(pos, 'x') and hasattr(pos, 'y'):
                return Vector2(pos.x, pos.y)

        return Vector2(0, 0)

    def get_script(self, node: Any = None) -> Any:
        """Get script attached to node."""
        if node is None:
            return None
        return getattr(node, 'script', None)

    def get_path(self, script: Any) -> str:
        """Get path of script."""
        if hasattr(script, 'path'):
            return script.path
        return ""

    # --------------------------------------------------------------------------
    # Time & Frame Functions (Delegated to Runtime / Engine)
    # --------------------------------------------------------------------------
    def get_time(self) -> float:
        """Return seconds since game start."""
        return self.runtime.get_time()

    def get_runtime_time(self) -> float:
        """Alias for get_time()."""
        return self.runtime.get_runtime_time()

    def get_delta(self) -> float:
        """Return delta time (seconds) of last frame."""
        return self.runtime.get_delta()

    def get_fps(self) -> float:
        """Return current frames-per-second (1 / delta)."""
        return self.runtime.get_fps()

    def wait(self, seconds: float) -> None:
        """
        Block execution for `seconds`.
        (In an actual engine, this would yield in a coroutine;
        here it's a stub for compatibility.)
        """
        self.runtime.wait(seconds)

    # --------------------------------------------------------------------------
    # Physics Callbacks (Stubs)
    # --------------------------------------------------------------------------
    def _physics_process(self, delta: float) -> None:
        """
        Physics process callback invoked at fixed intervals.
        Override in scripts to implement physics logic.
        """
        pass

    # --------------------------------------------------------------------------
    # Signal Management (Delegated to Runtime / Engine)
    # --------------------------------------------------------------------------
    def connect(self, signal_name: str, target: Any, method: str) -> None:
        """Connect `signal_name` to `target.method`."""
        self.runtime.connect(signal_name, target, method)

    def disconnect(self, signal_name: str, target: Any, method: str) -> None:
        """Disconnect `signal_name` from `target.method`."""
        self.runtime.disconnect(signal_name, target, method)

    def emit_signal(self, signal_name: str, *args: Any) -> None:
        """Emit `signal_name` with optional arguments."""
        self.runtime.emit_signal(signal_name, *args)

    def is_connected(self, signal_name: str, target: Any, method: str) -> bool:
        """Return True if `signal_name` is connected to `target.method`."""
        return self.runtime.is_connected(signal_name, target, method)

    # --------------------------------------------------------------------------
    # Resource Management (Delegated to Runtime / Engine)
    # --------------------------------------------------------------------------
    def load(self, path: str) -> Any:
        """Load (or retrieve) a resource at `path`."""
        return self.runtime.load(path)

    def preload(self, path: str) -> Any:
        """Preload a resource at `path` for faster subsequent load."""
        return self.runtime.preload(path)

    def save(self, resource: Any, path: str) -> None:
        """Save `resource` to `path` (stub; actual engine handles serialization)."""
        self.runtime.save(resource, path)

    # --------------------------------------------------------------------------
    # Geometry & Vector3 Helpers
    # --------------------------------------------------------------------------
    def Vector3(self,
                x: float = 0.0,
                y: float = 0.0,
                z: float = 0.0) -> Tuple[float, float, float]:
        """Construct a 3-element tuple representing a 3D vector."""
        return (float(x), float(y), float(z))

    def distance(self, a: Union[Tuple[float, ...], List[float]],
                 b: Union[Tuple[float, ...], List[float]]) -> float:
        """Compute Euclidean distance between two 2D/3D tuples."""
        if len(a) != len(b):
            raise ValueError("Vectors must have same dimensionality.")
        return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))

    def dot_product(self, a: Union[Tuple[float, ...], List[float]],
                    b: Union[Tuple[float, ...], List[float]]) -> float:
        """Compute dot product of two vectors."""
        if len(a) != len(b):
            raise ValueError("Vectors must have same dimensionality.")
        return sum(a[i] * b[i] for i in range(len(a)))

    def cross_product(self,
                      a: Union[Tuple[float, ...], List[float]],
                      b: Union[Tuple[float, ...], List[float]]) -> Tuple[float, ...]:
        """
        Compute 3D cross product (a × b). Both `a` and `b` must be length 3.
        """
        if len(a) != 3 or len(b) != 3:
            raise ValueError("Cross product is defined only for 3D vectors.")
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )

    def normalize(self, vector: Union[Tuple[float, ...], List[float]]) -> Tuple[float, ...]:
        """Return a normalized version of a 2D or 3D vector (tuple or list)."""
        dim = len(vector)
        if dim < 2 or dim > 3:
            raise ValueError("normalize() supports only 2D or 3D vectors.")
        mag = math.sqrt(sum(vector[i] * vector[i] for i in range(dim)))
        if mag == 0:
            return tuple(0.0 for _ in range(dim))
        return tuple(vector[i] / mag for i in range(dim))

    # --------------------------------------------------------------------------
    # Assertion & Utility Alias (avoid conflict with Python built-in assert)
    # --------------------------------------------------------------------------
    assert_builtin = assert_


# Expose built-in names at module level for direct import if needed
__all__ = [
    "Vector2",
    "Rect2",
    "Color",
    "Texture",
    "LSCBuiltins",
]
