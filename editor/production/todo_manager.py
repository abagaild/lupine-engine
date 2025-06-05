"""
To-Do Manager Tool for Lupine Engine
Provides task management and to-do list functionality
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QGroupBox, QTabWidget, QTextEdit, QDateEdit,
    QCheckBox, QMessageBox, QInputDialog, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.project import LupineProject


class TaskDialog(QDialog):
    """Dialog for creating/editing tasks"""
    
    def __init__(self, task_data: Dict = None, parent=None):
        super().__init__(parent)
        self.task_data = task_data or {}
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Task Editor")
        self.setModal(True)
        self.resize(400, 350)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter task title...")
        form_layout.addRow("Title:", self.title_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter task description...")
        form_layout.addRow("Description:", self.description_edit)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        self.priority_combo.setCurrentText("Medium")
        form_layout.addRow("Priority:", self.priority_combo)
        
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Enter category (optional)...")
        form_layout.addRow("Category:", self.category_edit)
        
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate().addDays(7))
        self.due_date_edit.setCalendarPopup(True)
        form_layout.addRow("Due Date:", self.due_date_edit)
        
        self.estimated_hours_spin = QSpinBox()
        self.estimated_hours_spin.setRange(0, 999)
        self.estimated_hours_spin.setSuffix(" hours")
        form_layout.addRow("Estimated Hours:", self.estimated_hours_spin)
        
        self.completed_checkbox = QCheckBox("Mark as completed")
        form_layout.addRow("Status:", self.completed_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_data(self):
        """Load task data into form"""
        if not self.task_data:
            return
            
        self.title_edit.setText(self.task_data.get("title", ""))
        self.description_edit.setPlainText(self.task_data.get("description", ""))
        self.priority_combo.setCurrentText(self.task_data.get("priority", "Medium"))
        self.category_edit.setText(self.task_data.get("category", ""))
        
        due_date = self.task_data.get("due_date")
        if due_date:
            self.due_date_edit.setDate(QDate.fromString(due_date, Qt.DateFormat.ISODate))
            
        self.estimated_hours_spin.setValue(self.task_data.get("estimated_hours", 0))
        self.completed_checkbox.setChecked(self.task_data.get("completed", False))
        
    def get_task_data(self) -> Dict:
        """Get task data from form"""
        return {
            "title": self.title_edit.text(),
            "description": self.description_edit.toPlainText(),
            "priority": self.priority_combo.currentText(),
            "category": self.category_edit.text(),
            "due_date": self.due_date_edit.date().toString(Qt.DateFormat.ISODate),
            "estimated_hours": self.estimated_hours_spin.value(),
            "completed": self.completed_checkbox.isChecked(),
            "created_date": self.task_data.get("created_date", datetime.now().isoformat()),
            "completed_date": datetime.now().isoformat() if self.completed_checkbox.isChecked() else None,
            "id": self.task_data.get("id", datetime.now().timestamp())
        }


class TodoListWidget(QWidget):
    """Widget for managing a single to-do list"""
    
    def __init__(self, list_name: str, project: LupineProject):
        super().__init__()
        self.list_name = list_name
        self.project = project
        self.tasks: List[Dict] = []
        self.setup_ui()
        self.load_tasks()
        
    def setup_ui(self):
        """Setup the list UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"List: {self.list_name}"))
        header_layout.addStretch()
        
        self.add_task_btn = QPushButton("Add Task")
        self.add_task_btn.clicked.connect(self.add_task)
        header_layout.addWidget(self.add_task_btn)
        
        layout.addLayout(header_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Pending", "Completed", "High Priority", "Overdue"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_combo)
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Task tree
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabels(["Task", "Priority", "Category", "Due Date", "Status"])
        self.task_tree.setRootIsDecorated(False)
        self.task_tree.itemDoubleClicked.connect(self.edit_task)
        
        layout.addWidget(self.task_tree)
        
        # Task controls
        controls_layout = QHBoxLayout()
        
        self.edit_task_btn = QPushButton("Edit Task")
        self.edit_task_btn.clicked.connect(self.edit_selected_task)
        
        self.complete_task_btn = QPushButton("Toggle Complete")
        self.complete_task_btn.clicked.connect(self.toggle_task_completion)
        
        self.delete_task_btn = QPushButton("Delete Task")
        self.delete_task_btn.clicked.connect(self.delete_task)
        
        controls_layout.addWidget(self.edit_task_btn)
        controls_layout.addWidget(self.complete_task_btn)
        controls_layout.addWidget(self.delete_task_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
    def load_tasks(self):
        """Load tasks from project data"""
        todo_file = Path(self.project.project_path) / "data" / "todos.json"
        
        if todo_file.exists():
            try:
                with open(todo_file, 'r') as f:
                    data = json.load(f)
                    lists_data = data.get("lists", {})
                    self.tasks = lists_data.get(self.list_name, [])
            except Exception as e:
                print(f"Error loading todos: {e}")
                self.tasks = []
        else:
            self.tasks = []
            
        self.update_categories()
        self.refresh_tasks()
        
    def save_tasks(self):
        """Save tasks to project data"""
        todo_file = Path(self.project.project_path) / "data" / "todos.json"
        todo_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        data = {"lists": {}, "last_updated": datetime.now().isoformat()}
        if todo_file.exists():
            try:
                with open(todo_file, 'r') as f:
                    data = json.load(f)
            except:
                pass
                
        # Update this list's data
        if "lists" not in data:
            data["lists"] = {}
        data["lists"][self.list_name] = self.tasks
        data["last_updated"] = datetime.now().isoformat()
        
        try:
            with open(todo_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save tasks: {e}")
            
    def update_categories(self):
        """Update category filter with available categories"""
        categories = set()
        for task in self.tasks:
            category = task.get("category", "").strip()
            if category:
                categories.add(category)
                
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")
        for category in sorted(categories):
            self.category_filter.addItem(category)
            
    def refresh_tasks(self):
        """Refresh the task tree"""
        self.task_tree.clear()
        
        for task in self.tasks:
            if not self.should_show_task(task):
                continue
                
            item = QTreeWidgetItem()
            
            # Task title
            title = task.get("title", "")
            if task.get("completed", False):
                title = f"✓ {title}"
            item.setText(0, title)
            
            # Priority
            priority = task.get("priority", "Medium")
            item.setText(1, priority)
            
            # Category
            item.setText(2, task.get("category", ""))
            
            # Due date
            item.setText(3, task.get("due_date", ""))
            
            # Status
            status = "Completed" if task.get("completed", False) else "Pending"
            item.setText(4, status)
            
            # Color coding
            if task.get("completed", False):
                item.setForeground(0, QColor(128, 128, 128))
            elif priority == "Critical":
                item.setForeground(0, QColor(255, 0, 0))
            elif priority == "High":
                item.setForeground(0, QColor(255, 165, 0))
                
            # Check if overdue
            due_date = task.get("due_date")
            if due_date and not task.get("completed", False):
                try:
                    due = datetime.fromisoformat(due_date)
                    if due.date() < datetime.now().date():
                        item.setBackground(0, QColor(255, 230, 230))
                except:
                    pass
                    
            # Store task data
            item.setData(0, Qt.ItemDataRole.UserRole, task)
            
            self.task_tree.addTopLevelItem(item)
            
    def should_show_task(self, task: Dict) -> bool:
        """Check if task should be shown based on current filters"""
        filter_type = self.filter_combo.currentText()
        category_filter = self.category_filter.currentText()
        
        # Category filter
        if category_filter != "All Categories":
            if task.get("category", "") != category_filter:
                return False
                
        # Type filter
        if filter_type == "Pending":
            return not task.get("completed", False)
        elif filter_type == "Completed":
            return task.get("completed", False)
        elif filter_type == "High Priority":
            return task.get("priority") in ["High", "Critical"]
        elif filter_type == "Overdue":
            if task.get("completed", False):
                return False
            due_date = task.get("due_date")
            if due_date:
                try:
                    due = datetime.fromisoformat(due_date)
                    return due.date() < datetime.now().date()
                except:
                    pass
            return False
            
        return True
        
    def apply_filter(self):
        """Apply current filters"""
        self.refresh_tasks()
        
    def add_task(self):
        """Add a new task"""
        dialog = TaskDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            self.tasks.append(task_data)
            self.save_tasks()
            self.update_categories()
            self.refresh_tasks()
            
    def edit_task(self, item: QTreeWidgetItem):
        """Edit a task (double-click handler)"""
        task_data = item.data(0, Qt.ItemDataRole.UserRole)
        if task_data:
            self.edit_task_data(task_data)
            
    def edit_selected_task(self):
        """Edit the selected task"""
        current_item = self.task_tree.currentItem()
        if current_item:
            self.edit_task(current_item)
            
    def edit_task_data(self, task_data: Dict):
        """Edit task data"""
        dialog = TaskDialog(task_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_task_data()
            
            # Find and update the task
            for i, task in enumerate(self.tasks):
                if task.get("id") == task_data.get("id"):
                    self.tasks[i] = updated_data
                    break
                    
            self.save_tasks()
            self.update_categories()
            self.refresh_tasks()
            
    def toggle_task_completion(self):
        """Toggle completion status of selected task"""
        current_item = self.task_tree.currentItem()
        if current_item:
            task_data = current_item.data(0, Qt.ItemDataRole.UserRole)
            if task_data:
                # Find and update the task
                for task in self.tasks:
                    if task.get("id") == task_data.get("id"):
                        task["completed"] = not task.get("completed", False)
                        if task["completed"]:
                            task["completed_date"] = datetime.now().isoformat()
                        else:
                            task["completed_date"] = None
                        break
                        
                self.save_tasks()
                self.refresh_tasks()
                
    def delete_task(self):
        """Delete the selected task"""
        current_item = self.task_tree.currentItem()
        if current_item:
            task_data = current_item.data(0, Qt.ItemDataRole.UserRole)
            if task_data:
                reply = QMessageBox.question(
                    self, "Confirm Delete",
                    f"Are you sure you want to delete task '{task_data.get('title', '')}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Find and remove the task
                    self.tasks = [t for t in self.tasks if t.get("id") != task_data.get("id")]
                    self.save_tasks()
                    self.update_categories()
                    self.refresh_tasks()


class TodoManagerWindow(QMainWindow):
    """Main To-Do Manager window"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_window()
        self.setup_ui()
        
    def setup_window(self):
        """Setup the window"""
        self.setWindowTitle("To-Do Manager - Lupine Engine")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # List management
        list_controls = QHBoxLayout()
        
        list_controls.addWidget(QLabel("To-Do Lists:"))
        
        self.add_list_btn = QPushButton("Add List")
        self.add_list_btn.clicked.connect(self.add_list)
        
        self.rename_list_btn = QPushButton("Rename List")
        self.rename_list_btn.clicked.connect(self.rename_list)
        
        self.delete_list_btn = QPushButton("Delete List")
        self.delete_list_btn.clicked.connect(self.delete_list)
        
        list_controls.addWidget(self.add_list_btn)
        list_controls.addWidget(self.rename_list_btn)
        list_controls.addWidget(self.delete_list_btn)
        list_controls.addStretch()
        
        layout.addLayout(list_controls)
        
        # Tab widget for lists
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_list_tab)
        
        layout.addWidget(self.tab_widget)
        
        # Load existing lists
        self.load_lists()
        
    def load_lists(self):
        """Load existing to-do lists"""
        todo_file = Path(self.project.project_path) / "data" / "todos.json"
        
        if todo_file.exists():
            try:
                with open(todo_file, 'r') as f:
                    data = json.load(f)
                    lists_data = data.get("lists", {})
                    
                    for list_name in lists_data.keys():
                        self.add_list_tab(list_name)
            except Exception as e:
                print(f"Error loading todo lists: {e}")
                
        # If no lists exist, create a default one
        if self.tab_widget.count() == 0:
            self.add_list_tab("General")
            
    def add_list(self):
        """Add a new to-do list"""
        name, ok = QInputDialog.getText(self, "New List", "Enter list name:")
        if ok and name.strip():
            self.add_list_tab(name.strip())
            
    def add_list_tab(self, list_name: str):
        """Add a tab for a to-do list"""
        # Check if list already exists
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == list_name:
                self.tab_widget.setCurrentIndex(i)
                return
                
        # Create new list widget
        list_widget = TodoListWidget(list_name, self.project)
        self.tab_widget.addTab(list_widget, list_name)
        self.tab_widget.setCurrentWidget(list_widget)
        
    def rename_list(self):
        """Rename the current list"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            old_name = self.tab_widget.tabText(current_index)
            new_name, ok = QInputDialog.getText(self, "Rename List", "Enter new name:", text=old_name)
            
            if ok and new_name.strip() and new_name.strip() != old_name:
                # Update tab text
                self.tab_widget.setTabText(current_index, new_name.strip())
                
                # Update data file
                self.rename_list_in_data(old_name, new_name.strip())
                
    def rename_list_in_data(self, old_name: str, new_name: str):
        """Rename a list in the data file"""
        todo_file = Path(self.project.project_path) / "data" / "todos.json"
        
        if todo_file.exists():
            try:
                with open(todo_file, 'r') as f:
                    data = json.load(f)
                    
                lists_data = data.get("lists", {})
                if old_name in lists_data:
                    lists_data[new_name] = lists_data.pop(old_name)
                    
                    with open(todo_file, 'w') as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename list: {e}")
                
    def delete_list(self):
        """Delete the current list"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            list_name = self.tab_widget.tabText(current_index)
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete list '{list_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.close_list_tab(current_index)
                self.delete_list_from_data(list_name)
                
    def close_list_tab(self, index: int):
        """Close a list tab"""
        self.tab_widget.removeTab(index)
        
    def delete_list_from_data(self, list_name: str):
        """Delete a list from the data file"""
        todo_file = Path(self.project.project_path) / "data" / "todos.json"
        
        if todo_file.exists():
            try:
                with open(todo_file, 'r') as f:
                    data = json.load(f)
                    
                lists_data = data.get("lists", {})
                if list_name in lists_data:
                    del lists_data[list_name]
                    
                    with open(todo_file, 'w') as f:
                        json.dump(data, f, indent=2)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete list: {e}")
