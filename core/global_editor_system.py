"""
Global Editor System for Lupine Engine
Provides unified undo/redo, clipboard, and keyboard shortcut management across all editors
"""

import json
from typing import Any, Dict, List, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QWidget


class EditorCommand:
    """Base class for editor commands that can be undone/redone"""
    
    def __init__(self, description: str = ""):
        self.description = description
    
    def execute(self) -> Any:
        """Execute the command and return any result"""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def undo(self):
        """Undo the command"""
        raise NotImplementedError("Subclasses must implement undo()")
    
    def get_description(self) -> str:
        """Get command description for UI"""
        return self.description


class PropertyChangeCommand(EditorCommand):
    """Command for property changes that can be undone"""
    
    def __init__(self, target: Any, property_name: str, new_value: Any, old_value: Any, description: str = ""):
        super().__init__(description or f"Change {property_name}")
        self.target = target
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = old_value
    
    def execute(self) -> Any:
        """Set the new value"""
        if hasattr(self.target, self.property_name):
            setattr(self.target, self.property_name, self.new_value)
        elif isinstance(self.target, dict):
            self.target[self.property_name] = self.new_value
        return self.new_value
    
    def undo(self):
        """Restore the old value"""
        if hasattr(self.target, self.property_name):
            setattr(self.target, self.property_name, self.old_value)
        elif isinstance(self.target, dict):
            self.target[self.property_name] = self.old_value


class GlobalClipboard:
    """Global clipboard system for all editors"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.data_type: str = ""
    
    def copy(self, data: Any, data_type: str = "generic"):
        """Copy data to clipboard"""
        try:
            # Try to serialize the data to ensure it's copyable
            if isinstance(data, (dict, list, str, int, float, bool)):
                self.data = {"content": data, "serialized": json.dumps(data)}
            else:
                # For complex objects, store reference and try to serialize
                self.data = {"content": data, "serialized": str(data)}
            
            self.data_type = data_type
            print(f"[Clipboard] Copied {data_type}: {str(data)[:100]}...")
            return True
        except Exception as e:
            print(f"[Clipboard] Error copying data: {e}")
            return False
    
    def paste(self, expected_type: str = "") -> Optional[Any]:
        """Paste data from clipboard"""
        if not self.data:
            return None
        
        if expected_type and self.data_type != expected_type:
            print(f"[Clipboard] Type mismatch: expected {expected_type}, got {self.data_type}")
            return None
        
        return self.data.get("content")
    
    def has_data(self, data_type: str = "") -> bool:
        """Check if clipboard has data of specified type"""
        if not self.data:
            return False
        
        if data_type:
            return self.data_type == data_type
        
        return True
    
    def clear(self):
        """Clear clipboard"""
        self.data = {}
        self.data_type = ""


class GlobalUndoRedoManager:
    """Global undo/redo manager for all editors"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: List[EditorCommand] = []
        self.current_index = -1
        self.enabled = True
    
    def execute_command(self, command: EditorCommand) -> Any:
        """Execute a command and add it to history"""
        if not self.enabled:
            return command.execute()
        
        result = command.execute()
        
        # Remove any commands after current index (when undoing then doing new action)
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new command
        self.history.append(command)
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
        
        print(f"[UndoRedo] Executed: {command.get_description()}")
        return result
    
    def undo(self) -> bool:
        """Undo the last command"""
        if not self.enabled or not self.can_undo():
            return False
        
        command = self.history[self.current_index]
        command.undo()
        self.current_index -= 1
        print(f"[UndoRedo] Undid: {command.get_description()}")
        return True
    
    def redo(self) -> bool:
        """Redo the next command"""
        if not self.enabled or not self.can_redo():
            return False
        
        self.current_index += 1
        command = self.history[self.current_index]
        command.execute()
        print(f"[UndoRedo] Redid: {command.get_description()}")
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.current_index < len(self.history) - 1
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of command that would be undone"""
        if self.can_undo():
            return self.history[self.current_index].get_description()
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of command that would be redone"""
        if self.can_redo():
            return self.history[self.current_index + 1].get_description()
        return None
    
    def clear_history(self):
        """Clear all history"""
        self.history.clear()
        self.current_index = -1
    
    def set_enabled(self, enabled: bool):
        """Enable or disable undo/redo tracking"""
        self.enabled = enabled


