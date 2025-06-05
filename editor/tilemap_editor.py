"""
Tilemap Editor for Lupine Engine
Comprehensive tilemap editing tool with layer support, painting tools, and tileset integration
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QLabel, QPushButton, QSpinBox, QLineEdit,
    QGroupBox, QFormLayout, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QTabWidget, QTextEdit,
    QCheckBox, QComboBox, QGridLayout, QFrame, QSlider,
    QDoubleSpinBox, QToolBar, QMenuBar, QMenu, QStatusBar,
    QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QPoint
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QBrush, QColor, QFont,
    QAction, QIcon, QKeySequence, QWheelEvent, QMouseEvent
)

from core.project import LupineProject
from core.tileset import TileSet, get_tileset_manager


class TilemapCanvas(QWidget):
    """Canvas widget for editing tilemap with painting tools"""
    
    tile_painted = pyqtSignal(int, int, int, dict)  # x, y, layer, tile_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tilemap_node = None
        self.current_tileset = None
        self.current_tile_id = -1
        self.current_layer = 0
        self.current_tileset_index = 0
        self.zoom = 1.0
        self.offset = QPoint(0, 0)
        self.grid_visible = True
        self.collision_visible = False

        # Multiple tileset support
        self.tilesets = []  # List of loaded tilesets
        self.tileset_textures = {}  # Dict[int, QPixmap] - cached textures

        # Painting state
        self.painting = False
        self.paint_mode = "paint"  # "paint", "erase", "fill"
        self.last_paint_pos = None

        # Mouse interaction
        self.dragging = False
        self.last_mouse_pos = QPoint()

        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
    
    def set_tilemap_node(self, tilemap_node: Dict[str, Any]):
        """Set the tilemap node to edit"""
        self.tilemap_node = tilemap_node
        self.update()
    
    def set_current_tileset(self, tileset: TileSet):
        """Set the current tileset for painting"""
        self.current_tileset = tileset
        # Add to tilesets list if not already there
        if tileset and tileset not in self.tilesets:
            self.tilesets.append(tileset)
            self.current_tileset_index = len(self.tilesets) - 1
            self.load_tileset_texture(self.current_tileset_index, tileset)
        elif tileset:
            self.current_tileset_index = self.tilesets.index(tileset)
        self.update()

    def get_tileset_by_index(self, index: int):
        """Get tileset by index"""
        if 0 <= index < len(self.tilesets):
            return self.tilesets[index]
        return None

    def load_tileset_texture(self, index: int, tileset):
        """Load texture for a tileset"""
        if not tileset or not tileset.texture_path:
            return

        try:
            from PyQt6.QtGui import QPixmap
            # Try relative to project first, then absolute
            if hasattr(self, 'project') and self.project:
                texture_path = self.project.project_path / tileset.texture_path
            else:
                texture_path = Path(tileset.texture_path)

            if texture_path.exists():
                pixmap = QPixmap(str(texture_path))
                if not pixmap.isNull():
                    self.tileset_textures[index] = pixmap
        except Exception as e:
            print(f"Error loading tileset texture: {e}")

    def set_project(self, project):
        """Set the project reference for texture loading"""
        self.project = project
    
    def set_current_tile(self, tile_id: int):
        """Set the current tile for painting"""
        self.current_tile_id = tile_id
    
    def set_current_layer(self, layer: int):
        """Set the current layer for editing"""
        self.current_layer = layer
    
    def set_paint_mode(self, mode: str):
        """Set the painting mode"""
        self.paint_mode = mode
    
    def paintEvent(self, event):
        """Paint the tilemap canvas"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(64, 64, 64))
        
        if not self.tilemap_node:
            painter.setPen(QColor(128, 128, 128))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No tilemap loaded")
            return
        
        # Apply zoom and offset
        painter.scale(self.zoom, self.zoom)
        painter.translate(self.offset)
        
        # Draw background grid
        if self.grid_visible:
            self.draw_grid(painter)
        
        # Draw tiles for all layers
        self.draw_tiles(painter)
        
        # Draw collision shapes if enabled
        if self.collision_visible:
            self.draw_collision_shapes(painter)
    
    def draw_grid(self, painter: QPainter):
        """Draw the tile grid"""
        if not self.tilemap_node:
            return

        cell_size = self.tilemap_node.get("cell_size", [32, 32])
        tile_w, tile_h = cell_size
        map_size_mode = self.tilemap_node.get("map_size_mode", "infinite")

        # Use different colors for different zoom levels
        if self.zoom >= 1.0:
            grid_color = QColor(255, 255, 255, 128)  # More visible when zoomed in
            line_width = 1
        elif self.zoom >= 0.5:
            grid_color = QColor(255, 255, 255, 96)
            line_width = 1
        else:
            grid_color = QColor(255, 255, 255, 64)  # Less visible when zoomed out
            line_width = 1

        painter.setPen(QPen(grid_color, line_width))

        # Calculate visible area in world coordinates
        visible_rect = self.rect()
        world_start_x = (-self.offset.x()) / self.zoom
        world_start_y = (-self.offset.y()) / self.zoom
        world_end_x = world_start_x + visible_rect.width() / self.zoom
        world_end_y = world_start_y + visible_rect.height() / self.zoom

        # Calculate grid bounds
        if map_size_mode == "fixed":
            # Limit grid to fixed map size
            fixed_size = self.tilemap_node.get("fixed_map_size", [100, 100])
            map_width = fixed_size[0] * tile_w
            map_height = fixed_size[1] * tile_h

            grid_start_x = max(0, int(world_start_x // tile_w) * tile_w)
            grid_start_y = max(0, int(world_start_y // tile_h) * tile_h)
            grid_end_x = min(map_width, int(world_end_x // tile_w + 1) * tile_w)
            grid_end_y = min(map_height, int(world_end_y // tile_h + 1) * tile_h)
        else:
            # Infinite mode - draw grid based on visible area
            grid_start_x = int(world_start_x // tile_w) * tile_w
            grid_start_y = int(world_start_y // tile_h) * tile_h
            grid_end_x = int(world_end_x // tile_w + 1) * tile_w
            grid_end_y = int(world_end_y // tile_h + 1) * tile_h

        # Draw vertical lines
        x = grid_start_x
        while x <= grid_end_x:
            painter.drawLine(int(x), int(grid_start_y), int(x), int(grid_end_y))
            x += tile_w

        # Draw horizontal lines
        y = grid_start_y
        while y <= grid_end_y:
            painter.drawLine(int(grid_start_x), int(y), int(grid_end_x), int(y))
            y += tile_h

        # Draw map boundary for fixed mode
        if map_size_mode == "fixed":
            fixed_size = self.tilemap_node.get("fixed_map_size", [100, 100])
            map_width = fixed_size[0] * tile_w
            map_height = fixed_size[1] * tile_h

            painter.setPen(QPen(QColor(255, 255, 0, 200), 3))  # Yellow boundary
            painter.drawRect(0, 0, int(map_width), int(map_height))

        # Draw origin lines (thicker, different color)
        if grid_start_x <= 0 <= grid_end_x:
            painter.setPen(QPen(QColor(255, 0, 0, 128), 2))  # Red vertical line at x=0
            painter.drawLine(0, int(grid_start_y), 0, int(grid_end_y))

        if grid_start_y <= 0 <= grid_end_y:
            painter.setPen(QPen(QColor(0, 255, 0, 128), 2))  # Green horizontal line at y=0
            painter.drawLine(int(grid_start_x), 0, int(grid_end_x), 0)
    
    def draw_tiles(self, painter: QPainter):
        """Draw all tiles from all layers"""
        if not self.tilemap_node:
            return
        
        # Get layer data
        layers = self.tilemap_node.get("layers", [])
        tiles_data = self.tilemap_node.get("tiles", {})
        cell_size = self.tilemap_node.get("cell_size", [32, 32])
        tile_w, tile_h = cell_size
        
        # Draw layers in order
        for layer_index, layer in enumerate(layers):
            if not layer.get("visible", True):
                continue
            
            layer_key = str(layer_index)
            if layer_key not in tiles_data:
                continue
            
            layer_tiles = tiles_data[layer_key]
            layer_opacity = layer.get("opacity", 1.0)
            
            # Set layer opacity
            painter.setOpacity(layer_opacity)
            
            # Draw tiles in this layer
            for pos_key, tile_data in layer_tiles.items():
                try:
                    x, y = map(int, pos_key.split(','))
                    self.draw_single_tile(painter, x, y, tile_data, tile_w, tile_h)
                except (ValueError, KeyError):
                    continue
            
            # Reset opacity
            painter.setOpacity(1.0)
    
    def draw_single_tile(self, painter: QPainter, x: int, y: int, tile_data: Dict[str, Any], tile_w: int, tile_h: int):
        """Draw a single tile"""
        if not tile_data:
            return

        tile_id = tile_data.get("tile_id", -1)
        if tile_id < 0:
            return

        # Get tileset index (default to 0 for backward compatibility)
        tileset_index = tile_data.get("tileset", 0)
        tileset = self.get_tileset_by_index(tileset_index)

        if not tileset:
            # Draw placeholder if no tileset
            world_x = x * tile_w
            world_y = y * tile_h
            painter.fillRect(world_x, world_y, tile_w, tile_h, QColor(255, 0, 0, 100))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawRect(world_x, world_y, tile_w, tile_h)
            painter.drawText(world_x + 2, world_y + 12, f"?{tile_id}")
            return

        tile_def = tileset.get_tile(tile_id)
        if not tile_def:
            # Draw placeholder for missing tile
            world_x = x * tile_w
            world_y = y * tile_h
            painter.fillRect(world_x, world_y, tile_w, tile_h, QColor(255, 255, 0, 100))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawRect(world_x, world_y, tile_w, tile_h)
            painter.drawText(world_x + 2, world_y + 12, f"!{tile_id}")
            return

        # Calculate world position
        world_x = x * tile_w
        world_y = y * tile_h

        # Try to draw actual texture if available
        if hasattr(self, 'tileset_textures') and tileset_index in self.tileset_textures:
            texture = self.tileset_textures[tileset_index]
            if texture and not texture.isNull():
                # Draw tile from texture
                tile_rect = tile_def.texture_rect
                source_rect = QRect(tile_rect[0], tile_rect[1], tile_rect[2], tile_rect[3])
                target_rect = QRect(world_x, world_y, tile_w, tile_h)
                painter.drawPixmap(target_rect, texture, source_rect)
                return

        # Fallback: draw colored rectangle with tile ID
        # Use different colors for different tile IDs
        hue = (tile_id * 137) % 360  # Golden angle for good color distribution
        color = QColor.fromHsv(hue, 180, 200, 180)
        painter.fillRect(world_x, world_y, tile_w, tile_h, color)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(world_x, world_y, tile_w, tile_h)

        # Draw tile ID for debugging
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(world_x + 2, world_y + 12, str(tile_id))
    
    def draw_collision_shapes(self, painter: QPainter):
        """Draw collision shapes for tiles"""
        # TODO: Implement collision shape visualization
        pass
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.paint_mode in ["paint", "erase"]:
                self.start_painting(event.position().toPoint())
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.dragging = True
            self.last_mouse_pos = event.position().toPoint()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        if self.painting and self.paint_mode in ["paint", "erase"]:
            self.continue_painting(event.position().toPoint())
        elif self.dragging:
            delta = event.position().toPoint() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.position().toPoint()
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.stop_painting()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.dragging = False
    
    def start_painting(self, pos: QPoint):
        """Start painting operation"""
        self.painting = True
        self.paint_at_position(pos)
        self.last_paint_pos = pos
    
    def continue_painting(self, pos: QPoint):
        """Continue painting operation (drag painting)"""
        if self.last_paint_pos:
            # Paint along the line from last position to current position
            self.paint_line(self.last_paint_pos, pos)
        self.last_paint_pos = pos
    
    def stop_painting(self):
        """Stop painting operation"""
        self.painting = False
        self.last_paint_pos = None
    
    def paint_at_position(self, screen_pos: QPoint):
        """Paint a tile at the given screen position"""
        if not self.tilemap_node:
            return

        # Convert screen position to tile coordinates
        tile_pos = self.screen_to_tile_coords(screen_pos)
        if tile_pos is None:
            return

        x, y = tile_pos

        if self.paint_mode == "paint" and self.current_tile_id >= 0:
            # Paint tile
            tile_data = {
                "tile_id": self.current_tile_id,
                "tileset": self.current_tileset_index
            }
            self.tile_painted.emit(x, y, self.current_layer, tile_data)
        elif self.paint_mode == "erase":
            # Erase tile
            self.tile_painted.emit(x, y, self.current_layer, {})
        elif self.paint_mode == "fill":
            # Fill bucket
            self.fill_area(x, y)

        self.update()

    def fill_area(self, start_x: int, start_y: int):
        """Fill an area with the current tile using flood fill algorithm"""
        if not self.tilemap_node or self.current_tile_id < 0:
            return

        # Get current layer tiles
        tiles_data = self.tilemap_node.get("tiles", {})
        layer_key = str(self.current_layer)
        layer_tiles = tiles_data.get(layer_key, {})

        # Get the tile we're replacing
        start_key = f"{start_x},{start_y}"
        original_tile = layer_tiles.get(start_key, {})
        original_tile_id = original_tile.get("tile_id", -1)

        # New tile data
        new_tile_data = {
            "tile_id": self.current_tile_id,
            "tileset": self.current_tileset_index
        }

        # Don't fill if we're already the target tile
        if original_tile_id == self.current_tile_id:
            return

        # Flood fill using stack-based approach
        stack = [(start_x, start_y)]
        filled_tiles = set()

        while stack and len(filled_tiles) < 1000:  # Limit to prevent infinite loops
            x, y = stack.pop()
            pos_key = f"{x},{y}"

            # Skip if already processed
            if pos_key in filled_tiles:
                continue

            # Check if this tile matches the original
            current_tile = layer_tiles.get(pos_key, {})
            current_tile_id = current_tile.get("tile_id", -1)

            if current_tile_id != original_tile_id:
                continue

            # Fill this tile
            filled_tiles.add(pos_key)
            self.tile_painted.emit(x, y, self.current_layer, new_tile_data)

            # Add neighbors to stack
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_x, neighbor_y = x + dx, y + dy
                neighbor_key = f"{neighbor_x},{neighbor_y}"

                if neighbor_key not in filled_tiles:
                    stack.append((neighbor_x, neighbor_y))
    
    def paint_line(self, start_pos: QPoint, end_pos: QPoint):
        """Paint tiles along a line (for drag painting)"""
        # Simple line drawing algorithm
        start_tile = self.screen_to_tile_coords(start_pos)
        end_tile = self.screen_to_tile_coords(end_pos)
        
        if not start_tile or not end_tile:
            return
        
        x0, y0 = start_tile
        x1, y1 = end_tile
        
        # Bresenham's line algorithm
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            self.paint_at_position(self.tile_to_screen_coords(x, y))
            
            if x == x1 and y == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def screen_to_tile_coords(self, screen_pos: QPoint) -> Optional[tuple]:
        """Convert screen coordinates to tile coordinates"""
        if not self.tilemap_node:
            return None
        
        cell_size = self.tilemap_node.get("cell_size", [32, 32])
        tile_w, tile_h = cell_size
        
        # Apply inverse transform
        world_x = (screen_pos.x() / self.zoom) - self.offset.x()
        world_y = (screen_pos.y() / self.zoom) - self.offset.y()
        
        # Convert to tile coordinates
        tile_x = int(world_x // tile_w)
        tile_y = int(world_y // tile_h)
        
        return (tile_x, tile_y)
    
    def tile_to_screen_coords(self, tile_x: int, tile_y: int) -> QPoint:
        """Convert tile coordinates to screen coordinates"""
        if not self.tilemap_node:
            return QPoint(0, 0)
        
        cell_size = self.tilemap_node.get("cell_size", [32, 32])
        tile_w, tile_h = cell_size
        
        world_x = tile_x * tile_w
        world_y = tile_y * tile_h
        
        screen_x = int((world_x + self.offset.x()) * self.zoom)
        screen_y = int((world_y + self.offset.y()) * self.zoom)
        
        return QPoint(screen_x, screen_y)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom with mouse wheel"""
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.zoom = max(0.1, min(5.0, self.zoom * zoom_factor))
        self.update()


class TilemapEditorWindow(QMainWindow):
    """Main tilemap editor window"""
    
    def __init__(self, project: LupineProject, tilemap_node: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.project = project
        self.tilemap_node = tilemap_node
        self.current_tileset = None
        
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_status_bar()
        
        # Load tileset if specified
        self.load_tileset()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Tilemap Editor - Lupine Engine")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Tools and layers
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center - Tilemap canvas
        self.canvas = TilemapCanvas()
        self.canvas.set_project(self.project)
        self.canvas.set_tilemap_node(self.tilemap_node)
        self.canvas.tile_painted.connect(self.on_tile_painted)
        splitter.addWidget(self.canvas)
        
        # Right panel - Tileset palette
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([250, 800, 350])
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with tools and layers"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tools group
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout(tools_group)

        # Paint mode buttons
        self.tool_group = QButtonGroup()

        paint_radio = QRadioButton("Paint")
        paint_radio.setChecked(True)
        paint_radio.toggled.connect(lambda checked: self.set_paint_mode("paint") if checked else None)
        self.tool_group.addButton(paint_radio)
        tools_layout.addWidget(paint_radio)

        erase_radio = QRadioButton("Erase")
        erase_radio.toggled.connect(lambda checked: self.set_paint_mode("erase") if checked else None)
        self.tool_group.addButton(erase_radio)
        tools_layout.addWidget(erase_radio)

        fill_radio = QRadioButton("Fill")
        fill_radio.toggled.connect(lambda checked: self.set_paint_mode("fill") if checked else None)
        self.tool_group.addButton(fill_radio)
        tools_layout.addWidget(fill_radio)

        layout.addWidget(tools_group)

        # View options group
        view_group = QGroupBox("View Options")
        view_layout = QVBoxLayout(view_group)

        # Grid toggle
        from PyQt6.QtWidgets import QCheckBox
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.toggled.connect(self.toggle_grid_checkbox)
        view_layout.addWidget(self.grid_checkbox)

        # Collision toggle
        self.collision_checkbox = QCheckBox("Show Collision")
        self.collision_checkbox.setChecked(False)
        self.collision_checkbox.toggled.connect(self.toggle_collision_checkbox)
        view_layout.addWidget(self.collision_checkbox)

        layout.addWidget(view_group)
        
        # Layers group
        layers_group = QGroupBox("Layers")
        layers_layout = QVBoxLayout(layers_group)
        
        # Layer controls
        layer_controls = QHBoxLayout()
        add_layer_btn = QPushButton("Add")
        add_layer_btn.clicked.connect(self.add_layer)
        layer_controls.addWidget(add_layer_btn)
        
        remove_layer_btn = QPushButton("Remove")
        remove_layer_btn.clicked.connect(self.remove_layer)
        layer_controls.addWidget(remove_layer_btn)
        
        layers_layout.addLayout(layer_controls)
        
        # Layers list
        self.layers_list = QListWidget()
        self.layers_list.itemSelectionChanged.connect(self.on_layer_selected)
        layers_layout.addWidget(self.layers_list)
        
        layout.addWidget(layers_group)
        
        layout.addStretch()
        return panel

    def create_right_panel(self) -> QWidget:
        """Create the right panel with tileset palette"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Tileset selection
        tileset_group = QGroupBox("Tilesets")
        tileset_layout = QVBoxLayout(tileset_group)

        # Current tileset selector
        tileset_selector_layout = QHBoxLayout()
        tileset_selector_layout.addWidget(QLabel("Current:"))
        self.tileset_combo = QComboBox()
        self.tileset_combo.currentIndexChanged.connect(self.on_tileset_changed)
        tileset_selector_layout.addWidget(self.tileset_combo)
        tileset_layout.addLayout(tileset_selector_layout)

        # Tileset management buttons
        tileset_buttons_layout = QHBoxLayout()

        add_tileset_btn = QPushButton("Add Tileset")
        add_tileset_btn.clicked.connect(self.add_tileset)
        tileset_buttons_layout.addWidget(add_tileset_btn)

        remove_tileset_btn = QPushButton("Remove")
        remove_tileset_btn.clicked.connect(self.remove_tileset)
        tileset_buttons_layout.addWidget(remove_tileset_btn)

        tileset_layout.addLayout(tileset_buttons_layout)

        # Open tileset editor button
        open_tileset_editor_btn = QPushButton("Open Tileset Editor")
        open_tileset_editor_btn.clicked.connect(self.open_tileset_editor)
        tileset_layout.addWidget(open_tileset_editor_btn)

        layout.addWidget(tileset_group)

        # Tile palette
        palette_group = QGroupBox("Tile Palette")
        palette_layout = QVBoxLayout(palette_group)

        # Tile grid (simplified for now)
        self.tile_palette = QListWidget()
        self.tile_palette.setViewMode(QListWidget.ViewMode.IconMode)
        self.tile_palette.setGridSize(QSize(56, 56))  # Larger grid for 48x48 icons
        self.tile_palette.setIconSize(QSize(48, 48))
        self.tile_palette.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.tile_palette.itemSelectionChanged.connect(self.on_tile_selected)
        palette_layout.addWidget(self.tile_palette)

        layout.addWidget(palette_group)

        # Map properties
        map_group = QGroupBox("Map Properties")
        map_layout = QFormLayout(map_group)

        # Cell size
        cell_size = self.tilemap_node.get("cell_size", [32, 32])
        cell_size_layout = QHBoxLayout()

        self.cell_width_spin = QSpinBox()
        self.cell_width_spin.setRange(1, 512)
        self.cell_width_spin.setValue(int(cell_size[0]))
        self.cell_width_spin.valueChanged.connect(self.update_cell_size)
        cell_size_layout.addWidget(self.cell_width_spin)

        cell_size_layout.addWidget(QLabel("x"))

        self.cell_height_spin = QSpinBox()
        self.cell_height_spin.setRange(1, 512)
        self.cell_height_spin.setValue(int(cell_size[1]))
        self.cell_height_spin.valueChanged.connect(self.update_cell_size)
        cell_size_layout.addWidget(self.cell_height_spin)

        map_layout.addRow("Cell Size:", cell_size_layout)

        # Map size mode
        self.map_size_mode_combo = QComboBox()
        self.map_size_mode_combo.addItems(["infinite", "fixed"])
        self.map_size_mode_combo.setCurrentText(self.tilemap_node.get("map_size_mode", "infinite"))
        self.map_size_mode_combo.currentTextChanged.connect(self.update_map_size_mode)
        map_layout.addRow("Size Mode:", self.map_size_mode_combo)

        # Fixed map size (only shown when mode is fixed)
        fixed_size = self.tilemap_node.get("fixed_map_size", [100, 100])
        fixed_size_layout = QHBoxLayout()

        self.map_width_spin = QSpinBox()
        self.map_width_spin.setRange(1, 10000)
        self.map_width_spin.setValue(int(fixed_size[0]))
        self.map_width_spin.valueChanged.connect(self.update_fixed_map_size)
        fixed_size_layout.addWidget(self.map_width_spin)

        fixed_size_layout.addWidget(QLabel("x"))

        self.map_height_spin = QSpinBox()
        self.map_height_spin.setRange(1, 10000)
        self.map_height_spin.setValue(int(fixed_size[1]))
        self.map_height_spin.valueChanged.connect(self.update_fixed_map_size)
        fixed_size_layout.addWidget(self.map_height_spin)

        map_layout.addRow("Map Size:", fixed_size_layout)

        layout.addWidget(map_group)

        # Utility scaling group
        utility_group = QGroupBox("Utility Scaling")
        utility_layout = QFormLayout(utility_group)

        # Tile size in world space
        self.world_tile_size_spin = QDoubleSpinBox()
        self.world_tile_size_spin.setRange(0.1, 1000.0)
        self.world_tile_size_spin.setValue(32.0)
        self.world_tile_size_spin.setSuffix(" units")
        self.world_tile_size_spin.valueChanged.connect(self.update_utility_scale)
        utility_layout.addRow("Tile Size in World:", self.world_tile_size_spin)

        # Auto-calculate scale button
        calc_scale_btn = QPushButton("Auto-Calculate Scale")
        calc_scale_btn.clicked.connect(self.auto_calculate_scale)
        utility_layout.addRow("", calc_scale_btn)

        # Current scale display
        self.current_scale_label = QLabel("Scale: 1.0 x 1.0")
        utility_layout.addRow("Current Scale:", self.current_scale_label)

        layout.addWidget(utility_group)

        return panel

    def setup_menus(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save Tilemap", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_tilemap)
        file_menu.addAction(save_action)

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
        toolbar.addAction("Save", self.save_tilemap)

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

    def set_tilemap_node(self, tilemap_node: Dict[str, Any]):
        """Set the tilemap node to edit"""
        self.tilemap_node = tilemap_node
        self.canvas.set_tilemap_node(tilemap_node)
        self.update_layers_list()
        self.load_tileset()

    def load_tileset(self):
        """Load the tileset for the tilemap"""
        tilesets = self.tilemap_node.get("tilesets", [])
        if not tilesets:
            # Check legacy tileset property
            tileset_path = self.tilemap_node.get("tileset", "")
            if tileset_path:
                tilesets = [tileset_path]

        if tilesets:
            tileset_path = tilesets[0]  # Use first tileset for now
            self.tileset_path_edit.setText(tileset_path)

            # Load tileset
            tileset_manager = get_tileset_manager()
            full_path = self.project.project_path / tileset_path
            self.current_tileset = tileset_manager.load_tileset(str(full_path))

            if self.current_tileset:
                self.canvas.set_current_tileset(self.current_tileset)
                self.update_tile_palette()
            else:
                self.status_bar.showMessage(f"Failed to load tileset: {tileset_path}")

    def add_tileset(self):
        """Add a new tileset to the tilemap"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Tileset", "", "Tileset Files (*.tres);;All Files (*)"
        )
        if file_path:
            self.load_tileset_from_path(file_path)

    def load_tileset_from_path(self, file_path: str):
        """Load a tileset from a file path"""
        from core.tileset import get_tileset_manager

        tileset_manager = get_tileset_manager()
        tileset = tileset_manager.load_tileset(file_path)

        if tileset:
            # Add to canvas
            self.canvas.set_current_tileset(tileset)

            # Add to tilemap node tilesets list
            tilesets = self.tilemap_node.setdefault("tilesets", [])
            if file_path not in tilesets:
                tilesets.append(file_path)

            # Update UI
            self.update_tileset_combo()
            self.update_tile_palette()
            self.status_bar.showMessage(f"Added tileset: {tileset.name}")
        else:
            QMessageBox.warning(self, "Error", f"Failed to load tileset: {file_path}")

    def remove_tileset(self):
        """Remove the current tileset from the tilemap"""
        current_index = self.tileset_combo.currentIndex()
        if current_index >= 0 and len(self.canvas.tilesets) > 1:
            # Remove from canvas
            removed_tileset = self.canvas.tilesets.pop(current_index)
            if current_index in self.canvas.tileset_textures:
                del self.canvas.tileset_textures[current_index]

            # Update tilemap node
            tileset_paths = self.tilemap_node.get("tilesets", [])
            if current_index < len(tileset_paths):
                tileset_paths.pop(current_index)
                self.tilemap_node["tilesets"] = tileset_paths

            # Update UI
            self.update_tileset_combo()

            # Set new current tileset
            if self.canvas.tilesets:
                self.canvas.current_tileset = self.canvas.tilesets[0]
                self.canvas.current_tileset_index = 0
                self.update_tile_palette()

    def on_tileset_changed(self, index: int):
        """Handle tileset selection change"""
        if 0 <= index < len(self.canvas.tilesets):
            self.canvas.current_tileset = self.canvas.tilesets[index]
            self.canvas.current_tileset_index = index
            self.update_tile_palette()

    def update_tileset_combo(self):
        """Update the tileset combo box"""
        self.tileset_combo.clear()
        for i, tileset in enumerate(self.canvas.tilesets):
            name = tileset.name if tileset.name else f"Tileset {i}"
            self.tileset_combo.addItem(name)

        # Set current selection
        if self.canvas.current_tileset_index < self.tileset_combo.count():
            self.tileset_combo.setCurrentIndex(self.canvas.current_tileset_index)

    def update_tile_palette(self):
        """Update the tile palette with tiles from current tileset"""
        self.tile_palette.clear()

        if not self.current_tileset:
            return

        # Load tileset texture for previews
        tileset_texture = None
        if self.current_tileset.texture_path:
            from PyQt6.QtGui import QPixmap
            texture_path = self.project.project_path / self.current_tileset.texture_path
            if texture_path.exists():
                tileset_texture = QPixmap(str(texture_path))

        # Sort tiles by ID for consistent ordering
        sorted_tiles = sorted(self.current_tileset.tiles.items())

        for tile_id, tile_def in sorted_tiles:
            # Create item with no text (image only)
            item = QListWidgetItem("")
            item.setData(Qt.ItemDataRole.UserRole, tile_id)

            # Create tile preview icon
            if tileset_texture and not tileset_texture.isNull():
                tile_rect = tile_def.texture_rect
                # Extract tile from texture
                tile_pixmap = tileset_texture.copy(
                    tile_rect[0], tile_rect[1],
                    tile_rect[2], tile_rect[3]
                )

                # Scale to fit in palette (48x48 for better visibility)
                if not tile_pixmap.isNull():
                    scaled_pixmap = tile_pixmap.scaled(
                        48, 48,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    from PyQt6.QtGui import QIcon
                    item.setIcon(QIcon(scaled_pixmap))
            else:
                # Fallback: create a colored square icon
                from PyQt6.QtGui import QIcon, QPixmap
                fallback_pixmap = QPixmap(48, 48)
                hue = (tile_id * 137) % 360
                color = QColor.fromHsv(hue, 180, 200)
                fallback_pixmap.fill(color)
                item.setIcon(QIcon(fallback_pixmap))

            # Add tooltip with tile info
            tooltip_text = f"Tile ID: {tile_id}\nName: {tile_def.name}"
            if tile_def.tags:
                tooltip_text += f"\nTags: {', '.join(tile_def.tags)}"
            if tile_def.collision_shapes:
                tooltip_text += f"\nCollision shapes: {len(tile_def.collision_shapes)}"
            item.setToolTip(tooltip_text)

            self.tile_palette.addItem(item)

    def update_layers_list(self):
        """Update the layers list"""
        self.layers_list.clear()

        layers = self.tilemap_node.get("layers", [])
        for i, layer in enumerate(layers):
            item = QListWidgetItem(layer.get("name", f"Layer {i}"))
            item.setData(Qt.ItemDataRole.UserRole, i)
            if not layer.get("visible", True):
                item.setForeground(QColor(128, 128, 128))
            self.layers_list.addItem(item)

        # Select current layer
        current_layer = self.tilemap_node.get("current_layer", 0)
        if 0 <= current_layer < self.layers_list.count():
            self.layers_list.setCurrentRow(current_layer)

    # Event handlers
    def on_tile_painted(self, x: int, y: int, layer: int, tile_data: Dict[str, Any]):
        """Handle tile painting"""
        if not self.tilemap_node:
            return

        # Update tilemap node data
        tiles = self.tilemap_node.setdefault("tiles", {})
        layer_key = str(layer)
        layer_tiles = tiles.setdefault(layer_key, {})

        pos_key = f"{x},{y}"
        if tile_data and tile_data.get("tile_id", -1) >= 0:
            layer_tiles[pos_key] = tile_data
        else:
            # Remove tile
            if pos_key in layer_tiles:
                del layer_tiles[pos_key]

        # Update canvas with new tilemap data
        self.canvas.set_tilemap_node(self.tilemap_node)
        self.canvas.update()

        # Mark as modified
        self.status_bar.showMessage(f"Painted tile at ({x}, {y}) on layer {layer}")

    def on_layer_selected(self):
        """Handle layer selection"""
        current_item = self.layers_list.currentItem()
        if current_item:
            layer_index = current_item.data(Qt.ItemDataRole.UserRole)
            self.canvas.set_current_layer(layer_index)
            self.tilemap_node["current_layer"] = layer_index

    def on_tile_selected(self):
        """Handle tile selection from palette"""
        current_item = self.tile_palette.currentItem()
        if current_item:
            tile_id = current_item.data(Qt.ItemDataRole.UserRole)
            self.canvas.set_current_tile(tile_id)
            self.status_bar.showMessage(f"Selected tile {tile_id}")

    def set_paint_mode(self, mode: str):
        """Set the painting mode"""
        self.canvas.set_paint_mode(mode)
        self.status_bar.showMessage(f"Paint mode: {mode}")

    # Layer management
    def add_layer(self):
        """Add a new layer"""
        layers = self.tilemap_node.setdefault("layers", [])
        if len(layers) >= 20:  # Max layers limit
            QMessageBox.warning(self, "Warning", "Maximum of 20 layers allowed.")
            return

        layer_name = f"Layer {len(layers)}"
        new_layer = {
            "name": layer_name,
            "visible": True,
            "opacity": 1.0,
            "z_index": len(layers)
        }

        layers.append(new_layer)

        # Initialize layer tiles
        tiles = self.tilemap_node.setdefault("tiles", {})
        tiles[str(len(layers) - 1)] = {}

        self.update_layers_list()
        self.status_bar.showMessage(f"Added {layer_name}")

    def remove_layer(self):
        """Remove the selected layer"""
        current_item = self.layers_list.currentItem()
        if not current_item:
            return

        layers = self.tilemap_node.get("layers", [])
        if len(layers) <= 1:
            QMessageBox.warning(self, "Warning", "Cannot remove the last layer.")
            return

        layer_index = current_item.data(Qt.ItemDataRole.UserRole)
        layer_name = layers[layer_index].get("name", f"Layer {layer_index}")

        # Confirm removal
        reply = QMessageBox.question(
            self, "Remove Layer",
            f"Are you sure you want to remove '{layer_name}'?\nThis will delete all tiles on this layer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove layer
            del layers[layer_index]

            # Remove layer tiles and reindex
            tiles = self.tilemap_node.get("tiles", {})
            new_tiles = {}
            for i, layer in enumerate(layers):
                old_key = str(i + 1 if i >= layer_index else i)
                if old_key in tiles:
                    new_tiles[str(i)] = tiles[old_key]

            self.tilemap_node["tiles"] = new_tiles

            # Update current layer
            current_layer = self.tilemap_node.get("current_layer", 0)
            if current_layer >= len(layers):
                self.tilemap_node["current_layer"] = len(layers) - 1

            self.update_layers_list()
            self.canvas.update()
            self.status_bar.showMessage(f"Removed {layer_name}")

    # Tileset management
    def browse_tileset(self):
        """Browse for a tileset file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Tileset",
            str(self.project.project_path / "assets"),
            "Tileset Files (*.tres *.json);;All Files (*)"
        )

        if file_path:
            # Convert to relative path
            try:
                relative_path = Path(file_path).relative_to(self.project.project_path)
                self.tileset_path_edit.setText(str(relative_path))

                # Update tilemap node
                tilesets = self.tilemap_node.setdefault("tilesets", [])
                if str(relative_path) not in tilesets:
                    tilesets.clear()  # For now, only support one tileset
                    tilesets.append(str(relative_path))

                # Load the tileset
                self.load_tileset()

            except ValueError:
                QMessageBox.warning(self, "Warning", "Please select a tileset within the project folder.")

    def open_tileset_editor(self):
        """Open the tileset editor"""
        try:
            # Get the main editor window
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'open_tileset_editor'):
                main_window = main_window.parent()

            if main_window:
                main_window.open_tileset_editor()
            else:
                QMessageBox.information(self, "Info", "Tileset editor not available from this context.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open tileset editor: {e}")

    # Map property updates
    def update_cell_size(self):
        """Update cell size"""
        self.tilemap_node["cell_size"] = [
            self.cell_width_spin.value(),
            self.cell_height_spin.value()
        ]
        self.canvas.update()

    def update_map_size_mode(self, mode: str):
        """Update map size mode"""
        self.tilemap_node["map_size_mode"] = mode
        # Enable/disable fixed size controls based on mode
        fixed_enabled = (mode == "fixed")
        self.map_width_spin.setEnabled(fixed_enabled)
        self.map_height_spin.setEnabled(fixed_enabled)

    def update_fixed_map_size(self):
        """Update fixed map size"""
        self.tilemap_node["fixed_map_size"] = [
            self.map_width_spin.value(),
            self.map_height_spin.value()
        ]

    def update_utility_scale(self):
        """Update the utility scale display"""
        self.update_scale_display()

    def auto_calculate_scale(self):
        """Auto-calculate scale based on tile size in world space"""
        world_tile_size = self.world_tile_size_spin.value()
        current_cell_size = self.tilemap_node.get("cell_size", [32, 32])

        # Calculate scale factor
        scale_x = world_tile_size / current_cell_size[0]
        scale_y = world_tile_size / current_cell_size[1]

        # Update tilemap node scale
        self.tilemap_node["scale"] = [scale_x, scale_y]

        # Update display
        self.update_scale_display()

        # Update canvas
        self.canvas.update()

        self.status_bar.showMessage(f"Scale updated to {scale_x:.2f} x {scale_y:.2f}")

    def update_scale_display(self):
        """Update the scale display label"""
        scale = self.tilemap_node.get("scale", [1.0, 1.0])
        self.current_scale_label.setText(f"Scale: {scale[0]:.2f} x {scale[1]:.2f}")

        # Calculate effective tile size in world space
        cell_size = self.tilemap_node.get("cell_size", [32, 32])
        effective_size_x = cell_size[0] * scale[0]
        effective_size_y = cell_size[1] * scale[1]

        # Update world tile size spin box to match
        self.world_tile_size_spin.blockSignals(True)
        self.world_tile_size_spin.setValue(effective_size_x)
        self.world_tile_size_spin.blockSignals(False)

    # View controls
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.canvas.grid_visible = not self.canvas.grid_visible
        self.grid_checkbox.setChecked(self.canvas.grid_visible)
        self.canvas.update()

    def toggle_collision(self):
        """Toggle collision shapes visibility"""
        self.canvas.collision_visible = not self.canvas.collision_visible
        self.collision_checkbox.setChecked(self.canvas.collision_visible)
        self.canvas.update()

    def toggle_grid_checkbox(self, checked: bool):
        """Toggle grid visibility from checkbox"""
        self.canvas.grid_visible = checked
        self.canvas.update()

    def toggle_collision_checkbox(self, checked: bool):
        """Toggle collision visibility from checkbox"""
        self.canvas.collision_visible = checked
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

    def save_tilemap(self):
        """Save the tilemap changes"""
        # In a full implementation, this would save the tilemap node back to the scene
        # For now, just show a message
        self.status_bar.showMessage("Tilemap saved (changes applied to node)")
        QMessageBox.information(self, "Save", "Tilemap changes have been applied to the node.")

    def closeEvent(self, event):
        """Handle window close event"""
        # Could add unsaved changes check here
        event.accept()
