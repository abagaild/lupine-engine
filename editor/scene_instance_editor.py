"""
Advanced Scene Instance Editor for Lupine Engine
Provides comprehensive editing capabilities for scene instances
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget,
    QTreeWidgetItem, QSplitter, QGroupBox, QCheckBox, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QTextEdit, QTabWidget, QScrollArea, QFrame,
    QMessageBox, QFileDialog, QProgressBar, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette
from typing import Dict, Any, List, Optional
from pathlib import Path


class SceneInstanceEditor(QWidget):
    """
    Advanced editor for scene instances with features:
    - Property override management
    - Visual diff display
    - Instance variant creation
    - Performance monitoring
    - Dependency visualization
    """
    
    instance_changed = pyqtSignal()
    override_added = pyqtSignal(str, str, object)  # node_path, property, value
    override_removed = pyqtSignal(str, str)  # node_path, property
    
    def __init__(self, scene_instance=None, parent=None):
        super().__init__(parent)
        self.scene_instance = scene_instance
        self.original_scene = None
        self.property_editors = {}
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_display)
        self.update_timer.setSingleShot(True)
        
        self.setup_ui()
        if scene_instance:
            self.load_scene_instance(scene_instance)

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Header with instance info
        self.create_header_section(layout)
        
        # Main content in tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Property Overrides tab
        self.create_overrides_tab()
        
        # Scene Hierarchy tab
        self.create_hierarchy_tab()
        
        # Performance tab
        self.create_performance_tab()
        
        # Dependencies tab
        self.create_dependencies_tab()

    def create_header_section(self, layout):
        """Create the header section with basic instance info"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        
        # Instance name and scene path
        info_layout = QHBoxLayout()
        
        self.instance_name_label = QLabel("Instance: N/A")
        self.instance_name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(self.instance_name_label)
        
        info_layout.addStretch()
        
        self.scene_path_label = QLabel("Scene: N/A")
        info_layout.addWidget(self.scene_path_label)
        
        header_layout.addLayout(info_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.reload_btn = QPushButton("Reload from Scene")
        self.reload_btn.clicked.connect(self.reload_instance)
        button_layout.addWidget(self.reload_btn)
        
        self.create_variant_btn = QPushButton("Create Variant")
        self.create_variant_btn.clicked.connect(self.create_variant)
        button_layout.addWidget(self.create_variant_btn)
        
        self.break_instance_btn = QPushButton("Break Instance")
        self.break_instance_btn.clicked.connect(self.break_instance)
        button_layout.addWidget(self.break_instance_btn)
        
        button_layout.addStretch()
        
        self.edit_original_btn = QPushButton("Edit Original Scene")
        self.edit_original_btn.clicked.connect(self.edit_original_scene)
        button_layout.addWidget(self.edit_original_btn)
        
        header_layout.addLayout(button_layout)
        layout.addWidget(header_frame)

    def create_overrides_tab(self):
        """Create the property overrides management tab"""
        overrides_widget = QWidget()
        layout = QVBoxLayout(overrides_widget)
        
        # Override controls
        controls_layout = QHBoxLayout()
        
        add_override_btn = QPushButton("Add Override")
        add_override_btn.clicked.connect(self.add_property_override)
        controls_layout.addWidget(add_override_btn)
        
        remove_override_btn = QPushButton("Remove Override")
        remove_override_btn.clicked.connect(self.remove_property_override)
        controls_layout.addWidget(remove_override_btn)
        
        controls_layout.addStretch()
        
        reset_overrides_btn = QPushButton("Reset All Overrides")
        reset_overrides_btn.clicked.connect(self.reset_all_overrides)
        controls_layout.addWidget(reset_overrides_btn)
        
        layout.addLayout(controls_layout)
        
        # Overrides table
        self.overrides_table = QTableWidget()
        self.overrides_table.setColumnCount(4)
        self.overrides_table.setHorizontalHeaderLabels([
            "Node Path", "Property", "Override Value", "Original Value"
        ])
        self.overrides_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.overrides_table)
        
        # Override diff view
        diff_group = QGroupBox("Property Diff")
        diff_layout = QVBoxLayout(diff_group)
        
        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)
        self.diff_text.setMaximumHeight(150)
        diff_layout.addWidget(self.diff_text)
        
        layout.addWidget(diff_group)
        
        self.tab_widget.addTab(overrides_widget, "Property Overrides")

    def create_hierarchy_tab(self):
        """Create the scene hierarchy visualization tab"""
        hierarchy_widget = QWidget()
        layout = QVBoxLayout(hierarchy_widget)
        
        # Hierarchy tree
        self.hierarchy_tree = QTreeWidget()
        self.hierarchy_tree.setHeaderLabels(["Node", "Type", "Overridden"])
        self.hierarchy_tree.itemSelectionChanged.connect(self.on_node_selected)
        layout.addWidget(self.hierarchy_tree)
        
        # Node details
        details_group = QGroupBox("Node Details")
        details_layout = QVBoxLayout(details_group)
        
        self.node_details_text = QTextEdit()
        self.node_details_text.setReadOnly(True)
        self.node_details_text.setMaximumHeight(100)
        details_layout.addWidget(self.node_details_text)
        
        layout.addWidget(details_group)
        
        self.tab_widget.addTab(hierarchy_widget, "Scene Hierarchy")

    def create_performance_tab(self):
        """Create the performance monitoring tab"""
        performance_widget = QWidget()
        layout = QVBoxLayout(performance_widget)
        
        # Performance metrics
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.performance_labels = {}
        metrics = [
            "Load Time", "Memory Usage", "Node Count", "Override Count",
            "Complexity Score", "Last Updated"
        ]
        
        for metric in metrics:
            label = QLabel(f"{metric}: N/A")
            self.performance_labels[metric] = label
            metrics_layout.addWidget(label)
        
        layout.addWidget(metrics_group)
        
        # Memory usage chart placeholder
        memory_group = QGroupBox("Memory Usage Over Time")
        memory_layout = QVBoxLayout(memory_group)
        
        self.memory_chart_label = QLabel("Memory usage chart would go here")
        self.memory_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.memory_chart_label.setMinimumHeight(200)
        self.memory_chart_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        memory_layout.addWidget(self.memory_chart_label)
        
        layout.addWidget(memory_group)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Performance Data")
        refresh_btn.clicked.connect(self.refresh_performance_data)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        self.tab_widget.addTab(performance_widget, "Performance")

    def create_dependencies_tab(self):
        """Create the dependencies visualization tab"""
        dependencies_widget = QWidget()
        layout = QVBoxLayout(dependencies_widget)
        
        # Dependencies tree
        deps_group = QGroupBox("Scene Dependencies")
        deps_layout = QVBoxLayout(deps_group)
        
        self.dependencies_tree = QTreeWidget()
        self.dependencies_tree.setHeaderLabels(["Scene", "Type", "Status"])
        deps_layout.addWidget(self.dependencies_tree)
        
        layout.addWidget(deps_group)
        
        # Dependents (scenes that use this one)
        dependents_group = QGroupBox("Scenes Using This Instance")
        dependents_layout = QVBoxLayout(dependents_group)
        
        self.dependents_tree = QTreeWidget()
        self.dependents_tree.setHeaderLabels(["Scene", "Instance Count"])
        dependents_layout.addWidget(self.dependents_tree)
        
        layout.addWidget(dependents_group)
        
        # Validation
        validation_group = QGroupBox("Dependency Validation")
        validation_layout = QVBoxLayout(validation_group)
        
        validate_btn = QPushButton("Validate Dependencies")
        validate_btn.clicked.connect(self.validate_dependencies)
        validation_layout.addWidget(validate_btn)
        
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setMaximumHeight(100)
        validation_layout.addWidget(self.validation_text)
        
        layout.addWidget(validation_group)
        
        self.tab_widget.addTab(dependencies_widget, "Dependencies")

    def load_scene_instance(self, scene_instance):
        """Load a scene instance for editing"""
        self.scene_instance = scene_instance
        
        if not scene_instance:
            return
        
        # Update header info
        self.instance_name_label.setText(f"Instance: {scene_instance.name}")
        self.scene_path_label.setText(f"Scene: {scene_instance.scene_path}")
        
        # Load original scene for comparison
        self.load_original_scene()
        
        # Refresh all displays
        self.refresh_all_displays()

    def load_original_scene(self):
        """Load the original scene for comparison"""
        if not self.scene_instance or not self.scene_instance.scene_path:
            return
        
        try:
            from core.project import get_current_project
            project = get_current_project()
            if project and project.scene_manager:
                self.original_scene = project.scene_manager.load_scene(
                    self.scene_instance.scene_path
                )
        except Exception as e:
            print(f"Error loading original scene: {e}")

    def refresh_all_displays(self):
        """Refresh all display elements"""
        self.refresh_overrides_table()
        self.refresh_hierarchy_tree()
        self.refresh_performance_data()
        self.refresh_dependencies()
        self.refresh_diff_display()

    def refresh_overrides_table(self):
        """Refresh the property overrides table"""
        if not self.scene_instance:
            return
        
        overrides = self.scene_instance.property_overrides
        self.overrides_table.setRowCount(0)
        
        row = 0
        for node_path, properties in overrides.items():
            for prop_name, override_value in properties.items():
                self.overrides_table.insertRow(row)
                
                # Node path
                self.overrides_table.setItem(row, 0, QTableWidgetItem(node_path))
                
                # Property name
                self.overrides_table.setItem(row, 1, QTableWidgetItem(prop_name))
                
                # Override value
                self.overrides_table.setItem(row, 2, QTableWidgetItem(str(override_value)))
                
                # Original value
                original_value = self.get_original_property_value(node_path, prop_name)
                self.overrides_table.setItem(row, 3, QTableWidgetItem(str(original_value)))
                
                row += 1

    def refresh_hierarchy_tree(self):
        """Refresh the scene hierarchy tree"""
        self.hierarchy_tree.clear()
        
        if not self.scene_instance:
            return
        
        # Add instance root
        root_item = QTreeWidgetItem(self.hierarchy_tree)
        root_item.setText(0, self.scene_instance.name)
        root_item.setText(1, "SceneInstance")
        root_item.setText(2, "Yes" if self.scene_instance.property_overrides else "No")
        
        # Add children recursively
        for child in self.scene_instance.children:
            self.add_hierarchy_node(root_item, child)
        
        self.hierarchy_tree.expandAll()

    def add_hierarchy_node(self, parent_item, node):
        """Add a node to the hierarchy tree"""
        item = QTreeWidgetItem(parent_item)
        item.setText(0, node.name)
        item.setText(1, node.type)
        
        # Check if this node has overrides
        node_path = self.get_node_path(node)
        has_overrides = node_path in self.scene_instance.property_overrides
        item.setText(2, "Yes" if has_overrides else "No")
        
        # Store node reference
        item.setData(0, Qt.ItemDataRole.UserRole, node)
        
        # Add children
        for child in node.children:
            self.add_hierarchy_node(item, child)

    def get_node_path(self, node):
        """Get the path to a node from the scene instance root"""
        path_parts = []
        current = node
        
        while current and current != self.scene_instance:
            path_parts.append(current.name)
            current = current.parent
        
        return "/".join(reversed(path_parts))

    def refresh_performance_data(self):
        """Refresh performance metrics display"""
        if not self.scene_instance:
            return
        
        try:
            # Get memory usage
            memory_stats = self.scene_instance.get_memory_usage()
            
            # Update labels
            self.performance_labels["Memory Usage"].setText(
                f"Memory Usage: {memory_stats.get('instance_size', 0)} bytes"
            )
            self.performance_labels["Node Count"].setText(
                f"Node Count: {memory_stats.get('total_nodes', 0)}"
            )
            self.performance_labels["Override Count"].setText(
                f"Override Count: {memory_stats.get('override_count', 0)}"
            )
            
            # Additional metrics would be calculated here
            
        except Exception as e:
            print(f"Error refreshing performance data: {e}")

    def refresh_dependencies(self):
        """Refresh dependencies display"""
        # This would be implemented with actual dependency tracking
        pass

    def refresh_diff_display(self):
        """Refresh the property diff display"""
        if not self.scene_instance:
            return
        
        try:
            diff = self.scene_instance.get_override_diff()
            diff_text = "Property Overrides:\n\n"
            
            for node_path, properties in diff.items():
                diff_text += f"Node: {node_path}\n"
                for prop_name, values in properties.items():
                    original = values.get('original', 'N/A')
                    override = values.get('override', 'N/A')
                    diff_text += f"  {prop_name}: {original} → {override}\n"
                diff_text += "\n"
            
            self.diff_text.setPlainText(diff_text)
            
        except Exception as e:
            print(f"Error refreshing diff display: {e}")

    def get_original_property_value(self, node_path, property_name):
        """Get the original property value from the source scene"""
        if not self.scene_instance:
            return "N/A"
        
        try:
            return self.scene_instance._get_original_property_value(node_path, property_name)
        except:
            return "N/A"

    # ========== EVENT HANDLERS ==========
    
    def on_node_selected(self):
        """Handle node selection in hierarchy tree"""
        current_item = self.hierarchy_tree.currentItem()
        if not current_item:
            return
        
        node = current_item.data(0, Qt.ItemDataRole.UserRole)
        if node:
            # Display node details
            details = f"Name: {node.name}\n"
            details += f"Type: {node.type}\n"
            details += f"Children: {len(node.children)}\n"
            
            # Add property information
            if hasattr(node, 'properties'):
                details += f"Properties: {len(node.properties)}\n"
            
            self.node_details_text.setPlainText(details)

    def add_property_override(self):
        """Add a new property override"""
        # This would open a dialog to select node and property
        QMessageBox.information(self, "Add Override", "Property override dialog would open here")

    def remove_property_override(self):
        """Remove selected property override"""
        current_row = self.overrides_table.currentRow()
        if current_row >= 0:
            self.overrides_table.removeRow(current_row)
            # Also remove from scene instance
            # Implementation would go here

    def reset_all_overrides(self):
        """Reset all property overrides"""
        reply = QMessageBox.question(
            self, "Reset Overrides", 
            "Are you sure you want to reset all property overrides?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.scene_instance:
                self.scene_instance.property_overrides.clear()
                self.refresh_all_displays()

    def reload_instance(self):
        """Reload the instance from its source scene"""
        if self.scene_instance:
            try:
                from core.project import get_current_project
                project = get_current_project()
                if project and project.scene_manager:
                    self.scene_instance.reload_from_scene(project.scene_manager)
                    self.refresh_all_displays()
                    QMessageBox.information(self, "Reload", "Instance reloaded successfully")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to reload instance: {e}")

    def create_variant(self):
        """Create a variant of this instance"""
        if self.scene_instance:
            variant = self.scene_instance.create_variant(f"{self.scene_instance.name}_variant")
            QMessageBox.information(self, "Variant Created", f"Created variant: {variant.name}")

    def break_instance(self):
        """Break the scene instance into regular nodes"""
        reply = QMessageBox.question(
            self, "Break Instance", 
            "Are you sure you want to break this scene instance? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.scene_instance:
                children = self.scene_instance.break_instance()
                QMessageBox.information(self, "Instance Broken", f"Instance broken into {len(children)} nodes")

    def edit_original_scene(self):
        """Open the original scene for editing"""
        if self.scene_instance and self.scene_instance.scene_path:
            # This would signal the main editor to open the scene
            QMessageBox.information(self, "Edit Scene", f"Would open: {self.scene_instance.scene_path}")

    def validate_dependencies(self):
        """Validate scene dependencies"""
        if self.scene_instance:
            issues = self.scene_instance.validate_integrity()
            if issues:
                self.validation_text.setPlainText("\n".join(issues))
            else:
                self.validation_text.setPlainText("No dependency issues found.")

    def refresh_display(self):
        """Refresh the display (called by timer)"""
        self.refresh_all_displays()