class GlobalEditorSystem(QObject):
    """Global system for managing editor functionality across all components"""
    
    # Signals
    undo_performed = pyqtSignal()
    redo_performed = pyqtSignal()
    clipboard_changed = pyqtSignal(str)  # data_type
    
    def __init__(self):
        super().__init__()
        self.undo_manager = GlobalUndoRedoManager()
        self.clipboard = GlobalClipboard()
        self.shortcuts: Dict[str, QShortcut] = {}
        self.active_widget: Optional[QWidget] = None
        
        # Callback functions for different operations
        self.copy_callbacks: Dict[str, Callable] = {}
        self.paste_callbacks: Dict[str, Callable] = {}
        self.cut_callbacks: Dict[str, Callable] = {}
    
    def setup_shortcuts(self, widget: QWidget):
        """Setup global shortcuts for a widget"""
        # Clear existing shortcuts for this widget
        widget_id = id(widget)
        if widget_id in self.shortcuts:
            for shortcut in self.shortcuts[widget_id]:
                shortcut.deleteLater()
        
        shortcuts = []
        
        # Undo (Ctrl+Z)
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), widget)
        undo_shortcut.activated.connect(self.undo)
        shortcuts.append(undo_shortcut)
        
        # Redo (Ctrl+Y and Ctrl+Shift+Z)
        redo_shortcut1 = QShortcut(QKeySequence("Ctrl+Y"), widget)
        redo_shortcut1.activated.connect(self.redo)
        shortcuts.append(redo_shortcut1)
        
        redo_shortcut2 = QShortcut(QKeySequence("Ctrl+Shift+Z"), widget)
        redo_shortcut2.activated.connect(self.redo)
        shortcuts.append(redo_shortcut2)
        
        # Copy (Ctrl+C)
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), widget)
        copy_shortcut.activated.connect(lambda: self.copy(widget))
        shortcuts.append(copy_shortcut)
        
        # Cut (Ctrl+X)
        cut_shortcut = QShortcut(QKeySequence("Ctrl+X"), widget)
        cut_shortcut.activated.connect(lambda: self.cut(widget))
        shortcuts.append(cut_shortcut)
        
        # Paste (Ctrl+V)
        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), widget)
        paste_shortcut.activated.connect(lambda: self.paste(widget))
        shortcuts.append(paste_shortcut)
        
        self.shortcuts[widget_id] = shortcuts
        print(f"[GlobalEditor] Setup shortcuts for {widget.__class__.__name__}")
    
    def register_copy_callback(self, widget_type: str, callback: Callable):
        """Register copy callback for a widget type"""
        self.copy_callbacks[widget_type] = callback
    
    def register_paste_callback(self, widget_type: str, callback: Callable):
        """Register paste callback for a widget type"""
        self.paste_callbacks[widget_type] = callback
    
    def register_cut_callback(self, widget_type: str, callback: Callable):
        """Register cut callback for a widget type"""
        self.cut_callbacks[widget_type] = callback
    
    def undo(self):
        """Perform global undo"""
        if self.undo_manager.undo():
            self.undo_performed.emit()
    
    def redo(self):
        """Perform global redo"""
        if self.undo_manager.redo():
            self.redo_performed.emit()
    
    def copy(self, widget: QWidget):
        """Perform copy operation"""
        widget_type = widget.__class__.__name__
        if widget_type in self.copy_callbacks:
            data = self.copy_callbacks[widget_type]()
            if data is not None:
                self.clipboard.copy(data, widget_type)
                self.clipboard_changed.emit(widget_type)
        else:
            print(f"[GlobalEditor] No copy callback for {widget_type}")
    
    def cut(self, widget: QWidget):
        """Perform cut operation"""
        widget_type = widget.__class__.__name__
        if widget_type in self.cut_callbacks:
            data = self.cut_callbacks[widget_type]()
            if data is not None:
                self.clipboard.copy(data, widget_type)
                self.clipboard_changed.emit(widget_type)
        else:
            # Fallback: copy then delete if possible
            self.copy(widget)
    
    def paste(self, widget: QWidget):
        """Perform paste operation"""
        widget_type = widget.__class__.__name__
        if widget_type in self.paste_callbacks:
            data = self.clipboard.paste(widget_type)
            if data is not None:
                self.paste_callbacks[widget_type](data)
        else:
            print(f"[GlobalEditor] No paste callback for {widget_type}")


# Global instance
_global_editor_system: Optional[GlobalEditorSystem] = None


def get_global_editor_system() -> GlobalEditorSystem:
    """Get the global editor system instance"""
    global _global_editor_system
    if _global_editor_system is None:
        _global_editor_system = GlobalEditorSystem()
    return _global_editor_system


def setup_editor_shortcuts(widget: QWidget):
    """Convenience function to setup shortcuts for a widget"""
    get_global_editor_system().setup_shortcuts(widget)
