"""
Inspector Widget for Lupine Engine
Displays and edits properties of selected nodes using LSC export variables
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFormLayout, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QGroupBox, QPushButton, QHBoxLayout, QTextEdit, QMessageBox,
    QFileDialog, QDialog, QListWidget, QDialogButtonBox, QFrame,
    QSplitter, QTreeWidget, QTreeWidgetItem, QMenu, QGridLayout,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize
from PyQt6.QtGui import QFont, QAction, QPainter, QPen, QBrush, QColor

from core.project import LupineProject
from core.lsc.export_parser import LSCExportParser, ExportGroup, ExportVariable
from .script_dialog import ScriptAttachmentDialog


class AnchorSelectorWidget(QWidget):
    """Visual anchor selector widget similar to Godot's anchor editor"""

    anchor_changed = pyqtSignal(str, float)  # side, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)

        # Current anchor values
        self.anchor_left = 0.0
        self.anchor_top = 0.0
        self.anchor_right = 0.0
        self.anchor_bottom = 0.0

        # Preset configurations
        self.presets = {
            "top_left": (0.0, 0.0, 0.0, 0.0),
            "top_center": (0.5, 0.0, 0.5, 0.0),
            "top_right": (1.0, 0.0, 1.0, 0.0),
            "center_left": (0.0, 0.5, 0.0, 0.5),
            "center": (0.5, 0.5, 0.5, 0.5),
            "center_right": (1.0, 0.5, 1.0, 0.5),
            "bottom_left": (0.0, 1.0, 0.0, 1.0),
            "bottom_center": (0.5, 1.0, 0.5, 1.0),
            "bottom_right": (1.0, 1.0, 1.0, 1.0),
            "left_wide": (0.0, 0.0, 0.0, 1.0),
            "top_wide": (0.0, 0.0, 1.0, 0.0),
            "right_wide": (1.0, 0.0, 1.0, 1.0),
            "bottom_wide": (0.0, 1.0, 1.0, 1.0),
            "vcenter_wide": (0.0, 0.5, 1.0, 0.5),
            "hcenter_wide": (0.5, 0.0, 0.5, 1.0),
            "full_rect": (0.0, 0.0, 1.0, 1.0)
        }

        self.setToolTip("Click to select anchor preset")

    def set_anchors(self, left: float, top: float, right: float, bottom: float):
        """Set anchor values"""
        self.anchor_left = left
        self.anchor_top = top
        self.anchor_right = right
        self.anchor_bottom = bottom
        self.update()

    def paintEvent(self, event):
        """Paint the anchor selector"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), QColor(40, 40, 40))

        # Draw parent container outline
        margin = 10
        container_rect = self.rect().adjusted(margin, margin, -margin, -margin)
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(container_rect)

        # Draw anchor lines
        painter.setPen(QPen(QColor(150, 150, 255), 2))

        # Calculate anchor positions
        left_x = container_rect.left() + self.anchor_left * container_rect.width()
        top_y = container_rect.top() + self.anchor_top * container_rect.height()
        right_x = container_rect.left() + self.anchor_right * container_rect.width()
        bottom_y = container_rect.top() + self.anchor_bottom * container_rect.height()

        # Draw anchor rectangle
        if self.anchor_left != self.anchor_right or self.anchor_top != self.anchor_bottom:
            # Draw anchor area
            painter.setBrush(QBrush(QColor(150, 150, 255, 50)))
            painter.drawRect(int(left_x), int(top_y), int(right_x - left_x), int(bottom_y - top_y))

        # Draw anchor points
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0), 1))

        # Draw corner points
        point_size = 4
        painter.drawEllipse(int(left_x - point_size/2), int(top_y - point_size/2), point_size, point_size)
        painter.drawEllipse(int(right_x - point_size/2), int(top_y - point_size/2), point_size, point_size)
        painter.drawEllipse(int(left_x - point_size/2), int(bottom_y - point_size/2), point_size, point_size)
        painter.drawEllipse(int(right_x - point_size/2), int(bottom_y - point_size/2), point_size, point_size)

    def mousePressEvent(self, event):
        """Handle mouse clicks to select presets"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Determine which preset area was clicked
            x_ratio = event.position().x() / self.width()
            y_ratio = event.position().y() / self.height()

            # Map click position to preset
            preset_name = self._get_preset_from_position(x_ratio, y_ratio)
            if preset_name and preset_name in self.presets:
                left, top, right, bottom = self.presets[preset_name]
                self.set_anchors(left, top, right, bottom)

                # Emit signals for each anchor
                self.anchor_changed.emit("left", left)
                self.anchor_changed.emit("top", top)
                self.anchor_changed.emit("right", right)
                self.anchor_changed.emit("bottom", bottom)

    def _get_preset_from_position(self, x_ratio: float, y_ratio: float) -> str:
        """Map click position to preset name"""
        # Divide widget into 3x3 grid for basic presets
        col = 0 if x_ratio < 0.33 else (1 if x_ratio < 0.66 else 2)
        row = 0 if y_ratio < 0.33 else (1 if y_ratio < 0.66 else 2)

        preset_grid = [
            ["top_left", "top_center", "top_right"],
            ["center_left", "center", "center_right"],
            ["bottom_left", "bottom_center", "bottom_right"]
        ]

        return preset_grid[row][col]


