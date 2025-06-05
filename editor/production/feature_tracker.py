"""
Feature/Bug Tracker Tool for Lupine Engine
Provides issue tracking and feature management
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QGroupBox, QTabWidget, QTextEdit, QDateEdit,
    QSpinBox, QMessageBox, QAbstractItemView, QInputDialog,
    QDialog, QDialogButtonBox, QFormLayout, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.project import LupineProject


class IssueDialog(QDialog):
    """Dialog for creating/editing issues (features/bugs)"""
    
    def __init__(self, issue_data: Dict = None, parent=None):
        super().__init__(parent)
        self.issue_data = issue_data or {}
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Issue Editor")
        self.setModal(True)
        self.resize(500, 450)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter issue title...")
        form_layout.addRow("Title:", self.title_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Feature", "Bug", "Enhancement", "Task", "Documentation"])
        form_layout.addRow("Type:", self.type_combo)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Enter detailed description...")
        form_layout.addRow("Description:", self.description_edit)
        
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g., UI, Gameplay, Audio...")
        form_layout.addRow("Category:", self.category_edit)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        self.priority_combo.setCurrentText("Medium")
        form_layout.addRow("Priority:", self.priority_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Open", "In Progress", "Testing", "Resolved", "Closed", "Won't Fix"
        ])
        form_layout.addRow("Status:", self.status_combo)
        
        self.assignee_edit = QLineEdit()
        self.assignee_edit.setPlaceholderText("Enter assignee name...")
        form_layout.addRow("Assignee:", self.assignee_edit)
        
        self.reporter_edit = QLineEdit()
        self.reporter_edit.setPlaceholderText("Enter reporter name...")
        form_layout.addRow("Reporter:", self.reporter_edit)
        
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate().addDays(14))
        self.due_date_edit.setCalendarPopup(True)
        form_layout.addRow("Due Date:", self.due_date_edit)
        
        self.estimated_hours_spin = QSpinBox()
        self.estimated_hours_spin.setRange(0, 999)
        self.estimated_hours_spin.setSuffix(" hours")
        form_layout.addRow("Estimated Hours:", self.estimated_hours_spin)
        
        # Steps to reproduce (for bugs)
        self.steps_edit = QTextEdit()
        self.steps_edit.setMaximumHeight(80)
        self.steps_edit.setPlaceholderText("Steps to reproduce (for bugs)...")
        form_layout.addRow("Steps to Reproduce:", self.steps_edit)
        
        # Expected behavior
        self.expected_edit = QTextEdit()
        self.expected_edit.setMaximumHeight(60)
        self.expected_edit.setPlaceholderText("Expected behavior...")
        form_layout.addRow("Expected Behavior:", self.expected_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_data(self):
        """Load issue data into form"""
        if not self.issue_data:
            return
            
        self.title_edit.setText(self.issue_data.get("title", ""))
        self.type_combo.setCurrentText(self.issue_data.get("type", "Feature"))
        self.description_edit.setPlainText(self.issue_data.get("description", ""))
        self.category_edit.setText(self.issue_data.get("category", ""))
        self.priority_combo.setCurrentText(self.issue_data.get("priority", "Medium"))
        self.status_combo.setCurrentText(self.issue_data.get("status", "Open"))
        self.assignee_edit.setText(self.issue_data.get("assignee", ""))
        self.reporter_edit.setText(self.issue_data.get("reporter", ""))
        
        due_date = self.issue_data.get("due_date")
        if due_date:
            self.due_date_edit.setDate(QDate.fromString(due_date, Qt.DateFormat.ISODate))
            
        self.estimated_hours_spin.setValue(self.issue_data.get("estimated_hours", 0))
        self.steps_edit.setPlainText(self.issue_data.get("steps_to_reproduce", ""))
        self.expected_edit.setPlainText(self.issue_data.get("expected_behavior", ""))
        
    def get_issue_data(self) -> Dict:
        """Get issue data from form"""
        return {
            "title": self.title_edit.text(),
            "type": self.type_combo.currentText(),
            "description": self.description_edit.toPlainText(),
            "category": self.category_edit.text(),
            "priority": self.priority_combo.currentText(),
            "status": self.status_combo.currentText(),
            "assignee": self.assignee_edit.text(),
            "reporter": self.reporter_edit.text(),
            "due_date": self.due_date_edit.date().toString(Qt.DateFormat.ISODate),
            "estimated_hours": self.estimated_hours_spin.value(),
            "steps_to_reproduce": self.steps_edit.toPlainText(),
            "expected_behavior": self.expected_edit.toPlainText(),
            "created_date": self.issue_data.get("created_date", datetime.now().isoformat()),
            "last_updated": datetime.now().isoformat(),
            "id": self.issue_data.get("id", datetime.now().timestamp())
        }


class FeatureTrackerWidget(QWidget):
    """Main feature/bug tracking widget"""
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.issues: List[Dict] = []
        self.setup_ui()
        self.load_issues()
        
    def setup_ui(self):
        """Setup the tracker UI"""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.add_issue_btn = QPushButton("Add Issue")
        self.add_issue_btn.clicked.connect(self.add_issue)
        
        self.edit_issue_btn = QPushButton("Edit Issue")
        self.edit_issue_btn.clicked.connect(self.edit_issue)
        self.edit_issue_btn.setEnabled(False)
        
        self.delete_issue_btn = QPushButton("Delete Issue")
        self.delete_issue_btn.clicked.connect(self.delete_issue)
        self.delete_issue_btn.setEnabled(False)
        
        controls_layout.addWidget(self.add_issue_btn)
        controls_layout.addWidget(self.edit_issue_btn)
        controls_layout.addWidget(self.delete_issue_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filter by Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "All Types", "Feature", "Bug", "Enhancement", "Task", "Documentation"
        ])
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.type_filter)
        
        filter_layout.addWidget(QLabel("Filter by Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All Statuses", "Open", "In Progress", "Testing", "Resolved", "Closed", "Won't Fix"
        ])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addWidget(QLabel("Filter by Priority:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All Priorities", "Low", "Medium", "High", "Critical"])
        self.priority_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.priority_filter)
        
        filter_layout.addWidget(QLabel("Filter by Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Issues tree
        self.issues_tree = QTreeWidget()
        self.issues_tree.setHeaderLabels([
            "ID", "Title", "Type", "Status", "Priority", "Category", "Assignee", "Due Date"
        ])
        self.issues_tree.setRootIsDecorated(False)
        self.issues_tree.setAlternatingRowColors(True)
        self.issues_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.issues_tree.itemDoubleClicked.connect(self.edit_selected_issue)
        
        layout.addWidget(self.issues_tree)
        
        # Issue details
        details_group = QGroupBox("Issue Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        layout.addWidget(details_group)
        
    def load_issues(self):
        """Load issues from project data"""
        issues_file = Path(self.project.project_path) / "data" / "issues.json"
        
        if issues_file.exists():
            try:
                with open(issues_file, 'r') as f:
                    data = json.load(f)
                    self.issues = data.get("issues", [])
            except Exception as e:
                print(f"Error loading issues: {e}")
                self.issues = []
        else:
            self.issues = []
            
        self.update_categories()
        self.refresh_issues()
        
    def save_issues(self):
        """Save issues to project data"""
        issues_file = Path(self.project.project_path) / "data" / "issues.json"
        issues_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "issues": self.issues,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(issues_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save issues: {e}")
            
    def update_categories(self):
        """Update category filter with available categories"""
        categories = set()
        for issue in self.issues:
            category = issue.get("category", "").strip()
            if category:
                categories.add(category)
                
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")
        for category in sorted(categories):
            self.category_filter.addItem(category)
            
    def refresh_issues(self):
        """Refresh the issues tree"""
        self.issues_tree.clear()
        
        for issue in self.issues:
            if not self.should_show_issue(issue):
                continue
                
            item = QTreeWidgetItem()
            
            # ID
            issue_id = str(int(issue.get("id", 0)))
            item.setText(0, issue_id)
            
            # Title
            item.setText(1, issue.get("title", ""))
            
            # Type
            issue_type = issue.get("type", "")
            item.setText(2, issue_type)
            
            # Status
            status = issue.get("status", "")
            item.setText(3, status)
            
            # Priority
            priority = issue.get("priority", "")
            item.setText(4, priority)
            
            # Category
            item.setText(5, issue.get("category", ""))
            
            # Assignee
            item.setText(6, issue.get("assignee", ""))
            
            # Due Date
            item.setText(7, issue.get("due_date", ""))
            
            # Color coding
            if status == "Closed":
                item.setForeground(0, QColor(128, 128, 128))
            elif status == "Resolved":
                item.setForeground(0, QColor(0, 128, 0))
            elif priority == "Critical":
                item.setForeground(0, QColor(255, 0, 0))
            elif priority == "High":
                item.setForeground(0, QColor(255, 165, 0))
            elif issue_type == "Bug":
                item.setBackground(0, QColor(255, 240, 240))
                
            # Check if overdue
            due_date = issue.get("due_date")
            if due_date and status not in ["Resolved", "Closed"]:
                try:
                    due = datetime.fromisoformat(due_date)
                    if due.date() < datetime.now().date():
                        item.setBackground(7, QColor(255, 230, 230))
                except:
                    pass
                    
            # Store issue data
            item.setData(0, Qt.ItemDataRole.UserRole, issue)
            
            self.issues_tree.addTopLevelItem(item)
            
    def should_show_issue(self, issue: Dict) -> bool:
        """Check if issue should be shown based on current filters"""
        type_filter = self.type_filter.currentText()
        status_filter = self.status_filter.currentText()
        priority_filter = self.priority_filter.currentText()
        category_filter = self.category_filter.currentText()
        
        if type_filter != "All Types" and issue.get("type") != type_filter:
            return False
            
        if status_filter != "All Statuses" and issue.get("status") != status_filter:
            return False
            
        if priority_filter != "All Priorities" and issue.get("priority") != priority_filter:
            return False
            
        if category_filter != "All Categories" and issue.get("category") != category_filter:
            return False
            
        return True
        
    def apply_filters(self):
        """Apply current filters"""
        self.refresh_issues()
        
    def on_selection_changed(self):
        """Handle selection change"""
        has_selection = bool(self.issues_tree.selectedItems())
        self.edit_issue_btn.setEnabled(has_selection)
        self.delete_issue_btn.setEnabled(has_selection)
        
        # Update details
        current_item = self.issues_tree.currentItem()
        if current_item:
            issue_data = current_item.data(0, Qt.ItemDataRole.UserRole)
            if issue_data:
                self.show_issue_details(issue_data)
        else:
            self.details_text.clear()
            
    def show_issue_details(self, issue: Dict):
        """Show detailed information about an issue"""
        details = []
        
        details.append(f"Title: {issue.get('title', '')}")
        details.append(f"Type: {issue.get('type', '')}")
        details.append(f"Status: {issue.get('status', '')}")
        details.append(f"Priority: {issue.get('priority', '')}")
        details.append(f"Category: {issue.get('category', '')}")
        details.append(f"Assignee: {issue.get('assignee', '')}")
        details.append(f"Reporter: {issue.get('reporter', '')}")
        details.append(f"Due Date: {issue.get('due_date', '')}")
        details.append(f"Estimated Hours: {issue.get('estimated_hours', 0)}")
        details.append("")
        
        description = issue.get("description", "")
        if description:
            details.append(f"Description:\n{description}")
            details.append("")
            
        steps = issue.get("steps_to_reproduce", "")
        if steps:
            details.append(f"Steps to Reproduce:\n{steps}")
            details.append("")
            
        expected = issue.get("expected_behavior", "")
        if expected:
            details.append(f"Expected Behavior:\n{expected}")
            
        self.details_text.setPlainText("\n".join(details))
        
    def add_issue(self):
        """Add a new issue"""
        dialog = IssueDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            issue_data = dialog.get_issue_data()
            self.issues.append(issue_data)
            self.save_issues()
            self.update_categories()
            self.refresh_issues()
            
    def edit_issue(self):
        """Edit selected issue"""
        current_item = self.issues_tree.currentItem()
        if current_item:
            self.edit_selected_issue(current_item)
            
    def edit_selected_issue(self, item: QTreeWidgetItem):
        """Edit the selected issue"""
        issue_data = item.data(0, Qt.ItemDataRole.UserRole)
        if issue_data:
            dialog = IssueDialog(issue_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_issue_data()
                
                # Find and update the issue
                for i, issue in enumerate(self.issues):
                    if issue.get("id") == issue_data.get("id"):
                        self.issues[i] = updated_data
                        break
                        
                self.save_issues()
                self.update_categories()
                self.refresh_issues()
                
    def delete_issue(self):
        """Delete selected issue"""
        current_item = self.issues_tree.currentItem()
        if current_item:
            issue_data = current_item.data(0, Qt.ItemDataRole.UserRole)
            if issue_data:
                reply = QMessageBox.question(
                    self, "Confirm Delete",
                    f"Are you sure you want to delete issue '{issue_data.get('title', '')}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Find and remove the issue
                    self.issues = [i for i in self.issues if i.get("id") != issue_data.get("id")]
                    self.save_issues()
                    self.update_categories()
                    self.refresh_issues()


class FeatureTrackerWindow(QMainWindow):
    """Main Feature/Bug Tracker window"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_window()
        self.setup_ui()
        
    def setup_window(self):
        """Setup the window"""
        self.setWindowTitle("Feature/Bug Tracker - Lupine Engine")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
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
        
        # Feature tracker widget
        self.tracker_widget = FeatureTrackerWidget(self.project)
        layout.addWidget(self.tracker_widget)
