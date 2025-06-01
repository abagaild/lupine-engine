"""
Project Manager Window for Lupine Engine
Handles project selection, creation, and opening
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QFrame, QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QIcon

from core.project import ProjectManager as CoreProjectManager, LupineProject
from .project_dialog import NewProjectDialog


class ProjectListItem(QFrame):
    """Custom widget for project list items"""
    
    def __init__(self, project_info: dict):
        super().__init__()
        self.project_info = project_info
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for the project item"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border: 1px solid #555555;
                border-radius: 4px;
                margin: 2px;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #454545;
                border-color: #8b5fbf;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Project name
        name_label = QLabel(self.project_info["name"])
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #e0e0e0; border: none;")
        layout.addWidget(name_label)
        
        # Project path
        path_label = QLabel(self.project_info["path"])
        path_label.setStyleSheet("color: #b0b0b0; font-size: 10px; border: none;")
        layout.addWidget(path_label)
        
        # Project description
        if self.project_info.get("description"):
            desc_label = QLabel(self.project_info["description"])
            desc_label.setStyleSheet("color: #b0b0b0; border: none;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)


class ProjectManager(QMainWindow):
    """Main project manager window"""
    
    project_opened = pyqtSignal(str)  # Emitted when a project is opened
    
    def __init__(self):
        super().__init__()
        self.core_manager = CoreProjectManager()
        self.setup_ui()
        self.load_recent_projects()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Lupine Engine - Project Manager")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Logo and actions
        self.create_left_panel(splitter)
        
        # Right panel - Recent projects
        self.create_right_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
    
    def create_left_panel(self, parent):
        """Create the left panel with logo and action buttons"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale logo to fit nicely
            scaled_pixmap = pixmap.scaled(250, 150, Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("LUPINE ENGINE")
            logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #8b5fbf;")
        
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(logo_label)
        
        left_layout.addSpacing(30)
        
        # Action buttons
        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.setMinimumHeight(40)
        self.new_project_btn.clicked.connect(self.new_project)
        left_layout.addWidget(self.new_project_btn)
        
        self.open_project_btn = QPushButton("Open Project")
        self.open_project_btn.setMinimumHeight(40)
        self.open_project_btn.clicked.connect(self.open_project)
        left_layout.addWidget(self.open_project_btn)
        
        self.import_project_btn = QPushButton("Import Project")
        self.import_project_btn.setMinimumHeight(40)
        self.import_project_btn.clicked.connect(self.import_project)
        left_layout.addWidget(self.import_project_btn)
        
        # Placeholder for templates
        self.templates_btn = QPushButton("Project Templates")
        self.templates_btn.setMinimumHeight(40)
        self.templates_btn.setEnabled(False)  # Placeholder
        self.templates_btn.setToolTip("Coming soon!")
        left_layout.addWidget(self.templates_btn)
        
        left_layout.addStretch()
        
        parent.addWidget(left_widget)
    
    def create_right_panel(self, parent):
        """Create the right panel with recent projects"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Title
        title_label = QLabel("Recent Projects")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #e0e0e0; margin-bottom: 10px;")
        right_layout.addWidget(title_label)
        
        # Recent projects list
        self.recent_projects_list = QListWidget()
        self.recent_projects_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
                margin: 2px;
            }
        """)
        self.recent_projects_list.itemDoubleClicked.connect(self.open_recent_project)
        right_layout.addWidget(self.recent_projects_list)
        
        parent.addWidget(right_widget)
    
    def load_recent_projects(self):
        """Load and display recent projects"""
        self.recent_projects_list.clear()
        recent_projects = self.core_manager.get_recent_projects()
        
        for project_info in recent_projects:
            # Create custom widget for project item
            project_widget = ProjectListItem(project_info)
            
            # Create list item
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, project_info)
            item.setSizeHint(project_widget.sizeHint())
            
            # Add to list
            self.recent_projects_list.addItem(item)
            self.recent_projects_list.setItemWidget(item, project_widget)
    
    def new_project(self):
        """Create a new project"""
        dialog = NewProjectDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            project_info = dialog.get_project_info()
            
            # Create project
            project = LupineProject(project_info["path"])
            if project.create_new_project(project_info["name"], project_info["description"]):
                # Add to recent projects
                self.core_manager.add_recent_project(project_info["path"])
                
                # Refresh recent projects list
                self.load_recent_projects()
                
                # Open the project
                self.open_project_path(project_info["path"])
            else:
                QMessageBox.critical(self, "Error", "Failed to create project!")
    
    def open_project(self):
        """Open an existing project"""
        project_path = QFileDialog.getExistingDirectory(
            self, "Select Project Folder", str(Path.home())
        )
        
        if project_path:
            self.open_project_path(project_path)
    
    def open_project_path(self, project_path: str):
        """Open project at given path"""
        project_file = Path(project_path) / "project.lupine"
        if not project_file.exists():
            QMessageBox.warning(self, "Invalid Project", 
                              "Selected folder does not contain a valid Lupine project!")
            return
        
        # Add to recent projects
        self.core_manager.add_recent_project(project_path)
        
        # Emit signal to open editor
        self.project_opened.emit(project_path)
        
        # Import main editor here to avoid circular imports
        from editor.main_editor import MainEditor
        
        # Create and show main editor
        self.editor = MainEditor(project_path)
        self.editor.show()
        
        # Keep project manager open (as per user preference)
        # self.hide()  # Commented out to keep project manager open
    
    def open_recent_project(self, item: QListWidgetItem):
        """Open a recent project"""
        project_info = item.data(Qt.ItemDataRole.UserRole)
        self.open_project_path(project_info["path"])
    
    def import_project(self):
        """Import an existing project (placeholder)"""
        QMessageBox.information(self, "Import Project", 
                              "Project import functionality coming soon!")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Close the entire application when project manager is closed
        QApplication.quit()
        event.accept()
