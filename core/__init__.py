"""
Lupine Engine Core Module
Contains the fundamental classes and systems for the game engine
"""

__version__ = "1.0.0"
__author__ = "Lupine Engine Team"

# Core systems
from .project import LupineProject, ProjectManager
from .scene import Scene, Node, Node2D, Sprite, Camera2D, Area2D, Control, Panel, Label, CanvasLayer, SceneManager
from .audio import AudioManager, audio_manager

__all__ = [
    'LupineProject',
    'ProjectManager',
    'Scene',
    'Node',
    'Node2D',
    'Sprite',
    'Camera2D',
    'Area2D',
    'Control',
    'Panel',
    'Label',
    'CanvasLayer',
    'SceneManager',
    'AudioManager',
    'audio_manager'
]
