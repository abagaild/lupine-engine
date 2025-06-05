"""
Dialogue Script Editor Component
Text editor with syntax highlighting for Ren'py-style dialogue scripts
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QSplitter, QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont,
    QTextCursor, QTextDocument
)
import re
from typing import Dict, List, Any, Optional

from core.dialogue.dialogue_parser import DialogueParser, DialogueScript


class DialogueSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for dialogue scripts"""
    
    def __init__(self, document: QTextDocument):
        super().__init__(document)
        
        # Define highlighting rules
        self.highlighting_rules = []
        
        # Node ID format
        node_format = QTextCharFormat()
        node_format.setForeground(QColor(100, 150, 255))
        node_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'^[a-zA-Z0-9_]+(\s+if\s+.+)?$', node_format))
        
        # Commands format
        command_format = QTextCharFormat()
        command_format.setForeground(QColor(255, 150, 100))
        command_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'\[\[.+?\]\]', command_format))
        
        # Choices format
        choice_format = QTextCharFormat()
        choice_format.setForeground(QColor(150, 255, 150))
        self.highlighting_rules.append((r'\[.+?\|.+?\]', choice_format))
        
        # Simple connections format
        connection_format = QTextCharFormat()
        connection_format.setForeground(QColor(200, 200, 255))
        self.highlighting_rules.append((r'^\[.+?\]$', connection_format))
        
        # Speaker format
        speaker_format = QTextCharFormat()
        speaker_format.setForeground(QColor(255, 255, 100))
        speaker_format.setFontWeight(QFont.Weight.Bold)
        # This is tricky to detect, we'll handle it in highlightBlock
        
        # Comments format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(128, 128, 128))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((r'#.*', comment_format))
        
        # FN declaration format
        fn_format = QTextCharFormat()
        fn_format.setForeground(QColor(255, 100, 255))
        fn_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'^FN\s*:.*', fn_format))
        
        # End keyword format
        end_format = QTextCharFormat()
        end_format.setForeground(QColor(255, 100, 100))
        end_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((r'^end$', end_format))
    
    def highlightBlock(self, text: str):
        """Apply syntax highlighting to a block of text"""
        # Apply all rules
        for pattern, format_obj in self.highlighting_rules:
            regex = re.compile(pattern, re.MULTILINE)
            for match in regex.finditer(text):
                start = match.start()
                length = match.end() - match.start()
                self.setFormat(start, length, format_obj)


