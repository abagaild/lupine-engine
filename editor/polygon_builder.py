"""
Polygon Builder Tool for Lupine Engine
Godot-like polygon tracing and editing tool for collision shapes
"""

import math
from typing import List, Optional, Tuple, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSpinBox, QCheckBox, QGroupBox, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QCursor

from core.project import LupineProject


class PolygonBuilderWidget(QWidget):
    """Interactive polygon builder widget for creating collision polygons"""
    
    polygon_changed = pyqtSignal(list)  # Emitted when polygon points change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        
        # Polygon data
        self.polygon_points: List[List[float]] = []
        self.selected_point_index: Optional[int] = None
        self.is_editing: bool = False
        self.snap_to_grid: bool = True
        self.grid_size: int = 8
        
        # Mouse interaction
        self.last_mouse_pos: Optional[QPoint] = None
        self.is_dragging: bool = False
        
        # Visual settings
        self.point_radius = 6
        self.line_width = 2
        self.grid_color = QColor(100, 100, 100, 50)
        self.polygon_color = QColor(0, 150, 200, 100)
        self.point_color = QColor(255, 100, 100)
        self.selected_point_color = QColor(255, 255, 100)
        
        self.setMouseTracking(True)
        
    def set_polygon(self, points: List[List[float]]):
        """Set the polygon points"""
        self.polygon_points = [p.copy() for p in points]
        self.selected_point_index = None
        self.update()
        
    def get_polygon(self) -> List[List[float]]:
        """Get the current polygon points"""
        return [p.copy() for p in self.polygon_points]
        
    def clear_polygon(self):
        """Clear all polygon points"""
        self.polygon_points.clear()
        self.selected_point_index = None
        self.update()
        self.polygon_changed.emit(self.polygon_points)
        
    def set_snap_to_grid(self, enabled: bool):
        """Enable/disable grid snapping"""
        self.snap_to_grid = enabled
        
    def set_grid_size(self, size: int):
        """Set grid snap size"""
        self.grid_size = max(1, size)
        self.update()
        
    def _snap_to_grid(self, point: List[float]) -> List[float]:
        """Snap point to grid if enabled"""
        if not self.snap_to_grid:
            return point
        
        snapped_x = round(point[0] / self.grid_size) * self.grid_size
        snapped_y = round(point[1] / self.grid_size) * self.grid_size
        return [snapped_x, snapped_y]
        
    def _widget_to_polygon_coords(self, widget_pos: QPoint) -> List[float]:
        """Convert widget coordinates to polygon coordinates"""
        # Center the coordinate system
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        poly_x = widget_pos.x() - center_x
        poly_y = -(widget_pos.y() - center_y)  # Flip Y axis
        
        return [poly_x, poly_y]
        
    def _polygon_to_widget_coords(self, poly_pos: List[float]) -> QPoint:
        """Convert polygon coordinates to widget coordinates"""
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        widget_x = poly_pos[0] + center_x
        widget_y = -poly_pos[1] + center_y  # Flip Y axis
        
        return QPoint(int(widget_x), int(widget_y))
        
    def _find_point_at_position(self, pos: QPoint) -> Optional[int]:
        """Find polygon point at given position"""
        for i, point in enumerate(self.polygon_points):
            widget_pos = self._polygon_to_widget_coords(point)
            distance = math.sqrt((pos.x() - widget_pos.x())**2 + (pos.y() - widget_pos.y())**2)
            if distance <= self.point_radius + 2:
                return i
        return None
        
    def paintEvent(self, event):
        """Paint the polygon builder interface"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw grid
        if self.snap_to_grid:
            self._draw_grid(painter)
        
        # Draw coordinate axes
        self._draw_axes(painter)
        
        # Draw polygon
        if len(self.polygon_points) >= 2:
            self._draw_polygon(painter)
        
        # Draw points
        self._draw_points(painter)
        
    def _draw_grid(self, painter: QPainter):
        """Draw snap grid"""
        painter.setPen(QPen(self.grid_color, 1))
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Vertical lines
        x = center_x
        while x < self.width():
            painter.drawLine(int(x), 0, int(x), self.height())
            x += self.grid_size
        x = center_x - self.grid_size
        while x > 0:
            painter.drawLine(int(x), 0, int(x), self.height())
            x -= self.grid_size
            
        # Horizontal lines
        y = center_y
        while y < self.height():
            painter.drawLine(0, int(y), self.width(), int(y))
            y += self.grid_size
        y = center_y - self.grid_size
        while y > 0:
            painter.drawLine(0, int(y), self.width(), int(y))
            y -= self.grid_size
            
    def _draw_axes(self, painter: QPainter):
        """Draw coordinate axes"""
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # X axis
        painter.drawLine(0, int(center_y), self.width(), int(center_y))
        # Y axis
        painter.drawLine(int(center_x), 0, int(center_x), self.height())
        
    def _draw_polygon(self, painter: QPainter):
        """Draw the polygon"""
        if len(self.polygon_points) < 2:
            return
            
        # Create polygon for filling
        polygon = QPolygonF()
        for point in self.polygon_points:
            widget_pos = self._polygon_to_widget_coords(point)
            polygon.append(QPointF(widget_pos.x(), widget_pos.y()))
        
        # Fill polygon
        painter.setBrush(QBrush(self.polygon_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(polygon)
        
        # Draw polygon outline
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(self.polygon_color.darker(150), self.line_width))
        painter.drawPolygon(polygon)
        
    def _draw_points(self, painter: QPainter):
        """Draw polygon points"""
        for i, point in enumerate(self.polygon_points):
            widget_pos = self._polygon_to_widget_coords(point)
            
            # Choose color based on selection
            if i == self.selected_point_index:
                color = self.selected_point_color
            else:
                color = self.point_color
                
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(150), 2))
            painter.drawEllipse(
                widget_pos.x() - self.point_radius,
                widget_pos.y() - self.point_radius,
                self.point_radius * 2,
                self.point_radius * 2
            )
            
    def mousePressEvent(self, event):
        """Handle mouse press for point creation/selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking on existing point
            point_index = self._find_point_at_position(event.position().toPoint())
            
            if point_index is not None:
                # Select existing point
                self.selected_point_index = point_index
                self.is_dragging = True
            else:
                # Create new point
                poly_pos = self._widget_to_polygon_coords(event.position().toPoint())
                snapped_pos = self._snap_to_grid(poly_pos)
                
                self.polygon_points.append(snapped_pos)
                self.selected_point_index = len(self.polygon_points) - 1
                self.polygon_changed.emit(self.polygon_points)
                
            self.last_mouse_pos = event.position().toPoint()
            self.update()
            
        elif event.button() == Qt.MouseButton.RightButton:
            # Delete point
            point_index = self._find_point_at_position(event.position().toPoint())
            if point_index is not None and len(self.polygon_points) > 0:
                del self.polygon_points[point_index]
                if self.selected_point_index == point_index:
                    self.selected_point_index = None
                elif self.selected_point_index is not None and self.selected_point_index > point_index:
                    self.selected_point_index -= 1
                self.polygon_changed.emit(self.polygon_points)
                self.update()
                
    def mouseMoveEvent(self, event):
        """Handle mouse move for point dragging"""
        if self.is_dragging and self.selected_point_index is not None:
            poly_pos = self._widget_to_polygon_coords(event.position().toPoint())
            snapped_pos = self._snap_to_grid(poly_pos)
            
            self.polygon_points[self.selected_point_index] = snapped_pos
            self.polygon_changed.emit(self.polygon_points)
            self.update()
            
        # Update cursor
        point_index = self._find_point_at_position(event.position().toPoint())
        if point_index is not None:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            
        self.last_mouse_pos = event.position().toPoint()
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False


