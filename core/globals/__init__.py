"""
Lupine Engine Global Systems
Provides singleton and global variable management for projects
"""

from .singleton_manager import SingletonManager, get_singleton_manager
from .variables_manager import VariablesManager, get_variables_manager

__all__ = [
    'SingletonManager',
    'get_singleton_manager', 
    'VariablesManager',
    'get_variables_manager'
]
