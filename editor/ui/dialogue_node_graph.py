"""
Dialogue Node Graph Component
Visual node graph editor for dialogue scripts
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox,
    QMenu, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QMouseEvent, QPaintEvent,
    QWheelEvent, QKeyEvent, QContextMenuEvent
)
from typing import Dict, List, Any, Optional, Tuple
import math

from core.dialogue.dialogue_parser import DialogueScript, DialogueNode, NodeType, DialogueChoice
from .dialogue_node_widget import DialogueNodeWidget


class ConnectionLine:
    """Represents a connection between two nodes"""
    
    def __init__(self, from_node: str, to_node: str, from_point: QPoint, to_point: QPoint, 
                 choice_index: int = -1, choice_text: str = ""):
        self.from_node = from_node
        self.to_node = to_node
        self.from_point = from_point
        self.to_point = to_point
        self.choice_index = choice_index
        self.choice_text = choice_text
    
    def draw(self, painter: QPainter):
        """Draw the connection line"""
        # Set pen based on connection type
        if self.choice_index >= 0:
            painter.setPen(QPen(QColor(150, 255, 150), 2))  # Green for choices
        else:
            painter.setPen(QPen(QColor(200, 200, 255), 2))  # Blue for regular connections
        
        # Draw curved line
        self._draw_curved_line(painter, self.from_point, self.to_point)
        
        # Draw arrow head
        self._draw_arrow_head(painter, self.from_point, self.to_point)
        
        # Draw choice text if applicable
        if self.choice_text:
            mid_point = QPoint(
                (self.from_point.x() + self.to_point.x()) // 2,
                (self.from_point.y() + self.to_point.y()) // 2
            )
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawText(mid_point.x() - 50, mid_point.y() - 10, 100, 20, 
                           Qt.AlignmentFlag.AlignCenter, self.choice_text)
    
    def _draw_curved_line(self, painter: QPainter, start: QPoint, end: QPoint):
        """Draw a curved line between two points"""
        # Calculate control points for bezier curve
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        # Control points for smooth curve
        ctrl1 = QPoint(start.x() + dx // 3, start.y())
        ctrl2 = QPoint(end.x() - dx // 3, end.y())
        
        # Draw bezier curve (simplified as multiple line segments)
        steps = 20
        prev_point = start
        
        for i in range(1, steps + 1):
            t = i / steps
            # Cubic bezier calculation
            point = self._bezier_point(start, ctrl1, ctrl2, end, t)
            painter.drawLine(prev_point, point)
            prev_point = point
    
    def _bezier_point(self, p0: QPoint, p1: QPoint, p2: QPoint, p3: QPoint, t: float) -> QPoint:
        """Calculate point on cubic bezier curve"""
        u = 1 - t
        tt = t * t
        uu = u * u
        uuu = uu * u
        ttt = tt * t
        
        x = uuu * p0.x() + 3 * uu * t * p1.x() + 3 * u * tt * p2.x() + ttt * p3.x()
        y = uuu * p0.y() + 3 * uu * t * p1.y() + 3 * u * tt * p2.y() + ttt * p3.y()
        
        return QPoint(int(x), int(y))
    
    def _draw_arrow_head(self, painter: QPainter, start: QPoint, end: QPoint):
        """Draw arrow head at the end point"""
        # Calculate arrow direction
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        # Normalize direction
        dx /= length
        dy /= length
        
        # Arrow head size
        arrow_length = 10
        arrow_width = 5
        
        # Calculate arrow points
        arrow_p1 = QPoint(
            int(end.x() - arrow_length * dx + arrow_width * dy),
            int(end.y() - arrow_length * dy - arrow_width * dx)
        )
        arrow_p2 = QPoint(
            int(end.x() - arrow_length * dx - arrow_width * dy),
            int(end.y() - arrow_length * dy + arrow_width * dx)
        )
        
        # Draw arrow head
        painter.drawLine(end, arrow_p1)
        painter.drawLine(end, arrow_p2)


class DialogueNodeGraphCanvas(QFrame):
    """Canvas widget for the dialogue node graph"""
    
    # Signals
    node_selected = pyqtSignal(str)  # node_id
    script_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.script: Optional[DialogueScript] = None
        self.node_widgets: Dict[str, DialogueNodeWidget] = {}
        self.connections: List[ConnectionLine] = []
        
        # View state
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.is_panning = False
        self.pan_start_pos = QPoint()
        
        # Selection state
        self.selected_node: Optional[str] = None
        
        # Grid settings
        self.show_grid = True
        self.grid_size = 20
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the canvas UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set background color
        self.setStyleSheet("background-color: rgb(45, 45, 45);")
    
    def set_script(self, script: DialogueScript):
        """Set the dialogue script to display"""
        self.script = script
        self.clear_canvas()
        self.create_node_widgets()
        self.update_connections()
        self.update()
    
    def clear_canvas(self):
        """Clear all nodes and connections"""
        for widget in self.node_widgets.values():
            widget.setParent(None)
        
        self.node_widgets.clear()
        self.connections.clear()
        self.selected_node = None
    
    def create_node_widgets(self):
        """Create widgets for all nodes in the script"""
        if not self.script:
            return
        
        # Auto-layout nodes if they don't have positions
        self.auto_layout_nodes()
        
        # Create widgets
        for node_id, node in self.script.nodes.items():
            widget = DialogueNodeWidget(node)
            widget.setParent(self)
            
            # Set position (with default if not specified)
            position = getattr(node, 'position', QPoint(100, 100))
            widget.set_position(position)
            widget.show()
            
            # Connect signals
            widget.node_selected.connect(self.on_node_selected)
            widget.node_moved.connect(self.on_node_moved)
            widget.node_edited.connect(self.on_node_edited)
            
            self.node_widgets[node_id] = widget
    
    def auto_layout_nodes(self):
        """Automatically layout nodes if they don't have positions"""
        if not self.script:
            return
        
        # Simple grid layout
        nodes_per_row = 3
        node_spacing_x = 200
        node_spacing_y = 150
        start_x = 50
        start_y = 50
        
        for i, (node_id, node) in enumerate(self.script.nodes.items()):
            if not hasattr(node, 'position') or not node.position:
                row = i // nodes_per_row
                col = i % nodes_per_row
                
                x = start_x + col * node_spacing_x
                y = start_y + row * node_spacing_y
                
                node.position = QPoint(x, y)
    
    def update_connections(self):
        """Update connection lines between nodes"""
        self.connections.clear()
        
        if not self.script:
            return
        
        for node_id, node in self.script.nodes.items():
            from_widget = self.node_widgets.get(node_id)
            if not from_widget:
                continue
            
            # Handle choices
            for i, choice in enumerate(node.choices):
                to_widget = self.node_widgets.get(choice.target_node)
                if to_widget:
                    from_point = from_widget.get_connection_point(False, i)
                    to_point = to_widget.get_connection_point(True)
                    
                    connection = ConnectionLine(
                        node_id, choice.target_node, from_point, to_point,
                        choice_index=i, choice_text=choice.text[:15] + "..." if len(choice.text) > 15 else choice.text
                    )
                    self.connections.append(connection)
            
            # Handle regular connections
            for connection_target in node.connections:
                to_widget = self.node_widgets.get(connection_target)
                if to_widget:
                    from_point = from_widget.get_connection_point(False)
                    to_point = to_widget.get_connection_point(True)
                    
                    connection = ConnectionLine(node_id, connection_target, from_point, to_point)
                    self.connections.append(connection)
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint event"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Apply zoom and pan transformations
        painter.scale(self.zoom_factor, self.zoom_factor)
        painter.translate(self.pan_offset)
        
        # Draw grid
        if self.show_grid:
            self._draw_grid(painter)
        
        # Draw connections
        for connection in self.connections:
            connection.draw(painter)
    
    def _draw_grid(self, painter: QPainter):
        """Draw background grid"""
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        
        # Calculate visible area
        visible_rect = self.rect()
        
        # Draw vertical lines
        start_x = -(self.pan_offset.x() % self.grid_size)
        for x in range(int(start_x), visible_rect.width(), self.grid_size):
            painter.drawLine(x, 0, x, visible_rect.height())
        
        # Draw horizontal lines
        start_y = -(self.pan_offset.y() % self.grid_size)
        for y in range(int(start_y), visible_rect.height(), self.grid_size):
            painter.drawLine(0, y, visible_rect.width(), y)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        if self.is_panning and event.buttons() & Qt.MouseButton.MiddleButton:
            delta = event.pos() - self.pan_start_pos
            self.pan_offset += delta
            self.pan_start_pos = event.pos()
            self.update()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle wheel events for zooming"""
        # Zoom in/out
        zoom_in = event.angleDelta().y() > 0
        zoom_factor = 1.1 if zoom_in else 1.0 / 1.1
        
        # Limit zoom range
        new_zoom = self.zoom_factor * zoom_factor
        if 0.1 <= new_zoom <= 3.0:
            self.zoom_factor = new_zoom
            self.update()
    
    def on_node_selected(self, node_id: str):
        """Handle node selection"""
        # Deselect previous node
        if self.selected_node and self.selected_node in self.node_widgets:
            self.node_widgets[self.selected_node].set_selected(False)
        
        # Select new node
        self.selected_node = node_id
        if node_id in self.node_widgets:
            self.node_widgets[node_id].set_selected(True)
        
        self.node_selected.emit(node_id)
    
    def on_node_moved(self, node_id: str, new_position: QPoint):
        """Handle node movement"""
        if node_id in self.node_widgets:
            widget = self.node_widgets[node_id]
            widget.set_position(new_position)
            
            # Update script node position
            if self.script and node_id in self.script.nodes:
                self.script.nodes[node_id].position = new_position
            
            # Update connections
            self.update_connections()
            self.update()
            self.script_changed.emit()
    
    def on_node_edited(self, node_id: str, node_data: Optional[Dict[str, Any]]):
        """Handle node editing"""
        if node_data is None:
            # Delete node
            self.delete_node(node_id)
        else:
            # Update node
            if self.script and node_id in self.script.nodes:
                # Update script
                old_node = self.script.nodes[node_id]
                new_node = DialogueNode(
                    node_id=node_data['node_id'],
                    node_type=NodeType(node_data['node_type']),
                    speaker=node_data.get('speaker'),
                    condition=node_data.get('condition')
                )
                new_node.dialogue_lines = node_data.get('dialogue_lines', [])
                new_node.commands = node_data.get('commands', [])
                new_node.connections = node_data.get('connections', [])
                new_node.position = old_node.position
                
                # Handle choices
                for choice_data in node_data.get('choices', []):
                    choice = DialogueChoice(
                        text=choice_data['text'],
                        target_node=choice_data['target_node'],
                        condition=choice_data.get('condition')
                    )
                    new_node.choices.append(choice)
                
                # Update script
                if node_data['node_id'] != node_id:
                    # Node ID changed, remove old and add new
                    del self.script.nodes[node_id]
                    self.script.nodes[node_data['node_id']] = new_node
                else:
                    self.script.nodes[node_id] = new_node
                
                # Recreate widgets
                self.create_node_widgets()
                self.update_connections()
                self.update()
                self.script_changed.emit()
    
    def delete_node(self, node_id: str):
        """Delete a node"""
        if self.script and node_id in self.script.nodes:
            # Remove from script
            del self.script.nodes[node_id]
            
            # Remove widget
            if node_id in self.node_widgets:
                self.node_widgets[node_id].setParent(None)
                del self.node_widgets[node_id]
            
            # Update connections
            self.update_connections()
            self.update()
            self.script_changed.emit()


class DialogueNodeGraph(QWidget):
    """Complete dialogue node graph widget with toolbar"""
    
    # Signals
    node_selected = pyqtSignal(str)
    script_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.canvas = DialogueNodeGraphCanvas()
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_node_btn = QPushButton("Add Node")
        self.auto_layout_btn = QPushButton("Auto Layout")
        self.zoom_fit_btn = QPushButton("Zoom to Fit")
        
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(True)
        
        toolbar_layout.addWidget(self.add_node_btn)
        toolbar_layout.addWidget(self.auto_layout_btn)
        toolbar_layout.addWidget(self.zoom_fit_btn)
        toolbar_layout.addSpacing(20)  # Add spacing instead of separator
        toolbar_layout.addWidget(self.grid_checkbox)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Canvas
        layout.addWidget(self.canvas)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.canvas.node_selected.connect(self.node_selected.emit)
        self.canvas.script_changed.connect(self.script_changed.emit)
        
        self.add_node_btn.clicked.connect(self.add_node)
        self.auto_layout_btn.clicked.connect(self.auto_layout)
        self.zoom_fit_btn.clicked.connect(self.zoom_to_fit)
        self.grid_checkbox.toggled.connect(self.toggle_grid)
    
    def set_script(self, script: DialogueScript):
        """Set the dialogue script"""
        self.canvas.set_script(script)
    
    def add_node(self):
        """Add a new node"""
        node_id, ok = QInputDialog.getText(self, "Add Node", "Node ID:")
        if ok and node_id:
            if self.canvas.script and node_id not in self.canvas.script.nodes:
                # Create new node
                new_node = DialogueNode(node_id=node_id, node_type=NodeType.DIALOGUE)
                new_node.position = QPoint(100, 100)
                
                # Add to script
                self.canvas.script.nodes[node_id] = new_node
                
                # Recreate widgets
                self.canvas.create_node_widgets()
                self.canvas.update_connections()
                self.canvas.update()
                self.script_changed.emit()
            else:
                QMessageBox.warning(self, "Error", "Node ID already exists or no script loaded.")
    
    def auto_layout(self):
        """Auto-layout all nodes"""
        if self.canvas.script:
            self.canvas.auto_layout_nodes()
            self.canvas.create_node_widgets()
            self.canvas.update_connections()
            self.canvas.update()
            self.script_changed.emit()
    
    def zoom_to_fit(self):
        """Zoom to fit all nodes"""
        # Reset zoom and pan
        self.canvas.zoom_factor = 1.0
        self.canvas.pan_offset = QPoint(0, 0)
        self.canvas.update()
    
    def toggle_grid(self, show: bool):
        """Toggle grid display"""
        self.canvas.show_grid = show
        self.canvas.update()
