"""
Prefab Library Widget for Lupine Engine Menu and HUD Builder
Provides a categorized library of UI prefabs for drag-and-drop
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QPushButton, QLabel, QFrame, QScrollArea, QGridLayout,
    QGroupBox, QSplitter, QTextEdit, QComboBox, QApplication, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPainter, QPixmap, QFont
from typing import Dict, Any, Optional

from core.ui.ui_prefabs import BUILTIN_PREFABS, PrefabCategory, UIPrefab, get_prefabs_by_category
from core.node_registry import get_node_registry, NodeCategory


class PrefabItem(QWidget):
    """Widget representing a single prefab in the library"""
    
    prefab_selected = pyqtSignal(str)  # prefab_name
    prefab_dragged = pyqtSignal(str, QPoint)  # prefab_name, position
    
    def __init__(self, prefab: UIPrefab):
        super().__init__()
        self.prefab = prefab
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the prefab item UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Prefab name
        name_label = QLabel(self.prefab.name)
        name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Category indicator
        category_label = QLabel(f"[{self.prefab.category.value}]")
        category_label.setFont(QFont("Arial", 8))
        category_label.setStyleSheet("color: #888; font-style: italic;")
        category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(category_label)
        
        # Description
        desc_label = QLabel(self.prefab.description)
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Arial", 8))
        desc_label.setStyleSheet("color: #aaa;")
        desc_label.setMaximumHeight(30)
        layout.addWidget(desc_label)
        
        # Make the widget look clickable
        self.setStyleSheet("""
            PrefabItem {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                margin: 2px;
            }
            PrefabItem:hover {
                background-color: #3a3a3a;
                border: 1px solid #666;
            }
        """)
        
        self.setMinimumWidth(120)
        self.setMaximumWidth(140)
        self.setMinimumHeight(110)
        self.setMaximumHeight(110)
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection and drag start"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.prefab_selected.emit(self.prefab.name)
            self.drag_start_position = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for drag operation"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if not hasattr(self, 'drag_start_position'):
            return
        
        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"prefab:{self.prefab.name}")
        drag.setMimeData(mime_data)
        
        # Create drag pixmap
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.render(painter)
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)
        
        # Execute drag
        drop_action = drag.exec(Qt.DropAction.CopyAction)


class NodeItem(QWidget):
    """Widget representing a generic UI node in the library"""

    node_selected = pyqtSignal(str)  # node_type
    node_dragged = pyqtSignal(str, QPoint)  # node_type, position

    def __init__(self, node_type: str, description: str = ""):
        super().__init__()
        self.node_type = node_type
        self.description = description or f"Generic {node_type} node"
        self.setup_ui()

    def setup_ui(self):
        """Setup the node item UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Node name
        name_label = QLabel(self.node_type)
        name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # Type indicator
        type_label = QLabel(f"[UI Node]")
        type_label.setFont(QFont("Arial", 8))
        type_label.setStyleSheet("color: #888; font-style: italic;")
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(type_label)

        # Description
        desc_label = QLabel(self.description)
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Arial", 8))
        desc_label.setStyleSheet("color: #aaa;")
        desc_label.setMaximumHeight(30)
        layout.addWidget(desc_label)

        # Make the widget look clickable
        self.setStyleSheet("""
            NodeItem {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                margin: 2px;
            }
            NodeItem:hover {
                background-color: #3a3a3a;
                border: 1px solid #666;
            }
        """)

        self.setMinimumWidth(120)
        self.setMaximumWidth(140)
        self.setMinimumHeight(110)
        self.setMaximumHeight(110)

    def mousePressEvent(self, event):
        """Handle mouse press for selection and drag start"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.node_selected.emit(self.node_type)
            self.drag_start_position = event.position().toPoint()

    def mouseMoveEvent(self, event):
        """Handle mouse move for drag operation"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if not hasattr(self, 'drag_start_position'):
            return

        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() <
            QApplication.startDragDistance()):
            return

        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"node:{self.node_type}")
        drag.setMimeData(mime_data)

        # Create drag pixmap
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.render(painter)
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)

        # Execute drag
        drop_action = drag.exec(Qt.DropAction.CopyAction)


