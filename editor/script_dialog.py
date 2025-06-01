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
        self.script_name_edit.setText(f"{node_name}.lsc")
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
    
    def on_source_changed(self):
        """Handle script source selection change"""
        is_new_script = self.new_script_radio.isChecked()
        
        self.new_script_group.setEnabled(is_new_script)
        self.existing_script_group.setEnabled(not is_new_script)
        
        self.update_preview()
    
    def browse_script(self):
        """Browse for existing script file"""
        scripts_dir = self.project.get_absolute_path("scripts")
        script_file, _ = QFileDialog.getOpenFileName(
            self, "Select Script File", str(scripts_dir), "LSC Scripts (*.lsc);;All Files (*)"
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
        
        base_template = f'''# LSC Script for {node_name}
extends {node_type}

# Export variables (shown in inspector)
export var example_property: float = 1.0

# Called when the node enters the scene tree
func _ready():
    print("{node_name} ready!")

# Called every frame
func _process(delta: float):
    pass
'''
        
        if template_name == "Control Script":
            return f'''# LSC UI Script for {node_name}
extends Control

# Export variables
export var auto_focus: bool = false

# Called when the node enters the scene tree
func _ready():
    if auto_focus:
        grab_focus()

# Called every frame
func _process(delta: float):
    pass

# UI event handlers
func _on_button_pressed():
    pass

func _on_focus_entered():
    pass

func _on_focus_exited():
    pass
'''
        
        elif template_name == "Area2D Script":
            return f'''# LSC Area2D Script for {node_name}
extends Area2D

# Export variables
export var detection_enabled: bool = true

# Called when the node enters the scene tree
func _ready():
    connect("body_entered", self, "_on_body_entered")
    connect("body_exited", self, "_on_body_exited")

# Called every frame
func _process(delta: float):
    pass

# Area2D signals
func _on_body_entered(body):
    if detection_enabled:
        print("Body entered:", body.name)

func _on_body_exited(body):
    if detection_enabled:
        print("Body exited:", body.name)
'''
        
        elif template_name == "RigidBody2D Script":
            return f'''# LSC RigidBody2D Script for {node_name}
extends RigidBody2D

# Export variables
export var movement_force: float = 500.0
export var max_speed: float = 300.0

# Called when the node enters the scene tree
func _ready():
    pass

# Called every physics frame
func _physics_process(delta: float):
    # Handle physics-based movement
    pass

# Handle input
func _input(event):
    if event is InputEventKey:
        handle_movement_input(event)

func handle_movement_input(event):
    var force = Vector2.ZERO
    
    if Input.is_action_pressed("move_left"):
        force.x -= movement_force
    if Input.is_action_pressed("move_right"):
        force.x += movement_force
    
    apply_central_force(force)
'''
        
        elif template_name == "Empty Script":
            return f'''# LSC Script for {node_name}
extends {node_type}

func _ready():
    pass
'''
        
        return base_template
    
    def attach_script(self):
        """Attach the script to the node"""
        try:
            if self.new_script_radio.isChecked():
                # Create new script
                script_name = self.script_name_edit.text().strip()
                if not script_name:
                    QMessageBox.warning(self, "Invalid Input", "Please enter a script name!")
                    return
                
                if not script_name.endswith('.lsc'):
                    script_name += '.lsc'
                
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
