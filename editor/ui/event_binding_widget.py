"""
Event Binding Widget for Lupine Engine Menu and HUD Builder
Provides UI for configuring event bindings and code snippets for UI elements
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QTextEdit, QCheckBox, QTabWidget, QFileDialog,
    QMessageBox, QDialog, QDialogButtonBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any, List, Optional
from pathlib import Path


class EventBinding:
    """Represents an event binding with code snippet"""
    
    def __init__(self, event_name: str, code_snippet: str = "", 
                 audio_file: str = "", enabled: bool = True):
        self.event_name = event_name
        self.code_snippet = code_snippet
        self.audio_file = audio_file
        self.enabled = enabled
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_name": self.event_name,
            "code_snippet": self.code_snippet,
            "audio_file": self.audio_file,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventBinding":
        """Create from dictionary"""
        return cls(
            event_name=data["event_name"],
            code_snippet=data.get("code_snippet", ""),
            audio_file=data.get("audio_file", ""),
            enabled=data.get("enabled", True)
        )


class EventConfigDialog(QDialog):
    """Dialog for configuring a single event binding"""
    
    def __init__(self, event_binding: EventBinding = None, available_events: List[str] = None):
        super().__init__()
        self.event_binding = event_binding
        self.available_events = available_events or []
        self.setup_ui()
        
        if event_binding:
            self.load_event_binding(event_binding)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Configure Event Binding")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Event selection
        event_layout = QHBoxLayout()
        event_layout.addWidget(QLabel("Event:"))
        
        self.event_combo = QComboBox()
        for event_name in self.available_events:
            self.event_combo.addItem(event_name)
        event_layout.addWidget(self.event_combo)
        
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)
        event_layout.addWidget(self.enabled_checkbox)
        
        layout.addLayout(event_layout)
        
        # Tabs for different configuration aspects
        tab_widget = QTabWidget()
        
        # Code tab
        code_tab = QWidget()
        code_layout = QVBoxLayout(code_tab)
        
        code_layout.addWidget(QLabel("Code Snippet:"))
        self.code_edit = QTextEdit()
        self.code_edit.setFont(QFont("Consolas", 10))
        self.code_edit.setPlaceholderText(
            "# Python code to execute when event occurs\n"
            "# Available variables:\n"
            "#   self - the UI node\n"
            "#   event - event data (if applicable)\n"
            "#   globals() - access to global variables\n\n"
            "print('Event triggered!')"
        )
        code_layout.addWidget(self.code_edit)
        
        # Code snippet templates
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Templates:"))
        
        template_combo = QComboBox()
        template_combo.addItem("Select Template...")
        template_combo.addItem("Print Message")
        template_combo.addItem("Change Scene")
        template_combo.addItem("Play Sound")
        template_combo.addItem("Update Variable")
        template_combo.addItem("Show/Hide Element")
        template_combo.addItem("Enable/Disable Element")
        template_combo.currentTextChanged.connect(self.apply_code_template)
        template_layout.addWidget(template_combo)
        
        code_layout.addLayout(template_layout)
        
        tab_widget.addTab(code_tab, "Code")
        
        # Audio tab
        audio_tab = QWidget()
        audio_layout = QVBoxLayout(audio_tab)
        
        audio_file_layout = QHBoxLayout()
        audio_layout.addWidget(QLabel("Audio File:"))
        
        self.audio_edit = QLineEdit()
        self.audio_edit.setPlaceholderText("Path to audio file (optional)")
        audio_file_layout.addWidget(self.audio_edit)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_audio_file)
        audio_file_layout.addWidget(browse_button)
        
        audio_layout.addLayout(audio_file_layout)
        
        # Audio preview/test
        test_audio_button = QPushButton("Test Audio")
        test_audio_button.clicked.connect(self.test_audio)
        audio_layout.addWidget(test_audio_button)
        
        audio_layout.addStretch()
        
        tab_widget.addTab(audio_tab, "Audio")
        
        layout.addWidget(tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def apply_code_template(self, template_name: str):
        """Apply a code template"""
        templates = {
            "Print Message": "print('Button clicked!')",
            "Change Scene": "# Change to a different scene\n# change_scene('scenes/main_menu.scene')",
            "Play Sound": "# Play a sound effect\n# play_sound('sounds/click.wav')",
            "Update Variable": "# Update a global variable\n# set_global_var('player_score', get_global_var('player_score') + 10)",
            "Show/Hide Element": "# Show or hide another UI element\n# element = find_node('ElementName')\n# element.visible = not element.visible",
            "Enable/Disable Element": "# Enable or disable another UI element\n# element = find_node('ButtonName')\n# element.disabled = not element.disabled"
        }
        
        template_code = templates.get(template_name)
        if template_code:
            current_text = self.code_edit.toPlainText()
            if current_text:
                self.code_edit.setPlainText(current_text + "\n\n" + template_code)
            else:
                self.code_edit.setPlainText(template_code)
    
    def browse_audio_file(self):
        """Browse for an audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", 
            "Audio Files (*.wav *.mp3 *.ogg *.m4a);;All Files (*)"
        )
        if file_path:
            self.audio_edit.setText(file_path)
    
    def test_audio(self):
        """Test the selected audio file"""
        audio_file = self.audio_edit.text()
        if not audio_file:
            QMessageBox.information(self, "No Audio", "Please select an audio file first.")
            return
        
        if not Path(audio_file).exists():
            QMessageBox.warning(self, "File Not Found", f"Audio file not found: {audio_file}")
            return
        
        # TODO: Implement audio preview
        QMessageBox.information(self, "Audio Test", f"Would play: {audio_file}")
    
    def load_event_binding(self, event_binding: EventBinding):
        """Load event binding data into the form"""
        self.event_combo.setCurrentText(event_binding.event_name)
        self.code_edit.setPlainText(event_binding.code_snippet)
        self.audio_edit.setText(event_binding.audio_file)
        self.enabled_checkbox.setChecked(event_binding.enabled)
    
    def get_event_binding(self) -> Optional[EventBinding]:
        """Get the configured event binding"""
        event_name = self.event_combo.currentText()
        if not event_name:
            return None
        
        return EventBinding(
            event_name=event_name,
            code_snippet=self.code_edit.toPlainText(),
            audio_file=self.audio_edit.text(),
            enabled=self.enabled_checkbox.isChecked()
        )


