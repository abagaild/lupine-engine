"""
Lupine Engine Dialogue System
Comprehensive dialogue system with Ren'py-style scripting
"""

from .dialogue_parser import DialogueParser, DialogueScript, DialogueNode, NodeType, DialogueChoice
from .dialogue_runtime import DialogueRuntime, DialogueState, DialogueContext
from .dialogue_commands import DialogueCommandExecutor
from .asset_resolver import DialogueAssetResolver

__all__ = [
    'DialogueParser',
    'DialogueScript', 
    'DialogueNode',
    'NodeType',
    'DialogueChoice',
    'DialogueRuntime',
    'DialogueState',
    'DialogueContext',
    'DialogueCommandExecutor',
    'DialogueAssetResolver'
]
