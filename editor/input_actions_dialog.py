"""
Input Actions Dialog for Lupine Engine
Allows configuration of input actions and key mappings
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox, QListWidget,
    QListWidgetItem, QMessageBox, QSplitter, QWidget, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QFont

from core.input_manager import InputManager, InputAction, InputEvent
from core.input_constants import *
from core.project import LupineProject

class KeyCaptureWidget(QWidget):
    """Widget for capturing key input"""
    
    key_captured = pyqtSignal(int, list)  # key_code, modifiers
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.capturing = False
        
        layout = QVBoxLayout()
        self.label = QLabel("Click to capture key...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("border: 1px solid gray; padding: 10px; background: #f0f0f0;")
        layout.addWidget(self.label)
        self.setLayout(layout)
    
    def start_capture(self):
        """Start capturing key input"""
        self.capturing = True
        self.label.setText("Press a key...")
        self.label.setStyleSheet("border: 2px solid blue; padding: 10px; background: #e0e0ff;")
        self.setFocus()
    
    def stop_capture(self):
        """Stop capturing key input"""
        self.capturing = False
        self.label.setText("Click to capture key...")
        self.label.setStyleSheet("border: 1px solid gray; padding: 10px; background: #f0f0f0;")
    
    def mousePressEvent(self, event):
        """Handle mouse press to start capture"""
        if not self.capturing:
            self.start_capture()
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press during capture"""
        if self.capturing:
            key_code = event.key()
            modifiers = []
            
            # Check for modifier keys
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                modifiers.append("shift")
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                modifiers.append("ctrl")
            if event.modifiers() & Qt.KeyboardModifier.AltModifier:
                modifiers.append("alt")
            if event.modifiers() & Qt.KeyboardModifier.MetaModifier:
                modifiers.append("meta")
            
            # Convert Qt key to arcade key
            arcade_key = self._qt_to_arcade_key(key_code)
            if arcade_key != -1:
                self.key_captured.emit(arcade_key, modifiers)
                self.stop_capture()
                
                # Update label with captured key
                key_name = get_key_name(arcade_key)
                if modifiers:
                    modifier_text = "+".join(mod.title() for mod in modifiers)
                    self.label.setText(f"{modifier_text}+{key_name}")
                else:
                    self.label.setText(key_name)
        
        super().keyPressEvent(event)
    
    def _qt_to_arcade_key(self, qt_key):
        """Convert Qt key code to arcade key code"""
        # This is a simplified mapping - you might need to expand this
        qt_to_arcade = {
            Qt.Key.Key_A: KEY_A, Qt.Key.Key_B: KEY_B, Qt.Key.Key_C: KEY_C, Qt.Key.Key_D: KEY_D,
            Qt.Key.Key_E: KEY_E, Qt.Key.Key_F: KEY_F, Qt.Key.Key_G: KEY_G, Qt.Key.Key_H: KEY_H,
            Qt.Key.Key_I: KEY_I, Qt.Key.Key_J: KEY_J, Qt.Key.Key_K: KEY_K, Qt.Key.Key_L: KEY_L,
            Qt.Key.Key_M: KEY_M, Qt.Key.Key_N: KEY_N, Qt.Key.Key_O: KEY_O, Qt.Key.Key_P: KEY_P,
            Qt.Key.Key_Q: KEY_Q, Qt.Key.Key_R: KEY_R, Qt.Key.Key_S: KEY_S, Qt.Key.Key_T: KEY_T,
            Qt.Key.Key_U: KEY_U, Qt.Key.Key_V: KEY_V, Qt.Key.Key_W: KEY_W, Qt.Key.Key_X: KEY_X,
            Qt.Key.Key_Y: KEY_Y, Qt.Key.Key_Z: KEY_Z,
            
            Qt.Key.Key_0: KEY_0, Qt.Key.Key_1: KEY_1, Qt.Key.Key_2: KEY_2, Qt.Key.Key_3: KEY_3,
            Qt.Key.Key_4: KEY_4, Qt.Key.Key_5: KEY_5, Qt.Key.Key_6: KEY_6, Qt.Key.Key_7: KEY_7,
            Qt.Key.Key_8: KEY_8, Qt.Key.Key_9: KEY_9,
            
            Qt.Key.Key_Space: KEY_SPACE, Qt.Key.Key_Enter: KEY_ENTER, Qt.Key.Key_Return: KEY_ENTER,
            Qt.Key.Key_Escape: KEY_ESCAPE, Qt.Key.Key_Tab: KEY_TAB, Qt.Key.Key_Backspace: KEY_BACKSPACE,
            Qt.Key.Key_Delete: KEY_DELETE, Qt.Key.Key_Insert: KEY_INSERT,
            
            Qt.Key.Key_Left: KEY_LEFT, Qt.Key.Key_Right: KEY_RIGHT,
            Qt.Key.Key_Up: KEY_UP, Qt.Key.Key_Down: KEY_DOWN,
            
            Qt.Key.Key_F1: KEY_F1, Qt.Key.Key_F2: KEY_F2, Qt.Key.Key_F3: KEY_F3, Qt.Key.Key_F4: KEY_F4,
            Qt.Key.Key_F5: KEY_F5, Qt.Key.Key_F6: KEY_F6, Qt.Key.Key_F7: KEY_F7, Qt.Key.Key_F8: KEY_F8,
            Qt.Key.Key_F9: KEY_F9, Qt.Key.Key_F10: KEY_F10, Qt.Key.Key_F11: KEY_F11, Qt.Key.Key_F12: KEY_F12,
        }
        
        return qt_to_arcade.get(qt_key, -1)

