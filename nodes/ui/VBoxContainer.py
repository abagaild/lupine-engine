"""
VBoxContainer node implementation for Lupine Engine
Vertical layout container that automatically arranges children
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class VBoxContainer(Control):
    """
    Vertical layout container that automatically arranges children.
    
    Features:
    - Automatic vertical child arrangement
    - Configurable spacing between children
    - Alignment options (top, center, bottom)
    - Size flags for child expansion
    - Margin and padding support
    - Automatic size calculation
    """
    
    def __init__(self, name: str = "VBoxContainer"):
        super().__init__(name)
        self.type = "VBoxContainer"
        
        # Layout properties
        self.separation = 4.0  # Space between children
        self.alignment = "top"  # top, center, bottom
        
        # Container properties
        self.fit_content_height = True  # Auto-resize to fit children
        self.fit_content_width = False  # Keep fixed width
        
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
        
        # Calculate total content height
        total_height = 0.0
        for i, child in enumerate(visible_children):
            total_height += child.size[1]
            if i < len(visible_children) - 1:  # Add separation except for last child
                total_height += self.separation
        
        # Add padding
        content_height = total_height + self.padding_top + self.padding_bottom
        content_width = self.size[0]
        
        # Auto-resize container if enabled
        if self.fit_content_height:
            self.set_size(content_width, content_height)
        
        # Calculate starting Y position based on alignment
        available_height = self.size[1] - self.padding_top - self.padding_bottom
        
        if self.alignment == "top":
            start_y = self.padding_top
        elif self.alignment == "center":
            start_y = self.padding_top + (available_height - total_height) / 2
        elif self.alignment == "bottom":
            start_y = self.size[1] - self.padding_bottom - total_height
        else:
            start_y = self.padding_top
        
        # Position children
        current_y = start_y
        for child in visible_children:
            # Calculate X position (center horizontally within padding)
            available_width = self.size[0] - self.padding_left - self.padding_right
            child_x = self.padding_left
            
            # Handle child width expansion
            if hasattr(child, 'size_flags_horizontal'):
                if child.size_flags_horizontal == "expand_fill":
                    child.set_size(available_width, child.size[1])
                elif child.size_flags_horizontal == "shrink_center":
                    child_x = self.padding_left + (available_width - child.size[0]) / 2
                elif child.size_flags_horizontal == "shrink_end":
                    child_x = self.size[0] - self.padding_right - child.size[0]
            else:
                # Default: expand to fill width
                if self.fit_content_width:
                    # Keep child's original width
                    child_x = self.padding_left + (available_width - child.size[0]) / 2
                else:
                    # Expand child to fill available width
                    child.set_size(available_width, child.size[1])
            
            # Set child position
            child.set_position(child_x, current_y)
            
            # Move to next position
            current_y += child.size[1] + self.separation
        
        self.emit_signal("layout_changed")
    
    def set_separation(self, separation: float):
        """Set separation between children"""
        self.separation = max(0.0, separation)
        self._needs_layout_update = True
    
    def get_separation(self) -> float:
        """Get separation between children"""
        return self.separation
    
    def set_alignment(self, alignment: str):
        """Set vertical alignment"""
        valid_alignments = ["top", "center", "bottom"]
        if alignment in valid_alignments:
            self.alignment = alignment
            self._needs_layout_update = True
        else:
            print(f"Warning: Invalid alignment '{alignment}'. Valid alignments: {valid_alignments}")
    
    def get_alignment(self) -> str:
        """Get vertical alignment"""
        return self.alignment
    
    def set_fit_content(self, fit_height: bool, fit_width: bool = None):
        """Set content fitting options"""
        self.fit_content_height = fit_height
        if fit_width is not None:
            self.fit_content_width = fit_width
        self._needs_layout_update = True
    
    def set_padding(self, left: float, top: float, right: float, bottom: float):
        """Set padding values"""
        self.padding_left = max(0.0, left)
        self.padding_top = max(0.0, top)
        self.padding_right = max(0.0, right)
        self.padding_bottom = max(0.0, bottom)
        self._needs_layout_update = True
    
    def get_content_size(self) -> List[float]:
        """Get the minimum size needed to contain all children"""
        if not self.children:
            return [0.0, 0.0]
        
        visible_children = [child for child in self.children 
                           if hasattr(child, 'visible') and child.visible and hasattr(child, 'size')]
        
        if not visible_children:
            return [0.0, 0.0]
        
        # Calculate required width and height
        max_width = 0.0
        total_height = 0.0
        
        for i, child in enumerate(visible_children):
            max_width = max(max_width, child.size[0])
            total_height += child.size[1]
            if i < len(visible_children) - 1:
                total_height += self.separation
        
        # Add padding
        content_width = max_width + self.padding_left + self.padding_right
        content_height = total_height + self.padding_top + self.padding_bottom
        
        return [content_width, content_height]
    
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
        
        # Add VBoxContainer-specific properties
        data.update({
            "separation": self.separation,
            "alignment": self.alignment,
            "fit_content_height": self.fit_content_height,
            "fit_content_width": self.fit_content_width,
            "padding_left": self.padding_left,
            "padding_top": self.padding_top,
            "padding_right": self.padding_right,
            "padding_bottom": self.padding_bottom,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VBoxContainer":
        """Create from dictionary"""
        container = cls(data.get("name", "VBoxContainer"))
        cls._apply_node_properties(container, data)
        
        # Apply VBoxContainer properties
        container.separation = data.get("separation", 4.0)
        container.alignment = data.get("alignment", "top")
        container.fit_content_height = data.get("fit_content_height", True)
        container.fit_content_width = data.get("fit_content_width", False)
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
        return f"VBoxContainer({self.name}, rect={self.get_rect()}, children={len(self.children)})"
