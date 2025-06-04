"""
Lupine Engine Core Module
Contains the fundamental classes and systems for the game engine
"""

__version__ = "1.0.0"
__author__ = "Lupine Engine Team"

# Core systems
from .project import LupineProject, ProjectManager
from .scene import (Scene, Node,     SceneManager)
from .audio import AudioManager, audio_manager
from .python_runtime import PythonScriptRuntime, PythonScriptInstance

__all__ = [
    'LupineProject',
    'ProjectManager',
    'Scene',
    'Node',
    'AudioManager',
    'audio_manager',
    'PythonScriptRuntime',
    'PythonScriptInstance'
]
