"""
Level Builder for Lupine Engine
RPG Maker-style level editor with events and prefabs
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QCheckBox, QGroupBox, QFormLayout, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QMessageBox, QFileDialog, QScrollArea,
    QListWidget, QListWidgetItem, QDialog, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSlider,
    QColorDialog, QFrame, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QRect
from PyQt6.QtGui import (
    QFont, QIcon, QPixmap, QAction, QPainter, QPen, QBrush, 
    QColor, QMouseEvent, QPaintEvent, QWheelEvent, QKeyEvent
)
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import uuid

from core.project import LupineProject
from core.level.level_manager import LevelManager
from core.level.level_system import Level, LevelEvent, LevelLayer, EventTrigger, EventCondition
from core.prefabs.prefab_manager import PrefabManager
from .ui.visual_script_editor import VisualScriptEditor


class LevelCanvas(QWidget):
    """Canvas for level editing with grid and events"""
    
    event_selected = pyqtSignal(object)  # LevelEvent
    event_moved = pyqtSignal(object, tuple)  # LevelEvent, new_position
    event_added = pyqtSignal(object)  # LevelEvent
    canvas_clicked = pyqtSignal(int, int)  # grid_x, grid_y
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.level: Optional[Level] = None
        self.selected_event: Optional[LevelEvent] = None
        self.dragging_event: Optional[LevelEvent] = None
        self.drag_start_pos = QPoint()
        
        # View settings
        self.zoom_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Tool settings
        self.current_tool = "select"  # "select", "place_event", "erase"
        self.event_template: Optional[LevelEvent] = None
        
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
    
    def set_level(self, level: Level):
        """Set the level to edit"""
        self.level = level
        self.selected_event = None
        self.update()
    
    def set_tool(self, tool: str):
        """Set the current tool"""
        self.current_tool = tool
        self.setCursor(Qt.CursorShape.ArrowCursor if tool == "select" else Qt.CursorShape.CrossCursor)
    
    def set_event_template(self, event_template: LevelEvent):
        """Set the event template for placing"""
        self.event_template = event_template
    
    def paintEvent(self, event: QPaintEvent):
        """Paint the level canvas"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.level:
            painter.fillRect(self.rect(), QColor("#2b2b2b"))
            painter.setPen(QColor("white"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No level loaded")
            return
        
        # Fill background
        painter.fillRect(self.rect(), QColor(self.level.background_color))
        
        # Draw background image if any
        if self.level.background_image:
            # TODO: Load and draw background image
            pass
        
        # Draw grid
        if self.level.show_grid:
            self.draw_grid(painter)
        
        # Draw events from all visible layers
        for layer in self.level.layers:
            if layer.visible:
                self.draw_layer_events(painter, layer)
        
        # Draw selection
        if self.selected_event:
            self.draw_event_selection(painter, self.selected_event)
    
    def draw_grid(self, painter: QPainter):
        """Draw the grid"""
        if not self.level:
            return
        
        cell_size = int(self.level.cell_size * self.zoom_factor)
        
        painter.setPen(QPen(QColor(self.level.grid_color), 1))
        
        # Vertical lines
        for x in range(self.level.width + 1):
            screen_x = x * cell_size + self.offset_x
            painter.drawLine(screen_x, self.offset_y, 
                           screen_x, self.level.height * cell_size + self.offset_y)
        
        # Horizontal lines
        for y in range(self.level.height + 1):
            screen_y = y * cell_size + self.offset_y
            painter.drawLine(self.offset_x, screen_y,
                           self.level.width * cell_size + self.offset_x, screen_y)
    
    def draw_layer_events(self, painter: QPainter, layer: LevelLayer):
        """Draw events from a layer"""
        if not self.level:
            return
        
        cell_size = int(self.level.cell_size * self.zoom_factor)
        
        for event in layer.events:
            if not event.visible:
                continue
            
            ex, ey = event.position
            ew, eh = event.size
            
            # Calculate screen position
            screen_x = ex * cell_size + self.offset_x
            screen_y = ey * cell_size + self.offset_y
            screen_w = ew * cell_size
            screen_h = eh * cell_size
            
            # Draw event background
            if event.sprite_texture:
                # TODO: Load and draw sprite texture
                painter.fillRect(screen_x, screen_y, screen_w, screen_h, QColor("#4A90E2"))
            else:
                # Default event appearance
                color = self.get_event_color(event)
                painter.fillRect(screen_x, screen_y, screen_w, screen_h, color)
            
            # Draw event border
            painter.setPen(QPen(QColor("white"), 2))
            painter.drawRect(screen_x, screen_y, screen_w, screen_h)
            
            # Draw event name
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Arial", 8))
            text_rect = QRect(screen_x + 2, screen_y + 2, screen_w - 4, screen_h - 4)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, event.name)
    
    def get_event_color(self, event: LevelEvent) -> QColor:
        """Get color for an event based on its type"""
        trigger_colors = {
            EventTrigger.PLAYER_INTERACT: QColor("#4A90E2"),  # Blue
            EventTrigger.PLAYER_TOUCH: QColor("#50E3C2"),     # Cyan
            EventTrigger.AUTO_RUN: QColor("#F5A623"),         # Orange
            EventTrigger.PARALLEL: QColor("#D0021B"),         # Red
            EventTrigger.ON_ENTER: QColor("#7ED321"),         # Green
            EventTrigger.ON_EXIT: QColor("#9013FE"),          # Purple
            EventTrigger.TIMER: QColor("#BD10E0"),            # Magenta
            EventTrigger.CUSTOM: QColor("#B8E986")            # Light Green
        }
        return trigger_colors.get(event.trigger, QColor("#666666"))
    
    def draw_event_selection(self, painter: QPainter, event: LevelEvent):
        """Draw selection highlight for an event"""
        if not self.level:
            return
        
        cell_size = int(self.level.cell_size * self.zoom_factor)
        ex, ey = event.position
        ew, eh = event.size
        
        screen_x = ex * cell_size + self.offset_x
        screen_y = ey * cell_size + self.offset_y
        screen_w = ew * cell_size
        screen_h = eh * cell_size
        
        # Draw selection border
        painter.setPen(QPen(QColor("#FFD700"), 3))  # Gold
        painter.drawRect(screen_x - 1, screen_y - 1, screen_w + 2, screen_h + 2)
        
        # Draw resize handles
        handle_size = 6
        handles = [
            (screen_x - handle_size//2, screen_y - handle_size//2),  # Top-left
            (screen_x + screen_w - handle_size//2, screen_y - handle_size//2),  # Top-right
            (screen_x - handle_size//2, screen_y + screen_h - handle_size//2),  # Bottom-left
            (screen_x + screen_w - handle_size//2, screen_y + screen_h - handle_size//2)  # Bottom-right
        ]
        
        painter.fillRect(screen_x - handle_size//2, screen_y - handle_size//2, handle_size, handle_size, QColor("#FFD700"))
        for hx, hy in handles:
            painter.fillRect(hx, hy, handle_size, handle_size, QColor("#FFD700"))
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if not self.level:
            return
        
        grid_pos = self.screen_to_grid(event.pos())
        if not grid_pos:
            return
        
        grid_x, grid_y = grid_pos
        
        if event.button() == Qt.MouseButton.LeftButton:
            if self.current_tool == "select":
                # Select event at position
                events = self.level.get_events_at_position(grid_x, grid_y)
                if events:
                    self.selected_event = events[-1]  # Select topmost event
                    self.event_selected.emit(self.selected_event)
                    self.dragging_event = self.selected_event
                    self.drag_start_pos = event.pos()
                else:
                    self.selected_event = None
                    self.event_selected.emit(None)
                
                self.update()
            
            elif self.current_tool == "place_event" and self.event_template:
                # Place new event
                if self.level.is_position_free(grid_x, grid_y):
                    new_event = LevelEvent(
                        id=str(uuid.uuid4()),
                        name=self.event_template.name,
                        position=(grid_x, grid_y),
                        size=self.event_template.size,
                        trigger=self.event_template.trigger,
                        sprite_texture=self.event_template.sprite_texture,
                        raw_script=self.event_template.raw_script
                    )
                    
                    self.level.add_event(new_event)
                    self.event_added.emit(new_event)
                    self.update()
            
            elif self.current_tool == "erase":
                # Erase event at position
                events = self.level.get_events_at_position(grid_x, grid_y)
                if events:
                    event_to_remove = events[-1]
                    self.level.remove_event(event_to_remove.id)
                    if self.selected_event == event_to_remove:
                        self.selected_event = None
                        self.event_selected.emit(None)
                    self.update()
        
        self.canvas_clicked.emit(grid_x, grid_y)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move"""
        if self.dragging_event and event.buttons() & Qt.MouseButton.LeftButton:
            grid_pos = self.screen_to_grid(event.pos())
            if grid_pos:
                grid_x, grid_y = grid_pos
                old_pos = self.dragging_event.position
                
                # Check if new position is valid
                if (grid_x != old_pos[0] or grid_y != old_pos[1]) and \
                   self.level.is_position_free(grid_x, grid_y, self.dragging_event.id):
                    self.dragging_event.position = (grid_x, grid_y)
                    self.event_moved.emit(self.dragging_event, (grid_x, grid_y))
                    self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_event = None
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom
            delta = event.angleDelta().y()
            zoom_in = delta > 0
            
            old_zoom = self.zoom_factor
            if zoom_in:
                self.zoom_factor = min(3.0, self.zoom_factor * 1.2)
            else:
                self.zoom_factor = max(0.3, self.zoom_factor / 1.2)
            
            # Adjust offset to zoom towards mouse position
            mouse_pos = event.position()
            zoom_ratio = self.zoom_factor / old_zoom
            self.offset_x = mouse_pos.x() - (mouse_pos.x() - self.offset_x) * zoom_ratio
            self.offset_y = mouse_pos.y() - (mouse_pos.y() - self.offset_y) * zoom_ratio
            
            self.update()
        else:
            # Pan
            delta_x = event.angleDelta().x()
            delta_y = event.angleDelta().y()
            self.offset_x += delta_x * 0.5
            self.offset_y += delta_y * 0.5
            self.update()
    
    def screen_to_grid(self, screen_pos: QPoint) -> Optional[Tuple[int, int]]:
        """Convert screen position to grid coordinates"""
        if not self.level:
            return None
        
        cell_size = int(self.level.cell_size * self.zoom_factor)
        if cell_size <= 0:
            return None
        
        grid_x = int((screen_pos.x() - self.offset_x) // cell_size)
        grid_y = int((screen_pos.y() - self.offset_y) // cell_size)
        
        # Clamp to level bounds
        grid_x = max(0, min(self.level.width - 1, grid_x))
        grid_y = max(0, min(self.level.height - 1, grid_y))
        
        return (grid_x, grid_y)
    
    def grid_to_screen(self, grid_x: int, grid_y: int) -> QPoint:
        """Convert grid coordinates to screen position"""
        if not self.level:
            return QPoint(0, 0)
        
        cell_size = int(self.level.cell_size * self.zoom_factor)
        screen_x = grid_x * cell_size + self.offset_x
        screen_y = grid_y * cell_size + self.offset_y
        
        return QPoint(screen_x, screen_y)
    
    def center_on_event(self, event: LevelEvent):
        """Center the view on an event"""
        if not self.level:
            return
        
        ex, ey = event.position
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        cell_size = int(self.level.cell_size * self.zoom_factor)
        self.offset_x = center_x - (ex + 0.5) * cell_size
        self.offset_y = center_y - (ey + 0.5) * cell_size
        
        self.update()
    
    def fit_level_in_view(self):
        """Fit the entire level in the view"""
        if not self.level:
            return
        
        # Calculate zoom to fit level
        margin = 50
        available_width = self.width() - 2 * margin
        available_height = self.height() - 2 * margin
        
        zoom_x = available_width / (self.level.width * self.level.cell_size)
        zoom_y = available_height / (self.level.height * self.level.cell_size)
        
        self.zoom_factor = min(zoom_x, zoom_y, 3.0)
        
        # Center the level
        level_width = self.level.width * self.level.cell_size * self.zoom_factor
        level_height = self.level.height * self.level.cell_size * self.zoom_factor
        
        self.offset_x = (self.width() - level_width) // 2
        self.offset_y = (self.height() - level_height) // 2
        
        self.update()


class LevelBuilderWindow(QMainWindow):
    """Main Level Builder window"""

    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.level_manager = LevelManager(str(project.project_path))
        self.prefab_manager = PrefabManager(str(project.project_path))
        self.current_level: Optional[Level] = None
        self.current_event: Optional[LevelEvent] = None

        self.setWindowTitle("Level Builder - Lupine Engine")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        self.setup_ui()
        self.setup_menus()
        self.setup_toolbars()
        self.load_level_list()

    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel - Level list and tools
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Center - Level canvas
        self.canvas = LevelCanvas()
        self.canvas.event_selected.connect(self.on_event_selected)
        self.canvas.event_moved.connect(self.on_event_moved)
        self.canvas.event_added.connect(self.on_event_added)
        self.canvas.canvas_clicked.connect(self.on_canvas_clicked)
        splitter.addWidget(self.canvas)

        # Right panel - Properties and layers
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([300, 800, 400])

    def create_left_panel(self) -> QWidget:
        """Create the left panel with level list and tools"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Level list section
        level_group = QGroupBox("Levels")
        level_layout = QVBoxLayout(level_group)

        # Level list header
        header_layout = QHBoxLayout()

        level_title = QLabel("Levels")
        level_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_layout.addWidget(level_title)

        header_layout.addStretch()

        new_level_btn = QPushButton("New")
        new_level_btn.clicked.connect(self.new_level)
        header_layout.addWidget(new_level_btn)

        level_layout.addLayout(header_layout)

        # Level list
        self.level_list = QListWidget()
        self.level_list.itemClicked.connect(self.on_level_selected)
        level_layout.addWidget(self.level_list)

        # Level buttons
        level_buttons = QHBoxLayout()

        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.clicked.connect(self.duplicate_level)
        level_buttons.addWidget(duplicate_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_level)
        level_buttons.addWidget(delete_btn)

        level_layout.addLayout(level_buttons)

        layout.addWidget(level_group)

        # Tools section
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout(tools_group)

        # Tool buttons
        self.tool_buttons = {}

        select_btn = QPushButton("Select")
        select_btn.setCheckable(True)
        select_btn.setChecked(True)
        select_btn.clicked.connect(lambda: self.set_tool("select"))
        self.tool_buttons["select"] = select_btn
        tools_layout.addWidget(select_btn)

        place_btn = QPushButton("Place Event")
        place_btn.setCheckable(True)
        place_btn.clicked.connect(lambda: self.set_tool("place_event"))
        self.tool_buttons["place_event"] = place_btn
        tools_layout.addWidget(place_btn)

        erase_btn = QPushButton("Erase")
        erase_btn.setCheckable(True)
        erase_btn.clicked.connect(lambda: self.set_tool("erase"))
        self.tool_buttons["erase"] = erase_btn
        tools_layout.addWidget(erase_btn)

        layout.addWidget(tools_group)

        # Event templates section
        templates_group = QGroupBox("Event Templates")
        templates_layout = QVBoxLayout(templates_group)

        # Template list
        self.template_list = QListWidget()
        self.template_list.itemClicked.connect(self.on_template_selected)
        templates_layout.addWidget(self.template_list)

        # Template buttons
        template_buttons = QHBoxLayout()

        new_template_btn = QPushButton("New Template")
        new_template_btn.clicked.connect(self.create_event_template)
        template_buttons.addWidget(new_template_btn)

        templates_layout.addLayout(template_buttons)

        layout.addWidget(templates_group)

        # Load event templates
        self.load_event_templates()

        layout.addStretch()

        return panel

    def create_right_panel(self) -> QWidget:
        """Create the right panel with properties and layers"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Tab widget for different panels
        self.right_tabs = QTabWidget()
        layout.addWidget(self.right_tabs)

        # Event properties tab
        self.event_properties_tab = self.create_event_properties_tab()
        self.right_tabs.addTab(self.event_properties_tab, "Event")

        # Level properties tab
        self.level_properties_tab = self.create_level_properties_tab()
        self.right_tabs.addTab(self.level_properties_tab, "Level")

        # Layers tab
        self.layers_tab = self.create_layers_tab()
        self.right_tabs.addTab(self.layers_tab, "Layers")

        # Visual script tab
        self.visual_script_tab = VisualScriptEditor(self.prefab_manager)
        self.visual_script_tab.script_changed.connect(self.on_visual_script_changed)
        self.right_tabs.addTab(self.visual_script_tab, "Visual Script")

        return panel

    def create_event_properties_tab(self) -> QWidget:
        """Create the event properties tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Event info
        info_group = QGroupBox("Event Info")
        info_layout = QFormLayout(info_group)

        self.event_name_input = QLineEdit()
        self.event_name_input.textChanged.connect(self.on_event_property_changed)
        info_layout.addRow("Name:", self.event_name_input)

        self.event_position_label = QLabel("(0, 0)")
        info_layout.addRow("Position:", self.event_position_label)

        self.event_size_x = QSpinBox()
        self.event_size_x.setRange(1, 10)
        self.event_size_x.setValue(1)
        self.event_size_x.valueChanged.connect(self.on_event_property_changed)

        self.event_size_y = QSpinBox()
        self.event_size_y.setRange(1, 10)
        self.event_size_y.setValue(1)
        self.event_size_y.valueChanged.connect(self.on_event_property_changed)

        size_layout = QHBoxLayout()
        size_layout.addWidget(self.event_size_x)
        size_layout.addWidget(QLabel("x"))
        size_layout.addWidget(self.event_size_y)
        info_layout.addRow("Size:", size_layout)

        layout.addWidget(info_group)

        # Trigger settings
        trigger_group = QGroupBox("Trigger")
        trigger_layout = QFormLayout(trigger_group)

        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems([t.value for t in EventTrigger])
        self.trigger_combo.currentTextChanged.connect(self.on_event_property_changed)
        trigger_layout.addRow("Type:", self.trigger_combo)

        layout.addWidget(trigger_group)

        # Appearance settings
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        self.sprite_input = QLineEdit()
        self.sprite_input.textChanged.connect(self.on_event_property_changed)
        appearance_layout.addRow("Sprite:", self.sprite_input)

        sprite_btn = QPushButton("Browse...")
        sprite_btn.clicked.connect(self.browse_sprite)
        appearance_layout.addRow("", sprite_btn)

        self.visible_check = QCheckBox()
        self.visible_check.setChecked(True)
        self.visible_check.toggled.connect(self.on_event_property_changed)
        appearance_layout.addRow("Visible:", self.visible_check)

        self.through_check = QCheckBox()
        self.through_check.toggled.connect(self.on_event_property_changed)
        appearance_layout.addRow("Through:", self.through_check)

        layout.addWidget(appearance_group)

        # Script section
        script_group = QGroupBox("Script")
        script_layout = QVBoxLayout(script_group)

        self.script_editor = QTextEdit()
        self.script_editor.setFont(QFont("Consolas", 10))
        self.script_editor.setMaximumHeight(200)
        self.script_editor.textChanged.connect(self.on_script_changed)
        script_layout.addWidget(self.script_editor)

        layout.addWidget(script_group)

        layout.addStretch()

        return widget

    def create_level_properties_tab(self) -> QWidget:
        """Create the level properties tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Level info
        info_group = QGroupBox("Level Info")
        info_layout = QFormLayout(info_group)

        self.level_name_input = QLineEdit()
        self.level_name_input.textChanged.connect(self.on_level_property_changed)
        info_layout.addRow("Name:", self.level_name_input)

        self.level_description_input = QTextEdit()
        self.level_description_input.setMaximumHeight(60)
        self.level_description_input.textChanged.connect(self.on_level_property_changed)
        info_layout.addRow("Description:", self.level_description_input)

        layout.addWidget(info_group)

        # Dimensions
        dimensions_group = QGroupBox("Dimensions")
        dimensions_layout = QFormLayout(dimensions_group)

        self.level_width_input = QSpinBox()
        self.level_width_input.setRange(1, 100)
        self.level_width_input.setValue(20)
        self.level_width_input.valueChanged.connect(self.on_level_property_changed)
        dimensions_layout.addRow("Width:", self.level_width_input)

        self.level_height_input = QSpinBox()
        self.level_height_input.setRange(1, 100)
        self.level_height_input.setValue(15)
        self.level_height_input.valueChanged.connect(self.on_level_property_changed)
        dimensions_layout.addRow("Height:", self.level_height_input)

        self.cell_size_input = QSpinBox()
        self.cell_size_input.setRange(16, 128)
        self.cell_size_input.setValue(32)
        self.cell_size_input.valueChanged.connect(self.on_level_property_changed)
        dimensions_layout.addRow("Cell Size:", self.cell_size_input)

        layout.addWidget(dimensions_group)

        # Background
        background_group = QGroupBox("Background")
        background_layout = QFormLayout(background_group)

        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setStyleSheet("background-color: #2b2b2b")
        self.bg_color_btn.clicked.connect(self.choose_background_color)
        background_layout.addRow("Color:", self.bg_color_btn)

        self.bg_image_input = QLineEdit()
        self.bg_image_input.textChanged.connect(self.on_level_property_changed)
        background_layout.addRow("Image:", self.bg_image_input)

        bg_image_btn = QPushButton("Browse...")
        bg_image_btn.clicked.connect(self.browse_background_image)
        background_layout.addRow("", bg_image_btn)

        layout.addWidget(background_group)

        # Audio
        audio_group = QGroupBox("Audio")
        audio_layout = QFormLayout(audio_group)

        self.bg_music_input = QLineEdit()
        self.bg_music_input.textChanged.connect(self.on_level_property_changed)
        audio_layout.addRow("Music:", self.bg_music_input)

        bg_music_btn = QPushButton("Browse...")
        bg_music_btn.clicked.connect(self.browse_background_music)
        audio_layout.addRow("", bg_music_btn)

        layout.addWidget(audio_group)

        layout.addStretch()

        return widget

    def create_layers_tab(self) -> QWidget:
        """Create the layers tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Layers")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        add_layer_btn = QPushButton("Add Layer")
        add_layer_btn.clicked.connect(self.add_layer)
        header_layout.addWidget(add_layer_btn)

        layout.addLayout(header_layout)

        # Layers list
        self.layers_list = QListWidget()
        self.layers_list.itemClicked.connect(self.on_layer_selected)
        layout.addWidget(self.layers_list)

        # Layer buttons
        layer_buttons = QHBoxLayout()

        remove_layer_btn = QPushButton("Remove")
        remove_layer_btn.clicked.connect(self.remove_layer)
        layer_buttons.addWidget(remove_layer_btn)

        move_up_btn = QPushButton("Move Up")
        move_up_btn.clicked.connect(self.move_layer_up)
        layer_buttons.addWidget(move_up_btn)

        move_down_btn = QPushButton("Move Down")
        move_down_btn.clicked.connect(self.move_layer_down)
        layer_buttons.addWidget(move_down_btn)

        layout.addLayout(layer_buttons)

        return widget

    def setup_menus(self):
        """Setup the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Level", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_level)
        file_menu.addAction(new_action)

        save_action = QAction("Save Level", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_level)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        import_action = QAction("Import Level", self)
        import_action.triggered.connect(self.import_level)
        file_menu.addAction(import_action)

        export_action = QAction("Export Level", self)
        export_action.triggered.connect(self.export_level)
        file_menu.addAction(export_action)

        export_scene_action = QAction("Export to Scene", self)
        export_scene_action.triggered.connect(self.export_level_to_scene)
        file_menu.addAction(export_scene_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        duplicate_action = QAction("Duplicate Level", self)
        duplicate_action.setShortcut("Ctrl+D")
        duplicate_action.triggered.connect(self.duplicate_level)
        edit_menu.addAction(duplicate_action)

        delete_action = QAction("Delete Level", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_level)
        edit_menu.addAction(delete_action)

        # View menu
        view_menu = menubar.addMenu("View")

        fit_action = QAction("Fit Level in View", self)
        fit_action.setShortcut("F")
        fit_action.triggered.connect(self.fit_level_in_view)
        view_menu.addAction(fit_action)

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        # Visual Script Editor
        visual_script_action = QAction("Visual Script Editor", self)
        visual_script_action.triggered.connect(self.open_visual_script_editor)
        tools_menu.addAction(visual_script_action)

    def setup_toolbars(self):
        """Setup toolbars"""
        # Main toolbar
        main_toolbar = self.addToolBar("Main")

        # Tool actions
        select_action = QAction("Select", self)
        select_action.setCheckable(True)
        select_action.setChecked(True)
        select_action.triggered.connect(lambda: self.set_tool("select"))
        main_toolbar.addAction(select_action)

        place_action = QAction("Place Event", self)
        place_action.setCheckable(True)
        place_action.triggered.connect(lambda: self.set_tool("place_event"))
        main_toolbar.addAction(place_action)

        erase_action = QAction("Erase", self)
        erase_action.setCheckable(True)
        erase_action.triggered.connect(lambda: self.set_tool("erase"))
        main_toolbar.addAction(erase_action)

        main_toolbar.addSeparator()

        # Save action
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_level)
        main_toolbar.addAction(save_action)

    def load_level_list(self):
        """Load the list of levels"""
        self.level_list.clear()

        for level in self.level_manager.levels.values():
            item = QListWidgetItem(level.name)
            item.setData(Qt.ItemDataRole.UserRole, level.id)
            item.setToolTip(level.description)
            self.level_list.addItem(item)

    def load_event_templates(self):
        """Load event templates"""
        self.template_list.clear()

        # Create default templates
        templates = [
            ("NPC", EventTrigger.PLAYER_INTERACT),
            ("Touch Event", EventTrigger.PLAYER_TOUCH),
            ("Auto Event", EventTrigger.AUTO_RUN),
            ("Parallel Event", EventTrigger.PARALLEL),
            ("Trigger Zone", EventTrigger.PLAYER_TOUCH)
        ]

        for name, trigger in templates:
            template = self.level_manager.create_event_template(name, trigger)
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)

    def set_tool(self, tool: str):
        """Set the current tool"""
        # Update button states
        for tool_name, button in self.tool_buttons.items():
            button.setChecked(tool_name == tool)

        # Update canvas
        self.canvas.set_tool(tool)

    def new_level(self):
        """Create a new level"""
        name, ok = QInputDialog.getText(self, "New Level", "Level name:")
        if ok and name:
            try:
                level = self.level_manager.create_level(name)
                self.load_level_list()
                self.load_level(level)
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def duplicate_level(self):
        """Duplicate the selected level"""
        if not self.current_level:
            QMessageBox.information(self, "No Selection", "Please select a level to duplicate.")
            return

        name, ok = QInputDialog.getText(self, "Duplicate Level", "New level name:")
        if ok and name:
            try:
                new_level = self.level_manager.duplicate_level(self.current_level.id, name)
                if new_level:
                    self.load_level_list()
                    self.load_level(new_level)
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def delete_level(self):
        """Delete the selected level"""
        if not self.current_level:
            QMessageBox.information(self, "No Selection", "Please select a level to delete.")
            return

        reply = QMessageBox.question(
            self, "Delete Level",
            f"Are you sure you want to delete '{self.current_level.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.level_manager.remove_level(self.current_level.id)
            self.load_level_list()
            self.current_level = None
            self.canvas.level = None
            self.canvas.update()
            self.clear_properties()

    def save_level(self):
        """Save the current level"""
        if not self.current_level:
            return

        # Update level from UI
        self.update_level_from_ui()

        # Save to file
        self.level_manager.save_level(self.current_level)

        QMessageBox.information(self, "Saved", f"Level '{self.current_level.name}' saved successfully!")

    def import_level(self):
        """Import a level from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Level", "", "Level Files (*.level);;All Files (*)"
        )

        if file_path:
            level = self.level_manager.import_level(file_path)
            if level:
                self.load_level_list()
                self.load_level(level)
                QMessageBox.information(self, "Imported", f"Level '{level.name}' imported successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to import level!")

    def export_level(self):
        """Export the current level"""
        if not self.current_level:
            QMessageBox.information(self, "No Selection", "Please select a level to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Level", f"{self.current_level.name}.level",
            "Level Files (*.level);;All Files (*)"
        )

        if file_path:
            if self.level_manager.export_level(self.current_level.id, file_path):
                QMessageBox.information(self, "Exported", f"Level exported to '{file_path}'!")
            else:
                QMessageBox.warning(self, "Error", "Failed to export level!")

    def export_level_to_scene(self):
        """Export the current level to a scene file"""
        if not self.current_level:
            QMessageBox.information(self, "No Selection", "Please select a level to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Level to Scene", f"{self.current_level.name}.scene",
            "Scene Files (*.scene);;All Files (*)"
        )

        if file_path:
            try:
                self.current_level.export_to_scene(file_path)
                QMessageBox.information(self, "Exported", f"Level exported to scene file '{file_path}'!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export level to scene: {e}")

    def on_level_selected(self, item: QListWidgetItem):
        """Handle level selection"""
        level_id = item.data(Qt.ItemDataRole.UserRole)
        level = self.level_manager.get_level_by_id(level_id)
        if level:
            self.load_level(level)

    def load_level(self, level: Level):
        """Load a level into the editor"""
        self.current_level = level
        self.canvas.set_level(level)

        # Load level properties
        self.level_name_input.setText(level.name)
        self.level_description_input.setPlainText(level.description)
        self.level_width_input.setValue(level.width)
        self.level_height_input.setValue(level.height)
        self.cell_size_input.setValue(level.cell_size)
        self.bg_image_input.setText(level.background_image)
        self.bg_music_input.setText(level.background_music)

        # Update background color button
        self.bg_color_btn.setStyleSheet(f"background-color: {level.background_color}")

        # Load layers
        self.load_layers()

        # Fit level in view
        self.canvas.fit_level_in_view()

    def load_layers(self):
        """Load layers into the layers list"""
        self.layers_list.clear()

        if not self.current_level:
            return

        for layer in self.current_level.layers:
            item = QListWidgetItem(layer.name)
            item.setData(Qt.ItemDataRole.UserRole, layer.id)
            item.setCheckState(Qt.CheckState.Checked if layer.visible else Qt.CheckState.Unchecked)
            self.layers_list.addItem(item)

    def on_template_selected(self, item: QListWidgetItem):
        """Handle template selection"""
        template = item.data(Qt.ItemDataRole.UserRole)
        if template:
            self.canvas.set_event_template(template)
            self.set_tool("place_event")

    def create_event_template(self):
        """Create a new event template"""
        name, ok = QInputDialog.getText(self, "New Event Template", "Template name:")
        if ok and name:
            template = self.level_manager.create_event_template(name)
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)

    def on_event_selected(self, event: Optional[LevelEvent]):
        """Handle event selection"""
        self.current_event = event
        self.load_event_properties(event)
        self.right_tabs.setCurrentIndex(0)  # Switch to Event tab

    def load_event_properties(self, event: Optional[LevelEvent]):
        """Load event properties into the UI"""
        if not event:
            self.clear_event_properties()
            return

        self.event_name_input.setText(event.name)
        self.event_position_label.setText(f"({event.position[0]}, {event.position[1]})")
        self.event_size_x.setValue(event.size[0])
        self.event_size_y.setValue(event.size[1])
        self.trigger_combo.setCurrentText(event.trigger.value)
        self.sprite_input.setText(event.sprite_texture)
        self.visible_check.setChecked(event.visible)
        self.through_check.setChecked(event.through)
        self.script_editor.setPlainText(event.raw_script)

        # Load visual script if any
        if event.visual_script:
            self.visual_script_tab.load_script_data(event.visual_script)

    def clear_event_properties(self):
        """Clear event properties"""
        self.event_name_input.clear()
        self.event_position_label.setText("(0, 0)")
        self.event_size_x.setValue(1)
        self.event_size_y.setValue(1)
        self.trigger_combo.setCurrentIndex(0)
        self.sprite_input.clear()
        self.visible_check.setChecked(True)
        self.through_check.setChecked(False)
        self.script_editor.clear()

    def clear_properties(self):
        """Clear all properties"""
        self.clear_event_properties()
        self.level_name_input.clear()
        self.level_description_input.clear()
        self.level_width_input.setValue(20)
        self.level_height_input.setValue(15)
        self.cell_size_input.setValue(32)
        self.bg_image_input.clear()
        self.bg_music_input.clear()
        self.bg_color_btn.setStyleSheet("background-color: #2b2b2b")
        self.layers_list.clear()

    def on_event_property_changed(self):
        """Handle event property changes"""
        if not self.current_event:
            return

        self.current_event.name = self.event_name_input.text()
        self.current_event.size = (self.event_size_x.value(), self.event_size_y.value())
        self.current_event.trigger = EventTrigger(self.trigger_combo.currentText())
        self.current_event.sprite_texture = self.sprite_input.text()
        self.current_event.visible = self.visible_check.isChecked()
        self.current_event.through = self.through_check.isChecked()

        self.canvas.update()

    def on_level_property_changed(self):
        """Handle level property changes"""
        if not self.current_level:
            return

        self.current_level.name = self.level_name_input.text()
        self.current_level.description = self.level_description_input.toPlainText()
        self.current_level.width = self.level_width_input.value()
        self.current_level.height = self.level_height_input.value()
        self.current_level.cell_size = self.cell_size_input.value()
        self.current_level.background_image = self.bg_image_input.text()
        self.current_level.background_music = self.bg_music_input.text()

        self.canvas.update()

    def on_script_changed(self):
        """Handle script changes"""
        if self.current_event:
            self.current_event.raw_script = self.script_editor.toPlainText()

    def on_visual_script_changed(self):
        """Handle visual script changes"""
        if self.current_event:
            self.current_event.visual_script = self.visual_script_tab.get_script_data()

    def on_event_moved(self, event: LevelEvent, new_position: Tuple[int, int]):
        """Handle event movement"""
        if event == self.current_event:
            self.event_position_label.setText(f"({new_position[0]}, {new_position[1]})")

    def on_event_added(self, event: LevelEvent):
        """Handle event addition"""
        # Auto-select the new event
        self.on_event_selected(event)

    def on_canvas_clicked(self, grid_x: int, grid_y: int):
        """Handle canvas clicks"""
        # Update status or perform other actions
        pass

    def browse_sprite(self):
        """Browse for sprite texture"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Sprite", "", "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path:
            # Convert to relative path
            relative_path = self.project.get_relative_path(file_path)
            self.sprite_input.setText(relative_path)

    def browse_background_image(self):
        """Browse for background image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path:
            relative_path = self.project.get_relative_path(file_path)
            self.bg_image_input.setText(relative_path)

    def browse_background_music(self):
        """Browse for background music"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Music", "", "Audio Files (*.mp3 *.wav *.ogg);;All Files (*)"
        )
        if file_path:
            relative_path = self.project.get_relative_path(file_path)
            self.bg_music_input.setText(relative_path)

    def choose_background_color(self):
        """Choose background color"""
        if self.current_level:
            color = QColorDialog.getColor(QColor(self.current_level.background_color), self)
            if color.isValid():
                self.current_level.background_color = color.name()
                self.bg_color_btn.setStyleSheet(f"background-color: {color.name()}")
                self.canvas.update()

    def add_layer(self):
        """Add a new layer"""
        if not self.current_level:
            return

        name, ok = QInputDialog.getText(self, "Add Layer", "Layer name:")
        if ok and name:
            layer = self.current_level.add_layer(name)
            self.load_layers()

    def remove_layer(self):
        """Remove the selected layer"""
        current_item = self.layers_list.currentItem()
        if not current_item or not self.current_level:
            return

        layer_id = current_item.data(Qt.ItemDataRole.UserRole)
        if self.current_level.remove_layer(layer_id):
            self.load_layers()
            self.canvas.update()

    def move_layer_up(self):
        """Move layer up in the list"""
        # Implementation for layer reordering
        pass

    def move_layer_down(self):
        """Move layer down in the list"""
        # Implementation for layer reordering
        pass

    def on_layer_selected(self, item: QListWidgetItem):
        """Handle layer selection"""
        if self.current_level:
            layer_id = item.data(Qt.ItemDataRole.UserRole)
            self.current_level.active_layer_id = layer_id

    def fit_level_in_view(self):
        """Fit level in view"""
        self.canvas.fit_level_in_view()

    def zoom_in(self):
        """Zoom in"""
        self.canvas.zoom_factor = min(3.0, self.canvas.zoom_factor * 1.2)
        self.canvas.update()

    def zoom_out(self):
        """Zoom out"""
        self.canvas.zoom_factor = max(0.3, self.canvas.zoom_factor / 1.2)
        self.canvas.update()

    def update_level_from_ui(self):
        """Update the current level from UI values"""
        if not self.current_level:
            return

        # Level properties are updated in real-time via on_level_property_changed
        # This method can be used for final validation or batch updates
        pass

    def open_visual_script_editor(self):
        """Open the visual script editor popup"""
        from editor.ui.visual_script_popup import open_visual_script_popup

        # Determine target object
        target_object = None
        initial_script_path = None

        if self.current_event:
            target_object = self.current_event
            initial_script_path = getattr(self.current_event, 'visual_script_path', None)

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
            if target_object == self.current_event:
                self.load_event_properties(self.current_event)
