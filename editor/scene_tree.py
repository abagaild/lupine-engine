"""
Scene Tree Widget for Lupine Engine
Displays the hierarchical structure of nodes in the current scene
"""

import json
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QMenu, QMessageBox, QPushButton, QHBoxLayout
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
        self.tree.setHeaderLabel("Scene")
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree.itemChanged.connect(self.on_item_changed)
        
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
        item.setText(0, f"{node_name} ({node_type})")
        
        # Store node data
        item.setData(0, Qt.ItemDataRole.UserRole, node_data)
        
        # Make item editable
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Add children
        children = node_data.get("children", [])
        for child_data in children:
            self.add_node_to_tree(child_data, item)
        
        return item
    
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


