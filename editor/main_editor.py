"""
Main Editor Window for Lupine Engine
Provides the main editing interface with dockable panels and scene management
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QDockWidget, QMenuBar, QMenu, QToolBar, QStatusBar, QSplitter,
    QMessageBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from core.project import LupineProject
from core.node_registry import set_project_path
from .scene_tree import SceneTreeWidget
from .scene_view import SceneViewWidget
from .inspector import InspectorWidget
from .console import ConsoleWidget
from .script_editor import ScriptEditorWidget
from .file_browser import FileBrowserWidget
from .game_runner import GameRunnerWidget


class MainEditor(QMainWindow):
    """Main editor window with dockable interface"""
    
    def __init__(self, project_path: str):
        super().__init__()
        self.project = LupineProject(project_path)
        self.project.load_project()

        # Set up node registry with project path for dynamic node loading
        set_project_path(Path(project_path))

        self.current_scene = None
        self.open_scenes = {}  # scene_path -> scene_data
        
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbars()
        self.setup_docks()
        self.setup_status_bar()
        
        # Load main scene if available
        main_scene = self.project.get_main_scene()
        if main_scene:
            self.open_scene(main_scene)
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle(f"Lupine Engine - {self.project.get_project_name()}")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Central widget - Scene view tabs
        self.scene_tabs = QTabWidget()
        self.scene_tabs.setTabsClosable(True)
        self.scene_tabs.setMovable(True)
        self.scene_tabs.tabCloseRequested.connect(self.close_scene_tab)
        self.scene_tabs.currentChanged.connect(self.on_scene_tab_changed)
        
        # Add "+" tab for opening new scenes
        self.scene_tabs.addTab(QWidget(), "+")
        self.scene_tabs.tabBarClicked.connect(self.on_tab_clicked)
        
        self.setCentralWidget(self.scene_tabs)
    
    def setup_menus(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New scene
        new_scene_action = QAction("New Scene", self)
        new_scene_action.setShortcut(QKeySequence.StandardKey.New)
        new_scene_action.triggered.connect(self.new_scene)
        file_menu.addAction(new_scene_action)
        
        # Open scene
        open_scene_action = QAction("Open Scene", self)
        open_scene_action.setShortcut(QKeySequence.StandardKey.Open)
        open_scene_action.triggered.connect(self.open_scene_dialog)
        file_menu.addAction(open_scene_action)
        
        file_menu.addSeparator()
        
        # Save scene
        save_scene_action = QAction("Save Scene", self)
        save_scene_action.setShortcut(QKeySequence.StandardKey.Save)
        save_scene_action.triggered.connect(self.save_current_scene)
        file_menu.addAction(save_scene_action)
        
        # Save all
        save_all_action = QAction("Save All", self)
        save_all_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_all_action.triggered.connect(self.save_all_scenes)
        file_menu.addAction(save_all_action)
        
        file_menu.addSeparator()
        
        # Project settings
        project_settings_action = QAction("Project Settings", self)
        project_settings_action.triggered.connect(self.open_project_settings)
        file_menu.addAction(project_settings_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        # Undo/Redo (placeholder)
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setEnabled(False)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setEnabled(False)
        edit_menu.addAction(redo_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # This will be populated when docks are created
        self.view_menu = view_menu
        
        # Scene menu
        scene_menu = menubar.addMenu("Scene")
        
        # Run current scene
        run_scene_action = QAction("Run Current Scene", self)
        run_scene_action.setShortcut(QKeySequence("F6"))
        run_scene_action.triggered.connect(self.run_current_scene)
        scene_menu.addAction(run_scene_action)
        
        # Run main scene
        run_main_action = QAction("Run Main Scene", self)
        run_main_action.setShortcut(QKeySequence("F5"))
        run_main_action.triggered.connect(self.run_main_scene)
        scene_menu.addAction(run_main_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        # Script editor
        script_editor_action = QAction("Script Editor", self)
        script_editor_action.triggered.connect(self.open_script_editor)
        tools_menu.addAction(script_editor_action)

        # Input actions
        input_actions_action = QAction("Input Actions", self)
        input_actions_action.triggered.connect(self.open_input_actions)
        tools_menu.addAction(input_actions_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # About
        about_action = QAction("About Lupine Engine", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbars(self):
        """Setup toolbars"""
        # Main toolbar
        main_toolbar = self.addToolBar("Main")
        main_toolbar.setObjectName("MainToolBar")
        
        # Run buttons
        run_scene_action = QAction("Run Scene", self)
        run_scene_action.setToolTip("Run Current Scene (F6)")
        run_scene_action.triggered.connect(self.run_current_scene)
        main_toolbar.addAction(run_scene_action)
        
        run_main_action = QAction("Run Main", self)
        run_main_action.setToolTip("Run Main Scene (F5)")
        run_main_action.triggered.connect(self.run_main_scene)
        main_toolbar.addAction(run_main_action)
        
        main_toolbar.addSeparator()
        
        # Save action
        save_action = QAction("Save", self)
        save_action.setToolTip("Save Current Scene (Ctrl+S)")
        save_action.triggered.connect(self.save_current_scene)
        main_toolbar.addAction(save_action)
    
    def setup_docks(self):
        """Setup dockable widgets"""
        # Scene Tree
        self.scene_tree_dock = QDockWidget("Scene Tree", self)
        self.scene_tree_dock.setObjectName("SceneTreeDock")
        self.scene_tree = SceneTreeWidget(self.project)
        self.scene_tree.node_changed.connect(self.on_scene_node_changed)
        self.scene_tree.node_selected.connect(self.on_scene_tree_node_selected)
        self.scene_tree_dock.setWidget(self.scene_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.scene_tree_dock)
        
        # Inspector
        self.inspector_dock = QDockWidget("Inspector", self)
        self.inspector_dock.setObjectName("InspectorDock")
        self.inspector = InspectorWidget(self.project)
        self.inspector.property_changed.connect(self.on_inspector_property_changed)
        self.inspector_dock.setWidget(self.inspector)
        self.inspector_dock.setMinimumWidth(300)  # Make inspector wider
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.inspector_dock)
        
        # File Browser
        self.file_browser_dock = QDockWidget("Project Files", self)
        self.file_browser_dock.setObjectName("FileBrowserDock")
        self.file_browser = FileBrowserWidget(self.project)
        self.file_browser.file_opened.connect(self.open_file_from_browser)
        self.file_browser_dock.setWidget(self.file_browser)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.file_browser_dock)
        
        # Console/Output
        self.console_dock = QDockWidget("Output", self)
        self.console_dock.setObjectName("ConsoleDock")
        self.console = ConsoleWidget()
        self.console_dock.setWidget(self.console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)
        
        # Game Runner
        self.game_runner_dock = QDockWidget("Game Runner", self)
        self.game_runner_dock.setObjectName("GameRunnerDock")
        self.game_runner = GameRunnerWidget(self.project)
        self.game_runner_dock.setWidget(self.game_runner)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.game_runner_dock)
        
        # Script Editor
        self.script_editor_dock = QDockWidget("Script Editor", self)
        self.script_editor_dock.setObjectName("ScriptEditorDock")
        self.script_editor = ScriptEditorWidget(self.project)
        self.script_editor_dock.setWidget(self.script_editor)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.script_editor_dock)
        
        # Tabify bottom docks
        self.tabifyDockWidget(self.console_dock, self.game_runner_dock)
        self.tabifyDockWidget(self.game_runner_dock, self.script_editor_dock)
        
        # Tabify left docks
        self.tabifyDockWidget(self.scene_tree_dock, self.file_browser_dock)
        
        # Add dock toggle actions to view menu
        self.view_menu.addAction(self.scene_tree_dock.toggleViewAction())
        self.view_menu.addAction(self.inspector_dock.toggleViewAction())
        self.view_menu.addAction(self.file_browser_dock.toggleViewAction())
        self.view_menu.addAction(self.console_dock.toggleViewAction())
        self.view_menu.addAction(self.game_runner_dock.toggleViewAction())
        self.view_menu.addAction(self.script_editor_dock.toggleViewAction())
        
        # Show console by default
        self.console_dock.raise_()
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def on_tab_clicked(self, index):
        """Handle tab clicks"""
        if index == self.scene_tabs.count() - 1:  # "+" tab
            self.open_scene_dialog()

    def on_scene_tab_changed(self, index):
        """Handle scene tab change"""
        if index >= 0 and index < self.scene_tabs.count() - 1:  # Not the "+" tab
            scene_widget = self.scene_tabs.widget(index)
            if hasattr(scene_widget, 'scene_path'):
                self.current_scene = scene_widget.scene_path
                # Update scene tree with current scene data from open_scenes
                if self.current_scene in self.open_scenes:
                    # Ensure scene view and scene tree use the same data object
                    shared_scene_data = self.open_scenes[self.current_scene]
                    scene_widget.scene_data = shared_scene_data
                    if hasattr(scene_widget, 'viewport'):
                        scene_widget.viewport.scene_data = shared_scene_data

                    self.scene_tree.set_scene_data(shared_scene_data)
                    self.scene_tree.current_scene_path = self.current_scene

    def new_scene(self):
        """Create a new scene"""
        # For now, create a simple default scene
        scene_name = f"NewScene{len(self.open_scenes) + 1}"
        scene_path = f"scenes/{scene_name}.scene"

        # Create scene data
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

        # Add to open scenes (this becomes the master reference)
        self.open_scenes[scene_path] = scene_data

        # Create scene view widget with the same data object
        scene_view = SceneViewWidget(self.project, scene_path, scene_data)
        scene_view.scene_path = scene_path

        # Connect scene view signals
        self.connect_scene_view_signals(scene_view)

        # Add tab (before the "+" tab)
        tab_index = self.scene_tabs.count() - 1
        self.scene_tabs.insertTab(tab_index, scene_view, scene_name)
        self.scene_tabs.setCurrentIndex(tab_index)

        # Set as current scene
        self.current_scene = scene_path

        # Update scene tree with the same data object
        self.scene_tree.set_scene_data(scene_data)
        self.scene_tree.current_scene_path = scene_path

    def open_scene_dialog(self):
        """Open scene selection dialog"""
        scenes_dir = self.project.get_absolute_path("scenes")
        scene_file, _ = QFileDialog.getOpenFileName(
            self, "Open Scene", str(scenes_dir), "Scene Files (*.scene)"
        )

        if scene_file:
            # Convert to relative path
            relative_path = self.project.get_relative_path(scene_file)
            self.open_scene(relative_path)

    def open_scene(self, scene_path: str):
        """Open a scene by path"""
        # Check if already open
        for i in range(self.scene_tabs.count() - 1):  # Exclude "+" tab
            widget = self.scene_tabs.widget(i)
            if hasattr(widget, 'scene_path') and widget.scene_path == scene_path:
                self.scene_tabs.setCurrentIndex(i)
                return

        # Load scene data
        scene_file = self.project.get_absolute_path(scene_path)
        if not scene_file.exists():
            QMessageBox.warning(self, "Scene Not Found", f"Scene file not found: {scene_path}")
            return

        try:
            import json
            with open(scene_file, 'r') as f:
                scene_data = json.load(f)

            # Add to open scenes (this becomes the master reference)
            self.open_scenes[scene_path] = scene_data

            # Create scene view widget with the same data object
            scene_view = SceneViewWidget(self.project, scene_path, scene_data)
            scene_view.scene_path = scene_path

            # Connect scene view signals
            self.connect_scene_view_signals(scene_view)

            # Add tab
            scene_name = scene_data.get("name", Path(scene_path).stem)
            tab_index = self.scene_tabs.count() - 1
            self.scene_tabs.insertTab(tab_index, scene_view, scene_name)
            self.scene_tabs.setCurrentIndex(tab_index)

            # Set as current scene
            self.current_scene = scene_path

            # Update scene tree with the same data object (not a copy)
            self.scene_tree.set_scene_data(scene_data)
            self.scene_tree.current_scene_path = scene_path

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load scene: {e}")

    def close_scene_tab(self, index):
        """Close a scene tab"""
        if index < self.scene_tabs.count() - 1:  # Not the "+" tab
            widget = self.scene_tabs.widget(index)
            if hasattr(widget, 'scene_path'):
                scene_path = widget.scene_path
                # Remove from open scenes
                if scene_path in self.open_scenes:
                    del self.open_scenes[scene_path]

            self.scene_tabs.removeTab(index)

    def save_current_scene(self):
        """Save the current scene"""
        if self.current_scene and self.current_scene in self.open_scenes:
            self.save_scene(self.current_scene)

    def save_scene(self, scene_path: str):
        """Save a specific scene"""
        if scene_path not in self.open_scenes:
            return

        try:
            import json
            scene_file = self.project.get_absolute_path(scene_path)
            scene_file.parent.mkdir(parents=True, exist_ok=True)

            # Ensure we're saving the most up-to-date data
            # Priority: scene_tree.current_scene_data > open_scenes
            scene_data_to_save = self.open_scenes[scene_path]
            if self.scene_tree.current_scene_data and self.scene_tree.current_scene_path == scene_path:
                # Synchronize tree to scene data before saving
                self.scene_tree.sync_tree_to_scene_data()
                scene_data_to_save = self.scene_tree.current_scene_data
                # Update open_scenes to match
                self.open_scenes[scene_path] = scene_data_to_save

            with open(scene_file, 'w') as f:
                json.dump(scene_data_to_save, f, indent=2)

            self.status_bar.showMessage(f"Saved {scene_path}", 2000)

            # Update tab title to remove asterisk if present
            for i in range(self.scene_tabs.count() - 1):
                widget = self.scene_tabs.widget(i)
                if hasattr(widget, 'scene_path') and widget.scene_path == scene_path:
                    tab_text = self.scene_tabs.tabText(i)
                    if tab_text.endswith('*'):
                        self.scene_tabs.setTabText(i, tab_text[:-1])
                    break

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save scene: {e}")

    def save_all_scenes(self):
        """Save all open scenes"""
        for scene_path in self.open_scenes:
            self.save_scene(scene_path)

    def run_current_scene(self):
        """Run the current scene"""
        if self.current_scene:
            self.game_runner.run_scene(self.current_scene)
            self.game_runner_dock.raise_()
        else:
            QMessageBox.information(self, "No Scene", "No scene is currently open!")

    def run_main_scene(self):
        """Run the main scene"""
        main_scene = self.project.get_main_scene()
        if main_scene:
            self.game_runner.run_scene(main_scene)
            self.game_runner_dock.raise_()
        else:
            QMessageBox.information(self, "No Main Scene", "No main scene is set for this project!")

    def open_script_editor(self):
        """Open the script editor"""
        self.script_editor_dock.raise_()

    def open_project_settings(self):
        """Open project settings (placeholder)"""
        QMessageBox.information(self, "Project Settings", "Project settings dialog coming soon!")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Lupine Engine",
                         "Lupine Engine v1.0.0\n\n"
                         "A powerful game engine combining the flexibility of Godot/Unreal "
                         "with the ease of Ren'py/RPG Maker.\n\n"
                         "Built with Python, PyQt6, and Arcade.")

    def open_file_from_browser(self, file_path: str):
        """Open a file from the file browser"""
        file_path_obj = Path(file_path)

        if file_path_obj.suffix == '.scene':
            # Open scene file
            relative_path = self.project.get_relative_path(str(file_path_obj))
            self.open_scene(relative_path)
        elif file_path_obj.suffix == '.lsc':
            # Open script file in script editor
            self.script_editor.open_script_file(str(file_path_obj))
            self.script_editor_dock.raise_()
        else:
            # For other files, just show a message
            self.status_bar.showMessage(f"Opened: {file_path_obj.name}", 2000)

    def on_scene_node_changed(self, node_data):
        """Handle scene node changes"""
        # Mark current scene as modified
        if self.current_scene:
            for i in range(self.scene_tabs.count() - 1):
                widget = self.scene_tabs.widget(i)
                if hasattr(widget, 'scene_path') and widget.scene_path == self.current_scene:
                    tab_text = self.scene_tabs.tabText(i)
                    if not tab_text.endswith('*'):
                        self.scene_tabs.setTabText(i, tab_text + '*')
                    break

        # Update inspector if node is selected
        if node_data:
            self.inspector.set_node(node_data)

    def on_scene_tree_node_selected(self, node_data):
        """Handle node selection from scene tree"""
        # The scene tree now provides the current reference, so we can use it directly
        # Update inspector
        self.inspector.set_node(node_data)

        # Update scene view selection
        current_scene_widget = self.get_current_scene_widget()
        if current_scene_widget and hasattr(current_scene_widget, 'viewport'):
            current_scene_widget.viewport.set_selected_node(node_data)

    def connect_scene_view_signals(self, scene_view: SceneViewWidget):
        """Connect scene view signals to editor components"""
        if hasattr(scene_view, 'viewport'):
            # Connect node selection from scene view to inspector
            scene_view.viewport.node_selected.connect(self.on_scene_view_node_selected)
            # Connect node modifications from scene view to inspector
            scene_view.viewport.node_modified.connect(self.on_scene_view_node_modified)

    def on_scene_view_node_selected(self, node_data: dict):
        """Handle node selection from scene view"""
        # Get the most current node reference from our data stores
        current_node_ref = self.get_current_node_reference(node_data.get("name", ""))
        if current_node_ref:
            node_data = current_node_ref

        self.inspector.set_node(node_data)
        # Also update scene tree selection if needed
        self.scene_tree.select_node(node_data)

    def on_scene_view_node_modified(self, node_data: dict, property_name: str, value):
        """Handle node modification from scene view"""
        node_name = node_data.get("name", "")

        # Update the property in all our data stores to keep them synchronized
        if self.current_scene and self.current_scene in self.open_scenes:
            # Update the main scene data
            scene_node = self.find_node_by_name(self.open_scenes[self.current_scene], node_name)
            if scene_node:
                scene_node[property_name] = value

        # Update the scene tree data
        if self.scene_tree.current_scene_data:
            tree_node = self.find_node_by_name(self.scene_tree.current_scene_data, node_name)
            if tree_node:
                tree_node[property_name] = value

            # Also update the tree item data to keep the UI synchronized
            self.scene_tree.update_tree_item_property(node_name, property_name, value)

        # Update inspector to reflect the change without rebuilding the entire UI
        if self.inspector.current_node and self.inspector.current_node.get("name") == node_name:
            # Update the node reference and refresh property widgets
            self.inspector.update_node_reference(node_data)

        # Update scene view rendering to reflect any changes
        current_scene_widget = self.get_current_scene_widget()
        if current_scene_widget and hasattr(current_scene_widget, 'viewport'):
            current_scene_widget.viewport.update()

        # Mark scene as modified
        self.mark_scene_modified()

    def on_inspector_property_changed(self, node_id: str, property_name: str, value):
        """Handle property changes from inspector"""
        # The inspector updates the scene data reference, but we also need to update
        # the tree item data to keep everything synchronized

        # Update the tree item data to match the inspector changes
        self.scene_tree.update_tree_item_property(node_id, property_name, value)

        # Update scene view rendering
        current_scene_widget = self.get_current_scene_widget()
        if current_scene_widget and hasattr(current_scene_widget, 'viewport'):
            current_scene_widget.viewport.update()

        # Mark scene as modified
        self.mark_scene_modified()

    def get_current_scene_widget(self):
        """Get the currently active scene widget"""
        current_index = self.scene_tabs.currentIndex()
        if current_index >= 0 and current_index < self.scene_tabs.count() - 1:
            return self.scene_tabs.widget(current_index)
        return None

    def get_current_node_reference(self, node_name: str):
        """Get the most current reference to a node by name"""
        if not node_name:
            return None

        # Priority: open_scenes > scene_tree > scene_view
        if self.current_scene and self.current_scene in self.open_scenes:
            node = self.find_node_by_name(self.open_scenes[self.current_scene], node_name)
            if node:
                return node

        if self.scene_tree.current_scene_data:
            node = self.find_node_by_name(self.scene_tree.current_scene_data, node_name)
            if node:
                return node

        # Fallback to scene view
        current_scene_widget = self.get_current_scene_widget()
        if current_scene_widget and hasattr(current_scene_widget, 'viewport'):
            node = self.find_node_by_name(current_scene_widget.viewport.scene_data, node_name)
            if node:
                return node

        return None

    def find_node_by_name(self, scene_data: dict, node_name: str):
        """Find a node by name in scene data"""
        nodes = scene_data.get("nodes", [])
        return self._find_node_recursive(nodes, node_name)

    def _find_node_recursive(self, nodes: list, node_name: str):
        """Recursively find a node by name"""
        for node in nodes:
            if node.get("name") == node_name:
                return node
            # Check children
            children = node.get("children", [])
            if children:
                found = self._find_node_recursive(children, node_name)
                if found:
                    return found
        return None

    def mark_scene_modified(self):
        """Mark the current scene as modified"""
        if self.current_scene:
            for i in range(self.scene_tabs.count() - 1):
                widget = self.scene_tabs.widget(i)
                if hasattr(widget, 'scene_path') and widget.scene_path == self.current_scene:
                    tab_text = self.scene_tabs.tabText(i)
                    if not tab_text.endswith('*'):
                        self.scene_tabs.setTabText(i, tab_text + '*')
                    break

    def open_input_actions(self):
        """Open the input actions dialog"""
        try:
            from editor.input_actions_dialog import InputActionsDialog
            dialog = InputActionsDialog(self.project, self)
            dialog.exec()
        except ImportError:
            QMessageBox.warning(self, "Error", "Input Actions dialog not available yet.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Input Actions dialog: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        # Save all scenes before closing
        self.save_all_scenes()
        event.accept()
