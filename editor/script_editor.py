"""
Script Editor Widget for Lupine Engine
Provides LSC script editing with syntax highlighting and code completion
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit, 
    QPushButton, QFileDialog, QMessageBox, QLabel, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont, 
    QTextDocument, QKeySequence, QAction
)
import re

from core.project import LupineProject


class LSCSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for LSC (Lupine Script) language"""
    
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self.setup_highlighting_rules()
    
    def setup_highlighting_rules(self):
        """Setup syntax highlighting rules"""
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))  # Blue
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            "class", "extends", "func", "var", "const", "if", "else", "elif",
            "for", "while", "do", "break", "continue", "return", "pass",
            "and", "or", "not", "in", "is", "true", "false", "null",
            "export", "export_group", "signal", "enum", "tool", "onready",
            "self", "super", "yield", "await", "match", "when"
        ]
        
        for keyword in keywords:
            pattern = f"\\b{keyword}\\b"
            self.highlighting_rules.append((re.compile(pattern), keyword_format))
        
        # Built-in functions
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#dcdcaa"))  # Yellow
        
        builtins = [
            "print", "len", "range", "str", "int", "float", "bool",
            "get_node", "find_node", "add_child", "remove_child",
            "connect", "disconnect", "emit_signal", "has_method",
            "call", "call_deferred", "set_process", "set_physics_process"
        ]
        
        for builtin in builtins:
            pattern = f"\\b{builtin}\\b"
            self.highlighting_rules.append((re.compile(pattern), builtin_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))  # Orange
        
        # Double quoted strings
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        # Single quoted strings
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))  # Light green
        
        self.highlighting_rules.append((re.compile(r"\\b\\d+(\\.\\d+)?\\b"), number_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))  # Green
        comment_format.setFontItalic(True)
        
        self.highlighting_rules.append((re.compile(r"#[^\\n]*"), comment_format))
        
        # Function definitions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))  # Yellow
        function_format.setFontWeight(QFont.Weight.Bold)
        
        self.highlighting_rules.append((re.compile(r"\\bfunc\\s+(\\w+)"), function_format))
        
        # Class definitions
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4ec9b0"))  # Cyan
        class_format.setFontWeight(QFont.Weight.Bold)
        
        self.highlighting_rules.append((re.compile(r"\\bclass\\s+(\\w+)"), class_format))
        
        # Export variables
        export_format = QTextCharFormat()
        export_format.setForeground(QColor("#c586c0"))  # Purple
        export_format.setFontWeight(QFont.Weight.Bold)
        
        self.highlighting_rules.append((re.compile(r"\\bexport\\b"), export_format))
        self.highlighting_rules.append((re.compile(r"\\bexport_group\\b"), export_format))
    
    def highlightBlock(self, text: str):
        """Apply syntax highlighting to a block of text"""
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)


