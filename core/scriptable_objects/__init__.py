"""
Scriptable Objects System for Lupine Engine
Provides data-driven object templates and instances
"""

from .template import ScriptableObjectTemplate
from .instance import ScriptableObjectInstance
from .field import ScriptableObjectField
from .manager import ScriptableObjectManager

__all__ = [
    'ScriptableObjectTemplate',
    'ScriptableObjectInstance', 
    'ScriptableObjectField',
    'ScriptableObjectManager'
]
