"""
Scene View Widget for Lupine Engine
OpenGL-based scene viewport for visual editing
"""

import math
from typing import Dict, Any, Optional, Tuple
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QImage
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
import numpy as np
from pathlib import Path

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
    node_modified = pyqtSignal(dict, str, object)  # node, property_name, value
    
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
        self.is_dragging = False
        self.is_rotating = False
        self.is_scaling = False
        self.drag_start_pos = None
        self.drag_start_node_pos = None

        # Gizmo settings
        self.gizmo_size = 8
        self.rotation_handle_distance = 50

        # Texture cache
        self.texture_cache = {}  # path -> texture_id

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
        glEnable(GL_TEXTURE_2D)
    
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

        # Draw selection and gizmos
        if self.selected_node:
            self.draw_selection_gizmos()

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

    def load_texture(self, texture_path: str) -> Optional[Tuple[int, int, int]]:
        """Load a texture from file and return (texture_id, width, height)"""
        if not texture_path:
            return None

        # Check cache first
        if texture_path in self.texture_cache:
            return self.texture_cache[texture_path]

        try:
            # Convert to absolute path
            if not Path(texture_path).is_absolute():
                full_path = self.project.get_absolute_path(texture_path)
            else:
                full_path = Path(texture_path)

            if not full_path.exists():
                print(f"Texture file not found: {full_path}")
                return None

            # Use PIL/Pillow for more reliable image loading
            from PIL import Image

            # Load image using PIL
            pil_image = Image.open(str(full_path))

            # Convert to RGBA if not already
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')

            # Get image data
            width, height = pil_image.size
            image_data = pil_image.tobytes()

            # Flip image vertically for OpenGL (PIL loads top-to-bottom, OpenGL expects bottom-to-top)
            pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)
            image_data = pil_image.tobytes()

            # Generate OpenGL texture
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)

            # Set texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            # Upload texture data
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
                        0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)

            glBindTexture(GL_TEXTURE_2D, 0)

            # Cache the texture with size info
            texture_info = (texture_id, width, height)
            self.texture_cache[texture_path] = texture_info

            print(f"Successfully loaded texture: {texture_path} ({width}x{height})")
            return texture_info

        except Exception as e:
            print(f"Error loading texture {texture_path}: {e}")
            # Fallback to QImage method if PIL fails
            try:
                return self._load_texture_qimage_fallback(full_path)
            except Exception as e2:
                print(f"Fallback texture loading also failed: {e2}")
                return None

    def _load_texture_qimage_fallback(self, full_path) -> Optional[Tuple[int, int, int]]:
        """Fallback texture loading using QImage with proper data conversion"""
        try:
            # Load image using QImage
            image = QImage(str(full_path))
            if image.isNull():
                print(f"Failed to load image with QImage: {full_path}")
                return None

            # Convert to OpenGL format
            image = image.convertToFormat(QImage.Format.Format_RGBA8888)
            image = image.mirrored(False, True)  # Flip vertically for OpenGL

            # Convert QImage data to bytes properly
            width = image.width()
            height = image.height()

            # Get image data as bytes - this is the key fix
            ptr = image.constBits()
            ptr.setsize(width * height * 4)  # 4 bytes per pixel (RGBA)
            image_data = bytes(ptr)

            # Generate OpenGL texture
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)

            # Set texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            # Upload texture data
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
                        0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)

            glBindTexture(GL_TEXTURE_2D, 0)

            # Cache the texture with size info
            texture_info = (texture_id, width, height)

            print(f"Successfully loaded texture with QImage fallback: {full_path} ({width}x{height})")
            return texture_info

        except Exception as e:
            print(f"QImage fallback failed: {e}")
            return None

    def draw_textured_quad(self, texture_id: int, left: float, bottom: float,
                          right: float, top: float):
        """Draw a textured quad"""
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor3f(1.0, 1.0, 1.0)  # White to show texture as-is

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(left, bottom)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(right, bottom)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(right, top)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(left, top)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

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

        # Apply flipping by adjusting coordinates
        left = pos_x
        right = pos_x + frame_width
        bottom = pos_y
        top = pos_y + frame_height

        if flip_h:
            left, right = right, left
        if flip_v:
            bottom, top = top, bottom

        # Draw sprite
        if texture:
            # Try to load and render texture
            texture_info = self.load_texture(texture)
            if texture_info:
                texture_id, tex_width, tex_height = texture_info

                # Use actual texture size instead of default 64x64
                frame_width = tex_width / hframes
                frame_height = tex_height / vframes

                # Recalculate position with actual texture size
                pos_x = offset[0]
                pos_y = offset[1]

                if centered:
                    pos_x -= frame_width / 2
                    pos_y -= frame_height / 2

                # Recalculate coordinates with actual size
                left = pos_x
                right = pos_x + frame_width
                bottom = pos_y
                top = pos_y + frame_height

                if flip_h:
                    left, right = right, left
                if flip_v:
                    bottom, top = top, bottom

                # Draw textured quad
                self.draw_textured_quad(texture_id, left, bottom, right, top)
            else:
                # Fallback to wireframe if texture loading failed
                glColor3f(1.0, 0.0, 0.0)  # Red for failed texture
                glBegin(GL_LINE_LOOP)
                glVertex2f(left, bottom)
                glVertex2f(right, bottom)
                glVertex2f(right, top)
                glVertex2f(left, top)
                glEnd()
        else:
            # Draw wireframe for sprites without texture
            glColor3f(0.8, 0.8, 0.2)  # Yellow for sprites without texture
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
            # Convert screen coordinates to world coordinates
            world_pos = self.screen_to_world(event.position().x(), event.position().y())

            # Check for gizmo interaction first
            if self.selected_node:
                gizmo_type = self.check_gizmo_hit(world_pos[0], world_pos[1])
                if gizmo_type:
                    if gizmo_type == "move":
                        self.is_dragging = True
                    elif gizmo_type == "rotate":
                        self.is_rotating = True
                    elif gizmo_type == "scale":
                        self.is_scaling = True

                    self.drag_start_pos = world_pos
                    self.drag_start_node_pos = self.selected_node.get("position", [0, 0]).copy()
                    return

            # Check for node selection
            clicked_node = self.get_node_at_position(world_pos[0], world_pos[1])
            if clicked_node:
                self.selected_node = clicked_node
                self.node_selected.emit(clicked_node)
                self.is_dragging = True
                self.drag_start_pos = world_pos
                self.drag_start_node_pos = clicked_node.get("position", [0, 0]).copy()
            else:
                self.selected_node = None

            self.update()
    
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
        elif self.is_dragging and self.selected_node:
            # Handle node dragging
            world_pos = self.screen_to_world(event.position().x(), event.position().y())

            if self.drag_start_pos:
                delta_x = world_pos[0] - self.drag_start_pos[0]
                delta_y = world_pos[1] - self.drag_start_pos[1]

                new_pos = [
                    self.drag_start_node_pos[0] + delta_x,
                    self.drag_start_node_pos[1] + delta_y
                ]

                self.selected_node["position"] = new_pos
                # Emit signal for inspector update
                self.node_modified.emit(self.selected_node, "position", new_pos)
                self.update()

        self.last_mouse_pos = event.position()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
        elif event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.is_rotating = False
            self.is_scaling = False
            self.drag_start_pos = None
            self.drag_start_node_pos = None

    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        # Get viewport dimensions
        width = self.width()
        height = self.height()

        # Convert to normalized device coordinates (-1 to 1)
        ndc_x = (2.0 * screen_x / width) - 1.0
        ndc_y = 1.0 - (2.0 * screen_y / height)  # Flip Y axis

        # Calculate view dimensions
        aspect = width / height if height > 0 else 1.0
        view_half_width = (self.view_width / 2) / self.zoom
        view_half_height = (self.view_height / 2) / self.zoom

        # Adjust for aspect ratio
        if aspect > 1.0:
            view_half_width *= aspect
        else:
            view_half_height /= aspect

        # Convert to world coordinates
        world_x = ndc_x * view_half_width + self.pan_x
        world_y = ndc_y * view_half_height + self.pan_y

        return (world_x, world_y)

    def get_node_at_position(self, world_x: float, world_y: float) -> Optional[Dict[str, Any]]:
        """Find the node at the given world position"""
        if not self.scene_data:
            return None

        nodes = self.scene_data.get("nodes", [])
        return self._check_node_hit(nodes, world_x, world_y)

    def _check_node_hit(self, nodes: list, world_x: float, world_y: float) -> Optional[Dict[str, Any]]:
        """Recursively check if any node is hit by the given position"""
        # Check nodes in reverse order (top to bottom in rendering)
        for node in reversed(nodes):
            # Check children first (they render on top)
            children = node.get("children", [])
            if children:
                hit_child = self._check_node_hit(children, world_x, world_y)
                if hit_child:
                    return hit_child

            # Check this node
            if self._is_point_in_node(node, world_x, world_y):
                return node

        return None

    def _is_point_in_node(self, node: Dict[str, Any], world_x: float, world_y: float) -> bool:
        """Check if a point is inside a node's bounds"""
        position = node.get("position", [0, 0])
        node_type = node.get("type", "Node")

        # Adjust coordinates relative to node position
        local_x = world_x - position[0]
        local_y = world_y - position[1]

        if node_type == "Sprite":
            # Check sprite bounds
            centered = node.get("centered", True)
            offset = node.get("offset", [0.0, 0.0])

            # Default sprite size
            frame_width = 64
            frame_height = 64

            # Calculate bounds
            if centered:
                left = offset[0] - frame_width / 2
                right = offset[0] + frame_width / 2
                bottom = offset[1] - frame_height / 2
                top = offset[1] + frame_height / 2
            else:
                left = offset[0]
                right = offset[0] + frame_width
                bottom = offset[1]
                top = offset[1] + frame_height

            return left <= local_x <= right and bottom <= local_y <= top

        elif node_type == "Node2D":
            # Check small area around node center
            return abs(local_x) <= 10 and abs(local_y) <= 10

        else:
            # Default node hit area
            return abs(local_x) <= 8 and abs(local_y) <= 8

    def check_gizmo_hit(self, world_x: float, world_y: float) -> Optional[str]:
        """Check if a gizmo handle is hit"""
        if not self.selected_node:
            return None

        position = self.selected_node.get("position", [0, 0])
        local_x = world_x - position[0]
        local_y = world_y - position[1]

        # Check scale handles (corners)
        gizmo_size = self.gizmo_size
        if abs(local_x - 30) <= gizmo_size and abs(local_y - 30) <= gizmo_size:
            return "scale"
        if abs(local_x + 30) <= gizmo_size and abs(local_y - 30) <= gizmo_size:
            return "scale"
        if abs(local_x - 30) <= gizmo_size and abs(local_y + 30) <= gizmo_size:
            return "scale"
        if abs(local_x + 30) <= gizmo_size and abs(local_y + 30) <= gizmo_size:
            return "scale"

        # Check rotation handle
        rotation_distance = math.sqrt(local_x**2 + local_y**2)
        if abs(rotation_distance - self.rotation_handle_distance) <= gizmo_size:
            return "rotate"

        # Check move handle (center area)
        if abs(local_x) <= 15 and abs(local_y) <= 15:
            return "move"

        return None

    def draw_selection_gizmos(self):
        """Draw selection and transformation gizmos"""
        if not self.selected_node:
            return

        position = self.selected_node.get("position", [0, 0])

        glPushMatrix()
        glTranslatef(position[0], position[1], 0)

        # Draw selection outline
        glColor3f(1.0, 1.0, 0.0)  # Yellow selection
        glLineWidth(2.0)

        # Draw selection box around node
        node_type = self.selected_node.get("type", "Node")
        if node_type == "Sprite":
            # Draw around sprite bounds
            centered = self.selected_node.get("centered", True)
            offset = self.selected_node.get("offset", [0.0, 0.0])

            frame_width = 64
            frame_height = 64

            if centered:
                left = offset[0] - frame_width / 2
                right = offset[0] + frame_width / 2
                bottom = offset[1] - frame_height / 2
                top = offset[1] + frame_height / 2
            else:
                left = offset[0]
                right = offset[0] + frame_width
                bottom = offset[1]
                top = offset[1] + frame_height

            glBegin(GL_LINE_LOOP)
            glVertex2f(left, bottom)
            glVertex2f(right, bottom)
            glVertex2f(right, top)
            glVertex2f(left, top)
            glEnd()
        else:
            # Draw around node center
            glBegin(GL_LINE_LOOP)
            glVertex2f(-15, -15)
            glVertex2f(15, -15)
            glVertex2f(15, 15)
            glVertex2f(-15, 15)
            glEnd()

        # Draw transformation handles
        self.draw_move_gizmo()
        self.draw_scale_gizmos()
        self.draw_rotation_gizmo()

        glLineWidth(1.0)
        glPopMatrix()

    def draw_move_gizmo(self):
        """Draw move gizmo (center cross)"""
        glColor3f(0.0, 1.0, 0.0)  # Green for move
        glBegin(GL_LINES)
        glVertex2f(-10, 0)
        glVertex2f(10, 0)
        glVertex2f(0, -10)
        glVertex2f(0, 10)
        glEnd()

    def draw_scale_gizmos(self):
        """Draw scale gizmos (corner squares)"""
        glColor3f(0.0, 0.0, 1.0)  # Blue for scale
        size = self.gizmo_size

        # Corner positions
        corners = [
            (30, 30), (-30, 30), (30, -30), (-30, -30)
        ]

        for x, y in corners:
            glBegin(GL_LINE_LOOP)
            glVertex2f(x - size, y - size)
            glVertex2f(x + size, y - size)
            glVertex2f(x + size, y + size)
            glVertex2f(x - size, y + size)
            glEnd()

    def draw_rotation_gizmo(self):
        """Draw rotation gizmo (circle)"""
        glColor3f(1.0, 0.0, 0.0)  # Red for rotation
        glBegin(GL_LINE_LOOP)

        segments = 32
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = self.rotation_handle_distance * math.cos(angle)
            y = self.rotation_handle_distance * math.sin(angle)
            glVertex2f(x, y)

        glEnd()

    def update_node_property(self, node: Dict[str, Any], property_name: str, value):
        """Update a node property from inspector changes"""
        if node and property_name in node:
            node[property_name] = value
            self.update()

    def set_selected_node(self, node: Optional[Dict[str, Any]]):
        """Set the selected node from external source (like scene tree)"""
        self.selected_node = node
        self.update()