class EventBindingWidget(QWidget):
    """Widget for managing event bindings for a UI element"""
    
    bindings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_node = None
        self.event_bindings = []  # List of EventBinding objects
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Title
        title_label = QLabel("Event Bindings")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Events list
        self.events_list = QListWidget()
        self.events_list.itemDoubleClicked.connect(self.edit_event_binding)
        layout.addWidget(self.events_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_event_binding)
        button_layout.addWidget(add_button)
        
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_selected_event_binding)
        button_layout.addWidget(edit_button)
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_event_binding)
        button_layout.addWidget(remove_button)
        
        layout.addLayout(button_layout)
        
        # Quick actions
        quick_group = QGroupBox("Quick Actions")
        quick_layout = QVBoxLayout(quick_group)
        
        # Common event buttons
        common_layout = QHBoxLayout()
        
        click_button = QPushButton("Add Click")
        click_button.clicked.connect(lambda: self.add_quick_event("on_click"))
        common_layout.addWidget(click_button)
        
        hover_button = QPushButton("Add Hover")
        hover_button.clicked.connect(lambda: self.add_quick_event("on_hover"))
        common_layout.addWidget(hover_button)
        
        quick_layout.addLayout(common_layout)
        
        # Generate script button
        generate_button = QPushButton("Generate Script File")
        generate_button.clicked.connect(self.generate_script_file)
        quick_layout.addWidget(generate_button)
        
        layout.addWidget(quick_group)
    
    def set_node(self, node_data: Dict[str, Any]):
        """Set the current node and load its event bindings"""
        self.current_node = node_data
        self.load_event_bindings()
    
    def load_event_bindings(self):
        """Load event bindings for the current node"""
        self.event_bindings.clear()
        self.events_list.clear()
        
        if not self.current_node:
            return
        
        # Load event bindings from node data
        node_events = self.current_node.get("event_bindings", [])
        for event_data in node_events:
            event_binding = EventBinding.from_dict(event_data)
            self.event_bindings.append(event_binding)
            self.add_event_binding_to_list(event_binding)
    
    def add_event_binding_to_list(self, event_binding: EventBinding):
        """Add an event binding to the list widget"""
        status = "✓" if event_binding.enabled else "✗"
        audio_indicator = "♪" if event_binding.audio_file else ""
        item_text = f"{status} {event_binding.event_name} {audio_indicator}"
        
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, event_binding)
        
        # Color coding
        if not event_binding.enabled:
            item.setForeground(Qt.GlobalColor.gray)
        elif event_binding.audio_file:
            item.setForeground(Qt.GlobalColor.cyan)
        
        self.events_list.addItem(item)
    
    def get_available_events(self) -> List[str]:
        """Get list of available events for the current node type"""
        if not self.current_node:
            return []
        
        node_type = self.current_node.get("type", "")
        
        # Common events for all UI elements
        events = ["on_ready", "on_process", "on_physics_process"]
        
        # Type-specific events
        if node_type in ["Button", "InventorySlot"]:
            events.extend(["on_click", "on_hover", "on_release", "on_focus", "on_blur"])
        elif node_type in ["Label", "Panel"]:
            events.extend(["on_hover", "on_click"])
        elif node_type == "ProgressBar":
            events.extend(["on_value_changed", "on_progress_completed"])
        
        return events
    
    def add_event_binding(self):
        """Add a new event binding"""
        dialog = EventConfigDialog(available_events=self.get_available_events())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            event_binding = dialog.get_event_binding()
            if event_binding:
                self.event_bindings.append(event_binding)
                self.add_event_binding_to_list(event_binding)
                self.save_event_bindings()
                self.bindings_changed.emit()
    
    def add_quick_event(self, event_name: str):
        """Add a quick event binding with default code"""
        default_code = {
            "on_click": "print(f'{self.name} was clicked!')",
            "on_hover": "print(f'Hovering over {self.name}')"
        }
        
        event_binding = EventBinding(
            event_name=event_name,
            code_snippet=default_code.get(event_name, f"# {event_name} event"),
            enabled=True
        )
        
        self.event_bindings.append(event_binding)
        self.add_event_binding_to_list(event_binding)
        self.save_event_bindings()
        self.bindings_changed.emit()
    
    def edit_selected_event_binding(self):
        """Edit the selected event binding"""
        current_item = self.events_list.currentItem()
        if current_item:
            self.edit_event_binding(current_item)
    
    def edit_event_binding(self, item: QListWidgetItem):
        """Edit an event binding"""
        event_binding = item.data(Qt.ItemDataRole.UserRole)
        if not event_binding:
            return
        
        dialog = EventConfigDialog(event_binding, self.get_available_events())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_event_binding = dialog.get_event_binding()
            if new_event_binding:
                # Update the binding in the list
                index = self.event_bindings.index(event_binding)
                self.event_bindings[index] = new_event_binding
                item.setData(Qt.ItemDataRole.UserRole, new_event_binding)
                
                # Update item text
                status = "✓" if new_event_binding.enabled else "✗"
                audio_indicator = "♪" if new_event_binding.audio_file else ""
                item.setText(f"{status} {new_event_binding.event_name} {audio_indicator}")
                
                self.save_event_bindings()
                self.bindings_changed.emit()
    
    def remove_event_binding(self):
        """Remove the selected event binding"""
        current_item = self.events_list.currentItem()
        if not current_item:
            return
        
        event_binding = current_item.data(Qt.ItemDataRole.UserRole)
        if event_binding in self.event_bindings:
            self.event_bindings.remove(event_binding)
        
        self.events_list.takeItem(self.events_list.row(current_item))
        self.save_event_bindings()
        self.bindings_changed.emit()
    
    def save_event_bindings(self):
        """Save event bindings to the current node"""
        if not self.current_node:
            return
        
        # Convert event bindings to dict format
        event_data = [binding.to_dict() for binding in self.event_bindings]
        self.current_node["event_bindings"] = event_data
    
    def generate_script_file(self):
        """Generate a Python script file from the event bindings"""
        if not self.current_node or not self.event_bindings:
            QMessageBox.information(self, "No Events", "No event bindings to generate script from.")
            return
        
        node_name = self.current_node.get("name", "UIElement")
        script_content = self._generate_script_content(node_name)
        
        # Show the generated script in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Generated Script")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        script_edit = QTextEdit()
        script_edit.setFont(QFont("Consolas", 10))
        script_edit.setPlainText(script_content)
        layout.addWidget(script_edit)
        
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save to File")
        save_button.clicked.connect(lambda: self._save_script_to_file(script_content, node_name))
        button_layout.addWidget(save_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _generate_script_content(self, node_name: str) -> str:
        """Generate the script content from event bindings"""
        script_lines = [
            f'"""',
            f'Generated script for {node_name}',
            f'Auto-generated by Lupine Engine Menu and HUD Builder',
            f'"""',
            f'',
            f'from nodes.ui.{self.current_node.get("type", "Control")} import {self.current_node.get("type", "Control")}',
            f'',
            f'',
            f'class {node_name}Script({self.current_node.get("type", "Control")}):',
            f'    """Custom script for {node_name}"""',
            f'    ',
            f'    def __init__(self, name: str = "{node_name}"):',
            f'        super().__init__(name)',
            f'    '
        ]
        
        # Add event methods
        for event_binding in self.event_bindings:
            if event_binding.enabled and event_binding.code_snippet:
                script_lines.extend([
                    f'    def {event_binding.event_name}(self, *args):',
                    f'        """Event handler for {event_binding.event_name}"""'
                ])
                
                # Add audio playback if specified
                if event_binding.audio_file:
                    script_lines.append(f'        # Play audio: {event_binding.audio_file}')
                    script_lines.append(f'        # play_sound("{event_binding.audio_file}")')
                
                # Add the code snippet (indented)
                code_lines = event_binding.code_snippet.split('\n')
                for line in code_lines:
                    script_lines.append(f'        {line}')
                
                script_lines.append('')
        
        return '\n'.join(script_lines)
    
    def _save_script_to_file(self, script_content: str, node_name: str):
        """Save the generated script to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Script File", f"{node_name}_script.py",
            "Python Files (*.py);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                QMessageBox.information(self, "Script Saved", f"Script saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save script: {e}")
