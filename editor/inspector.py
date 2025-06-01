"""
Inspector Widget for Lupine Engine
Displays and edits properties of selected nodes using LSC export variables
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFormLayout, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QGroupBox, QPushButton, QHBoxLayout, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.project import LupineProject
from core.lsc.export_parser import LSCExportParser, ExportGroup, ExportVariable
from .script_dialog import ScriptAttachmentDialog


class InspectorWidget(QWidget):
    """Widget for inspecting and editing node properties"""
    
    property_changed = pyqtSignal(str, str, object)  # node_id, property_name, value
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.current_node = None
        self.property_widgets = {}
        self.export_parser = LSCExportParser()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel("Inspector")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Scroll area for properties
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Properties widget
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_widget)
        self.properties_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.properties_widget)
        layout.addWidget(self.scroll_area)
        
        # Show empty state initially
        self.show_empty_state()
    
    def show_empty_state(self):
        """Show empty state when no node is selected"""
        self.clear_properties()
        
        empty_label = QLabel("No node selected")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("color: #b0b0b0; font-style: italic;")
        self.properties_layout.addWidget(empty_label)
    
    def clear_properties(self):
        """Clear all property widgets"""
        # Remove all widgets from layout
        while self.properties_layout.count():
            child = self.properties_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.property_widgets.clear()
    
    def set_node(self, node_data: Dict[str, Any]):
        """Set the node to inspect"""
        self.current_node = node_data
        self.refresh_properties()
    
    def refresh_properties(self):
        """Refresh the properties display"""
        self.clear_properties()
        
        if not self.current_node:
            self.show_empty_state()
            return
        
        # Node info group
        self.create_node_info_group()
        
        # Transform group (for Node2D and derived)
        node_type = self.current_node.get("type", "Node")
        if "2D" in node_type or node_type in ["Sprite", "Camera2D", "Area2D"]:
            self.create_transform_group()
        
        # Type-specific properties
        if node_type == "Sprite":
            self.create_sprite_group()
        elif node_type == "Camera2D":
            self.create_camera_group()
        elif node_type == "Area2D":
            self.create_area_group()
        
        # Script properties (LSC export variables)
        script_path = self.current_node.get("script")
        if script_path:
            self.create_script_group(script_path)
        
        # Add script button if no script attached
        if not script_path:
            self.create_script_button()
    
    def create_node_info_group(self):
        """Create node information group"""
        group = QGroupBox("Node")
        layout = QFormLayout(group)
        
        # Node name
        name_edit = QLineEdit(self.current_node.get("name", ""))
        name_edit.textChanged.connect(lambda text: self.update_property("name", text))
        layout.addRow("Name:", name_edit)
        self.property_widgets["name"] = name_edit
        
        # Node type (read-only)
        type_label = QLabel(self.current_node.get("type", "Node"))
        type_label.setStyleSheet("color: #b0b0b0;")
        layout.addRow("Type:", type_label)
        
        self.properties_layout.addWidget(group)
    
    def create_transform_group(self):
        """Create transform properties group"""
        group = QGroupBox("Transform")
        layout = QFormLayout(group)
        
        # Position
        position = self.current_node.get("position", [0, 0])
        pos_layout = QHBoxLayout()
        
        pos_x = QDoubleSpinBox()
        pos_x.setRange(-999999, 999999)
        pos_x.setValue(position[0])
        pos_x.valueChanged.connect(lambda v: self.update_position(0, v))
        pos_layout.addWidget(pos_x)
        
        pos_y = QDoubleSpinBox()
        pos_y.setRange(-999999, 999999)
        pos_y.setValue(position[1])
        pos_y.valueChanged.connect(lambda v: self.update_position(1, v))
        pos_layout.addWidget(pos_y)
        
        layout.addRow("Position:", pos_layout)
        self.property_widgets["position_x"] = pos_x
        self.property_widgets["position_y"] = pos_y
        
        # Rotation
        rotation = self.current_node.get("rotation", 0)
        rot_spin = QDoubleSpinBox()
        rot_spin.setRange(-360, 360)
        rot_spin.setSuffix("°")
        rot_spin.setValue(rotation)
        rot_spin.valueChanged.connect(lambda v: self.update_property("rotation", v))
        layout.addRow("Rotation:", rot_spin)
        self.property_widgets["rotation"] = rot_spin
        
        # Scale
        scale = self.current_node.get("scale", [1, 1])
        scale_layout = QHBoxLayout()
        
        scale_x = QDoubleSpinBox()
        scale_x.setRange(0.01, 100)
        scale_x.setSingleStep(0.1)
        scale_x.setValue(scale[0])
        scale_x.valueChanged.connect(lambda v: self.update_scale(0, v))
        scale_layout.addWidget(scale_x)
        
        scale_y = QDoubleSpinBox()
        scale_y.setRange(0.01, 100)
        scale_y.setSingleStep(0.1)
        scale_y.setValue(scale[1])
        scale_y.valueChanged.connect(lambda v: self.update_scale(1, v))
        scale_layout.addWidget(scale_y)
        
        layout.addRow("Scale:", scale_layout)
        self.property_widgets["scale_x"] = scale_x
        self.property_widgets["scale_y"] = scale_y
        
        # Z Index
        z_index = self.current_node.get("z_index", 0)
        z_spin = QSpinBox()
        z_spin.setRange(-1000, 1000)
        z_spin.setValue(z_index)
        z_spin.valueChanged.connect(lambda v: self.update_property("z_index", v))
        layout.addRow("Z Index:", z_spin)
        self.property_widgets["z_index"] = z_spin
        
        # Visible
        visible = self.current_node.get("visible", True)
        visible_check = QCheckBox()
        visible_check.setChecked(visible)
        visible_check.toggled.connect(lambda v: self.update_property("visible", v))
        layout.addRow("Visible:", visible_check)
        self.property_widgets["visible"] = visible_check
        
        self.properties_layout.addWidget(group)
    
    def create_sprite_group(self):
        """Create sprite-specific properties - Godot Sprite2D equivalent"""
        group = QGroupBox("Sprite")
        layout = QFormLayout(group)

        # Texture path
        texture = self.current_node.get("texture", "")
        texture_edit = QLineEdit(str(texture) if texture else "")
        texture_edit.setPlaceholderText("Path to texture file...")
        texture_edit.textChanged.connect(lambda text: self.update_property("texture", text))
        layout.addRow("Texture:", texture_edit)
        self.property_widgets["texture"] = texture_edit

        # Centered
        centered = self.current_node.get("centered", True)
        centered_check = QCheckBox()
        centered_check.setChecked(centered)
        centered_check.toggled.connect(lambda v: self.update_property("centered", v))
        layout.addRow("Centered:", centered_check)
        self.property_widgets["centered"] = centered_check

        # Offset
        offset = self.current_node.get("offset", [0.0, 0.0])
        offset_layout = QHBoxLayout()

        offset_x = QDoubleSpinBox()
        offset_x.setRange(-9999.0, 9999.0)
        offset_x.setValue(offset[0])
        offset_x.valueChanged.connect(lambda v: self.update_offset(0, v))
        offset_layout.addWidget(offset_x)

        offset_y = QDoubleSpinBox()
        offset_y.setRange(-9999.0, 9999.0)
        offset_y.setValue(offset[1])
        offset_y.valueChanged.connect(lambda v: self.update_offset(1, v))
        offset_layout.addWidget(offset_y)

        layout.addRow("Offset:", offset_layout)
        self.property_widgets["offset_x"] = offset_x
        self.property_widgets["offset_y"] = offset_y

        # Flip H/V
        flip_layout = QHBoxLayout()

        flip_h = self.current_node.get("flip_h", False)
        flip_h_check = QCheckBox("Horizontal")
        flip_h_check.setChecked(flip_h)
        flip_h_check.toggled.connect(lambda v: self.update_property("flip_h", v))
        flip_layout.addWidget(flip_h_check)
        self.property_widgets["flip_h"] = flip_h_check

        flip_v = self.current_node.get("flip_v", False)
        flip_v_check = QCheckBox("Vertical")
        flip_v_check.setChecked(flip_v)
        flip_v_check.toggled.connect(lambda v: self.update_property("flip_v", v))
        flip_layout.addWidget(flip_v_check)
        self.property_widgets["flip_v"] = flip_v_check

        layout.addRow("Flip:", flip_layout)

        # Animation frames
        hframes = self.current_node.get("hframes", 1)
        hframes_spin = QSpinBox()
        hframes_spin.setRange(1, 999)
        hframes_spin.setValue(hframes)
        hframes_spin.valueChanged.connect(lambda v: self.update_property("hframes", v))
        layout.addRow("H Frames:", hframes_spin)
        self.property_widgets["hframes"] = hframes_spin

        vframes = self.current_node.get("vframes", 1)
        vframes_spin = QSpinBox()
        vframes_spin.setRange(1, 999)
        vframes_spin.setValue(vframes)
        vframes_spin.valueChanged.connect(lambda v: self.update_property("vframes", v))
        layout.addRow("V Frames:", vframes_spin)
        self.property_widgets["vframes"] = vframes_spin

        # Current frame
        frame = self.current_node.get("frame", 0)
        frame_spin = QSpinBox()
        frame_spin.setRange(0, 999)
        frame_spin.setValue(frame)
        frame_spin.valueChanged.connect(lambda v: self.update_property("frame", v))
        layout.addRow("Frame:", frame_spin)
        self.property_widgets["frame"] = frame_spin

        self.properties_layout.addWidget(group)
    
    def create_camera_group(self):
        """Create camera-specific properties"""
        group = QGroupBox("Camera2D")
        layout = QFormLayout(group)
        
        # Current camera
        current = self.current_node.get("current", False)
        current_check = QCheckBox()
        current_check.setChecked(current)
        current_check.toggled.connect(lambda v: self.update_property("current", v))
        layout.addRow("Current:", current_check)
        self.property_widgets["current"] = current_check
        
        # Zoom
        zoom = self.current_node.get("zoom", [1.0, 1.0])
        zoom_layout = QHBoxLayout()
        
        zoom_x = QDoubleSpinBox()
        zoom_x.setRange(0.1, 10.0)
        zoom_x.setSingleStep(0.1)
        zoom_x.setValue(zoom[0])
        zoom_x.valueChanged.connect(lambda v: self.update_zoom(0, v))
        zoom_layout.addWidget(zoom_x)
        
        zoom_y = QDoubleSpinBox()
        zoom_y.setRange(0.1, 10.0)
        zoom_y.setSingleStep(0.1)
        zoom_y.setValue(zoom[1])
        zoom_y.valueChanged.connect(lambda v: self.update_zoom(1, v))
        zoom_layout.addWidget(zoom_y)
        
        layout.addRow("Zoom:", zoom_layout)
        self.property_widgets["zoom_x"] = zoom_x
        self.property_widgets["zoom_y"] = zoom_y
        
        self.properties_layout.addWidget(group)
    
    def create_area_group(self):
        """Create Area2D-specific properties"""
        group = QGroupBox("Area2D")
        layout = QFormLayout(group)
        
        # Monitoring
        monitoring = self.current_node.get("monitoring", True)
        monitoring_check = QCheckBox()
        monitoring_check.setChecked(monitoring)
        monitoring_check.toggled.connect(lambda v: self.update_property("monitoring", v))
        layout.addRow("Monitoring:", monitoring_check)
        self.property_widgets["monitoring"] = monitoring_check
        
        self.properties_layout.addWidget(group)
    
    def create_script_group(self, script_path: str):
        """Create script properties group with export variables"""
        group = QGroupBox("Script")
        layout = QFormLayout(group)

        # Script path with edit button
        script_layout = QHBoxLayout()
        script_label = QLabel(script_path)
        script_label.setStyleSheet("color: #b0b0b0;")
        script_layout.addWidget(script_label)

        edit_script_btn = QPushButton("Edit")
        edit_script_btn.setMaximumWidth(60)
        edit_script_btn.clicked.connect(lambda: self.edit_script(script_path))
        script_layout.addWidget(edit_script_btn)

        layout.addRow("Script:", script_layout)

        # Parse and display export variables
        self.load_export_variables(script_path, layout)

        self.properties_layout.addWidget(group)
    
    def create_script_button(self):
        """Create attach script button"""
        button_layout = QHBoxLayout()
        attach_script_btn = QPushButton("Attach Script")
        attach_script_btn.clicked.connect(self.attach_script)
        button_layout.addWidget(attach_script_btn)
        button_layout.addStretch()
        
        self.properties_layout.addLayout(button_layout)
    
    def update_property(self, property_name: str, value):
        """Update a node property"""
        if self.current_node:
            self.current_node[property_name] = value
            # Emit signal for external listeners
            node_id = self.current_node.get("name", "")
            self.property_changed.emit(node_id, property_name, value)
    
    def update_position(self, index: int, value: float):
        """Update position component"""
        if self.current_node:
            position = self.current_node.get("position", [0, 0])
            position[index] = value
            self.current_node["position"] = position
            self.property_changed.emit(self.current_node.get("name", ""), "position", position)
    
    def update_scale(self, index: int, value: float):
        """Update scale component"""
        if self.current_node:
            scale = self.current_node.get("scale", [1, 1])
            scale[index] = value
            self.current_node["scale"] = scale
            self.property_changed.emit(self.current_node.get("name", ""), "scale", scale)
    
    def update_size(self, index: int, value: int):
        """Update size component"""
        if self.current_node:
            size = self.current_node.get("size", [64, 64])
            size[index] = value
            self.current_node["size"] = size
            self.property_changed.emit(self.current_node.get("name", ""), "size", size)
    
    def update_zoom(self, index: int, value: float):
        """Update zoom component"""
        if self.current_node:
            zoom = self.current_node.get("zoom", [1.0, 1.0])
            zoom[index] = value
            self.current_node["zoom"] = zoom
            self.property_changed.emit(self.current_node.get("name", ""), "zoom", zoom)
    
    def attach_script(self):
        """Attach a script to the current node"""
        if not self.current_node:
            return

        dialog = ScriptAttachmentDialog(self.project, self.current_node, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            script_path = dialog.get_script_path()
            if script_path:
                # Attach script to node
                self.current_node["script"] = script_path

                # Refresh properties to show script group
                self.refresh_properties()

                # Emit property change signal
                node_id = self.current_node.get("name", "")
                self.property_changed.emit(node_id, "script", script_path)

    def edit_script(self, script_path: str):
        """Open script in script editor"""
        # Get the main editor window
        main_window = self.window()
        if hasattr(main_window, 'script_editor'):
            full_path = self.project.get_absolute_path(script_path)
            main_window.script_editor.open_script_file(str(full_path))
            main_window.script_editor_dock.raise_()

    def load_export_variables(self, script_path: str, layout: QFormLayout):
        """Load and display export variables from script"""
        try:
            full_path = self.project.get_absolute_path(script_path)
            if not full_path.exists():
                return

            # Parse export variables
            groups, ungrouped_vars = self.export_parser.parse_script_file(str(full_path))

            # Add ungrouped variables first
            for var in ungrouped_vars:
                self.create_export_variable_widget(var, layout)

            # Add grouped variables
            for group in groups:
                # Create group separator
                group_label = QLabel(f"--- {group.name} ---")
                group_label.setStyleSheet("font-weight: bold; color: #8b5fbf; margin-top: 10px;")
                layout.addRow(group_label)

                if group.hint:
                    hint_label = QLabel(group.hint)
                    hint_label.setStyleSheet("color: #b0b0b0; font-style: italic; font-size: 10px;")
                    layout.addRow(hint_label)

                for var in group.variables:
                    self.create_export_variable_widget(var, layout)

        except Exception as e:
            print(f"Error loading export variables: {e}")

    def create_export_variable_widget(self, var: ExportVariable, layout: QFormLayout):
        """Create widget for an export variable"""
        widget_key = f"export_{var.name}"

        # Get current value from node or use default
        current_value = self.current_node.get(var.name, var.default_value)

        if var.type in ['int', 'integer']:
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(int(current_value) if current_value is not None else 0)
            widget.valueChanged.connect(lambda v: self.update_property(var.name, v))

        elif var.type in ['float', 'real']:
            widget = QDoubleSpinBox()
            widget.setRange(-999999.0, 999999.0)
            widget.setDecimals(3)
            widget.setValue(float(current_value) if current_value is not None else 0.0)
            widget.valueChanged.connect(lambda v: self.update_property(var.name, v))

        elif var.type in ['bool', 'boolean']:
            widget = QCheckBox()
            widget.setChecked(bool(current_value) if current_value is not None else False)
            widget.toggled.connect(lambda v: self.update_property(var.name, v))

        elif var.type in ['string', 'str']:
            widget = QLineEdit()
            widget.setText(str(current_value) if current_value is not None else "")
            widget.textChanged.connect(lambda text: self.update_property(var.name, text))

        elif var.type == 'Vector2':
            widget = QWidget()
            widget_layout = QHBoxLayout(widget)
            widget_layout.setContentsMargins(0, 0, 0, 0)

            value = current_value if isinstance(current_value, list) else [0.0, 0.0]

            x_spin = QDoubleSpinBox()
            x_spin.setRange(-999999.0, 999999.0)
            x_spin.setValue(value[0])
            x_spin.valueChanged.connect(lambda v: self.update_vector2(var.name, 0, v))

            y_spin = QDoubleSpinBox()
            y_spin.setRange(-999999.0, 999999.0)
            y_spin.setValue(value[1])
            y_spin.valueChanged.connect(lambda v: self.update_vector2(var.name, 1, v))

            widget_layout.addWidget(x_spin)
            widget_layout.addWidget(y_spin)

            self.property_widgets[f"{widget_key}_x"] = x_spin
            self.property_widgets[f"{widget_key}_y"] = y_spin

        else:
            # Default to string for unknown types
            widget = QLineEdit()
            widget.setText(str(current_value) if current_value is not None else "")
            widget.textChanged.connect(lambda text: self.update_property(var.name, text))

        # Add tooltip if hint is available
        if var.hint:
            widget.setToolTip(var.hint)

        # Create label with type info
        label_text = f"{var.name} ({var.type})"
        layout.addRow(label_text, widget)

        self.property_widgets[widget_key] = widget

    def update_vector2(self, property_name: str, index: int, value: float):
        """Update Vector2 component"""
        if self.current_node:
            current_value = self.current_node.get(property_name, [0.0, 0.0])
            if not isinstance(current_value, list):
                current_value = [0.0, 0.0]

            current_value[index] = value
            self.current_node[property_name] = current_value

            node_id = self.current_node.get("name", "")
            self.property_changed.emit(node_id, property_name, current_value)

    def update_offset(self, index: int, value: float):
        """Update offset component"""
        if self.current_node:
            offset = self.current_node.get("offset", [0.0, 0.0])
            offset[index] = value
            self.current_node["offset"] = offset
            self.property_changed.emit(self.current_node.get("name", ""), "offset", offset)
