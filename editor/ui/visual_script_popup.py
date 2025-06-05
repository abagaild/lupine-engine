"""
Visual Script Editor Popup Window
Provides a popup interface for visual scripting in various builders
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
import json

from .enhanced_visual_script_editor import EnhancedVisualScriptEditor
from core.project import LupineProject


class VisualScriptPopup(QDialog):
    """Popup window for visual script editing"""
    
    script_saved = pyqtSignal(str)  # Emitted when script is saved
    script_applied = pyqtSignal(str)  # Emitted when script is applied to object
    
    def __init__(self, parent=None, project: LupineProject = None, 
                 target_object=None, initial_script_path: str = None):
        super().__init__(parent)
        self.project = project
        self.target_object = target_object
        self.initial_script_path = initial_script_path
        self.current_script_path = None
        
        self.setup_ui()
        self.setup_editor()
        
        # Load initial script if provided
        if initial_script_path:
            self.load_script(initial_script_path)
    
    def setup_ui(self):
        """Setup the popup UI"""
        self.setWindowTitle("Visual Script Editor")
        self.setModal(True)
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Visual Script Editor")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Target object info
        if self.target_object:
            target_label = QLabel(f"Target: {getattr(self.target_object, 'name', 'Unknown')}")
            target_label.setStyleSheet("color: #888; font-style: italic;")
            header_layout.addWidget(target_label)
        
        layout.addLayout(header_layout)
        
        # Editor container
        self.editor_container = QVBoxLayout()
        layout.addLayout(self.editor_container)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("New Script")
        self.new_btn.clicked.connect(self.new_script)
        button_layout.addWidget(self.new_btn)
        
        self.open_btn = QPushButton("Open Script")
        self.open_btn.clicked.connect(self.open_script)
        button_layout.addWidget(self.open_btn)
        
        self.save_btn = QPushButton("Save Script")
        self.save_btn.clicked.connect(self.save_script)
        button_layout.addWidget(self.save_btn)
        
        self.save_as_btn = QPushButton("Save As...")
        self.save_as_btn.clicked.connect(self.save_script_as)
        button_layout.addWidget(self.save_as_btn)
        
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply to Object")
        self.apply_btn.clicked.connect(self.apply_script)
        self.apply_btn.setEnabled(bool(self.target_object))
        button_layout.addWidget(self.apply_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def setup_editor(self):
        """Setup the visual script editor"""
        self.editor = EnhancedVisualScriptEditor(project=self.project)
        self.editor.script_saved.connect(self.on_script_saved)
        self.editor_container.addWidget(self.editor)
    
    def new_script(self):
        """Create a new script"""
        self.editor.clear_canvas()
        self.current_script_path = None
        self.setWindowTitle("Visual Script Editor - New Script")
    
    def open_script(self):
        """Open an existing script"""
        if self.project:
            scripts_dir = str(self.project.get_absolute_path("scripts"))
        else:
            scripts_dir = ""
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Visual Script", scripts_dir,
            "Visual Scripts (*.vscript);;All Files (*)"
        )
        
        if file_path:
            self.load_script(file_path)
    
    def load_script(self, file_path: str):
        """Load a script from file"""
        try:
            if self.project:
                # Convert to relative path if needed
                if Path(file_path).is_absolute():
                    file_path = str(self.project.get_relative_path(file_path))
                
                # Load the script
                full_path = self.project.get_absolute_path(file_path)
            else:
                full_path = Path(file_path)
            
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
                
                # Load into editor
                self.editor.load_script_data(script_data)
                self.current_script_path = file_path
                
                file_name = Path(file_path).name
                self.setWindowTitle(f"Visual Script Editor - {file_name}")
            else:
                QMessageBox.warning(self, "File Not Found", f"Script file not found: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load script: {e}")
    
    def save_script(self):
        """Save the current script"""
        if self.current_script_path:
            self.save_to_path(self.current_script_path)
        else:
            self.save_script_as()
    
    def save_script_as(self):
        """Save the script with a new name"""
        if self.project:
            scripts_dir = str(self.project.get_absolute_path("scripts"))
        else:
            scripts_dir = ""
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Visual Script", scripts_dir,
            "Visual Scripts (*.vscript);;All Files (*)"
        )
        
        if file_path:
            if not file_path.endswith('.vscript'):
                file_path += '.vscript'
            
            self.save_to_path(file_path)
    
    def save_to_path(self, file_path: str):
        """Save script to specific path"""
        try:
            # Get script data from editor
            script_data = self.editor.get_script_data()
            
            # Ensure scripts directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save the script
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2)
            
            # Update current path
            if self.project:
                self.current_script_path = str(self.project.get_relative_path(file_path))
            else:
                self.current_script_path = file_path
            
            file_name = Path(file_path).name
            self.setWindowTitle(f"Visual Script Editor - {file_name}")
            
            # Emit signal
            self.script_saved.emit(self.current_script_path)
            
            QMessageBox.information(self, "Success", f"Script saved to: {file_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save script: {e}")
    
    def apply_script(self):
        """Apply the script to the target object"""
        if not self.target_object:
            QMessageBox.warning(self, "No Target", "No target object to apply script to.")
            return
        
        if not self.current_script_path:
            # Save first
            reply = QMessageBox.question(
                self, "Save Script",
                "Script must be saved before applying. Save now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.save_script_as()
            else:
                return
        
        if self.current_script_path:
            # Apply to target object
            if hasattr(self.target_object, 'visual_script_path'):
                self.target_object.visual_script_path = self.current_script_path
            
            self.script_applied.emit(self.current_script_path)
            QMessageBox.information(self, "Applied", "Visual script applied to object.")
    
    def on_script_saved(self, file_path: str):
        """Handle script saved from editor"""
        self.current_script_path = file_path
        file_name = Path(file_path).name
        self.setWindowTitle(f"Visual Script Editor - {file_name}")
    
    def get_current_script_path(self) -> str:
        """Get the current script path"""
        return self.current_script_path or ""


def open_visual_script_popup(parent=None, project: LupineProject = None, 
                           target_object=None, initial_script_path: str = None) -> str:
    """Convenience function to open visual script popup and return selected script path"""
    popup = VisualScriptPopup(parent, project, target_object, initial_script_path)
    
    if popup.exec() == QDialog.DialogCode.Accepted:
        return popup.get_current_script_path()
    
    return ""
