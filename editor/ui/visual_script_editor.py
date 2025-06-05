"""
Visual Script Editor for Lupine Engine
Provides RPG Maker-style visual scripting interface
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox,
    QMenu, QMessageBox, QInputDialog, QSplitter, QTreeWidget,
    QTreeWidgetItem, QTextEdit, QLineEdit, QGroupBox, QListWidget,
    QListWidgetItem, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer, QMimeData
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QMouseEvent, QPaintEvent,
    QWheelEvent, QKeyEvent, QContextMenuEvent, QDrag, QPixmap, QFont
)
from typing import Dict, List, Any, Optional, Tuple
import json
import uuid

from core.prefabs.prefab_system import VisualScriptBlock, VisualScriptBlockType, VisualScriptInput, VisualScriptOutput


class VisualScriptBlockWidget(QFrame):
    """Widget representing a visual script block"""
    
    block_selected = pyqtSignal(object)  # VisualScriptBlockWidget
    block_moved = pyqtSignal(object, QPoint)  # VisualScriptBlockWidget, new_position
    block_connected = pyqtSignal(object, object, str, str)  # from_block, to_block, output_name, input_name
    
    def __init__(self, script_block: VisualScriptBlock, parent=None):
        super().__init__(parent)
        self.script_block = script_block
        self.position = QPoint(100, 100)
        self.is_selected = False
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        
        self.setup_ui()
        self.update_appearance()
    
    def setup_ui(self):
        """Setup the block UI"""
        self.setFixedSize(200, 120)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Title
        title_label = QLabel(self.script_block.name)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        if self.script_block.description:
            desc_label = QLabel(self.script_block.description)
            desc_label.setFont(QFont("Arial", 8))
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(desc_label)
        
        # Inputs and outputs (simplified representation)
        if self.script_block.inputs or self.script_block.outputs:
            io_layout = QHBoxLayout()
            
            # Inputs
            if self.script_block.inputs:
                inputs_label = QLabel(f"In: {len(self.script_block.inputs)}")
                inputs_label.setFont(QFont("Arial", 8))
                io_layout.addWidget(inputs_label)
            
            io_layout.addStretch()
            
            # Outputs
            if self.script_block.outputs:
                outputs_label = QLabel(f"Out: {len(self.script_block.outputs)}")
                outputs_label.setFont(QFont("Arial", 8))
                io_layout.addWidget(outputs_label)
            
            layout.addLayout(io_layout)
        
        layout.addStretch()
    
    def update_appearance(self):
        """Update the visual appearance based on state"""
        color = QColor(self.script_block.color)
        if self.is_selected:
            color = color.lighter(120)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color.name()};
                border: 2px solid {'#FFD700' if self.is_selected else '#333333'};
                border-radius: 8px;
            }}
            QLabel {{
                color: white;
                background: transparent;
                border: none;
            }}
        """)
    
    def set_position(self, position: QPoint):
        """Set the block position"""
        self.position = position
        self.move(position)
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        self.update_appearance()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.pos()
            self.block_selected.emit(self)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move"""
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = self.position + (event.pos() - self.drag_start_pos)
            self.set_position(new_pos)
            self.block_moved.emit(self, new_pos)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
        super().mouseReleaseEvent(event)


class VisualScriptCanvas(QScrollArea):
    """Canvas for visual script editing"""
    
    script_changed = pyqtSignal()
    block_selected = pyqtSignal(object)  # VisualScriptBlockWidget
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.script_blocks: List[VisualScriptBlockWidget] = []
        self.connections: List[Dict[str, Any]] = []
        self.selected_block: Optional[VisualScriptBlockWidget] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the canvas UI"""
        # Create canvas widget
        self.canvas_widget = QWidget()
        self.canvas_widget.setMinimumSize(2000, 2000)
        self.canvas_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                background-image: 
                    radial-gradient(circle, #404040 1px, transparent 1px);
                background-size: 20px 20px;
            }
        """)
        
        self.setWidget(self.canvas_widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    def add_script_block(self, script_block: VisualScriptBlock, position: Optional[QPoint] = None):
        """Add a script block to the canvas"""
        block_widget = VisualScriptBlockWidget(script_block, self.canvas_widget)
        
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
        
        block_widget.show()
        self.script_blocks.append(block_widget)
        self.script_changed.emit()
    
    def remove_script_block(self, block_widget: VisualScriptBlockWidget):
        """Remove a script block from the canvas"""
        if block_widget in self.script_blocks:
            self.script_blocks.remove(block_widget)
            block_widget.deleteLater()
            
            # Remove connections involving this block
            self.connections = [
                conn for conn in self.connections
                if conn['from_block'] != block_widget and conn['to_block'] != block_widget
            ]
            
            if self.selected_block == block_widget:
                self.selected_block = None
            
            self.script_changed.emit()
    
    def clear_canvas(self):
        """Clear all blocks from the canvas"""
        for block_widget in self.script_blocks[:]:
            self.remove_script_block(block_widget)
    
    def on_block_selected(self, block_widget: VisualScriptBlockWidget):
        """Handle block selection"""
        # Deselect previous block
        if self.selected_block:
            self.selected_block.set_selected(False)
        
        # Select new block
        self.selected_block = block_widget
        block_widget.set_selected(True)
        
        self.block_selected.emit(block_widget)
    
    def on_block_moved(self, block_widget: VisualScriptBlockWidget, new_position: QPoint):
        """Handle block movement"""
        self.script_changed.emit()
    
    def get_script_data(self) -> Dict[str, Any]:
        """Get the current script data"""
        blocks_data = []
        for block_widget in self.script_blocks:
            block_data = {
                'id': block_widget.script_block.id,
                'position': [block_widget.position.x(), block_widget.position.y()],
                'block_definition': block_widget.script_block
            }
            blocks_data.append(block_data)
        
        return {
            'blocks': blocks_data,
            'connections': self.connections
        }
    
    def load_script_data(self, script_data: Dict[str, Any]):
        """Load script data into the canvas"""
        self.clear_canvas()
        
        # Load blocks
        for block_data in script_data.get('blocks', []):
            position = QPoint(block_data['position'][0], block_data['position'][1])
            self.add_script_block(block_data['block_definition'], position)
        
        # Load connections
        self.connections = script_data.get('connections', [])


class VisualScriptEditor(QWidget):
    """Main visual script editor widget"""
    
    script_changed = pyqtSignal()
    
    def __init__(self, prefab_manager=None, parent=None):
        super().__init__(parent)
        self.prefab_manager = prefab_manager
        self.current_script_data = {}
        
        self.setup_ui()
        self.load_available_blocks()
    
    def setup_ui(self):
        """Setup the editor UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Block library
        left_panel = self.create_block_library()
        splitter.addWidget(left_panel)
        
        # Center - Canvas
        self.canvas = VisualScriptCanvas()
        self.canvas.script_changed.connect(self.script_changed)
        self.canvas.block_selected.connect(self.on_block_selected)
        splitter.addWidget(self.canvas)
        
        # Right panel - Properties
        right_panel = self.create_properties_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([250, 800, 250])
    
    def create_block_library(self) -> QWidget:
        """Create the block library panel"""
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
        
        # Properties area
        self.properties_area = QScrollArea()
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_widget)
        self.properties_area.setWidget(self.properties_widget)
        self.properties_area.setWidgetResizable(True)
        layout.addWidget(self.properties_area)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        delete_btn = QPushButton("Delete Block")
        delete_btn.clicked.connect(self.delete_selected_block)
        buttons_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_script)
        buttons_layout.addWidget(clear_btn)
        
        layout.addLayout(buttons_layout)
        
        return panel
    
    def load_available_blocks(self):
        """Load available script blocks into the library"""
        if not self.prefab_manager:
            return
        
        # Get all script block categories
        categories = self.prefab_manager.get_all_script_block_categories()
        
        for category in sorted(categories):
            # Create tab for category
            tab_widget = QListWidget()
            tab_widget.setDragDropMode(QListWidget.DragDropMode.DragOnly)
            
            # Add blocks to tab
            blocks = self.prefab_manager.get_script_blocks_by_category(category)
            for block in blocks:
                item = QListWidgetItem(block.name)
                item.setData(Qt.ItemDataRole.UserRole, block)
                item.setToolTip(block.description)
                tab_widget.addItem(item)
            
            # Connect double-click to add block
            tab_widget.itemDoubleClicked.connect(self.add_block_from_library)
            
            self.block_tabs.addTab(tab_widget, category)
    
    def filter_blocks(self, text: str):
        """Filter blocks based on search text"""
        # Implementation for filtering blocks
        pass
    
    def add_block_from_library(self, item: QListWidgetItem):
        """Add a block from the library to the canvas"""
        block = item.data(Qt.ItemDataRole.UserRole)
        if block:
            self.canvas.add_script_block(block)
    
    def on_block_selected(self, block_widget: VisualScriptBlockWidget):
        """Handle block selection"""
        self.update_properties_panel(block_widget)
    
    def update_properties_panel(self, block_widget: Optional[VisualScriptBlockWidget]):
        """Update the properties panel for the selected block"""
        # Clear existing properties
        for i in reversed(range(self.properties_layout.count())):
            child = self.properties_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        if not block_widget:
            return
        
        block = block_widget.script_block
        
        # Block info
        info_group = QGroupBox("Block Info")
        info_layout = QVBoxLayout(info_group)
        
        info_layout.addWidget(QLabel(f"Name: {block.name}"))
        info_layout.addWidget(QLabel(f"Type: {block.block_type.value}"))
        info_layout.addWidget(QLabel(f"Category: {block.category}"))
        
        if block.description:
            desc_label = QLabel(f"Description: {block.description}")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        self.properties_layout.addWidget(info_group)
        
        # Inputs
        if block.inputs:
            inputs_group = QGroupBox("Inputs")
            inputs_layout = QVBoxLayout(inputs_group)
            
            for input_param in block.inputs:
                input_label = QLabel(f"{input_param.name} ({input_param.type})")
                inputs_layout.addWidget(input_label)
                
                if input_param.description:
                    desc_label = QLabel(input_param.description)
                    desc_label.setStyleSheet("color: gray; font-size: 10px;")
                    inputs_layout.addWidget(desc_label)
            
            self.properties_layout.addWidget(inputs_group)
        
        # Outputs
        if block.outputs:
            outputs_group = QGroupBox("Outputs")
            outputs_layout = QVBoxLayout(outputs_group)
            
            for output_param in block.outputs:
                output_label = QLabel(f"{output_param.name} ({output_param.type})")
                outputs_layout.addWidget(output_label)
                
                if output_param.description:
                    desc_label = QLabel(output_param.description)
                    desc_label.setStyleSheet("color: gray; font-size: 10px;")
                    outputs_layout.addWidget(desc_label)
            
            self.properties_layout.addWidget(outputs_group)
        
        self.properties_layout.addStretch()
    
    def delete_selected_block(self):
        """Delete the selected block"""
        if self.canvas.selected_block:
            self.canvas.remove_script_block(self.canvas.selected_block)
            self.update_properties_panel(None)
    
    def clear_script(self):
        """Clear the entire script"""
        reply = QMessageBox.question(
            self, "Clear Script", 
            "Are you sure you want to clear the entire script?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.clear_canvas()
            self.update_properties_panel(None)
    
    def get_script_data(self) -> Dict[str, Any]:
        """Get the current script data"""
        return self.canvas.get_script_data()
    
    def load_script_data(self, script_data: Dict[str, Any]):
        """Load script data"""
        self.current_script_data = script_data
        self.canvas.load_script_data(script_data)
    
    def generate_python_code(self) -> str:
        """Generate Python code from the visual script"""
        # This would implement the code generation logic
        # For now, return a placeholder
        code_lines = ["# Generated Python code from visual script", ""]

        # Add imports
        code_lines.append("# Imports")
        code_lines.append("from core.game_engine import *")
        code_lines.append("")

        # Generate code for each block
        for block_widget in self.canvas.script_blocks:
            block = block_widget.script_block
            code_lines.append(f"# {block.name} - {block.description}")

            # Use the block's code template
            if block.code_template:
                # In a full implementation, this would substitute actual values
                code_lines.append(block.code_template)
            else:
                code_lines.append("pass")

            code_lines.append("")

        return "\n".join(code_lines)
