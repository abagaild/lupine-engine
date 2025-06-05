"""
Prefab system for Lupine Engine
"""

from .prefab_system import EnhancedPrefab, PrefabType, VisualScriptBlock, VisualScriptBlockType
from .prefab_manager import PrefabManager
from .builtin_prefabs import create_builtin_prefabs
from .builtin_script_blocks import create_builtin_script_blocks

__all__ = [
    'EnhancedPrefab',
    'PrefabType', 
    'VisualScriptBlock',
    'VisualScriptBlockType',
    'PrefabManager',
    'create_builtin_prefabs',
    'create_builtin_script_blocks'
]
