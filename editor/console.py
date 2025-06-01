"""
Console/Output Widget for Lupine Engine
Displays engine output, errors, and provides interactive console
"""

import sys
import io
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, 
    QHBoxLayout, QComboBox, QLabel
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCursor, QFont, QColor


class ConsoleWidget(QWidget):
    """Console widget for output and interactive commands"""
    
    command_executed = pyqtSignal(str)  # Emitted when a command is executed
    
    def __init__(self):
        super().__init__()
        self.command_history = []
        self.history_index = -1
        self.setup_ui()
        self.setup_output_capture()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        # Filter combo
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Info", "Warning", "Error", "Debug"])
        self.filter_combo.currentTextChanged.connect(self.filter_messages)
        header_layout.addWidget(QLabel("Filter:"))
        header_layout.addWidget(self.filter_combo)
        
        header_layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_output)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #555555;
            }
        """)
        layout.addWidget(self.output_text)
        
        # Command input
        input_layout = QHBoxLayout()
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter LSC command or Python expression...")
        self.command_input.returnPressed.connect(self.execute_command)
        self.command_input.keyPressEvent = self.handle_input_key
        input_layout.addWidget(self.command_input)
        
        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(execute_btn)
        
        layout.addLayout(input_layout)
        
        # Welcome message
        self.log_info("Lupine Engine Console Ready")
        self.log_info("Type LSC commands or Python expressions")
        self.log_info("Use 'help' for available commands")
    
    def setup_output_capture(self):
        """Setup stdout/stderr capture"""
        # Store original streams
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Create custom streams
        self.stdout_capture = OutputCapture(self.log_info)
        self.stderr_capture = OutputCapture(self.log_error)
        
        # Redirect streams
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
    
    def restore_output_capture(self):
        """Restore original stdout/stderr"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
    
    def handle_input_key(self, event):
        """Handle special keys in command input"""
        if event.key() == Qt.Key.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key.Key_Down:
            self.navigate_history(1)
        else:
            # Call original keyPressEvent
            QLineEdit.keyPressEvent(self.command_input, event)
    
    def navigate_history(self, direction: int):
        """Navigate command history"""
        if not self.command_history:
            return
        
        self.history_index += direction
        self.history_index = max(-1, min(len(self.command_history) - 1, self.history_index))
        
        if self.history_index >= 0:
            self.command_input.setText(self.command_history[self.history_index])
        else:
            self.command_input.clear()
    
    def execute_command(self):
        """Execute the command in the input field"""
        command = self.command_input.text().strip()
        if not command:
            return
        
        # Add to history
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = -1
        
        # Clear input
        self.command_input.clear()
        
        # Log command
        self.log_command(command)
        
        # Execute command
        try:
            if command.startswith("help"):
                self.show_help()
            elif command.startswith("clear"):
                self.clear_output()
            elif command.startswith("lsc "):
                # Execute LSC command
                lsc_code = command[4:]
                self.execute_lsc(lsc_code)
            else:
                # Execute as Python expression
                self.execute_python(command)
        except Exception as e:
            self.log_error(f"Error executing command: {e}")
        
        # Emit signal
        self.command_executed.emit(command)
    
    def execute_lsc(self, code: str):
        """Execute LSC code"""
        try:
            # TODO: Integrate with LSC interpreter
            self.log_info(f"LSC execution not yet implemented: {code}")
        except Exception as e:
            self.log_error(f"LSC Error: {e}")
    
    def execute_python(self, expression: str):
        """Execute Python expression"""
        try:
            # Create a safe namespace
            namespace = {
                '__builtins__': __builtins__,
                'print': self.log_info,
                'console': self
            }
            
            # Try to evaluate as expression first
            try:
                result = eval(expression, namespace)
                if result is not None:
                    self.log_info(str(result))
            except SyntaxError:
                # If it fails, try to execute as statement
                exec(expression, namespace)
                
        except Exception as e:
            self.log_error(f"Python Error: {e}")
    
    def show_help(self):
        """Show help information"""
        help_text = """
Available Commands:
  help                 - Show this help
  clear                - Clear console output
  lsc <code>          - Execute LSC code
  <python_expression> - Execute Python expression

Examples:
  lsc print("Hello World")
  2 + 2
  import math; math.pi
        """
        self.log_info(help_text.strip())
    
    def log_message(self, message: str, level: str = "INFO", color: str = "#e0e0e0"):
        """Log a message with timestamp and level"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # Move cursor to end
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)
        
        # Insert colored text
        self.output_text.setTextColor(QColor(color))
        self.output_text.insertPlainText(formatted_message + "\n")
        
        # Auto-scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def log_info(self, message: str):
        """Log info message"""
        self.log_message(message, "INFO", "#e0e0e0")
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.log_message(message, "WARN", "#ff9800")
    
    def log_error(self, message: str):
        """Log error message"""
        self.log_message(message, "ERROR", "#f44336")
    
    def log_debug(self, message: str):
        """Log debug message"""
        self.log_message(message, "DEBUG", "#b0b0b0")
    
    def log_command(self, command: str):
        """Log executed command"""
        self.log_message(f"> {command}", "CMD", "#8b5fbf")
    
    def filter_messages(self, filter_type: str):
        """Filter messages by type (placeholder)"""
        # TODO: Implement message filtering
        pass
    
    def clear_output(self):
        """Clear the output text"""
        self.output_text.clear()
        self.log_info("Console cleared")
    
    def closeEvent(self, event):
        """Handle widget close"""
        self.restore_output_capture()
        event.accept()


class OutputCapture(io.StringIO):
    """Custom output stream that captures and redirects output"""
    
    def __init__(self, log_function):
        super().__init__()
        self.log_function = log_function
    
    def write(self, text: str):
        """Write text to the log function"""
        if text.strip():  # Only log non-empty text
            self.log_function(text.strip())
        return len(text)
    
    def flush(self):
        """Flush the stream (no-op)"""
        pass
