"""
Dialogue Writer Window
Main window for creating and editing dialogue scripts with dual-mode interface
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QPushButton, QFileDialog, QMessageBox, QInputDialog, QComboBox,
    QCheckBox, QSpinBox, QGroupBox, QListWidget, QListWidgetItem,
    QTextEdit, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from core.project import LupineProject
from core.dialogue.dialogue_parser import DialogueParser, DialogueScript
from core.dialogue.dialogue_runtime import DialogueRuntime
from core.dialogue.asset_resolver import DialogueAssetResolver
from .ui.dialogue_script_editor import DialogueScriptEditor
from .ui.dialogue_node_graph import DialogueNodeGraph


class DialogueWriterWindow(QMainWindow):
    """Main dialogue writer window"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.parser = DialogueParser()
        self.asset_resolver = DialogueAssetResolver(project)
        self.runtime = DialogueRuntime(project, self.asset_resolver)
        
        # Current state
        self.current_script: Optional[DialogueScript] = None
        self.current_file_path: Optional[str] = None
        self.is_modified = False
        
        # Settings
        self.settings = QSettings("LupineEngine", "DialogueWriter")
        
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbars()
        self.setup_connections()
        self.setup_status_bar()
        
        # Load settings
        self.load_settings()
        
        # Create default directories
        self.ensure_dialogue_directories()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Dialogue Writer - Lupine Engine")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel - File browser and assets
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Center - Main editing area
        center_widget = self.create_center_widget()
        main_splitter.addWidget(center_widget)
        
        # Right panel - Preview and tools
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([250, 800, 350])
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with file browser and assets"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # File browser
        file_group = QGroupBox("Dialogue Files")
        file_layout = QVBoxLayout(file_group)
        
        # File list
        self.file_list = QListWidget()
        file_layout.addWidget(self.file_list)
        
        # File buttons
        file_buttons = QHBoxLayout()
        self.new_file_btn = QPushButton("New")
        self.open_file_btn = QPushButton("Open")
        self.delete_file_btn = QPushButton("Delete")
        
        file_buttons.addWidget(self.new_file_btn)
        file_buttons.addWidget(self.open_file_btn)
        file_buttons.addWidget(self.delete_file_btn)
        file_layout.addLayout(file_buttons)
        
        layout.addWidget(file_group)
        
        # Asset browser
        asset_group = QGroupBox("Assets")
        asset_layout = QVBoxLayout(asset_group)
        
        # Asset tabs
        self.asset_tabs = QTabWidget()
        
        # Backgrounds
        self.backgrounds_list = QListWidget()
        self.asset_tabs.addTab(self.backgrounds_list, "Backgrounds")
        
        # Music
        self.music_list = QListWidget()
        self.asset_tabs.addTab(self.music_list, "Music")
        
        # Sound Effects
        self.sounds_list = QListWidget()
        self.asset_tabs.addTab(self.sounds_list, "Sounds")
        
        # Portraits
        self.portraits_list = QListWidget()
        self.asset_tabs.addTab(self.portraits_list, "Portraits")
        
        asset_layout.addWidget(self.asset_tabs)
        
        # Refresh assets button
        self.refresh_assets_btn = QPushButton("Refresh Assets")
        asset_layout.addWidget(self.refresh_assets_btn)
        
        layout.addWidget(asset_group)
        
        return panel
    
    def create_center_widget(self) -> QWidget:
        """Create the center editing widget"""
        # Tab widget for different editing modes
        self.edit_tabs = QTabWidget()
        
        # Script editor tab
        self.script_editor = DialogueScriptEditor()
        self.edit_tabs.addTab(self.script_editor, "Script Editor")
        
        # Node graph tab
        self.node_graph = DialogueNodeGraph()
        self.edit_tabs.addTab(self.node_graph, "Node Graph")
        
        return self.edit_tabs
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with preview and tools"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview group
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Preview controls
        preview_controls = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn = QPushButton("Stop")
        self.next_btn = QPushButton("Next")
        
        preview_controls.addWidget(self.play_btn)
        preview_controls.addWidget(self.pause_btn)
        preview_controls.addWidget(self.stop_btn)
        preview_controls.addWidget(self.next_btn)
        preview_layout.addLayout(preview_controls)
        
        # Preview display
        self.preview_display = QTextEdit()
        self.preview_display.setMaximumHeight(200)
        self.preview_display.setReadOnly(True)
        preview_layout.addWidget(self.preview_display)
        
        layout.addWidget(preview_group)
        
        # Variables group
        variables_group = QGroupBox("Variables")
        variables_layout = QVBoxLayout(variables_group)
        
        self.variables_list = QListWidget()
        self.variables_list.setMaximumHeight(150)
        variables_layout.addWidget(self.variables_list)
        
        # Variable controls
        var_controls = QHBoxLayout()
        self.add_var_btn = QPushButton("Add")
        self.edit_var_btn = QPushButton("Edit")
        self.remove_var_btn = QPushButton("Remove")
        
        var_controls.addWidget(self.add_var_btn)
        var_controls.addWidget(self.edit_var_btn)
        var_controls.addWidget(self.remove_var_btn)
        variables_layout.addLayout(var_controls)
        
        layout.addWidget(variables_group)
        
        # Validation group
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout(validation_group)
        
        self.validation_display = QTextEdit()
        self.validation_display.setMaximumHeight(100)
        self.validation_display.setReadOnly(True)
        validation_layout.addWidget(self.validation_display)
        
        layout.addWidget(validation_group)
        
        layout.addStretch()
        
        return panel
    
    def setup_menus(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New script
        new_action = QAction("New Script", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_script)
        file_menu.addAction(new_action)
        
        # Open script
        open_action = QAction("Open Script", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_script)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Save script
        save_action = QAction("Save Script", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_script)
        file_menu.addAction(save_action)
        
        # Save as
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_script_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Export
        export_action = QAction("Export Script", self)
        export_action.triggered.connect(self.export_script)
        file_menu.addAction(export_action)
        
        # Import
        import_action = QAction("Import Script", self)
        import_action.triggered.connect(self.import_script)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Close
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        # Validate
        validate_action = QAction("Validate Script", self)
        validate_action.setShortcut(QKeySequence("F7"))
        validate_action.triggered.connect(self.validate_script)
        edit_menu.addAction(validate_action)
        
        # Format
        format_action = QAction("Format Script", self)
        format_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        format_action.triggered.connect(self.format_script)
        edit_menu.addAction(format_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Switch to script editor
        script_view_action = QAction("Script Editor", self)
        script_view_action.setShortcut(QKeySequence("F1"))
        script_view_action.triggered.connect(lambda: self.edit_tabs.setCurrentIndex(0))
        view_menu.addAction(script_view_action)
        
        # Switch to node graph
        graph_view_action = QAction("Node Graph", self)
        graph_view_action.setShortcut(QKeySequence("F2"))
        graph_view_action.triggered.connect(lambda: self.edit_tabs.setCurrentIndex(1))
        view_menu.addAction(graph_view_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        # Test dialogue
        test_action = QAction("Test Dialogue", self)
        test_action.setShortcut(QKeySequence("F5"))
        test_action.triggered.connect(self.test_dialogue)
        tools_menu.addAction(test_action)
        
        # Asset manager
        assets_action = QAction("Asset Manager", self)
        assets_action.triggered.connect(self.open_asset_manager)
        tools_menu.addAction(assets_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # About
        about_action = QAction("About Dialogue Writer", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbars(self):
        """Setup toolbars"""
        # Main toolbar
        main_toolbar = self.addToolBar("Main")
        main_toolbar.setObjectName("MainToolBar")
        
        # File actions
        main_toolbar.addAction("New", self.new_script)
        main_toolbar.addAction("Open", self.open_script)
        main_toolbar.addAction("Save", self.save_script)
        main_toolbar.addSeparator()
        
        # Edit actions
        main_toolbar.addAction("Validate", self.validate_script)
        main_toolbar.addAction("Format", self.format_script)
        main_toolbar.addSeparator()
        
        # Preview actions
        main_toolbar.addAction("Play", self.play_preview)
        main_toolbar.addAction("Stop", self.stop_preview)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Script editor connections
        self.script_editor.script_changed.connect(self.on_script_changed)
        self.script_editor.node_selected.connect(self.on_node_selected)
        
        # Node graph connections
        self.node_graph.script_changed.connect(self.on_script_changed)
        self.node_graph.node_selected.connect(self.on_node_selected)
        
        # File list connections
        self.file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        self.new_file_btn.clicked.connect(self.new_script)
        self.open_file_btn.clicked.connect(self.open_script)
        self.delete_file_btn.clicked.connect(self.delete_script_file)
        
        # Asset connections
        self.refresh_assets_btn.clicked.connect(self.refresh_assets)
        
        # Preview connections
        self.play_btn.clicked.connect(self.play_preview)
        self.pause_btn.clicked.connect(self.pause_preview)
        self.stop_btn.clicked.connect(self.stop_preview)
        self.next_btn.clicked.connect(self.next_dialogue)
        
        # Variable connections
        self.add_var_btn.clicked.connect(self.add_variable)
        self.edit_var_btn.clicked.connect(self.edit_variable)
        self.remove_var_btn.clicked.connect(self.remove_variable)
        
        # Tab change connection
        self.edit_tabs.currentChanged.connect(self.on_tab_changed)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = self.statusBar()
        
        # Status labels
        self.file_status_label = QLabel("No file loaded")
        self.validation_status_label = QLabel("Ready")
        self.node_count_label = QLabel("0 nodes")
        
        self.status_bar.addWidget(self.file_status_label)
        self.status_bar.addPermanentWidget(self.validation_status_label)
        self.status_bar.addPermanentWidget(self.node_count_label)
    
    def ensure_dialogue_directories(self):
        """Ensure dialogue directories exist"""
        dialogue_dir = Path(self.project.project_path) / "dialogue"
        dialogue_dir.mkdir(exist_ok=True)
        
        (dialogue_dir / "scripts").mkdir(exist_ok=True)
        (dialogue_dir / "scenes").mkdir(exist_ok=True)
    
    def refresh_file_list(self):
        """Refresh the dialogue file list"""
        self.file_list.clear()
        
        dialogue_dir = Path(self.project.project_path) / "dialogue"
        if dialogue_dir.exists():
            # Add script files
            scripts_dir = dialogue_dir / "scripts"
            if scripts_dir.exists():
                for file_path in scripts_dir.glob("*.dlg"):
                    item = QListWidgetItem(file_path.stem)
                    item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                    self.file_list.addItem(item)
            
            # Add scene files
            scenes_dir = dialogue_dir / "scenes"
            if scenes_dir.exists():
                for file_path in scenes_dir.glob("*.dlg"):
                    item = QListWidgetItem(f"[Scene] {file_path.stem}")
                    item.setData(Qt.ItemDataRole.UserRole, str(file_path))
                    self.file_list.addItem(item)
    
    def refresh_assets(self):
        """Refresh asset lists"""
        # Clear lists
        self.backgrounds_list.clear()
        self.music_list.clear()
        self.sounds_list.clear()
        self.portraits_list.clear()
        
        # Populate backgrounds
        for bg in self.asset_resolver.get_available_backgrounds():
            self.backgrounds_list.addItem(bg)
        
        # Populate music
        for music in self.asset_resolver.get_available_music():
            self.music_list.addItem(music)
        
        # Populate sounds
        for sound in self.asset_resolver.get_available_sound_effects():
            self.sounds_list.addItem(sound)
        
        # Populate portraits
        portraits = self.asset_resolver.get_available_portraits()
        for character, emotions in portraits.items():
            for emotion in emotions:
                portrait_name = f"{character}_{emotion}" if emotion != 'neutral' else character
                self.portraits_list.addItem(portrait_name)

    def load_settings(self):
        """Load window settings"""
        self.restoreGeometry(self.settings.value("geometry", b""))
        self.restoreState(self.settings.value("windowState", b""))

        # Load recent files
        self.refresh_file_list()
        self.refresh_assets()

    def save_settings(self):
        """Save window settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def closeEvent(self, event):
        """Handle window close event"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                if not self.save_script():
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        self.save_settings()
        event.accept()

    def new_script(self):
        """Create a new dialogue script"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save before creating a new script?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                if not self.save_script():
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        # Get script name
        name, ok = QInputDialog.getText(self, "New Script", "Script name:")
        if not ok or not name:
            return

        # Create new script
        self.current_script = DialogueScript(filename=name)
        self.current_file_path = None
        self.is_modified = False

        # Update UI
        self.script_editor.set_script_text("", name)
        self.node_graph.set_script(self.current_script)
        self.update_status()

    def open_script(self):
        """Open an existing dialogue script"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save before opening another script?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                if not self.save_script():
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        # Open file dialog
        dialogue_dir = Path(self.project.project_path) / "dialogue"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Dialogue Script", str(dialogue_dir),
            "Dialogue Scripts (*.dlg);;All Files (*)"
        )

        if file_path:
            self.load_script_file(file_path)

    def load_script_file(self, file_path: str):
        """Load a script file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse script
            script = self.parser.parse_script(content)
            script.filename = Path(file_path).stem

            # Validate
            errors = self.parser.validate_script(script)
            if errors:
                QMessageBox.warning(
                    self, "Script Validation",
                    f"Script has validation errors:\n" + "\n".join(errors)
                )

            # Load into UI
            self.current_script = script
            self.current_file_path = file_path
            self.is_modified = False

            self.script_editor.set_script_text(content, script.filename)
            self.node_graph.set_script(script)
            self.update_status()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load script: {e}")

    def save_script(self) -> bool:
        """Save the current script"""
        if not self.current_file_path:
            return self.save_script_as()

        try:
            # Get script content
            script_text = self.script_editor.get_script_text()

            # Save to file
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(script_text)

            self.is_modified = False
            self.update_status()
            self.refresh_file_list()

            self.status_bar.showMessage("Script saved successfully", 2000)
            return True

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save script: {e}")
            return False

    def save_script_as(self) -> bool:
        """Save the script with a new name"""
        dialogue_dir = Path(self.project.project_path) / "dialogue" / "scripts"
        dialogue_dir.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Dialogue Script", str(dialogue_dir),
            "Dialogue Scripts (*.dlg);;All Files (*)"
        )

        if file_path:
            self.current_file_path = file_path
            return self.save_script()

        return False

    def on_script_changed(self):
        """Handle script content changes"""
        self.is_modified = True
        self.update_status()

        # Sync between editors
        sender = self.sender()
        if sender == self.script_editor:
            # Update node graph from script editor
            try:
                script_text = self.script_editor.get_script_text()
                if script_text.strip():
                    script = self.parser.parse_script(script_text)
                    self.current_script = script
                    self.node_graph.set_script(script)
            except Exception:
                pass  # Ignore parsing errors during editing

        elif sender == self.node_graph:
            # Update script editor from node graph
            if self.current_script:
                script_text = self.parser.script_to_text(self.current_script)
                self.script_editor.set_script_text(script_text, self.current_script.filename)

    def on_node_selected(self, node_id: str):
        """Handle node selection"""
        # Update preview if available
        if self.current_script and node_id in self.current_script.nodes:
            node = self.current_script.nodes[node_id]
            preview_text = f"Node: {node_id}\n"
            if node.speaker:
                preview_text += f"Speaker: {node.speaker}\n"
            if node.dialogue_lines:
                preview_text += "Dialogue:\n" + "\n".join(node.dialogue_lines)

            self.preview_display.setPlainText(preview_text)

    def on_tab_changed(self, index: int):
        """Handle tab changes between script editor and node graph"""
        # Sync content when switching tabs
        if index == 1:  # Switching to node graph
            try:
                script_text = self.script_editor.get_script_text()
                if script_text.strip():
                    script = self.parser.parse_script(script_text)
                    self.current_script = script
                    self.node_graph.set_script(script)
            except Exception as e:
                self.validation_display.setPlainText(f"Parse Error: {e}")

        elif index == 0:  # Switching to script editor
            if self.current_script:
                script_text = self.parser.script_to_text(self.current_script)
                self.script_editor.set_script_text(script_text, self.current_script.filename)

    def on_file_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on file list item"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.load_script_file(file_path)

    def delete_script_file(self):
        """Delete selected script file"""
        current_item = self.file_list.currentItem()
        if not current_item:
            return

        file_path = current_item.data(Qt.ItemDataRole.UserRole)
        if not file_path:
            return

        reply = QMessageBox.question(
            self, "Delete File",
            f"Are you sure you want to delete '{Path(file_path).name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                Path(file_path).unlink()
                self.refresh_file_list()
                self.status_bar.showMessage("File deleted successfully", 2000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete file: {e}")

    def validate_script(self):
        """Validate the current script"""
        try:
            script_text = self.script_editor.get_script_text()
            if not script_text.strip():
                self.validation_display.setPlainText("No script to validate")
                return

            script = self.parser.parse_script(script_text)
            errors = self.parser.validate_script(script)

            if errors:
                error_text = "Validation Errors:\n" + "\n".join(f"• {error}" for error in errors)
                self.validation_display.setPlainText(error_text)
                self.validation_status_label.setText("Validation Failed")
            else:
                self.validation_display.setPlainText("✓ Script is valid")
                self.validation_status_label.setText("Valid")

        except Exception as e:
            self.validation_display.setPlainText(f"Parse Error: {e}")
            self.validation_status_label.setText("Parse Error")

    def format_script(self):
        """Format the current script"""
        self.script_editor.format_script()

    def update_status(self):
        """Update status bar"""
        if self.current_file_path:
            file_name = Path(self.current_file_path).name
            status = f"{file_name}{'*' if self.is_modified else ''}"
        else:
            status = f"Untitled{'*' if self.is_modified else ''}"

        self.file_status_label.setText(status)

        # Update node count
        if self.current_script:
            node_count = len(self.current_script.nodes)
            self.node_count_label.setText(f"{node_count} nodes")
        else:
            self.node_count_label.setText("0 nodes")

    def play_preview(self):
        """Start dialogue preview"""
        try:
            script_text = self.script_editor.get_script_text()
            if not script_text.strip():
                QMessageBox.warning(self, "Warning", "No script to preview")
                return

            # Load script into runtime
            if self.runtime.load_script_from_text(script_text):
                # Set up callbacks
                self.runtime.set_callbacks(
                    on_dialogue_line=self.on_preview_dialogue,
                    on_choices_available=self.on_preview_choices,
                    on_dialogue_finished=self.on_preview_finished,
                    on_state_change=self.on_preview_state_change
                )

                # Start dialogue
                if self.runtime.start_dialogue():
                    self.play_btn.setEnabled(False)
                    self.pause_btn.setEnabled(True)
                    self.stop_btn.setEnabled(True)
                    self.next_btn.setEnabled(True)
                else:
                    QMessageBox.warning(self, "Warning", "Failed to start dialogue")
            else:
                QMessageBox.warning(self, "Warning", "Failed to load script for preview")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Preview error: {e}")

    def pause_preview(self):
        """Pause dialogue preview"""
        self.runtime.pause_dialogue()
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def stop_preview(self):
        """Stop dialogue preview"""
        self.runtime.stop_dialogue()
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.preview_display.clear()

    def next_dialogue(self):
        """Advance to next dialogue line"""
        self.runtime.advance_dialogue()

    def on_preview_dialogue(self, line: str, speaker: str = None):
        """Handle dialogue line in preview"""
        preview_text = ""
        if speaker:
            preview_text += f"{speaker}: "
        preview_text += line

        self.preview_display.append(preview_text)

    def on_preview_choices(self, choices: List[str]):
        """Handle choices in preview"""
        self.preview_display.append("\nChoices:")
        for i, choice in enumerate(choices):
            self.preview_display.append(f"{i + 1}. {choice}")

        # For now, auto-select first choice
        QTimer.singleShot(1000, lambda: self.runtime.make_choice(0))

    def on_preview_finished(self):
        """Handle dialogue finished in preview"""
        self.preview_display.append("\n[Dialogue Finished]")
        self.stop_preview()

    def on_preview_state_change(self, state):
        """Handle state change in preview"""
        self.validation_status_label.setText(f"Preview: {state.value}")

    def test_dialogue(self):
        """Test dialogue in a separate window"""
        # This could open a more comprehensive test window
        self.play_preview()

    def add_variable(self):
        """Add a new variable"""
        name, ok = QInputDialog.getText(self, "Add Variable", "Variable name:")
        if ok and name:
            # Add to variables list (this is just for display)
            self.variables_list.addItem(f"{name} = (undefined)")

    def edit_variable(self):
        """Edit selected variable"""
        current_item = self.variables_list.currentItem()
        if current_item:
            QMessageBox.information(self, "Edit Variable", "Variable editing not implemented yet")

    def remove_variable(self):
        """Remove selected variable"""
        current_row = self.variables_list.currentRow()
        if current_row >= 0:
            self.variables_list.takeItem(current_row)

    def export_script(self):
        """Export script to different format"""
        if not self.current_script:
            QMessageBox.warning(self, "Warning", "No script to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Script", "",
            "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                if file_path.endswith('.json'):
                    # Export as JSON
                    script_data = {
                        'filename': self.current_script.filename,
                        'nodes': {
                            node_id: {
                                'node_type': node.node_type.value,
                                'speaker': node.speaker,
                                'dialogue_lines': node.dialogue_lines,
                                'choices': [{'text': c.text, 'target_node': c.target_node, 'condition': c.condition} for c in node.choices],
                                'commands': node.commands,
                                'connections': node.connections,
                                'condition': node.condition
                            }
                            for node_id, node in self.current_script.nodes.items()
                        },
                        'start_node': self.current_script.start_node
                    }

                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(script_data, f, indent=2, ensure_ascii=False)
                else:
                    # Export as text
                    script_text = self.parser.script_to_text(self.current_script)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(script_text)

                self.status_bar.showMessage("Script exported successfully", 2000)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export script: {e}")

    def import_script(self):
        """Import script from different format"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Script", "",
            "JSON Files (*.json);;Text Files (*.txt *.dlg);;All Files (*)"
        )

        if file_path:
            try:
                if file_path.endswith('.json'):
                    # Import from JSON
                    with open(file_path, 'r', encoding='utf-8') as f:
                        script_data = json.load(f)

                    # Convert JSON to script format
                    script_text = self._json_to_script_text(script_data)
                else:
                    # Import from text
                    with open(file_path, 'r', encoding='utf-8') as f:
                        script_text = f.read()

                # Load into editor
                script = self.parser.parse_script(script_text)
                self.current_script = script
                self.current_file_path = None
                self.is_modified = True

                self.script_editor.set_script_text(script_text, script.filename)
                self.node_graph.set_script(script)
                self.update_status()

                self.status_bar.showMessage("Script imported successfully", 2000)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import script: {e}")

    def _json_to_script_text(self, script_data: Dict[str, Any]) -> str:
        """Convert JSON script data to script text format"""
        lines = []

        # Add filename
        if 'filename' in script_data:
            lines.append(f"FN : {script_data['filename']}")
            lines.append("")

        # Add nodes
        nodes = script_data.get('nodes', {})
        start_node = script_data.get('start_node')

        # Add start node first
        if start_node and start_node in nodes:
            lines.extend(self._json_node_to_text(start_node, nodes[start_node]))

        # Add remaining nodes
        for node_id, node_data in nodes.items():
            if node_id != start_node:
                lines.extend(self._json_node_to_text(node_id, node_data))

        return '\n'.join(lines)

    def _json_node_to_text(self, node_id: str, node_data: Dict[str, Any]) -> List[str]:
        """Convert JSON node data to text lines"""
        lines = []

        # Node declaration
        if node_data.get('condition'):
            lines.append(f"{node_id} if {node_data['condition']}")
        else:
            lines.append(node_id)

        # Speaker
        if node_data.get('speaker'):
            lines.append(node_data['speaker'])

        # Dialogue lines
        for line in node_data.get('dialogue_lines', []):
            lines.append(line)

        # Commands
        for command in node_data.get('commands', []):
            lines.append(f"[[{command}]]")

        # Choices
        for choice in node_data.get('choices', []):
            lines.append(f"[{choice['text']}|{choice['target_node']}]")

        # Connections
        for connection in node_data.get('connections', []):
            lines.append(f"[{connection}]")

        lines.append("")  # Empty line after node
        return lines

    def open_asset_manager(self):
        """Open asset manager (placeholder)"""
        QMessageBox.information(self, "Asset Manager", "Asset manager not implemented yet")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About Dialogue Writer",
            "Dialogue Writer for Lupine Engine\n\n"
            "A comprehensive tool for creating and editing dialogue scripts\n"
            "with Ren'py-style syntax and visual node graph editing.\n\n"
            "Features:\n"
            "• Dual-mode editing (script and visual)\n"
            "• Real-time validation\n"
            "• Asset integration\n"
            "• Preview system\n"
            "• Export/Import support"
        )
