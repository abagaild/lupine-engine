"""
Tileset Editor for Lupine Engine
Comprehensive tileset creation and editing tool
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QLabel, QPushButton, QSpinBox, QLineEdit,
    QGroupBox, QFormLayout, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QTabWidget, QTextEdit,
    QCheckBox, QComboBox, QGridLayout, QFrame, QSlider,
    QDoubleSpinBox, QToolBar, QMenuBar, QMenu, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QPoint
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QBrush, QColor, QFont,
    QAction, QIcon, QKeySequence, QWheelEvent, QMouseEvent
)

from core.project import LupineProject
from core.tileset import TileSet, TileDefinition, get_tileset_manager


class TilesetCanvas(QWidget):
    """Canvas widget for displaying and editing tileset texture"""
    
    tile_selected = pyqtSignal(int)  # tile_id
    tile_modified = pyqtSignal(int)  # tile_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tileset = None
        self.texture_pixmap = None
        self.zoom = 1.0
        self.offset = QPoint(0, 0)
        self.selected_tile_id = -1
        self.grid_visible = True
        self.collision_visible = False
        
        # Mouse interaction
        self.dragging = False
        self.last_mouse_pos = QPoint()
        
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
    
    def set_tileset(self, tileset: TileSet):
        """Set the tileset to display"""
        self.tileset = tileset
        self.load_texture()
        self.update()
    
    def load_texture(self):
        """Load the texture for the tileset"""
        if not self.tileset or not self.tileset.texture_path:
            self.texture_pixmap = None
            return
        
        try:
            # Try to load the texture
            texture_path = Path(self.tileset.texture_path)
            if texture_path.exists():
                self.texture_pixmap = QPixmap(str(texture_path))
            else:
                self.texture_pixmap = None
                print(f"Texture not found: {texture_path}")
        except Exception as e:
            print(f"Error loading texture: {e}")
            self.texture_pixmap = None
    
    def paintEvent(self, event):
        """Paint the tileset canvas"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(64, 64, 64))
        
        if not self.tileset:
            painter.setPen(QColor(128, 128, 128))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No tileset loaded")
            return
        
        # Apply zoom and offset
        painter.scale(self.zoom, self.zoom)
        painter.translate(self.offset)
        
        # Draw texture if available
        if self.texture_pixmap:
            painter.drawPixmap(0, 0, self.texture_pixmap)
        else:
            # Draw placeholder
            painter.fillRect(0, 0, 512, 512, QColor(96, 96, 96))
            painter.setPen(QColor(160, 160, 160))
            painter.drawText(QRect(0, 0, 512, 512), Qt.AlignmentFlag.AlignCenter, 
                           f"Texture: {self.tileset.texture_path}\n(Not found)")
        
        # Draw grid if enabled
        if self.grid_visible:
            self.draw_grid(painter)
        
        # Draw tile selection
        if self.selected_tile_id >= 0:
            self.draw_tile_selection(painter)
        
        # Draw collision shapes if enabled
        if self.collision_visible:
            self.draw_collision_shapes(painter)
    
    def draw_grid(self, painter: QPainter):
        """Draw the tile grid"""
        if not self.tileset:
            return
        
        painter.setPen(QPen(QColor(255, 255, 255, 128), 1))
        
        tile_w, tile_h = self.tileset.tile_size
        margin_x, margin_y = self.tileset.margin
        spacing_x, spacing_y = self.tileset.spacing
        
        # Calculate grid bounds
        texture_w = self.texture_pixmap.width() if self.texture_pixmap else 512
        texture_h = self.texture_pixmap.height() if self.texture_pixmap else 512
        
        # Draw vertical lines
        x = margin_x
        while x < texture_w:
            painter.drawLine(x, 0, x, texture_h)
            x += tile_w + spacing_x
        
        # Draw horizontal lines
        y = margin_y
        while y < texture_h:
            painter.drawLine(0, y, texture_w, y)
            y += tile_h + spacing_y
    
    def draw_tile_selection(self, painter: QPainter):
        """Draw selection highlight for the selected tile"""
        tile_def = self.tileset.get_tile(self.selected_tile_id)
        if not tile_def:
            return
        
        rect = tile_def.texture_rect
        painter.setPen(QPen(QColor(255, 255, 0), 2))
        painter.setBrush(QBrush(QColor(255, 255, 0, 64)))
        painter.drawRect(rect[0], rect[1], rect[2], rect[3])
    
    def draw_collision_shapes(self, painter: QPainter):
        """Draw collision shapes for all tiles"""
        if not self.tileset:
            return
        
        painter.setPen(QPen(QColor(255, 0, 0, 180), 2))
        painter.setBrush(QBrush(QColor(255, 0, 0, 64)))
        
        for tile_def in self.tileset.tiles.values():
            tile_rect = tile_def.texture_rect
            tile_x, tile_y = tile_rect[0], tile_rect[1]
            
            for shape in tile_def.collision_shapes:
                if shape.get("type") == "rect":
                    # Rectangle collision shape
                    shape_rect = shape.get("rect", [0, 0, 32, 32])
                    painter.drawRect(
                        tile_x + shape_rect[0], tile_y + shape_rect[1],
                        shape_rect[2], shape_rect[3]
                    )
                elif shape.get("type") == "polygon":
                    # Polygon collision shape
                    points = shape.get("points", [])
                    if len(points) >= 3:
                        from PyQt6.QtGui import QPolygon
                        polygon = QPolygon()
                        for point in points:
                            polygon.append(QPoint(tile_x + point[0], tile_y + point[1]))
                        painter.drawPolygon(polygon)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert to tileset coordinates
            local_pos = self.map_to_tileset_coords(event.position().toPoint())
            tile_id = self.get_tile_at_position(local_pos)
            
            if tile_id >= 0:
                self.selected_tile_id = tile_id
                self.tile_selected.emit(tile_id)
                self.update()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.dragging = True
            self.last_mouse_pos = event.position().toPoint()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        if self.dragging:
            delta = event.position().toPoint() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.position().toPoint()
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.dragging = False
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom with mouse wheel"""
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.zoom = max(0.1, min(5.0, self.zoom * zoom_factor))
        self.update()
    
    def map_to_tileset_coords(self, screen_pos: QPoint) -> QPoint:
        """Convert screen coordinates to tileset coordinates"""
        return QPoint(
            int((screen_pos.x() / self.zoom) - self.offset.x()),
            int((screen_pos.y() / self.zoom) - self.offset.y())
        )
    
    def get_tile_at_position(self, pos: QPoint) -> int:
        """Get tile ID at the given position"""
        if not self.tileset:
            return -1

        tile_w, tile_h = self.tileset.tile_size
        margin_x, margin_y = self.tileset.margin
        spacing_x, spacing_y = self.tileset.spacing

        # Calculate tile grid position
        adjusted_x = pos.x() - margin_x
        adjusted_y = pos.y() - margin_y

        if adjusted_x < 0 or adjusted_y < 0:
            return -1

        tile_x = adjusted_x // (tile_w + spacing_x)
        tile_y = adjusted_y // (tile_h + spacing_y)

        # Check if we're actually within a tile (not in spacing)
        local_x = adjusted_x % (tile_w + spacing_x)
        local_y = adjusted_y % (tile_h + spacing_y)

        if local_x >= tile_w or local_y >= tile_h:
            return -1  # In spacing area

        # Find the actual tile at this grid position by checking existing tiles
        for tile_id, tile_def in self.tileset.tiles.items():
            tile_rect = tile_def.texture_rect
            tile_grid_x = (tile_rect[0] - margin_x) // (tile_w + spacing_x)
            tile_grid_y = (tile_rect[1] - margin_y) // (tile_h + spacing_y)

            if tile_grid_x == tile_x and tile_grid_y == tile_y:
                return tile_id

        return -1


class TilesetEditorWindow(QMainWindow):
    """Main tileset editor window"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.current_tileset = None
        self.current_file_path = None
        
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_status_bar()
        
        # Load default or create new tileset
        self.new_tileset()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Tileset Editor - Lupine Engine")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Tileset canvas
        self.canvas = TilesetCanvas()
        self.canvas.tile_selected.connect(self.on_tile_selected)
        splitter.addWidget(self.canvas)
        
        # Right panel - Properties and tools
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([700, 300])
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with properties and tools"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget for different tool sections
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Tileset properties tab
        tileset_tab = self.create_tileset_properties_tab()
        tabs.addTab(tileset_tab, "Tileset")
        
        # Tile properties tab
        tile_tab = self.create_tile_properties_tab()
        tabs.addTab(tile_tab, "Tile")
        
        # Collision editor tab
        collision_tab = self.create_collision_editor_tab()
        tabs.addTab(collision_tab, "Collision")
        
        # Tags tab
        tags_tab = self.create_tags_tab()
        tabs.addTab(tags_tab, "Tags")
        
        return panel

    def create_tileset_properties_tab(self) -> QWidget:
        """Create tileset properties tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tileset info group
        info_group = QGroupBox("Tileset Information")
        info_layout = QFormLayout(info_group)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.on_tileset_property_changed)
        info_layout.addRow("Name:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.textChanged.connect(self.on_tileset_property_changed)
        info_layout.addRow("Description:", self.description_edit)

        layout.addWidget(info_group)

        # Texture group
        texture_group = QGroupBox("Texture")
        texture_layout = QFormLayout(texture_group)

        texture_row = QHBoxLayout()
        self.texture_path_edit = QLineEdit()
        self.texture_path_edit.textChanged.connect(self.on_texture_changed)
        texture_row.addWidget(self.texture_path_edit)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_texture)
        texture_row.addWidget(browse_btn)

        texture_layout.addRow("Texture:", texture_row)

        layout.addWidget(texture_group)

        # Tile size group
        size_group = QGroupBox("Tile Configuration")
        size_layout = QFormLayout(size_group)

        # Tile size
        tile_size_row = QHBoxLayout()
        self.tile_width_spin = QSpinBox()
        self.tile_width_spin.setRange(1, 512)
        self.tile_width_spin.setValue(32)
        self.tile_width_spin.valueChanged.connect(self.on_tileset_property_changed)
        tile_size_row.addWidget(self.tile_width_spin)

        tile_size_row.addWidget(QLabel("x"))

        self.tile_height_spin = QSpinBox()
        self.tile_height_spin.setRange(1, 512)
        self.tile_height_spin.setValue(32)
        self.tile_height_spin.valueChanged.connect(self.on_tileset_property_changed)
        tile_size_row.addWidget(self.tile_height_spin)

        size_layout.addRow("Tile Size:", tile_size_row)

        # Margin
        margin_row = QHBoxLayout()
        self.margin_x_spin = QSpinBox()
        self.margin_x_spin.setRange(0, 100)
        self.margin_x_spin.valueChanged.connect(self.on_tileset_property_changed)
        margin_row.addWidget(self.margin_x_spin)

        margin_row.addWidget(QLabel("x"))

        self.margin_y_spin = QSpinBox()
        self.margin_y_spin.setRange(0, 100)
        self.margin_y_spin.valueChanged.connect(self.on_tileset_property_changed)
        margin_row.addWidget(self.margin_y_spin)

        size_layout.addRow("Margin:", margin_row)

        # Spacing
        spacing_row = QHBoxLayout()
        self.spacing_x_spin = QSpinBox()
        self.spacing_x_spin.setRange(0, 100)
        self.spacing_x_spin.valueChanged.connect(self.on_tileset_property_changed)
        spacing_row.addWidget(self.spacing_x_spin)

        spacing_row.addWidget(QLabel("x"))

        self.spacing_y_spin = QSpinBox()
        self.spacing_y_spin.setRange(0, 100)
        self.spacing_y_spin.valueChanged.connect(self.on_tileset_property_changed)
        spacing_row.addWidget(self.spacing_y_spin)

        size_layout.addRow("Spacing:", spacing_row)

        layout.addWidget(size_group)

        # Auto-generate button
        auto_gen_btn = QPushButton("Auto-Generate Tiles")
        auto_gen_btn.clicked.connect(self.auto_generate_tiles)
        layout.addWidget(auto_gen_btn)

        layout.addStretch()
        return widget

    def create_tile_properties_tab(self) -> QWidget:
        """Create tile properties tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Selected tile info
        self.tile_info_label = QLabel("No tile selected")
        self.tile_info_label.setStyleSheet("font-weight: bold; padding: 8px; background: #f0f0f0;")
        layout.addWidget(self.tile_info_label)

        # Tile properties group
        props_group = QGroupBox("Tile Properties")
        props_layout = QFormLayout(props_group)

        self.tile_name_edit = QLineEdit()
        self.tile_name_edit.textChanged.connect(self.on_tile_property_changed)
        props_layout.addRow("Name:", self.tile_name_edit)

        # Texture rect (read-only for now)
        self.texture_rect_label = QLabel("0, 0, 32, 32")
        props_layout.addRow("Texture Rect:", self.texture_rect_label)

        layout.addWidget(props_group)

        # Custom properties
        custom_group = QGroupBox("Custom Properties")
        custom_layout = QVBoxLayout(custom_group)

        # Add property button
        add_prop_btn = QPushButton("Add Property")
        add_prop_btn.clicked.connect(self.add_custom_property)
        custom_layout.addWidget(add_prop_btn)

        # Properties list
        self.custom_props_widget = QWidget()
        self.custom_props_layout = QVBoxLayout(self.custom_props_widget)
        custom_layout.addWidget(self.custom_props_widget)

        layout.addWidget(custom_group)

        layout.addStretch()
        return widget

    def create_collision_editor_tab(self) -> QWidget:
        """Create collision editor tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Collision shapes list
        shapes_group = QGroupBox("Collision Shapes")
        shapes_layout = QVBoxLayout(shapes_group)

        # Add shape buttons
        buttons_row = QHBoxLayout()

        add_rect_btn = QPushButton("Add Rectangle")
        add_rect_btn.clicked.connect(lambda: self.add_collision_shape("rect"))
        buttons_row.addWidget(add_rect_btn)

        add_poly_btn = QPushButton("Add Polygon")
        add_poly_btn.clicked.connect(lambda: self.add_collision_shape("polygon"))
        buttons_row.addWidget(add_poly_btn)

        shapes_layout.addLayout(buttons_row)

        # Shapes list
        self.collision_shapes_list = QListWidget()
        self.collision_shapes_list.itemSelectionChanged.connect(self.on_collision_shape_selected)
        shapes_layout.addWidget(self.collision_shapes_list)

        # Remove shape button
        remove_shape_btn = QPushButton("Remove Selected")
        remove_shape_btn.clicked.connect(self.remove_collision_shape)
        shapes_layout.addWidget(remove_shape_btn)

        layout.addWidget(shapes_group)

        # Shape properties
        self.shape_props_group = QGroupBox("Shape Properties")
        self.shape_props_layout = QFormLayout(self.shape_props_group)
        layout.addWidget(self.shape_props_group)

        layout.addStretch()
        return widget

    def create_tags_tab(self) -> QWidget:
        """Create tags management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tags for current tile
        tile_tags_group = QGroupBox("Tile Tags")
        tile_tags_layout = QVBoxLayout(tile_tags_group)

        # Add tag row
        add_tag_row = QHBoxLayout()
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("Enter tag name...")
        add_tag_row.addWidget(self.new_tag_edit)

        add_tag_btn = QPushButton("Add")
        add_tag_btn.clicked.connect(self.add_tag_to_tile)
        add_tag_row.addWidget(add_tag_btn)

        tile_tags_layout.addLayout(add_tag_row)

        # Current tile tags
        self.tile_tags_list = QListWidget()
        self.tile_tags_list.itemSelectionChanged.connect(self.on_tile_tag_selected)
        tile_tags_layout.addWidget(self.tile_tags_list)

        # Remove tag button
        remove_tag_btn = QPushButton("Remove Selected")
        remove_tag_btn.clicked.connect(self.remove_tag_from_tile)
        tile_tags_layout.addWidget(remove_tag_btn)

        layout.addWidget(tile_tags_group)

        # All tags in tileset
        all_tags_group = QGroupBox("All Tags in Tileset")
        all_tags_layout = QVBoxLayout(all_tags_group)

        self.all_tags_list = QListWidget()
        all_tags_layout.addWidget(self.all_tags_list)

        layout.addWidget(all_tags_group)

        layout.addStretch()
        return widget

    def setup_menus(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Tileset", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_tileset)
        file_menu.addAction(new_action)

        open_action = QAction("Open Tileset", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_tileset)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_tileset)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_tileset_as)
        file_menu.addAction(save_as_action)

        # View menu
        view_menu = menubar.addMenu("View")

        grid_action = QAction("Show Grid", self)
        grid_action.setCheckable(True)
        grid_action.setChecked(True)
        grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(grid_action)

        collision_action = QAction("Show Collision", self)
        collision_action.setCheckable(True)
        collision_action.triggered.connect(self.toggle_collision)
        view_menu.addAction(collision_action)

        view_menu.addSeparator()

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("Reset Zoom", self)
        zoom_reset_action.triggered.connect(self.zoom_reset)
        view_menu.addAction(zoom_reset_action)

    def setup_toolbar(self):
        """Setup toolbar"""
        toolbar = self.addToolBar("Main")

        # File actions
        toolbar.addAction("New", self.new_tileset)
        toolbar.addAction("Open", self.open_tileset)
        toolbar.addAction("Save", self.save_tileset)

        toolbar.addSeparator()

        # View actions
        toolbar.addAction("Grid", self.toggle_grid)
        toolbar.addAction("Collision", self.toggle_collision)

        toolbar.addSeparator()

        # Zoom controls
        toolbar.addAction("Zoom In", self.zoom_in)
        toolbar.addAction("Zoom Out", self.zoom_out)
        toolbar.addAction("Reset Zoom", self.zoom_reset)

    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def new_tileset(self):
        """Create a new tileset"""
        self.current_tileset = TileSet("New TileSet")
        self.current_file_path = None
        self.canvas.set_tileset(self.current_tileset)
        self.update_ui_from_tileset()
        self.status_bar.showMessage("New tileset created")

    def open_tileset(self):
        """Open an existing tileset"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Tileset",
            str(self.project.project_path / "assets"),
            "Tileset Files (*.tres *.json);;All Files (*)"
        )

        if file_path:
            try:
                self.current_tileset = TileSet.load_from_file(file_path)
                self.current_file_path = file_path
                self.canvas.set_tileset(self.current_tileset)
                self.update_ui_from_tileset()
                self.status_bar.showMessage(f"Opened: {Path(file_path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open tileset: {e}")

    def save_tileset(self):
        """Save the current tileset"""
        if not self.current_tileset:
            return

        if not self.current_file_path:
            self.save_tileset_as()
            return

        try:
            self.update_tileset_from_ui()
            self.current_tileset.save_to_file(self.current_file_path)
            self.status_bar.showMessage(f"Saved: {Path(self.current_file_path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save tileset: {e}")

    def save_tileset_as(self):
        """Save the tileset with a new name"""
        if not self.current_tileset:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Tileset As",
            str(self.project.project_path / "assets" / f"{self.current_tileset.name}.tres"),
            "Tileset Files (*.tres *.json);;All Files (*)"
        )

        if file_path:
            try:
                self.update_tileset_from_ui()
                self.current_tileset.save_to_file(file_path)
                self.current_file_path = file_path
                self.status_bar.showMessage(f"Saved: {Path(file_path).name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save tileset: {e}")

    def update_ui_from_tileset(self):
        """Update UI controls from current tileset"""
        if not self.current_tileset:
            return

        # Update tileset properties
        self.name_edit.setText(self.current_tileset.name)
        self.description_edit.setPlainText(self.current_tileset.description)
        self.texture_path_edit.setText(self.current_tileset.texture_path)

        self.tile_width_spin.setValue(int(self.current_tileset.tile_size[0]))
        self.tile_height_spin.setValue(int(self.current_tileset.tile_size[1]))
        self.margin_x_spin.setValue(int(self.current_tileset.margin[0]))
        self.margin_y_spin.setValue(int(self.current_tileset.margin[1]))
        self.spacing_x_spin.setValue(int(self.current_tileset.spacing[0]))
        self.spacing_y_spin.setValue(int(self.current_tileset.spacing[1]))

        # Update all tags list
        self.update_all_tags_list()

        # Clear tile selection
        self.canvas.selected_tile_id = -1
        self.update_tile_ui()

    def update_tileset_from_ui(self):
        """Update tileset from UI controls"""
        if not self.current_tileset:
            return

        self.current_tileset.name = self.name_edit.text()
        self.current_tileset.description = self.description_edit.toPlainText()
        self.current_tileset.texture_path = self.texture_path_edit.text()

        self.current_tileset.tile_size = [
            self.tile_width_spin.value(),
            self.tile_height_spin.value()
        ]
        self.current_tileset.margin = [
            self.margin_x_spin.value(),
            self.margin_y_spin.value()
        ]
        self.current_tileset.spacing = [
            self.spacing_x_spin.value(),
            self.spacing_y_spin.value()
        ]

    # Event handlers
    def on_tileset_property_changed(self):
        """Handle tileset property changes"""
        if self.current_tileset:
            self.update_tileset_from_ui()
            self.canvas.load_texture()
            self.canvas.update()

    def on_texture_changed(self):
        """Handle texture path changes"""
        if self.current_tileset:
            self.current_tileset.texture_path = self.texture_path_edit.text()
            self.canvas.load_texture()
            self.canvas.update()

    def on_tile_selected(self, tile_id: int):
        """Handle tile selection"""
        self.canvas.selected_tile_id = tile_id
        self.update_tile_ui()

    def on_tile_property_changed(self):
        """Handle tile property changes"""
        if self.current_tileset and self.canvas.selected_tile_id >= 0:
            tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)
            if tile_def:
                tile_def.name = self.tile_name_edit.text()
                self.canvas.update()

    def on_collision_shape_selected(self):
        """Handle collision shape selection"""
        # Update shape properties UI
        pass

    def on_tile_tag_selected(self):
        """Handle tile tag selection"""
        pass

    def update_tile_ui(self):
        """Update tile-specific UI elements"""
        if not self.current_tileset or self.canvas.selected_tile_id < 0:
            self.tile_info_label.setText("No tile selected")
            self.tile_name_edit.clear()
            self.texture_rect_label.setText("0, 0, 32, 32")
            self.tile_tags_list.clear()
            self.collision_shapes_list.clear()
            return

        tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)
        if not tile_def:
            return

        # Update tile info
        self.tile_info_label.setText(f"Tile {tile_def.tile_id}: {tile_def.name}")
        self.tile_name_edit.setText(tile_def.name)

        # Update texture rect display
        rect = tile_def.texture_rect
        self.texture_rect_label.setText(f"{rect[0]}, {rect[1]}, {rect[2]}, {rect[3]}")

        # Update tags list
        self.tile_tags_list.clear()
        for tag in tile_def.tags:
            self.tile_tags_list.addItem(tag)

        # Update collision shapes list
        self.collision_shapes_list.clear()
        for i, shape in enumerate(tile_def.collision_shapes):
            shape_type = shape.get("type", "unknown")
            item_text = f"{shape_type.title()} {i+1}"
            self.collision_shapes_list.addItem(item_text)

    def update_all_tags_list(self):
        """Update the list of all tags in the tileset"""
        if not self.current_tileset:
            return

        all_tags = set()
        for tile_def in self.current_tileset.tiles.values():
            all_tags.update(tile_def.tags)

        self.all_tags_list.clear()
        for tag in sorted(all_tags):
            self.all_tags_list.addItem(tag)

    # Tool actions
    def browse_texture(self):
        """Browse for texture file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Texture",
            str(self.project.project_path / "assets"),
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
        )

        if file_path:
            # Convert to relative path if possible
            try:
                relative_path = self.project.get_relative_path(file_path)
                self.texture_path_edit.setText(str(relative_path))
            except:
                self.texture_path_edit.setText(file_path)

    def auto_generate_tiles(self):
        """Auto-generate tiles from texture"""
        if not self.current_tileset or not self.current_tileset.texture_path:
            QMessageBox.warning(self, "Warning", "Please set a texture path first.")
            return

        # Get texture dimensions
        texture_path = Path(self.current_tileset.texture_path)
        if not texture_path.exists():
            # Try relative to project
            texture_path = self.project.project_path / self.current_tileset.texture_path

        if not texture_path.exists():
            QMessageBox.warning(self, "Warning", "Texture file not found.")
            return

        try:
            pixmap = QPixmap(str(texture_path))
            if pixmap.isNull():
                QMessageBox.warning(self, "Warning", "Failed to load texture.")
                return

            # Update tileset from UI first
            self.update_tileset_from_ui()

            # Auto-generate tiles
            self.current_tileset.auto_generate_tiles_from_texture(pixmap.width(), pixmap.height())

            # Update canvas and UI
            self.canvas.update()
            self.update_tile_ui()
            self.status_bar.showMessage(f"Generated {len(self.current_tileset.tiles)} tiles")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to auto-generate tiles: {e}")

    def add_custom_property(self):
        """Add a custom property to the selected tile"""
        if not self.current_tileset or self.canvas.selected_tile_id < 0:
            return

        # Simple dialog for now - could be enhanced
        from PyQt6.QtWidgets import QInputDialog
        prop_name, ok = QInputDialog.getText(self, "Add Property", "Property name:")
        if ok and prop_name:
            prop_value, ok = QInputDialog.getText(self, "Add Property", f"Value for '{prop_name}':")
            if ok:
                tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)
                if tile_def:
                    tile_def.custom_properties[prop_name] = prop_value
                    # Refresh custom properties display
                    self.refresh_custom_properties_ui()

    def refresh_custom_properties_ui(self):
        """Refresh the custom properties UI"""
        # Clear existing widgets
        while self.custom_props_layout.count():
            child = self.custom_props_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.current_tileset or self.canvas.selected_tile_id < 0:
            return

        tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)
        if not tile_def:
            return

        # Add widgets for each custom property
        for prop_name, prop_value in tile_def.custom_properties.items():
            prop_widget = QWidget()
            prop_layout = QHBoxLayout(prop_widget)
            prop_layout.setContentsMargins(0, 0, 0, 0)

            name_label = QLabel(f"{prop_name}:")
            prop_layout.addWidget(name_label)

            value_edit = QLineEdit(str(prop_value))
            value_edit.textChanged.connect(
                lambda text, name=prop_name: self.update_custom_property(name, text)
            )
            prop_layout.addWidget(value_edit)

            remove_btn = QPushButton("X")
            remove_btn.setMaximumWidth(30)
            remove_btn.clicked.connect(
                lambda checked, name=prop_name: self.remove_custom_property(name)
            )
            prop_layout.addWidget(remove_btn)

            self.custom_props_layout.addWidget(prop_widget)

    def update_custom_property(self, prop_name: str, value: str):
        """Update a custom property value"""
        if not self.current_tileset or self.canvas.selected_tile_id < 0:
            return

        tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)
        if tile_def:
            tile_def.custom_properties[prop_name] = value

    def remove_custom_property(self, prop_name: str):
        """Remove a custom property"""
        if not self.current_tileset or self.canvas.selected_tile_id < 0:
            return

        tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)
        if tile_def and prop_name in tile_def.custom_properties:
            del tile_def.custom_properties[prop_name]
            self.refresh_custom_properties_ui()

    # Collision shape management
    def add_collision_shape(self, shape_type: str):
        """Add a collision shape to the selected tile"""
        if not self.current_tileset or self.canvas.selected_tile_id < 0:
            return

        tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)
        if not tile_def:
            return

        if shape_type == "rect":
            # Add rectangle collision shape
            shape = {
                "type": "rect",
                "rect": [0, 0, tile_def.texture_rect[2], tile_def.texture_rect[3]]
            }
        elif shape_type == "polygon":
            # Add polygon collision shape with default triangle
            tile_w, tile_h = tile_def.texture_rect[2], tile_def.texture_rect[3]
            shape = {
                "type": "polygon",
                "points": [
                    [tile_w // 2, 0],
                    [0, tile_h],
                    [tile_w, tile_h]
                ]
            }
        else:
            return

        tile_def.collision_shapes.append(shape)
        self.update_tile_ui()
        self.canvas.update()

    def remove_collision_shape(self):
        """Remove the selected collision shape"""
        if not self.current_tileset or self.canvas.selected_tile_id < 0:
            return

        current_item = self.collision_shapes_list.currentItem()
        if not current_item:
            return

        shape_index = self.collision_shapes_list.row(current_item)
        tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)

        if tile_def and 0 <= shape_index < len(tile_def.collision_shapes):
            del tile_def.collision_shapes[shape_index]
            self.update_tile_ui()
            self.canvas.update()

    # Tag management
    def add_tag_to_tile(self):
        """Add a tag to the selected tile"""
        if not self.current_tileset or self.canvas.selected_tile_id < 0:
            return

        tag_name = self.new_tag_edit.text().strip()
        if not tag_name:
            return

        tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)
        if tile_def and tag_name not in tile_def.tags:
            tile_def.tags.append(tag_name)
            self.new_tag_edit.clear()
            self.update_tile_ui()
            self.update_all_tags_list()

    def remove_tag_from_tile(self):
        """Remove the selected tag from the tile"""
        if not self.current_tileset or self.canvas.selected_tile_id < 0:
            return

        current_item = self.tile_tags_list.currentItem()
        if not current_item:
            return

        tag_name = current_item.text()
        tile_def = self.current_tileset.get_tile(self.canvas.selected_tile_id)

        if tile_def and tag_name in tile_def.tags:
            tile_def.tags.remove(tag_name)
            self.update_tile_ui()
            self.update_all_tags_list()

    # View controls
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.canvas.grid_visible = not self.canvas.grid_visible
        self.canvas.update()

    def toggle_collision(self):
        """Toggle collision shapes visibility"""
        self.canvas.collision_visible = not self.canvas.collision_visible
        self.canvas.update()

    def zoom_in(self):
        """Zoom in the canvas"""
        self.canvas.zoom = min(5.0, self.canvas.zoom * 1.2)
        self.canvas.update()

    def zoom_out(self):
        """Zoom out the canvas"""
        self.canvas.zoom = max(0.1, self.canvas.zoom / 1.2)
        self.canvas.update()

    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.canvas.zoom = 1.0
        self.canvas.offset = QPoint(0, 0)
        self.canvas.update()
