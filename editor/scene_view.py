"""
Scene View Widget for Lupine Engine
OpenGL-based scene viewport for visual editing
"""

import math
from typing import Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
import numpy as np

from core.project import LupineProject


class SceneViewWidget(QWidget):
    """Main scene view widget with controls and OpenGL viewport"""
    
    def __init__(self, project: LupineProject, scene_path: str, scene_data: Dict[str, Any]):
        super().__init__()
        self.project = project
        self.scene_path = scene_path
        self.scene_data = scene_data
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        # Controls bar with fixed height
        controls_widget = QWidget()
        controls_widget.setMaximumHeight(32)
        controls_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-bottom: 1px solid #555555;
            }
        """)

        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(8, 4, 8, 4)
        controls_layout.setSpacing(12)

        # Grid toggle
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.toggled.connect(self.toggle_grid)
        controls_layout.addWidget(self.grid_checkbox)

        # Game bounds toggle
        self.bounds_checkbox = QCheckBox("Show Game Bounds")
        self.bounds_checkbox.setChecked(True)
        self.bounds_checkbox.toggled.connect(self.toggle_bounds)
        controls_layout.addWidget(self.bounds_checkbox)

        controls_layout.addStretch()

        # Zoom info
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        controls_layout.addWidget(self.zoom_label)

        layout.addWidget(controls_widget)

        # OpenGL viewport
        self.viewport = SceneViewport(self.project, self.scene_data)
        self.viewport.zoom_changed.connect(self.update_zoom_label)
        layout.addWidget(self.viewport)
    
    def toggle_grid(self, enabled: bool):
        """Toggle grid display"""
        self.viewport.show_grid = enabled
        self.viewport.update()
    
    def toggle_bounds(self, enabled: bool):
        """Toggle game bounds display"""
        self.viewport.show_bounds = enabled
        self.viewport.update()
    
    def update_zoom_label(self, zoom: float):
        """Update zoom percentage label"""
        self.zoom_label.setText(f"Zoom: {int(zoom * 100)}%")


class SceneViewport(QOpenGLWidget):
    """OpenGL viewport for scene rendering"""
    
    zoom_changed = pyqtSignal(float)
    node_selected = pyqtSignal(dict)
    
    def __init__(self, project: LupineProject, scene_data: Dict[str, Any]):
        super().__init__()
        self.project = project
        self.scene_data = scene_data
        
        # View settings
        self.zoom = 2.0  # Start more zoomed in
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.show_grid = True
        self.show_bounds = True

        # Game bounds (16:9 aspect ratio)
        self.game_width = 1920  # 16:9 aspect ratio
        self.game_height = 1080

        # View area should be square for proper grid display
        # Use the larger dimension to make it square
        max_dimension = max(self.game_width, self.game_height) * 3
        self.view_width = max_dimension
        self.view_height = max_dimension
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.is_panning = False
        self.selected_node = None
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # Update timer for animations
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(16)  # ~60 FPS
    
    def initializeGL(self):
        """Initialize OpenGL"""
        glClearColor(0.2, 0.2, 0.2, 1.0)  # Dark gray background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    
    def resizeGL(self, width: int, height: int):
        """Handle viewport resize"""
        glViewport(0, 0, width, height)
        self.setup_projection()
    
    def setup_projection(self):
        """Setup projection matrix"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        # Calculate aspect ratio
        width = self.width()
        height = self.height()
        if height == 0:
            height = 1
        
        aspect = width / height
        
        # Set orthographic projection
        view_half_width = (self.view_width / 2) / self.zoom
        view_half_height = (self.view_height / 2) / self.zoom
        
        if aspect > 1:
            view_half_width *= aspect
        else:
            view_half_height /= aspect
        
        glOrtho(
            -view_half_width + self.pan_x, view_half_width + self.pan_x,
            -view_half_height + self.pan_y, view_half_height + self.pan_y,
            -1, 1
        )
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def paintGL(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT)
        
        self.setup_projection()
        
        # Draw grid
        if self.show_grid:
            self.draw_grid()
        
        # Draw game bounds
        if self.show_bounds:
            self.draw_game_bounds()
        
        # Draw scene nodes
        self.draw_scene_nodes()
        
        # Draw origin
        self.draw_origin()
    
    def draw_grid(self):
        """Draw background grid"""
        glColor3f(0.25, 0.25, 0.25)  # Slightly darker grid
        glBegin(GL_LINES)

        # Calculate grid spacing based on zoom - larger base spacing
        base_spacing = 100  # Larger base grid
        spacing = base_spacing

        # Adjust spacing based on zoom level for better visibility
        while spacing * self.zoom < 20:
            spacing *= 2
        while spacing * self.zoom > 200:
            spacing /= 2

        # Calculate visible area - extend beyond view bounds for full coverage
        view_half_width = (self.view_width / 2) / self.zoom
        view_half_height = (self.view_height / 2) / self.zoom

        # Extend grid beyond visible area
        margin = max(view_half_width, view_half_height) * 0.5
        left = -view_half_width + self.pan_x - margin
        right = view_half_width + self.pan_x + margin
        bottom = -view_half_height + self.pan_y - margin
        top = view_half_height + self.pan_y + margin

        # Vertical lines
        start_x = int(left / spacing) * spacing
        x = start_x
        while x <= right:
            glVertex2f(x, bottom)
            glVertex2f(x, top)
            x += spacing

        # Horizontal lines
        start_y = int(bottom / spacing) * spacing
        y = start_y
        while y <= top:
            glVertex2f(left, y)
            glVertex2f(right, y)
            y += spacing

        glEnd()

        # Draw major grid lines (every 5th line)
        glColor3f(0.35, 0.35, 0.35)  # Slightly brighter for major lines
        glBegin(GL_LINES)

        major_spacing = spacing * 5

        # Major vertical lines
        start_x = int(left / major_spacing) * major_spacing
        x = start_x
        while x <= right:
            glVertex2f(x, bottom)
            glVertex2f(x, top)
            x += major_spacing

        # Major horizontal lines
        start_y = int(bottom / major_spacing) * major_spacing
        y = start_y
        while y <= top:
            glVertex2f(left, y)
            glVertex2f(right, y)
            y += major_spacing

        glEnd()
    
    def draw_game_bounds(self):
        """Draw game screen bounds"""
        glColor3f(0.8, 0.5, 0.2)  # Orange color
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        
        half_width = self.game_width / 2
        half_height = self.game_height / 2
        
        glVertex2f(-half_width, -half_height)
        glVertex2f(half_width, -half_height)
        glVertex2f(half_width, half_height)
        glVertex2f(-half_width, half_height)
        
        glEnd()
        glLineWidth(1.0)
    
    def draw_origin(self):
        """Draw coordinate system origin"""
        glLineWidth(2.0)
        
        # X axis (red)
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex2f(0, 0)
        glVertex2f(50, 0)
        glEnd()
        
        # Y axis (green)
        glColor3f(0.0, 1.0, 0.0)
        glBegin(GL_LINES)
        glVertex2f(0, 0)
        glVertex2f(0, 50)
        glEnd()
        
        glLineWidth(1.0)
    
    def draw_scene_nodes(self):
        """Draw scene nodes"""
        if not self.scene_data:
            return
        
        nodes = self.scene_data.get("nodes", [])
        for node in nodes:
            self.draw_node(node)
    
    def draw_node(self, node_data: Dict[str, Any]):
        """Draw a single node"""
        node_type = node_data.get("type", "Node")
        position = node_data.get("position", [0, 0])
        
        glPushMatrix()
        glTranslatef(position[0], position[1], 0)
        
        # Draw based on node type
        if node_type == "Node2D":
            self.draw_node2d(node_data)
        elif node_type == "Sprite":
            self.draw_sprite(node_data)
        elif node_type == "Camera2D":
            self.draw_camera(node_data)
        else:
            # Default node representation
            self.draw_default_node(node_data)
        
        # Draw children
        children = node_data.get("children", [])
        for child in children:
            self.draw_node(child)
        
        glPopMatrix()
    
    def draw_node2d(self, node_data: Dict[str, Any]):
        """Draw Node2D"""
        # Draw as a small cross
        glColor3f(0.7, 0.7, 0.7)
        glBegin(GL_LINES)
        glVertex2f(-10, 0)
        glVertex2f(10, 0)
        glVertex2f(0, -10)
        glVertex2f(0, 10)
        glEnd()
    
    def draw_sprite(self, node_data: Dict[str, Any]):
        """Draw Sprite node - Godot Sprite2D equivalent"""
        # Get sprite properties
        texture = node_data.get("texture", "")
        centered = node_data.get("centered", True)
        offset = node_data.get("offset", [0.0, 0.0])
        flip_h = node_data.get("flip_h", False)
        flip_v = node_data.get("flip_v", False)
        hframes = node_data.get("hframes", 1)
        vframes = node_data.get("vframes", 1)
        frame = node_data.get("frame", 0)

        # Calculate frame size (default 64x64 if no texture)
        base_size = [64, 64]
        frame_width = base_size[0] / hframes
        frame_height = base_size[1] / vframes

        # Calculate position
        pos_x = offset[0]
        pos_y = offset[1]

        if centered:
            pos_x -= frame_width / 2
            pos_y -= frame_height / 2

        # Draw sprite rectangle
        if texture:
            glColor3f(0.2, 0.8, 0.2)  # Green for textured sprites
        else:
            glColor3f(0.8, 0.8, 0.2)  # Yellow for sprites without texture

        # Apply flipping by adjusting coordinates
        left = pos_x
        right = pos_x + frame_width
        bottom = pos_y
        top = pos_y + frame_height

        if flip_h:
            left, right = right, left
        if flip_v:
            bottom, top = top, bottom

        glBegin(GL_LINE_LOOP)
        glVertex2f(left, bottom)
        glVertex2f(right, bottom)
        glVertex2f(right, top)
        glVertex2f(left, top)
        glEnd()

        # Draw frame indicator if using sprite sheet
        if hframes > 1 or vframes > 1:
            glColor3f(1.0, 0.5, 0.0)  # Orange for frame indicator
            glBegin(GL_LINES)

            # Draw frame grid
            for i in range(1, hframes):
                x = pos_x + (i * frame_width)
                glVertex2f(x, pos_y)
                glVertex2f(x, pos_y + frame_height)

            for i in range(1, vframes):
                y = pos_y + (i * frame_height)
                glVertex2f(pos_x, y)
                glVertex2f(pos_x + frame_width, y)

            glEnd()

            # Highlight current frame
            current_frame_x = (frame % hframes) * frame_width + pos_x
            current_frame_y = (frame // hframes) * frame_height + pos_y

            glColor3f(1.0, 0.0, 0.0)  # Red for current frame
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(current_frame_x, current_frame_y)
            glVertex2f(current_frame_x + frame_width, current_frame_y)
            glVertex2f(current_frame_x + frame_width, current_frame_y + frame_height)
            glVertex2f(current_frame_x, current_frame_y + frame_height)
            glEnd()
            glLineWidth(1.0)

        # Draw texture name if available
        if texture:
            # This would be rendered as text in a real implementation
            pass
    
    def draw_camera(self, node_data: Dict[str, Any]):
        """Draw Camera2D node"""
        # Draw camera icon
        glColor3f(0.8, 0.8, 0.2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(-20, -15)
        glVertex2f(20, -15)
        glVertex2f(20, 15)
        glVertex2f(-20, 15)
        glEnd()
        
        # Camera "lens"
        glBegin(GL_LINE_LOOP)
        glVertex2f(-10, -8)
        glVertex2f(10, -8)
        glVertex2f(10, 8)
        glVertex2f(-10, 8)
        glEnd()
    
    def draw_default_node(self, node_data: Dict[str, Any]):
        """Draw default node representation"""
        # Draw as a small circle
        glColor3f(0.6, 0.6, 0.8)
        glBegin(GL_LINE_LOOP)
        for i in range(16):
            angle = 2 * math.pi * i / 16
            x = 8 * math.cos(angle)
            y = 8 * math.sin(angle)
            glVertex2f(x, y)
        glEnd()
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 1.0 / 1.1
        
        self.zoom *= zoom_factor
        self.zoom = max(0.1, min(10.0, self.zoom))  # Clamp zoom
        
        self.zoom_changed.emit(self.zoom)
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        self.last_mouse_pos = event.position()
        
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
        elif event.button() == Qt.MouseButton.LeftButton:
            # TODO: Implement node selection
            pass
    
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        if self.last_mouse_pos is None:
            self.last_mouse_pos = event.position()
            return
        
        if self.is_panning:
            delta_x = event.position().x() - self.last_mouse_pos.x()
            delta_y = event.position().y() - self.last_mouse_pos.y()
            
            # Convert screen delta to world delta
            scale = (self.view_width / self.width()) / self.zoom
            self.pan_x -= delta_x * scale
            self.pan_y += delta_y * scale  # Flip Y axis
            
            self.update()
        
        self.last_mouse_pos = event.position()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
