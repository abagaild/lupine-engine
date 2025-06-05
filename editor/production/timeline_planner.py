"""
Timeline Planner Tool for Lupine Engine
Provides project timeline and milestone management
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QGroupBox, QTabWidget, QTextEdit, QDateEdit,
    QSpinBox, QMessageBox, QHeaderView, QAbstractItemView,
    QInputDialog, QDialog, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.project import LupineProject


class MilestoneDialog(QDialog):
    """Dialog for creating/editing milestones"""
    
    def __init__(self, milestone_data: Dict = None, parent=None):
        super().__init__(parent)
        self.milestone_data = milestone_data or {}
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Milestone Editor")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter milestone name...")
        form_layout.addRow("Name:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter milestone description...")
        form_layout.addRow("Description:", self.description_edit)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        form_layout.addRow("Start Date:", self.start_date_edit)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addDays(7))
        self.end_date_edit.setCalendarPopup(True)
        form_layout.addRow("End Date:", self.end_date_edit)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        self.priority_combo.setCurrentText("Medium")
        form_layout.addRow("Priority:", self.priority_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Not Started", "In Progress", "Completed", "On Hold"])
        form_layout.addRow("Status:", self.status_combo)
        
        self.progress_spin = QSpinBox()
        self.progress_spin.setRange(0, 100)
        self.progress_spin.setSuffix("%")
        form_layout.addRow("Progress:", self.progress_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_data(self):
        """Load milestone data into form"""
        if not self.milestone_data:
            return
            
        self.name_edit.setText(self.milestone_data.get("name", ""))
        self.description_edit.setPlainText(self.milestone_data.get("description", ""))
        
        start_date = self.milestone_data.get("start_date")
        if start_date:
            self.start_date_edit.setDate(QDate.fromString(start_date, Qt.DateFormat.ISODate))
            
        end_date = self.milestone_data.get("end_date")
        if end_date:
            self.end_date_edit.setDate(QDate.fromString(end_date, Qt.DateFormat.ISODate))
            
        self.priority_combo.setCurrentText(self.milestone_data.get("priority", "Medium"))
        self.status_combo.setCurrentText(self.milestone_data.get("status", "Not Started"))
        self.progress_spin.setValue(self.milestone_data.get("progress", 0))
        
    def get_milestone_data(self) -> Dict:
        """Get milestone data from form"""
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText(),
            "start_date": self.start_date_edit.date().toString(Qt.DateFormat.ISODate),
            "end_date": self.end_date_edit.date().toString(Qt.DateFormat.ISODate),
            "priority": self.priority_combo.currentText(),
            "status": self.status_combo.currentText(),
            "progress": self.progress_spin.value(),
            "created_date": datetime.now().isoformat(),
            "id": self.milestone_data.get("id", datetime.now().timestamp())
        }


class TimelineWidget(QWidget):
    """Widget for displaying project timeline"""
    
    milestone_selected = pyqtSignal(dict)
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.milestones: List[Dict] = []
        self.setup_ui()
        self.load_milestones()
        
    def setup_ui(self):
        """Setup the timeline UI"""
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.add_milestone_btn = QPushButton("Add Milestone")
        self.add_milestone_btn.clicked.connect(self.add_milestone)
        
        self.edit_milestone_btn = QPushButton("Edit Milestone")
        self.edit_milestone_btn.clicked.connect(self.edit_milestone)
        self.edit_milestone_btn.setEnabled(False)
        
        self.delete_milestone_btn = QPushButton("Delete Milestone")
        self.delete_milestone_btn.clicked.connect(self.delete_milestone)
        self.delete_milestone_btn.setEnabled(False)
        
        controls_layout.addWidget(self.add_milestone_btn)
        controls_layout.addWidget(self.edit_milestone_btn)
        controls_layout.addWidget(self.delete_milestone_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Timeline table
        self.timeline_table = QTableWidget()
        self.timeline_table.setColumnCount(7)
        self.timeline_table.setHorizontalHeaderLabels([
            "Name", "Description", "Start Date", "End Date", "Priority", "Status", "Progress"
        ])
        
        # Configure table
        header = self.timeline_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        self.timeline_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.timeline_table.setAlternatingRowColors(True)
        self.timeline_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.timeline_table)
        
    def load_milestones(self):
        """Load milestones from project data"""
        timeline_file = Path(self.project.project_path) / "data" / "timeline.json"
        
        if timeline_file.exists():
            try:
                with open(timeline_file, 'r') as f:
                    data = json.load(f)
                    self.milestones = data.get("milestones", [])
            except Exception as e:
                print(f"Error loading timeline: {e}")
                self.milestones = []
        else:
            self.milestones = []
            
        self.refresh_timeline()
        
    def save_milestones(self):
        """Save milestones to project data"""
        timeline_file = Path(self.project.project_path) / "data" / "timeline.json"
        timeline_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "milestones": self.milestones,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(timeline_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save timeline: {e}")
            
    def refresh_timeline(self):
        """Refresh the timeline table"""
        self.timeline_table.setRowCount(len(self.milestones))
        
        for row, milestone in enumerate(self.milestones):
            # Name
            name_item = QTableWidgetItem(milestone.get("name", ""))
            self.timeline_table.setItem(row, 0, name_item)
            
            # Description
            desc_item = QTableWidgetItem(milestone.get("description", ""))
            self.timeline_table.setItem(row, 1, desc_item)
            
            # Start Date
            start_item = QTableWidgetItem(milestone.get("start_date", ""))
            self.timeline_table.setItem(row, 2, start_item)
            
            # End Date
            end_item = QTableWidgetItem(milestone.get("end_date", ""))
            self.timeline_table.setItem(row, 3, end_item)
            
            # Priority
            priority_item = QTableWidgetItem(milestone.get("priority", ""))
            priority = milestone.get("priority", "Medium")
            if priority == "Critical":
                priority_item.setBackground(QColor(255, 200, 200))
            elif priority == "High":
                priority_item.setBackground(QColor(255, 230, 200))
            self.timeline_table.setItem(row, 4, priority_item)
            
            # Status
            status_item = QTableWidgetItem(milestone.get("status", ""))
            status = milestone.get("status", "Not Started")
            if status == "Completed":
                status_item.setBackground(QColor(200, 255, 200))
            elif status == "In Progress":
                status_item.setBackground(QColor(200, 230, 255))
            elif status == "On Hold":
                status_item.setBackground(QColor(255, 255, 200))
            self.timeline_table.setItem(row, 5, status_item)
            
            # Progress
            progress_item = QTableWidgetItem(f"{milestone.get('progress', 0)}%")
            self.timeline_table.setItem(row, 6, progress_item)
            
    def on_selection_changed(self):
        """Handle selection change"""
        has_selection = bool(self.timeline_table.selectedItems())
        self.edit_milestone_btn.setEnabled(has_selection)
        self.delete_milestone_btn.setEnabled(has_selection)
        
        if has_selection:
            row = self.timeline_table.currentRow()
            if 0 <= row < len(self.milestones):
                self.milestone_selected.emit(self.milestones[row])
                
    def add_milestone(self):
        """Add a new milestone"""
        dialog = MilestoneDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            milestone_data = dialog.get_milestone_data()
            self.milestones.append(milestone_data)
            self.save_milestones()
            self.refresh_timeline()
            
    def edit_milestone(self):
        """Edit selected milestone"""
        row = self.timeline_table.currentRow()
        if 0 <= row < len(self.milestones):
            dialog = MilestoneDialog(self.milestones[row], parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                milestone_data = dialog.get_milestone_data()
                self.milestones[row] = milestone_data
                self.save_milestones()
                self.refresh_timeline()
                
    def delete_milestone(self):
        """Delete selected milestone"""
        row = self.timeline_table.currentRow()
        if 0 <= row < len(self.milestones):
            milestone = self.milestones[row]
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete milestone '{milestone.get('name', '')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                del self.milestones[row]
                self.save_milestones()
                self.refresh_timeline()


class TimelinePlannerWindow(QMainWindow):
    """Main Timeline Planner window"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_window()
        self.setup_ui()
        
    def setup_window(self):
        """Setup the window"""
        self.setWindowTitle("Timeline Planner - Lupine Engine")
        self.setMinimumSize(900, 600)
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
        
        # Timeline widget
        self.timeline_widget = TimelineWidget(self.project)
        layout.addWidget(self.timeline_widget)
