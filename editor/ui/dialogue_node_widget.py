"""
Dialogue Node Widget
Visual representation of dialogue nodes for the node graph editor
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QComboBox, QFrame, QSizePolicy,
    QMenu, QDialog, QDialogButtonBox, QFormLayout, QSpinBox,
    QCheckBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics,
    QMouseEvent, QPaintEvent, QContextMenuEvent
)
from typing import Dict, List, Any, Optional, Tuple

from core.dialogue.dialogue_parser import DialogueNode, NodeType, DialogueChoice


class DialogueNodeWidget(QFrame):
    """Visual widget representing a dialogue node"""
    
    # Signals
    node_selected = pyqtSignal(str)  # node_id
    node_moved = pyqtSignal(str, QPoint)  # node_id, new_position
    node_edited = pyqtSignal(str, dict)  # node_id, node_data
    connection_requested = pyqtSignal(str, str)  # from_node_id, to_node_id
    
    def __init__(self, node: DialogueNode, position: QPoint = None):
        super().__init__()
        self.node = node
        self.position = position or QPoint(0, 0)
        self.is_selected = False
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        
        # Visual properties
        self.min_width = 150
        self.min_height = 80
        self.padding = 8
        self.header_height = 25
        
        # Connection points
        self.input_point = QPoint()
        self.output_points: List[QPoint] = []
        
        self.setup_ui()
        self.update_appearance()
    
    def setup_ui(self):
        """Setup the widget UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumSize(self.min_width, self.min_height)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Calculate size based on content
        self.calculate_size()
    
    def calculate_size(self):
        """Calculate widget size based on content"""
        font_metrics = QFontMetrics(self.font())
        
        # Calculate width based on content
        width = self.min_width
        
        # Node ID width
        id_width = font_metrics.horizontalAdvance(self.node.node_id) + self.padding * 2
        width = max(width, id_width)
        
        # Speaker width
        if self.node.speaker:
            speaker_width = font_metrics.horizontalAdvance(f"Speaker: {self.node.speaker}") + self.padding * 2
            width = max(width, speaker_width)
        
        # Dialogue lines width
        for line in self.node.dialogue_lines:
            line_width = font_metrics.horizontalAdvance(line[:30] + "...") + self.padding * 2
            width = max(width, line_width)
        
        # Calculate height based on content
        height = self.header_height + self.padding
        
        # Speaker line
        if self.node.speaker:
            height += font_metrics.height()
        
        # Dialogue lines (max 3 shown)
        dialogue_lines = min(len(self.node.dialogue_lines), 3)
        height += dialogue_lines * font_metrics.height()
        
        # Choices (max 3 shown)
        choice_lines = min(len(self.node.choices), 3)
        height += choice_lines * font_metrics.height()
        
        # Commands indicator
        if self.node.commands:
            height += font_metrics.height()
        
        height += self.padding
        height = max(height, self.min_height)
        
        self.setFixedSize(int(width), int(height))
        self.update_connection_points()
    
    def update_connection_points(self):
        """Update connection point positions"""
        # Input point (top center)
        self.input_point = QPoint(self.width() // 2, 0)
        
        # Output points
        self.output_points.clear()
        
        if self.node.node_type == NodeType.CHOICE:
            # Multiple output points for choices
            choice_count = len(self.node.choices)
            if choice_count > 0:
                spacing = self.width() // (choice_count + 1)
                for i in range(choice_count):
                    x = spacing * (i + 1)
                    self.output_points.append(QPoint(x, self.height()))
        else:
            # Single output point (bottom center)
            self.output_points.append(QPoint(self.width() // 2, self.height()))
    
    def update_appearance(self):
        """Update widget appearance based on node type and state"""
        # Set colors based on node type
        if self.node.node_type == NodeType.DIALOGUE:
            bg_color = QColor(70, 130, 180) if not self.is_selected else QColor(100, 160, 210)
        elif self.node.node_type == NodeType.CHOICE:
            bg_color = QColor(60, 180, 75) if not self.is_selected else QColor(90, 210, 105)
        elif self.node.node_type == NodeType.END:
            bg_color = QColor(180, 60, 60) if not self.is_selected else QColor(210, 90, 90)
        else:
            bg_color = QColor(128, 128, 128) if not self.is_selected else QColor(158, 158, 158)
        
        # Apply stylesheet
        border_color = "white" if self.is_selected else "gray"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()});
                border: 2px solid {border_color};
                border-radius: 5px;
                color: white;
            }}
        """)
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint event to draw node content"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set font
        font = self.font()
        painter.setFont(font)
        font_metrics = QFontMetrics(font)
        
        # Draw header (node ID)
        header_rect = QRect(0, 0, self.width(), self.header_height)
        painter.fillRect(header_rect, QBrush(QColor(0, 0, 0, 50)))
        
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        header_font = QFont(font)
        header_font.setBold(True)
        painter.setFont(header_font)
        
        node_text = self.node.node_id
        if self.node.condition:
            node_text += " (conditional)"
        
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, node_text)
        
        # Draw content
        painter.setFont(font)
        y = self.header_height + self.padding
        
        # Speaker
        if self.node.speaker:
            painter.setPen(QPen(QColor(255, 255, 100), 1))
            painter.drawText(self.padding, y, f"Speaker: {self.node.speaker}")
            y += font_metrics.height()
        
        # Dialogue lines
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        for i, line in enumerate(self.node.dialogue_lines[:3]):
            display_line = line[:30] + "..." if len(line) > 30 else line
            painter.drawText(self.padding, y, display_line)
            y += font_metrics.height()
        
        if len(self.node.dialogue_lines) > 3:
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawText(self.padding, y, f"... +{len(self.node.dialogue_lines) - 3} more")
            y += font_metrics.height()
        
        # Choices
        if self.node.choices:
            painter.setPen(QPen(QColor(150, 255, 150), 1))
            for i, choice in enumerate(self.node.choices[:3]):
                choice_text = f"• {choice.text[:25]}..." if len(choice.text) > 25 else f"• {choice.text}"
                painter.drawText(self.padding, y, choice_text)
                y += font_metrics.height()
            
            if len(self.node.choices) > 3:
                painter.setPen(QPen(QColor(200, 200, 200), 1))
                painter.drawText(self.padding, y, f"... +{len(self.node.choices) - 3} more")
                y += font_metrics.height()
        
        # Commands indicator
        if self.node.commands:
            painter.setPen(QPen(QColor(255, 150, 100), 1))
            painter.drawText(self.padding, y, f"Commands: {len(self.node.commands)}")
        
        # Draw connection points
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        
        # Input point
        painter.drawEllipse(self.input_point.x() - 3, self.input_point.y() - 3, 6, 6)
        
        # Output points
        for point in self.output_points:
            painter.drawEllipse(point.x() - 3, point.y() - 3, 6, 6)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.pos()
            self.node_selected.emit(self.node.node_id)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            # Calculate new position
            delta = event.pos() - self.drag_start_pos
            new_pos = self.position + delta
            
            # Emit move signal
            self.node_moved.emit(self.node.node_id, new_pos)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
        
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click to edit node"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_node()
        
        super().mouseDoubleClickEvent(event)
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        """Handle context menu"""
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit Node")
        edit_action.triggered.connect(self.edit_node)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete Node")
        delete_action.triggered.connect(lambda: self.node_edited.emit(self.node.node_id, None))
        
        menu.exec(event.globalPos())
    
    def edit_node(self):
        """Open node edit dialog"""
        dialog = NodeEditDialog(self.node, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_node = dialog.get_node_data()
            self.node = updated_node
            self.calculate_size()
            self.update_appearance()
            self.update()
            
            # Emit edit signal
            self.node_edited.emit(self.node.node_id, self.node_to_dict())
    
    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        self.update_appearance()
    
    def set_position(self, position: QPoint):
        """Set widget position"""
        self.position = position
        self.move(position)
    
    def get_connection_point(self, is_input: bool, index: int = 0) -> QPoint:
        """Get connection point in global coordinates"""
        if is_input:
            local_point = self.input_point
        else:
            if index < len(self.output_points):
                local_point = self.output_points[index]
            else:
                local_point = self.output_points[0] if self.output_points else QPoint(self.width() // 2, self.height())
        
        return self.mapToParent(local_point)
    
    def node_to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        return {
            'node_id': self.node.node_id,
            'node_type': self.node.node_type.value,
            'speaker': self.node.speaker,
            'dialogue_lines': self.node.dialogue_lines,
            'choices': [{'text': c.text, 'target_node': c.target_node, 'condition': c.condition} for c in self.node.choices],
            'commands': self.node.commands,
            'connections': self.node.connections,
            'condition': self.node.condition,
            'position': {'x': self.position.x(), 'y': self.position.y()}
        }


class NodeEditDialog(QDialog):
    """Dialog for editing dialogue nodes"""
    
    def __init__(self, node: DialogueNode, parent=None):
        super().__init__(parent)
        self.node = node
        self.setup_ui()
        self.load_node_data()
    
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Edit Dialogue Node")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Node ID
        self.node_id_edit = QLineEdit()
        form_layout.addRow("Node ID:", self.node_id_edit)
        
        # Node Type
        self.node_type_combo = QComboBox()
        self.node_type_combo.addItems([t.value for t in NodeType])
        form_layout.addRow("Node Type:", self.node_type_combo)
        
        # Speaker
        self.speaker_edit = QLineEdit()
        form_layout.addRow("Speaker:", self.speaker_edit)
        
        # Condition
        self.condition_edit = QLineEdit()
        form_layout.addRow("Condition:", self.condition_edit)
        
        layout.addLayout(form_layout)
        
        # Dialogue lines
        layout.addWidget(QLabel("Dialogue Lines:"))
        self.dialogue_edit = QTextEdit()
        self.dialogue_edit.setMaximumHeight(100)
        layout.addWidget(self.dialogue_edit)
        
        # Commands
        layout.addWidget(QLabel("Commands:"))
        self.commands_edit = QTextEdit()
        self.commands_edit.setMaximumHeight(80)
        layout.addWidget(self.commands_edit)
        
        # Choices
        layout.addWidget(QLabel("Choices:"))
        self.choices_list = QListWidget()
        self.choices_list.setMaximumHeight(100)
        layout.addWidget(self.choices_list)
        
        # Choice buttons
        choice_buttons = QHBoxLayout()
        self.add_choice_btn = QPushButton("Add Choice")
        self.edit_choice_btn = QPushButton("Edit Choice")
        self.remove_choice_btn = QPushButton("Remove Choice")
        
        choice_buttons.addWidget(self.add_choice_btn)
        choice_buttons.addWidget(self.edit_choice_btn)
        choice_buttons.addWidget(self.remove_choice_btn)
        layout.addLayout(choice_buttons)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect signals
        self.add_choice_btn.clicked.connect(self.add_choice)
        self.edit_choice_btn.clicked.connect(self.edit_choice)
        self.remove_choice_btn.clicked.connect(self.remove_choice)
    
    def load_node_data(self):
        """Load node data into form"""
        self.node_id_edit.setText(self.node.node_id)
        self.node_type_combo.setCurrentText(self.node.node_type.value)
        self.speaker_edit.setText(self.node.speaker or "")
        self.condition_edit.setText(self.node.condition or "")
        self.dialogue_edit.setPlainText("\n".join(self.node.dialogue_lines))
        self.commands_edit.setPlainText("\n".join(self.node.commands))
        
        # Load choices
        for choice in self.node.choices:
            item_text = f"{choice.text} → {choice.target_node}"
            if choice.condition:
                item_text += f" (if {choice.condition})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, choice)
            self.choices_list.addItem(item)
    
    def add_choice(self):
        """Add a new choice"""
        choice = DialogueChoice("New Choice", "target_node")
        if self.edit_choice_dialog(choice):
            item_text = f"{choice.text} → {choice.target_node}"
            if choice.condition:
                item_text += f" (if {choice.condition})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, choice)
            self.choices_list.addItem(item)
    
    def edit_choice(self):
        """Edit selected choice"""
        current_item = self.choices_list.currentItem()
        if current_item:
            choice = current_item.data(Qt.ItemDataRole.UserRole)
            if self.edit_choice_dialog(choice):
                item_text = f"{choice.text} → {choice.target_node}"
                if choice.condition:
                    item_text += f" (if {choice.condition})"
                current_item.setText(item_text)
    
    def remove_choice(self):
        """Remove selected choice"""
        current_row = self.choices_list.currentRow()
        if current_row >= 0:
            self.choices_list.takeItem(current_row)
    
    def edit_choice_dialog(self, choice: DialogueChoice) -> bool:
        """Edit choice in a dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Choice")
        layout = QFormLayout(dialog)
        
        text_edit = QLineEdit(choice.text)
        target_edit = QLineEdit(choice.target_node)
        condition_edit = QLineEdit(choice.condition or "")
        
        layout.addRow("Choice Text:", text_edit)
        layout.addRow("Target Node:", target_edit)
        layout.addRow("Condition:", condition_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            choice.text = text_edit.text()
            choice.target_node = target_edit.text()
            choice.condition = condition_edit.text() or None
            return True
        
        return False
    
    def get_node_data(self) -> DialogueNode:
        """Get updated node data"""
        # Create new node with updated data
        node = DialogueNode(
            node_id=self.node_id_edit.text(),
            node_type=NodeType(self.node_type_combo.currentText()),
            speaker=self.speaker_edit.text() or None,
            condition=self.condition_edit.text() or None
        )
        
        # Set dialogue lines
        dialogue_text = self.dialogue_edit.toPlainText().strip()
        if dialogue_text:
            node.dialogue_lines = [line.strip() for line in dialogue_text.split('\n') if line.strip()]
        
        # Set commands
        commands_text = self.commands_edit.toPlainText().strip()
        if commands_text:
            node.commands = [line.strip() for line in commands_text.split('\n') if line.strip()]
        
        # Set choices
        for i in range(self.choices_list.count()):
            item = self.choices_list.item(i)
            choice = item.data(Qt.ItemDataRole.UserRole)
            node.choices.append(choice)
        
        return node
