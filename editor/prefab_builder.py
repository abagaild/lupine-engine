"""
Prefab Builder for Lupine Engine
Comprehensive tool for creating and editing prefabs with visual scripting
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QCheckBox, QGroupBox, QFormLayout, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QMessageBox, QFileDialog, QScrollArea,
    QListWidget, QListWidgetItem, QDialog, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from core.project import LupineProject
from core.prefabs.prefab_manager import PrefabManager
from core.prefabs.prefab_system import EnhancedPrefab, PrefabType, PrefabProperty, EventDefinition, VisualScriptInput
from .ui.visual_script_editor import VisualScriptEditor
from .scene_view import SceneViewWidget


class PrefabPropertyEditor(QWidget):
    """Editor for prefab properties"""
    
    property_changed = pyqtSignal(str, object)  # property_name, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.properties: List[PrefabProperty] = []
        self.property_widgets: Dict[str, QWidget] = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the property editor UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Properties")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        add_btn = QPushButton("Add Property")
        add_btn.clicked.connect(self.add_property)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Properties list
        self.properties_scroll = QScrollArea()
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_widget)
        self.properties_scroll.setWidget(self.properties_widget)
        self.properties_scroll.setWidgetResizable(True)
        layout.addWidget(self.properties_scroll)
    
    def add_property(self):
        """Add a new property"""
        dialog = PropertyDefinitionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            prop_data = dialog.get_property_data()
            prop = PrefabProperty(**prop_data)
            self.properties.append(prop)
            self.create_property_widget(prop)
    
    def create_property_widget(self, prop: PrefabProperty):
        """Create a widget for a property"""
        group = QGroupBox(f"{prop.name} ({prop.type})")
        layout = QFormLayout(group)
        
        # Property info
        layout.addRow("Description:", QLabel(prop.description))
        layout.addRow("Group:", QLabel(prop.group))
        layout.addRow("Export:", QLabel("Yes" if prop.export else "No"))
        
        # Default value editor
        if prop.type == "string":
            value_widget = QLineEdit(str(prop.default_value or ""))
        elif prop.type == "number":
            value_widget = QSpinBox()
            value_widget.setRange(-999999, 999999)
            value_widget.setValue(int(prop.default_value or 0))
        elif prop.type == "boolean":
            value_widget = QCheckBox()
            value_widget.setChecked(bool(prop.default_value))
        else:
            value_widget = QLineEdit(str(prop.default_value or ""))
        
        layout.addRow("Default Value:", value_widget)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_property(prop, group))
        layout.addRow("", remove_btn)
        
        self.properties_layout.addWidget(group)
        self.property_widgets[prop.name] = value_widget
    
    def remove_property(self, prop: PrefabProperty, widget: QWidget):
        """Remove a property"""
        if prop in self.properties:
            self.properties.remove(prop)
        
        if prop.name in self.property_widgets:
            del self.property_widgets[prop.name]
        
        widget.deleteLater()
    
    def load_properties(self, properties: List[PrefabProperty]):
        """Load properties into the editor"""
        # Clear existing
        self.properties.clear()
        self.property_widgets.clear()
        
        for i in reversed(range(self.properties_layout.count())):
            child = self.properties_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        # Load new properties
        self.properties = properties[:]
        for prop in self.properties:
            self.create_property_widget(prop)
    
    def get_properties(self) -> List[PrefabProperty]:
        """Get the current properties"""
        return self.properties[:]


class PropertyDefinitionDialog(QDialog):
    """Dialog for defining a new property"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Property")
        self.setModal(True)
        self.resize(400, 300)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "string", "number", "boolean", "color", "path", 
            "nodepath", "vector2", "vector3"
        ])
        form_layout.addRow("Type:", self.type_combo)
        
        self.default_input = QLineEdit()
        form_layout.addRow("Default Value:", self.default_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        form_layout.addRow("Description:", self.description_input)
        
        self.group_input = QLineEdit()
        form_layout.addRow("Group:", self.group_input)
        
        self.export_check = QCheckBox()
        self.export_check.setChecked(True)
        form_layout.addRow("Export:", self.export_check)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_property_data(self) -> Dict[str, Any]:
        """Get the property data"""
        return {
            "name": self.name_input.text(),
            "type": self.type_combo.currentText(),
            "default_value": self.default_input.text(),
            "description": self.description_input.toPlainText(),
            "group": self.group_input.text(),
            "export": self.export_check.isChecked()
        }


class PrefabBuilderWindow(QMainWindow):
    """Main Prefab Builder window"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.prefab_manager = PrefabManager(str(project.project_path))
        self.current_prefab: Optional[EnhancedPrefab] = None
        
        self.setWindowTitle("Prefab Builder - Lupine Engine")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        self.setup_ui()
        self.setup_menus()
        self.load_prefab_list()
    
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Prefab list
        left_panel = self.create_prefab_list_panel()
        splitter.addWidget(left_panel)
        
        # Center - Main editor
        center_panel = self.create_main_editor_panel()
        splitter.addWidget(center_panel)
        
        # Right panel - Properties
        right_panel = self.create_properties_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([250, 700, 350])
    
    def create_prefab_list_panel(self) -> QWidget:
        """Create the prefab list panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Prefabs")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_prefab)
        header_layout.addWidget(new_btn)
        
        layout.addLayout(header_layout)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search prefabs...")
        self.search_input.textChanged.connect(self.filter_prefabs)
        layout.addWidget(self.search_input)
        
        # Prefab list
        self.prefab_list = QListWidget()
        self.prefab_list.itemClicked.connect(self.on_prefab_selected)
        layout.addWidget(self.prefab_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.clicked.connect(self.duplicate_prefab)
        buttons_layout.addWidget(duplicate_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_prefab)
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
        
        return panel
    
    def create_main_editor_panel(self) -> QWidget:
        """Create the main editor panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget for different editor views
        self.editor_tabs = QTabWidget()
        layout.addWidget(self.editor_tabs)
        
        # Basic Info tab
        self.basic_info_tab = self.create_basic_info_tab()
        self.editor_tabs.addTab(self.basic_info_tab, "Basic Info")
        
        # Node Structure tab
        self.node_structure_tab = self.create_node_structure_tab()
        self.editor_tabs.addTab(self.node_structure_tab, "Node Structure")
        
        # Visual Script tab
        self.visual_script_tab = VisualScriptEditor(self.prefab_manager)
        self.visual_script_tab.script_changed.connect(self.on_script_changed)
        self.editor_tabs.addTab(self.visual_script_tab, "Visual Script")
        
        # Raw Script tab
        self.raw_script_tab = self.create_raw_script_tab()
        self.editor_tabs.addTab(self.raw_script_tab, "Raw Script")
        
        return panel
    
    def create_basic_info_tab(self) -> QWidget:
        """Create the basic info tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self.on_basic_info_changed)
        layout.addRow("Name:", self.name_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in PrefabType])
        self.type_combo.currentTextChanged.connect(self.on_basic_info_changed)
        layout.addRow("Type:", self.type_combo)
        
        self.category_input = QLineEdit()
        self.category_input.textChanged.connect(self.on_basic_info_changed)
        layout.addRow("Category:", self.category_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.textChanged.connect(self.on_basic_info_changed)
        layout.addRow("Description:", self.description_input)
        
        self.base_node_input = QComboBox()
        self.base_node_input.addItems([
            "Node", "Node2D", "KinematicBody2D", "StaticBody2D", 
            "RigidBody2D", "Area2D", "Control", "Panel", "Button"
        ])
        self.base_node_input.currentTextChanged.connect(self.on_basic_info_changed)
        layout.addRow("Base Node:", self.base_node_input)
        
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Comma-separated tags")
        self.tags_input.textChanged.connect(self.on_basic_info_changed)
        layout.addRow("Tags:", self.tags_input)
        
        return widget
    
    def create_node_structure_tab(self) -> QWidget:
        """Create the node structure tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Node tree
        self.node_tree = QTreeWidget()
        self.node_tree.setHeaderLabels(["Node", "Type"])
        layout.addWidget(self.node_tree)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        add_child_btn = QPushButton("Add Child")
        add_child_btn.clicked.connect(self.add_child_node)
        buttons_layout.addWidget(add_child_btn)
        
        remove_node_btn = QPushButton("Remove Node")
        remove_node_btn.clicked.connect(self.remove_node)
        buttons_layout.addWidget(remove_node_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        return widget
    
    def create_raw_script_tab(self) -> QWidget:
        """Create the raw script tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Script editor
        self.script_editor = QTextEdit()
        self.script_editor.setFont(QFont("Consolas", 10))
        self.script_editor.textChanged.connect(self.on_script_changed)
        layout.addWidget(self.script_editor)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Generate from Visual")
        generate_btn.clicked.connect(self.generate_script_from_visual)
        buttons_layout.addWidget(generate_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        return widget
    
    def create_properties_panel(self) -> QWidget:
        """Create the properties panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Properties editor
        self.property_editor = PrefabPropertyEditor()
        layout.addWidget(self.property_editor)

        return panel

    def setup_menus(self):
        """Setup the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Prefab", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_prefab)
        file_menu.addAction(new_action)

        save_action = QAction("Save Prefab", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_prefab)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        import_action = QAction("Import Prefab", self)
        import_action.triggered.connect(self.import_prefab)
        file_menu.addAction(import_action)

        export_action = QAction("Export Prefab", self)
        export_action.triggered.connect(self.export_prefab)
        file_menu.addAction(export_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        duplicate_action = QAction("Duplicate Prefab", self)
        duplicate_action.setShortcut("Ctrl+D")
        duplicate_action.triggered.connect(self.duplicate_prefab)
        edit_menu.addAction(duplicate_action)

        delete_action = QAction("Delete Prefab", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_prefab)
        edit_menu.addAction(delete_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        # Visual Script Editor
        visual_script_action = QAction("Visual Script Editor", self)
        visual_script_action.triggered.connect(self.open_visual_script_editor)
        tools_menu.addAction(visual_script_action)

    def load_prefab_list(self):
        """Load the list of prefabs"""
        self.prefab_list.clear()

        for prefab in self.prefab_manager.prefabs.values():
            item = QListWidgetItem(f"{prefab.name} ({prefab.category})")
            item.setData(Qt.ItemDataRole.UserRole, prefab.id)
            item.setToolTip(prefab.description)
            self.prefab_list.addItem(item)

    def filter_prefabs(self, text: str):
        """Filter prefabs based on search text"""
        for i in range(self.prefab_list.count()):
            item = self.prefab_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def new_prefab(self):
        """Create a new prefab"""
        name, ok = QInputDialog.getText(self, "New Prefab", "Prefab name:")
        if ok and name:
            if name in self.prefab_manager.prefabs_by_name:
                QMessageBox.warning(self, "Error", "A prefab with this name already exists!")
                return

            prefab = EnhancedPrefab(name, PrefabType.NODE)
            prefab.category = "Custom"
            prefab.description = "New prefab"

            self.prefab_manager.add_prefab(prefab)
            self.prefab_manager.save_prefab(prefab)

            self.load_prefab_list()
            self.load_prefab(prefab)

    def duplicate_prefab(self):
        """Duplicate the selected prefab"""
        if not self.current_prefab:
            QMessageBox.information(self, "No Selection", "Please select a prefab to duplicate.")
            return

        name, ok = QInputDialog.getText(self, "Duplicate Prefab", "New prefab name:")
        if ok and name:
            new_prefab = self.prefab_manager.duplicate_prefab(self.current_prefab.id, name)
            if new_prefab:
                self.load_prefab_list()
                self.load_prefab(new_prefab)
            else:
                QMessageBox.warning(self, "Error", "Failed to duplicate prefab!")

    def delete_prefab(self):
        """Delete the selected prefab"""
        if not self.current_prefab:
            QMessageBox.information(self, "No Selection", "Please select a prefab to delete.")
            return

        reply = QMessageBox.question(
            self, "Delete Prefab",
            f"Are you sure you want to delete '{self.current_prefab.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.prefab_manager.remove_prefab(self.current_prefab.id)
            self.load_prefab_list()
            self.current_prefab = None
            self.clear_editor()

    def save_prefab(self):
        """Save the current prefab"""
        if not self.current_prefab:
            return

        # Update prefab from UI
        self.update_prefab_from_ui()

        # Save to file
        self.prefab_manager.save_prefab(self.current_prefab)

        QMessageBox.information(self, "Saved", f"Prefab '{self.current_prefab.name}' saved successfully!")

    def import_prefab(self):
        """Import a prefab from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Prefab", "", "Prefab Files (*.prefab);;All Files (*)"
        )

        if file_path:
            prefab = self.prefab_manager.import_prefab(file_path)
            if prefab:
                self.load_prefab_list()
                self.load_prefab(prefab)
                QMessageBox.information(self, "Imported", f"Prefab '{prefab.name}' imported successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to import prefab!")

    def export_prefab(self):
        """Export the current prefab"""
        if not self.current_prefab:
            QMessageBox.information(self, "No Selection", "Please select a prefab to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Prefab", f"{self.current_prefab.name}.prefab",
            "Prefab Files (*.prefab);;All Files (*)"
        )

        if file_path:
            if self.prefab_manager.export_prefab(self.current_prefab.id, file_path):
                QMessageBox.information(self, "Exported", f"Prefab exported to '{file_path}'!")
            else:
                QMessageBox.warning(self, "Error", "Failed to export prefab!")

    def on_prefab_selected(self, item: QListWidgetItem):
        """Handle prefab selection"""
        prefab_id = item.data(Qt.ItemDataRole.UserRole)
        prefab = self.prefab_manager.get_prefab_by_id(prefab_id)
        if prefab:
            self.load_prefab(prefab)

    def load_prefab(self, prefab: EnhancedPrefab):
        """Load a prefab into the editor"""
        self.current_prefab = prefab

        # Load basic info
        self.name_input.setText(prefab.name)
        self.type_combo.setCurrentText(prefab.prefab_type.value)
        self.category_input.setText(prefab.category)
        self.description_input.setPlainText(prefab.description)
        self.base_node_input.setCurrentText(prefab.base_node_type)
        self.tags_input.setText(", ".join(prefab.tags))

        # Load properties
        self.property_editor.load_properties(prefab.properties)

        # Load node structure
        self.load_node_structure(prefab.node_structure)

        # Load script
        self.script_editor.setPlainText(prefab.default_script)

        # Load visual script (if any)
        # This would load visual script data if it exists

    def load_node_structure(self, node_data: Dict[str, Any]):
        """Load node structure into the tree"""
        self.node_tree.clear()

        if node_data:
            root_item = QTreeWidgetItem([node_data.get("name", "Root"), node_data.get("type", "Node")])
            self.node_tree.addTopLevelItem(root_item)

            # Load children recursively
            self.load_node_children(root_item, node_data.get("children", []))

            self.node_tree.expandAll()

    def load_node_children(self, parent_item: QTreeWidgetItem, children: List[Dict[str, Any]]):
        """Load child nodes recursively"""
        for child_data in children:
            child_item = QTreeWidgetItem([child_data.get("name", "Node"), child_data.get("type", "Node")])
            parent_item.addChild(child_item)

            # Load grandchildren
            self.load_node_children(child_item, child_data.get("children", []))

    def clear_editor(self):
        """Clear the editor"""
        self.name_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.category_input.clear()
        self.description_input.clear()
        self.base_node_input.setCurrentIndex(0)
        self.tags_input.clear()
        self.property_editor.load_properties([])
        self.node_tree.clear()
        self.script_editor.clear()

    def update_prefab_from_ui(self):
        """Update the current prefab from UI values"""
        if not self.current_prefab:
            return

        self.current_prefab.name = self.name_input.text()
        self.current_prefab.prefab_type = PrefabType(self.type_combo.currentText())
        self.current_prefab.category = self.category_input.text()
        self.current_prefab.description = self.description_input.toPlainText()
        self.current_prefab.base_node_type = self.base_node_input.currentText()
        self.current_prefab.tags = [tag.strip() for tag in self.tags_input.text().split(",") if tag.strip()]
        self.current_prefab.properties = self.property_editor.get_properties()
        self.current_prefab.default_script = self.script_editor.toPlainText()

        # Update node structure from tree
        self.current_prefab.node_structure = self.get_node_structure_from_tree()

    def get_node_structure_from_tree(self) -> Dict[str, Any]:
        """Get node structure from the tree widget"""
        if self.node_tree.topLevelItemCount() == 0:
            return {}

        root_item = self.node_tree.topLevelItem(0)
        return self.get_node_data_from_item(root_item)

    def get_node_data_from_item(self, item: QTreeWidgetItem) -> Dict[str, Any]:
        """Get node data from a tree item"""
        node_data = {
            "name": item.text(0),
            "type": item.text(1),
            "position": [0, 0],
            "children": []
        }

        # Get children
        for i in range(item.childCount()):
            child_item = item.child(i)
            child_data = self.get_node_data_from_item(child_item)
            node_data["children"].append(child_data)

        return node_data

    def add_child_node(self):
        """Add a child node to the selected node"""
        current_item = self.node_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a parent node.")
            return

        name, ok = QMessageBox.getText(self, "Add Child Node", "Node name:")
        if ok and name:
            child_item = QTreeWidgetItem([name, "Node2D"])
            current_item.addChild(child_item)
            self.node_tree.expandItem(current_item)

    def remove_node(self):
        """Remove the selected node"""
        current_item = self.node_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a node to remove.")
            return

        parent = current_item.parent()
        if parent:
            parent.removeChild(current_item)
        else:
            # Removing root item
            index = self.node_tree.indexOfTopLevelItem(current_item)
            self.node_tree.takeTopLevelItem(index)

    def on_basic_info_changed(self):
        """Handle basic info changes"""
        # Auto-save or mark as modified
        pass

    def on_script_changed(self):
        """Handle script changes"""
        # Auto-save or mark as modified
        pass

    def generate_script_from_visual(self):
        """Generate script code from visual script"""
        code = self.visual_script_tab.generate_python_code()
        self.script_editor.setPlainText(code)

    def open_visual_script_editor(self):
        """Open the visual script editor popup"""
        from editor.ui.visual_script_popup import open_visual_script_popup

        # Determine target object
        target_object = None
        initial_script_path = None

        if self.current_prefab:
            target_object = self.current_prefab
            initial_script_path = getattr(self.current_prefab, 'visual_script_path', None)

        # Open the popup
        script_path = open_visual_script_popup(
            parent=self,
            project=self.project,
            target_object=target_object,
            initial_script_path=initial_script_path or ""
        )

        # If a script was selected and we have a target object, apply it
        if script_path and target_object:
            if hasattr(target_object, 'visual_script_path'):
                target_object.visual_script_path = script_path

            # Refresh the properties panel
            if target_object == self.current_prefab and self.current_prefab:
                self.load_prefab(self.current_prefab)