class InputActionsDialog(QDialog):
    """Dialog for configuring input actions"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.input_manager = InputManager(project.project_path if project else None)
        self.current_action = None
        
        self.setWindowTitle("Input Actions")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_actions()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Actions list
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # Actions list
        actions_label = QLabel("Input Actions:")
        actions_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        left_layout.addWidget(actions_label)
        
        self.actions_tree = QTreeWidget()
        self.actions_tree.setHeaderLabels(["Action", "Keys"])
        self.actions_tree.itemSelectionChanged.connect(self.on_action_selected)
        left_layout.addWidget(self.actions_tree)
        
        # Action buttons
        action_buttons_layout = QHBoxLayout()
        self.add_action_btn = QPushButton("Add Action")
        self.add_action_btn.clicked.connect(self.add_action)
        self.remove_action_btn = QPushButton("Remove Action")
        self.remove_action_btn.clicked.connect(self.remove_action)
        self.remove_action_btn.setEnabled(False)
        
        action_buttons_layout.addWidget(self.add_action_btn)
        action_buttons_layout.addWidget(self.remove_action_btn)
        left_layout.addLayout(action_buttons_layout)
        
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Right side - Action details
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # Action name
        name_group = QGroupBox("Action Name")
        name_layout = QVBoxLayout()
        self.action_name_edit = QLineEdit()
        self.action_name_edit.textChanged.connect(self.on_action_name_changed)
        name_layout.addWidget(self.action_name_edit)
        name_group.setLayout(name_layout)
        right_layout.addWidget(name_group)
        
        # Key bindings
        bindings_group = QGroupBox("Key Bindings")
        bindings_layout = QVBoxLayout()
        
        self.bindings_list = QListWidget()
        bindings_layout.addWidget(self.bindings_list)
        
        # Binding buttons
        binding_buttons_layout = QHBoxLayout()
        self.add_binding_btn = QPushButton("Add Key")
        self.add_binding_btn.clicked.connect(self.add_key_binding)
        self.remove_binding_btn = QPushButton("Remove Key")
        self.remove_binding_btn.clicked.connect(self.remove_key_binding)
        
        binding_buttons_layout.addWidget(self.add_binding_btn)
        binding_buttons_layout.addWidget(self.remove_binding_btn)
        bindings_layout.addLayout(binding_buttons_layout)
        
        bindings_group.setLayout(bindings_layout)
        right_layout.addWidget(bindings_group)
        
        # Key capture widget
        capture_group = QGroupBox("Capture New Key")
        capture_layout = QVBoxLayout()
        self.key_capture = KeyCaptureWidget()
        self.key_capture.key_captured.connect(self.on_key_captured)
        capture_layout.addWidget(self.key_capture)
        capture_group.setLayout(capture_layout)
        right_layout.addWidget(capture_group)
        
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
        
        # Dialog buttons
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_actions)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_actions(self):
        """Load actions into the tree widget"""
        self.actions_tree.clear()
        
        for action_name, action in self.input_manager.get_all_actions().items():
            item = QTreeWidgetItem([action_name, self.get_action_keys_text(action)])
            item.setData(0, Qt.ItemDataRole.UserRole, action_name)
            self.actions_tree.addTopLevelItem(item)
    
    def get_action_keys_text(self, action: InputAction) -> str:
        """Get text representation of action keys"""
        if not action.events:
            return "No keys assigned"
        
        key_texts = []
        for event in action.events:
            if event.type == "key":
                key_name = get_key_name(event.code)
                if event.modifiers:
                    modifier_text = "+".join(mod.title() for mod in event.modifiers)
                    key_texts.append(f"{modifier_text}+{key_name}")
                else:
                    key_texts.append(key_name)
            elif event.type == "mouse":
                key_texts.append(get_key_name(event.code))
        
        return ", ".join(key_texts)
    
    def on_action_selected(self):
        """Handle action selection"""
        selected_items = self.actions_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            action_name = item.data(0, Qt.ItemDataRole.UserRole)
            self.current_action = self.input_manager.get_action(action_name)
            self.load_action_details()
            self.remove_action_btn.setEnabled(True)
        else:
            self.current_action = None
            self.clear_action_details()
            self.remove_action_btn.setEnabled(False)
    
    def load_action_details(self):
        """Load details of the selected action"""
        if not self.current_action:
            return
        
        self.action_name_edit.setText(self.current_action.name)
        
        # Load key bindings
        self.bindings_list.clear()
        for event in self.current_action.events:
            if event.type == "key":
                key_name = get_key_name(event.code)
                if event.modifiers:
                    modifier_text = "+".join(mod.title() for mod in event.modifiers)
                    text = f"{modifier_text}+{key_name}"
                else:
                    text = key_name
            elif event.type == "mouse":
                text = get_key_name(event.code)
            else:
                text = f"Unknown: {event.code}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, event)
            self.bindings_list.addItem(item)
    
    def clear_action_details(self):
        """Clear action details"""
        self.action_name_edit.clear()
        self.bindings_list.clear()
    
    def add_action(self):
        """Add a new action"""
        action_name = f"new_action_{len(self.input_manager.get_all_actions())}"
        new_action = InputAction(action_name, [])
        self.input_manager.add_action(new_action)
        self.load_actions()
        
        # Select the new action
        for i in range(self.actions_tree.topLevelItemCount()):
            item = self.actions_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == action_name:
                self.actions_tree.setCurrentItem(item)
                break
    
    def remove_action(self):
        """Remove the selected action"""
        if not self.current_action:
            return
        
        reply = QMessageBox.question(
            self, "Remove Action",
            f"Are you sure you want to remove the action '{self.current_action.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.input_manager.remove_action(self.current_action.name)
            self.load_actions()
    
    def on_action_name_changed(self):
        """Handle action name change"""
        if not self.current_action:
            return
        
        new_name = self.action_name_edit.text().strip()
        if new_name and new_name != self.current_action.name:
            # Check if name already exists
            if new_name in self.input_manager.get_all_actions():
                QMessageBox.warning(self, "Duplicate Name", f"Action '{new_name}' already exists.")
                self.action_name_edit.setText(self.current_action.name)
                return
            
            # Update action name
            old_name = self.current_action.name
            self.input_manager.remove_action(old_name)
            self.current_action.name = new_name
            self.input_manager.add_action(self.current_action)
            self.load_actions()
            
            # Reselect the renamed action
            for i in range(self.actions_tree.topLevelItemCount()):
                item = self.actions_tree.topLevelItem(i)
                if item.data(0, Qt.ItemDataRole.UserRole) == new_name:
                    self.actions_tree.setCurrentItem(item)
                    break
    
    def add_key_binding(self):
        """Add a key binding to the current action"""
        if not self.current_action:
            return
        
        self.key_capture.start_capture()
    
    def remove_key_binding(self):
        """Remove the selected key binding"""
        if not self.current_action:
            return
        
        current_item = self.bindings_list.currentItem()
        if current_item:
            event = current_item.data(Qt.ItemDataRole.UserRole)
            self.current_action.events.remove(event)
            self.load_action_details()
            self.update_action_in_tree()
    
    def on_key_captured(self, key_code, modifiers):
        """Handle captured key"""
        if not self.current_action:
            return
        
        # Create new input event
        new_event = InputEvent("key", key_code, modifiers)
        
        # Check if this key combination already exists
        for event in self.current_action.events:
            if (event.type == new_event.type and 
                event.code == new_event.code and 
                event.modifiers == new_event.modifiers):
                QMessageBox.information(self, "Duplicate Key", "This key combination is already assigned to this action.")
                return
        
        # Add the new event
        self.current_action.events.append(new_event)
        self.load_action_details()
        self.update_action_in_tree()
    
    def update_action_in_tree(self):
        """Update the action display in the tree"""
        if not self.current_action:
            return
        
        for i in range(self.actions_tree.topLevelItemCount()):
            item = self.actions_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == self.current_action.name:
                item.setText(1, self.get_action_keys_text(self.current_action))
                break
    
    def save_actions(self):
        """Save actions and close dialog"""
        self.input_manager.save_actions()
        QMessageBox.information(self, "Saved", "Input actions have been saved.")
        self.accept()
