"""
New Project Dialog for Lupine Engine
Handles new project creation with name, path, and description
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QFileDialog, QMessageBox,
    QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class NewProjectDialog(QDialog):
    """Dialog for creating new projects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.set_default_values()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("New Project")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.resize(600, 450)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Create New Project")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #e0e0e0; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Project details group
        details_group = QGroupBox("Project Details")
        details_layout = QFormLayout(details_group)
        details_layout.setSpacing(10)
        
        # Project name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name...")
        self.name_edit.textChanged.connect(self.on_name_changed)
        details_layout.addRow("Project Name:", self.name_edit)
        
        # Project path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select project location...")
        self.path_edit.setReadOnly(True)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setMaximumWidth(80)
        self.browse_btn.clicked.connect(self.browse_location)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        details_layout.addRow("Location:", path_layout)
        
        # Full project path (read-only)
        self.full_path_edit = QLineEdit()
        self.full_path_edit.setReadOnly(True)
        self.full_path_edit.setStyleSheet("background-color: #2d2d2d; color: #b0b0b0;")
        details_layout.addRow("Full Path:", self.full_path_edit)
        
        # Project description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter project description (optional)...")
        self.description_edit.setMaximumHeight(100)
        details_layout.addRow("Description:", self.description_edit)
        
        main_layout.addWidget(details_group)
        
        # Project settings group (placeholder for future features)
        settings_group = QGroupBox("Project Settings")
        settings_layout = QFormLayout(settings_group)
        
        # Template selection (placeholder)
        template_label = QLabel("Template: Default (2D Game)")
        template_label.setStyleSheet("color: #b0b0b0;")
        settings_layout.addRow("Template:", template_label)
        
        # Engine version
        version_label = QLabel("Engine Version: 1.0.0")
        version_label.setStyleSheet("color: #b0b0b0;")
        settings_layout.addRow("Engine:", version_label)
        
        main_layout.addWidget(settings_group)
        
        # Spacer
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(spacer)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(80)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.create_btn = QPushButton("Create Project")
        self.create_btn.setMinimumWidth(120)
        self.create_btn.setDefault(True)
        self.create_btn.clicked.connect(self.create_project)
        self.create_btn.setEnabled(False)  # Disabled until valid input
        button_layout.addWidget(self.create_btn)
        
        main_layout.addLayout(button_layout)
    
    def set_default_values(self):
        """Set default values for the form"""
        # Default project location
        default_location = Path.home() / "LupineProjects"
        self.path_edit.setText(str(default_location))
        self.update_full_path()
    
    def browse_location(self):
        """Browse for project location"""
        location = QFileDialog.getExistingDirectory(
            self, "Select Project Location", self.path_edit.text()
        )
        
        if location:
            self.path_edit.setText(location)
            self.update_full_path()
    
    def on_name_changed(self):
        """Handle project name change"""
        self.update_full_path()
        self.validate_input()
    
    def update_full_path(self):
        """Update the full project path display"""
        if self.name_edit.text() and self.path_edit.text():
            full_path = Path(self.path_edit.text()) / self.name_edit.text()
            self.full_path_edit.setText(str(full_path))
        else:
            self.full_path_edit.setText("")
    
    def validate_input(self):
        """Validate user input and enable/disable create button"""
        name = self.name_edit.text().strip()
        location = self.path_edit.text().strip()
        
        # Check if name is valid
        if not name:
            self.create_btn.setEnabled(False)
            return
        
        # Check if location is valid
        if not location or not Path(location).exists():
            self.create_btn.setEnabled(False)
            return
        
        # Check if project folder already exists
        full_path = Path(location) / name
        if full_path.exists():
            self.create_btn.setEnabled(False)
            return
        
        # All checks passed
        self.create_btn.setEnabled(True)
    
    def create_project(self):
        """Create the project"""
        name = self.name_edit.text().strip()
        location = self.path_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a project name!")
            return
        
        if not location:
            QMessageBox.warning(self, "Invalid Input", "Please select a project location!")
            return
        
        # Check if location exists
        location_path = Path(location)
        if not location_path.exists():
            try:
                location_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create location directory:\n{e}")
                return
        
        # Check if project already exists
        full_path = location_path / name
        if full_path.exists():
            QMessageBox.warning(self, "Project Exists", 
                              "A folder with this name already exists at the selected location!")
            return
        
        # Store project info and accept dialog
        self.project_info = {
            "name": name,
            "path": str(full_path),
            "description": description
        }
        
        self.accept()
    
    def get_project_info(self):
        """Get the project information"""
        return getattr(self, 'project_info', None)
