"""
Add Node Dialog for Lupine Engine
Dynamic node creation dialog with categorized node types
"""

from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QTextEdit, QSplitter, QFrame,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from core.node_registry import get_node_registry, NodeCategory, NodeDefinition
from core.project import LupineProject


class AddNodeDialog(QDialog):
    """Dialog for adding new nodes to the scene"""
    
    node_selected = pyqtSignal(str, str)  # node_type, node_name
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.selected_node_type = None

        try:
            self.registry = get_node_registry()
            self.setup_ui()
            self.populate_nodes()
        except Exception as e:
            print(f"Error initializing AddNodeDialog: {e}")
            # Set up minimal UI in case of error
            self.setWindowTitle("Create Node - Error")
            layout = QVBoxLayout(self)
            error_label = QLabel(f"Error loading node registry: {e}")
            layout.addWidget(error_label)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Create Node")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.resize(800, 600)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Create Node")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #e0e0e0; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #e0e0e0;")
        search_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to filter nodes...")
        self.search_edit.textChanged.connect(self.filter_nodes)
        search_layout.addWidget(self.search_edit)
        
        main_layout.addLayout(search_layout)
        
        # Content splitter
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # Left side - Node tree
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        tree_label = QLabel("Available Nodes:")
        tree_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        left_layout.addWidget(tree_label)
        
        self.node_tree = QTreeWidget()
        self.node_tree.setHeaderHidden(True)
        self.node_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.node_tree.itemSelectionChanged.connect(self.on_node_selected)
        self.node_tree.itemDoubleClicked.connect(self.on_node_double_clicked)
        left_layout.addWidget(self.node_tree)
        
        content_splitter.addWidget(left_frame)
        
        # Right side - Node details
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        details_label = QLabel("Node Details:")
        details_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        right_layout.addWidget(details_label)
        
        # Node name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setStyleSheet("color: #e0e0e0;")
        name_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Node name...")
        name_layout.addWidget(self.name_edit)
        
        right_layout.addLayout(name_layout)
        
        # Node description
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(150)
        self.description_text.setPlaceholderText("Select a node to see its description...")
        right_layout.addWidget(self.description_text)
        
        # Node properties preview
        props_label = QLabel("Properties:")
        props_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        right_layout.addWidget(props_label)
        
        self.properties_text = QTextEdit()
        self.properties_text.setReadOnly(True)
        self.properties_text.setMaximumHeight(200)
        self.properties_text.setPlaceholderText("Node properties will be shown here...")
        right_layout.addWidget(self.properties_text)
        
        content_splitter.addWidget(right_frame)
        content_splitter.setSizes([400, 400])
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.create_btn = QPushButton("Create")
        self.create_btn.setDefault(True)
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self.create_node)
        button_layout.addWidget(self.create_btn)
        
        main_layout.addLayout(button_layout)
        
        # Focus on search
        self.search_edit.setFocus()
    
    def populate_nodes(self):
        """Populate the node tree with available nodes"""
        try:
            self.node_tree.clear()

            # Create category items
            category_items = {}
            for category in self.registry.get_all_categories():
                category_item = QTreeWidgetItem([category.value])
                category_item.setExpanded(True)

                # Style category items
                font = QFont()
                font.setBold(True)
                category_item.setFont(0, font)

                self.node_tree.addTopLevelItem(category_item)
                category_items[category] = category_item

            # Add nodes to categories
            for category in self.registry.get_all_categories():
                try:
                    nodes = self.registry.get_nodes_by_category(category)
                    category_item = category_items[category]

                    for node_def in sorted(nodes, key=lambda x: x.name):
                        node_item = QTreeWidgetItem([node_def.name])
                        node_item.setData(0, Qt.ItemDataRole.UserRole, node_def)

                        # Add icon if available
                        if node_def.icon_path:
                            # TODO: Load and set icon
                            pass

                        # Style based on node type
                        if not node_def.is_builtin:
                            node_item.setToolTip(0, f"Custom node: {node_def.description}")
                        else:
                            node_item.setToolTip(0, node_def.description)

                        category_item.addChild(node_item)

                except Exception as e:
                    print(f"Error adding nodes for category {category}: {e}")

        except Exception as e:
            print(f"Error populating nodes: {e}")
            # Add error item to tree
            error_item = QTreeWidgetItem(["Error loading nodes"])
            self.node_tree.addTopLevelItem(error_item)
    
    def load_dynamic_nodes(self):
        """Load prefabs and custom nodes"""
        try:
            # Load prefabs from project
            prefabs_dir = self.project.get_absolute_path("prefabs")
            if prefabs_dir.exists():
                self.registry.load_prefabs_from_directory(prefabs_dir)

            # Load custom nodes
            nodes_dir = self.project.get_absolute_path("nodes")
            if nodes_dir.exists():
                self.registry.scan_for_custom_nodes(nodes_dir)

        except Exception as e:
            print(f"Warning: Error loading dynamic nodes: {e}")
    
    def filter_nodes(self, text: str):
        """Filter nodes based on search text"""
        text = text.lower()
        
        for i in range(self.node_tree.topLevelItemCount()):
            category_item = self.node_tree.topLevelItem(i)
            category_visible = False
            
            for j in range(category_item.childCount()):
                node_item = category_item.child(j)
                node_name = node_item.text(0).lower()
                
                # Show item if it matches search or if search is empty
                visible = not text or text in node_name
                node_item.setHidden(not visible)
                
                if visible:
                    category_visible = True
            
            # Hide category if no children are visible
            category_item.setHidden(not category_visible)
    
    def on_node_selected(self):
        """Handle node selection"""
        selected_items = self.node_tree.selectedItems()
        if not selected_items:
            self.selected_node_type = None
            self.create_btn.setEnabled(False)
            self.description_text.clear()
            self.properties_text.clear()
            self.name_edit.clear()
            return
        
        item = selected_items[0]
        node_def = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not node_def:  # Category item selected
            self.selected_node_type = None
            self.create_btn.setEnabled(False)
            self.description_text.clear()
            self.properties_text.clear()
            self.name_edit.clear()
            return
        
        # Node item selected
        self.selected_node_type = node_def.name
        self.create_btn.setEnabled(True)
        
        # Set default name
        self.name_edit.setText(node_def.name)
        
        # Show description
        description = node_def.description
        if node_def.script_path:
            description += f"\n\nScript: {node_def.script_path}"
        if not node_def.is_builtin:
            description += "\n\n[Custom Node]"
        
        self.description_text.setPlainText(description)
        
        # Show properties preview
        self.show_node_properties(node_def)
    
    def show_node_properties(self, node_def: NodeDefinition):
        """Show preview of node properties"""
        properties_text = f"Type: {node_def.class_name}\n"
        properties_text += f"Category: {node_def.category.value}\n"
        
        if node_def.script_path:
            properties_text += f"\nScript Properties:\n"
            # TODO: Parse script and show export variables
            properties_text += "- Export variables will be shown in inspector\n"
            properties_text += "- Custom methods and signals available\n"
        
        # Add common properties based on category
        if node_def.category == NodeCategory.NODE_2D:
            properties_text += "\nTransform Properties:\n"
            properties_text += "- position: Vector2\n"
            properties_text += "- rotation: float\n"
            properties_text += "- scale: Vector2\n"
            properties_text += "- z_index: int\n"
        
        if node_def.category == NodeCategory.UI:
            properties_text += "\nUI Properties:\n"
            properties_text += "- rect: Rect2\n"
            properties_text += "- anchor: Vector2\n"
            properties_text += "- margin: Vector4\n"
        
        self.properties_text.setPlainText(properties_text)
    
    def on_node_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click to create node"""
        node_def = item.data(0, Qt.ItemDataRole.UserRole)
        if node_def:
            self.create_node()
    
    def create_node(self):
        """Create the selected node"""
        if not self.selected_node_type:
            return
        
        node_name = self.name_edit.text().strip()
        if not node_name:
            node_name = self.selected_node_type
        
        self.node_selected.emit(self.selected_node_type, node_name)
        self.accept()
    
    def get_selected_node_info(self) -> tuple:
        """Get selected node type and name"""
        node_name = self.name_edit.text().strip()
        if not node_name:
            node_name = self.selected_node_type
        
        return self.selected_node_type, node_name
