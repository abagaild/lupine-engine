"""
Enhanced Visual Script Editor for Lupine Engine
Provides Blueprint-style visual scripting with advanced features
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox,
    QMenu, QMessageBox, QInputDialog, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTextEdit, QLineEdit, QGroupBox, QListWidget,
    QListWidgetItem, QTabWidget, QDialog, QDialogButtonBox,
    QFormLayout, QColorDialog, QFileDialog, QMainWindow,
    QMenuBar, QToolBar, QStatusBar, QDockWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer, QMimeData, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QMouseEvent, QPaintEvent,
    QWheelEvent, QKeyEvent, QContextMenuEvent, QDrag, QPixmap, QFont,
    QAction, QIcon, QPainterPath, QPolygonF
)
from PyQt6.QtCore import QPointF
from typing import Dict, List, Any, Optional, Tuple, Set
import json
import uuid
import os
from pathlib import Path

from core.prefabs.prefab_system import (
    VisualScriptBlock, VisualScriptBlockType, VisualScriptInput, 
    VisualScriptOutput
)
from core.prefabs.builtin_script_blocks import create_builtin_script_blocks


class VisualScriptConnection:
    """Represents a connection between two visual script blocks"""
    
    def __init__(self, from_block_id: str, from_output: str,
                 to_block_id: str, to_input: str, connection_type: str = "data",
                 id: Optional[str] = None, color: Optional[str] = None):
        self.id = id or str(uuid.uuid4())
        self.from_block_id = from_block_id
        self.from_output = from_output
        self.to_block_id = to_block_id
        self.to_input = to_input
        self.connection_type = connection_type  # "data" or "exec"
        self.color = color or ("#FFFFFF" if connection_type == "exec" else "#808080")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert connection to dictionary"""
        return {
            "id": self.id,
            "from_block_id": self.from_block_id,
            "from_output": self.from_output,
            "to_block_id": self.to_block_id,
            "to_input": self.to_input,
            "connection_type": self.connection_type,
            "color": self.color
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualScriptConnection":
        """Create connection from dictionary"""
        conn = cls(
            data["from_block_id"],
            data["from_output"],
            data["to_block_id"],
            data["to_input"],
            data.get("connection_type", "data")
        )
        conn.id = data.get("id", str(uuid.uuid4()))
        conn.color = data.get("color", "#808080")
        return conn


class EnhancedVisualScriptBlockWidget(QFrame):
    """Enhanced widget representing a visual script block with connection pins"""
    
    block_selected = pyqtSignal(object)  # EnhancedVisualScriptBlockWidget
    block_moved = pyqtSignal(object, QPoint)  # EnhancedVisualScriptBlockWidget, new_position
    connection_requested = pyqtSignal(object, str, bool)  # block, pin_name, is_output
    
    def __init__(self, script_block: VisualScriptBlock, parent=None):
        super().__init__(parent)
        self.script_block = script_block
        self.position = QPoint(100, 100)
        self.is_selected = False
        self.is_dragging = False
        self.drag_start_pos = QPoint()

        # Pin positions for connections
        self.input_pins: Dict[str, QRect] = {}
        self.output_pins: Dict[str, QRect] = {}

        # Node naming
        self.node_name = script_block.name  # Default to block name

        # Connection fallback - dropdown selectors for each pin
        self.input_connections: Dict[str, str] = {}  # pin_name -> source_node_id.output_pin
        self.output_connections: Dict[str, List[str]] = {}  # pin_name -> [target_node_id.input_pin, ...]

        self.setup_ui()
        self.update_appearance()
    
    def setup_ui(self):
        """Setup the block UI"""
        self.setMinimumSize(150, 80)
        self.setMaximumSize(400, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Node name editor
        self.name_edit = QLineEdit(self.node_name)
        self.name_edit.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.name_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_edit.textChanged.connect(self.on_name_changed)
        layout.addWidget(self.name_edit)

        # Block type label
        type_label = QLabel(f"({self.script_block.name})")
        type_label.setFont(QFont("Arial", 8))
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(type_label)

        # Block description (if short)
        if self.script_block.description and len(self.script_block.description) < 50:
            desc_label = QLabel(self.script_block.description)
            desc_label.setFont(QFont("Arial", 8))
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(desc_label)

        # Input widgets for editable inputs
        self.input_widgets = {}
        self.create_input_widgets(layout)

        self.setLayout(layout)

    def create_input_widgets(self, layout):
        """Create input widgets for editable block inputs"""
        from PyQt6.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox

        for input_pin in self.script_block.inputs:
            if hasattr(input_pin, 'is_execution_pin') and input_pin.is_execution_pin:
                continue  # Skip execution pins

            # Create input widget based on type
            widget = None
            if input_pin.type == "string":
                widget = QLineEdit()
                widget.setText(str(input_pin.default_value or ""))
                widget.setPlaceholderText(input_pin.description)
                widget.textChanged.connect(lambda text, pin=input_pin: self.on_input_changed(pin.name, text))

            elif input_pin.type == "number":
                if isinstance(input_pin.default_value, float):
                    widget = QDoubleSpinBox()
                    widget.setRange(-999999.0, 999999.0)
                    widget.setValue(float(input_pin.default_value or 0.0))
                    widget.valueChanged.connect(lambda value, pin=input_pin: self.on_input_changed(pin.name, value))
                else:
                    widget = QSpinBox()
                    widget.setRange(-999999, 999999)
                    widget.setValue(int(input_pin.default_value or 0))
                    widget.valueChanged.connect(lambda value, pin=input_pin: self.on_input_changed(pin.name, value))

            elif input_pin.type == "boolean":
                widget = QCheckBox()
                widget.setChecked(bool(input_pin.default_value))
                widget.toggled.connect(lambda checked, pin=input_pin: self.on_input_changed(pin.name, checked))

            elif input_pin.options:  # Dropdown for options
                widget = QComboBox()
                widget.addItems(input_pin.options)
                if input_pin.default_value in input_pin.options:
                    widget.setCurrentText(str(input_pin.default_value))
                widget.currentTextChanged.connect(lambda text, pin=input_pin: self.on_input_changed(pin.name, text))

            if widget:
                # Create a container with label
                container = QWidget()
                container_layout = QHBoxLayout(container)
                container_layout.setContentsMargins(2, 2, 2, 2)

                label = QLabel(input_pin.name + ":")
                label.setFont(QFont("Arial", 8))
                label.setMinimumWidth(40)
                container_layout.addWidget(label)

                widget.setFont(QFont("Arial", 8))
                widget.setMaximumHeight(20)
                container_layout.addWidget(widget)

                layout.addWidget(container)
                self.input_widgets[input_pin.name] = widget

        # Add connection fallback dropdowns
        self.create_connection_widgets(layout)

    def create_connection_widgets(self, layout):
        """Create connection fallback dropdown widgets"""
        from PyQt6.QtWidgets import QComboBox, QLabel

        # Input connection dropdowns
        for input_pin in self.script_block.inputs:
            if hasattr(input_pin, 'is_execution_pin') and input_pin.is_execution_pin:
                continue

            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(2, 2, 2, 2)

            label = QLabel(f"Connect {input_pin.name}:")
            label.setFont(QFont("Arial", 7))
            container_layout.addWidget(label)

            combo = QComboBox()
            combo.addItem("(No Connection)")
            combo.setFont(QFont("Arial", 7))
            combo.currentTextChanged.connect(
                lambda text, pin=input_pin.name: self.on_connection_changed(pin, text, True)
            )
            container_layout.addWidget(combo)

            layout.addWidget(container)
            self.input_widgets[f"connect_{input_pin.name}"] = combo

    def on_name_changed(self, new_name: str):
        """Handle node name change"""
        self.node_name = new_name
        if hasattr(self.parent(), 'script_changed'):
            self.parent().script_changed.emit()

    def on_connection_changed(self, pin_name: str, connection_text: str, is_input: bool):
        """Handle connection dropdown change"""
        if connection_text == "(No Connection)":
            if is_input and pin_name in self.input_connections:
                del self.input_connections[pin_name]
        else:
            if is_input:
                self.input_connections[pin_name] = connection_text

        if hasattr(self.parent(), 'script_changed'):
            self.parent().script_changed.emit()

    def update_connection_dropdowns(self, available_nodes: List['EnhancedVisualScriptBlockWidget']):
        """Update connection dropdown options"""
        for input_pin in self.script_block.inputs:
            if hasattr(input_pin, 'is_execution_pin') and input_pin.is_execution_pin:
                continue

            combo_key = f"connect_{input_pin.name}"
            if combo_key in self.input_widgets:
                combo = self.input_widgets[combo_key]
                current_text = combo.currentText()

                combo.clear()
                combo.addItem("(No Connection)")

                # Add available connections
                for node in available_nodes:
                    if node == self:  # Don't connect to self
                        continue

                    for output_pin in node.script_block.outputs:
                        if hasattr(output_pin, 'is_execution_pin') and output_pin.is_execution_pin:
                            continue

                        # Check type compatibility
                        if (input_pin.type == "any" or output_pin.type == "any" or
                            input_pin.type == output_pin.type):
                            connection_text = f"{node.node_name}.{output_pin.name}"
                            combo.addItem(connection_text)

                # Restore previous selection if still valid
                index = combo.findText(current_text)
                if index >= 0:
                    combo.setCurrentIndex(index)

    def on_input_changed(self, input_name: str, value):
        """Handle input value changes"""
        # Update the input pin's default value
        for input_pin in self.script_block.inputs:
            if input_pin.name == input_name:
                input_pin.default_value = value
                break

        # Emit signal that block data changed
        if hasattr(self.parent(), 'script_changed'):
            self.parent().script_changed.emit()
    
    def update_appearance(self):
        """Update the visual appearance based on state"""
        color = QColor(self.script_block.color)
        if self.is_selected:
            color = color.lighter(120)
        
        border_color = '#FFD700' if self.is_selected else '#333333'
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color.name()};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{
                color: white;
                background: transparent;
                border: none;
            }}
        """)
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint event to draw connection pins"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw input pins on the left
        y_offset = 30  # Start below title
        pin_size = 8
        pin_spacing = 20
        
        self.input_pins.clear()
        for i, input_pin in enumerate(self.script_block.inputs):
            pin_y = y_offset + i * pin_spacing
            pin_rect = QRect(-pin_size//2, pin_y, pin_size, pin_size)
            self.input_pins[input_pin.name] = pin_rect
            
            # Draw pin
            pin_color = getattr(input_pin, 'color', '#808080')
            painter.setBrush(QBrush(QColor(pin_color)))
            painter.setPen(QPen(QColor("white"), 1))
            painter.drawEllipse(pin_rect)
            
            # Draw pin label
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Arial", 7))
            painter.drawText(pin_size + 2, pin_y + pin_size//2 + 2, input_pin.name)
        
        # Draw output pins on the right
        self.output_pins.clear()
        for i, output_pin in enumerate(self.script_block.outputs):
            pin_y = y_offset + i * pin_spacing
            pin_rect = QRect(self.width() - pin_size//2, pin_y, pin_size, pin_size)
            self.output_pins[output_pin.name] = pin_rect
            
            # Draw pin
            pin_color = getattr(output_pin, 'color', '#808080')
            painter.setBrush(QBrush(QColor(pin_color)))
            painter.setPen(QPen(QColor("white"), 1))
            painter.drawEllipse(pin_rect)
            
            # Draw pin label (right-aligned)
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Arial", 7))
            text_width = painter.fontMetrics().horizontalAdvance(output_pin.name)
            painter.drawText(self.width() - pin_size - text_width - 2, 
                           pin_y + pin_size//2 + 2, output_pin.name)
    
    def get_input_pin_position(self, pin_name: str) -> Optional[QPoint]:
        """Get the global position of an input pin"""
        if pin_name in self.input_pins:
            local_rect = self.input_pins[pin_name]
            return self.mapToParent(local_rect.center())
        return None
    
    def get_output_pin_position(self, pin_name: str) -> Optional[QPoint]:
        """Get the global position of an output pin"""
        if pin_name in self.output_pins:
            local_rect = self.output_pins[pin_name]
            return self.mapToParent(local_rect.center())
        return None
    
    def set_position(self, position: QPoint):
        """Set the block position"""
        self.position = position
        self.move(position)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        self.update_appearance()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking on a pin
            local_pos = event.pos()

            # Check input pins
            for pin_name, pin_rect in self.input_pins.items():
                if pin_rect.contains(local_pos):
                    print(f"Input pin clicked: {pin_name}")  # Debug
                    self.connection_requested.emit(self, pin_name, False)
                    event.accept()
                    return

            # Check output pins
            for pin_name, pin_rect in self.output_pins.items():
                if pin_rect.contains(local_pos):
                    print(f"Output pin clicked: {pin_name}")  # Debug
                    self.connection_requested.emit(self, pin_name, True)
                    event.accept()
                    return

            # Regular block selection/dragging
            self.block_selected.emit(self)
            self.is_dragging = True
            self.drag_start_pos = event.pos()

        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.pos() - self.drag_start_pos
            new_position = self.position + delta
            self.set_position(new_position)
            self.block_moved.emit(self, new_position)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False


class EnhancedVisualScriptCanvas(QScrollArea):
    """Enhanced canvas for visual script editing with connection support"""
    
    script_changed = pyqtSignal()
    block_selected = pyqtSignal(object)  # EnhancedVisualScriptBlockWidget
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.script_blocks: List[EnhancedVisualScriptBlockWidget] = []
        self.connections: List[VisualScriptConnection] = []
        self.selected_block: Optional[EnhancedVisualScriptBlockWidget] = None
        
        # Connection state
        self.connecting_from_block: Optional[EnhancedVisualScriptBlockWidget] = None
        self.connecting_from_pin: Optional[str] = None
        self.connecting_is_output: bool = False
        self.temp_connection_end: Optional[QPoint] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the canvas UI"""
        self.canvas_widget = QWidget()
        self.canvas_widget.setMinimumSize(2000, 2000)
        self.canvas_widget.setStyleSheet("background-color: #2b2b2b;")
        self.setWidget(self.canvas_widget)
        
        # Enable mouse tracking for connection drawing
        self.canvas_widget.setMouseTracking(True)
        self.setMouseTracking(True)
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint event to draw connections"""
        super().paintEvent(event)
        
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw existing connections
        for connection in self.connections:
            self.draw_connection(painter, connection)
        
        # Draw temporary connection while connecting
        if (self.connecting_from_block and self.connecting_from_pin and 
            self.temp_connection_end):
            self.draw_temp_connection(painter)
    
    def draw_connection(self, painter: QPainter, connection: VisualScriptConnection):
        """Draw a connection between two blocks"""
        from_block = self.get_block_by_id(connection.from_block_id)
        to_block = self.get_block_by_id(connection.to_block_id)
        
        if not from_block or not to_block:
            return
        
        from_pos = from_block.get_output_pin_position(connection.from_output)
        to_pos = to_block.get_input_pin_position(connection.to_input)
        
        if not from_pos or not to_pos:
            return
        
        # Convert to viewport coordinates
        from_pos = self.widget().mapTo(self.viewport(), from_pos)
        to_pos = self.widget().mapTo(self.viewport(), to_pos)
        
        # Draw bezier curve
        painter.setPen(QPen(QColor(connection.color), 2))
        
        # Calculate control points for smooth curve
        control_offset = abs(to_pos.x() - from_pos.x()) * 0.5
        control1 = QPoint(int(from_pos.x() + control_offset), int(from_pos.y()))
        control2 = QPoint(int(to_pos.x() - control_offset), int(to_pos.y()))
        
        # Create bezier path
        path = QPainterPath()
        path.moveTo(QPointF(from_pos))
        path.cubicTo(QPointF(control1), QPointF(control2), QPointF(to_pos))
        painter.drawPath(path)
    
    def draw_temp_connection(self, painter: QPainter):
        """Draw temporary connection while connecting"""
        if not self.connecting_from_block or not self.connecting_from_pin:
            return
        
        if self.connecting_is_output:
            from_pos = self.connecting_from_block.get_output_pin_position(self.connecting_from_pin)
        else:
            from_pos = self.connecting_from_block.get_input_pin_position(self.connecting_from_pin)
        
        if not from_pos or not self.temp_connection_end:
            return
        
        # Convert to viewport coordinates
        from_pos = self.widget().mapTo(self.viewport(), from_pos)
        to_pos = self.temp_connection_end
        
        # Draw temporary connection
        painter.setPen(QPen(QColor("#FFFF00"), 2))  # Yellow for temp connection
        
        control_offset = abs(to_pos.x() - from_pos.x()) * 0.5
        control1 = QPoint(int(from_pos.x() + control_offset), int(from_pos.y()))
        control2 = QPoint(int(to_pos.x() - control_offset), int(to_pos.y()))
        
        path = QPainterPath()
        path.moveTo(QPointF(from_pos))
        path.cubicTo(QPointF(control1), QPointF(control2), QPointF(to_pos))
        painter.drawPath(path)

    def get_block_by_id(self, block_id: str) -> Optional[EnhancedVisualScriptBlockWidget]:
        """Get a block widget by its script block ID"""
        for block_widget in self.script_blocks:
            if block_widget.script_block.id == block_id:
                return block_widget
        return None

    def add_script_block(self, script_block: VisualScriptBlock, position: Optional[QPoint] = None, save_state: bool = True):
        """Add a script block to the canvas"""
        # Save state for undo if requested
        if save_state and hasattr(self.parent(), 'save_state_for_undo'):
            self.parent().save_state_for_undo()

        block_widget = EnhancedVisualScriptBlockWidget(script_block, self.canvas_widget)

        if position:
            block_widget.set_position(position)
        else:
            # Auto-position
            x = 100 + (len(self.script_blocks) % 5) * 220
            y = 100 + (len(self.script_blocks) // 5) * 140
            block_widget.set_position(QPoint(x, y))

        # Connect signals
        block_widget.block_selected.connect(self.on_block_selected)
        block_widget.block_moved.connect(self.on_block_moved)
        block_widget.connection_requested.connect(self.on_connection_requested)

        block_widget.show()
        self.script_blocks.append(block_widget)

        # Update connection dropdowns for all blocks
        self.update_all_connection_dropdowns()

        self.script_changed.emit()

    def update_all_connection_dropdowns(self):
        """Update connection dropdowns for all blocks"""
        for block_widget in self.script_blocks:
            block_widget.update_connection_dropdowns(self.script_blocks)

    def remove_script_block(self, block_widget: EnhancedVisualScriptBlockWidget):
        """Remove a script block from the canvas"""
        if block_widget in self.script_blocks:
            # Remove connections involving this block
            block_id = block_widget.script_block.id
            self.connections = [
                conn for conn in self.connections
                if conn.from_block_id != block_id and conn.to_block_id != block_id
            ]

            self.script_blocks.remove(block_widget)
            block_widget.deleteLater()

            if self.selected_block == block_widget:
                self.selected_block = None

            self.script_changed.emit()
            self.update()

    def clear_canvas(self):
        """Clear all blocks from the canvas"""
        for block_widget in self.script_blocks[:]:
            self.remove_script_block(block_widget)
        self.connections.clear()

    def on_block_selected(self, block_widget: EnhancedVisualScriptBlockWidget):
        """Handle block selection"""
        if self.selected_block:
            self.selected_block.set_selected(False)

        self.selected_block = block_widget
        block_widget.set_selected(True)
        self.block_selected.emit(block_widget)

    def on_block_moved(self, block_widget: EnhancedVisualScriptBlockWidget, new_position: QPoint):
        """Handle block movement"""
        # Update connections when blocks move
        self.update()  # Redraw connections

    def on_connection_requested(self, block_widget: EnhancedVisualScriptBlockWidget,
                               pin_name: str, is_output: bool):
        """Handle connection request from a pin"""
        if not self.connecting_from_block:
            # Start new connection
            self.connecting_from_block = block_widget
            self.connecting_from_pin = pin_name
            self.connecting_is_output = is_output
        else:
            # Complete connection
            if self.connecting_is_output != is_output:  # Can only connect output to input
                if is_output:
                    # Connecting from input to output (reverse)
                    from_block = block_widget
                    from_pin = pin_name
                    to_block = self.connecting_from_block
                    to_pin = self.connecting_from_pin
                else:
                    # Connecting from output to input (normal)
                    from_block = self.connecting_from_block
                    from_pin = self.connecting_from_pin
                    to_block = block_widget
                    to_pin = pin_name

                # Validate connection types (ensure pins are not None)
                if (from_pin and to_pin and
                    self.can_connect(from_block, from_pin, to_block, to_pin)):
                    self.create_connection(from_block, from_pin, to_block, to_pin)

            # Reset connection state
            self.connecting_from_block = None
            self.connecting_from_pin = None
            self.connecting_is_output = False
            self.temp_connection_end = None
            self.update()

    def can_connect(self, from_block: EnhancedVisualScriptBlockWidget, from_pin: str,
                   to_block: EnhancedVisualScriptBlockWidget, to_pin: str) -> bool:
        """Check if two pins can be connected"""
        # Find the output and input pin definitions
        from_output = None
        for output in from_block.script_block.outputs:
            if output.name == from_pin:
                from_output = output
                break

        to_input = None
        for input_pin in to_block.script_block.inputs:
            if input_pin.name == to_pin:
                to_input = input_pin
                break

        if not from_output or not to_input:
            return False

        # Check type compatibility
        if from_output.type == "any" or to_input.type == "any":
            return True

        return from_output.type == to_input.type

    def create_connection(self, from_block: EnhancedVisualScriptBlockWidget, from_pin: str,
                         to_block: EnhancedVisualScriptBlockWidget, to_pin: str):
        """Create a new connection between two pins"""
        # Check if connection already exists
        for conn in self.connections:
            if (conn.from_block_id == from_block.script_block.id and
                conn.from_output == from_pin and
                conn.to_block_id == to_block.script_block.id and
                conn.to_input == to_pin):
                return  # Connection already exists

        # Determine connection type
        from_output = None
        for output in from_block.script_block.outputs:
            if output.name == from_pin:
                from_output = output
                break

        connection_type = "exec" if from_output and getattr(from_output, 'is_execution_pin', False) else "data"

        # Create connection
        connection = VisualScriptConnection(
            from_block.script_block.id, from_pin,
            to_block.script_block.id, to_pin,
            connection_type
        )

        # Set color based on type
        if connection_type == "exec":
            connection.color = "#FFFFFF"
        else:
            connection.color = getattr(from_output, 'color', '#808080') if from_output else "#808080"

        self.connections.append(connection)
        self.script_changed.emit()
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for temporary connection drawing"""
        if self.connecting_from_block and self.connecting_from_pin:
            self.temp_connection_end = event.pos()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to cancel connection"""
        if event.button() == Qt.MouseButton.RightButton:
            # Cancel connection
            self.connecting_from_block = None
            self.connecting_from_pin = None
            self.connecting_is_output = False
            self.temp_connection_end = None
            self.update()
        super().mouseReleaseEvent(event)

    def get_script_data(self) -> Dict[str, Any]:
        """Get the current script data"""
        blocks_data = []
        for block_widget in self.script_blocks:
            blocks_data.append({
                "block_definition": block_widget.script_block,
                "position": [block_widget.position.x(), block_widget.position.y()]
            })

        connections_data = [conn.to_dict() for conn in self.connections]

        return {
            "blocks": blocks_data,
            "connections": connections_data
        }

    def load_script_data(self, script_data: Dict[str, Any]):
        """Load script data into the canvas"""
        self.clear_canvas()

        # Load blocks (don't save state when loading)
        for block_data in script_data.get('blocks', []):
            position = QPoint(block_data['position'][0], block_data['position'][1])
            self.add_script_block(block_data['block_definition'], position, save_state=False)

        # Load connections
        for conn_data in script_data.get('connections', []):
            connection = VisualScriptConnection.from_dict(conn_data)
            self.connections.append(connection)

        self.update()


class EnhancedVisualScriptEditor(QMainWindow):
    """Enhanced main visual script editor with Blueprint-style interface"""

    script_changed = pyqtSignal()
    script_saved = pyqtSignal(str)  # file_path

    def __init__(self, project=None, parent=None):
        super().__init__(parent)
        self.project = project
        self.current_script_file: Optional[str] = None
        self.current_script_data = {}
        self.builtin_blocks = create_builtin_script_blocks()

        # Undo/Redo system
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50

        # Clipboard
        self.clipboard_blocks = []

        self.setWindowTitle("Enhanced Visual Script Editor - Lupine Engine")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)

        self.setup_ui()
        self.setup_menus()
        self.setup_toolbars()
        self.setup_docks()
        self.setup_shortcuts()
        self.load_available_blocks()

    def setup_ui(self):
        """Setup the main UI"""
        # Central widget - tabbed interface
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Visual editor tab
        self.visual_tab = QWidget()
        self.setup_visual_tab()
        self.tab_widget.addTab(self.visual_tab, "Visual Editor")

        # Code editor tab
        self.code_tab = QWidget()
        self.setup_code_tab()
        self.tab_widget.addTab(self.code_tab, "Generated Code")

        # Connect tab change to update code
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def setup_visual_tab(self):
        """Setup the visual editor tab"""
        layout = QHBoxLayout(self.visual_tab)
        layout.setContentsMargins(4, 4, 4, 4)

        # Main canvas
        self.canvas = EnhancedVisualScriptCanvas()
        self.canvas.script_changed.connect(self.script_changed)
        self.canvas.block_selected.connect(self.on_block_selected)
        layout.addWidget(self.canvas)

    def setup_code_tab(self):
        """Setup the code editor tab"""
        layout = QVBoxLayout(self.code_tab)
        layout.setContentsMargins(4, 4, 4, 4)

        # Toolbar for code tab
        code_toolbar = QHBoxLayout()

        # Generate code button
        generate_btn = QPushButton("Generate Code")
        generate_btn.clicked.connect(self.generate_code)
        code_toolbar.addWidget(generate_btn)

        # Save code button
        save_code_btn = QPushButton("Save as Python File")
        save_code_btn.clicked.connect(self.save_generated_code)
        code_toolbar.addWidget(save_code_btn)

        code_toolbar.addStretch()
        layout.addLayout(code_toolbar)

        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)
        layout.addWidget(self.code_editor)

    def setup_menus(self):
        """Setup the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # New script
        new_action = QAction("New Visual Script", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_script)
        file_menu.addAction(new_action)

        # Open script
        open_action = QAction("Open Visual Script", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_script)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Save script
        save_action = QAction("Save Visual Script", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_script)
        file_menu.addAction(save_action)

        # Save as
        save_as_action = QAction("Save Visual Script As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_script_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Export to Python
        export_action = QAction("Export to Python", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_to_python)
        file_menu.addAction(export_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        # Clear canvas
        clear_action = QAction("Clear Canvas", self)
        clear_action.triggered.connect(self.clear_canvas)
        edit_menu.addAction(clear_action)

        # View menu
        view_menu = menubar.addMenu("View")

        # This will be populated when docks are created
        self.view_menu = view_menu

    def setup_toolbars(self):
        """Setup toolbars"""
        # Main toolbar
        main_toolbar = self.addToolBar("Main")

        # New script
        new_action = QAction("New", self)
        new_action.setToolTip("New Visual Script")
        new_action.triggered.connect(self.new_script)
        main_toolbar.addAction(new_action)

        # Open script
        open_action = QAction("Open", self)
        open_action.setToolTip("Open Visual Script")
        open_action.triggered.connect(self.open_script)
        main_toolbar.addAction(open_action)

        # Save script
        save_action = QAction("Save", self)
        save_action.setToolTip("Save Visual Script")
        save_action.triggered.connect(self.save_script)
        main_toolbar.addAction(save_action)

        main_toolbar.addSeparator()

        # Generate code
        generate_action = QAction("Generate Code", self)
        generate_action.setToolTip("Generate Python Code")
        generate_action.triggered.connect(self.generate_code)
        main_toolbar.addAction(generate_action)

    def setup_docks(self):
        """Setup dock widgets"""
        # Block library dock
        self.block_library_dock = QDockWidget("Block Library", self)
        self.block_library_dock.setObjectName("BlockLibraryDock")
        self.block_library_widget = self.create_block_library()
        self.block_library_dock.setWidget(self.block_library_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.block_library_dock)

        # Properties dock
        self.properties_dock = QDockWidget("Properties", self)
        self.properties_dock.setObjectName("PropertiesDock")
        self.properties_widget = self.create_properties_panel()
        self.properties_dock.setWidget(self.properties_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_dock)

        # Add dock toggles to view menu
        self.view_menu.addAction(self.block_library_dock.toggleViewAction())
        self.view_menu.addAction(self.properties_dock.toggleViewAction())

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        from PyQt6.QtGui import QShortcut, QKeySequence

        # Undo (Ctrl+Z)
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.undo)

        # Redo (Ctrl+Y)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_shortcut.activated.connect(self.redo)

        # Copy (Ctrl+C)
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy_selected)

        # Paste (Ctrl+V)
        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        paste_shortcut.activated.connect(self.paste)

        # Delete (Del)
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self.delete_selected)

        # Select All (Ctrl+A)
        select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        select_all_shortcut.activated.connect(self.select_all)

    def save_state_for_undo(self):
        """Save current state for undo functionality"""
        current_state = {
            'blocks': [],
            'connections': []
        }

        # Save blocks
        for block_widget in self.canvas.script_blocks:
            block_data = {
                'block': block_widget.script_block,
                'position': [block_widget.position.x(), block_widget.position.y()]
            }
            current_state['blocks'].append(block_data)

        # Save connections
        current_state['connections'] = [conn.to_dict() for conn in self.canvas.connections]

        # Add to undo stack
        self.undo_stack.append(current_state)

        # Limit undo stack size
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)

        # Clear redo stack when new action is performed
        self.redo_stack.clear()

    def undo(self):
        """Undo last action"""
        if not self.undo_stack:
            return

        # Save current state to redo stack
        current_state = self.get_current_state()
        self.redo_stack.append(current_state)

        # Restore previous state
        previous_state = self.undo_stack.pop()
        self.restore_state(previous_state)

    def redo(self):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        # Save current state to undo stack
        current_state = self.get_current_state()
        self.undo_stack.append(current_state)

        # Restore next state
        next_state = self.redo_stack.pop()
        self.restore_state(next_state)

    def get_current_state(self):
        """Get current editor state"""
        current_state = {
            'blocks': [],
            'connections': []
        }

        # Save blocks
        for block_widget in self.canvas.script_blocks:
            block_data = {
                'block': block_widget.script_block,
                'position': [block_widget.position.x(), block_widget.position.y()]
            }
            current_state['blocks'].append(block_data)

        # Save connections
        current_state['connections'] = [conn.to_dict() for conn in self.canvas.connections]

        return current_state

    def restore_state(self, state):
        """Restore editor state"""
        # Clear current canvas
        self.canvas.clear_canvas()

        # Restore blocks (don't save state when restoring)
        for block_data in state['blocks']:
            position = QPoint(block_data['position'][0], block_data['position'][1])
            self.canvas.add_script_block(block_data['block'], position, save_state=False)

        # Restore connections
        for conn_data in state['connections']:
            connection = VisualScriptConnection.from_dict(conn_data)
            self.canvas.connections.append(connection)

        self.canvas.update()

    def copy_selected(self):
        """Copy selected blocks to clipboard"""
        if self.canvas.selected_block:
            self.clipboard_blocks = [{
                'block': self.canvas.selected_block.script_block,
                'position': [self.canvas.selected_block.position.x(), self.canvas.selected_block.position.y()]
            }]

    def paste(self):
        """Paste blocks from clipboard"""
        if not self.clipboard_blocks:
            return

        self.save_state_for_undo()

        for block_data in self.clipboard_blocks:
            # Create a copy of the block with new ID
            new_block = VisualScriptBlock(
                id=str(uuid.uuid4()),
                name=block_data['block'].name,
                category=block_data['block'].category,
                block_type=block_data['block'].block_type,
                description=block_data['block'].description,
                inputs=block_data['block'].inputs.copy(),
                outputs=block_data['block'].outputs.copy(),
                code_template=block_data['block'].code_template,
                icon=block_data['block'].icon,
                color=block_data['block'].color
            )

            # Offset position slightly
            position = QPoint(block_data['position'][0] + 20, block_data['position'][1] + 20)
            self.canvas.add_script_block(new_block, position, save_state=False)

    def delete_selected(self):
        """Delete selected blocks"""
        if self.canvas.selected_block:
            self.save_state_for_undo()
            self.canvas.remove_script_block(self.canvas.selected_block)

    def select_all(self):
        """Select all blocks (for future multi-selection support)"""
        # For now, just select the first block if any exist
        if self.canvas.script_blocks:
            self.canvas.on_block_selected(self.canvas.script_blocks[0])

    def create_block_library(self) -> QWidget:
        """Create the block library panel"""
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QLineEdit, QGroupBox

        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("Script Blocks")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search blocks...")
        self.search_input.textChanged.connect(self.filter_blocks)
        layout.addWidget(self.search_input)

        # Category tabs
        self.block_tabs = QTabWidget()
        layout.addWidget(self.block_tabs)

        return panel

    def create_properties_panel(self) -> QWidget:
        """Create the properties panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("Properties")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Properties content
        self.properties_content = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_content)
        layout.addWidget(self.properties_content)

        # No selection message
        self.no_selection_label = QLabel("No block selected")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.properties_layout.addWidget(self.no_selection_label)

        layout.addStretch()
        return panel

    def load_available_blocks(self):
        """Load available script blocks into the library"""
        # Group blocks by category
        categories = {}
        for block in self.builtin_blocks:
            if block.category not in categories:
                categories[block.category] = []
            categories[block.category].append(block)

        # Create tabs for each category
        for category, blocks in sorted(categories.items()):
            tab_widget = QListWidget()
            tab_widget.setDragDropMode(QListWidget.DragDropMode.DragOnly)

            for block in blocks:
                item = QListWidgetItem(block.name)
                item.setData(Qt.ItemDataRole.UserRole, block)
                item.setToolTip(block.description)
                tab_widget.addItem(item)

            # Connect double-click to add block
            tab_widget.itemDoubleClicked.connect(self.add_block_from_library)

            self.block_tabs.addTab(tab_widget, category)

    def filter_blocks(self, search_text: str):
        """Filter blocks based on search text"""
        search_text = search_text.lower()

        for i in range(self.block_tabs.count()):
            tab_widget = self.block_tabs.widget(i)
            if isinstance(tab_widget, QListWidget):
                for j in range(tab_widget.count()):
                    item = tab_widget.item(j)
                    if item:
                        block = item.data(Qt.ItemDataRole.UserRole)
                        visible = (search_text in block.name.lower() or
                                 search_text in block.description.lower())
                        item.setHidden(not visible)

    def add_block_from_library(self, item: QListWidgetItem):
        """Add a block from the library to the canvas"""
        block = item.data(Qt.ItemDataRole.UserRole)
        if block:
            # Create a copy of the block with new ID
            new_block = VisualScriptBlock(
                id=str(uuid.uuid4()),
                name=block.name,
                category=block.category,
                block_type=block.block_type,
                description=block.description,
                inputs=block.inputs.copy(),
                outputs=block.outputs.copy(),
                code_template=block.code_template,
                icon=block.icon,
                color=block.color
            )
            self.canvas.add_script_block(new_block)

    def on_block_selected(self, block_widget: EnhancedVisualScriptBlockWidget):
        """Handle block selection"""
        self.update_properties_panel(block_widget)

    def update_properties_panel(self, block_widget: Optional[EnhancedVisualScriptBlockWidget]):
        """Update the properties panel for the selected block"""
        # Clear existing properties
        for i in reversed(range(self.properties_layout.count())):
            child = self.properties_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        if not block_widget:
            self.no_selection_label = QLabel("No block selected")
            self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.properties_layout.addWidget(self.no_selection_label)
            return

        block = block_widget.script_block

        # Block info
        info_group = QGroupBox("Block Information")
        info_layout = QFormLayout(info_group)

        info_layout.addRow("Name:", QLabel(block.name))
        info_layout.addRow("Type:", QLabel(block.block_type.value))
        info_layout.addRow("Category:", QLabel(block.category))

        desc_label = QLabel(block.description)
        desc_label.setWordWrap(True)
        info_layout.addRow("Description:", desc_label)

        self.properties_layout.addWidget(info_group)

        # Input properties
        if block.inputs:
            inputs_group = QGroupBox("Inputs")
            inputs_layout = QFormLayout(inputs_group)

            for input_pin in block.inputs:
                type_label = QLabel(f"{input_pin.type} ({'required' if input_pin.required else 'optional'})")
                inputs_layout.addRow(f"{input_pin.name}:", type_label)

            self.properties_layout.addWidget(inputs_group)

        # Output properties
        if block.outputs:
            outputs_group = QGroupBox("Outputs")
            outputs_layout = QFormLayout(outputs_group)

            for output_pin in block.outputs:
                type_label = QLabel(output_pin.type)
                outputs_layout.addRow(f"{output_pin.name}:", type_label)

            self.properties_layout.addWidget(outputs_group)

        self.properties_layout.addStretch()

    def on_tab_changed(self, index: int):
        """Handle tab change"""
        if index == 1:  # Code tab
            self.generate_code()

    def new_script(self):
        """Create a new visual script"""
        self.canvas.clear_canvas()
        self.current_script_file = None
        self.current_script_data = {}
        self.setWindowTitle("Enhanced Visual Script Editor - Lupine Engine - New Script")

    def open_script(self):
        """Open an existing visual script"""
        from PyQt6.QtWidgets import QFileDialog

        if self.project:
            scripts_dir = str(self.project.get_absolute_path("scripts"))
        else:
            scripts_dir = ""

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Visual Script", scripts_dir,
            "Visual Script Files (*.vscript);;All Files (*)"
        )

        if file_path:
            self.load_script_file(file_path)

    def load_script_file(self, file_path: str):
        """Load a visual script file"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)

            self.canvas.load_script_data(script_data)
            self.current_script_file = file_path
            self.current_script_data = script_data

            file_name = os.path.basename(file_path)
            self.setWindowTitle(f"Enhanced Visual Script Editor - Lupine Engine - {file_name}")

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to load script file:\n{e}")

    def save_script(self):
        """Save the current visual script"""
        if self.current_script_file:
            self.save_script_to_file(self.current_script_file)
        else:
            self.save_script_as()

    def save_script_as(self):
        """Save the visual script with a new name"""
        from PyQt6.QtWidgets import QFileDialog

        if self.project:
            scripts_dir = str(self.project.get_absolute_path("scripts"))
        else:
            scripts_dir = ""

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Visual Script", scripts_dir,
            "Visual Script Files (*.vscript);;All Files (*)"
        )

        if file_path:
            if not file_path.endswith('.vscript'):
                file_path += '.vscript'
            self.save_script_to_file(file_path)

    def save_script_to_file(self, file_path: str):
        """Save the visual script to a file"""
        try:
            import json
            script_data = self.canvas.get_script_data()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, default=str)

            self.current_script_file = file_path
            self.current_script_data = script_data

            file_name = os.path.basename(file_path)
            self.setWindowTitle(f"Enhanced Visual Script Editor - Lupine Engine - {file_name}")

            self.script_saved.emit(file_path)

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to save script file:\n{e}")

    def clear_canvas(self):
        """Clear the canvas"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self, "Clear Canvas",
            "Are you sure you want to clear the entire canvas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.clear_canvas()
            self.update_properties_panel(None)

    def generate_code(self):
        """Generate Python code from the visual script"""
        try:
            code = self.generate_python_code()
            self.code_editor.setPlainText(code)
        except Exception as e:
            error_code = f"# Error generating code:\n# {e}\n\n# Please check your visual script for errors."
            self.code_editor.setPlainText(error_code)

    def generate_python_code(self) -> str:
        """Generate Python code from the visual script blocks"""
        code_lines = [
            "# Generated Python code from visual script",
            "# Created with Lupine Engine Enhanced Visual Script Editor",
            "",
            "# Imports",
            "from core.game_engine import *",
            "from core.scene.base_node import Node",
            "",
        ]

        # Analyze execution flow
        execution_blocks = []
        data_blocks = []

        for block_widget in self.canvas.script_blocks:
            block = block_widget.script_block

            # Check if block has execution pins
            has_exec_input = any(inp.is_execution_pin for inp in block.inputs)
            has_exec_output = any(out.is_execution_pin for out in block.outputs)

            if has_exec_input or has_exec_output:
                execution_blocks.append(block_widget)
            else:
                data_blocks.append(block_widget)

        # Generate class definition
        code_lines.extend([
            "class GeneratedScript:",
            "    \"\"\"Generated script class from visual blocks\"\"\"",
            "    ",
            "    def __init__(self, node):",
            "        self.node = node",
            "        self._setup_variables()",
            "    ",
            "    def _setup_variables(self):",
            "        \"\"\"Setup variables from data blocks\"\"\"",
        ])

        # Generate variable initialization from data blocks
        for block_widget in data_blocks:
            block = block_widget.script_block
            if block.code_template:
                # Get the actual value from the block widget
                var_name = block_widget.node_name.lower().replace(" ", "_").replace("-", "_")
                var_name = "".join(c for c in var_name if c.isalnum() or c == "_")
                if not var_name or var_name[0].isdigit():
                    var_name = f"block_{var_name}"

                value = self._get_block_value_for_generation(block_widget)
                code_lines.append(f"        self.{var_name} = {value}")

        code_lines.extend([
            "    ",
            "    def execute(self):",
            "        \"\"\"Execute the visual script logic\"\"\"",
        ])

        # Generate execution flow
        if execution_blocks:
            # Find entry points (blocks with no execution input connections)
            entry_blocks = []
            for block_widget in execution_blocks:
                has_exec_input_connection = False
                for conn in self.canvas.connections:
                    if (conn.to_block_id == block_widget.script_block.id and
                        conn.connection_type == "exec"):
                        has_exec_input_connection = True
                        break

                if not has_exec_input_connection:
                    entry_blocks.append(block_widget)

            # Generate code for each entry point
            for entry_block in entry_blocks:
                self._generate_execution_chain(entry_block, code_lines, "        ")
        else:
            code_lines.append("        pass  # No execution blocks found")

        return "\n".join(code_lines)

    def _generate_execution_chain(self, block_widget: EnhancedVisualScriptBlockWidget,
                                 code_lines: List[str], indent: str):
        """Generate code for an execution chain starting from a block"""
        block = block_widget.script_block

        # Add comment
        code_lines.append(f"{indent}# {block.name}")

        # Generate block code
        if block.code_template:
            # Replace placeholders with actual values
            code = block.code_template

            # Simple placeholder replacement (in a full implementation, this would be more sophisticated)
            for input_pin in block.inputs:
                if not input_pin.is_execution_pin:
                    placeholder = f"{{{input_pin.name}}}"
                    if placeholder in code:
                        # Find connected value or use default
                        value = self._get_input_value(block_widget, input_pin.name)
                        code = code.replace(placeholder, str(value))

            code_lines.append(f"{indent}{code}")
        else:
            code_lines.append(f"{indent}pass  # {block.name}")

        # Find next execution blocks
        next_blocks = []
        for conn in self.canvas.connections:
            if (conn.from_block_id == block_widget.script_block.id and
                conn.connection_type == "exec"):
                next_block = self.canvas.get_block_by_id(conn.to_block_id)
                if next_block:
                    next_blocks.append(next_block)

        # Generate code for next blocks
        for next_block in next_blocks:
            code_lines.append("")
            self._generate_execution_chain(next_block, code_lines, indent)

    def _get_input_value(self, block_widget: EnhancedVisualScriptBlockWidget,
                        input_name: str) -> Any:
        """Get the value for an input pin"""
        # First check for direct connections
        for conn in self.canvas.connections:
            if (conn.to_block_id == block_widget.script_block.id and
                conn.to_input == input_name and
                conn.connection_type == "data"):

                # Find the source block
                source_block = self.canvas.get_block_by_id(conn.from_block_id)
                if source_block:
                    var_name = source_block.node_name.lower().replace(" ", "_").replace("-", "_")
                    var_name = "".join(c for c in var_name if c.isalnum() or c == "_")
                    if not var_name or var_name[0].isdigit():
                        var_name = f"block_{var_name}"
                    return f"self.{var_name}"

        # Check for fallback dropdown connections
        if input_name in block_widget.input_connections:
            connection_text = block_widget.input_connections[input_name]
            if "." in connection_text:
                node_name, output_pin = connection_text.split(".", 1)
                var_name = node_name.lower().replace(" ", "_").replace("-", "_")
                var_name = "".join(c for c in var_name if c.isalnum() or c == "_")
                if not var_name or var_name[0].isdigit():
                    var_name = f"block_{var_name}"
                return f"self.{var_name}"

        # Check for direct input widget value
        if input_name in block_widget.input_widgets:
            widget = block_widget.input_widgets[input_name]
            if hasattr(widget, 'text'):
                value = widget.text()
                # Quote strings properly
                for input_pin in block_widget.script_block.inputs:
                    if input_pin.name == input_name and input_pin.type == "string":
                        return f'"{value}"'
                return value
            elif hasattr(widget, 'value'):
                return widget.value()
            elif hasattr(widget, 'isChecked'):
                return widget.isChecked()

        # No connection found, use default value
        for input_pin in block_widget.script_block.inputs:
            if input_pin.name == input_name:
                if input_pin.type == "string" and input_pin.default_value:
                    return f'"{input_pin.default_value}"'
                return input_pin.default_value or "None"

        return "None"

    def _get_block_value_for_generation(self, block_widget: EnhancedVisualScriptBlockWidget) -> str:
        """Get the value for a block based on its inputs for code generation"""
        block = block_widget.script_block

        if block.code_template:
            # Process the code template with actual input values
            code = block.code_template

            for input_pin in block.inputs:
                if hasattr(input_pin, 'is_execution_pin') and input_pin.is_execution_pin:
                    continue

                placeholder = f"{{{input_pin.name}}}"
                if placeholder in code:
                    # Get the actual value from the input widget
                    value = self._get_widget_input_value(block_widget, input_pin.name)
                    code = code.replace(placeholder, str(value))

            return code
        else:
            return "None"

    def _get_widget_input_value(self, block_widget: EnhancedVisualScriptBlockWidget, input_name: str) -> Any:
        """Get input value from widget"""
        # Check if there's a direct input widget
        if input_name in block_widget.input_widgets:
            widget = block_widget.input_widgets[input_name]
            if hasattr(widget, 'text'):
                value = widget.text()
                # Quote strings properly
                for input_pin in block_widget.script_block.inputs:
                    if input_pin.name == input_name and input_pin.type == "string":
                        return f'"{value}"'
                return value
            elif hasattr(widget, 'value'):
                return widget.value()
            elif hasattr(widget, 'isChecked'):
                return widget.isChecked()

        # Use default value from pin
        for input_pin in block_widget.script_block.inputs:
            if input_pin.name == input_name:
                if input_pin.type == "string" and input_pin.default_value:
                    return f'"{input_pin.default_value}"'
                return input_pin.default_value or "None"

        return "None"

    def save_generated_code(self):
        """Save the generated code as a Python file"""
        from PyQt6.QtWidgets import QFileDialog

        if self.project:
            scripts_dir = str(self.project.get_absolute_path("scripts"))
        else:
            scripts_dir = ""

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Generated Python Code", scripts_dir,
            "Python Files (*.py);;All Files (*)"
        )

        if file_path:
            if not file_path.endswith('.py'):
                file_path += '.py'

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.code_editor.toPlainText())

                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", f"Code saved to:\n{file_path}")

            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", f"Failed to save code:\n{e}")

    def export_to_python(self):
        """Export the visual script to a Python file"""
        self.generate_code()
        self.save_generated_code()

    def get_script_data(self) -> Dict[str, Any]:
        """Get the current script data for saving"""
        script_data = {
            "version": "1.0",
            "name": "Visual Script",
            "description": "Generated visual script",
            "blocks": [],
            "connections": []
        }

        # Add blocks
        for block_widget in self.canvas.script_blocks:
            block_data = {
                "id": block_widget.script_block.id,
                "position": [block_widget.position.x(), block_widget.position.y()],
                "node_name": block_widget.node_name,
                "block_definition": {
                    "id": block_widget.script_block.id,
                    "name": block_widget.script_block.name,
                    "category": block_widget.script_block.category,
                    "block_type": {"value": block_widget.script_block.block_type.value},
                    "description": block_widget.script_block.description,
                    "inputs": [
                        {
                            "name": inp.name,
                            "type": inp.type,
                            "default_value": inp.default_value,
                            "description": inp.description,
                            "is_execution_pin": getattr(inp, 'is_execution_pin', False)
                        }
                        for inp in block_widget.script_block.inputs
                    ],
                    "outputs": [
                        {
                            "name": out.name,
                            "type": out.type,
                            "description": out.description,
                            "is_execution_pin": getattr(out, 'is_execution_pin', False)
                        }
                        for out in block_widget.script_block.outputs
                    ],
                    "code_template": block_widget.script_block.code_template,
                    "color": block_widget.script_block.color
                },
                "input_values": {},
                "input_connections": block_widget.input_connections.copy()
            }

            # Add input widget values
            for input_name, widget in block_widget.input_widgets.items():
                if not input_name.startswith("connect_"):
                    if hasattr(widget, 'text'):
                        block_data["input_values"][input_name] = widget.text()
                    elif hasattr(widget, 'value'):
                        block_data["input_values"][input_name] = widget.value()
                    elif hasattr(widget, 'isChecked'):
                        block_data["input_values"][input_name] = widget.isChecked()

            script_data["blocks"].append(block_data)

        # Add connections
        for connection in self.canvas.connections:
            conn_data = {
                "id": connection.id,
                "from_block_id": connection.from_block_id,
                "from_output": connection.from_output,
                "to_block_id": connection.to_block_id,
                "to_input": connection.to_input,
                "connection_type": connection.connection_type,
                "color": connection.color
            }
            script_data["connections"].append(conn_data)

        return script_data

    def load_script_data(self, script_data: Dict[str, Any]):
        """Load script data into the editor"""
        try:
            # Clear current canvas
            self.clear_canvas()

            # Load blocks
            for block_data in script_data.get("blocks", []):
                if "block_definition" in block_data:
                    block_def = block_data["block_definition"]

                    # Create visual script block
                    visual_block = self._create_visual_script_block_from_data(block_def)
                    if visual_block:
                        # Create block widget
                        block_widget = EnhancedVisualScriptBlockWidget(visual_block, self.canvas)

                        # Set position
                        if "position" in block_data:
                            pos = block_data["position"]
                            block_widget.position = QPoint(int(pos[0]), int(pos[1]))
                            block_widget.move(block_widget.position)

                        # Set node name
                        if "node_name" in block_data:
                            block_widget.node_name = block_data["node_name"]
                            if hasattr(block_widget, 'name_edit'):
                                block_widget.name_edit.setText(block_widget.node_name)

                        # Set input values
                        input_values = block_data.get("input_values", {})
                        for input_name, value in input_values.items():
                            if input_name in block_widget.input_widgets:
                                widget = block_widget.input_widgets[input_name]
                                if hasattr(widget, 'setText'):
                                    widget.setText(str(value))
                                elif hasattr(widget, 'setValue'):
                                    widget.setValue(value)
                                elif hasattr(widget, 'setChecked'):
                                    widget.setChecked(bool(value))

                        # Set input connections
                        input_connections = block_data.get("input_connections", {})
                        block_widget.input_connections = input_connections.copy()

                        # Add to canvas
                        block_widget.setParent(self.canvas)
                        block_widget.show()
                        self.canvas.script_blocks.append(block_widget)

            # Load connections
            for conn_data in script_data.get("connections", []):
                connection = VisualScriptConnection(
                    id=conn_data.get("id", str(uuid.uuid4())),
                    from_block_id=conn_data["from_block_id"],
                    from_output=conn_data["from_output"],
                    to_block_id=conn_data["to_block_id"],
                    to_input=conn_data["to_input"],
                    connection_type=conn_data.get("connection_type", "data"),
                    color=conn_data.get("color", "#808080")
                )
                self.canvas.connections.append(connection)

            # Update connection dropdowns
            self.canvas.update_all_connection_dropdowns()

            # Refresh canvas
            self.canvas.update()

        except Exception as e:
            print(f"Error loading script data: {e}")

    def _create_visual_script_block_from_data(self, block_def: Dict[str, Any]) -> Optional[VisualScriptBlock]:
        """Create a VisualScriptBlock from data"""
        try:
            from core.prefabs.prefab_system import VisualScriptInput, VisualScriptOutput, VisualScriptBlockType

            # Create inputs
            inputs = []
            for inp_data in block_def.get('inputs', []):
                input_obj = VisualScriptInput(
                    name=inp_data.get('name', ''),
                    type=inp_data.get('type', 'any'),
                    default_value=inp_data.get('default_value'),
                    description=inp_data.get('description', ''),
                    is_execution_pin=inp_data.get('is_execution_pin', False)
                )
                inputs.append(input_obj)

            # Create outputs
            outputs = []
            for out_data in block_def.get('outputs', []):
                output_obj = VisualScriptOutput(
                    name=out_data.get('name', ''),
                    type=out_data.get('type', 'any'),
                    description=out_data.get('description', ''),
                    is_execution_pin=out_data.get('is_execution_pin', False)
                )
                outputs.append(output_obj)

            # Get block type
            block_type_data = block_def.get('block_type', {})
            if isinstance(block_type_data, dict):
                block_type_value = block_type_data.get('value', 'action')
            else:
                block_type_value = str(block_type_data)

            # Map string to enum
            block_type_map = {
                'event': VisualScriptBlockType.EVENT,
                'action': VisualScriptBlockType.ACTION,
                'flow': VisualScriptBlockType.FLOW,
                'variable': VisualScriptBlockType.VARIABLE,
                'custom': VisualScriptBlockType.CUSTOM
            }
            block_type = block_type_map.get(block_type_value, VisualScriptBlockType.ACTION)

            # Create the block
            visual_block = VisualScriptBlock(
                id=block_def.get('id', str(uuid.uuid4())),
                name=block_def.get('name', ''),
                category=block_def.get('category', ''),
                block_type=block_type,
                description=block_def.get('description', ''),
                inputs=inputs,
                outputs=outputs,
                code_template=block_def.get('code_template', ''),
                color=block_def.get('color', '#808080')
            )

            return visual_block

        except Exception as e:
            print(f"Error creating visual script block: {e}")
            return None