class DialogueScriptEditor(QWidget):
    """Text editor for dialogue scripts with syntax highlighting"""
    
    # Signals
    script_changed = pyqtSignal(str)  # Emitted when script content changes
    node_selected = pyqtSignal(str)   # Emitted when a node is selected
    
    def __init__(self):
        super().__init__()
        self.parser = DialogueParser()
        self.current_script: Optional[DialogueScript] = None
        self._updating_from_external = False
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.validate_button = QPushButton("Validate Script")
        self.format_button = QPushButton("Format Script")
        self.clear_button = QPushButton("Clear")
        
        toolbar_layout.addWidget(self.validate_button)
        toolbar_layout.addWidget(self.format_button)
        toolbar_layout.addWidget(self.clear_button)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Main content area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Script editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        # Script name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Script Name:"))
        self.script_name_edit = QLineEdit()
        self.script_name_edit.setPlaceholderText("Enter script filename...")
        name_layout.addWidget(self.script_name_edit)
        editor_layout.addLayout(name_layout)
        
        # Text editor
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Consolas", 10))
        self.text_editor.setPlaceholderText(self._get_example_script())
        
        # Apply syntax highlighting
        self.highlighter = DialogueSyntaxHighlighter(self.text_editor.document())
        
        editor_layout.addWidget(self.text_editor)
        
        # Validation results
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("color: red; font-weight: bold;")
        self.validation_label.hide()
        editor_layout.addWidget(self.validation_label)
        
        splitter.addWidget(editor_widget)
        
        # Right side - Node outline and tools
        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        
        # Node outline
        outline_group = QGroupBox("Script Outline")
        outline_layout = QVBoxLayout(outline_group)
        
        self.node_list = QListWidget()
        self.node_list.setMaximumWidth(250)
        outline_layout.addWidget(self.node_list)
        
        tools_layout.addWidget(outline_group)
        
        # Quick insert tools
        insert_group = QGroupBox("Quick Insert")
        insert_layout = QVBoxLayout(insert_group)
        
        # Command buttons
        commands = [
            ("Background", "[[background ]]"),
            ("Set Left", "[[setLeft ]]"),
            ("Set Right", "[[setRight ]]"),
            ("Play Music", "[[playMusic ]]"),
            ("Play Sound", "[[playSound ]]"),
            ("Variable", "[[var  = ]]"),
            ("Signal", "[[signal ]]"),
            ("Choice", "[Choice Text|target_node]"),
            ("Connection", "[target_node]")
        ]
        
        for name, template in commands:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, t=template: self.insert_template(t))
            insert_layout.addWidget(btn)
        
        tools_layout.addWidget(insert_group)
        tools_layout.addStretch()
        
        splitter.addWidget(tools_widget)
        
        # Set splitter proportions
        splitter.setSizes([600, 250])
    
    def setup_connections(self):
        """Setup signal connections"""
        self.text_editor.textChanged.connect(self.on_text_changed)
        self.script_name_edit.textChanged.connect(self.on_script_name_changed)
        self.node_list.itemClicked.connect(self.on_node_selected)
        
        self.validate_button.clicked.connect(self.validate_script)
        self.format_button.clicked.connect(self.format_script)
        self.clear_button.clicked.connect(self.clear_script)
        
        # Auto-validation timer
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.validate_script)
    
    def on_text_changed(self):
        """Handle text editor changes"""
        if self._updating_from_external:
            return
        
        # Start validation timer
        self.validation_timer.start(1000)  # Validate after 1 second of no changes
        
        # Update script outline
        self.update_script_outline()
        
        # Emit signal
        self.script_changed.emit(self.get_script_text())
    
    def on_script_name_changed(self):
        """Handle script name changes"""
        if not self._updating_from_external:
            self.script_changed.emit(self.get_script_text())
    
    def on_node_selected(self, item: QListWidgetItem):
        """Handle node selection in outline"""
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self.node_selected.emit(node_id)
            self.jump_to_node(node_id)
    
    def set_script_text(self, text: str, script_name: str = ""):
        """Set the script text content"""
        self._updating_from_external = True
        try:
            self.text_editor.setPlainText(text)
            if script_name:
                self.script_name_edit.setText(script_name)
            self.update_script_outline()
            self.validate_script()
        finally:
            self._updating_from_external = False
    
    def get_script_text(self) -> str:
        """Get the current script text"""
        script_name = self.script_name_edit.text().strip()
        content = self.text_editor.toPlainText()
        
        # Add FN declaration if not present and script name is provided
        if script_name and not content.startswith("FN :"):
            content = f"FN : {script_name}\n\n{content}"
        
        return content
    
    def insert_template(self, template: str):
        """Insert a template at the current cursor position"""
        cursor = self.text_editor.textCursor()
        cursor.insertText(template)
        
        # Position cursor for editing (find first space or between brackets)
        if " " in template:
            # Move cursor to after the space
            pos = template.find(" ") + 1
            cursor.setPosition(cursor.position() - len(template) + pos)
            self.text_editor.setTextCursor(cursor)
    
    def validate_script(self):
        """Validate the current script"""
        try:
            script_text = self.get_script_text()
            if not script_text.strip():
                self.validation_label.hide()
                return
            
            script = self.parser.parse_script(script_text)
            errors = self.parser.validate_script(script)
            
            if errors:
                error_text = "Validation Errors:\n" + "\n".join(f"• {error}" for error in errors)
                self.validation_label.setText(error_text)
                self.validation_label.setStyleSheet("color: red; font-weight: bold;")
                self.validation_label.show()
            else:
                self.validation_label.setText("✓ Script is valid")
                self.validation_label.setStyleSheet("color: green; font-weight: bold;")
                self.validation_label.show()
                
                # Hide after 3 seconds if valid
                QTimer.singleShot(3000, self.validation_label.hide)
            
            self.current_script = script
            
        except Exception as e:
            self.validation_label.setText(f"Parse Error: {str(e)}")
            self.validation_label.setStyleSheet("color: red; font-weight: bold;")
            self.validation_label.show()
    
    def format_script(self):
        """Format the current script"""
        try:
            script_text = self.get_script_text()
            if not script_text.strip():
                return
            
            script = self.parser.parse_script(script_text)
            formatted_text = self.parser.script_to_text(script)
            
            self._updating_from_external = True
            try:
                self.text_editor.setPlainText(formatted_text)
                self.update_script_outline()
            finally:
                self._updating_from_external = False
            
        except Exception as e:
            self.validation_label.setText(f"Format Error: {str(e)}")
            self.validation_label.setStyleSheet("color: red; font-weight: bold;")
            self.validation_label.show()
    
    def clear_script(self):
        """Clear the script content"""
        self.text_editor.clear()
        self.script_name_edit.clear()
        self.node_list.clear()
        self.validation_label.hide()
    
    def update_script_outline(self):
        """Update the script outline list"""
        self.node_list.clear()
        
        try:
            script_text = self.get_script_text()
            if not script_text.strip():
                return
            
            script = self.parser.parse_script(script_text)
            
            for node_id, node in script.nodes.items():
                item_text = node_id
                if node.condition:
                    item_text += f" (if {node.condition})"
                
                if node.speaker:
                    item_text += f" - {node.speaker}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, node_id)
                
                # Color code by node type
                if node.node_type.value == "choice":
                    item.setForeground(QColor(150, 255, 150))
                elif node.node_type.value == "end":
                    item.setForeground(QColor(255, 100, 100))
                else:
                    item.setForeground(QColor(200, 200, 255))
                
                self.node_list.addItem(item)
                
        except Exception:
            # Ignore parsing errors during outline update
            pass
    
    def jump_to_node(self, node_id: str):
        """Jump to a specific node in the text editor"""
        text = self.text_editor.toPlainText()
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == node_id or line.strip().startswith(f"{node_id} if"):
                # Move cursor to this line
                cursor = self.text_editor.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, i)
                self.text_editor.setTextCursor(cursor)
                self.text_editor.ensureCursorVisible()
                break
    
    def _get_example_script(self) -> str:
        """Get example script text for placeholder"""
        return """FN : Example Conversation

[[background forest_clearing]]
[[setLeft Char1_neutral]]
[[setRight Char2_neutral]]

1_1
Char1
Hello there! How are you doing today?
[Good!|2_1]
[Not so great...|2_2]

2_1
Char2_happy
That's wonderful to hear!
[[var mood = good]]
[3_1]

2_2
Char2_sad
Oh, I'm sorry to hear that.
[[var mood = bad]]
[3_1]

3_1 if mood = good
Char2_happy
I'm doing great as well!
[[signal conversation_positive]]
[end]

3_1 if mood = bad
Char2_neutral
Well, I hope things get better for you.
[[signal conversation_neutral]]
[end]"""
