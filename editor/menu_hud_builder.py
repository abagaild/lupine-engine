"""
Menu and HUD Builder for Lupine Engine
Comprehensive tool for creating UI layouts with drag-and-drop prefabs,
variable bindings, and event handling
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QGroupBox, QLabel, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QFrame, QScrollArea, QMessageBox, QFileDialog,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMainWindow,
    QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMimeData
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.project import LupineProject
from core.ui.ui_prefabs import BUILTIN_PREFABS, UIPrefab, get_prefab
from core.ui.variable_binding import get_binding_manager, initialize_binding_manager
from editor.ui.prefab_library import PrefabLibrary
from editor.ui.variable_binding_widget import VariableBindingWidget
from editor.ui.event_binding_widget import EventBindingWidget
from editor.scene_view import SceneViewWidget
from editor.inspector import InspectorWidget


class HudPreviewWidget(QWidget):
    """Widget for previewing the HUD layout with camera bounds"""
    
    node_selected = pyqtSignal(dict)  # node_data
    node_modified = pyqtSignal(dict, str, object)  # node_data, property, value
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.scene_data = None
        self.setup_ui()
        self.create_default_scene()
    
    def setup_ui(self):
        """Setup the preview UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Title and controls
        header_layout = QHBoxLayout()
        
        title_label = QLabel("HUD Preview")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Resolution selector
        header_layout.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080", "1280x720", "1024x768", "800x600", "Custom"
        ])
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        header_layout.addWidget(self.resolution_combo)
        
        # Grid toggle
        self.grid_checkbox = QCheckBox("Grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.toggled.connect(self.toggle_grid)
        header_layout.addWidget(self.grid_checkbox)
        
        # Bounds toggle
        self.bounds_checkbox = QCheckBox("Bounds")
        self.bounds_checkbox.setChecked(True)
        self.bounds_checkbox.toggled.connect(self.toggle_bounds)
        header_layout.addWidget(self.bounds_checkbox)
        
        layout.addLayout(header_layout)
        
        # Scene view
        self.scene_view = None
        self.create_scene_view()
        layout.addWidget(self.scene_view)
    
    def create_default_scene(self):
        """Create a default scene for HUD building"""
        self.scene_data = {
            "name": "HUD_Builder_Scene",
            "nodes": [
                {
                    "name": "HUD_Root",
                    "type": "Control",
                    "position": [0, 0],
                    "size": [1920, 1080],
                    "follow_viewport": True,
                    "children": []
                }
            ]
        }
    
    def create_scene_view(self):
        """Create the scene view widget"""
        if self.scene_view:
            self.scene_view.setParent(None)

        self.scene_view = SceneViewWidget(self.project, "hud_builder_temp.scene", self.scene_data)

        # Connect signals
        if hasattr(self.scene_view, 'viewport') and self.scene_view.viewport:
            self.scene_view.viewport.node_selected.connect(self.node_selected)
            self.scene_view.viewport.node_modified.connect(self.node_modified)

            # Enable drop for prefabs
            self.scene_view.viewport.setAcceptDrops(True)
            # Store original methods
            self.scene_view.viewport._original_dragEnterEvent = self.scene_view.viewport.dragEnterEvent
            self.scene_view.viewport._original_dropEvent = self.scene_view.viewport.dropEvent
            # Override with our methods
            self.scene_view.viewport.dragEnterEvent = self.drag_enter_event
            self.scene_view.viewport.dropEvent = self.drop_event
    
    def drag_enter_event(self, event):
        """Handle drag enter for prefab and node drops"""
        mime_text = event.mimeData().text() if event.mimeData().hasText() else ""
        if mime_text.startswith("prefab:") or mime_text.startswith("node:"):
            event.acceptProposedAction()

    def drop_event(self, event):
        """Handle prefab and node drops"""
        if not event.mimeData().hasText():
            return

        mime_text = event.mimeData().text()
        drop_pos = event.position()

        # Convert screen position to world position
        if (self.scene_view and hasattr(self.scene_view, 'viewport') and
            self.scene_view.viewport and hasattr(self.scene_view.viewport, 'screen_to_world')):
            world_pos = self.scene_view.viewport.screen_to_world(drop_pos.x(), drop_pos.y())
            position = [world_pos[0], world_pos[1]]
        else:
            # Fallback to screen coordinates
            position = [drop_pos.x(), drop_pos.y()]

        if mime_text.startswith("prefab:"):
            prefab_name = mime_text.replace("prefab:", "")
            self.add_prefab_at_position(prefab_name, position)
        elif mime_text.startswith("node:"):
            node_type = mime_text.replace("node:", "")
            self.add_generic_node_at_position(node_type, position)

        event.acceptProposedAction()

    def add_prefab_at_position(self, prefab_name: str, position: List[float]):
        """Add a prefab instance at the specified position"""
        prefab = get_prefab(prefab_name)
        if not prefab or not self.scene_data:
            return

        # Create instance
        instance = prefab.create_instance()
        instance["position"] = position

        # Add to scene
        if self.scene_data and "nodes" in self.scene_data and len(self.scene_data["nodes"]) > 0:
            root_node = self.scene_data["nodes"][0]
            if "children" not in root_node:
                root_node["children"] = []
            root_node["children"].append(instance)

            # Update scene view
            if (self.scene_view and hasattr(self.scene_view, 'viewport') and
                self.scene_view.viewport):
                self.scene_view.viewport.scene_data = self.scene_data
                self.scene_view.viewport.update()

            # Select the new node
            self.node_selected.emit(instance)

            print(f"Added prefab '{prefab_name}' at position {position}")

    def add_generic_node_at_position(self, node_type: str, position: List[float]):
        """Add a generic UI node at the specified position"""
        if not self.scene_data:
            return

        # Create a basic node instance
        instance = {
            "name": f"{node_type}_{len(self.scene_data.get('nodes', [{}])[0].get('children', []))}",
            "type": node_type,
            "position": position,
            "size": [100, 30],  # Default size
            "children": []
        }

        # Add type-specific default properties
        if node_type == "Button":
            instance.update({
                "text": "Button",
                "bg_color": [0.3, 0.3, 0.3, 1.0],
                "border_width": 1.0
            })
        elif node_type == "Label":
            instance.update({
                "text": "Label",
                "font_size": 14,
                "font_color": [1.0, 1.0, 1.0, 1.0]
            })
        elif node_type == "Panel":
            instance.update({
                "bg_color": [0.2, 0.2, 0.2, 0.8],
                "border_width": 1.0,
                "size": [200, 150]
            })
        elif node_type == "TextureRect":
            instance.update({
                "texture": "",
                "stretch_mode": "stretch",
                "size": [100, 100]
            })
        elif node_type == "ProgressBar":
            instance.update({
                "min_value": 0.0,
                "max_value": 100.0,
                "value": 50.0,
                "size": [200, 20]
            })

        # Add to scene
        if self.scene_data and "nodes" in self.scene_data and len(self.scene_data["nodes"]) > 0:
            root_node = self.scene_data["nodes"][0]
            if "children" not in root_node:
                root_node["children"] = []
            root_node["children"].append(instance)

            # Update scene view
            if (self.scene_view and hasattr(self.scene_view, 'viewport') and
                self.scene_view.viewport):
                self.scene_view.viewport.scene_data = self.scene_data
                self.scene_view.viewport.update()

            # Select the new node
            self.node_selected.emit(instance)

            print(f"Added generic node '{node_type}' at position {position}")
    
    def on_resolution_changed(self, resolution_text: str):
        """Handle resolution change"""
        if resolution_text == "Custom":
            # TODO: Show custom resolution dialog
            return
        
        try:
            width, height = map(int, resolution_text.split('x'))
            # Update scene bounds
            if self.scene_data and self.scene_data["nodes"]:
                root_node = self.scene_data["nodes"][0]
                root_node["size"] = [width, height]
                
                if self.scene_view and hasattr(self.scene_view, 'viewport'):
                    self.scene_view.viewport.update()
        except:
            pass
    
    def toggle_grid(self, enabled: bool):
        """Toggle grid display"""
        if self.scene_view:
            self.scene_view.toggle_grid(enabled)
    
    def toggle_bounds(self, enabled: bool):
        """Toggle bounds display"""
        if self.scene_view:
            self.scene_view.toggle_bounds(enabled)
    
    def get_scene_data(self) -> Dict[str, Any]:
        """Get the current scene data"""
        return self.scene_data or {}

    def set_scene_data(self, scene_data: Dict[str, Any]):
        """Set the scene data"""
        self.scene_data = scene_data
        if (self.scene_view and hasattr(self.scene_view, 'viewport') and
            self.scene_view.viewport):
            self.scene_view.viewport.scene_data = scene_data
            self.scene_view.viewport.update()


class MenuHudBuilder(QWidget):
    """Main Menu and HUD Builder widget"""
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.current_node = None
        self.setup_ui()
        self.initialize_binding_system()
    
    def setup_ui(self):
        """Setup the main UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Prefab Library
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_panel.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(2, 2, 2, 2)
        
        self.prefab_library = PrefabLibrary()
        self.prefab_library.prefab_selected.connect(self.on_prefab_selected)
        left_layout.addWidget(self.prefab_library)
        
        main_splitter.addWidget(left_panel)
        
        # Center panel - Preview
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(2, 2, 2, 2)
        
        self.preview_widget = HudPreviewWidget(self.project)
        self.preview_widget.node_selected.connect(self.on_node_selected)
        self.preview_widget.node_modified.connect(self.on_node_modified)
        center_layout.addWidget(self.preview_widget)
        
        main_splitter.addWidget(center_panel)
        
        # Right panel - Inspector with tabs
        right_panel = QWidget()
        right_panel.setMaximumWidth(350)
        right_panel.setMinimumWidth(300)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(2, 2, 2, 2)
        
        # Inspector tabs
        self.inspector_tabs = QTabWidget()
        
        # Properties tab - use the actual InspectorWidget
        self.inspector_widget = InspectorWidget(self.project)
        self.inspector_widget.property_changed.connect(self.on_inspector_property_changed)
        self.inspector_tabs.addTab(self.inspector_widget, "Properties")
        
        # Variable bindings tab
        self.variable_binding_widget = VariableBindingWidget()
        self.variable_binding_widget.bindings_changed.connect(self.on_bindings_changed)
        self.inspector_tabs.addTab(self.variable_binding_widget, "Variables")
        
        # Event bindings tab
        self.event_binding_widget = EventBindingWidget()
        self.event_binding_widget.bindings_changed.connect(self.on_bindings_changed)
        self.inspector_tabs.addTab(self.event_binding_widget, "Events")
        
        right_layout.addWidget(self.inspector_tabs)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        save_button = QPushButton("Save HUD")
        save_button.clicked.connect(self.save_hud)
        action_layout.addWidget(save_button)
        
        load_button = QPushButton("Load HUD")
        load_button.clicked.connect(self.load_hud)
        action_layout.addWidget(load_button)
        
        test_button = QPushButton("Test HUD")
        test_button.clicked.connect(self.test_hud)
        action_layout.addWidget(test_button)
        
        right_layout.addLayout(action_layout)
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([250, 600, 300])
        
        layout.addWidget(main_splitter)
    
    def initialize_binding_system(self):
        """Initialize the variable binding system"""
        initialize_binding_manager()
    
    def on_prefab_selected(self, prefab_name: str):
        """Handle prefab selection from library"""
        # Could show prefab info or prepare for drag-and-drop
        pass
    
    def on_node_selected(self, node_data: Dict[str, Any]):
        """Handle node selection from preview"""
        self.current_node = node_data

        # Update inspector widget with the selected node
        self.inspector_widget.set_node(node_data)

        # Update inspector tabs
        self.variable_binding_widget.set_node(node_data)
        self.event_binding_widget.set_node(node_data)
    
    def on_node_modified(self, node_data: Dict[str, Any], property_name: str, value: Any):
        """Handle node modification from preview"""
        # Update binding system if needed
        binding_manager = get_binding_manager()
        if binding_manager:
            # Check if this affects any variable bindings
            node_id = node_data.get("name", "")
            bindings = binding_manager.get_bindings(node_id)
            for binding in bindings:
                if binding.property_name == property_name:
                    # Property that has bindings was modified
                    break
    
    def on_inspector_property_changed(self, node_id: str, property_name: str, value: Any):
        """Handle property changes from the inspector"""
        # Update the scene view
        if (self.preview_widget and hasattr(self.preview_widget, 'scene_view') and
            self.preview_widget.scene_view and hasattr(self.preview_widget.scene_view, 'viewport') and
            self.preview_widget.scene_view.viewport):
            self.preview_widget.scene_view.viewport.update()

        # Update variable bindings if needed
        self.on_bindings_changed()

    def on_bindings_changed(self):
        """Handle changes to variable or event bindings"""
        # Update the preview if needed
        if (self.preview_widget and hasattr(self.preview_widget, 'scene_view') and
            self.preview_widget.scene_view and hasattr(self.preview_widget.scene_view, 'viewport') and
            self.preview_widget.scene_view.viewport):
            self.preview_widget.scene_view.viewport.update()
    
    def save_hud(self):
        """Save the current HUD layout"""
        scene_data = self.preview_widget.get_scene_data()
        if not scene_data:
            QMessageBox.warning(self, "No Data", "No HUD data to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save HUD Layout", "", "Scene Files (*.scene);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(scene_data, f, indent=2)
                QMessageBox.information(self, "Saved", f"HUD layout saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save HUD: {e}")
    
    def load_hud(self):
        """Load a HUD layout"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load HUD Layout", "", "Scene Files (*.scene);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    scene_data = json.load(f)
                
                self.preview_widget.set_scene_data(scene_data)
                QMessageBox.information(self, "Loaded", f"HUD layout loaded from: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load HUD: {e}")
    
    def test_hud(self):
        """Test the current HUD with sample data"""
        # TODO: Implement HUD testing with sample variable values
        QMessageBox.information(self, "Test HUD", "HUD testing functionality coming soon!")


class MenuHudBuilderWindow(QMainWindow):
    """Standalone window for the Menu and HUD Builder"""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_window()

    def setup_window(self):
        """Setup the window"""
        self.setWindowTitle("Menu and HUD Builder - Lupine Engine")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Create the main widget
        self.hud_builder = MenuHudBuilder(self.project)
        self.setCentralWidget(self.hud_builder)

        # Connect signals for node handling
        self.hud_builder.prefab_library.node_selected.connect(self.on_generic_node_selected)

        # Set window icon if available
        try:
            from PyQt6.QtGui import QIcon
            import os
            icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass

    def on_generic_node_selected(self, node_type: str):
        """Handle selection of generic UI nodes"""
        # For now, just add them like prefabs
        # In the future, this could open a configuration dialog
        print(f"Generic node selected: {node_type}")

        # Add the node at a default position
        if hasattr(self.hud_builder, 'preview_widget'):
            self.hud_builder.preview_widget.add_generic_node_at_position(node_type, [100, 100])

    def closeEvent(self, event):
        """Handle window close event"""
        # Save any unsaved changes or ask user
        event.accept()