class PolygonBuilderDialog(QDialog):
    """Dialog for building and editing collision polygons"""

    def __init__(self, initial_polygon: Optional[List[List[float]]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Polygon Builder")
        self.setModal(True)
        self.resize(600, 500)

        self.setup_ui()

        if initial_polygon:
            self.polygon_widget.set_polygon(initial_polygon)

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Left click: Add/select point\n"
            "Right click: Delete point\n"
            "Drag: Move selected point"
        )
        instructions.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(instructions)

        # Main polygon builder widget
        self.polygon_widget = PolygonBuilderWidget()
        self.polygon_widget.polygon_changed.connect(self.on_polygon_changed)
        layout.addWidget(self.polygon_widget)

        # Controls
        controls_layout = QHBoxLayout()

        # Grid controls
        grid_group = QGroupBox("Grid")
        grid_layout = QHBoxLayout(grid_group)

        self.snap_checkbox = QCheckBox("Snap to Grid")
        self.snap_checkbox.setChecked(True)
        self.snap_checkbox.toggled.connect(self.polygon_widget.set_snap_to_grid)
        grid_layout.addWidget(self.snap_checkbox)

        grid_layout.addWidget(QLabel("Size:"))
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(1, 32)
        self.grid_size_spin.setValue(8)
        self.grid_size_spin.valueChanged.connect(self.polygon_widget.set_grid_size)
        grid_layout.addWidget(self.grid_size_spin)

        controls_layout.addWidget(grid_group)

        # Polygon operations
        ops_group = QGroupBox("Operations")
        ops_layout = QHBoxLayout(ops_group)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.polygon_widget.clear_polygon)
        ops_layout.addWidget(clear_btn)

        preset_btn = QPushButton("Rectangle")
        preset_btn.clicked.connect(self.create_rectangle_preset)
        ops_layout.addWidget(preset_btn)

        triangle_btn = QPushButton("Triangle")
        triangle_btn.clicked.connect(self.create_triangle_preset)
        ops_layout.addWidget(triangle_btn)

        controls_layout.addWidget(ops_group)

        layout.addLayout(controls_layout)

        # Point list
        self.point_list = QListWidget()
        self.point_list.setMaximumHeight(100)
        layout.addWidget(QLabel("Points:"))
        layout.addWidget(self.point_list)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_polygon_changed(self, points: List[List[float]]):
        """Handle polygon changes"""
        self.update_point_list(points)

    def update_point_list(self, points: List[List[float]]):
        """Update the point list display"""
        self.point_list.clear()
        for i, point in enumerate(points):
            item_text = f"Point {i}: ({point[0]:.1f}, {point[1]:.1f})"
            self.point_list.addItem(item_text)

    def create_rectangle_preset(self):
        """Create a rectangle preset"""
        rect_points = [
            [-32.0, -32.0],
            [32.0, -32.0],
            [32.0, 32.0],
            [-32.0, 32.0]
        ]
        self.polygon_widget.set_polygon(rect_points)

    def create_triangle_preset(self):
        """Create a triangle preset"""
        triangle_points = [
            [0.0, -32.0],
            [32.0, 32.0],
            [-32.0, 32.0]
        ]
        self.polygon_widget.set_polygon(triangle_points)

    def get_polygon(self) -> List[List[float]]:
        """Get the final polygon"""
        return self.polygon_widget.get_polygon()


