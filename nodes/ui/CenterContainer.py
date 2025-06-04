"""
CenterContainer node implementation for Lupine Engine
Container that centers its children within its bounds
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class CenterContainer(Control):
    """
    Container that centers its children within its bounds.
    
    Features:
    - Automatic child centering (horizontal and vertical)
    - Option to use top-left positioning instead
    - Maintains child sizes while centering positions
    - Supports multiple children with stacking
    - Padding support for content area
    """
    
    def __init__(self, name: str = "CenterContainer"):
        super().__init__(name)
        self.type = "CenterContainer"
        
        # Layout properties
        self.use_top_left = False  # If true, align to top-left instead of center
        
        # Padding
        self.padding_left = 0.0
        self.padding_top = 0.0
        self.padding_right = 0.0
        self.padding_bottom = 0.0
        
        # Built-in signals
        self.add_signal("layout_changed")
        
        # Internal state
        self._needs_layout_update = True
    
    def _ready(self):
        """Called when container enters the scene tree"""
        super()._ready()
        
        # Connect to child signals
        self.connect("child_entered_tree", self, "_on_child_added")
        self.connect("child_exiting_tree", self, "_on_child_removed")
        self.connect("resized", self, "_on_container_resized")
        
        # Initial layout
        self._update_layout()
    
    def _on_child_added(self, child):
        """Handle child being added"""
        self._needs_layout_update = True
        if hasattr(child, 'connect') and hasattr(child, 'resized'):
            child.connect("resized", self, "_on_child_resized")
    
    def _on_child_removed(self, child):
        """Handle child being removed"""
        self._needs_layout_update = True
        if hasattr(child, 'disconnect'):
            try:
                child.disconnect("resized", self, "_on_child_resized")
            except:
                pass  # Connection might not exist
    
    def _on_child_resized(self):
        """Handle child resize"""
        self._needs_layout_update = True
    
    def _on_container_resized(self):
        """Handle container resize"""
        self._needs_layout_update = True
    
    def _process(self, delta: float):
        """Process layout updates"""
        super()._process(delta)
        
        if self._needs_layout_update:
            self._update_layout()
            self._needs_layout_update = False
    
    def _update_layout(self):
        """Update the layout of children"""
        if not self.children:
            return
        
        # Get visible children with size
        visible_children = []
        for child in self.children:
            if (hasattr(child, 'visible') and child.visible and 
                hasattr(child, 'size') and hasattr(child, 'set_position')):
                visible_children.append(child)
        
        if not visible_children:
            return
        
        # Calculate content area
        content_x = self.padding_left
        content_y = self.padding_top
        content_width = max(0, self.size[0] - self.padding_left - self.padding_right)
        content_height = max(0, self.size[1] - self.padding_top - self.padding_bottom)
        
        # Position each child
        for child in visible_children:
            if self.use_top_left:
                # Align to top-left of content area
                child_x = content_x
                child_y = content_y
            else:
                # Center within content area
                child_x = content_x + (content_width - child.size[0]) / 2
                child_y = content_y + (content_height - child.size[1]) / 2
            
            # Set child position
            child.set_position(child_x, child_y)
        
        self.emit_signal("layout_changed")
    
    def set_use_top_left(self, use_top_left: bool):
        """Set whether to use top-left alignment instead of centering"""
        self.use_top_left = use_top_left
        self._needs_layout_update = True
    
    def get_use_top_left(self) -> bool:
        """Get whether using top-left alignment"""
        return self.use_top_left
    
    def set_padding(self, left: float, top: float, right: float, bottom: float):
        """Set padding values"""
        self.padding_left = max(0.0, left)
        self.padding_top = max(0.0, top)
        self.padding_right = max(0.0, right)
        self.padding_bottom = max(0.0, bottom)
        self._needs_layout_update = True
    
    def get_content_rect(self) -> List[float]:
        """Get the content area rectangle [x, y, width, height]"""
        content_x = self.padding_left
        content_y = self.padding_top
        content_width = max(0, self.size[0] - self.padding_left - self.padding_right)
        content_height = max(0, self.size[1] - self.padding_top - self.padding_bottom)
        return [content_x, content_y, content_width, content_height]
    
    def get_centered_position_for_size(self, child_size: List[float]) -> List[float]:
        """Get the centered position for a child of given size"""
        content_rect = self.get_content_rect()
        
        if self.use_top_left:
            return [content_rect[0], content_rect[1]]
        else:
            center_x = content_rect[0] + (content_rect[2] - child_size[0]) / 2
            center_y = content_rect[1] + (content_rect[3] - child_size[1]) / 2
            return [center_x, center_y]
    
    def add_child(self, child):
        """Override add_child to trigger layout update"""
        super().add_child(child)
        self._needs_layout_update = True
    
    def remove_child(self, child):
        """Override remove_child to trigger layout update"""
        super().remove_child(child)
        self._needs_layout_update = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        
        # Add CenterContainer-specific properties
        data.update({
            "use_top_left": self.use_top_left,
            "padding_left": self.padding_left,
            "padding_top": self.padding_top,
            "padding_right": self.padding_right,
            "padding_bottom": self.padding_bottom,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CenterContainer":
        """Create from dictionary"""
        container = cls(data.get("name", "CenterContainer"))
        cls._apply_node_properties(container, data)
        
        # Apply CenterContainer properties
        container.use_top_left = data.get("use_top_left", False)
        container.padding_left = data.get("padding_left", 0.0)
        container.padding_top = data.get("padding_top", 0.0)
        container.padding_right = data.get("padding_right", 0.0)
        container.padding_bottom = data.get("padding_bottom", 0.0)
        
        # Create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            container.add_child(child)
        
        return container
    
    def __str__(self) -> str:
        """String representation of the container"""
        return f"CenterContainer({self.name}, rect={self.get_rect()}, children={len(self.children)})"
