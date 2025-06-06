"""
YSort node implementation for Lupine Engine
Automatically sorts child nodes by their Y position for proper depth rendering
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional
import math


class YSort(Node2D):
    """
    YSort node that automatically sorts its children by Y position.
    
    Features:
    - Automatic Y-position based sorting of children
    - Configurable sort offset for fine-tuning
    - Real-time sorting when children move
    - Efficient dirty tracking to minimize sorting operations
    - Support for nested YSort nodes
    - Compatible with physics bodies and dynamic objects
    """
    
    def __init__(self, name: str = "YSort"):
        super().__init__(name)
        self.type = "YSort"
        
        # YSort specific properties
        self.sort_enabled: bool = True
        self.sort_offset: float = 0.0  # Additional offset for sorting calculation
        self._needs_sort: bool = True
        self._last_child_count: int = 0
        self._child_positions: Dict[str, List[float]] = {}  # Track child positions for change detection
        
        # Export variables for editor
        self.export_variables.update({
            "sort_enabled": {
                "type": "bool",
                "value": True,
                "description": "Enable/disable Y-sorting of children"
            },
            "sort_offset": {
                "type": "float",
                "value": 0.0,
                "min": -1000.0,
                "max": 1000.0,
                "step": 1.0,
                "description": "Additional offset added to Y position for sorting"
            }
        })
        
        # Built-in signals
        self.add_signal("sort_changed")
    
    def _ready(self):
        """Called when node enters the scene tree"""
        super()._ready()
        
        # Connect to child signals for automatic sorting
        self.connect("child_entered_tree", self, "_on_child_added")
        self.connect("child_exiting_tree", self, "_on_child_removed")
        
        # Connect to existing children
        for child in self.children:
            self._connect_to_child(child)
        
        # Initial sort
        self._mark_sort_needed()
    
    def _on_child_added(self, child):
        """Handle child being added"""
        self._connect_to_child(child)
        self._mark_sort_needed()
    
    def _on_child_removed(self, child):
        """Handle child being removed"""
        self._disconnect_from_child(child)
        self._mark_sort_needed()
    
    def _connect_to_child(self, child):
        """Connect to child's transform signals"""
        if hasattr(child, 'connect') and hasattr(child, 'transform_changed'):
            try:
                child.connect("transform_changed", self, "_on_child_transform_changed")
            except:
                pass  # Connection might already exist or not be supported
    
    def _disconnect_from_child(self, child):
        """Disconnect from child's transform signals"""
        if hasattr(child, 'disconnect'):
            try:
                child.disconnect("transform_changed", self, "_on_child_transform_changed")
            except:
                pass  # Connection might not exist
    
    def _on_child_transform_changed(self):
        """Handle child transform change"""
        if self.sort_enabled:
            self._mark_sort_needed()
    
    def _mark_sort_needed(self):
        """Mark that sorting is needed"""
        self._needs_sort = True
    
    def _process(self, delta: float):
        """Process sorting updates"""
        super()._process(delta)
        
        if self.sort_enabled and self._needs_sort:
            self._update_sort()
    
    def _update_sort(self):
        """Update the sorting of children"""
        if not self.sort_enabled or len(self.children) <= 1:
            self._needs_sort = False
            return
        
        # Check if we actually need to sort by comparing positions
        if not self._has_children_moved():
            self._needs_sort = False
            return
        
        # Sort children by Y position
        sorted_children = self._get_sorted_children()
        
        # Update z_index for each child based on sort order
        for i, child in enumerate(sorted_children):
            if hasattr(child, 'z_index'):
                # Use negative values so lower Y positions render behind higher Y positions
                child.z_index = -i
                child.z_as_relative = True
        
        # Update child positions cache
        self._update_child_positions_cache()
        
        self._needs_sort = False
        self.emit_signal("sort_changed")
    
    def _has_children_moved(self) -> bool:
        """Check if any children have moved since last sort"""
        # Check if child count changed
        if len(self.children) != self._last_child_count:
            self._last_child_count = len(self.children)
            return True
        
        # Check if any child positions changed
        for child in self.children:
            if hasattr(child, 'position'):
                child_id = str(id(child))
                current_pos = list(child.position)
                
                if child_id not in self._child_positions:
                    return True
                
                last_pos = self._child_positions[child_id]
                if abs(current_pos[1] - last_pos[1]) > 0.001:  # Only care about Y position changes
                    return True
        
        return False
    
    def _update_child_positions_cache(self):
        """Update the cache of child positions"""
        self._child_positions.clear()
        for child in self.children:
            if hasattr(child, 'position'):
                child_id = str(id(child))
                self._child_positions[child_id] = list(child.position)
    
    def _get_sorted_children(self) -> List:
        """Get children sorted by Y position"""
        def sort_key(child):
            if hasattr(child, 'position') and len(child.position) >= 2:
                # Use global Y position for sorting
                if hasattr(child, 'get_global_position'):
                    global_pos = child.get_global_position()
                    return global_pos[1] + self.sort_offset
                else:
                    return child.position[1] + self.sort_offset
            return 0.0
        
        return sorted(self.children, key=sort_key)
    
    def set_sort_enabled(self, enabled: bool):
        """Enable or disable sorting"""
        if self.sort_enabled != enabled:
            self.sort_enabled = enabled
            if enabled:
                self._mark_sort_needed()
    
    def get_sort_enabled(self) -> bool:
        """Get whether sorting is enabled"""
        return self.sort_enabled
    
    def set_sort_offset(self, offset: float):
        """Set the sort offset"""
        if self.sort_offset != offset:
            self.sort_offset = offset
            if self.sort_enabled:
                self._mark_sort_needed()
    
    def get_sort_offset(self) -> float:
        """Get the sort offset"""
        return self.sort_offset
    
    def force_sort(self):
        """Force an immediate sort of children"""
        if self.sort_enabled:
            self._needs_sort = True
            self._update_sort()
    
    def add_child(self, child):
        """Override add_child to trigger sorting"""
        super().add_child(child)
        self._connect_to_child(child)
        self._mark_sort_needed()
    
    def remove_child(self, child):
        """Override remove_child to trigger sorting"""
        self._disconnect_from_child(child)
        super().remove_child(child)
        self._mark_sort_needed()
