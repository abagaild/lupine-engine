"""
Asset Tracker Tool for Lupine Engine
Provides asset pipeline tracking and management
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QGroupBox, QTabWidget, QTextEdit, QDateEdit,
    QSpinBox, QMessageBox, QHeaderView, QAbstractItemView,
    QInputDialog, QDialog, QDialogButtonBox, QFormLayout,
    QFileDialog, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPixmap

from core.project import LupineProject


class AssetTypeDialog(QDialog):
    """Dialog for creating/editing asset types"""

    def __init__(self, asset_type_data: Dict = None, parent=None):
        super().__init__(parent)
        self.asset_type_data = asset_type_data or {}
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Asset Type Editor")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter asset type name...")
        form_layout.addRow("Name:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter asset type description...")
        form_layout.addRow("Description:", self.description_edit)

        self.file_extensions_edit = QLineEdit()
        self.file_extensions_edit.setPlaceholderText("e.g., .png,.jpg,.jpeg")
        form_layout.addRow("File Extensions:", self.file_extensions_edit)

        # Stages
        stages_label = QLabel("Production Stages (one per line):")
        form_layout.addRow(stages_label)

        self.stages_edit = QTextEdit()
        self.stages_edit.setMaximumHeight(100)
        self.stages_edit.setPlaceholderText("Concept\nDraft\nFinal\nApproved")
        form_layout.addRow(self.stages_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_data(self):
        """Load asset type data into form"""
        if not self.asset_type_data:
            return

        self.name_edit.setText(self.asset_type_data.get("name", ""))
        self.description_edit.setPlainText(self.asset_type_data.get("description", ""))

        extensions = self.asset_type_data.get("file_extensions", [])
        self.file_extensions_edit.setText(",".join(extensions))

        stages = self.asset_type_data.get("stages", [])
        self.stages_edit.setPlainText("\n".join(stages))

    def get_asset_type_data(self) -> Dict:
        """Get asset type data from form"""
        extensions_text = self.file_extensions_edit.text().strip()
        extensions = [ext.strip() for ext in extensions_text.split(",") if ext.strip()]

        stages_text = self.stages_edit.toPlainText().strip()
        stages = [stage.strip() for stage in stages_text.split("\n") if stage.strip()]

        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText(),
            "file_extensions": extensions,
            "stages": stages,
            "created_date": self.asset_type_data.get("created_date", datetime.now().isoformat()),
            "id": self.asset_type_data.get("id", datetime.now().timestamp())
        }


class AssetDialog(QDialog):
    """Dialog for creating/editing assets"""

    def __init__(self, asset_data: Dict = None, asset_types: List[Dict] = None, parent=None):
        super().__init__(parent)
        self.asset_data = asset_data or {}
        self.asset_types = asset_types or []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Asset Editor")
        self.setModal(True)
        self.resize(450, 400)

        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter asset name...")
        form_layout.addRow("Name:", self.name_edit)

        self.type_combo = QComboBox()
        for asset_type in self.asset_types:
            self.type_combo.addItem(asset_type.get("name", ""))
        form_layout.addRow("Type:", self.type_combo)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter asset description...")
        form_layout.addRow("Description:", self.description_edit)

        # File path
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select asset file...")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_btn)
        form_layout.addRow("File Path:", file_layout)

        self.stage_combo = QComboBox()
        self.stage_combo.addItems(["Concept", "Draft", "Final", "Approved"])
        form_layout.addRow("Current Stage:", self.stage_combo)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        self.priority_combo.setCurrentText("Medium")
        form_layout.addRow("Priority:", self.priority_combo)

        self.assignee_edit = QLineEdit()
        self.assignee_edit.setPlaceholderText("Enter assignee name...")
        form_layout.addRow("Assignee:", self.assignee_edit)

        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate().addDays(7))
        self.due_date_edit.setCalendarPopup(True)
        form_layout.addRow("Due Date:", self.due_date_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Enter notes...")
        form_layout.addRow("Notes:", self.notes_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Update stages when type changes
        self.type_combo.currentTextChanged.connect(self.update_stages)
        self.update_stages()

    def update_stages(self):
        """Update stage combo based on selected type"""
        type_name = self.type_combo.currentText()

        # Find the asset type
        for asset_type in self.asset_types:
            if asset_type.get("name") == type_name:
                stages = asset_type.get("stages", ["Concept", "Draft", "Final", "Approved"])
                current_stage = self.stage_combo.currentText()

                self.stage_combo.clear()
                self.stage_combo.addItems(stages)

                # Restore selection if possible
                index = self.stage_combo.findText(current_stage)
                if index >= 0:
                    self.stage_combo.setCurrentIndex(index)
                break

    def browse_file(self):
        """Browse for asset file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Asset File", "", "All Files (*.*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def load_data(self):
        """Load asset data into form"""
        if not self.asset_data:
            return

        self.name_edit.setText(self.asset_data.get("name", ""))

        asset_type = self.asset_data.get("type", "")
        index = self.type_combo.findText(asset_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        self.description_edit.setPlainText(self.asset_data.get("description", ""))
        self.file_path_edit.setText(self.asset_data.get("file_path", ""))

        stage = self.asset_data.get("stage", "")
        stage_index = self.stage_combo.findText(stage)
        if stage_index >= 0:
            self.stage_combo.setCurrentIndex(stage_index)

        self.priority_combo.setCurrentText(self.asset_data.get("priority", "Medium"))
        self.assignee_edit.setText(self.asset_data.get("assignee", ""))

        due_date = self.asset_data.get("due_date")
        if due_date:
            self.due_date_edit.setDate(QDate.fromString(due_date, Qt.DateFormat.ISODate))

        self.notes_edit.setPlainText(self.asset_data.get("notes", ""))

    def get_asset_data(self) -> Dict:
        """Get asset data from form"""
        return {
            "name": self.name_edit.text(),
            "type": self.type_combo.currentText(),
            "description": self.description_edit.toPlainText(),
            "file_path": self.file_path_edit.text(),
            "stage": self.stage_combo.currentText(),
            "priority": self.priority_combo.currentText(),
            "assignee": self.assignee_edit.text(),
            "due_date": self.due_date_edit.date().toString(Qt.DateFormat.ISODate),
            "notes": self.notes_edit.toPlainText(),
            "created_date": self.asset_data.get("created_date", datetime.now().isoformat()),
            "last_updated": datetime.now().isoformat(),
            "id": self.asset_data.get("id", datetime.now().timestamp())
        }


class AssetTrackerWidget(QWidget):
    """Main asset tracking widget"""

    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.asset_types: List[Dict] = []
        self.assets: List[Dict] = []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the tracker UI"""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Asset Types tab
        self.setup_asset_types_tab()

        # Assets tab
        self.setup_assets_tab()

        layout.addWidget(self.tab_widget)

    def setup_asset_types_tab(self):
        """Setup the asset types management tab"""
        types_widget = QWidget()
        layout = QVBoxLayout(types_widget)

        # Controls
        controls_layout = QHBoxLayout()

        self.add_type_btn = QPushButton("Add Asset Type")
        self.add_type_btn.clicked.connect(self.add_asset_type)

        self.edit_type_btn = QPushButton("Edit Type")
        self.edit_type_btn.clicked.connect(self.edit_asset_type)
        self.edit_type_btn.setEnabled(False)

        self.delete_type_btn = QPushButton("Delete Type")
        self.delete_type_btn.clicked.connect(self.delete_asset_type)
        self.delete_type_btn.setEnabled(False)

        controls_layout.addWidget(self.add_type_btn)
        controls_layout.addWidget(self.edit_type_btn)
        controls_layout.addWidget(self.delete_type_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Asset types table
        self.types_table = QTableWidget()
        self.types_table.setColumnCount(4)
        self.types_table.setHorizontalHeaderLabels([
            "Name", "Description", "File Extensions", "Stages"
        ])

        # Configure table
        header = self.types_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.types_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.types_table.setAlternatingRowColors(True)
        self.types_table.itemSelectionChanged.connect(self.on_type_selection_changed)

        layout.addWidget(self.types_table)

        self.tab_widget.addTab(types_widget, "Asset Types")

    def setup_assets_tab(self):
        """Setup the assets management tab"""
        assets_widget = QWidget()
        layout = QVBoxLayout(assets_widget)

        # Controls
        controls_layout = QHBoxLayout()

        self.add_asset_btn = QPushButton("Add Asset")
        self.add_asset_btn.clicked.connect(self.add_asset)

        self.edit_asset_btn = QPushButton("Edit Asset")
        self.edit_asset_btn.clicked.connect(self.edit_asset)
        self.edit_asset_btn.setEnabled(False)

        self.delete_asset_btn = QPushButton("Delete Asset")
        self.delete_asset_btn.clicked.connect(self.delete_asset)
        self.delete_asset_btn.setEnabled(False)

        controls_layout.addWidget(self.add_asset_btn)
        controls_layout.addWidget(self.edit_asset_btn)
        controls_layout.addWidget(self.delete_asset_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Filter controls
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Filter by Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.type_filter)

        filter_layout.addWidget(QLabel("Filter by Stage:"))
        self.stage_filter = QComboBox()
        self.stage_filter.addItem("All Stages")
        self.stage_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.stage_filter)

        filter_layout.addWidget(QLabel("Filter by Priority:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All Priorities", "Low", "Medium", "High", "Critical"])
        self.priority_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.priority_filter)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Assets table
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(8)
        self.assets_table.setHorizontalHeaderLabels([
            "Name", "Type", "Stage", "Priority", "Assignee", "Due Date", "File Path", "Notes"
        ])

        # Configure table
        header = self.assets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.assets_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.assets_table.setAlternatingRowColors(True)
        self.assets_table.itemSelectionChanged.connect(self.on_asset_selection_changed)

        layout.addWidget(self.assets_table)

        self.tab_widget.addTab(assets_widget, "Assets")

    def load_data(self):
        """Load asset data from project"""
        assets_file = Path(self.project.project_path) / "data" / "assets.json"

        if assets_file.exists():
            try:
                with open(assets_file, 'r') as f:
                    data = json.load(f)
                    self.asset_types = data.get("asset_types", [])
                    self.assets = data.get("assets", [])
            except Exception as e:
                print(f"Error loading assets: {e}")
                self.asset_types = []
                self.assets = []
        else:
            self.asset_types = []
            self.assets = []

        self.refresh_all()

    def save_data(self):
        """Save asset data to project"""
        assets_file = Path(self.project.project_path) / "data" / "assets.json"
        assets_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "asset_types": self.asset_types,
            "assets": self.assets,
            "last_updated": datetime.now().isoformat()
        }

        try:
            with open(assets_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save assets: {e}")

    def refresh_all(self):
        """Refresh all UI elements"""
        self.refresh_asset_types()
        self.refresh_assets()
        self.update_filters()

    def refresh_asset_types(self):
        """Refresh the asset types table"""
        self.types_table.setRowCount(len(self.asset_types))

        for row, asset_type in enumerate(self.asset_types):
            # Name
            name_item = QTableWidgetItem(asset_type.get("name", ""))
            self.types_table.setItem(row, 0, name_item)

            # Description
            desc_item = QTableWidgetItem(asset_type.get("description", ""))
            self.types_table.setItem(row, 1, desc_item)

            # File Extensions
            extensions = asset_type.get("file_extensions", [])
            ext_item = QTableWidgetItem(", ".join(extensions))
            self.types_table.setItem(row, 2, ext_item)

            # Stages
            stages = asset_type.get("stages", [])
            stages_item = QTableWidgetItem(", ".join(stages))
            self.types_table.setItem(row, 3, stages_item)

    def refresh_assets(self):
        """Refresh the assets table"""
        # Filter assets based on current filters
        filtered_assets = []
        for asset in self.assets:
            if self.should_show_asset(asset):
                filtered_assets.append(asset)

        self.assets_table.setRowCount(len(filtered_assets))

        for row, asset in enumerate(filtered_assets):
            # Name
            name_item = QTableWidgetItem(asset.get("name", ""))
            self.assets_table.setItem(row, 0, name_item)

            # Type
            type_item = QTableWidgetItem(asset.get("type", ""))
            self.assets_table.setItem(row, 1, type_item)

            # Stage
            stage_item = QTableWidgetItem(asset.get("stage", ""))
            self.assets_table.setItem(row, 2, stage_item)

            # Priority
            priority_item = QTableWidgetItem(asset.get("priority", ""))
            priority = asset.get("priority", "Medium")
            if priority == "Critical":
                priority_item.setBackground(QColor(255, 200, 200))
            elif priority == "High":
                priority_item.setBackground(QColor(255, 230, 200))
            self.assets_table.setItem(row, 3, priority_item)

            # Assignee
            assignee_item = QTableWidgetItem(asset.get("assignee", ""))
            self.assets_table.setItem(row, 4, assignee_item)

            # Due Date
            due_date_item = QTableWidgetItem(asset.get("due_date", ""))
            # Check if overdue
            due_date = asset.get("due_date")
            if due_date:
                try:
                    due = datetime.fromisoformat(due_date)
                    if due.date() < datetime.now().date():
                        due_date_item.setBackground(QColor(255, 230, 230))
                except:
                    pass
            self.assets_table.setItem(row, 5, due_date_item)

            # File Path
            file_path_item = QTableWidgetItem(asset.get("file_path", ""))
            self.assets_table.setItem(row, 6, file_path_item)

            # Notes
            notes_item = QTableWidgetItem(asset.get("notes", ""))
            self.assets_table.setItem(row, 7, notes_item)

    def should_show_asset(self, asset: Dict) -> bool:
        """Check if asset should be shown based on filters"""
        type_filter = self.type_filter.currentText()
        stage_filter = self.stage_filter.currentText()
        priority_filter = self.priority_filter.currentText()

        if type_filter != "All Types" and asset.get("type") != type_filter:
            return False

        if stage_filter != "All Stages" and asset.get("stage") != stage_filter:
            return False

        if priority_filter != "All Priorities" and asset.get("priority") != priority_filter:
            return False

        return True

    def update_filters(self):
        """Update filter combo boxes"""
        # Update type filter
        current_type = self.type_filter.currentText()
        self.type_filter.clear()
        self.type_filter.addItem("All Types")
        for asset_type in self.asset_types:
            self.type_filter.addItem(asset_type.get("name", ""))

        # Restore selection
        index = self.type_filter.findText(current_type)
        if index >= 0:
            self.type_filter.setCurrentIndex(index)

        # Update stage filter
        current_stage = self.stage_filter.currentText()
        self.stage_filter.clear()
        self.stage_filter.addItem("All Stages")

        stages = set()
        for asset_type in self.asset_types:
            stages.update(asset_type.get("stages", []))

        for stage in sorted(stages):
            self.stage_filter.addItem(stage)

        # Restore selection
        index = self.stage_filter.findText(current_stage)
        if index >= 0:
            self.stage_filter.setCurrentIndex(index)

    def apply_filters(self):
        """Apply current filters"""
        self.refresh_assets()

    def on_type_selection_changed(self):
        """Handle asset type selection change"""
        has_selection = bool(self.types_table.selectedItems())
        self.edit_type_btn.setEnabled(has_selection)
        self.delete_type_btn.setEnabled(has_selection)

    def on_asset_selection_changed(self):
        """Handle asset selection change"""
        has_selection = bool(self.assets_table.selectedItems())
        self.edit_asset_btn.setEnabled(has_selection)
        self.delete_asset_btn.setEnabled(has_selection)

    def add_asset_type(self):
        """Add a new asset type"""
        dialog = AssetTypeDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            type_data = dialog.get_asset_type_data()
            self.asset_types.append(type_data)
            self.save_data()
            self.refresh_all()

    def edit_asset_type(self):
        """Edit selected asset type"""
        row = self.types_table.currentRow()
        if 0 <= row < len(self.asset_types):
            dialog = AssetTypeDialog(self.asset_types[row], parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                type_data = dialog.get_asset_type_data()
                self.asset_types[row] = type_data
                self.save_data()
                self.refresh_all()

    def delete_asset_type(self):
        """Delete selected asset type"""
        row = self.types_table.currentRow()
        if 0 <= row < len(self.asset_types):
            asset_type = self.asset_types[row]
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete asset type '{asset_type.get('name', '')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                del self.asset_types[row]
                self.save_data()
                self.refresh_all()

    def add_asset(self):
        """Add a new asset"""
        if not self.asset_types:
            QMessageBox.warning(self, "Warning", "Please create at least one asset type first.")
            return

        dialog = AssetDialog(asset_types=self.asset_types, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            asset_data = dialog.get_asset_data()
            self.assets.append(asset_data)
            self.save_data()
            self.refresh_assets()

    def edit_asset(self):
        """Edit selected asset"""
        row = self.assets_table.currentRow()
        if row >= 0:
            # Find the actual asset (considering filters)
            filtered_assets = [a for a in self.assets if self.should_show_asset(a)]
            if 0 <= row < len(filtered_assets):
                asset = filtered_assets[row]
                dialog = AssetDialog(asset, self.asset_types, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    updated_asset = dialog.get_asset_data()

                    # Find and update the original asset
                    for i, original_asset in enumerate(self.assets):
                        if original_asset.get("id") == asset.get("id"):
                            self.assets[i] = updated_asset
                            break

                    self.save_data()
                    self.refresh_assets()

    def delete_asset(self):
        """Delete selected asset"""
        row = self.assets_table.currentRow()
        if row >= 0:
            # Find the actual asset (considering filters)
            filtered_assets = [a for a in self.assets if self.should_show_asset(a)]
            if 0 <= row < len(filtered_assets):
                asset = filtered_assets[row]
                reply = QMessageBox.question(
                    self, "Confirm Delete",
                    f"Are you sure you want to delete asset '{asset.get('name', '')}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # Find and remove the original asset
                    self.assets = [a for a in self.assets if a.get("id") != asset.get("id")]
                    self.save_data()
                    self.refresh_assets()


class AssetTrackerWindow(QMainWindow):
    """Main Asset Tracker window"""

    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_window()
        self.setup_ui()

    def setup_window(self):
        """Setup the window"""
        self.setWindowTitle("Asset Tracker - Lupine Engine")
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

        # Asset tracker widget
        self.tracker_widget = AssetTrackerWidget(self.project)
        layout.addWidget(self.tracker_widget)