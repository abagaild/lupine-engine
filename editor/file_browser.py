"""
File Browser Widget for Lupine Engine
Displays project files and allows file operations
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QHeaderView, QMenu,
    QMessageBox, QInputDialog, QLineEdit
)
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from core.project import LupineProject


class FileBrowserWidget(QWidget):
    """File browser widget for project files"""
    
    file_opened = pyqtSignal(str)  # Emitted when a file is double-clicked
    file_selected = pyqtSignal(str)  # Emitted when a file is selected
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # File system model
        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.project.project_path))
        
        # Tree view
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(str(self.project.project_path)))
        
        # Hide unnecessary columns
        self.tree_view.hideColumn(1)  # Size
        self.tree_view.hideColumn(2)  # Type
        self.tree_view.hideColumn(3)  # Date Modified
        
        # Configure tree view
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.doubleClicked.connect(self.on_double_click)
        self.tree_view.clicked.connect(self.on_single_click)
        
        # Expand the root
        self.tree_view.expand(self.model.index(str(self.project.project_path)))
        
        layout.addWidget(self.tree_view)
    
    def show_context_menu(self, position):
        """Show context menu for files and folders"""
        index = self.tree_view.indexAt(position)
        
        menu = QMenu(self)
        
        if index.isValid():
            file_path = self.model.filePath(index)
            is_dir = self.model.isDir(index)
            
            if is_dir:
                # Folder context menu
                new_file_action = QAction("New File", self)
                new_file_action.triggered.connect(lambda: self.new_file(file_path))
                menu.addAction(new_file_action)

                new_script_action = QAction("New Script", self)
                new_script_action.triggered.connect(lambda: self.new_script(file_path))
                menu.addAction(new_script_action)

                new_scene_action = QAction("New Scene", self)
                new_scene_action.triggered.connect(lambda: self.new_scene(file_path))
                menu.addAction(new_scene_action)

                new_folder_action = QAction("New Folder", self)
                new_folder_action.triggered.connect(lambda: self.new_folder(file_path))
                menu.addAction(new_folder_action)

                menu.addSeparator()

                # Import file
                import_action = QAction("Import File", self)
                import_action.triggered.connect(lambda: self.import_file(file_path))
                menu.addAction(import_action)
            else:
                # File context menu
                open_action = QAction("Open", self)
                open_action.triggered.connect(lambda: self.open_file(file_path))
                menu.addAction(open_action)
                
                menu.addSeparator()
                
                # Show in explorer (Windows) / Finder (Mac) / File manager (Linux)
                show_action = QAction("Show in Explorer", self)
                show_action.triggered.connect(lambda: self.show_in_explorer(file_path))
                menu.addAction(show_action)
            
            menu.addSeparator()
            
            # Rename
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.rename_item(index))
            menu.addAction(rename_action)
            
            # Delete
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self.delete_item(file_path))
            menu.addAction(delete_action)
        else:
            # Empty space context menu
            new_file_action = QAction("New File", self)
            new_file_action.triggered.connect(lambda: self.new_file(str(self.project.project_path)))
            menu.addAction(new_file_action)
            
            new_folder_action = QAction("New Folder", self)
            new_folder_action.triggered.connect(lambda: self.new_folder(str(self.project.project_path)))
            menu.addAction(new_folder_action)
        
        menu.exec(self.tree_view.mapToGlobal(position))
    
    def on_double_click(self, index: QModelIndex):
        """Handle double click on file/folder"""
        if index.isValid():
            file_path = self.model.filePath(index)
            if not self.model.isDir(index):
                self.open_file(file_path)
    
    def on_single_click(self, index: QModelIndex):
        """Handle single click on file/folder"""
        if index.isValid():
            file_path = self.model.filePath(index)
            self.file_selected.emit(file_path)
    
    def open_file(self, file_path: str):
        """Open a file"""
        self.file_opened.emit(file_path)
    
    def new_file(self, parent_dir: str):
        """Create a new file"""
        name, ok = QInputDialog.getText(
            self, "New File", "Enter file name:", QLineEdit.EchoMode.Normal, "new_file.lsc"
        )
        
        if ok and name:
            file_path = Path(parent_dir) / name
            try:
                # Create file with appropriate template
                if name.endswith('.lsc'):
                    template = self.get_lsc_template()
                elif name.endswith('.scene'):
                    template = self.get_scene_template()
                else:
                    template = ""
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(template)
                
                # Refresh view
                self.refresh()
                
                # Open the new file
                self.open_file(str(file_path))
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file: {e}")

    def new_script(self, parent_dir: str):
        """Create a new LSC script"""
        name, ok = QInputDialog.getText(
            self, "New Script", "Enter script name:", QLineEdit.EchoMode.Normal, "new_script.lsc"
        )

        if ok and name:
            if not name.endswith('.lsc'):
                name += '.lsc'

            file_path = Path(parent_dir) / name
            try:
                template = self.get_lsc_template()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(template)

                # Refresh view
                self.refresh()

                # Open the new script
                self.open_file(str(file_path))

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create script: {e}")

    def new_scene(self, parent_dir: str):
        """Create a new scene"""
        name, ok = QInputDialog.getText(
            self, "New Scene", "Enter scene name:", QLineEdit.EchoMode.Normal, "new_scene.scene"
        )

        if ok and name:
            if not name.endswith('.scene'):
                name += '.scene'

            file_path = Path(parent_dir) / name
            try:
                # Create scene with the name (without extension) as the root node name
                scene_name = Path(name).stem
                template = self.get_scene_template(scene_name)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(template)

                # Refresh view
                self.refresh()

                # Open the new scene
                self.open_file(str(file_path))

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create scene: {e}")

    def new_folder(self, parent_dir: str):
        """Create a new folder"""
        name, ok = QInputDialog.getText(
            self, "New Folder", "Enter folder name:", QLineEdit.EchoMode.Normal, "new_folder"
        )
        
        if ok and name:
            folder_path = Path(parent_dir) / name
            try:
                folder_path.mkdir(exist_ok=True)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create folder: {e}")
    
    def import_file(self, target_dir: str):
        """Import a file to the project"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import File", "", "All Files (*)"
        )
        
        if file_path:
            try:
                import shutil
                file_name = os.path.basename(file_path)
                target_path = Path(target_dir) / file_name
                
                # Check if file already exists
                if target_path.exists():
                    reply = QMessageBox.question(
                        self, "File Exists",
                        f"File '{file_name}' already exists. Overwrite?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                
                shutil.copy2(file_path, target_path)
                self.refresh()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import file: {e}")
    
    def rename_item(self, index: QModelIndex):
        """Rename a file or folder"""
        if not index.isValid():
            return
        
        current_name = self.model.fileName(index)
        new_name, ok = QInputDialog.getText(
            self, "Rename", "Enter new name:", QLineEdit.EchoMode.Normal, current_name
        )
        
        if ok and new_name and new_name != current_name:
            old_path = Path(self.model.filePath(index))
            new_path = old_path.parent / new_name
            
            try:
                old_path.rename(new_path)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename: {e}")
    
    def delete_item(self, file_path: str):
        """Delete a file or folder"""
        path = Path(file_path)
        item_type = "folder" if path.is_dir() else "file"
        
        reply = QMessageBox.question(
            self, "Delete Item",
            f"Are you sure you want to delete this {item_type}?\n\n{path.name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                else:
                    path.unlink()
                
                self.refresh()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete {item_type}: {e}")
    
    def show_in_explorer(self, file_path: str):
        """Show file in system file explorer"""
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", file_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open file explorer: {e}")
    
    def refresh(self):
        """Refresh the file browser"""
        self.model.setRootPath("")  # Reset
        self.model.setRootPath(str(self.project.project_path))  # Reload
    
    def get_lsc_template(self) -> str:
        """Get LSC script template"""
        return '''# LSC Script
extends Node2D

# Export variables
export var example_property: float = 1.0

# Called when the node enters the scene tree
func _ready():
    print("Node ready!")

# Called every frame
func _process(delta: float):
    pass
'''
    
    def get_scene_template(self, scene_name: str = "Scene") -> str:
        """Get scene file template"""
        import json
        scene_data = {
            "name": scene_name,
            "nodes": [
                {
                    "name": scene_name,
                    "type": "Node2D",
                    "position": [0, 0],
                    "children": []
                }
            ]
        }
        return json.dumps(scene_data, indent=2)
    
    def expand_folder(self, folder_path: str):
        """Expand a specific folder"""
        index = self.model.index(folder_path)
        if index.isValid():
            self.tree_view.expand(index)