class ScriptEditorTab(QWidget):
    """Individual script editor tab"""
    
    content_changed = pyqtSignal(str)  # file_path
    
    def __init__(self, file_path: str = None, content: str = ""):
        super().__init__()
        self.file_path = file_path
        self.is_modified = False
        self.setup_ui()
        
        if content:
            self.text_edit.setPlainText(content)
        elif file_path and os.path.exists(file_path):
            self.load_file()
    
    def setup_ui(self):
        """Setup the UI for the script tab"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setTabStopDistance(40)  # 4 spaces
        self.text_edit.textChanged.connect(self.on_text_changed)
        
        # Apply syntax highlighting
        self.highlighter = LSCSyntaxHighlighter(self.text_edit.document())
        
        layout.addWidget(self.text_edit)
    
    def load_file(self):
        """Load file content"""
        if not self.file_path or not os.path.exists(self.file_path):
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text_edit.setPlainText(content)
            self.is_modified = False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
    
    def save_file(self) -> bool:
        """Save file content"""
        if not self.file_path:
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.text_edit.toPlainText())
            
            self.is_modified = False
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
            return False
    
    def on_text_changed(self):
        """Handle text change"""
        self.is_modified = True
        if self.file_path:
            self.content_changed.emit(self.file_path)
    
    def get_content(self) -> str:
        """Get current content"""
        return self.text_edit.toPlainText()
    
    def set_content(self, content: str):
        """Set content"""
        self.text_edit.setPlainText(content)
        self.is_modified = False


class ScriptEditorWidget(QWidget):
    """Main script editor widget with tabs"""
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.open_files = {}  # file_path -> tab_index
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.new_script_btn = QPushButton("New Script")
        self.new_script_btn.clicked.connect(self.new_script)
        toolbar_layout.addWidget(self.new_script_btn)
        
        self.open_script_btn = QPushButton("Open Script")
        self.open_script_btn.clicked.connect(self.open_script)
        toolbar_layout.addWidget(self.open_script_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_current)
        toolbar_layout.addWidget(self.save_btn)
        
        self.save_all_btn = QPushButton("Save All")
        self.save_all_btn.clicked.connect(self.save_all)
        toolbar_layout.addWidget(self.save_all_btn)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        layout.addWidget(self.tab_widget)
        
        # Show welcome message if no tabs
        self.show_welcome_tab()
    
    def show_welcome_tab(self):
        """Show welcome tab when no scripts are open"""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome_label = QLabel("LSC Script Editor")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #8b5fbf;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        
        info_label = QLabel("Create a new script or open an existing one to start editing")
        info_label.setStyleSheet("color: #b0b0b0; margin-top: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(info_label)
        
        self.tab_widget.addTab(welcome_widget, "Welcome")
    
    def new_script(self):
        """Create a new script"""
        # Default LSC script template
        template = '''# LSC Script
# Lupine Scripting Language

extends Node2D

# Export variables (shown in inspector)
export var speed: float = 100.0
export var health: int = 100

# Called when the node enters the scene tree
func _ready():
    print("Script ready!")

# Called every frame
func _process(delta: float):
    # Update logic here
    pass

# Called for physics updates
func _physics_process(delta: float):
    # Physics logic here
    pass
'''
        
        # Remove welcome tab if it exists
        if self.tab_widget.count() == 1 and self.tab_widget.tabText(0) == "Welcome":
            self.tab_widget.removeTab(0)
        
        # Create new tab
        script_tab = ScriptEditorTab(content=template)
        script_tab.content_changed.connect(self.on_content_changed)
        
        tab_index = self.tab_widget.addTab(script_tab, "New Script*")
        self.tab_widget.setCurrentIndex(tab_index)
    
    def open_script(self):
        """Open an existing script"""
        scripts_dir = self.project.get_absolute_path("scripts")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Script", str(scripts_dir), "LSC Scripts (*.lsc);;All Files (*)"
        )
        
        if file_path:
            self.open_script_file(file_path)
    
    def open_script_file(self, file_path: str):
        """Open a specific script file"""
        # Check if already open
        if file_path in self.open_files:
            self.tab_widget.setCurrentIndex(self.open_files[file_path])
            return
        
        # Remove welcome tab if it exists
        if self.tab_widget.count() == 1 and self.tab_widget.tabText(0) == "Welcome":
            self.tab_widget.removeTab(0)
        
        # Create new tab
        script_tab = ScriptEditorTab(file_path)
        script_tab.content_changed.connect(self.on_content_changed)
        
        file_name = os.path.basename(file_path)
        tab_index = self.tab_widget.addTab(script_tab, file_name)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Track open file
        self.open_files[file_path] = tab_index
    
    def close_tab(self, index: int):
        """Close a tab"""
        widget = self.tab_widget.widget(index)
        
        if isinstance(widget, ScriptEditorTab):
            # Check if modified
            if widget.is_modified:
                reply = QMessageBox.question(
                    self, "Unsaved Changes",
                    "The script has unsaved changes. Do you want to save before closing?",
                    QMessageBox.StandardButton.Save | 
                    QMessageBox.StandardButton.Discard | 
                    QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Save:
                    if not self.save_tab(index):
                        return  # Don't close if save failed
                elif reply == QMessageBox.StandardButton.Cancel:
                    return  # Don't close
            
            # Remove from open files tracking
            if widget.file_path in self.open_files:
                del self.open_files[widget.file_path]
        
        self.tab_widget.removeTab(index)
        
        # Show welcome tab if no tabs left
        if self.tab_widget.count() == 0:
            self.show_welcome_tab()
    
    def save_current(self):
        """Save current tab"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.save_tab(current_index)
    
    def save_tab(self, index: int) -> bool:
        """Save a specific tab"""
        widget = self.tab_widget.widget(index)
        
        if not isinstance(widget, ScriptEditorTab):
            return False
        
        if not widget.file_path:
            # Need to save as
            scripts_dir = self.project.get_absolute_path("scripts")
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Script", str(scripts_dir), "LSC Scripts (*.lsc)"
            )
            
            if not file_path:
                return False
            
            widget.file_path = file_path
            
            # Update tab title
            file_name = os.path.basename(file_path)
            self.tab_widget.setTabText(index, file_name)
            
            # Track open file
            self.open_files[file_path] = index
        
        return widget.save_file()
    
    def save_all(self):
        """Save all open tabs"""
        for i in range(self.tab_widget.count()):
            self.save_tab(i)
    
    def on_content_changed(self, file_path: str):
        """Handle content change in a tab"""
        if file_path in self.open_files:
            index = self.open_files[file_path]
            current_text = self.tab_widget.tabText(index)
            if not current_text.endswith("*"):
                self.tab_widget.setTabText(index, current_text + "*")
