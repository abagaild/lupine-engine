"""
Notepad Tool for Lupine Engine
Provides multi-tab text editor with optional Python syntax highlighting
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTextEdit, QPushButton, QLabel, QLineEdit, QComboBox,
    QGroupBox, QMessageBox, QFileDialog, QInputDialog,
    QCheckBox, QMenuBar, QMenu, QToolBar, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat,
    QAction, QKeySequence, QTextDocument
)
import re

from core.project import LupineProject


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Python syntax highlighter for the text editor"""
    
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self.setup_highlighting_rules()
        
    def setup_highlighting_rules(self):
        """Setup syntax highlighting rules for Python"""
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(0, 0, 255))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
            'while', 'with', 'yield', 'None', 'True', 'False'
        ]
        
        for keyword in keywords:
            pattern = f'\\b{keyword}\\b'
            self.highlighting_rules.append((re.compile(pattern), keyword_format))
            
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(0, 128, 0))
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(128, 128, 128))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((re.compile(r'#[^\n]*'), comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(255, 0, 255))
        self.highlighting_rules.append((re.compile(r'\b\d+\.?\d*\b'), number_format))
        
        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(0, 128, 128))
        function_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((re.compile(r'\bdef\s+(\w+)'), function_format))
        
        # Classes
        class_format = QTextCharFormat()
        class_format.setForeground(QColor(128, 0, 128))
        class_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((re.compile(r'\bclass\s+(\w+)'), class_format))
        
    def highlightBlock(self, text: str):
        """Apply syntax highlighting to a block of text"""
        for pattern, format_obj in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)


