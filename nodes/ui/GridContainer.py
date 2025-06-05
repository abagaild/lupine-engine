"""
GridContainer node implementation for Lupine Engine
Grid layout container that automatically arranges children in a grid
"""

from nodes.ui.Control import Control
from typing import Dict, Any, List, Optional


class GridContainer(Control):
    """
    Grid layout container that automatically arranges children in a grid.
    
    Features:
    - Automatic grid child arrangement
    - Configurable number of columns
    - Configurable spacing between children
    - Equal cell sizing or content-based sizing
    - Margin and padding support
    - Automatic size calculation
    """
    
    def __init__(self, name: str = "GridContainer"):
        super().__init__(name)
        self.type = "GridContainer"
        
        # Export variables for editor
        self.export_variables.update({
            "columns": {
                "type": "int",
                "value": 2,
                "min": 1,
                "max": 20,
                "description": "Number of columns in the grid"
            },
            "separation": {
                "type": "float",
                "value": 4.0,
                "min": 0.0,
                "max": 100.0,
                "description": "Space between children (both H and V)"
            },
            "h_separation": {
                "type": "float",
                "value": 4.0,
                "min": 0.0,
                "max": 100.0,
                "description": "Horizontal space between children"
            },
            "v_separation": {
                "type": "float",
                "value": 4.0,
                "min": 0.0,
                "max": 100.0,
                "description": "Vertical space between children"
            },
            "alignment": {
                "type": "enum",
                "value": "top_left",
                "options": ["top_left", "top_center", "top_right", "center_left", "center", "center_right", "bottom_left", "bottom_center", "bottom_right"],
                "description": "Grid content alignment"
            },
            "equal_cell_size": {
                "type": "bool",
                "value": True,
                "description": "Make all cells the same size"
            },
            "fit_content_width": {
                "type": "bool",
                "value": True,
                "description": "Auto-resize width to fit grid"
            },
            "fit_content_height": {
                "type": "bool",
                "value": True,
                "description": "Auto-resize height to fit grid"
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
        self.columns = 2
        self.separation = 4.0  # General separation (used for both H and V if not specified separately)
        self.h_separation = 4.0  # Horizontal space between children
        self.v_separation = 4.0  # Vertical space between children
        self.alignment = "top_left"  # Grid content alignment
        self.equal_cell_size = True
        
        # Container properties
        self.fit_content_width = True
        self.fit_content_height = True
        
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
                pass
    
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
        if not self.children or self.columns <= 0:
            return
        
        # Get visible children
        visible_children = []
        for child in self.children:
            if (hasattr(child, 'visible') and child.visible and 
                hasattr(child, 'size') and hasattr(child, 'set_position')):
                visible_children.append(child)
        
        if not visible_children:
            return
        
        # Calculate grid dimensions
        rows = (len(visible_children) + self.columns - 1) // self.columns
        
        # Calculate cell size
        if self.equal_cell_size:
            # Find the largest child size
            max_width = 0.0
            max_height = 0.0
            for child in visible_children:
                max_width = max(max_width, child.size[0])
                max_height = max(max_height, child.size[1])
            cell_width = max_width
            cell_height = max_height
        else:
            # Use individual child sizes (simplified for now)
            cell_width = 100.0
            cell_height = 50.0
        
        # Calculate total grid size
        total_width = (self.columns * cell_width + 
                      (self.columns - 1) * self.h_separation + 
                      self.padding_left + self.padding_right)
        total_height = (rows * cell_height + 
                       (rows - 1) * self.v_separation + 
                       self.padding_top + self.padding_bottom)
        
        # Update container size if needed
        if self.fit_content_width:
            self.size[0] = total_width
        if self.fit_content_height:
            self.size[1] = total_height
        
        # Position children
        start_x = -self.size[0] / 2 + self.padding_left
        start_y = -self.size[1] / 2 + self.padding_top
        
        for i, child in enumerate(visible_children):
            row = i // self.columns
            col = i % self.columns
            
            # Calculate position
            child_x = start_x + col * (cell_width + self.h_separation) + cell_width / 2
            child_y = start_y + row * (cell_height + self.v_separation) + cell_height / 2
            
            # Set child position
            child.set_position(child_x, child_y)
            
            # Resize child if equal cell size is enabled
            if self.equal_cell_size and hasattr(child, 'set_size'):
                child.set_size(cell_width, cell_height)
        
        self.emit_signal("layout_changed")
    
    def set_columns(self, columns: int):
        """Set number of columns"""
        self.columns = max(1, columns)
        self._needs_layout_update = True
    
    def get_columns(self) -> int:
        """Get number of columns"""
        return self.columns
    
    def set_separation(self, h_separation: float, v_separation: Optional[float] = None):
        """Set separation between children"""
        self.h_separation = max(0.0, h_separation)
        if v_separation is not None:
            self.v_separation = max(0.0, v_separation)
        else:
            self.v_separation = self.h_separation
        self._needs_layout_update = True
    
    def get_separation(self) -> List[float]:
        """Get separation between children"""
        return [self.h_separation, self.v_separation]
    
    def set_equal_cell_size(self, equal: bool):
        """Set whether all cells should be the same size"""
        self.equal_cell_size = equal
        self._needs_layout_update = True
    
    def get_equal_cell_size(self) -> bool:
        """Get whether all cells are the same size"""
        return self.equal_cell_size
    
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
        
        # Add GridContainer-specific properties
        data.update({
            "columns": self.columns,
            "h_separation": self.h_separation,
            "v_separation": self.v_separation,
            "equal_cell_size": self.equal_cell_size,
            "fit_content_width": self.fit_content_width,
            "fit_content_height": self.fit_content_height,
            "padding_left": self.padding_left,
            "padding_top": self.padding_top,
            "padding_right": self.padding_right,
            "padding_bottom": self.padding_bottom,
            "background_color": self.background_color,
            "border_color": self.border_color,
            "border_width": self.border_width,
        })
        
        return data