class AnchorPresetWidget(QWidget):
    """Widget with preset buttons for common anchor configurations"""

    preset_selected = pyqtSignal(str)  # preset name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the preset buttons"""
        layout = QGridLayout(self)
        layout.setSpacing(2)

        # Define preset buttons with their grid positions
        presets = [
            ("TL", "top_left", 0, 0),
            ("TC", "top_center", 0, 1),
            ("TR", "top_right", 0, 2),
            ("CL", "center_left", 1, 0),
            ("CC", "center", 1, 1),
            ("CR", "center_right", 1, 2),
            ("BL", "bottom_left", 2, 0),
            ("BC", "bottom_center", 2, 1),
            ("BR", "bottom_right", 2, 2),
            ("LW", "left_wide", 3, 0),
            ("TW", "top_wide", 3, 1),
            ("RW", "right_wide", 3, 2),
            ("BW", "bottom_wide", 4, 0),
            ("VW", "vcenter_wide", 4, 1),
            ("HW", "hcenter_wide", 4, 2),
            ("FR", "full_rect", 5, 1)
        ]

        for text, preset_name, row, col in presets:
            btn = QPushButton(text)
            btn.setFixedSize(30, 25)
            btn.setToolTip(self._get_preset_tooltip(preset_name))
            btn.clicked.connect(lambda checked, name=preset_name: self.preset_selected.emit(name))
            layout.addWidget(btn, row, col)

    def _get_preset_tooltip(self, preset_name: str) -> str:
        """Get tooltip for preset"""
        tooltips = {
            "top_left": "Top Left",
            "top_center": "Top Center",
            "top_right": "Top Right",
            "center_left": "Center Left",
            "center": "Center",
            "center_right": "Center Right",
            "bottom_left": "Bottom Left",
            "bottom_center": "Bottom Center",
            "bottom_right": "Bottom Right",
            "left_wide": "Left Wide",
            "top_wide": "Top Wide",
            "right_wide": "Right Wide",
            "bottom_wide": "Bottom Wide",
            "vcenter_wide": "Vertical Center Wide",
            "hcenter_wide": "Horizontal Center Wide",
            "full_rect": "Full Rectangle"
        }
        return tooltips.get(preset_name, preset_name)


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

        # For nodes with built-in scripts, ensure script path is properly set
        if node_data and node_data.get("type") in ["Button", "Sprite", "Timer", "Panel", "Label", "CanvasLayer", "Camera2D", "AnimatedSprite"]:
            # Check if node has a script path but it's not in the dict
            node_type = node_data.get("type")
            if not node_data.get("script"):
                # Add default script path for built-in nodes
                script_paths = {
                    "Button": "nodes/Button.lsc",
                    "Sprite": "nodes/Sprite.lsc",
                    "Timer": "nodes/Timer.lsc",
                    "Panel": "nodes/Panel.lsc",
                    "Label": "nodes/Label.lsc",
                    "CanvasLayer": "nodes/CanvasLayer.lsc",
                    "Camera2D": "nodes/Camera2D.lsc",
                    "AnimatedSprite": "nodes/AnimatedSprite.lsc"
                }
                if node_type in script_paths:
                    node_data["script"] = script_paths[node_type]

        self.refresh_properties()

    def update_node_reference(self, updated_node_data: dict):
        """Update the current node reference while preserving the UI state"""
        if self.current_node and updated_node_data:
            current_node_name = self.current_node.get("name", "")
            updated_node_name = updated_node_data.get("name", "")

            # Only update if it's the same node
            if current_node_name == updated_node_name:
                self.current_node = updated_node_data
                # Update UI widgets to reflect the new values
                self.update_property_widgets()

    def update_property_widgets(self):
        """Update property widgets to reflect current node values without rebuilding UI"""
        if not self.current_node:
            return

        # Update Vector2 properties (position, scale, etc.)
        vector2_props = ["position", "scale", "zoom", "offset"]
        for prop_name in vector2_props:
            value = self.current_node.get(prop_name)
            if value is not None and isinstance(value, list) and len(value) >= 2:
                # Try both old hardcoded keys and new export keys
                x_keys = [f"{prop_name}_x", f"export_{prop_name}_x"]
                y_keys = [f"{prop_name}_y", f"export_{prop_name}_y"]

                for x_key in x_keys:
                    if x_key in self.property_widgets:
                        widget = self.property_widgets[x_key]
                        widget.blockSignals(True)
                        widget.setValue(value[0])
                        widget.blockSignals(False)
                        break

                for y_key in y_keys:
                    if y_key in self.property_widgets:
                        widget = self.property_widgets[y_key]
                        widget.blockSignals(True)
                        widget.setValue(value[1])
                        widget.blockSignals(False)
                        break

        # Update scalar properties
        scalar_props = ["rotation", "z_index", "opacity", "wait_time", "speed_scale", "frame"]
        for prop_name in scalar_props:
            value = self.current_node.get(prop_name)
            if value is not None:
                # Try both old hardcoded keys and new export keys
                keys = [prop_name, f"export_{prop_name}"]

                for key in keys:
                    if key in self.property_widgets:
                        widget = self.property_widgets[key]
                        widget.blockSignals(True)
                        if hasattr(widget, 'setValue'):
                            widget.setValue(value)
                        elif hasattr(widget, 'setText'):
                            widget.setText(str(value))
                        widget.blockSignals(False)
                        break

        # Update boolean properties
        bool_props = ["visible", "centered", "flip_h", "flip_v", "current", "enabled",
                     "monitoring", "one_shot", "autostart", "paused", "playing"]
        for prop_name in bool_props:
            value = self.current_node.get(prop_name)
            if value is not None:
                # Try both old hardcoded keys and new export keys
                keys = [prop_name, f"export_{prop_name}"]

                for key in keys:
                    if key in self.property_widgets:
                        widget = self.property_widgets[key]
                        widget.blockSignals(True)
                        widget.setChecked(bool(value))
                        widget.blockSignals(False)
                        break

        # Update string properties
        string_props = ["name", "texture", "animation", "autoplay", "follow_target"]
        for prop_name in string_props:
            value = self.current_node.get(prop_name)
            if value is not None:
                # Try both old hardcoded keys and new export keys
                keys = [prop_name, f"export_{prop_name}"]

                for key in keys:
                    if key in self.property_widgets:
                        widget = self.property_widgets[key]
                        widget.blockSignals(True)
                        widget.setText(str(value))
                        widget.blockSignals(False)
                        break
    
    def refresh_properties(self):
        """Refresh the properties display"""
        self.clear_properties()
        
        if not self.current_node:
            self.show_empty_state()
            return
        
        # Node info group
        self.create_node_info_group()
        
        # All node properties are now handled dynamically through LSC export variables
        # No more hardcoded property groups needed
        
        # Script management section
        self.create_script_management_section()
    
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

        # Texture path with browse button
        texture = self.current_node.get("texture", "")
        texture_layout = QHBoxLayout()

        texture_edit = QLineEdit(str(texture) if texture else "")
        texture_edit.setPlaceholderText("Path to texture file...")
        texture_edit.textChanged.connect(lambda text: self.update_property("texture", text))
        texture_layout.addWidget(texture_edit)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_texture(texture_edit))
        texture_layout.addWidget(browse_btn)

        layout.addRow("Texture:", texture_layout)
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

    def create_animated_sprite_group(self):
        """Create AnimatedSprite-specific properties - Godot AnimatedSprite2D equivalent"""
        # First create the base sprite properties
        self.create_sprite_group()

        # Add animation-specific properties
        group = QGroupBox("Animation")
        layout = QFormLayout(group)

        # Animation name
        animation = self.current_node.get("animation", "default")
        animation_edit = QLineEdit(str(animation))
        animation_edit.textChanged.connect(lambda text: self.update_property("animation", text))
        layout.addRow("Animation:", animation_edit)
        self.property_widgets["animation"] = animation_edit

        # Speed scale
        speed_scale = self.current_node.get("speed_scale", 1.0)
        speed_spin = QDoubleSpinBox()
        speed_spin.setRange(0.01, 10.0)
        speed_spin.setSingleStep(0.1)
        speed_spin.setValue(speed_scale)
        speed_spin.valueChanged.connect(lambda v: self.update_property("speed_scale", v))
        layout.addRow("Speed Scale:", speed_spin)
        self.property_widgets["speed_scale"] = speed_spin

        # Playing state
        playing = self.current_node.get("playing", False)
        playing_check = QCheckBox()
        playing_check.setChecked(playing)
        playing_check.toggled.connect(lambda v: self.update_property("playing", v))
        layout.addRow("Playing:", playing_check)
        self.property_widgets["playing"] = playing_check

        # Autoplay animation
        autoplay = self.current_node.get("autoplay", "")
        autoplay_edit = QLineEdit(str(autoplay))
        autoplay_edit.textChanged.connect(lambda text: self.update_property("autoplay", text))
        layout.addRow("Autoplay:", autoplay_edit)
        self.property_widgets["autoplay"] = autoplay_edit

        # Frame progress (read-only for now)
        frame_progress = self.current_node.get("frame_progress", 0.0)
        progress_label = QLabel(f"{frame_progress:.2f}")
        progress_label.setStyleSheet("color: #b0b0b0;")
        layout.addRow("Frame Progress:", progress_label)

        # Animation controls
        controls_layout = QHBoxLayout()

        play_btn = QPushButton("Play")
        play_btn.clicked.connect(lambda: self.update_property("playing", True))
        controls_layout.addWidget(play_btn)

        pause_btn = QPushButton("Pause")
        pause_btn.clicked.connect(lambda: self.update_property("playing", False))
        controls_layout.addWidget(pause_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(lambda: [
            self.update_property("playing", False),
            self.update_property("frame", 0)
        ])
        controls_layout.addWidget(stop_btn)

        layout.addRow("Controls:", controls_layout)

        self.properties_layout.addWidget(group)

    def create_timer_group(self):
        """Create Timer-specific properties"""
        group = QGroupBox("Timer")
        layout = QFormLayout(group)

        # Wait time
        wait_time = self.current_node.get("wait_time", 1.0)
        wait_spin = QDoubleSpinBox()
        wait_spin.setRange(0.01, 3600.0)  # 1 centisecond to 1 hour
        wait_spin.setSingleStep(0.1)
        wait_spin.setSuffix(" sec")
        wait_spin.setValue(wait_time)
        wait_spin.valueChanged.connect(lambda v: self.update_property("wait_time", v))
        layout.addRow("Wait Time:", wait_spin)
        self.property_widgets["wait_time"] = wait_spin

        # One shot
        one_shot = self.current_node.get("one_shot", True)
        one_shot_check = QCheckBox()
        one_shot_check.setChecked(one_shot)
        one_shot_check.toggled.connect(lambda v: self.update_property("one_shot", v))
        layout.addRow("One Shot:", one_shot_check)
        self.property_widgets["one_shot"] = one_shot_check

        # Autostart
        autostart = self.current_node.get("autostart", False)
        autostart_check = QCheckBox()
        autostart_check.setChecked(autostart)
        autostart_check.toggled.connect(lambda v: self.update_property("autostart", v))
        layout.addRow("Autostart:", autostart_check)
        self.property_widgets["autostart"] = autostart_check

        # Paused
        paused = self.current_node.get("paused", False)
        paused_check = QCheckBox()
        paused_check.setChecked(paused)
        paused_check.toggled.connect(lambda v: self.update_property("paused", v))
        layout.addRow("Paused:", paused_check)
        self.property_widgets["paused"] = paused_check

        # Read-only properties
        time_left = self.current_node.get("_time_left", 0.0)
        time_left_label = QLabel(f"{time_left:.2f} sec")
        time_left_label.setStyleSheet("color: #b0b0b0;")
        layout.addRow("Time Left:", time_left_label)

        is_running = self.current_node.get("_is_running", False)
        running_label = QLabel("Yes" if is_running else "No")
        running_label.setStyleSheet("color: #b0b0b0;")
        layout.addRow("Running:", running_label)

        # Timer controls
        controls_layout = QHBoxLayout()

        start_btn = QPushButton("Start")
        start_btn.clicked.connect(lambda: self.update_property("_is_running", True))
        controls_layout.addWidget(start_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(lambda: [
            self.update_property("_is_running", False),
            self.update_property("_time_left", 0.0)
        ])
        controls_layout.addWidget(stop_btn)

        pause_btn = QPushButton("Pause")
        pause_btn.clicked.connect(lambda: self.update_property("paused", True))
        controls_layout.addWidget(pause_btn)

        layout.addRow("Controls:", controls_layout)

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

        # Enabled
        enabled = self.current_node.get("enabled", True)
        enabled_check = QCheckBox()
        enabled_check.setChecked(enabled)
        enabled_check.toggled.connect(lambda v: self.update_property("enabled", v))
        layout.addRow("Enabled:", enabled_check)
        self.property_widgets["enabled"] = enabled_check

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

        # Follow Target (Node Picker)
        follow_target = self.current_node.get("follow_target", "")
        follow_layout = QHBoxLayout()

        follow_edit = QLineEdit(str(follow_target))
        follow_edit.setPlaceholderText("Node path (e.g., Player)")
        follow_edit.textChanged.connect(lambda text: self.update_property("follow_target", text))
        follow_layout.addWidget(follow_edit)
        self.property_widgets["follow_target"] = follow_edit

        # Node picker button
        pick_node_btn = QPushButton("Pick")
        pick_node_btn.setMaximumWidth(50)
        pick_node_btn.clicked.connect(self.pick_follow_target_node)
        follow_layout.addWidget(pick_node_btn)

        layout.addRow("Follow Target:", follow_layout)

        # Follow Smoothing
        follow_smoothing = self.current_node.get("follow_smoothing", True)
        smoothing_check = QCheckBox()
        smoothing_check.setChecked(follow_smoothing)
        smoothing_check.toggled.connect(lambda v: self.update_property("follow_smoothing", v))
        layout.addRow("Follow Smoothing:", smoothing_check)
        self.property_widgets["follow_smoothing"] = smoothing_check

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

    def create_script_management_section(self):
        """Create enhanced script management section with multiple scripts support"""
        group = QGroupBox("Scripts")
        layout = QVBoxLayout(group)

        # Get current scripts (support multiple scripts)
        scripts = self.current_node.get("scripts", [])
        if not scripts:
            # Check for legacy single script
            script_path = self.current_node.get("script")
            if script_path:
                scripts = [{"path": script_path, "type": "main"}]

        # Scripts list
        scripts_layout = QVBoxLayout()

        for i, script_info in enumerate(scripts):
            script_path = script_info.get("path", "")
            script_type = script_info.get("type", "main")

            # Create script item
            script_item = QGroupBox(f"Script {i+1} ({script_type})")
            script_item_layout = QHBoxLayout(script_item)

            # Script path display
            path_label = QLabel(script_path if script_path else "No script")
            path_label.setStyleSheet("color: #b0b0b0; font-style: italic;")
            script_item_layout.addWidget(path_label)

            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, path=script_path: self.edit_script(path))
            script_item_layout.addWidget(edit_btn)

            # Make Local button
            local_btn = QPushButton("Make Local")
            local_btn.clicked.connect(lambda checked, path=script_path, idx=i: self.make_script_local(path, idx))
            script_item_layout.addWidget(local_btn)

            # Remove button (only for additional scripts)
            if i > 0 or len(scripts) > 1:
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, idx=i: self.remove_script(idx))
                script_item_layout.addWidget(remove_btn)

            scripts_layout.addWidget(script_item)

            # Add export variables from this script
            if script_path:
                self.create_script_export_group(script_path, i)

        layout.addLayout(scripts_layout)

        # Add script button
        add_script_layout = QHBoxLayout()
        add_script_btn = QPushButton("+ Add Script")
        add_script_btn.clicked.connect(self.add_new_script)
        add_script_layout.addWidget(add_script_btn)

        # Attach existing script button
        attach_script_btn = QPushButton("Attach Existing")
        attach_script_btn.clicked.connect(self.attach_existing_script)
        add_script_layout.addWidget(attach_script_btn)

        layout.addLayout(add_script_layout)

        self.properties_layout.addWidget(group)

    def create_script_export_group(self, script_path: str, script_index: int):
        """Create export variables group for a specific script, including parent class variables"""
        try:
            # Parse LSC file for export variables
            full_path = self.project.project_path / script_path
            if not full_path.exists():
                return

            # Get all export variables including from parent classes
            all_groups, all_ungrouped = self.get_all_export_variables(str(full_path))

            # Process grouped variables
            for export_group in all_groups:
                if not export_group.variables:
                    continue

                # Create group for this script's exports
                group_widget = QGroupBox(f"{export_group.name}")
                layout = QFormLayout(group_widget)

                # Special handling for Anchors group
                if export_group.name == "Anchors":
                    self.create_anchor_controls_for_export_group(layout, export_group.variables)
                else:
                    for var in export_group.variables:
                        self.create_export_variable_widget(layout, var)

                self.properties_layout.addWidget(group_widget)

            # Process ungrouped variables
            if all_ungrouped:
                group_widget = QGroupBox("Properties")
                layout = QFormLayout(group_widget)

                for var in all_ungrouped:
                    self.create_export_variable_widget(layout, var)

                self.properties_layout.addWidget(group_widget)

        except Exception as e:
            print(f"Error parsing script exports for {script_path}: {e}")

    def create_anchor_controls_for_export_group(self, layout: QFormLayout, anchor_variables: List):
        """Create anchor controls for export group with visual selector"""
        if not self.current_node:
            return

        # Extract anchor values from variables
        anchor_values = {}
        for var in anchor_variables:
            if var.name in ["anchor_left", "anchor_top", "anchor_right", "anchor_bottom"]:
                current_value = self.current_node.get(var.name, var.default_value) if self.current_node else var.default_value
                anchor_values[var.name] = float(current_value) if current_value is not None else 0.0

        # Get current anchor values
        anchor_left = anchor_values.get("anchor_left", 0.0)
        anchor_top = anchor_values.get("anchor_top", 0.0)
        anchor_right = anchor_values.get("anchor_right", 0.0)
        anchor_bottom = anchor_values.get("anchor_bottom", 0.0)

        # Visual anchor selector
        anchor_widget = QWidget()
        anchor_layout = QHBoxLayout(anchor_widget)
        anchor_layout.setContentsMargins(0, 0, 0, 0)

        # Visual anchor selector
        self.anchor_selector = AnchorSelectorWidget()
        self.anchor_selector.set_anchors(anchor_left, anchor_top, anchor_right, anchor_bottom)
        self.anchor_selector.anchor_changed.connect(self.update_anchor)
        anchor_layout.addWidget(self.anchor_selector)

        # Preset buttons
        preset_widget = AnchorPresetWidget()
        preset_widget.preset_selected.connect(self.apply_anchor_preset)
        anchor_layout.addWidget(preset_widget)

        layout.addRow("Anchors:", anchor_widget)

        # Individual anchor value controls
        anchor_values_widget = QWidget()
        anchor_values_layout = QGridLayout(anchor_values_widget)
        anchor_values_layout.setContentsMargins(0, 0, 0, 0)
        anchor_values_layout.setSpacing(5)

        # Left anchor
        anchor_values_layout.addWidget(QLabel("L:"), 0, 0)
        left_spin = QDoubleSpinBox()
        left_spin.setRange(0.0, 1.0)
        left_spin.setSingleStep(0.01)
        left_spin.setDecimals(3)
        left_spin.setValue(anchor_left)
        left_spin.valueChanged.connect(lambda v: self.update_anchor("left", v))
        anchor_values_layout.addWidget(left_spin, 0, 1)
        self.property_widgets["anchor_left"] = left_spin

        # Top anchor
        anchor_values_layout.addWidget(QLabel("T:"), 0, 2)
        top_spin = QDoubleSpinBox()
        top_spin.setRange(0.0, 1.0)
        top_spin.setSingleStep(0.01)
        top_spin.setDecimals(3)
        top_spin.setValue(anchor_top)
        top_spin.valueChanged.connect(lambda v: self.update_anchor("top", v))
        anchor_values_layout.addWidget(top_spin, 0, 3)
        self.property_widgets["anchor_top"] = top_spin

        # Right anchor
        anchor_values_layout.addWidget(QLabel("R:"), 1, 0)
        right_spin = QDoubleSpinBox()
        right_spin.setRange(0.0, 1.0)
        right_spin.setSingleStep(0.01)
        right_spin.setDecimals(3)
        right_spin.setValue(anchor_right)
        right_spin.valueChanged.connect(lambda v: self.update_anchor("right", v))
        anchor_values_layout.addWidget(right_spin, 1, 1)
        self.property_widgets["anchor_right"] = right_spin

        # Bottom anchor
        anchor_values_layout.addWidget(QLabel("B:"), 1, 2)
        bottom_spin = QDoubleSpinBox()
        bottom_spin.setRange(0.0, 1.0)
        bottom_spin.setSingleStep(0.01)
        bottom_spin.setDecimals(3)
        bottom_spin.setValue(anchor_bottom)
        bottom_spin.valueChanged.connect(lambda v: self.update_anchor("bottom", v))
        anchor_values_layout.addWidget(bottom_spin, 1, 3)
        self.property_widgets["anchor_bottom"] = bottom_spin

        layout.addRow("Anchor Values:", anchor_values_widget)

    def get_all_export_variables(self, script_path: str):
        """Get all export variables including from parent classes"""
        all_groups = []
        all_ungrouped = []
        processed_files = set()

        def process_script_file(file_path: str):
            if file_path in processed_files:
                return
            processed_files.add(file_path)

            try:
                # Parse current file
                groups, ungrouped_vars = self.export_parser.parse_script_file(file_path)
                all_groups.extend(groups)
                all_ungrouped.extend(ungrouped_vars)

                # Check for extends clause to find parent class
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for extends clause
                import re
                extends_match = re.search(r'extends\s+(\w+)', content)
                if extends_match:
                    parent_class = extends_match.group(1)

                    # Find parent class script file
                    parent_script_path = self.find_parent_script(parent_class)
                    if parent_script_path:
                        process_script_file(parent_script_path)

            except Exception as e:
                print(f"Error processing script file {file_path}: {e}")

        process_script_file(script_path)
        return all_groups, all_ungrouped

    def find_parent_script(self, class_name: str) -> Optional[str]:
        """Find the script file for a parent class"""
        try:
            # Check in project nodes directories
            nodes_dir = self.project.project_path / "nodes"
            for subdir in ["base", "node2d", "ui", "prefabs"]:
                script_path = nodes_dir / subdir / f"{class_name}.lsc"
                if script_path.exists():
                    return str(script_path)

            # Check in engine nodes directory (fallback)
            engine_root = Path(__file__).parent.parent
            engine_script_path = engine_root / "nodes" / f"{class_name}.lsc"
            if engine_script_path.exists():
                return str(engine_script_path)

        except Exception as e:
            print(f"Error finding parent script for {class_name}: {e}")

        return None

    def edit_script(self, script_path: str):
        """Open script in editor"""
        if script_path:
            # Emit signal to open script in editor
            # This would be connected to the main editor's script opening functionality
            print(f"Opening script for editing: {script_path}")
            # TODO: Implement script editor opening

    def make_script_local(self, script_path: str, script_index: int):
        """Make a local copy of the script"""
        if not script_path:
            return

        # Open save dialog
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("LSC Scripts (*.lsc)")
        file_dialog.setDefaultSuffix("lsc")

        # Set default name based on node and script type
        node_name = self.current_node.get("name", "Node")
        default_name = f"{node_name}_custom.lsc"
        file_dialog.selectFile(default_name)

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                new_path = selected_files[0]

                try:
                    # Copy the original script to new location
                    original_path = self.project.project_path / script_path
                    if original_path.exists():
                        import shutil
                        shutil.copy2(original_path, new_path)

                        # Update the script path in node
                        scripts = self.current_node.get("scripts", [])
                        if script_index < len(scripts):
                            scripts[script_index]["path"] = str(Path(new_path).relative_to(self.project.project_path))
                            self.update_property("scripts", scripts)

                        # Refresh the inspector
                        self.refresh_properties()

                        QMessageBox.information(self, "Success", f"Script copied to: {new_path}")
                    else:
                        QMessageBox.warning(self, "Error", f"Original script not found: {script_path}")

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to copy script: {e}")

    def add_new_script(self):
        """Add a new script to the node"""
        # Open file dialog to create new script
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("LSC Scripts (*.lsc)")
        file_dialog.setDefaultSuffix("lsc")

        node_name = self.current_node.get("name", "Node")
        default_name = f"{node_name}_script.lsc"
        file_dialog.selectFile(default_name)

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                new_script_path = selected_files[0]

                try:
                    # Create basic script template
                    script_template = f"""# Custom script for {node_name}
# Generated by Lupine Engine

extends {self.current_node.get("type", "Node")}

# Export variables
export_group("Custom Properties")
export var custom_property: String = "default_value"

# Called when the node enters the scene tree
func _ready():
    pass

# Called every frame
func _process(delta: float):
    pass
"""

                    with open(new_script_path, 'w', encoding='utf-8') as f:
                        f.write(script_template)

                    # Add to node's scripts
                    scripts = self.current_node.get("scripts", [])
                    relative_path = str(Path(new_script_path).relative_to(self.project.project_path))
                    scripts.append({"path": relative_path, "type": "custom"})
                    self.update_property("scripts", scripts)

                    # Refresh the inspector
                    self.refresh_properties()

                    QMessageBox.information(self, "Success", f"New script created: {new_script_path}")

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create script: {e}")

    def attach_existing_script(self):
        """Attach an existing script to the node"""
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        file_dialog.setNameFilter("LSC Scripts (*.lsc)")

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                script_path = selected_files[0]

                try:
                    # Add to node's scripts
                    scripts = self.current_node.get("scripts", [])
                    relative_path = str(Path(script_path).relative_to(self.project.project_path))
                    scripts.append({"path": relative_path, "type": "attached"})
                    self.update_property("scripts", scripts)

                    # Refresh the inspector
                    self.refresh_properties()

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to attach script: {e}")

    def remove_script(self, script_index: int):
        """Remove a script from the node"""
        scripts = self.current_node.get("scripts", [])
        if 0 <= script_index < len(scripts):
            removed_script = scripts.pop(script_index)
            self.update_property("scripts", scripts)

            # Refresh the inspector
            self.refresh_properties()

            QMessageBox.information(self, "Script Removed", f"Removed script: {removed_script.get('path', 'Unknown')}")

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

    def create_export_variable_widget(self, layout: QFormLayout, var: ExportVariable):
        """Create widget for an export variable"""
        widget_key = f"export_{var.name}"

        # Get current value from node or use default
        current_value = self.current_node.get(var.name, var.default_value) if self.current_node else var.default_value

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

        elif var.type == 'Color':
            widget = QWidget()
            widget_layout = QHBoxLayout(widget)
            widget_layout.setContentsMargins(0, 0, 0, 0)

            value = current_value if isinstance(current_value, list) else [1.0, 1.0, 1.0, 1.0]

            # R, G, B, A spinboxes
            for i, component in enumerate(['R', 'G', 'B', 'A']):
                label = QLabel(component)
                label.setMinimumWidth(15)
                widget_layout.addWidget(label)

                spin = QDoubleSpinBox()
                spin.setRange(0.0, 1.0)
                spin.setSingleStep(0.01)
                spin.setDecimals(3)
                spin.setValue(value[i] if i < len(value) else (1.0 if i == 3 else 0.0))
                spin.valueChanged.connect(lambda v, idx=i: self.update_color_component(var.name, idx, v))
                widget_layout.addWidget(spin)
                self.property_widgets[f"{widget_key}_{component.lower()}"] = spin

        elif var.type == 'path':
            # Special path type with file browser
            widget = QWidget()
            widget_layout = QHBoxLayout(widget)
            widget_layout.setContentsMargins(0, 0, 0, 0)

            path_edit = QLineEdit()
            path_edit.setText(str(current_value) if current_value is not None else "")
            path_edit.textChanged.connect(lambda text: self.update_property(var.name, text))
            widget_layout.addWidget(path_edit)

            browse_btn = QPushButton("Browse")
            browse_btn.clicked.connect(lambda: self.browse_path_for_variable(var.name, path_edit))
            widget_layout.addWidget(browse_btn)

            self.property_widgets[f"{widget_key}_edit"] = path_edit

        elif var.type == 'nodepath':
            # Special nodepath type with node browser
            widget = QWidget()
            widget_layout = QHBoxLayout(widget)
            widget_layout.setContentsMargins(0, 0, 0, 0)

            nodepath_edit = QLineEdit()
            nodepath_edit.setText(str(current_value) if current_value is not None else "")
            nodepath_edit.textChanged.connect(lambda text: self.update_property(var.name, text))
            widget_layout.addWidget(nodepath_edit)

            pick_btn = QPushButton("Pick Node")
            pick_btn.clicked.connect(lambda: self.pick_node_for_variable(var.name, nodepath_edit))
            widget_layout.addWidget(pick_btn)

            self.property_widgets[f"{widget_key}_edit"] = nodepath_edit

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

    def create_control_group(self):
        """Create Control node properties group"""
        group = QGroupBox("Control")
        layout = QFormLayout(group)

        # Position (UI nodes use 'position' instead of 'rect_position')
        position = self.current_node.get("position", [0.0, 0.0])
        pos_layout = QHBoxLayout()

        pos_x = QDoubleSpinBox()
        pos_x.setRange(-9999, 9999)
        pos_x.setValue(position[0])
        pos_x.valueChanged.connect(lambda v: self.update_position(0, v))
        pos_layout.addWidget(pos_x)
        self.property_widgets["position_x"] = pos_x

        pos_y = QDoubleSpinBox()
        pos_y.setRange(-9999, 9999)
        pos_y.setValue(position[1])
        pos_y.valueChanged.connect(lambda v: self.update_position(1, v))
        pos_layout.addWidget(pos_y)
        self.property_widgets["position_y"] = pos_y

        layout.addRow("Position:", pos_layout)

        # Rect Size
        rect_size = self.current_node.get("rect_size", [100.0, 100.0])
        size_layout = QHBoxLayout()

        size_x = QDoubleSpinBox()
        size_x.setRange(0, 9999)
        size_x.setValue(rect_size[0])
        size_x.valueChanged.connect(lambda v: self.update_rect_size(0, v))
        size_layout.addWidget(size_x)
        self.property_widgets["rect_size_x"] = size_x

        size_y = QDoubleSpinBox()
        size_y.setRange(0, 9999)
        size_y.setValue(rect_size[1])
        size_y.valueChanged.connect(lambda v: self.update_rect_size(1, v))
        size_layout.addWidget(size_y)
        self.property_widgets["rect_size_y"] = size_y

        layout.addRow("Rect Size:", size_layout)

        # Anchors Section
        self.create_anchor_controls(layout)

        # Z Layer
        z_layer = self.current_node.get("z_layer", 0)
        z_spin = QSpinBox()
        z_spin.setRange(-1000, 1000)
        z_spin.setValue(z_layer)
        z_spin.valueChanged.connect(lambda v: self.update_property("z_layer", v))
        layout.addRow("Z Layer:", z_spin)
        self.property_widgets["z_layer"] = z_spin

        self.properties_layout.addWidget(group)

    def create_anchor_controls(self, layout: QFormLayout):
        """Create anchor controls for UI nodes"""
        if not self.current_node:
            return

        # Get current anchor values
        anchor_left = self.current_node.get("anchor_left", 0.0)
        anchor_top = self.current_node.get("anchor_top", 0.0)
        anchor_right = self.current_node.get("anchor_right", 0.0)
        anchor_bottom = self.current_node.get("anchor_bottom", 0.0)

        # Visual anchor selector
        anchor_widget = QWidget()
        anchor_layout = QHBoxLayout(anchor_widget)
        anchor_layout.setContentsMargins(0, 0, 0, 0)

        # Visual anchor selector
        self.anchor_selector = AnchorSelectorWidget()
        self.anchor_selector.set_anchors(anchor_left, anchor_top, anchor_right, anchor_bottom)
        self.anchor_selector.anchor_changed.connect(self.update_anchor)
        anchor_layout.addWidget(self.anchor_selector)

        # Preset buttons
        preset_widget = AnchorPresetWidget()
        preset_widget.preset_selected.connect(self.apply_anchor_preset)
        anchor_layout.addWidget(preset_widget)

        layout.addRow("Anchors:", anchor_widget)

        # Individual anchor value controls
        anchor_values_widget = QWidget()
        anchor_values_layout = QGridLayout(anchor_values_widget)
        anchor_values_layout.setContentsMargins(0, 0, 0, 0)
        anchor_values_layout.setSpacing(5)

        # Left anchor
        anchor_values_layout.addWidget(QLabel("L:"), 0, 0)
        left_spin = QDoubleSpinBox()
        left_spin.setRange(0.0, 1.0)
        left_spin.setSingleStep(0.01)
        left_spin.setDecimals(3)
        left_spin.setValue(anchor_left)
        left_spin.valueChanged.connect(lambda v: self.update_anchor("left", v))
        anchor_values_layout.addWidget(left_spin, 0, 1)
        self.property_widgets["anchor_left"] = left_spin

        # Top anchor
        anchor_values_layout.addWidget(QLabel("T:"), 0, 2)
        top_spin = QDoubleSpinBox()
        top_spin.setRange(0.0, 1.0)
        top_spin.setSingleStep(0.01)
        top_spin.setDecimals(3)
        top_spin.setValue(anchor_top)
        top_spin.valueChanged.connect(lambda v: self.update_anchor("top", v))
        anchor_values_layout.addWidget(top_spin, 0, 3)
        self.property_widgets["anchor_top"] = top_spin

        # Right anchor
        anchor_values_layout.addWidget(QLabel("R:"), 1, 0)
        right_spin = QDoubleSpinBox()
        right_spin.setRange(0.0, 1.0)
        right_spin.setSingleStep(0.01)
        right_spin.setDecimals(3)
        right_spin.setValue(anchor_right)
        right_spin.valueChanged.connect(lambda v: self.update_anchor("right", v))
        anchor_values_layout.addWidget(right_spin, 1, 1)
        self.property_widgets["anchor_right"] = right_spin

        # Bottom anchor
        anchor_values_layout.addWidget(QLabel("B:"), 1, 2)
        bottom_spin = QDoubleSpinBox()
        bottom_spin.setRange(0.0, 1.0)
        bottom_spin.setSingleStep(0.01)
        bottom_spin.setDecimals(3)
        bottom_spin.setValue(anchor_bottom)
        bottom_spin.valueChanged.connect(lambda v: self.update_anchor("bottom", v))
        anchor_values_layout.addWidget(bottom_spin, 1, 3)
        self.property_widgets["anchor_bottom"] = bottom_spin

        layout.addRow("Anchor Values:", anchor_values_widget)

        # Margins (offset from anchors)
        margin_left = self.current_node.get("margin_left", 0.0)
        margin_top = self.current_node.get("margin_top", 0.0)
        margin_right = self.current_node.get("margin_right", 0.0)
        margin_bottom = self.current_node.get("margin_bottom", 0.0)

        margin_widget = QWidget()
        margin_layout = QGridLayout(margin_widget)
        margin_layout.setContentsMargins(0, 0, 0, 0)
        margin_layout.setSpacing(5)

        # Left margin
        margin_layout.addWidget(QLabel("L:"), 0, 0)
        margin_left_spin = QDoubleSpinBox()
        margin_left_spin.setRange(-9999.0, 9999.0)
        margin_left_spin.setValue(margin_left)
        margin_left_spin.valueChanged.connect(lambda v: self.update_property("margin_left", v))
        margin_layout.addWidget(margin_left_spin, 0, 1)
        self.property_widgets["margin_left"] = margin_left_spin

        # Top margin
        margin_layout.addWidget(QLabel("T:"), 0, 2)
        margin_top_spin = QDoubleSpinBox()
        margin_top_spin.setRange(-9999.0, 9999.0)
        margin_top_spin.setValue(margin_top)
        margin_top_spin.valueChanged.connect(lambda v: self.update_property("margin_top", v))
        margin_layout.addWidget(margin_top_spin, 0, 3)
        self.property_widgets["margin_top"] = margin_top_spin

        # Right margin
        margin_layout.addWidget(QLabel("R:"), 1, 0)
        margin_right_spin = QDoubleSpinBox()
        margin_right_spin.setRange(-9999.0, 9999.0)
        margin_right_spin.setValue(margin_right)
        margin_right_spin.valueChanged.connect(lambda v: self.update_property("margin_right", v))
        margin_layout.addWidget(margin_right_spin, 1, 1)
        self.property_widgets["margin_right"] = margin_right_spin

        # Bottom margin
        margin_layout.addWidget(QLabel("B:"), 1, 2)
        margin_bottom_spin = QDoubleSpinBox()
        margin_bottom_spin.setRange(-9999.0, 9999.0)
        margin_bottom_spin.setValue(margin_bottom)
        margin_bottom_spin.valueChanged.connect(lambda v: self.update_property("margin_bottom", v))
        margin_layout.addWidget(margin_bottom_spin, 1, 3)
        self.property_widgets["margin_bottom"] = margin_bottom_spin

        layout.addRow("Margins:", margin_widget)

    def update_anchor(self, side: str, value: float):
        """Update anchor value"""
        if self.current_node:
            property_name = f"anchor_{side}"
            self.current_node[property_name] = value

            # Update visual selector
            if hasattr(self, 'anchor_selector'):
                current_anchors = [
                    self.current_node.get("anchor_left", 0.0),
                    self.current_node.get("anchor_top", 0.0),
                    self.current_node.get("anchor_right", 0.0),
                    self.current_node.get("anchor_bottom", 0.0)
                ]
                self.anchor_selector.set_anchors(*current_anchors)

            # Update corresponding spinbox
            if f"anchor_{side}" in self.property_widgets:
                spinbox = self.property_widgets[f"anchor_{side}"]
                if spinbox.value() != value:
                    spinbox.blockSignals(True)
                    spinbox.setValue(value)
                    spinbox.blockSignals(False)

            # Emit property change signal
            node_id = self.current_node.get("name", "")
            self.property_changed.emit(node_id, property_name, value)

    def apply_anchor_preset(self, preset_name: str):
        """Apply anchor preset"""
        if not self.current_node:
            return

        # Define preset values
        presets = {
            "top_left": (0.0, 0.0, 0.0, 0.0),
            "top_center": (0.5, 0.0, 0.5, 0.0),
            "top_right": (1.0, 0.0, 1.0, 0.0),
            "center_left": (0.0, 0.5, 0.0, 0.5),
            "center": (0.5, 0.5, 0.5, 0.5),
            "center_right": (1.0, 0.5, 1.0, 0.5),
            "bottom_left": (0.0, 1.0, 0.0, 1.0),
            "bottom_center": (0.5, 1.0, 0.5, 1.0),
            "bottom_right": (1.0, 1.0, 1.0, 1.0),
            "left_wide": (0.0, 0.0, 0.0, 1.0),
            "top_wide": (0.0, 0.0, 1.0, 0.0),
            "right_wide": (1.0, 0.0, 1.0, 1.0),
            "bottom_wide": (0.0, 1.0, 1.0, 1.0),
            "vcenter_wide": (0.0, 0.5, 1.0, 0.5),
            "hcenter_wide": (0.5, 0.0, 0.5, 1.0),
            "full_rect": (0.0, 0.0, 1.0, 1.0)
        }

        if preset_name in presets:
            left, top, right, bottom = presets[preset_name]

            # Update all anchor values
            self.update_anchor("left", left)
            self.update_anchor("top", top)
            self.update_anchor("right", right)
            self.update_anchor("bottom", bottom)

    def create_panel_group(self):
        """Create Panel node properties group"""
        # First create Control properties
        self.create_control_group()

        # Then add Panel-specific properties
        group = QGroupBox("Panel")
        layout = QFormLayout(group)

        # Panel Color
        panel_color = self.current_node.get("panel_color", [0.2, 0.2, 0.2, 1.0])
        color_layout = QHBoxLayout()

        # R, G, B, A spinboxes
        for i, component in enumerate(['R', 'G', 'B', 'A']):
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 1.0)
            spin.setSingleStep(0.01)
            spin.setValue(panel_color[i])
            spin.valueChanged.connect(lambda v, idx=i: self.update_color_component("panel_color", idx, v))
            color_layout.addWidget(QLabel(component))
            color_layout.addWidget(spin)
            self.property_widgets[f"panel_color_{component.lower()}"] = spin

        layout.addRow("Panel Color:", color_layout)

        # Corner Radius
        corner_radius = self.current_node.get("corner_radius", 0.0)
        radius_spin = QDoubleSpinBox()
        radius_spin.setRange(0.0, 100.0)
        radius_spin.setValue(corner_radius)
        radius_spin.valueChanged.connect(lambda v: self.update_property("corner_radius", v))
        layout.addRow("Corner Radius:", radius_spin)
        self.property_widgets["corner_radius"] = radius_spin

        # Border Width
        border_width = self.current_node.get("border_width", 0.0)
        border_spin = QDoubleSpinBox()
        border_spin.setRange(0.0, 20.0)
        border_spin.setValue(border_width)
        border_spin.valueChanged.connect(lambda v: self.update_property("border_width", v))
        layout.addRow("Border Width:", border_spin)
        self.property_widgets["border_width"] = border_spin

        self.properties_layout.addWidget(group)

    def create_label_group(self):
        """Create Label node properties group"""
        # First create Control properties
        self.create_control_group()

        # Then add Label-specific properties
        group = QGroupBox("Label")
        layout = QFormLayout(group)

        # Text
        text = self.current_node.get("text", "Label")
        text_edit = QLineEdit(str(text))
        text_edit.textChanged.connect(lambda t: self.update_property("text", t))
        layout.addRow("Text:", text_edit)
        self.property_widgets["text"] = text_edit

        # Font Family
        font = self.current_node.get("font", "Arial")
        font_combo = QComboBox()
        font_combo.addItems([
            "Arial", "Times New Roman", "Courier New", "Helvetica",
            "Georgia", "Verdana", "Trebuchet MS", "Comic Sans MS",
            "Impact", "Lucida Console", "Tahoma", "Calibri"
        ])
        font_combo.setCurrentText(str(font) if font else "Arial")
        font_combo.currentTextChanged.connect(lambda t: self.update_property("font", t))
        layout.addRow("Font:", font_combo)
        self.property_widgets["font"] = font_combo

        # Font Size
        font_size = self.current_node.get("font_size", 14)
        size_spin = QSpinBox()
        size_spin.setRange(6, 72)
        size_spin.setValue(font_size)
        size_spin.valueChanged.connect(lambda v: self.update_property("font_size", v))
        layout.addRow("Font Size:", size_spin)
        self.property_widgets["font_size"] = size_spin

        # Horizontal Alignment
        h_align = self.current_node.get("h_align", "Left")
        h_align_combo = QComboBox()
        h_align_combo.addItems(["Left", "Center", "Right"])
        h_align_combo.setCurrentText(h_align)
        h_align_combo.currentTextChanged.connect(lambda t: self.update_property("h_align", t))
        layout.addRow("H Align:", h_align_combo)
        self.property_widgets["h_align"] = h_align_combo

        # Vertical Alignment
        v_align = self.current_node.get("v_align", "Top")
        v_align_combo = QComboBox()
        v_align_combo.addItems(["Top", "Center", "Bottom"])
        v_align_combo.setCurrentText(v_align)
        v_align_combo.currentTextChanged.connect(lambda t: self.update_property("v_align", t))
        layout.addRow("V Align:", v_align_combo)
        self.property_widgets["v_align"] = v_align_combo

        self.properties_layout.addWidget(group)

    def create_button_group(self):
        """Create Button node properties group"""
        # First create Control properties
        self.create_control_group()

        # Note: Button-specific properties are handled by LSC export variables
        # The Button.lsc script contains all the button-specific properties
        # like text, colors, style, and behavior settings

    def create_canvas_layer_group(self):
        """Create CanvasLayer node properties group"""
        group = QGroupBox("CanvasLayer")
        layout = QFormLayout(group)

        # Layer
        layer = self.current_node.get("layer", 1)
        layer_spin = QSpinBox()
        layer_spin.setRange(-100, 100)
        layer_spin.setValue(layer)
        layer_spin.valueChanged.connect(lambda v: self.update_property("layer", v))
        layout.addRow("Layer:", layer_spin)
        self.property_widgets["layer"] = layer_spin

        # Offset
        offset = self.current_node.get("offset", [0.0, 0.0])
        offset_layout = QHBoxLayout()

        offset_x = QDoubleSpinBox()
        offset_x.setRange(-9999, 9999)
        offset_x.setValue(offset[0])
        offset_x.valueChanged.connect(lambda v: self.update_vector2_component("offset", 0, v))
        offset_layout.addWidget(offset_x)
        self.property_widgets["offset_x"] = offset_x

        offset_y = QDoubleSpinBox()
        offset_y.setRange(-9999, 9999)
        offset_y.setValue(offset[1])
        offset_y.valueChanged.connect(lambda v: self.update_vector2_component("offset", 1, v))
        offset_layout.addWidget(offset_y)
        self.property_widgets["offset_y"] = offset_y

        layout.addRow("Offset:", offset_layout)

        # Follow Viewport
        follow_viewport = self.current_node.get("follow_viewport_enable", False)
        follow_check = QCheckBox()
        follow_check.setChecked(follow_viewport)
        follow_check.toggled.connect(lambda v: self.update_property("follow_viewport_enable", v))
        layout.addRow("Follow Viewport:", follow_check)
        self.property_widgets["follow_viewport_enable"] = follow_check

        self.properties_layout.addWidget(group)

    def update_rect_position(self, index: int, value: float):
        """Update rect position component (legacy method for compatibility)"""
        if self.current_node:
            rect_position = self.current_node.get("rect_position", [0.0, 0.0])
            rect_position[index] = value
            self.update_property("rect_position", rect_position)

    def update_rect_size(self, index: int, value: float):
        """Update rect size component"""
        if self.current_node:
            rect_size = self.current_node.get("rect_size", [100.0, 100.0])
            rect_size[index] = value
            self.update_property("rect_size", rect_size)

    def update_color_component(self, color_name: str, index: int, value: float):
        """Update color component"""
        if self.current_node:
            color = self.current_node.get(color_name, [1.0, 1.0, 1.0, 1.0])
            color[index] = value
            self.update_property(color_name, color)

    def update_vector2_component(self, vector_name: str, index: int, value: float):
        """Update Vector2 component"""
        if self.current_node:
            vector = self.current_node.get(vector_name, [0.0, 0.0])
            vector[index] = value
            self.update_property(vector_name, vector)

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

    def pick_follow_target_node(self):
        """Open a dialog to pick a node for camera follow target"""
        if not self.current_node:
            return

        try:
            # Get the main editor window to access the scene tree
            main_window = self.window()
            if not hasattr(main_window, 'scene_tree'):
                QMessageBox.warning(self, "Error", "Scene tree not available")
                return

            scene_tree = main_window.scene_tree

            # Create a simple dialog with available nodes
            dialog = QDialog(self)
            dialog.setWindowTitle("Select Follow Target")
            dialog.setModal(True)
            dialog.resize(300, 400)

            layout = QVBoxLayout(dialog)

            # Instructions
            label = QLabel("Select a node for the camera to follow:")
            layout.addWidget(label)

            # Node list
            node_list = QListWidget()

            # Populate with nodes from scene tree
            def add_nodes_to_list(item, path=""):
                try:
                    node_name = item.text(0)
                    node_path = f"{path}/{node_name}" if path else node_name
                    node_list.addItem(node_path)

                    for i in range(item.childCount()):
                        child = item.child(i)
                        add_nodes_to_list(child, node_path)
                except Exception as e:
                    print(f"Error adding node to list: {e}")

            try:
                if scene_tree.topLevelItemCount() > 0:
                    root_item = scene_tree.topLevelItem(0)
                    if root_item:
                        add_nodes_to_list(root_item)
                else:
                    # Add a message if no nodes are available
                    node_list.addItem("No nodes available")
            except Exception as e:
                print(f"Error populating node list: {e}")
                node_list.addItem("Error loading nodes")

            layout.addWidget(node_list)

            # Buttons
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            # Show dialog and handle result
            if dialog.exec() == QDialog.DialogCode.Accepted:
                current_item = node_list.currentItem()
                if current_item and current_item.text() not in ["No nodes available", "Error loading nodes"]:
                    selected_path = current_item.text()
                    # Update the follow_target property
                    self.update_property("follow_target", selected_path)
                    # Update the UI widget
                    if "follow_target" in self.property_widgets:
                        self.property_widgets["follow_target"].setText(selected_path)

        except Exception as e:
            print(f"Error in pick_follow_target_node: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open node picker: {e}")

    def update_offset(self, index: int, value: float):
        """Update offset component"""
        if self.current_node:
            offset = self.current_node.get("offset", [0.0, 0.0])
            offset[index] = value
            self.current_node["offset"] = offset
            self.property_changed.emit(self.current_node.get("name", ""), "offset", offset)

    def browse_texture(self, texture_edit: QLineEdit):
        """Browse for texture file"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tga)")
        file_dialog.setDirectory(str(self.project.project_path / "assets"))

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                # Convert to relative path from project root
                try:
                    relative_path = self.project.get_relative_path(file_path)
                    texture_edit.setText(str(relative_path))
                    self.update_property("texture", str(relative_path))
                except ValueError:
                    # File is outside project, use absolute path
                    texture_edit.setText(file_path)
                    self.update_property("texture", file_path)

    def browse_path_for_variable(self, var_name: str, path_edit: QLineEdit):
        """Browse for file path for a path export variable"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        # Set appropriate file filter based on variable name
        if var_name in ["stream", "audio_stream"]:
            file_dialog.setNameFilter("Audio Files (*.wav *.mp3 *.ogg *.flac)")
        elif var_name in ["texture", "normal_map"]:
            file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tga)")
        else:
            file_dialog.setNameFilter("All Files (*.*)")

        file_dialog.setDirectory(str(self.project.project_path / "assets"))

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                # Convert to relative path from project root
                try:
                    relative_path = self.project.get_relative_path(file_path)
                    path_edit.setText(str(relative_path))
                    self.update_property(var_name, str(relative_path))
                except ValueError:
                    # File is outside project, use absolute path
                    path_edit.setText(file_path)
                    self.update_property(var_name, file_path)

    def pick_node_for_variable(self, var_name: str, nodepath_edit: QLineEdit):
        """Pick a node for a nodepath export variable"""
        if not self.current_node:
            return

        try:
            # Get the main editor window to access the scene tree
            main_window = self.window()
            if not hasattr(main_window, 'scene_tree'):
                QMessageBox.warning(self, "Error", "Scene tree not available")
                return

            scene_tree = main_window.scene_tree

            # Create a simple dialog with available nodes
            dialog = QDialog(self)
            dialog.setWindowTitle("Select Node")
            dialog.setModal(True)
            dialog.resize(300, 400)

            layout = QVBoxLayout(dialog)

            # Instructions
            label = QLabel(f"Select a node for {var_name}:")
            layout.addWidget(label)

            # Node list
            node_list = QListWidget()

            # Populate with nodes from scene tree
            def add_nodes_to_list(item, path=""):
                try:
                    node_name = item.text(0)
                    node_path = f"{path}/{node_name}" if path else node_name
                    node_list.addItem(node_path)

                    for i in range(item.childCount()):
                        child = item.child(i)
                        add_nodes_to_list(child, node_path)
                except Exception as e:
                    print(f"Error adding node to list: {e}")

            try:
                if scene_tree.topLevelItemCount() > 0:
                    root_item = scene_tree.topLevelItem(0)
                    if root_item:
                        add_nodes_to_list(root_item)
                else:
                    # Add a message if no nodes are available
                    node_list.addItem("No nodes available")
            except Exception as e:
                print(f"Error populating node list: {e}")
                node_list.addItem("Error loading nodes")

            layout.addWidget(node_list)

            # Buttons
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            # Show dialog and handle result
            if dialog.exec() == QDialog.DialogCode.Accepted:
                current_item = node_list.currentItem()
                if current_item and current_item.text() not in ["No nodes available", "Error loading nodes"]:
                    selected_path = current_item.text()
                    # Update the property
                    nodepath_edit.setText(selected_path)
                    self.update_property(var_name, selected_path)

        except Exception as e:
            print(f"Error in pick_node_for_variable: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open node picker: {e}")