class PrefabLibrary(QWidget):
    """Main prefab library widget with categories and search"""

    prefab_selected = pyqtSignal(str)  # prefab_name
    prefab_dragged = pyqtSignal(str, QPoint)  # prefab_name, position
    node_selected = pyqtSignal(str)  # node_type for generic nodes

    def __init__(self):
        super().__init__()
        self.current_category = None
        self.prefab_items = {}  # prefab_name -> PrefabItem
        self.node_items = {}  # node_type -> NodeItem
        self.setup_ui()
        self.populate_categories()
        
    def setup_ui(self):
        """Setup the library UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Title
        title_label = QLabel("UI Library")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Tabs for prefabs and generic nodes
        self.tab_widget = QTabWidget()

        # Prefabs tab
        prefabs_tab = QWidget()
        self.setup_prefabs_tab(prefabs_tab)
        self.tab_widget.addTab(prefabs_tab, "Prefabs")

        # Generic nodes tab
        nodes_tab = QWidget()
        self.setup_nodes_tab(nodes_tab)
        self.tab_widget.addTab(nodes_tab, "UI Nodes")

        layout.addWidget(self.tab_widget)

        # Selected item info
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(80)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)

        layout.addWidget(info_group)

    def setup_prefabs_tab(self, tab_widget):
        """Setup the prefabs tab"""
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search prefabs...")
        self.search_edit.textChanged.connect(self.filter_prefabs)
        search_layout.addWidget(self.search_edit)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_search)
        clear_button.setMaximumWidth(50)
        search_layout.addWidget(clear_button)

        layout.addLayout(search_layout)

        # Category selector
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))

        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        category_layout.addWidget(self.category_combo)

        layout.addLayout(category_layout)

        # Prefab grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.prefab_container = QWidget()
        self.prefab_layout = QGridLayout(self.prefab_container)
        self.prefab_layout.setSpacing(4)

        self.scroll_area.setWidget(self.prefab_container)
        layout.addWidget(self.scroll_area)

    def setup_nodes_tab(self, tab_widget):
        """Setup the generic nodes tab"""
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Search bar for nodes
        search_layout = QHBoxLayout()
        self.node_search_edit = QLineEdit()
        self.node_search_edit.setPlaceholderText("Search UI nodes...")
        self.node_search_edit.textChanged.connect(self.filter_nodes)
        search_layout.addWidget(self.node_search_edit)

        clear_node_button = QPushButton("Clear")
        clear_node_button.clicked.connect(self.clear_node_search)
        clear_node_button.setMaximumWidth(50)
        search_layout.addWidget(clear_node_button)

        layout.addLayout(search_layout)

        # Nodes grid
        self.node_scroll_area = QScrollArea()
        self.node_scroll_area.setWidgetResizable(True)
        self.node_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.node_container = QWidget()
        self.node_layout = QGridLayout(self.node_container)
        self.node_layout.setSpacing(4)

        self.node_scroll_area.setWidget(self.node_container)
        layout.addWidget(self.node_scroll_area)

        # Populate with UI nodes
        self.populate_ui_nodes()

    def populate_ui_nodes(self):
        """Populate the nodes tab with generic UI nodes"""
        try:
            registry = get_node_registry()
            ui_nodes = registry.get_nodes_by_category(NodeCategory.UI)

            row, col = 0, 0
            max_cols = 2

            for node_def in ui_nodes:
                node_type = node_def.name
                description = node_def.description or f"Generic {node_type} UI node"

                item = NodeItem(node_type, description)
                item.node_selected.connect(self.on_node_selected)
                item.node_dragged.connect(self.node_selected)  # Emit as node selection

                self.node_items[node_type] = item
                self.node_layout.addWidget(item, row, col)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

        except Exception as e:
            print(f"Error populating UI nodes: {e}")

    def filter_nodes(self, search_text: str):
        """Filter nodes based on search text"""
        search_text = search_text.lower()

        for node_type, item in self.node_items.items():
            visible = (search_text in node_type.lower() or
                      search_text in item.description.lower())
            item.setVisible(visible)

    def clear_node_search(self):
        """Clear the node search field"""
        self.node_search_edit.clear()

    def on_node_selected(self, node_type: str):
        """Handle generic node selection"""
        info_text = f"<b>{node_type}</b><br>"
        info_text += f"<i>Category: UI Node</i><br>"
        info_text += f"Generic UI node that can be customized<br><br>"
        info_text += f"Drag to add to your layout"

        self.info_text.setHtml(info_text)
        self.node_selected.emit(node_type)
    
    def populate_categories(self):
        """Populate the category combo box"""
        self.category_combo.addItem("All Categories")
        for category in PrefabCategory:
            self.category_combo.addItem(category.value)
        
        # Start with all categories
        self.show_all_prefabs()
    
    def on_category_changed(self, category_text: str):
        """Handle category selection change"""
        if category_text == "All Categories":
            self.show_all_prefabs()
        else:
            # Find the category enum
            for category in PrefabCategory:
                if category.value == category_text:
                    self.show_category(category)
                    break
    
    def show_all_prefabs(self):
        """Show all prefabs"""
        self.clear_prefab_grid()
        
        row, col = 0, 0
        max_cols = 2
        
        for prefab in BUILTIN_PREFABS.values():
            self.add_prefab_to_grid(prefab, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def show_category(self, category: PrefabCategory):
        """Show prefabs from a specific category"""
        self.current_category = category
        self.clear_prefab_grid()
        
        prefabs = get_prefabs_by_category(category)
        row, col = 0, 0
        max_cols = 2
        
        for prefab in prefabs:
            self.add_prefab_to_grid(prefab, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def add_prefab_to_grid(self, prefab: UIPrefab, row: int, col: int):
        """Add a prefab item to the grid"""
        item = PrefabItem(prefab)
        item.prefab_selected.connect(self.on_prefab_selected)
        item.prefab_dragged.connect(self.prefab_dragged)
        
        self.prefab_items[prefab.name] = item
        self.prefab_layout.addWidget(item, row, col)
    
    def clear_prefab_grid(self):
        """Clear all prefab items from the grid"""
        for item in self.prefab_items.values():
            item.setParent(None)
        self.prefab_items.clear()
    
    def filter_prefabs(self, search_text: str):
        """Filter prefabs based on search text"""
        search_text = search_text.lower()
        
        for prefab_name, item in self.prefab_items.items():
            prefab = BUILTIN_PREFABS[prefab_name]
            visible = (search_text in prefab.name.lower() or 
                      search_text in prefab.description.lower())
            item.setVisible(visible)
    
    def clear_search(self):
        """Clear the search field"""
        self.search_edit.clear()
    
    def on_prefab_selected(self, prefab_name: str):
        """Handle prefab selection"""
        prefab = BUILTIN_PREFABS.get(prefab_name)
        if prefab:
            info_text = f"<b>{prefab.name}</b><br>"
            info_text += f"<i>Category: {prefab.category.value}</i><br>"
            info_text += f"Base Type: {prefab.base_node_type}<br><br>"
            info_text += prefab.description
            
            if prefab.variable_bindings:
                info_text += f"<br><br><b>Variable Bindings:</b> {', '.join(prefab.variable_bindings)}"
            
            if prefab.event_bindings:
                info_text += f"<br><b>Event Bindings:</b> {', '.join(prefab.event_bindings)}"
            
            self.info_text.setHtml(info_text)
        
        self.prefab_selected.emit(prefab_name)
