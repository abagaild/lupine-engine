"""
scene/__init__.py

Package for scene graph and node definitions in Lupine Engine.
"""

from .base_node import Node

from .scene import Scene
from .scene_manager import SceneManager
from .node_registry import NodeRegistry

from .node2d import Node2D
from .sprite import Sprite
from .camera import Camera2D
