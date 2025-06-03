"""
scene/node_registry.py

Maintains a registry of all built-in and custom node definitions,
so that nodes can be instantiated by type name.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Type, Any

from .base_node import Node
from .node2d import Node2D
from .sprite import Sprite, AnimatedSprite
from .timer import Timer
from .camera import Camera2D
from .physics_nodes import (
    CollisionShape2D, CollisionPolygon2D,
    Area2D, RigidBody2D, StaticBody2D, KinematicBody2D
)
from .audio_nodes import AudioStreamPlayer, AudioStreamPlayer2D
from .ui_nodes.control import Control
from .ui_nodes.panel import Panel
from .ui_nodes.label import Label
from .ui_nodes.button import Button
from .ui_nodes.color_rect import ColorRect
from .ui_nodes.texture_rect import TextureRect
from .ui_nodes.progress_bar import ProgressBar
from .ui_nodes.containers import (
    VBoxContainer, HBoxContainer, CenterContainer, GridContainer
)
from .ui_nodes.rich_text_label import RichTextLabel
from .ui_nodes.panel_container import PanelContainer
from .ui_nodes.nine_patch_rect import NinePatchRect
from .ui_nodes.item_list import ItemList
from .ui_nodes.line_edit import LineEdit
from .ui_nodes.check_box import CheckBox
from .ui_nodes.slider import Slider
from .ui_nodes.scroll_container import ScrollContainer
from .ui_nodes.separators import HSeparator, VSeparator
from .ui_nodes.canvas_layer import CanvasLayer


class NodeRegistry:
    """
    Registry mapping node-type strings to their Python classes.
    Allows instantiating nodes by type name and loading custom script-based nodes.
    """

    def __init__(self):
        self._registry: Dict[str, Type[Node]] = {}
        self._register_builtin_nodes()

    def _register_builtin_nodes(self) -> None:
        """Register all built-in node types with their class."""
        base_nodes = {
            "Node": Node,
            "Node2D": Node2D,
            "Timer": Timer
        }
        sprite_nodes = {
            "Sprite": Sprite,
            "AnimatedSprite": AnimatedSprite
        }
        camera_nodes = {
            "Camera2D": Camera2D
        }
        physics_nodes = {
            "CollisionShape2D": CollisionShape2D,
            "CollisionPolygon2D": CollisionPolygon2D,
            "Area2D": Area2D,
            "RigidBody2D": RigidBody2D,
            "StaticBody2D": StaticBody2D,
            "KinematicBody2D": KinematicBody2D
        }
        audio_nodes = {
            "AudioStreamPlayer": AudioStreamPlayer,
            "AudioStreamPlayer2D": AudioStreamPlayer2D
        }
        ui_nodes = {
            "Control": Control,
            "Panel": Panel,
            "Label": Label,
            "Button": Button,
            "ColorRect": ColorRect,
            "TextureRect": TextureRect,
            "ProgressBar": ProgressBar,
            "VBoxContainer": VBoxContainer,
            "HBoxContainer": HBoxContainer,
            "CenterContainer": CenterContainer,
            "GridContainer": GridContainer,
            "RichTextLabel": RichTextLabel,
            "PanelContainer": PanelContainer,
            "NinePatchRect": NinePatchRect,
            "ItemList": ItemList,
            "LineEdit": LineEdit,
            "CheckBox": CheckBox,
            "Slider": Slider,
            "ScrollContainer": ScrollContainer,
            "HSeparator": HSeparator,
            "VSeparator": VSeparator,
            "CanvasLayer": CanvasLayer
        }

        for mapping in (base_nodes, sprite_nodes, camera_nodes,
                        physics_nodes, audio_nodes, ui_nodes):
            for type_name, cls in mapping.items():
                self.register_node(type_name, cls)

    def register_node(self, type_name: str, cls: Type[Node]) -> None:
        """
        Add or override a node-type mapping.  
        type_name: string used in serialized 'type' fields.  
        cls: the Python class implementing that node.
        """
        self._registry[type_name] = cls

    def unregister_node(self, type_name: str) -> None:
        """Remove a node type from the registry if present."""
        self._registry.pop(type_name, None)

    def create_node(self, type_name: str, name: Optional[str] = None) -> Optional[Node]:
        """
        Instantiate a node by type name.  
        If name is provided, set node.name accordingly; else default name from the class.
        """
        cls = self._registry.get(type_name)
        if not cls:
            return None
        node = cls(name or type_name)
        return node

    def get_registered_types(self) -> List[str]:
        """Return a list of all registered node-type strings."""
        return list(self._registry.keys())

    def load_custom_nodes(self, directory: Path) -> None:
        """
        Search for .py script files in `directory` (and subdirectories),
        parse their `class <ClassName>` declaration, and register them
        at runtime so that user-defined node types become available.
        """
        for root, _, files in os.walk(directory):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                script_path = Path(root) / fname
                with open(script_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                class_name = None
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("class "):
                        # e.g. "class Enemy(Node2D):"
                        parts = stripped.split()
                        if len(parts) >= 2:
                            class_name = parts[1]
                            if "(" in class_name:
                                class_name = class_name.split("(")[0]
                            if class_name.endswith(":"):
                                class_name = class_name[:-1]
                        break
                if class_name:
                    # For now, register a placeholder Node that records script path.
                    class PlaceholderNode(Node):
                        def __init__(self, name: str = class_name):
                            super().__init__(name, class_name)
                            self.script_path = str(script_path.relative_to(directory.parent))
                    self.register_node(class_name, PlaceholderNode)