class NotepadTab(QWidget):
    """Individual notepad tab"""
    
    content_changed = pyqtSignal(str)  # tab_id
    title_changed = pyqtSignal(str, str)  # tab_id, new_title
    
    def __init__(self, tab_id: str, title: str = "New Note", content: str = "", 
                 python_highlighting: bool = False):
        super().__init__()
        self.tab_id = tab_id
        self.title = title
        self.is_modified = False
        self.python_highlighting = python_highlighting
        self.setup_ui()
        
        if content:
            self.text_edit.setPlainText(content)
            self.is_modified = False
            
    def setup_ui(self):
        """Setup the tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Header with title and options
        header_layout = QHBoxLayout()
        
        self.title_edit = QLineEdit(self.title)
        self.title_edit.editingFinished.connect(self.on_title_changed)
        header_layout.addWidget(QLabel("Title:"))
        header_layout.addWidget(self.title_edit)
        
        self.python_checkbox = QCheckBox("Python Syntax Highlighting")
        self.python_checkbox.setChecked(self.python_highlighting)
        self.python_checkbox.toggled.connect(self.toggle_python_highlighting)
        header_layout.addWidget(self.python_checkbox)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.textChanged.connect(self.on_text_changed)
        
        # Apply syntax highlighting if enabled
        if self.python_highlighting:
            self.highlighter = PythonSyntaxHighlighter(self.text_edit.document())
        else:
            self.highlighter = None
            
        layout.addWidget(self.text_edit)
        
    def toggle_python_highlighting(self, enabled: bool):
        """Toggle Python syntax highlighting"""
        self.python_highlighting = enabled
        
        if enabled and not self.highlighter:
            self.highlighter = PythonSyntaxHighlighter(self.text_edit.document())
        elif not enabled and self.highlighter:
            self.highlighter.setDocument(None)
            self.highlighter = None
            
        self.mark_modified()
        
    def on_title_changed(self):
        """Handle title change"""
        new_title = self.title_edit.text().strip()
        if new_title and new_title != self.title:
            self.title = new_title
            self.title_changed.emit(self.tab_id, new_title)
            self.mark_modified()
            
    def on_text_changed(self):
        """Handle text change"""
        self.mark_modified()
        
    def mark_modified(self):
        """Mark the tab as modified"""
        if not self.is_modified:
            self.is_modified = True
            self.content_changed.emit(self.tab_id)
            
    def get_content(self) -> str:
        """Get current content"""
        return self.text_edit.toPlainText()
        
    def set_content(self, content: str):
        """Set content"""
        self.text_edit.setPlainText(content)
        self.is_modified = False
        
    def get_data(self) -> Dict:
        """Get tab data for saving"""
        return {
            "id": self.tab_id,
            "title": self.title,
            "content": self.get_content(),
            "python_highlighting": self.python_highlighting,
            "created_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        }


class NotepadWidget(QWidget):
    """Main notepad widget with tab management"""
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.tabs_data: Dict[str, Dict] = {}
        self.setup_ui()
        self.load_notes()
        
    def setup_ui(self):
        """Setup the notepad UI"""
        layout = QVBoxLayout(self)
        
        # Tab controls
        controls_layout = QHBoxLayout()
        
        self.new_tab_btn = QPushButton("New Note")
        self.new_tab_btn.clicked.connect(self.new_tab)
        
        self.save_tab_btn = QPushButton("Save Note")
        self.save_tab_btn.clicked.connect(self.save_current_tab)
        
        self.save_all_btn = QPushButton("Save All")
        self.save_all_btn.clicked.connect(self.save_all_tabs)
        
        self.export_btn = QPushButton("Export Note")
        self.export_btn.clicked.connect(self.export_current_tab)
        
        self.import_btn = QPushButton("Import Note")
        self.import_btn.clicked.connect(self.import_note)
        
        controls_layout.addWidget(self.new_tab_btn)
        controls_layout.addWidget(self.save_tab_btn)
        controls_layout.addWidget(self.save_all_btn)
        controls_layout.addWidget(self.export_btn)
        controls_layout.addWidget(self.import_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
        
    def load_notes(self):
        """Load saved notes"""
        notes_file = Path(self.project.project_path) / "data" / "notes.json"
        
        if notes_file.exists():
            try:
                with open(notes_file, 'r') as f:
                    data = json.load(f)
                    notes = data.get("notes", [])
                    
                    for note_data in notes:
                        self.create_tab_from_data(note_data)
            except Exception as e:
                print(f"Error loading notes: {e}")
                
        # If no notes exist, create a default one
        if self.tab_widget.count() == 0:
            self.new_tab()
            
    def save_notes(self):
        """Save all notes to project data"""
        notes_file = Path(self.project.project_path) / "data" / "notes.json"
        notes_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Collect all tab data
        notes = []
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, NotepadTab):
                notes.append(tab.get_data())
                
        data = {
            "notes": notes,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(notes_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save notes: {e}")
            
    def new_tab(self):
        """Create a new notepad tab"""
        tab_id = str(datetime.now().timestamp())
        title = f"Note {self.tab_widget.count() + 1}"
        
        tab = NotepadTab(tab_id, title)
        tab.content_changed.connect(self.on_tab_content_changed)
        tab.title_changed.connect(self.on_tab_title_changed)
        
        index = self.tab_widget.addTab(tab, title)
        self.tab_widget.setCurrentIndex(index)
        
        return tab
        
    def create_tab_from_data(self, note_data: Dict):
        """Create a tab from saved data"""
        tab = NotepadTab(
            note_data.get("id", str(datetime.now().timestamp())),
            note_data.get("title", "Untitled"),
            note_data.get("content", ""),
            note_data.get("python_highlighting", False)
        )
        
        tab.content_changed.connect(self.on_tab_content_changed)
        tab.title_changed.connect(self.on_tab_title_changed)
        
        self.tab_widget.addTab(tab, note_data.get("title", "Untitled"))
        
    def close_tab(self, index: int):
        """Close a tab"""
        tab = self.tab_widget.widget(index)
        if isinstance(tab, NotepadTab) and tab.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                f"Note '{tab.title}' has unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.save_tab(tab)
            elif reply == QMessageBox.StandardButton.Cancel:
                return
                
        self.tab_widget.removeTab(index)
        
        # Create a new tab if all tabs are closed
        if self.tab_widget.count() == 0:
            self.new_tab()
            
    def on_tab_changed(self, index: int):
        """Handle tab change"""
        pass  # Could be used for additional functionality
        
    def on_tab_content_changed(self, tab_id: str):
        """Handle tab content change"""
        # Find the tab and update its display
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, NotepadTab) and tab.tab_id == tab_id:
                title = tab.title
                if tab.is_modified:
                    title += " *"
                self.tab_widget.setTabText(i, title)
                break
                
    def on_tab_title_changed(self, tab_id: str, new_title: str):
        """Handle tab title change"""
        # Find the tab and update its display
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, NotepadTab) and tab.tab_id == tab_id:
                display_title = new_title
                if tab.is_modified:
                    display_title += " *"
                self.tab_widget.setTabText(i, display_title)
                break
                
    def save_current_tab(self):
        """Save the current tab"""
        current_tab = self.tab_widget.currentWidget()
        if isinstance(current_tab, NotepadTab):
            self.save_tab(current_tab)
            
    def save_tab(self, tab: NotepadTab):
        """Save a specific tab"""
        tab.is_modified = False
        self.on_tab_content_changed(tab.tab_id)  # Update display
        self.save_notes()  # Save all notes
        
    def save_all_tabs(self):
        """Save all tabs"""
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, NotepadTab):
                tab.is_modified = False
                self.on_tab_content_changed(tab.tab_id)
                
        self.save_notes()
        QMessageBox.information(self, "Saved", "All notes have been saved.")
        
    def auto_save(self):
        """Auto-save all modified tabs"""
        has_modified = False
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if isinstance(tab, NotepadTab) and tab.is_modified:
                has_modified = True
                break
                
        if has_modified:
            self.save_notes()
            
    def export_current_tab(self):
        """Export current tab to a file"""
        current_tab = self.tab_widget.currentWidget()
        if isinstance(current_tab, NotepadTab):
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Note", f"{current_tab.title}.txt", 
                "Text Files (*.txt);;Python Files (*.py);;All Files (*.*)"
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(current_tab.get_content())
                    QMessageBox.information(self, "Exported", f"Note exported to {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export note: {e}")
                    
    def import_note(self):
        """Import a note from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Note", "", 
            "Text Files (*.txt);;Python Files (*.py);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Create new tab with imported content
                tab = self.new_tab()
                tab.set_content(content)
                
                # Set title based on filename
                filename = Path(file_path).stem
                tab.title = filename
                tab.title_edit.setText(filename)
                self.on_tab_title_changed(tab.tab_id, filename)
                
                # Enable Python highlighting for .py files
                if file_path.endswith('.py'):
                    tab.python_checkbox.setChecked(True)
                    tab.toggle_python_highlighting(True)
                    
                QMessageBox.information(self, "Imported", f"Note imported from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import note: {e}")


class NotepadWindow(QMainWindow):
    """Main Notepad window"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_window()
        self.setup_ui()
        
    def setup_window(self):
        """Setup the window"""
        self.setWindowTitle("Notepad - Lupine Engine")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Project info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"Project: {self.project.config.get('name', 'Unknown')}"))
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Notepad widget
        self.notepad_widget = NotepadWidget(self.project)
        layout.addWidget(self.notepad_widget)
