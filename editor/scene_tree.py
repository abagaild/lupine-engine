"""
Scene Tree Widget for Lupine Engine
Displays the hierarchical structure of nodes in the current scene
"""

import json
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QMenu, QMessageBox, QPushButton, QHBoxLayout, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from core.project import LupineProject
from core.node_registry import get_node_registry
from .add_node_dialog import AddNodeDialog


class SceneTreeWidget(QWidget):
    """Widget for displaying and editing scene hierarchy"""
    
    node_selected = pyqtSignal(dict)  # Emitted when a node is selected
    node_changed = pyqtSignal(dict)   # Emitted when a node is modified
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.current_scene_data = None
        self.current_scene_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Add node button
        button_layout = QHBoxLayout()
        self.add_node_btn = QPushButton("Add Node")
        self.add_node_btn.clicked.connect(self.add_node)
        button_layout.addWidget(self.add_node_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Scene", "Visible"])
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree.itemChanged.connect(self.on_item_changed)

        # Set column widths
        self.tree.setColumnWidth(0, 200)  # Scene name column
        self.tree.setColumnWidth(1, 60)   # Visibility column
        
        # Enable drag and drop for reordering
        self.tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)

        # Connect drag and drop events
        self.tree.model().rowsMoved.connect(self.on_rows_moved)
        
        layout.addWidget(self.tree)
    
    def set_current_scene(self, scene_path: str):
        """Set the current scene to display"""
        self.current_scene_path = scene_path

        # Load scene data
        scene_file = self.project.get_absolute_path(scene_path)
        if scene_file.exists():
            try:
                with open(scene_file, 'r') as f:
                    self.current_scene_data = json.load(f)
                self.refresh_tree()
            except Exception as e:
                print(f"Error loading scene: {e}")
                self.current_scene_data = None
                self.tree.clear()
        else:
            self.current_scene_data = None
            self.tree.clear()

    def set_scene_data(self, scene_data: dict):
        """Set scene data directly (for syncing with main editor)"""
        # Store the currently selected node name to restore selection after refresh
        selected_node_name = None
        selected_items = self.tree.selectedItems()
        if selected_items:
            selected_node_data = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
            if selected_node_data:
                selected_node_name = selected_node_data.get("name", "")

        self.current_scene_data = scene_data
        self.refresh_tree()

        # Restore selection if we had one
        if selected_node_name:
            self.select_node_by_name(selected_node_name)
    
    def refresh_tree(self):
        """Refresh the tree display"""
        self.tree.clear()
        
        if not self.current_scene_data:
            return
        
        # Add root nodes
        nodes = self.current_scene_data.get("nodes", [])
        for node_data in nodes:
            self.add_node_to_tree(node_data, None)
        
        # Expand all items
        self.tree.expandAll()
    
    def add_node_to_tree(self, node_data: Dict[str, Any], parent_item: Optional[QTreeWidgetItem]):
        """Add a node to the tree widget"""
        # Create tree item
        if parent_item:
            item = QTreeWidgetItem(parent_item)
        else:
            item = QTreeWidgetItem(self.tree)

        # Set node name and type
        node_name = node_data.get("name", "Unnamed")
        node_type = node_data.get("type", "Node")

        # Special handling for scene instances
        if node_type == "SceneInstance":
            scene_path = node_data.get("scene_path", "")
            if scene_path:
                scene_name = scene_path.split("/")[-1].replace(".scene", "")
                item.setText(0, f"📁 {node_name} ({scene_name})")
            else:
                item.setText(0, f"📁 {node_name} (No Scene)")
        else:
            item.setText(0, f"{node_name} ({node_type})")

        # Store node data
        item.setData(0, Qt.ItemDataRole.UserRole, node_data)

        # Make item editable
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

        # Add visibility toggle button
        self._add_visibility_toggle(item, node_data)

        # Add children
        children = node_data.get("children", [])
        for child_data in children:
            self.add_node_to_tree(child_data, item)

        return item

    def _add_visibility_toggle(self, item: QTreeWidgetItem, node_data: Dict[str, Any]):
        """Add visibility toggle button to tree item"""
        # Create visibility checkbox
        visibility_checkbox = QCheckBox()
        visibility_checkbox.setChecked(node_data.get("visible", True))
        visibility_checkbox.setToolTip("Toggle node visibility")

        # Connect to visibility change handler
        visibility_checkbox.stateChanged.connect(
            lambda state, item=item: self._on_visibility_changed(item, state == Qt.CheckState.Checked.value)
        )

        # Set the checkbox as a widget for the tree item
        self.tree.setItemWidget(item, 1, visibility_checkbox)

    def _on_visibility_changed(self, item: QTreeWidgetItem, visible: bool):
        """Handle visibility toggle"""
        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if node_data:
            node_data["visible"] = visible

            # Update visual appearance of the item
            font = item.font(0)
            if visible:
                font.setStrikeOut(False)
                item.setForeground(0, self.palette().color(self.palette().ColorRole.Text))
            else:
                font.setStrikeOut(True)
                item.setForeground(0, self.palette().color(self.palette().ColorRole.PlaceholderText))
            item.setFont(0, font)

            # Synchronize to scene data
            self.sync_tree_to_scene_data()

            # Emit change signal
            self.node_changed.emit(node_data)

    def on_selection_changed(self):
        """Handle tree selection change"""
        selected_items = self.tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            node_data = item.data(0, Qt.ItemDataRole.UserRole)
            if node_data:
                # Get the current reference from scene data instead of the tree copy
                node_name = node_data.get("name", "")
                current_node_ref = self.find_node_in_scene_data(node_name)
                if current_node_ref:
                    self.node_selected.emit(current_node_ref)
                else:
                    # Fallback to tree copy if not found in scene data
                    self.node_selected.emit(node_data)
    
    def on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle item name change"""
        if column == 0:
            # Extract new name from display text
            display_text = item.text(0)
            if "(" in display_text:
                new_name = display_text.split("(")[0].strip()
            else:
                new_name = display_text.strip()

            # Update node data
            node_data = item.data(0, Qt.ItemDataRole.UserRole)
            if node_data:
                old_name = node_data.get("name", "")
                if new_name != old_name:
                    node_data["name"] = new_name
                    # Update display text to include type
                    node_type = node_data.get("type", "Node")
                    item.setText(0, f"{new_name} ({node_type})")

                    # Synchronize to scene data
                    self.sync_tree_to_scene_data()

                    # Emit change signal
                    self.node_changed.emit(node_data)
    
    def show_context_menu(self, position):
        """Show context menu for tree items"""
        item = self.tree.itemAt(position)
        
        menu = QMenu(self)
        
        # Add child node
        add_child_action = QAction("Add Child Node...", self)
        add_child_action.triggered.connect(lambda: self.show_add_node_dialog(item))
        menu.addAction(add_child_action)
        
        if item:
            node_data = item.data(0, Qt.ItemDataRole.UserRole)
            node_type = node_data.get("type", "Node") if node_data else "Node"

            # Special options for scene instances
            if node_type == "SceneInstance":
                # Edit original scene
                edit_scene_action = QAction("Edit Original Scene", self)
                edit_scene_action.triggered.connect(lambda: self.edit_original_scene(item))
                menu.addAction(edit_scene_action)

                # Reload scene instance
                reload_action = QAction("Reload Scene Instance", self)
                reload_action.triggered.connect(lambda: self.reload_scene_instance(item))
                menu.addAction(reload_action)

                # Advanced scene instance options
                menu.addSeparator()

                # Create variant
                variant_action = QAction("Create Variant", self)
                variant_action.triggered.connect(lambda: self.create_instance_variant(item))
                menu.addAction(variant_action)

                # Show property overrides
                overrides_action = QAction("Show Property Overrides", self)
                overrides_action.triggered.connect(lambda: self.show_property_overrides(item))
                menu.addAction(overrides_action)

                # Performance information
                performance_action = QAction("Performance Info", self)
                performance_action.triggered.connect(lambda: self.show_performance_info(item))
                menu.addAction(performance_action)

                # Validate instance
                validate_action = QAction("Validate Instance", self)
                validate_action.triggered.connect(lambda: self.validate_scene_instance(item))
                menu.addAction(validate_action)

                menu.addSeparator()

                # Break instance (convert to regular nodes)
                break_action = QAction("Break Scene Instance", self)
                break_action.triggered.connect(lambda: self.break_scene_instance(item))
                menu.addAction(break_action)

                menu.addSeparator()

            # Duplicate node
            duplicate_action = QAction("Duplicate Node", self)
            duplicate_action.triggered.connect(lambda: self.duplicate_node(item))
            menu.addAction(duplicate_action)

            menu.addSeparator()

            # Delete node
            delete_action = QAction("Delete Node", self)
            delete_action.triggered.connect(lambda: self.delete_node(item))
            menu.addAction(delete_action)
        
        menu.exec(self.tree.mapToGlobal(position))
    
    def add_node(self):
        """Add a new root node"""
        self.show_add_node_dialog(None)

    def show_add_node_dialog(self, parent_item: Optional[QTreeWidgetItem]):
        """Show the add node dialog"""
        dialog = AddNodeDialog(self.project, self)
        dialog.node_selected.connect(lambda node_type, node_name: self.add_child_node(node_type, node_name, parent_item))
        dialog.exec()

    def add_child_node(self, node_type: str, node_name: str, parent_item: Optional[QTreeWidgetItem]):
        """Add a child node of specified type"""
        try:
            # Create node using registry
            registry = get_node_registry()
            new_node_instance = registry.create_node_instance(node_type, node_name)

            if new_node_instance is None:
                raise Exception(f"Failed to create node instance for {node_type}")

            # Convert to dict format
            new_node = new_node_instance.to_dict()

            # Add to tree first
            tree_item = self.add_node_to_tree(new_node, parent_item)

            # Synchronize tree structure back to scene data
            self.sync_tree_to_scene_data()

            # Select the new item
            self.tree.setCurrentItem(tree_item)

            # Emit change signal
            self.node_changed.emit(new_node)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create node: {e}")
    
    def duplicate_node(self, item: QTreeWidgetItem):
        """Duplicate a node"""
        if not item:
            return

        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data:
            return

        # Create copy of node data
        import copy
        new_node = copy.deepcopy(node_data)
        new_node["name"] = f"{new_node['name']}_copy"

        # Add to tree first
        parent_item = item.parent()
        tree_item = self.add_node_to_tree(new_node, parent_item)

        # Synchronize tree structure back to scene data
        self.sync_tree_to_scene_data()

        # Select the new item
        self.tree.setCurrentItem(tree_item)

        # Emit change signal
        self.node_changed.emit(new_node)
    
    def delete_node(self, item: QTreeWidgetItem):
        """Delete a node"""
        if not item:
            return
        
        # Confirm deletion
        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        node_name = node_data.get("name", "Node") if node_data else "Node"
        
        reply = QMessageBox.question(
            self, "Delete Node", 
            f"Are you sure you want to delete '{node_name}' and all its children?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Remove from tree first
        parent_item = item.parent()
        if parent_item:
            parent_item.removeChild(item)
        else:
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))

        # Synchronize tree structure back to scene data
        self.sync_tree_to_scene_data()

        # Emit change signal
        self.node_changed.emit({})
    
    def count_nodes(self) -> int:
        """Count total number of nodes in scene"""
        if not self.current_scene_data:
            return 0
        
        def count_recursive(nodes):
            count = len(nodes)
            for node in nodes:
                count += count_recursive(node.get("children", []))
            return count
        
        return count_recursive(self.current_scene_data.get("nodes", []))
    
    def get_selected_node(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected node data"""
        selected_items = self.tree.selectedItems()
        if selected_items:
            node_data = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
            if node_data:
                # Get the current reference from scene data instead of the tree copy
                node_name = node_data.get("name", "")
                current_node_ref = self.find_node_in_scene_data(node_name)
                if current_node_ref:
                    return current_node_ref
                else:
                    # Fallback to tree copy if not found in scene data
                    return node_data
        return None

    def select_node(self, node_data: dict):
        """Select a node in the tree"""
        if not node_data:
            return

        # Find the tree item for this node
        node_name = node_data.get("name", "")
        item = self.find_tree_item_by_name(self.tree.invisibleRootItem(), node_name)
        if item:
            self.tree.setCurrentItem(item)

    def select_node_by_name(self, node_name: str):
        """Select a node in the tree by name"""
        if not node_name:
            return

        # Find the tree item for this node
        item = self.find_tree_item_by_name(self.tree.invisibleRootItem(), node_name)
        if item:
            self.tree.setCurrentItem(item)

    def find_tree_item_by_name(self, parent_item, node_name: str):
        """Find a tree item by node name"""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            # Extract name from display text (remove type part)
            display_text = child.text(0)
            if "(" in display_text:
                item_name = display_text.split("(")[0].strip()
            else:
                item_name = display_text.strip()

            if item_name == node_name:
                return child
            # Check children recursively
            found = self.find_tree_item_by_name(child, node_name)
            if found:
                return found
        return None

    def find_node_in_scene_data(self, node_name: str, parent_path: str = ""):
        """Find a node by name and parent path in the current scene data"""
        if not self.current_scene_data or not node_name:
            return None

        def search_nodes(nodes, current_path=""):
            for node in nodes:
                node_path = f"{current_path}/{node.get('name')}" if current_path else node.get('name')

                if node.get("name") == node_name:
                    # If parent_path is specified, check if it matches
                    if parent_path:
                        expected_path = f"{parent_path}/{node_name}"
                        if node_path == expected_path:
                            return node
                    else:
                        return node

                # Search children
                children = node.get("children", [])
                if children:
                    result = search_nodes(children, node_path)
                    if result:
                        return result
            return None

        return search_nodes(self.current_scene_data.get("nodes", []))

    def get_node_path(self, item: QTreeWidgetItem) -> str:
        """Get the full path of a node from root"""
        path_parts = []
        current_item = item

        while current_item:
            node_data = current_item.data(0, Qt.ItemDataRole.UserRole)
            if node_data:
                node_name = node_data.get("name", "")
                if node_name:
                    path_parts.insert(0, node_name)
            current_item = current_item.parent()

        return "/".join(path_parts)

    def sync_tree_to_scene_data(self):
        """Synchronize tree widget state back to scene data"""
        if not self.current_scene_data:
            return

        # Rebuild scene data from tree structure
        def build_node_data(item: QTreeWidgetItem) -> dict:
            node_data = item.data(0, Qt.ItemDataRole.UserRole)
            if not node_data:
                return {}

            # Create a copy of the node data
            result = dict(node_data)

            # Rebuild children from tree structure
            children = []
            for i in range(item.childCount()):
                child_item = item.child(i)
                child_data = build_node_data(child_item)
                if child_data:
                    children.append(child_data)

            result["children"] = children
            return result

        # Rebuild root nodes
        new_nodes = []
        for i in range(self.tree.topLevelItemCount()):
            root_item = self.tree.topLevelItem(i)
            node_data = build_node_data(root_item)
            if node_data:
                new_nodes.append(node_data)

        self.current_scene_data["nodes"] = new_nodes

    def update_tree_item_property(self, node_id: str, property_name: str, value):
        """Update a property in the tree item data to match inspector changes"""
        # Find the tree item for this node
        item = self.find_tree_item_by_name(self.tree.invisibleRootItem(), node_id)
        if item:
            # Get the node data from the tree item
            node_data = item.data(0, Qt.ItemDataRole.UserRole)
            if node_data:
                # Update the property in the tree item data
                node_data[property_name] = value
                # Store the updated data back to the tree item
                item.setData(0, Qt.ItemDataRole.UserRole, node_data)

                # Also update the scene data to keep it synchronized
                self.sync_tree_to_scene_data()

    def on_rows_moved(self, parent, start, end, destination, row):
        """Handle drag and drop operations"""
        # Synchronize tree structure back to scene data after drag/drop
        self.sync_tree_to_scene_data()

        # Emit change signal to notify other components
        self.node_changed.emit({})

    # ========== ENHANCED SCENE INSTANCE METHODS ==========

    def create_instance_variant(self, item: QTreeWidgetItem):
        """Create a variant of a scene instance"""
        if not item:
            return

        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data or node_data.get("type") != "SceneInstance":
            return

        try:
            # Create scene instance from data
            from nodes.base.SceneInstance import SceneInstance
            scene_instance = SceneInstance.from_dict(node_data)

            # Create variant
            variant_name = f"{scene_instance.name}_variant"
            variant = scene_instance.create_variant(variant_name)

            if variant:
                # Add variant to the scene tree
                variant_data = variant.to_dict()
                parent_item = item.parent()
                self.add_node_to_tree(variant_data, parent_item)
                self.sync_tree_to_scene_data()

                QMessageBox.information(self, "Variant Created",
                                      f"Created variant: {variant.name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to create variant")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to create variant: {e}")

    def show_property_overrides(self, item: QTreeWidgetItem):
        """Show property overrides for a scene instance"""
        if not item:
            return

        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data or node_data.get("type") != "SceneInstance":
            return

        try:
            # Get property overrides
            overrides = node_data.get("property_overrides", {})

            if not overrides:
                QMessageBox.information(self, "Property Overrides",
                                      "This scene instance has no property overrides.")
                return

            # Format overrides for display
            override_text = "Property Overrides:\n\n"
            for node_path, properties in overrides.items():
                override_text += f"Node: {node_path}\n"
                for prop_name, value in properties.items():
                    override_text += f"  {prop_name}: {value}\n"
                override_text += "\n"

            # Show in message box (could be enhanced with a custom dialog)
            QMessageBox.information(self, "Property Overrides", override_text)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to show overrides: {e}")

    def show_performance_info(self, item: QTreeWidgetItem):
        """Show performance information for a scene instance"""
        if not item:
            return

        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data or node_data.get("type") != "SceneInstance":
            return

        try:
            # Create scene instance to get performance info
            from nodes.base.SceneInstance import SceneInstance
            scene_instance = SceneInstance.from_dict(node_data)

            # Get memory usage statistics
            memory_stats = scene_instance.get_memory_usage()

            # Format performance info
            perf_text = "Performance Information:\n\n"
            perf_text += f"Instance Size: {memory_stats.get('instance_size', 0)} bytes\n"
            perf_text += f"Children Count: {memory_stats.get('children_count', 0)}\n"
            perf_text += f"Override Count: {memory_stats.get('override_count', 0)}\n"
            perf_text += f"Total Nodes: {memory_stats.get('total_nodes', 0)}\n"
            perf_text += f"Scene Path: {memory_stats.get('scene_path', 'N/A')}\n"
            perf_text += f"Is Pooled: {memory_stats.get('is_pooled', False)}\n"
            perf_text += f"Is Active: {memory_stats.get('is_active', True)}\n"

            QMessageBox.information(self, "Performance Info", perf_text)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to get performance info: {e}")

    def validate_scene_instance(self, item: QTreeWidgetItem):
        """Validate a scene instance for integrity issues"""
        if not item:
            return

        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data or node_data.get("type") != "SceneInstance":
            return

        try:
            # Create scene instance to validate
            from nodes.base.SceneInstance import SceneInstance
            scene_instance = SceneInstance.from_dict(node_data)

            # Validate integrity
            issues = scene_instance.validate_integrity()

            if not issues:
                QMessageBox.information(self, "Validation Result",
                                      "Scene instance validation passed. No issues found.")
            else:
                issue_text = "Validation Issues Found:\n\n"
                for i, issue in enumerate(issues, 1):
                    issue_text += f"{i}. {issue}\n"

                QMessageBox.warning(self, "Validation Issues", issue_text)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to validate instance: {e}")

    def edit_original_scene(self, item: QTreeWidgetItem):
        """Edit the original scene file of a scene instance"""
        if not item:
            return

        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data or node_data.get("type") != "SceneInstance":
            return

        scene_path = node_data.get("scene_path", "")
        if not scene_path:
            QMessageBox.warning(self, "Error", "No scene file specified for this instance.")
            return

        # TODO: Implement opening scene in new tab or window
        # For now, just show a message
        QMessageBox.information(self, "Edit Scene", f"Would open scene: {scene_path}")

    def reload_scene_instance(self, item: QTreeWidgetItem):
        """Reload a scene instance from its original scene file"""
        if not item:
            return

        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data or node_data.get("type") != "SceneInstance":
            return

        try:
            # Get the scene instance node
            from nodes.base.SceneInstance import SceneInstance

            # Create a new instance and reload it
            scene_instance = SceneInstance.from_dict(node_data)
            if scene_instance.reload_scene():
                # Update the node data with the reloaded content
                updated_data = scene_instance.to_dict()
                item.setData(0, Qt.ItemDataRole.UserRole, updated_data)

                # Rebuild the tree item's children
                # Remove existing children
                while item.childCount() > 0:
                    item.removeChild(item.child(0))

                # Add new children from reloaded scene
                for child_data in updated_data.get("children", []):
                    self.add_node_to_tree(child_data, item)

                # Synchronize back to scene data
                self.sync_tree_to_scene_data()

                # Emit change signal
                self.node_changed.emit(updated_data)

                QMessageBox.information(self, "Success", "Scene instance reloaded successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to reload scene instance.")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to reload scene instance: {e}")

    def break_scene_instance(self, item: QTreeWidgetItem):
        """Break a scene instance, converting it to regular nodes"""
        if not item:
            return

        node_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_data or node_data.get("type") != "SceneInstance":
            return

        # Confirm the action
        reply = QMessageBox.question(
            self, "Break Scene Instance",
            "Are you sure you want to break this scene instance? "
            "This will convert it to regular nodes and remove the link to the original scene.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Get the scene instance node
            from nodes.base.SceneInstance import SceneInstance

            # Create a scene instance and break it
            scene_instance = SceneInstance.from_dict(node_data)
            children = scene_instance.break_instance()

            # Update the node data to be a regular Node
            node_data["type"] = "Node"
            node_data.pop("scene_path", None)
            node_data.pop("instance_id", None)
            node_data.pop("property_overrides", None)
            node_data.pop("editable_children", None)

            # Update the tree item
            node_name = node_data.get("name", "Node")
            item.setText(0, f"{node_name} (Node)")
            item.setData(0, Qt.ItemDataRole.UserRole, node_data)

            # Synchronize back to scene data
            self.sync_tree_to_scene_data()

            # Emit change signal
            self.node_changed.emit(node_data)

            QMessageBox.information(self, "Success", "Scene instance broken successfully.")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to break scene instance: {e}")


