"""
Script Attachment Dialog for Lupine Engine
Allows attaching scripts to nodes and creating new scripts
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QTextEdit,
    QGroupBox, QRadioButton, QButtonGroup, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.project import LupineProject


class ScriptAttachmentDialog(QDialog):
    """Dialog for attaching scripts to nodes"""
    
    def __init__(self, project: LupineProject, node_data: dict, parent=None):
        super().__init__(parent)
        self.project = project
        self.node_data = node_data
        self.script_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Attach Script")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel(f"Attach Script to '{self.node_data.get('name', 'Node')}'")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #e0e0e0; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Script type selection
        type_group = QGroupBox("Script Type")
        type_layout = QHBoxLayout(type_group)

        self.type_button_group = QButtonGroup()

        self.python_radio = QRadioButton("Python Script")
        self.python_radio.setChecked(True)
        self.python_radio.toggled.connect(self.on_script_type_changed)
        self.type_button_group.addButton(self.python_radio)
        type_layout.addWidget(self.python_radio)

        self.visual_radio = QRadioButton("Visual Script")
        self.visual_radio.toggled.connect(self.on_script_type_changed)
        self.type_button_group.addButton(self.visual_radio)
        type_layout.addWidget(self.visual_radio)

        main_layout.addWidget(type_group)

        # Script source selection
        source_group = QGroupBox("Script Source")
        source_layout = QVBoxLayout(source_group)
        
        self.source_button_group = QButtonGroup()
        
        # Create new script option
        self.new_script_radio = QRadioButton("Create new script")
        self.new_script_radio.setChecked(True)
        self.new_script_radio.toggled.connect(self.on_source_changed)
        self.source_button_group.addButton(self.new_script_radio)
        source_layout.addWidget(self.new_script_radio)
        
        # Attach existing script option
        self.existing_script_radio = QRadioButton("Attach existing script")
        self.existing_script_radio.toggled.connect(self.on_source_changed)
        self.source_button_group.addButton(self.existing_script_radio)
        source_layout.addWidget(self.existing_script_radio)
        
        main_layout.addWidget(source_group)
        
        # New script options
        self.new_script_group = QGroupBox("New Script Options")
        new_script_layout = QFormLayout(self.new_script_group)
        
        # Script name
        self.script_name_edit = QLineEdit()
        node_name = self.node_data.get('name', 'Node').replace(' ', '')
        self.script_name_edit.setText(f"{node_name}.py")
        new_script_layout.addRow("Script Name:", self.script_name_edit)
        
        # Script template
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "Node2D Script",
            "Control Script", 
            "Area2D Script",
            "RigidBody2D Script",
            "Empty Script"
        ])
        
        # Select appropriate template based on node type
        node_type = self.node_data.get('type', 'Node')
        if 'Control' in node_type or 'UI' in node_type:
            self.template_combo.setCurrentText("Control Script")
        elif 'Area2D' in node_type:
            self.template_combo.setCurrentText("Area2D Script")
        elif 'RigidBody' in node_type:
            self.template_combo.setCurrentText("RigidBody2D Script")
        else:
            self.template_combo.setCurrentText("Node2D Script")
        
        new_script_layout.addRow("Template:", self.template_combo)
        
        main_layout.addWidget(self.new_script_group)
        
        # Existing script options
        self.existing_script_group = QGroupBox("Existing Script")
        existing_layout = QHBoxLayout(self.existing_script_group)
        
        self.script_path_edit = QLineEdit()
        self.script_path_edit.setPlaceholderText("Select script file...")
        self.script_path_edit.setReadOnly(True)
        existing_layout.addWidget(self.script_path_edit)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_script)
        existing_layout.addWidget(self.browse_btn)
        
        main_layout.addWidget(self.existing_script_group)
        
        # Script preview
        preview_group = QGroupBox("Script Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setFont(QFont("Consolas", 9))
        preview_layout.addWidget(self.preview_text)
        
        main_layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.attach_btn = QPushButton("Attach Script")
        self.attach_btn.setDefault(True)
        self.attach_btn.clicked.connect(self.attach_script)
        button_layout.addWidget(self.attach_btn)
        
        main_layout.addLayout(button_layout)
        
        # Initialize UI state
        self.on_source_changed()
        self.update_preview()
        
        # Connect signals
        self.template_combo.currentTextChanged.connect(self.update_preview)
        self.script_name_edit.textChanged.connect(self.update_preview)

    def on_script_type_changed(self):
        """Handle script type change"""
        is_python = self.python_radio.isChecked()

        # Update script name extension
        current_name = self.script_name_edit.text()
        if is_python:
            if current_name.endswith('.vscript'):
                current_name = current_name.replace('.vscript', '.py')
            elif not current_name.endswith('.py'):
                current_name = current_name.split('.')[0] + '.py'
        else:
            if current_name.endswith('.py'):
                current_name = current_name.replace('.py', '.vscript')
            elif not current_name.endswith('.vscript'):
                current_name = current_name.split('.')[0] + '.vscript'

        self.script_name_edit.setText(current_name)

        # Update template combo for visual scripts
        if is_python:
            self.template_combo.clear()
            self.template_combo.addItems([
                "Node2D Script",
                "Control Script",
                "Area2D Script",
                "RigidBody2D Script",
                "Empty Script"
            ])
        else:
            self.template_combo.clear()
            self.template_combo.addItems([
                "Basic Visual Script",
                "Event Handler Script",
                "Input Handler Script",
                "Timer Script"
            ])

        self.update_preview()
    
    def on_source_changed(self):
        """Handle script source selection change"""
        is_new_script = self.new_script_radio.isChecked()
        
        self.new_script_group.setEnabled(is_new_script)
        self.existing_script_group.setEnabled(not is_new_script)
        
        self.update_preview()
    
    def browse_script(self):
        """Browse for existing script file"""
        scripts_dir = self.project.get_absolute_path("scripts")

        if self.python_radio.isChecked():
            file_filter = "Python Scripts (*.py);;All Files (*)"
        else:
            file_filter = "Visual Scripts (*.vscript);;All Files (*)"

        script_file, _ = QFileDialog.getOpenFileName(
            self, "Select Script File", str(scripts_dir), file_filter
        )
        
        if script_file:
            relative_path = self.project.get_relative_path(script_file)
            self.script_path_edit.setText(relative_path)
            self.update_preview()
    
    def update_preview(self):
        """Update script preview"""
        if self.new_script_radio.isChecked():
            # Show template preview
            template = self.get_script_template()
            self.preview_text.setPlainText(template)
        else:
            # Show existing script preview
            script_path = self.script_path_edit.text()
            if script_path:
                try:
                    full_path = self.project.get_absolute_path(script_path)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Show first 10 lines
                    lines = content.split('\n')[:10]
                    preview = '\n'.join(lines)
                    if len(content.split('\n')) > 10:
                        preview += '\n...'
                    
                    self.preview_text.setPlainText(preview)
                except Exception as e:
                    self.preview_text.setPlainText(f"Error reading script: {e}")
            else:
                self.preview_text.setPlainText("No script selected")
    
    def get_script_template(self) -> str:
        """Get script template based on selection"""
        template_name = self.template_combo.currentText()
        node_type = self.node_data.get('type', 'Node')
        node_name = self.node_data.get('name', 'Node')

        # Handle visual script templates
        if self.visual_radio.isChecked():
            return self.get_visual_script_template(template_name, node_type, node_name)
        
        base_template = f'''# Python Script for {node_name}
# Node type: {node_type}

# Export variables (shown in inspector)
!example_property = 1.0

# Called when the node enters the scene tree
def _ready():
    print("{node_name} ready!")

# Called every frame
def _process(delta):
    pass
'''
        
        if template_name == "Control Script":
            return f'''# Python UI Script for {node_name}
# Node type: Control

# Export variables
!auto_focus = False

# Called when the node enters the scene tree
def _ready():
    if auto_focus:
        grab_focus()

# Called every frame
def _process(delta):
    pass

# UI event handlers
def _on_button_pressed():
    pass

def _on_focus_entered():
    pass

def _on_focus_exited():
    pass
'''
        
        elif template_name == "Area2D Script":
            return f'''# Python Area2D Script for {node_name}
# Node type: Area2D

# Export variables
!detection_enabled = True

# Called when the node enters the scene tree
def _ready():
    connect("body_entered", self, "_on_body_entered")
    connect("body_exited", self, "_on_body_exited")

# Called every frame
def _process(delta):
    pass

# Area2D signals
def _on_body_entered(body):
    if detection_enabled:
        print("Body entered:", body.name)

def _on_body_exited(body):
    if detection_enabled:
        print("Body exited:", body.name)
'''
        
        elif template_name == "RigidBody2D Script":
            return f'''# Python RigidBody2D Script for {node_name}
# Node type: RigidBody2D

# Export variables
!movement_force = 500.0
!max_speed = 300.0

# Called when the node enters the scene tree
def _ready():
    pass

# Called every physics frame
def _physics_process(delta):
    # Handle physics-based movement
    pass

# Handle input
def _input(event):
    if event.type == "key":
        handle_movement_input(event)

def handle_movement_input(event):
    force = [0.0, 0.0]

    if is_action_pressed("move_left"):
        force[0] -= movement_force
    if is_action_pressed("move_right"):
        force[0] += movement_force

    apply_central_force(force)
'''
        
        elif template_name == "Empty Script":
            return f'''# Python Script for {node_name}
# Node type: {node_type}

def _ready():
    pass
'''
        
        return base_template

    def get_visual_script_template(self, template_name: str, node_type: str, node_name: str) -> str:
        """Get visual script template"""
        import json

        if template_name == "Basic Visual Script":
            return json.dumps({
                "version": "1.0",
                "name": f"{node_name} Visual Script",
                "description": f"Basic visual script for {node_name}",
                "blocks": [
                    {
                        "id": "start_1",
                        "position": [100, 100],
                        "node_name": "Start",
                        "block_definition": {
                            "id": "start_1",
                            "name": "Start",
                            "category": "Events",
                            "block_type": {"value": "event"},
                            "description": "Script entry point",
                            "inputs": [],
                            "outputs": [
                                {
                                    "name": "exec",
                                    "type": "exec",
                                    "description": "Execution output",
                                    "is_execution_pin": True
                                }
                            ],
                            "code_template": "# Start",
                            "color": "#4CAF50"
                        }
                    },
                    {
                        "id": "print_1",
                        "position": [300, 100],
                        "node_name": "Print Hello",
                        "block_definition": {
                            "id": "print_1",
                            "name": "Print",
                            "category": "Debug",
                            "block_type": {"value": "action"},
                            "description": "Print a message",
                            "inputs": [
                                {
                                    "name": "exec",
                                    "type": "exec",
                                    "default_value": None,
                                    "description": "Execution input",
                                    "is_execution_pin": True
                                },
                                {
                                    "name": "message",
                                    "type": "string",
                                    "default_value": f"Hello from {node_name}!",
                                    "description": "Message to print"
                                }
                            ],
                            "outputs": [
                                {
                                    "name": "exec",
                                    "type": "exec",
                                    "description": "Execution output",
                                    "is_execution_pin": True
                                }
                            ],
                            "code_template": "print({message})",
                            "color": "#2196F3"
                        }
                    }
                ],
                "connections": [
                    {
                        "id": "conn_1",
                        "from_block_id": "start_1",
                        "from_output": "exec",
                        "to_block_id": "print_1",
                        "to_input": "exec",
                        "connection_type": "exec",
                        "color": "#FFFFFF"
                    }
                ]
            }, indent=2)

        elif template_name == "Event Handler Script":
            return json.dumps({
                "version": "1.0",
                "name": f"{node_name} Event Handler",
                "description": f"Event handling script for {node_name}",
                "blocks": [
                    {
                        "id": "ready_1",
                        "position": [100, 100],
                        "node_name": "Ready Event",
                        "block_definition": {
                            "id": "ready_1",
                            "name": "Ready",
                            "category": "Events",
                            "block_type": {"value": "event"},
                            "description": "Called when node is ready",
                            "inputs": [],
                            "outputs": [
                                {
                                    "name": "exec",
                                    "type": "exec",
                                    "description": "Execution output",
                                    "is_execution_pin": True
                                }
                            ],
                            "code_template": "# Ready event",
                            "color": "#4CAF50"
                        }
                    }
                ]
            }, indent=2)

        # Default basic template
        return json.dumps({
            "version": "1.0",
            "name": f"{node_name} Visual Script",
            "description": f"Visual script for {node_name}",
            "blocks": [],
            "connections": []
        }, indent=2)
    
    def attach_script(self):
        """Attach the script to the node"""
        try:
            if self.new_script_radio.isChecked():
                # Create new script
                script_name = self.script_name_edit.text().strip()
                if not script_name:
                    QMessageBox.warning(self, "Invalid Input", "Please enter a script name!")
                    return
                
                # Add appropriate extension
                if self.python_radio.isChecked():
                    if not script_name.endswith('.py'):
                        script_name += '.py'
                else:
                    if not script_name.endswith('.vscript'):
                        script_name += '.vscript'
                
                # Create script file
                scripts_dir = self.project.get_absolute_path("scripts")
                scripts_dir.mkdir(parents=True, exist_ok=True)
                
                script_file = scripts_dir / script_name
                
                if script_file.exists():
                    reply = QMessageBox.question(
                        self, "File Exists",
                        f"Script '{script_name}' already exists. Overwrite?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                
                # Write script content
                template = self.get_script_template()
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(template)
                
                # Set relative path
                self.script_path = self.project.get_relative_path(str(script_file))
                
            else:
                # Use existing script
                script_path = self.script_path_edit.text().strip()
                if not script_path:
                    QMessageBox.warning(self, "Invalid Input", "Please select a script file!")
                    return
                
                # Verify script exists
                full_path = self.project.get_absolute_path(script_path)
                if not full_path.exists():
                    QMessageBox.warning(self, "File Not Found", "Selected script file does not exist!")
                    return
                
                self.script_path = script_path
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to attach script: {e}")
    
    def get_script_path(self) -> str:
        """Get the attached script path"""
        return self.script_path or ""
