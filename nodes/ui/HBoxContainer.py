"""
HBoxContainer node implementation for Lupine Engine
Horizontal layout container that automatically arranges children
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class HBoxContainer(Control):
    """
    Horizontal layout container that automatically arranges children.
    
    Features:
    - Automatic horizontal child arrangement
    - Configurable spacing between children
    - Alignment options (left, center, right)
    - Size flags for child expansion
    - Margin and padding support
    - Automatic size calculation
    """
    
    def __init__(self, name: str = "HBoxContainer"):
        super().__init__(name)
        self.type = "HBoxContainer"

        # Export variables for editor
        self.export_variables.update({
            "separation": {
                "type": "float",
                "value": 4.0,
                "min": 0.0,
                "max": 100.0,
                "description": "Space between children in pixels"
            },
            "alignment": {
                "type": "enum",
                "value": "left",
                "options": ["left", "center", "right"],
                "description": "Horizontal alignment of children"
            },
            "fit_content_width": {
                "type": "bool",
                "value": True,
                "description": "Auto-resize width to fit children"
            },
            "fit_content_height": {
                "type": "bool",
                "value": False,
                "description": "Auto-resize height to fit children"
            },
            "padding_left": {
                "type": "float",
                "value": 0.0,
                "min": 0.0,
                "max": 100.0,
                "description": "Left padding in pixels"
            },
            "padding_top": {
                "type": "float",
                "value": 0.0,
                "min": 0.0,
                "max": 100.0,
                "description": "Top padding in pixels"
            },
            "padding_right": {
                "type": "float",
                "value": 0.0,
                "min": 0.0,
                "max": 100.0,
                "description": "Right padding in pixels"
            },
            "padding_bottom": {
                "type": "float",
                "value": 0.0,
                "min": 0.0,
                "max": 100.0,
                "description": "Bottom padding in pixels"
            },
            "background_color": {
                "type": "color",
                "value": [0.0, 0.0, 0.0, 0.0],
                "description": "Background color (RGBA)"
            },
            "border_color": {
                "type": "color",
                "value": [0.5, 0.5, 0.5, 1.0],
                "description": "Border color (RGBA)"
            },
            "border_width": {
                "type": "float",
                "value": 0.0,
                "min": 0.0,
                "max": 10.0,
                "description": "Border width in pixels"
            }
        })

        # Layout properties
        self.separation = 4.0  # Space between children
        self.alignment = "left"  # left, center, right

        # Container properties
        self.fit_content_width = True  # Auto-resize to fit children
        self.fit_content_height = False  # Keep fixed height

        # Padding
        self.padding_left = 0.0
        self.padding_top = 0.0
        self.padding_right = 0.0
        self.padding_bottom = 0.0

        # Visual properties
        self.background_color = [0.0, 0.0, 0.0, 0.0]
        self.border_color = [0.5, 0.5, 0.5, 1.0]
        self.border_width = 0.0

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
        
        # Calculate total content width
        total_width = 0.0
        for i, child in enumerate(visible_children):
            total_width += child.size[0]
            if i < len(visible_children) - 1:  # Add separation except for last child
                total_width += self.separation
        
        # Add padding
        content_width = total_width + self.padding_left + self.padding_right
        content_height = self.size[1]
        
        # Auto-resize container if enabled
        if self.fit_content_width:
            self.set_size(content_width, content_height)
        
        # Calculate starting X position based on alignment
        available_width = self.size[0] - self.padding_left - self.padding_right
        
        if self.alignment == "left":
            start_x = self.padding_left
        elif self.alignment == "center":
            start_x = self.padding_left + (available_width - total_width) / 2
        elif self.alignment == "right":
            start_x = self.size[0] - self.padding_right - total_width
        else:
            start_x = self.padding_left
        
        # Position children
        current_x = start_x
        for child in visible_children:
            # Calculate Y position (center vertically within padding)
            available_height = self.size[1] - self.padding_top - self.padding_bottom
            child_y = self.padding_top
            
            # Handle child height expansion
            if hasattr(child, 'size_flags_vertical'):
                if child.size_flags_vertical == "expand_fill":
                    child.set_size(child.size[0], available_height)
                elif child.size_flags_vertical == "shrink_center":
                    child_y = self.padding_top + (available_height - child.size[1]) / 2
                elif child.size_flags_vertical == "shrink_end":
                    child_y = self.size[1] - self.padding_bottom - child.size[1]
            else:
                # Default: expand to fill height
                if self.fit_content_height:
                    # Keep child's original height
                    child_y = self.padding_top + (available_height - child.size[1]) / 2
                else:
                    # Expand child to fill available height
                    child.set_size(child.size[0], available_height)
            
            # Set child position
            child.set_position(current_x, child_y)
            
            # Move to next position
            current_x += child.size[0] + self.separation
        
        self.emit_signal("layout_changed")
    
    def set_separation(self, separation: float):
        """Set separation between children"""
        self.separation = max(0.0, separation)
        self._needs_layout_update = True
    
    def get_separation(self) -> float:
        """Get separation between children"""
        return self.separation
    
    def set_alignment(self, alignment: str):
        """Set horizontal alignment"""
        valid_alignments = ["left", "center", "right"]
        if alignment in valid_alignments:
            self.alignment = alignment
            self._needs_layout_update = True
        else:
            print(f"Warning: Invalid alignment '{alignment}'. Valid alignments: {valid_alignments}")
    
    def get_alignment(self) -> str:
        """Get horizontal alignment"""
        return self.alignment
    
    def set_fit_content(self, fit_width: bool, fit_height: Optional[bool] = None):
        """Set content fitting options"""
        self.fit_content_width = fit_width
        if fit_height is not None:
            self.fit_content_height = fit_height
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
        total_width = 0.0
        max_height = 0.0
        
        for i, child in enumerate(visible_children):
            total_width += child.size[0]
            max_height = max(max_height, child.size[1])
            if i < len(visible_children) - 1:
                total_width += self.separation
        
        # Add padding
        content_width = total_width + self.padding_left + self.padding_right
        content_height = max_height + self.padding_top + self.padding_bottom
        
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
        
        # Add HBoxContainer-specific properties
        data.update({
            "separation": self.separation,
            "alignment": self.alignment,
            "fit_content_width": self.fit_content_width,
            "fit_content_height": self.fit_content_height,
            "padding_left": self.padding_left,
            "padding_top": self.padding_top,
            "padding_right": self.padding_right,
            "padding_bottom": self.padding_bottom,
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HBoxContainer":
        """Create from dictionary"""
        container = cls(data.get("name", "HBoxContainer"))
        cls._apply_node_properties(container, data)
        
        # Apply HBoxContainer properties
        container.separation = data.get("separation", 4.0)
        container.alignment = data.get("alignment", "left")
        container.fit_content_width = data.get("fit_content_width", True)
        container.fit_content_height = data.get("fit_content_height", False)
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
        return f"HBoxContainer({self.name}, rect={self.get_rect()}, children={len(self.children)})"