class PolygonTracer:
    """Utility class for tracing polygons from sprites/images"""

    @staticmethod
    def trace_sprite_outline(sprite_path: str, threshold: int = 128) -> List[List[float]]:
        """
        Trace the outline of a sprite to create a collision polygon.
        This is a simplified version - a full implementation would use
        image processing to detect edges.
        """
        try:
            from PIL import Image
            import numpy as np

            # Load image
            image = Image.open(sprite_path).convert("RGBA")
            width, height = image.size

            # Convert to numpy array
            img_array = np.array(image)

            # Find non-transparent pixels
            alpha_channel = img_array[:, :, 3]
            non_transparent = alpha_channel > threshold

            # Find bounding box of non-transparent pixels
            rows = np.any(non_transparent, axis=1)
            cols = np.any(non_transparent, axis=0)

            if not np.any(rows) or not np.any(cols):
                # No non-transparent pixels, return default rectangle
                return [[-width/2, -height/2], [width/2, -height/2],
                       [width/2, height/2], [-width/2, height/2]]

            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]

            # Convert to polygon coordinates (centered)
            center_x, center_y = width / 2, height / 2

            # Create simplified polygon from bounding box
            # In a full implementation, this would trace the actual outline
            polygon = [
                [cmin - center_x, rmin - center_y],
                [cmax - center_x, rmin - center_y],
                [cmax - center_x, rmax - center_y],
                [cmin - center_x, rmax - center_y]
            ]

            return polygon

        except ImportError:
            print("PIL not available for sprite tracing")
            return [[-32, -32], [32, -32], [32, 32], [-32, 32]]
        except Exception as e:
            print(f"Error tracing sprite: {e}")
            return [[-32, -32], [32, -32], [32, 32], [-32, 32]]
