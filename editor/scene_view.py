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
from core.shared_renderer import SharedRenderer

# Import pygame for font rendering
try:
    import pygame
    pygame.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available, text rendering will be limited")


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

        # Load game bounds from project settings
        self.game_width, self.game_height = self._load_game_bounds_from_project()

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

        # Shared renderer for consistent rendering with game runner
        self.renderer = None  # Will be initialized in initializeGL

        # Texture cache (legacy - will be replaced by shared renderer)
        self.texture_cache = {}  # path -> texture_id

        # Font cache for text rendering (legacy - will be replaced by shared renderer)
        self.font_cache = {}  # (font_name, size) -> pygame.font.Font
        self.text_texture_cache = {}  # (text, font_name, size, color) -> texture_id

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

        # Initialize shared renderer for consistent rendering with game runner
        self.renderer = SharedRenderer(self.width(), self.height(), str(self.project.project_path), auto_setup_gl=False)

    def _load_game_bounds_from_project(self) -> tuple[int, int]:
        """Load game bounds from project settings"""
        try:
            project_file = self.project.project_path / "project.lupine"
            if project_file.exists():
                import json
                with open(project_file, 'r') as f:
                    project_data = json.load(f)

                display_settings = project_data.get("settings", {}).get("display", {})
                width = display_settings.get("width", 1920)  # Default to 1920x1080 if not set
                height = display_settings.get("height", 1080)

                print(f"[Scene View] Loaded game bounds from project: {width}x{height}")
                return width, height
        except Exception as e:
            print(f"Warning: Could not load game bounds from project settings: {e}")

        # Fallback to default 1920x1080
        return 1920, 1080
    
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
        # Clear the screen using shared renderer if available
        if self.renderer:
            self.renderer.clear((0.2, 0.2, 0.2, 1.0))
        else:
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

    def get_font(self, font_name: Optional[str] = None, font_size: int = 14):
        """Get a pygame font for text rendering"""
        if not PYGAME_AVAILABLE:
            return None

        font_key = (font_name, font_size)
        if font_key not in self.font_cache:
            try:
                if font_name:
                    font = pygame.font.Font(font_name, font_size)
                else:
                    font = pygame.font.Font(None, font_size)
                self.font_cache[font_key] = font
            except Exception as e:
                print(f"Error loading font {font_name}: {e}")
                # Fallback to default font
                font = pygame.font.Font(None, font_size)
                self.font_cache[font_key] = font

        return self.font_cache[font_key]

    def create_text_texture(self, text: str, font, color: tuple) -> Optional[int]:
        """Create an OpenGL texture from text using pygame font"""
        if not PYGAME_AVAILABLE or not font:
            return None

        try:
            # Render text to pygame surface
            text_surface = font.render(text, True, color[:3])  # RGB only for pygame

            # Convert to RGBA format
            text_data = pygame.image.tostring(text_surface, 'RGBA', True)
            text_width, text_height = text_surface.get_size()

            # Create OpenGL texture
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)

            # Set texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            # Upload texture data
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_width, text_height,
                        0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

            glBindTexture(GL_TEXTURE_2D, 0)

            return texture_id

        except Exception as e:
            print(f"Error creating text texture: {e}")
            return None

    def draw_text_opengl(self, text: str, x: float, y: float, font_name: Optional[str] = None,
                        font_size: int = 14, color: tuple = (1.0, 1.0, 1.0, 1.0)):
        """Draw text using OpenGL with pygame font rendering"""
        if not text or not PYGAME_AVAILABLE:
            # Fallback to bitmap rendering
            self.draw_text_bitmap(text, x, y, list(color[:3]), font_size)
            return

        # Create cache key
        pygame_color = (int(color[0] * 255), int(color[1] * 255),
                       int(color[2] * 255), int(color[3] * 255))
        text_key = (text, font_name, font_size, pygame_color)

        # Check cache
        if text_key not in self.text_texture_cache:
            font = self.get_font(font_name, font_size)
            if font:
                texture_id = self.create_text_texture(text, font, pygame_color)
                if texture_id:
                    # Get text dimensions
                    text_width, text_height = font.size(text)
                    self.text_texture_cache[text_key] = (texture_id, text_width, text_height)

        # Draw cached text texture
        if text_key in self.text_texture_cache:
            texture_id, text_width, text_height = self.text_texture_cache[text_key]

            # Draw textured quad
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glColor4f(1.0, 1.0, 1.0, color[3])  # Use alpha from color

            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0)
            glVertex2f(x, y)
            glTexCoord2f(1.0, 0.0)
            glVertex2f(x + text_width, y)
            glTexCoord2f(1.0, 1.0)
            glVertex2f(x + text_width, y + text_height)
            glTexCoord2f(0.0, 1.0)
            glVertex2f(x, y + text_height)
            glEnd()

            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

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
                          right: float, top: float, tex_left: float = 0.0,
                          tex_bottom: float = 0.0, tex_right: float = 1.0,
                          tex_top: float = 1.0):
        """Draw a textured quad with custom texture coordinates"""
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor3f(1.0, 1.0, 1.0)  # White to show texture as-is

        glBegin(GL_QUADS)
        glTexCoord2f(tex_left, tex_bottom)
        glVertex2f(left, bottom)
        glTexCoord2f(tex_right, tex_bottom)
        glVertex2f(right, bottom)
        glTexCoord2f(tex_right, tex_top)
        glVertex2f(right, top)
        glTexCoord2f(tex_left, tex_top)
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

        # All nodes now use the same position property
        position = node_data.get("position", [0, 0])

        # Store original position for UI nodes
        original_position = position.copy() if isinstance(position, list) else [position[0], position[1]]

        # Handle coordinate conversion based on follow_viewport setting
        follow_viewport = node_data.get("follow_viewport", False)  # Default false for non-UI nodes
        if follow_viewport:
            # Convert viewport coordinates to editor world coordinates for rendering
            position = self._ui_to_world_coords(position)

        glPushMatrix()
        glTranslatef(position[0], position[1], 0)

        # Store the original position in the node data for hit detection
        node_data["_original_position"] = original_position

        # Draw based on node type - use dynamic dispatch
        draw_method_name = f"draw_{node_type.lower()}"
        if hasattr(self, draw_method_name):
            getattr(self, draw_method_name)(node_data)
        else:
            # Try common patterns
            if node_type == "Node2D":
                self.draw_node2d(node_data)
            elif node_type in ["Sprite", "AnimatedSprite"]:
                self.draw_sprite(node_data)
            elif node_type == "Timer":
                self.draw_timer(node_data)
            elif node_type == "Camera2D":
                self.draw_camera(node_data)
            elif node_type in ["Control", "Panel", "Label", "Button", "ColorRect", "TextureRect"]:
                # All UI nodes can use generic UI drawing
                self.draw_ui_node(node_data)
            elif node_type == "CanvasLayer":
                self.draw_canvas_layer(node_data)
            elif node_type in ["ProgressBar", "AudioStreamPlayer", "AudioStreamPlayer2D",
                              "VBoxContainer", "HBoxContainer", "CenterContainer", "GridContainer",
                              "RichTextLabel", "PanelContainer", "NinePatchRect", "ItemList"]:
                # Use generic UI drawing for these types
                self.draw_ui_node(node_data)
            elif node_type in ["CollisionShape2D", "CollisionPolygon2D"]:
                # Physics collision shapes
                if node_type == "CollisionShape2D":
                    self.draw_collision_shape(node_data)
                else:
                    self.draw_collision_polygon(node_data)
            elif node_type in ["Area2D", "RigidBody2D", "StaticBody2D", "KinematicBody2D"]:
                # Physics bodies
                if node_type == "Area2D":
                    self.draw_area2d(node_data)
                elif node_type == "RigidBody2D":
                    self.draw_rigid_body(node_data)
                elif node_type == "StaticBody2D":
                    self.draw_static_body(node_data)
                else:
                    self.draw_kinematic_body(node_data)
            elif node_type == "Light2D":
                self.draw_light2d(node_data)
            elif node_type == "TileMap":
                self.draw_tilemap(node_data)
            elif node_type == "RayCast2D":
                self.draw_raycast2d(node_data)
            elif node_type in ["Path2D", "PathFollow2D"]:
                if node_type == "Path2D":
                    self.draw_path2d(node_data)
                else:
                    self.draw_pathfollow2d(node_data)
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

                # Calculate texture coordinates for the current frame
                frame_x = frame % hframes
                frame_y = frame // hframes

                # Calculate texture coordinate bounds for this frame
                tex_left = frame_x / hframes
                tex_right = (frame_x + 1) / hframes
                tex_bottom = frame_y / vframes
                tex_top = (frame_y + 1) / vframes

                # Draw textured quad with proper frame coordinates
                self.draw_textured_quad(texture_id, left, bottom, right, top,
                                      tex_left, tex_bottom, tex_right, tex_top)
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

    def draw_animated_sprite(self, node_data: Dict[str, Any]):
        """Draw AnimatedSprite node - Godot AnimatedSprite2D equivalent"""
        # AnimatedSprite inherits from Sprite, so we can use the same rendering logic
        # but with additional animation-specific visual indicators

        # First draw as a regular sprite
        self.draw_sprite(node_data)

        # Add animation-specific visual indicators
        animation = node_data.get("animation", "default")
        playing = node_data.get("playing", False)
        speed_scale = node_data.get("speed_scale", 1.0)

        # Draw animation indicator (small play/pause icon)
        if playing:
            # Draw play indicator (triangle)
            glColor3f(0.0, 1.0, 0.0)  # Green for playing
            glBegin(GL_TRIANGLES)
            glVertex2f(-30, -5)
            glVertex2f(-30, 5)
            glVertex2f(-25, 0)
            glEnd()
        else:
            # Draw pause indicator (two bars)
            glColor3f(1.0, 1.0, 0.0)  # Yellow for paused
            glBegin(GL_QUADS)
            glVertex2f(-32, -5)
            glVertex2f(-30, -5)
            glVertex2f(-30, 5)
            glVertex2f(-32, 5)
            glVertex2f(-28, -5)
            glVertex2f(-26, -5)
            glVertex2f(-26, 5)
            glVertex2f(-28, 5)
            glEnd()

        # Draw animation name (simplified - would be text in real implementation)
        # This could show the current animation name

    def draw_timer(self, node_data: Dict[str, Any]):
        """Draw Timer node"""
        wait_time = node_data.get("wait_time", 1.0)
        time_left = node_data.get("_time_left", 0.0)
        is_running = node_data.get("_is_running", False)
        one_shot = node_data.get("one_shot", True)
        paused = node_data.get("paused", False)

        # Draw timer icon (clock-like)
        if is_running and not paused:
            glColor3f(0.0, 1.0, 0.0)  # Green when running
        elif paused:
            glColor3f(1.0, 1.0, 0.0)  # Yellow when paused
        else:
            glColor3f(0.6, 0.6, 0.6)  # Gray when stopped

        # Draw clock circle
        glBegin(GL_LINE_LOOP)
        for i in range(16):
            angle = 2 * math.pi * i / 16
            x = 15 * math.cos(angle)
            y = 15 * math.sin(angle)
            glVertex2f(x, y)
        glEnd()

        # Draw clock hands based on progress
        if wait_time > 0:
            progress = 1.0 - (time_left / wait_time) if is_running else 0.0
            progress = max(0.0, min(1.0, progress))

            # Hour hand (shows overall progress)
            hand_angle = progress * 2 * math.pi - math.pi / 2  # Start from top
            hand_x = 8 * math.cos(hand_angle)
            hand_y = 8 * math.sin(hand_angle)

            glBegin(GL_LINES)
            glVertex2f(0, 0)
            glVertex2f(hand_x, hand_y)
            glEnd()

        # Draw center dot
        glBegin(GL_QUADS)
        glVertex2f(-1, -1)
        glVertex2f(1, -1)
        glVertex2f(1, 1)
        glVertex2f(-1, 1)
        glEnd()

        # Draw mode indicator
        if one_shot:
            # Draw "1" for one-shot
            glBegin(GL_LINES)
            glVertex2f(-20, -8)
            glVertex2f(-20, 8)
            glEnd()
        else:
            # Draw circular arrow for repeating
            glBegin(GL_LINE_STRIP)
            for i in range(12):
                angle = 2 * math.pi * i / 12
                x = -20 + 5 * math.cos(angle)
                y = 5 * math.sin(angle)
                glVertex2f(x, y)
            glEnd()

            # Arrow head
            glBegin(GL_LINES)
            glVertex2f(-15, 3)
            glVertex2f(-17, 5)
            glVertex2f(-15, 3)
            glVertex2f(-17, 1)
            glEnd()

    def draw_camera(self, node_data: Dict[str, Any]):
        """Draw Camera2D node with viewport bounds and following indicators"""
        # Get camera properties
        current = node_data.get("current", False)
        enabled = node_data.get("enabled", True)
        zoom = node_data.get("zoom", [1.0, 1.0])
        offset = node_data.get("offset", [0.0, 0.0])
        follow_target = node_data.get("follow_target", None)

        # Calculate viewport size based on actual game bounds and zoom
        viewport_width = (self.game_width / 2) / zoom[0]
        viewport_height = (self.game_height / 2) / zoom[1]

        # Apply camera offset
        offset_x, offset_y = offset[0], offset[1]

        # Draw viewport bounds rectangle
        if current and enabled:
            glColor3f(1.0, 0.8, 0.2)  # Bright yellow for current camera
            glLineWidth(3.0)
        else:
            glColor3f(0.6, 0.6, 0.2)  # Dim yellow for inactive camera
            glLineWidth(2.0)

        # Draw viewport rectangle
        glBegin(GL_LINE_LOOP)
        glVertex2f(-viewport_width + offset_x, -viewport_height + offset_y)
        glVertex2f(viewport_width + offset_x, -viewport_height + offset_y)
        glVertex2f(viewport_width + offset_x, viewport_height + offset_y)
        glVertex2f(-viewport_width + offset_x, viewport_height + offset_y)
        glEnd()

        # Draw camera icon in center
        glColor3f(0.9, 0.9, 0.3)
        glLineWidth(2.0)
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

        # Draw current camera indicator
        if current:
            glColor3f(1.0, 0.2, 0.2)  # Red dot for current camera
            glBegin(GL_POLYGON)
            for i in range(8):
                angle = 2 * math.pi * i / 8
                x = 6 * math.cos(angle)
                y = 6 * math.sin(angle)
                glVertex2f(x, y)
            glEnd()

        # Draw follow target connection (if following another node)
        if follow_target and self.scene_data:
            target_node = self.find_node_by_path(follow_target)
            if target_node:
                target_pos = target_node.get("position", [0, 0])
                glColor3f(0.2, 0.8, 1.0)  # Cyan for follow connection
                glLineWidth(2.0)
                glEnable(GL_LINE_STIPPLE)
                glLineStipple(2, 0x5555)  # Dashed line
                glBegin(GL_LINES)
                glVertex2f(0, 0)  # Camera position
                glVertex2f(target_pos[0], target_pos[1])  # Target position
                glEnd()
                glDisable(GL_LINE_STIPPLE)

        # Reset line width
        glLineWidth(1.0)

    def find_node_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Find a node in the scene by its path"""
        if not self.scene_data or not path:
            return None

        # Simple implementation - search all nodes for matching name
        # In a full implementation, this would handle proper node paths
        def search_nodes(nodes, target_name):
            for node in nodes:
                if node.get("name") == target_name:
                    return node
                # Search children recursively
                children_result = search_nodes(node.get("children", []), target_name)
                if children_result:
                    return children_result
            return None

        # Extract node name from path (simplified)
        node_name = path.split("/")[-1] if "/" in path else path
        return search_nodes(self.scene_data.get("nodes", []), node_name)

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

    def draw_control(self, node_data: Dict[str, Any]):
        """Draw Control node (base UI node)"""
        # Get control properties - now uses size like other UI nodes
        size = node_data.get("size", [100.0, 100.0])

        # Draw control bounds (centered on position)
        glColor3f(0.5, 0.5, 0.8)  # Light blue for UI nodes
        glBegin(GL_LINE_LOOP)
        glVertex2f(-size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, size[1]/2)
        glVertex2f(-size[0]/2, size[1]/2)
        glEnd()

        # Draw UI indicator (small square in corner)
        glColor3f(0.8, 0.8, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(size[0]/2 - 8, size[1]/2 - 8)
        glVertex2f(size[0]/2, size[1]/2 - 8)
        glVertex2f(size[0]/2, size[1]/2)
        glVertex2f(size[0]/2 - 8, size[1]/2)
        glEnd()

    def draw_panel(self, node_data: Dict[str, Any]):
        """Draw Panel node"""
        # Get panel properties - now uses size like other UI nodes
        size = node_data.get("size", [100.0, 100.0])
        panel_color = node_data.get("panel_color", [0.2, 0.2, 0.2, 1.0])
        border_width = node_data.get("border_width", 0.0)
        border_color = node_data.get("border_color", [0.0, 0.0, 0.0, 1.0])

        # Draw panel background (centered on position)
        glColor4f(panel_color[0], panel_color[1], panel_color[2], panel_color[3])
        glBegin(GL_QUADS)
        glVertex2f(-size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, size[1]/2)
        glVertex2f(-size[0]/2, size[1]/2)
        glEnd()

        # Draw border if enabled
        if border_width > 0:
            glColor3f(border_color[0], border_color[1], border_color[2])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, size[1]/2)
            glVertex2f(-size[0]/2, size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw panel indicator (P in corner)
        glColor3f(1.0, 1.0, 1.0)
        # Simple "P" representation with lines
        glBegin(GL_LINES)
        # Vertical line
        glVertex2f(size[0]/2 - 12, size[1]/2 - 15)
        glVertex2f(size[0]/2 - 12, size[1]/2 - 3)
        # Top horizontal
        glVertex2f(size[0]/2 - 12, size[1]/2 - 3)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 3)
        # Middle horizontal
        glVertex2f(size[0]/2 - 12, size[1]/2 - 9)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 9)
        # Right vertical (top half)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 9)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 3)
        glEnd()

    def draw_label(self, node_data: Dict[str, Any]):
        """Draw Label node"""
        # Get label properties - now uses position like other nodes
        size = node_data.get("size", [100.0, 50.0])
        text = node_data.get("text", "Label")
        font_color = node_data.get("font_color", [1.0, 1.0, 1.0, 1.0])
        h_align = node_data.get("h_align", "Left")
        v_align = node_data.get("v_align", "Top")

        # Draw label bounds (dashed line, centered on position)
        glColor3f(0.7, 0.7, 0.9)  # Light purple for labels
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(1, 0xAAAA)  # Dashed line pattern
        glBegin(GL_LINE_LOOP)
        glVertex2f(-size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, size[1]/2)
        glVertex2f(-size[0]/2, size[1]/2)
        glEnd()
        glDisable(GL_LINE_STIPPLE)

        # Draw actual text content
        glColor3f(font_color[0], font_color[1], font_color[2])

        # Get font size for proper scaling
        font_size = node_data.get("font_size", 14)

        # Calculate text position based on alignment (relative to center)
        text_x = -size[0]/2 + 5  # Default left alignment
        if h_align == "Center":
            text_x = -len(text) * 3  # Approximate centering
        elif h_align == "Right":
            text_x = size[0]/2 - len(text) * 6 - 5  # Approximate right align

        text_y = size[1]/2 - 15  # Default top alignment
        if v_align == "Center":
            text_y = 0  # Center vertically
        elif v_align == "Bottom":
            text_y = -size[1]/2 + 15

        # Draw text using OpenGL rendering with pygame fonts
        font_path = node_data.get("font_path", None)  # Get font path from node data
        self.draw_text_opengl(text, text_x, text_y, font_path, font_size,
                             (font_color[0], font_color[1], font_color[2], 1.0))

    def draw_button(self, node_data: Dict[str, Any]):
        """Draw Button node with interactive states"""
        # Get button properties - now uses position like other nodes
        size = node_data.get("size", [100.0, 30.0])
        text = node_data.get("text", "Button")
        font_color = node_data.get("font_color", [1.0, 1.0, 1.0, 1.0])

        # Get button state colors
        normal_color = node_data.get("normal_color", [0.3, 0.3, 0.3, 1.0])
        hover_color = node_data.get("hover_color", [0.4, 0.4, 0.4, 1.0])
        pressed_color = node_data.get("pressed_color", [0.2, 0.2, 0.2, 1.0])
        disabled_color = node_data.get("disabled_color", [0.15, 0.15, 0.15, 1.0])

        # Get button state
        disabled = node_data.get("disabled", False)
        toggle_mode = node_data.get("toggle_mode", False)
        pressed = node_data.get("pressed", False)
        is_hovered = node_data.get("_is_hovered", False)
        is_mouse_pressed = node_data.get("_is_mouse_pressed", False)

        # Get style properties
        border_width = node_data.get("border_width", 1.0)
        border_color = node_data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        corner_radius = node_data.get("corner_radius", 4.0)

        # Determine current button color based on state
        if disabled:
            current_color = disabled_color
        elif is_mouse_pressed or (toggle_mode and pressed):
            current_color = pressed_color
        elif is_hovered:
            current_color = hover_color
        else:
            current_color = normal_color

        # Draw button background (centered on position)
        glColor4f(current_color[0], current_color[1], current_color[2], current_color[3])
        glBegin(GL_QUADS)
        glVertex2f(-size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, size[1]/2)
        glVertex2f(-size[0]/2, size[1]/2)
        glEnd()

        # Draw border if enabled
        if border_width > 0:
            glColor3f(border_color[0], border_color[1], border_color[2])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, size[1]/2)
            glVertex2f(-size[0]/2, size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw button text (centered)
        glColor3f(font_color[0], font_color[1], font_color[2])

        # Get font size for proper scaling
        font_size = node_data.get("font_size", 14)

        # Calculate text position (centered in button)
        text_x = -len(text) * 3  # Approximate centering
        text_y = -6  # Center vertically

        # Draw text using OpenGL rendering with pygame fonts
        font_path = node_data.get("font_path", None)  # Get font path from node data
        self.draw_text_opengl(text, text_x, text_y, font_path, font_size,
                             (font_color[0], font_color[1], font_color[2], 1.0))

        # Draw button indicator (B in corner)
        glColor3f(1.0, 1.0, 1.0)
        # Simple "B" representation with lines
        glBegin(GL_LINES)
        # Vertical line
        glVertex2f(size[0]/2 - 12, size[1]/2 - 15)
        glVertex2f(size[0]/2 - 12, size[1]/2 - 3)
        # Top horizontal
        glVertex2f(size[0]/2 - 12, size[1]/2 - 3)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 3)
        # Middle horizontal
        glVertex2f(size[0]/2 - 12, size[1]/2 - 9)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 9)
        # Bottom horizontal
        glVertex2f(size[0]/2 - 12, size[1]/2 - 15)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 15)
        # Right vertical (top half)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 9)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 3)
        # Right vertical (bottom half)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 15)
        glVertex2f(size[0]/2 - 6, size[1]/2 - 9)
        glEnd()

        # Draw state indicators
        if disabled:
            # Draw X for disabled
            glColor3f(0.8, 0.2, 0.2)  # Red for disabled
            glBegin(GL_LINES)
            glVertex2f(-size[0]/2 + 5, -size[1]/2 + 5)
            glVertex2f(size[0]/2 - 5, size[1]/2 - 5)
            glVertex2f(size[0]/2 - 5, -size[1]/2 + 5)
            glVertex2f(-size[0]/2 + 5, size[1]/2 - 5)
            glEnd()
        elif toggle_mode and pressed:
            # Draw checkmark for pressed toggle
            glColor3f(0.2, 0.8, 0.2)  # Green for pressed toggle
            glBegin(GL_LINES)
            glVertex2f(-size[0]/2 + 8, 0)
            glVertex2f(-size[0]/2 + 12, -4)
            glVertex2f(-size[0]/2 + 12, -4)
            glVertex2f(-size[0]/2 + 18, 6)
            glEnd()

    def draw_text_bitmap(self, text: str, x: float, y: float, color: list, font_size: int = 14):
        """Draw text using bitmap-based rendering with proper character shapes"""
        glColor3f(color[0], color[1], color[2])

        # Calculate character dimensions based on font size
        scale = max(0.5, font_size / 14.0)
        char_width = int(8 * scale)
        char_height = int(12 * scale)
        char_spacing = char_width + int(2 * scale)

        # Limit text length for performance
        display_text = text[:100] if len(text) > 100 else text

        # Draw each character using bitmap patterns
        for i, char in enumerate(display_text):
            char_x = x + i * char_spacing
            self.draw_character_bitmap(char, char_x, y, char_width, char_height, scale)

    def draw_character_bitmap(self, char: str, x: float, y: float, width: int, height: int, scale: float):
        """Draw a single character using bitmap patterns"""
        if char == ' ':
            return  # Skip spaces

        # Get character pattern (8x12 bitmap)
        pattern = self.get_character_pattern(char.upper())
        if not pattern:
            # Draw unknown character as a box with X
            self.draw_unknown_char(x, y, width, height)
            return

        # Draw the character using the bitmap pattern
        pixel_width = width / 8.0
        pixel_height = height / 12.0

        glBegin(GL_QUADS)
        for row in range(12):
            for col in range(8):
                if pattern[row] & (1 << (7 - col)):  # Check if pixel is set
                    px = x + col * pixel_width
                    py = y + (11 - row) * pixel_height  # Flip Y coordinate

                    # Draw a small quad for this pixel
                    glVertex2f(px, py)
                    glVertex2f(px + pixel_width, py)
                    glVertex2f(px + pixel_width, py + pixel_height)
                    glVertex2f(px, py + pixel_height)
        glEnd()

    def get_character_pattern(self, char: str):
        """Get 8x12 bitmap pattern for a character"""
        # Basic character patterns (8x12 bitmap, each row is a byte)
        patterns = {
            'A': [0x00, 0x18, 0x24, 0x42, 0x42, 0x7E, 0x42, 0x42, 0x42, 0x42, 0x00, 0x00],
            'B': [0x00, 0x7C, 0x42, 0x42, 0x7C, 0x42, 0x42, 0x42, 0x42, 0x7C, 0x00, 0x00],
            'C': [0x00, 0x3C, 0x42, 0x40, 0x40, 0x40, 0x40, 0x40, 0x42, 0x3C, 0x00, 0x00],
            'D': [0x00, 0x78, 0x44, 0x42, 0x42, 0x42, 0x42, 0x42, 0x44, 0x78, 0x00, 0x00],
            'E': [0x00, 0x7E, 0x40, 0x40, 0x40, 0x7C, 0x40, 0x40, 0x40, 0x7E, 0x00, 0x00],
            'F': [0x00, 0x7E, 0x40, 0x40, 0x40, 0x7C, 0x40, 0x40, 0x40, 0x40, 0x00, 0x00],
            'G': [0x00, 0x3C, 0x42, 0x40, 0x40, 0x4E, 0x42, 0x42, 0x42, 0x3C, 0x00, 0x00],
            'H': [0x00, 0x42, 0x42, 0x42, 0x42, 0x7E, 0x42, 0x42, 0x42, 0x42, 0x00, 0x00],
            'I': [0x00, 0x3E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x3E, 0x00, 0x00],
            'J': [0x00, 0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x44, 0x44, 0x38, 0x00, 0x00],
            'K': [0x00, 0x42, 0x44, 0x48, 0x50, 0x60, 0x50, 0x48, 0x44, 0x42, 0x00, 0x00],
            'L': [0x00, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x7E, 0x00, 0x00],
            'M': [0x00, 0x42, 0x66, 0x5A, 0x5A, 0x42, 0x42, 0x42, 0x42, 0x42, 0x00, 0x00],
            'N': [0x00, 0x42, 0x62, 0x52, 0x4A, 0x46, 0x42, 0x42, 0x42, 0x42, 0x00, 0x00],
            'O': [0x00, 0x3C, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x3C, 0x00, 0x00],
            'P': [0x00, 0x7C, 0x42, 0x42, 0x42, 0x7C, 0x40, 0x40, 0x40, 0x40, 0x00, 0x00],
            'Q': [0x00, 0x3C, 0x42, 0x42, 0x42, 0x42, 0x42, 0x4A, 0x44, 0x3A, 0x00, 0x00],
            'R': [0x00, 0x7C, 0x42, 0x42, 0x42, 0x7C, 0x48, 0x44, 0x42, 0x42, 0x00, 0x00],
            'S': [0x00, 0x3C, 0x42, 0x40, 0x30, 0x0C, 0x02, 0x42, 0x42, 0x3C, 0x00, 0x00],
            'T': [0x00, 0x7F, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x00, 0x00],
            'U': [0x00, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x3C, 0x00, 0x00],
            'V': [0x00, 0x42, 0x42, 0x42, 0x42, 0x42, 0x42, 0x24, 0x18, 0x18, 0x00, 0x00],
            'W': [0x00, 0x42, 0x42, 0x42, 0x42, 0x5A, 0x5A, 0x66, 0x42, 0x42, 0x00, 0x00],
            'X': [0x00, 0x42, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x42, 0x42, 0x00, 0x00],
            'Y': [0x00, 0x41, 0x41, 0x22, 0x14, 0x08, 0x08, 0x08, 0x08, 0x08, 0x00, 0x00],
            'Z': [0x00, 0x7E, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x40, 0x7E, 0x00, 0x00],
            '0': [0x00, 0x3C, 0x42, 0x46, 0x4A, 0x52, 0x62, 0x42, 0x42, 0x3C, 0x00, 0x00],
            '1': [0x00, 0x08, 0x18, 0x28, 0x08, 0x08, 0x08, 0x08, 0x08, 0x3E, 0x00, 0x00],
            '2': [0x00, 0x3C, 0x42, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x7E, 0x00, 0x00],
            '3': [0x00, 0x3C, 0x42, 0x02, 0x1C, 0x02, 0x02, 0x02, 0x42, 0x3C, 0x00, 0x00],
            '4': [0x00, 0x04, 0x0C, 0x14, 0x24, 0x44, 0x7E, 0x04, 0x04, 0x04, 0x00, 0x00],
            '5': [0x00, 0x7E, 0x40, 0x40, 0x7C, 0x02, 0x02, 0x02, 0x42, 0x3C, 0x00, 0x00],
            '6': [0x00, 0x1C, 0x20, 0x40, 0x7C, 0x42, 0x42, 0x42, 0x42, 0x3C, 0x00, 0x00],
            '7': [0x00, 0x7E, 0x02, 0x04, 0x08, 0x10, 0x10, 0x10, 0x10, 0x10, 0x00, 0x00],
            '8': [0x00, 0x3C, 0x42, 0x42, 0x3C, 0x42, 0x42, 0x42, 0x42, 0x3C, 0x00, 0x00],
            '9': [0x00, 0x3C, 0x42, 0x42, 0x42, 0x3E, 0x02, 0x04, 0x08, 0x70, 0x00, 0x00],
            '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00],
            ',': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x30, 0x00, 0x00],
            ':': [0x00, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x00],
            ';': [0x00, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x18, 0x18, 0x30, 0x00, 0x00],
            '!': [0x00, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00, 0x18, 0x18, 0x00, 0x00],
            '?': [0x00, 0x3C, 0x42, 0x02, 0x04, 0x08, 0x08, 0x00, 0x08, 0x08, 0x00, 0x00],
            '-': [0x00, 0x00, 0x00, 0x00, 0x00, 0x7E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            '+': [0x00, 0x00, 0x00, 0x08, 0x08, 0x7F, 0x08, 0x08, 0x00, 0x00, 0x00, 0x00],
            '=': [0x00, 0x00, 0x00, 0x00, 0x7E, 0x00, 0x7E, 0x00, 0x00, 0x00, 0x00, 0x00],
            '/': [0x00, 0x02, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x40, 0x80, 0x00, 0x00],
            '\\': [0x00, 0x80, 0x40, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x02, 0x00, 0x00],
            '(': [0x00, 0x0C, 0x10, 0x20, 0x20, 0x20, 0x20, 0x20, 0x10, 0x0C, 0x00, 0x00],
            ')': [0x00, 0x30, 0x08, 0x04, 0x04, 0x04, 0x04, 0x04, 0x08, 0x30, 0x00, 0x00],
            '[': [0x00, 0x3E, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x3E, 0x00, 0x00],
            ']': [0x00, 0x7C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x7C, 0x00, 0x00],
        }
        return patterns.get(char, None)

    def draw_unknown_char(self, x: float, y: float, width: int, height: int):
        """Draw a box with X for unknown characters"""
        # Draw box outline
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + width, y)
        glVertex2f(x + width, y + height)
        glVertex2f(x, y + height)
        glEnd()

        # Draw X inside
        glBegin(GL_LINES)
        glVertex2f(x + 1, y + 1)
        glVertex2f(x + width - 1, y + height - 1)
        glVertex2f(x + width - 1, y + 1)
        glVertex2f(x + 1, y + height - 1)
        glEnd()

    def draw_color_rect(self, node_data: Dict[str, Any]):
        """Draw ColorRect node"""
        # Get color rect properties
        size = node_data.get("size", [100.0, 100.0])
        color = node_data.get("color", [1.0, 1.0, 1.0, 1.0])

        # Draw color rectangle (centered on position)
        glColor4f(color[0], color[1], color[2], color[3])
        glBegin(GL_QUADS)
        glVertex2f(-size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, size[1]/2)
        glVertex2f(-size[0]/2, size[1]/2)
        glEnd()

        # Draw border for visibility in editor
        glColor3f(0.8, 0.8, 0.9)  # Light color for border
        glBegin(GL_LINE_LOOP)
        glVertex2f(-size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, size[1]/2)
        glVertex2f(-size[0]/2, size[1]/2)
        glEnd()

    def draw_texture_rect(self, node_data: Dict[str, Any]):
        """Draw TextureRect node"""
        # Get texture rect properties
        size = node_data.get("size", [100.0, 100.0])
        texture_path = node_data.get("texture", None)
        stretch_mode = node_data.get("stretch_mode", "stretch")
        flip_h = node_data.get("flip_h", False)
        flip_v = node_data.get("flip_v", False)

        # Try to load and draw texture if available
        if texture_path and isinstance(texture_path, str):
            texture_info = self.load_texture(texture_path)
            if texture_info:
                texture_id, tex_width, tex_height = texture_info

                # Calculate draw rectangle based on stretch mode
                draw_rect = self._calculate_texture_draw_rect(
                    size, [tex_width, tex_height], stretch_mode
                )

                # Draw textured rectangle
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glColor3f(1.0, 1.0, 1.0)  # White to show texture as-is

                # Set up texture coordinates based on flip settings
                u1, v1 = (1.0, 0.0) if flip_h else (0.0, 0.0)
                u2, v2 = (0.0, 0.0) if flip_h else (1.0, 0.0)
                u3, v3 = (0.0, 1.0) if flip_h else (1.0, 1.0)
                u4, v4 = (1.0, 1.0) if flip_h else (0.0, 1.0)

                if flip_v:
                    v1, v2, v3, v4 = v4, v3, v2, v1

                glBegin(GL_QUADS)
                glTexCoord2f(u1, v1)
                glVertex2f(draw_rect[0], draw_rect[1])
                glTexCoord2f(u2, v2)
                glVertex2f(draw_rect[2], draw_rect[1])
                glTexCoord2f(u3, v3)
                glVertex2f(draw_rect[2], draw_rect[3])
                glTexCoord2f(u4, v4)
                glVertex2f(draw_rect[0], draw_rect[3])
                glEnd()

                glDisable(GL_TEXTURE_2D)
            else:
                # Draw placeholder if texture failed to load
                self._draw_texture_placeholder(size, "MISSING")
        else:
            # Draw placeholder if no texture
            self._draw_texture_placeholder(size, "NO TEXTURE")

        # Draw border for visibility in editor
        glColor3f(0.9, 0.7, 0.9)  # Light purple for texture rect border
        glBegin(GL_LINE_LOOP)
        glVertex2f(-size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, size[1]/2)
        glVertex2f(-size[0]/2, size[1]/2)
        glEnd()

    def _calculate_texture_draw_rect(self, control_size, texture_size, stretch_mode):
        """Calculate the drawing rectangle for texture based on stretch mode"""
        # Convert to centered coordinates (relative to node position)
        half_width = control_size[0] / 2
        half_height = control_size[1] / 2

        if stretch_mode == "stretch":
            return [-half_width, -half_height, half_width, half_height]
        elif stretch_mode == "keep":
            tex_half_w = texture_size[0] / 2
            tex_half_h = texture_size[1] / 2
            return [-tex_half_w, -tex_half_h, tex_half_w, tex_half_h]
        elif stretch_mode == "keep_centered":
            tex_half_w = texture_size[0] / 2
            tex_half_h = texture_size[1] / 2
            return [-tex_half_w, -tex_half_h, tex_half_w, tex_half_h]
        elif stretch_mode in ["keep_aspect", "keep_aspect_centered"]:
            scale_x = control_size[0] / texture_size[0]
            scale_y = control_size[1] / texture_size[1]
            scale = min(scale_x, scale_y)
            scaled_w = texture_size[0] * scale / 2
            scaled_h = texture_size[1] * scale / 2
            return [-scaled_w, -scaled_h, scaled_w, scaled_h]
        elif stretch_mode == "keep_aspect_covered":
            scale_x = control_size[0] / texture_size[0]
            scale_y = control_size[1] / texture_size[1]
            scale = max(scale_x, scale_y)
            scaled_w = texture_size[0] * scale / 2
            scaled_h = texture_size[1] * scale / 2
            return [-scaled_w, -scaled_h, scaled_w, scaled_h]
        else:
            # Default to stretch
            return [-half_width, -half_height, half_width, half_height]

    def _draw_texture_placeholder(self, rect_size, text):
        """Draw a placeholder for missing or no texture"""
        # Draw checkered background
        glColor3f(0.8, 0.8, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, rect_size[1]/2)
        glVertex2f(-rect_size[0]/2, rect_size[1]/2)
        glEnd()

        # Draw checkered pattern
        glColor3f(0.7, 0.7, 0.7)
        checker_size = 8
        for x in range(int(-rect_size[0]/2), int(rect_size[0]/2), checker_size * 2):
            for y in range(int(-rect_size[1]/2), int(rect_size[1]/2), checker_size * 2):
                glBegin(GL_QUADS)
                glVertex2f(x, y)
                glVertex2f(x + checker_size, y)
                glVertex2f(x + checker_size, y + checker_size)
                glVertex2f(x, y + checker_size)
                glEnd()

                glBegin(GL_QUADS)
                glVertex2f(x + checker_size, y + checker_size)
                glVertex2f(x + checker_size * 2, y + checker_size)
                glVertex2f(x + checker_size * 2, y + checker_size * 2)
                glVertex2f(x + checker_size, y + checker_size * 2)
                glEnd()

        # Draw text in center
        glColor3f(0.3, 0.3, 0.3)
        # Simple text rendering would go here
        # For now, just draw a simple "T" shape to indicate texture
        glBegin(GL_LINES)
        glVertex2f(-10, 5)
        glVertex2f(10, 5)
        glVertex2f(0, 5)
        glVertex2f(0, -10)
        glEnd()

    def draw_progress_bar(self, node_data: Dict[str, Any]):
        """Draw ProgressBar node"""
        # Get progress bar properties
        size = node_data.get("size", [200.0, 24.0])
        min_value = node_data.get("min_value", 0.0)
        max_value = node_data.get("max_value", 100.0)
        value = node_data.get("value", 0.0)
        fill_mode = node_data.get("fill_mode", "left_to_right")
        background_color = node_data.get("background_color", [0.2, 0.2, 0.2, 1.0])
        fill_color = node_data.get("fill_color", [0.3, 0.6, 0.3, 1.0])
        border_color = node_data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        border_width = node_data.get("border_width", 1.0)
        show_percentage = node_data.get("show_percentage", False)

        # Calculate progress ratio
        if max_value > min_value:
            ratio = (value - min_value) / (max_value - min_value)
        else:
            ratio = 0.0
        ratio = max(0.0, min(1.0, ratio))

        # Draw background
        glColor4f(background_color[0], background_color[1], background_color[2], background_color[3])
        glBegin(GL_QUADS)
        glVertex2f(-size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, -size[1]/2)
        glVertex2f(size[0]/2, size[1]/2)
        glVertex2f(-size[0]/2, size[1]/2)
        glEnd()

        # Draw fill based on fill mode
        if ratio > 0.0:
            glColor4f(fill_color[0], fill_color[1], fill_color[2], fill_color[3])

            if fill_mode == "left_to_right":
                fill_width = size[0] * ratio
                glBegin(GL_QUADS)
                glVertex2f(-size[0]/2, -size[1]/2)
                glVertex2f(-size[0]/2 + fill_width, -size[1]/2)
                glVertex2f(-size[0]/2 + fill_width, size[1]/2)
                glVertex2f(-size[0]/2, size[1]/2)
                glEnd()
            elif fill_mode == "right_to_left":
                fill_width = size[0] * ratio
                glBegin(GL_QUADS)
                glVertex2f(size[0]/2 - fill_width, -size[1]/2)
                glVertex2f(size[0]/2, -size[1]/2)
                glVertex2f(size[0]/2, size[1]/2)
                glVertex2f(size[0]/2 - fill_width, size[1]/2)
                glEnd()
            elif fill_mode == "top_to_bottom":
                fill_height = size[1] * ratio
                glBegin(GL_QUADS)
                glVertex2f(-size[0]/2, size[1]/2 - fill_height)
                glVertex2f(size[0]/2, size[1]/2 - fill_height)
                glVertex2f(size[0]/2, size[1]/2)
                glVertex2f(-size[0]/2, size[1]/2)
                glEnd()
            elif fill_mode == "bottom_to_top":
                fill_height = size[1] * ratio
                glBegin(GL_QUADS)
                glVertex2f(-size[0]/2, -size[1]/2)
                glVertex2f(size[0]/2, -size[1]/2)
                glVertex2f(size[0]/2, -size[1]/2 + fill_height)
                glVertex2f(-size[0]/2, -size[1]/2 + fill_height)
                glEnd()
            elif fill_mode == "center_expand":
                fill_width = size[0] * ratio
                offset = (size[0] - fill_width) / 2
                glBegin(GL_QUADS)
                glVertex2f(-size[0]/2 + offset, -size[1]/2)
                glVertex2f(size[0]/2 - offset, -size[1]/2)
                glVertex2f(size[0]/2 - offset, size[1]/2)
                glVertex2f(-size[0]/2 + offset, size[1]/2)
                glEnd()

        # Draw border
        if border_width > 0:
            glColor4f(border_color[0], border_color[1], border_color[2], border_color[3])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, size[1]/2)
            glVertex2f(-size[0]/2, size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw percentage text if enabled
        if show_percentage:
            percentage = int(ratio * 100)
            # Simple text representation - just draw the percentage as a small indicator
            glColor3f(1.0, 1.0, 1.0)
            # Draw a small "%" symbol in the center
            glBegin(GL_LINES)
            # % symbol (simplified)
            glVertex2f(-5, 5)
            glVertex2f(5, -5)
            glVertex2f(-5, 3)
            glVertex2f(-3, 5)
            glVertex2f(3, -5)
            glVertex2f(5, -3)
            glEnd()

    def draw_audio_stream_player(self, node_data: Dict[str, Any]):
        """Draw AudioStreamPlayer node"""
        playing = node_data.get("playing", False)
        volume_db = node_data.get("volume_db", 0.0)
        stream = node_data.get("stream", None)

        # Choose color based on state
        if playing:
            glColor3f(0.0, 1.0, 0.0)  # Green when playing
        elif stream:
            glColor3f(0.8, 0.8, 0.0)  # Yellow when loaded but not playing
        else:
            glColor3f(0.5, 0.5, 0.5)  # Gray when no stream

        # Draw speaker icon
        size = 20
        glBegin(GL_QUADS)
        # Speaker cone
        glVertex2f(-size, -size/2)
        glVertex2f(-size/2, -size/2)
        glVertex2f(-size/2, size/2)
        glVertex2f(-size, size/2)
        glEnd()

        # Speaker horn
        glBegin(GL_LINE_STRIP)
        glVertex2f(-size/2, -size/2)
        glVertex2f(size/2, -size)
        glVertex2f(size, -size)
        glVertex2f(size, size)
        glVertex2f(size/2, size)
        glVertex2f(-size/2, size/2)
        glEnd()

        # Draw sound waves if playing
        if playing:
            glBegin(GL_LINES)
            for i in range(3):
                radius = size + (i + 1) * 8
                # Draw arc segments
                for j in range(8):
                    angle1 = -0.5 + j * 0.125
                    angle2 = -0.5 + (j + 1) * 0.125
                    x1 = radius * math.cos(angle1)
                    y1 = radius * math.sin(angle1)
                    x2 = radius * math.cos(angle2)
                    y2 = radius * math.sin(angle2)
                    glVertex2f(x1, y1)
                    glVertex2f(x2, y2)
            glEnd()

    def draw_audio_stream_player_2d(self, node_data: Dict[str, Any]):
        """Draw AudioStreamPlayer2D node"""
        playing = node_data.get("playing", False)
        volume_db = node_data.get("volume_db", 0.0)
        max_distance = node_data.get("max_distance", 2000.0)
        attenuation = node_data.get("attenuation", 1.0)
        stream = node_data.get("stream", None)

        # Choose color based on state
        if playing:
            glColor3f(0.0, 1.0, 0.0)  # Green when playing
        elif stream:
            glColor3f(0.8, 0.8, 0.0)  # Yellow when loaded but not playing
        else:
            glColor3f(0.5, 0.5, 0.5)  # Gray when no stream

        # Draw 2D speaker icon (similar to regular but with 2D indicator)
        size = 20
        glBegin(GL_QUADS)
        # Speaker cone
        glVertex2f(-size, -size/2)
        glVertex2f(-size/2, -size/2)
        glVertex2f(-size/2, size/2)
        glVertex2f(-size, size/2)
        glEnd()

        # Speaker horn
        glBegin(GL_LINE_STRIP)
        glVertex2f(-size/2, -size/2)
        glVertex2f(size/2, -size)
        glVertex2f(size, -size)
        glVertex2f(size, size)
        glVertex2f(size/2, size)
        glVertex2f(-size/2, size/2)
        glEnd()

        # Draw attenuation circle to show max distance (scaled down for visibility)
        if max_distance > 0:
            display_radius = min(50, max_distance / 40)  # Scale down for editor
            glColor4f(0.3, 0.3, 1.0, 0.3)  # Semi-transparent blue
            glBegin(GL_LINE_LOOP)
            segments = 32
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = display_radius * math.cos(angle)
                y = display_radius * math.sin(angle)
                glVertex2f(x, y)
            glEnd()

        # Draw sound waves if playing (360-degree for 2D)
        if playing:
            glColor3f(0.0, 1.0, 0.0)
            glBegin(GL_LINES)
            for i in range(3):
                radius = size + (i + 1) * 8
                segments = 16
                for j in range(segments):
                    angle1 = 2 * math.pi * j / segments
                    angle2 = 2 * math.pi * (j + 1) / segments
                    x1 = radius * math.cos(angle1)
                    y1 = radius * math.sin(angle1)
                    x2 = radius * math.cos(angle2)
                    y2 = radius * math.sin(angle2)
                    glVertex2f(x1, y1)
                    glVertex2f(x2, y2)
            glEnd()

        # Draw "2D" text indicator
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_LINES)
        # Simple "2D" text
        # "2"
        glVertex2f(-size - 15, size + 10)
        glVertex2f(-size - 5, size + 10)
        glVertex2f(-size - 5, size + 10)
        glVertex2f(-size - 5, size + 5)
        glVertex2f(-size - 5, size + 5)
        glVertex2f(-size - 15, size + 5)
        glVertex2f(-size - 15, size + 5)
        glVertex2f(-size - 15, size)
        glVertex2f(-size - 15, size)
        glVertex2f(-size - 5, size)
        # "D"
        glVertex2f(-size, size + 10)
        glVertex2f(-size, size)
        glVertex2f(-size, size + 10)
        glVertex2f(-size + 8, size + 10)
        glVertex2f(-size + 8, size + 10)
        glVertex2f(-size + 8, size)
        glVertex2f(-size + 8, size)
        glVertex2f(-size, size)
        glEnd()

    def draw_vbox_container(self, node_data: Dict[str, Any]):
        """Draw VBoxContainer node"""
        size = node_data.get("size", [100.0, 100.0])
        separation = node_data.get("separation", 4.0)
        alignment = node_data.get("alignment", "top")
        background_color = node_data.get("background_color", [0.0, 0.0, 0.0, 0.0])
        border_color = node_data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        border_width = node_data.get("border_width", 0.0)
        container_margin_left = node_data.get("container_margin_left", 0.0)
        container_margin_top = node_data.get("container_margin_top", 0.0)
        container_margin_right = node_data.get("container_margin_right", 0.0)
        container_margin_bottom = node_data.get("container_margin_bottom", 0.0)

        # Draw background if not transparent
        if background_color[3] > 0.0:
            glColor4f(background_color[0], background_color[1], background_color[2], background_color[3])
            glBegin(GL_QUADS)
            glVertex2f(-size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, size[1]/2)
            glVertex2f(-size[0]/2, size[1]/2)
            glEnd()

        # Draw border if enabled
        if border_width > 0:
            glColor4f(border_color[0], border_color[1], border_color[2], border_color[3])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, size[1]/2)
            glVertex2f(-size[0]/2, size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw container margins
        if any([container_margin_left, container_margin_top, container_margin_right, container_margin_bottom]):
            glColor3f(0.3, 0.7, 0.3)  # Green for margins
            glLineWidth(1.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-size[0]/2 + container_margin_left, -size[1]/2 + container_margin_bottom)
            glVertex2f(size[0]/2 - container_margin_right, -size[1]/2 + container_margin_bottom)
            glVertex2f(size[0]/2 - container_margin_right, size[1]/2 - container_margin_top)
            glVertex2f(-size[0]/2 + container_margin_left, size[1]/2 - container_margin_top)
            glEnd()

        # Draw layout indicator (vertical arrows)
        glColor3f(0.8, 0.8, 0.2)  # Yellow for layout direction
        glBegin(GL_LINES)
        # Vertical line
        glVertex2f(0, -size[1]/4)
        glVertex2f(0, size[1]/4)
        # Arrow heads
        glVertex2f(0, size[1]/4)
        glVertex2f(-5, size[1]/4 - 8)
        glVertex2f(0, size[1]/4)
        glVertex2f(5, size[1]/4 - 8)
        glEnd()

        # Draw alignment indicator
        if alignment == "center":
            glColor3f(1.0, 1.0, 0.0)
            glBegin(GL_LINES)
            glVertex2f(-10, 0)
            glVertex2f(10, 0)
            glEnd()
        elif alignment == "bottom":
            glColor3f(1.0, 1.0, 0.0)
            glBegin(GL_LINES)
            glVertex2f(-10, -size[1]/4)
            glVertex2f(10, -size[1]/4)
            glEnd()

    def draw_hbox_container(self, node_data: Dict[str, Any]):
        """Draw HBoxContainer node"""
        size = node_data.get("size", [100.0, 100.0])
        separation = node_data.get("separation", 4.0)
        alignment = node_data.get("alignment", "left")
        background_color = node_data.get("background_color", [0.0, 0.0, 0.0, 0.0])
        border_color = node_data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        border_width = node_data.get("border_width", 0.0)
        container_margin_left = node_data.get("container_margin_left", 0.0)
        container_margin_top = node_data.get("container_margin_top", 0.0)
        container_margin_right = node_data.get("container_margin_right", 0.0)
        container_margin_bottom = node_data.get("container_margin_bottom", 0.0)

        # Draw background if not transparent
        if background_color[3] > 0.0:
            glColor4f(background_color[0], background_color[1], background_color[2], background_color[3])
            glBegin(GL_QUADS)
            glVertex2f(-size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, size[1]/2)
            glVertex2f(-size[0]/2, size[1]/2)
            glEnd()

        # Draw border if enabled
        if border_width > 0:
            glColor4f(border_color[0], border_color[1], border_color[2], border_color[3])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, size[1]/2)
            glVertex2f(-size[0]/2, size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw container margins
        if any([container_margin_left, container_margin_top, container_margin_right, container_margin_bottom]):
            glColor3f(0.3, 0.7, 0.3)  # Green for margins
            glLineWidth(1.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-size[0]/2 + container_margin_left, -size[1]/2 + container_margin_bottom)
            glVertex2f(size[0]/2 - container_margin_right, -size[1]/2 + container_margin_bottom)
            glVertex2f(size[0]/2 - container_margin_right, size[1]/2 - container_margin_top)
            glVertex2f(-size[0]/2 + container_margin_left, size[1]/2 - container_margin_top)
            glEnd()

        # Draw layout indicator (horizontal arrows)
        glColor3f(0.8, 0.8, 0.2)  # Yellow for layout direction
        glBegin(GL_LINES)
        # Horizontal line
        glVertex2f(-size[0]/4, 0)
        glVertex2f(size[0]/4, 0)
        # Arrow heads
        glVertex2f(size[0]/4, 0)
        glVertex2f(size[0]/4 - 8, -5)
        glVertex2f(size[0]/4, 0)
        glVertex2f(size[0]/4 - 8, 5)
        glEnd()

        # Draw alignment indicator
        if alignment == "center":
            glColor3f(1.0, 1.0, 0.0)
            glBegin(GL_LINES)
            glVertex2f(0, -10)
            glVertex2f(0, 10)
            glEnd()
        elif alignment == "right":
            glColor3f(1.0, 1.0, 0.0)
            glBegin(GL_LINES)
            glVertex2f(size[0]/4, -10)
            glVertex2f(size[0]/4, 10)
            glEnd()

    def draw_center_container(self, node_data: Dict[str, Any]):
        """Draw CenterContainer node"""
        size = node_data.get("size", [100.0, 100.0])
        use_top_left = node_data.get("use_top_left", False)
        background_color = node_data.get("background_color", [0.0, 0.0, 0.0, 0.0])
        border_color = node_data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        border_width = node_data.get("border_width", 0.0)
        container_margin_left = node_data.get("container_margin_left", 0.0)
        container_margin_top = node_data.get("container_margin_top", 0.0)
        container_margin_right = node_data.get("container_margin_right", 0.0)
        container_margin_bottom = node_data.get("container_margin_bottom", 0.0)

        # Draw background if not transparent
        if background_color[3] > 0.0:
            glColor4f(background_color[0], background_color[1], background_color[2], background_color[3])
            glBegin(GL_QUADS)
            glVertex2f(-size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, size[1]/2)
            glVertex2f(-size[0]/2, size[1]/2)
            glEnd()

        # Draw border if enabled
        if border_width > 0:
            glColor4f(border_color[0], border_color[1], border_color[2], border_color[3])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, -size[1]/2)
            glVertex2f(size[0]/2, size[1]/2)
            glVertex2f(-size[0]/2, size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw container margins
        if any([container_margin_left, container_margin_top, container_margin_right, container_margin_bottom]):
            glColor3f(0.3, 0.7, 0.3)  # Green for margins
            glLineWidth(1.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-size[0]/2 + container_margin_left, -size[1]/2 + container_margin_bottom)
            glVertex2f(size[0]/2 - container_margin_right, -size[1]/2 + container_margin_bottom)
            glVertex2f(size[0]/2 - container_margin_right, size[1]/2 - container_margin_top)
            glVertex2f(-size[0]/2 + container_margin_left, size[1]/2 - container_margin_top)
            glEnd()

        # Draw center indicator (crosshair)
        glColor3f(0.8, 0.2, 0.8)  # Magenta for center
        glBegin(GL_LINES)
        # Horizontal line
        glVertex2f(-15, 0)
        glVertex2f(15, 0)
        # Vertical line
        glVertex2f(0, -15)
        glVertex2f(0, 15)
        glEnd()

        # Draw center point
        glColor3f(1.0, 0.0, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(-2, -2)
        glVertex2f(2, -2)
        glVertex2f(2, 2)
        glVertex2f(-2, 2)
        glEnd()

    def draw_grid_container(self, node_data: Dict[str, Any]):
        """Draw GridContainer node"""
        rect_size = node_data.get("rect_size", [200.0, 200.0])
        columns = node_data.get("columns", 2)
        h_separation = node_data.get("h_separation", 4.0)
        v_separation = node_data.get("v_separation", 4.0)
        background_color = node_data.get("background_color", [0.0, 0.0, 0.0, 0.0])
        border_color = node_data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        border_width = node_data.get("border_width", 0.0)
        container_margin_left = node_data.get("container_margin_left", 0.0)
        container_margin_top = node_data.get("container_margin_top", 0.0)
        container_margin_right = node_data.get("container_margin_right", 0.0)
        container_margin_bottom = node_data.get("container_margin_bottom", 0.0)

        # Draw background if not transparent
        if background_color[3] > 0.0:
            glColor4f(background_color[0], background_color[1], background_color[2], background_color[3])
            glBegin(GL_QUADS)
            glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, rect_size[1]/2)
            glVertex2f(-rect_size[0]/2, rect_size[1]/2)
            glEnd()

        # Draw border if enabled
        if border_width > 0:
            glColor4f(border_color[0], border_color[1], border_color[2], border_color[3])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, rect_size[1]/2)
            glVertex2f(-rect_size[0]/2, rect_size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw container margins
        if any([container_margin_left, container_margin_top, container_margin_right, container_margin_bottom]):
            glColor3f(0.3, 0.7, 0.3)  # Green for margins
            glLineWidth(1.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-rect_size[0]/2 + container_margin_left, -rect_size[1]/2 + container_margin_bottom)
            glVertex2f(rect_size[0]/2 - container_margin_right, -rect_size[1]/2 + container_margin_bottom)
            glVertex2f(rect_size[0]/2 - container_margin_right, rect_size[1]/2 - container_margin_top)
            glVertex2f(-rect_size[0]/2 + container_margin_left, rect_size[1]/2 - container_margin_top)
            glEnd()

        # Calculate grid layout for visualization
        if columns > 0:
            # Calculate available space
            available_width = rect_size[0] - container_margin_left - container_margin_right
            available_height = rect_size[1] - container_margin_top - container_margin_bottom

            # Assume 4 children for visualization (2x2 grid if columns=2)
            rows = max(1, 2)  # Show at least 2 rows for demo

            # Calculate cell size
            total_h_separation = h_separation * max(0, columns - 1)
            total_v_separation = v_separation * max(0, rows - 1)

            cell_width = (available_width - total_h_separation) / columns
            cell_height = (available_height - total_v_separation) / rows

            # Draw grid lines
            glColor3f(0.6, 0.6, 0.8)  # Light blue for grid
            glBegin(GL_LINES)

            # Vertical lines
            for i in range(columns + 1):
                x = -rect_size[0]/2 + container_margin_left + i * (cell_width + h_separation)
                if i == columns:
                    x -= h_separation  # Adjust last line
                glVertex2f(x, -rect_size[1]/2 + container_margin_bottom)
                glVertex2f(x, rect_size[1]/2 - container_margin_top)

            # Horizontal lines
            for i in range(rows + 1):
                y = -rect_size[1]/2 + container_margin_bottom + i * (cell_height + v_separation)
                if i == rows:
                    y -= v_separation  # Adjust last line
                glVertex2f(-rect_size[0]/2 + container_margin_left, y)
                glVertex2f(rect_size[0]/2 - container_margin_right, y)

            glEnd()

        # Draw grid indicator text (simplified)
        glColor3f(1.0, 1.0, 0.0)  # Yellow
        glBegin(GL_LINES)
        # Draw "G" for Grid
        glVertex2f(-8, 8)
        glVertex2f(-8, -8)
        glVertex2f(-8, 8)
        glVertex2f(0, 8)
        glVertex2f(0, 8)
        glVertex2f(0, 0)
        glVertex2f(0, 0)
        glVertex2f(-4, 0)
        glEnd()

    def draw_rich_text_label(self, node_data: Dict[str, Any]):
        """Draw RichTextLabel node"""
        rect_size = node_data.get("rect_size", [200.0, 100.0])
        text = node_data.get("text", "")
        bbcode_enabled = node_data.get("bbcode_enabled", True)
        background_color = node_data.get("background_color", [0.0, 0.0, 0.0, 0.0])
        border_color = node_data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        border_width = node_data.get("border_width", 0.0)
        scroll_active = node_data.get("scroll_active", True)
        default_color = node_data.get("default_color", [1.0, 1.0, 1.0, 1.0])

        # Draw background if not transparent
        if background_color[3] > 0.0:
            glColor4f(background_color[0], background_color[1], background_color[2], background_color[3])
            glBegin(GL_QUADS)
            glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, rect_size[1]/2)
            glVertex2f(-rect_size[0]/2, rect_size[1]/2)
            glEnd()

        # Draw border if enabled
        if border_width > 0:
            glColor4f(border_color[0], border_color[1], border_color[2], border_color[3])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, rect_size[1]/2)
            glVertex2f(-rect_size[0]/2, rect_size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw text content indicator
        if text:
            # Draw text lines indicator
            glColor4f(default_color[0], default_color[1], default_color[2], default_color[3])
            glBegin(GL_LINES)
            # Simulate text lines
            line_height = 12
            num_lines = min(int(rect_size[1] / line_height), 5)  # Max 5 lines for preview
            start_y = rect_size[1]/2 - 10

            for i in range(num_lines):
                y = start_y - i * line_height
                line_width = rect_size[0] * 0.8 if i < num_lines - 1 else rect_size[0] * 0.6  # Last line shorter
                glVertex2f(-line_width/2, y)
                glVertex2f(line_width/2, y)
            glEnd()

        # Draw BBCode indicator if enabled
        if bbcode_enabled:
            glColor3f(1.0, 0.8, 0.2)  # Orange for BBCode
            glBegin(GL_LINES)
            # Draw "BB" indicator
            # B
            glVertex2f(-rect_size[0]/2 + 5, rect_size[1]/2 - 5)
            glVertex2f(-rect_size[0]/2 + 5, rect_size[1]/2 - 15)
            glVertex2f(-rect_size[0]/2 + 5, rect_size[1]/2 - 5)
            glVertex2f(-rect_size[0]/2 + 10, rect_size[1]/2 - 5)
            glVertex2f(-rect_size[0]/2 + 5, rect_size[1]/2 - 10)
            glVertex2f(-rect_size[0]/2 + 10, rect_size[1]/2 - 10)
            glVertex2f(-rect_size[0]/2 + 10, rect_size[1]/2 - 10)
            glVertex2f(-rect_size[0]/2 + 10, rect_size[1]/2 - 15)
            # B
            glVertex2f(-rect_size[0]/2 + 12, rect_size[1]/2 - 5)
            glVertex2f(-rect_size[0]/2 + 12, rect_size[1]/2 - 15)
            glVertex2f(-rect_size[0]/2 + 12, rect_size[1]/2 - 5)
            glVertex2f(-rect_size[0]/2 + 17, rect_size[1]/2 - 5)
            glVertex2f(-rect_size[0]/2 + 12, rect_size[1]/2 - 10)
            glVertex2f(-rect_size[0]/2 + 17, rect_size[1]/2 - 10)
            glVertex2f(-rect_size[0]/2 + 17, rect_size[1]/2 - 10)
            glVertex2f(-rect_size[0]/2 + 17, rect_size[1]/2 - 15)
            glEnd()

        # Draw scroll indicator if scrolling is active
        if scroll_active:
            glColor3f(0.6, 0.6, 0.8)  # Light blue for scroll
            glBegin(GL_LINES)
            # Scroll bar on right side
            scroll_x = rect_size[0]/2 - 3
            glVertex2f(scroll_x, -rect_size[1]/2 + 5)
            glVertex2f(scroll_x, rect_size[1]/2 - 5)
            # Scroll thumb
            glVertex2f(scroll_x - 2, rect_size[1]/4)
            glVertex2f(scroll_x + 2, rect_size[1]/4)
            glVertex2f(scroll_x - 2, rect_size[1]/4 - 10)
            glVertex2f(scroll_x + 2, rect_size[1]/4 - 10)
            glEnd()

    def draw_panel_container(self, node_data: Dict[str, Any]):
        """Draw PanelContainer node"""
        rect_size = node_data.get("rect_size", [100.0, 100.0])
        panel_color = node_data.get("panel_color", [0.2, 0.2, 0.2, 1.0])
        border_color = node_data.get("border_color", [0.4, 0.4, 0.4, 1.0])
        border_width = node_data.get("border_width", 1.0)
        corner_radius = node_data.get("corner_radius", 4.0)
        shadow_enabled = node_data.get("shadow_enabled", False)
        shadow_color = node_data.get("shadow_color", [0.0, 0.0, 0.0, 0.5])
        shadow_offset = node_data.get("shadow_offset", [2.0, 2.0])
        container_margin_left = node_data.get("container_margin_left", 8.0)
        container_margin_top = node_data.get("container_margin_top", 8.0)
        container_margin_right = node_data.get("container_margin_right", 8.0)
        container_margin_bottom = node_data.get("container_margin_bottom", 8.0)

        # Draw shadow if enabled
        if shadow_enabled:
            glColor4f(shadow_color[0], shadow_color[1], shadow_color[2], shadow_color[3])
            shadow_x = shadow_offset[0]
            shadow_y = -shadow_offset[1]  # Flip Y for OpenGL coordinates
            glBegin(GL_QUADS)
            glVertex2f(-rect_size[0]/2 + shadow_x, -rect_size[1]/2 + shadow_y)
            glVertex2f(rect_size[0]/2 + shadow_x, -rect_size[1]/2 + shadow_y)
            glVertex2f(rect_size[0]/2 + shadow_x, rect_size[1]/2 + shadow_y)
            glVertex2f(-rect_size[0]/2 + shadow_x, rect_size[1]/2 + shadow_y)
            glEnd()

        # Draw panel background
        glColor4f(panel_color[0], panel_color[1], panel_color[2], panel_color[3])
        glBegin(GL_QUADS)
        glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, rect_size[1]/2)
        glVertex2f(-rect_size[0]/2, rect_size[1]/2)
        glEnd()

        # Draw border if enabled
        if border_width > 0:
            glColor4f(border_color[0], border_color[1], border_color[2], border_color[3])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, rect_size[1]/2)
            glVertex2f(-rect_size[0]/2, rect_size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw container margins
        if any([container_margin_left, container_margin_top, container_margin_right, container_margin_bottom]):
            glColor3f(0.3, 0.7, 0.3)  # Green for margins
            glLineWidth(1.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-rect_size[0]/2 + container_margin_left, -rect_size[1]/2 + container_margin_bottom)
            glVertex2f(rect_size[0]/2 - container_margin_right, -rect_size[1]/2 + container_margin_bottom)
            glVertex2f(rect_size[0]/2 - container_margin_right, rect_size[1]/2 - container_margin_top)
            glVertex2f(-rect_size[0]/2 + container_margin_left, rect_size[1]/2 - container_margin_top)
            glEnd()

        # Draw corner radius indicator if enabled
        if corner_radius > 0:
            glColor3f(0.8, 0.8, 0.2)  # Yellow for rounded corners
            glBegin(GL_LINES)
            # Draw small corner indicators
            corner_size = min(corner_radius, 8.0)
            # Top-left corner
            glVertex2f(-rect_size[0]/2, -rect_size[1]/2 + corner_size)
            glVertex2f(-rect_size[0]/2 + corner_size, -rect_size[1]/2)
            # Top-right corner
            glVertex2f(rect_size[0]/2 - corner_size, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, -rect_size[1]/2 + corner_size)
            # Bottom-right corner
            glVertex2f(rect_size[0]/2, rect_size[1]/2 - corner_size)
            glVertex2f(rect_size[0]/2 - corner_size, rect_size[1]/2)
            # Bottom-left corner
            glVertex2f(-rect_size[0]/2 + corner_size, rect_size[1]/2)
            glVertex2f(-rect_size[0]/2, rect_size[1]/2 - corner_size)
            glEnd()

        # Draw "PC" indicator for PanelContainer
        glColor3f(1.0, 1.0, 0.0)  # Yellow
        glBegin(GL_LINES)
        # P
        glVertex2f(-8, 8)
        glVertex2f(-8, -8)
        glVertex2f(-8, 8)
        glVertex2f(-2, 8)
        glVertex2f(-2, 8)
        glVertex2f(-2, 0)
        glVertex2f(-2, 0)
        glVertex2f(-8, 0)
        # C
        glVertex2f(2, 8)
        glVertex2f(8, 8)
        glVertex2f(2, 8)
        glVertex2f(2, -8)
        glVertex2f(2, -8)
        glVertex2f(8, -8)
        glEnd()

    def draw_nine_patch_rect(self, node_data: Dict[str, Any]):
        """Draw NinePatchRect node"""
        rect_size = node_data.get("rect_size", [100.0, 100.0])
        texture = node_data.get("texture", None)
        patch_margin_left = node_data.get("patch_margin_left", 0)
        patch_margin_top = node_data.get("patch_margin_top", 0)
        patch_margin_right = node_data.get("patch_margin_right", 0)
        patch_margin_bottom = node_data.get("patch_margin_bottom", 0)
        draw_center = node_data.get("draw_center", True)
        modulate = node_data.get("modulate", [1.0, 1.0, 1.0, 1.0])

        # Draw background/placeholder
        if texture:
            glColor4f(modulate[0], modulate[1], modulate[2], modulate[3])
        else:
            glColor3f(0.3, 0.3, 0.5)  # Blue-gray for no texture

        # Draw main rectangle
        glBegin(GL_QUADS)
        glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, rect_size[1]/2)
        glVertex2f(-rect_size[0]/2, rect_size[1]/2)
        glEnd()

        # Draw 9-patch margin indicators if they exist
        if any([patch_margin_left, patch_margin_top, patch_margin_right, patch_margin_bottom]):
            glColor3f(1.0, 0.8, 0.2)  # Orange for patch margins
            glLineWidth(1.0)

            # Draw patch margin lines
            glBegin(GL_LINES)

            # Left margin
            if patch_margin_left > 0:
                x = -rect_size[0]/2 + patch_margin_left
                glVertex2f(x, -rect_size[1]/2)
                glVertex2f(x, rect_size[1]/2)

            # Right margin
            if patch_margin_right > 0:
                x = rect_size[0]/2 - patch_margin_right
                glVertex2f(x, -rect_size[1]/2)
                glVertex2f(x, rect_size[1]/2)

            # Top margin
            if patch_margin_top > 0:
                y = rect_size[1]/2 - patch_margin_top
                glVertex2f(-rect_size[0]/2, y)
                glVertex2f(rect_size[0]/2, y)

            # Bottom margin
            if patch_margin_bottom > 0:
                y = -rect_size[1]/2 + patch_margin_bottom
                glVertex2f(-rect_size[0]/2, y)
                glVertex2f(rect_size[0]/2, y)

            glEnd()

        # Draw center indicator if center is disabled
        if not draw_center:
            glColor3f(1.0, 0.0, 0.0)  # Red X for no center
            glBegin(GL_LINES)
            glVertex2f(-10, -10)
            glVertex2f(10, 10)
            glVertex2f(-10, 10)
            glVertex2f(10, -10)
            glEnd()

        # Draw "9P" indicator for NinePatch
        glColor3f(1.0, 1.0, 0.0)  # Yellow
        glBegin(GL_LINES)
        # 9
        glVertex2f(-8, 8)
        glVertex2f(-2, 8)
        glVertex2f(-2, 8)
        glVertex2f(-2, 2)
        glVertex2f(-2, 2)
        glVertex2f(-8, 2)
        glVertex2f(-8, 2)
        glVertex2f(-8, -8)
        glVertex2f(-8, -8)
        glVertex2f(-2, -8)
        # P
        glVertex2f(2, 8)
        glVertex2f(2, -8)
        glVertex2f(2, 8)
        glVertex2f(8, 8)
        glVertex2f(8, 8)
        glVertex2f(8, 0)
        glVertex2f(8, 0)
        glVertex2f(2, 0)
        glEnd()

    def draw_item_list(self, node_data: Dict[str, Any]):
        """Draw ItemList node"""
        rect_size = node_data.get("rect_size", [200.0, 300.0])
        items = node_data.get("items", [])
        selected_items = node_data.get("selected_items", [])
        background_color = node_data.get("background_color", [0.1, 0.1, 0.1, 1.0])
        item_color_selected = node_data.get("item_color_selected", [0.3, 0.5, 0.8, 1.0])
        icon_mode = node_data.get("icon_mode", "top")
        max_columns = node_data.get("max_columns", 1)

        # Draw background
        glColor4f(background_color[0], background_color[1], background_color[2], background_color[3])
        glBegin(GL_QUADS)
        glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, rect_size[1]/2)
        glVertex2f(-rect_size[0]/2, rect_size[1]/2)
        glEnd()

        # Draw border
        glColor3f(0.5, 0.5, 0.5)
        glLineWidth(1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, -rect_size[1]/2)
        glVertex2f(rect_size[0]/2, rect_size[1]/2)
        glVertex2f(-rect_size[0]/2, rect_size[1]/2)
        glEnd()

        # Draw items (simplified visualization)
        if items:
            item_height = 20.0
            item_spacing = 2.0
            items_per_column = int((rect_size[1] - 10) / (item_height + item_spacing))

            if max_columns > 1:
                column_width = rect_size[0] / max_columns
            else:
                column_width = rect_size[0] - 10

            for i in range(min(len(items), 10)):  # Show max 10 items for preview
                column = i // items_per_column if max_columns > 1 else 0
                row = i % items_per_column

                if column >= max_columns:
                    break

                # Calculate item position
                item_x = -rect_size[0]/2 + 5 + column * column_width
                item_y = rect_size[1]/2 - 5 - row * (item_height + item_spacing)

                # Draw selection background if selected
                if i in selected_items:
                    glColor4f(item_color_selected[0], item_color_selected[1],
                             item_color_selected[2], item_color_selected[3])
                    glBegin(GL_QUADS)
                    glVertex2f(item_x, item_y - item_height)
                    glVertex2f(item_x + column_width - 10, item_y - item_height)
                    glVertex2f(item_x + column_width - 10, item_y)
                    glVertex2f(item_x, item_y)
                    glEnd()

                # Draw item indicator (simplified)
                glColor3f(0.8, 0.8, 0.8)  # Light gray for items
                glBegin(GL_LINE_LOOP)
                glVertex2f(item_x, item_y - item_height)
                glVertex2f(item_x + column_width - 10, item_y - item_height)
                glVertex2f(item_x + column_width - 10, item_y)
                glVertex2f(item_x, item_y)
                glEnd()

                # Draw icon placeholder if icon mode is left
                if icon_mode == "left":
                    glColor3f(0.6, 0.6, 0.8)  # Light blue for icon
                    glBegin(GL_QUADS)
                    glVertex2f(item_x + 2, item_y - item_height + 2)
                    glVertex2f(item_x + 16, item_y - item_height + 2)
                    glVertex2f(item_x + 16, item_y - 4)
                    glVertex2f(item_x + 2, item_y - 4)
                    glEnd()

        # Draw scroll indicator if needed
        if len(items) > 10:
            glColor3f(0.6, 0.6, 0.8)  # Light blue for scroll
            glBegin(GL_LINES)
            # Scroll bar on right side
            scroll_x = rect_size[0]/2 - 3
            glVertex2f(scroll_x, -rect_size[1]/2 + 5)
            glVertex2f(scroll_x, rect_size[1]/2 - 5)
            # Scroll thumb
            glVertex2f(scroll_x - 2, rect_size[1]/4)
            glVertex2f(scroll_x + 2, rect_size[1]/4)
            glVertex2f(scroll_x - 2, rect_size[1]/4 - 20)
            glVertex2f(scroll_x + 2, rect_size[1]/4 - 20)
            glEnd()

        # Draw "IL" indicator for ItemList
        glColor3f(1.0, 1.0, 0.0)  # Yellow
        glBegin(GL_LINES)
        # I
        glVertex2f(-8, 8)
        glVertex2f(-8, -8)
        glVertex2f(-10, 8)
        glVertex2f(-6, 8)
        glVertex2f(-10, -8)
        glVertex2f(-6, -8)
        # L
        glVertex2f(2, 8)
        glVertex2f(2, -8)
        glVertex2f(2, -8)
        glVertex2f(8, -8)
        glEnd()

    def draw_ui_node(self, node_data: Dict[str, Any]):
        """Generic UI node drawing - handles all UI node types dynamically"""
        node_type = node_data.get("type", "Control")

        # UI nodes now use 'size' property instead of 'rect_size'
        rect_size = node_data.get("size", node_data.get("rect_size", [100.0, 30.0]))

        # Get UI-specific properties
        background_color = node_data.get("background_color", [0.2, 0.2, 0.2, 0.8])
        border_color = node_data.get("border_color", [0.5, 0.5, 0.5, 1.0])
        border_width = node_data.get("border_width", 1.0)

        # Ensure rect_size is a valid list
        if not isinstance(rect_size, list) or len(rect_size) < 2:
            rect_size = [100.0, 30.0]

        # Draw background if visible
        if background_color[3] > 0:  # Alpha > 0
            glColor4f(background_color[0], background_color[1], background_color[2], background_color[3])
            glBegin(GL_QUADS)
            glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, rect_size[1]/2)
            glVertex2f(-rect_size[0]/2, rect_size[1]/2)
            glEnd()

        # Draw border
        if border_width > 0:
            glColor3f(border_color[0], border_color[1], border_color[2])
            glLineWidth(border_width)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, -rect_size[1]/2)
            glVertex2f(rect_size[0]/2, rect_size[1]/2)
            glVertex2f(-rect_size[0]/2, rect_size[1]/2)
            glEnd()
            glLineWidth(1.0)

        # Draw type-specific indicators
        self.draw_ui_type_indicator(node_type, rect_size)

    def draw_ui_type_indicator(self, node_type: str, rect_size: list):
        """Draw type-specific indicator for UI nodes"""
        # Draw a small icon or text to indicate the node type
        glColor3f(1.0, 1.0, 1.0)

        # Simple text indicators for different UI types
        if node_type == "Button":
            self.draw_simple_text("BTN", 0, 0, 8)
        elif node_type == "Label":
            self.draw_simple_text("LBL", 0, 0, 8)
        elif node_type == "Panel":
            self.draw_simple_text("PNL", 0, 0, 8)
        elif node_type == "ProgressBar":
            self.draw_simple_text("PGB", 0, 0, 8)
        elif node_type == "ColorRect":
            self.draw_simple_text("CLR", 0, 0, 8)
        elif node_type == "TextureRect":
            self.draw_simple_text("TEX", 0, 0, 8)
        elif node_type == "NinePatchRect":
            self.draw_simple_text("9PT", 0, 0, 8)
        elif node_type == "VBoxContainer":
            self.draw_simple_text("VBX", 0, 0, 8)
        elif node_type == "HBoxContainer":
            self.draw_simple_text("HBX", 0, 0, 8)
        elif node_type == "CenterContainer":
            self.draw_simple_text("CTR", 0, 0, 8)
        elif node_type == "GridContainer":
            self.draw_simple_text("GRD", 0, 0, 8)
        elif node_type == "PanelContainer":
            self.draw_simple_text("PC", 0, 0, 8)
        elif node_type == "LineEdit":
            self.draw_simple_text("EDT", 0, 0, 8)
        elif node_type == "CheckBox":
            self.draw_simple_text("CHK", 0, 0, 8)
        elif node_type == "Slider":
            self.draw_simple_text("SLD", 0, 0, 8)
        elif node_type == "ScrollContainer":
            self.draw_simple_text("SCR", 0, 0, 8)
        elif node_type == "ItemList":
            self.draw_simple_text("LST", 0, 0, 8)
        elif node_type == "HSeparator":
            self.draw_simple_text("H-", 0, 0, 8)
        elif node_type == "VSeparator":
            self.draw_simple_text("V|", 0, 0, 8)
        elif node_type == "RichTextLabel":
            self.draw_simple_text("RTL", 0, 0, 8)
        else:
            # Generic UI indicator
            self.draw_simple_text("UI", 0, 0, 8)

    def draw_canvas_layer(self, node_data: Dict[str, Any]):
        """Draw CanvasLayer node"""
        # Get canvas layer properties
        layer = node_data.get("layer", 1)
        offset = node_data.get("offset", [0.0, 0.0])
        rotation = node_data.get("rotation", 0.0)
        scale = node_data.get("scale", [1.0, 1.0])
        follow_viewport_enable = node_data.get("follow_viewport_enable", False)

        # Draw layer bounds (large dashed rectangle)
        glColor3f(0.9, 0.6, 0.2)  # Orange for canvas layers
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(2, 0x5555)  # Dashed line pattern
        glLineWidth(2.0)

        # Draw a large rectangle representing the layer
        layer_size = 200  # Fixed size for visualization
        glBegin(GL_LINE_LOOP)
        glVertex2f(-layer_size, -layer_size)
        glVertex2f(layer_size, -layer_size)
        glVertex2f(layer_size, layer_size)
        glVertex2f(-layer_size, layer_size)
        glEnd()

        glDisable(GL_LINE_STIPPLE)
        glLineWidth(1.0)

        # Draw layer number in center
        glColor3f(1.0, 0.8, 0.4)
        # Draw layer indicator (simplified "L" + number)
        glBegin(GL_LINES)
        # "L" shape
        glVertex2f(-10, -15)
        glVertex2f(-10, 15)
        glVertex2f(-10, -15)
        glVertex2f(5, -15)

        # Layer number representation (simplified bars)
        for i in range(min(layer, 5)):  # Show up to 5 bars
            x_offset = 10 + i * 4
            glVertex2f(x_offset, -10)
            glVertex2f(x_offset, 10)
        glEnd()

        # Draw transform indicators if not default
        if offset != [0.0, 0.0] or rotation != 0.0 or scale != [1.0, 1.0]:
            glColor3f(0.7, 0.9, 0.7)  # Light green for transform
            # Draw small transform indicator
            glBegin(GL_LINES)
            # Offset arrow
            if offset != [0.0, 0.0]:
                glVertex2f(0, 0)
                glVertex2f(offset[0] * 0.1, offset[1] * 0.1)  # Scale down for visibility

            # Scale indicator (corner marks)
            if scale != [1.0, 1.0]:
                scale_size = 5 * scale[0]  # Use X scale for size
                glVertex2f(-scale_size, -scale_size)
                glVertex2f(-scale_size + 3, -scale_size)
                glVertex2f(-scale_size, -scale_size)
                glVertex2f(-scale_size, -scale_size + 3)
            glEnd()

        # Draw viewport following indicator
        if follow_viewport_enable:
            glColor3f(0.2, 0.8, 1.0)  # Cyan for viewport following
            # Draw "V" for viewport
            glBegin(GL_LINES)
            glVertex2f(layer_size - 20, layer_size - 5)
            glVertex2f(layer_size - 15, layer_size - 15)
            glVertex2f(layer_size - 15, layer_size - 15)
            glVertex2f(layer_size - 10, layer_size - 5)
            glEnd()

    def draw_collision_shape(self, node_data: Dict[str, Any]):
        """Draw CollisionShape2D node"""
        shape_type = node_data.get("shape", "rectangle")
        disabled = node_data.get("disabled", False)
        debug_color = node_data.get("debug_color", [0.0, 0.6, 0.7, 0.5])

        if disabled:
            glColor3f(0.3, 0.3, 0.3)  # Gray for disabled
        else:
            glColor3f(debug_color[0], debug_color[1], debug_color[2])  # Use debug color

        glLineWidth(2.0)

        if shape_type == "rectangle":
            size = node_data.get("size", [32, 32])
            width, height = size[0], size[1]

            glBegin(GL_LINE_LOOP)
            glVertex2f(-width/2, -height/2)
            glVertex2f(width/2, -height/2)
            glVertex2f(width/2, height/2)
            glVertex2f(-width/2, height/2)
            glEnd()

        elif shape_type == "circle":
            radius = node_data.get("radius", 16.0)
            segments = 32

            glBegin(GL_LINE_LOOP)
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                glVertex2f(x, y)
            glEnd()

        elif shape_type == "capsule":
            radius = node_data.get("capsule_radius", 16.0)
            height = node_data.get("height", 32.0)

            # Draw capsule as two circles connected by lines
            segments = 16

            # Top circle
            glBegin(GL_LINE_STRIP)
            for i in range(segments + 1):
                angle = math.pi * i / segments  # Half circle
                x = radius * math.cos(angle)
                y = radius * math.sin(angle) + height/2 - radius
                glVertex2f(x, y)
            glEnd()

            # Bottom circle
            glBegin(GL_LINE_STRIP)
            for i in range(segments + 1):
                angle = math.pi + math.pi * i / segments  # Other half circle
                x = radius * math.cos(angle)
                y = radius * math.sin(angle) - height/2 + radius
                glVertex2f(x, y)
            glEnd()

            # Side lines
            glBegin(GL_LINES)
            glVertex2f(-radius, height/2 - radius)
            glVertex2f(-radius, -height/2 + radius)
            glVertex2f(radius, height/2 - radius)
            glVertex2f(radius, -height/2 + radius)
            glEnd()

        elif shape_type == "segment":
            point_a = node_data.get("point_a", [0, 0])
            point_b = node_data.get("point_b", [32, 0])

            glLineWidth(4.0)
            glBegin(GL_LINES)
            glVertex2f(point_a[0], point_a[1])
            glVertex2f(point_b[0], point_b[1])
            glEnd()

        glLineWidth(1.0)

    def draw_collision_polygon(self, node_data: Dict[str, Any]):
        """Draw CollisionPolygon2D node"""
        polygon = node_data.get("polygon", [[0, 0], [32, 0], [32, 32], [0, 32]])
        disabled = node_data.get("disabled", False)
        debug_color = node_data.get("debug_color", [0.0, 0.6, 0.7, 0.5])

        if disabled:
            glColor3f(0.3, 0.3, 0.3)  # Gray for disabled
        else:
            glColor3f(debug_color[0], debug_color[1], debug_color[2])  # Use debug color

        glLineWidth(2.0)

        if len(polygon) >= 3:
            glBegin(GL_LINE_LOOP)
            for vertex in polygon:
                if isinstance(vertex, list) and len(vertex) >= 2:
                    glVertex2f(vertex[0], vertex[1])
            glEnd()

        glLineWidth(1.0)

    def draw_area2d(self, node_data: Dict[str, Any]):
        """Draw Area2D node"""
        monitoring = node_data.get("monitoring", True)
        monitorable = node_data.get("monitorable", True)

        if monitoring and monitorable:
            glColor3f(0.0, 1.0, 0.0)  # Green for both
        elif monitoring:
            glColor3f(0.0, 0.0, 1.0)  # Blue for monitoring only
        elif monitorable:
            glColor3f(1.0, 1.0, 0.0)  # Yellow for monitorable only
        else:
            glColor3f(0.5, 0.5, 0.5)  # Gray for disabled

        # Draw area indicator (dashed circle)
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(2, 0x5555)
        glLineWidth(2.0)

        segments = 32
        radius = 30

        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            glVertex2f(x, y)
        glEnd()

        glDisable(GL_LINE_STIPPLE)
        glLineWidth(1.0)

        # Draw "A" in center for Area
        glBegin(GL_LINES)
        # A shape
        glVertex2f(-8, -10)
        glVertex2f(0, 10)
        glVertex2f(0, 10)
        glVertex2f(8, -10)
        glVertex2f(-4, 0)
        glVertex2f(4, 0)
        glEnd()

    def draw_rigid_body(self, node_data: Dict[str, Any]):
        """Draw RigidBody2D node"""
        mode = node_data.get("mode", "rigid")
        sleeping = node_data.get("sleeping", False)

        if sleeping:
            glColor3f(0.3, 0.3, 0.7)  # Dark blue for sleeping
        else:
            glColor3f(0.0, 0.7, 1.0)  # Cyan for active

        # Draw physics body indicator (solid circle)
        segments = 16
        radius = 20

        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            glVertex2f(x, y)
        glEnd()

        # Draw "R" in center
        glBegin(GL_LINES)
        # R shape
        glVertex2f(-6, -8)
        glVertex2f(-6, 8)
        glVertex2f(-6, 8)
        glVertex2f(2, 8)
        glVertex2f(2, 8)
        glVertex2f(2, 0)
        glVertex2f(2, 0)
        glVertex2f(-6, 0)
        glVertex2f(-2, 0)
        glVertex2f(4, -8)
        glEnd()

    def draw_static_body(self, node_data: Dict[str, Any]):
        """Draw StaticBody2D node"""
        constant_velocity = node_data.get("constant_linear_velocity", [0, 0])
        is_moving = constant_velocity[0] != 0 or constant_velocity[1] != 0

        if is_moving:
            glColor3f(1.0, 0.5, 0.0)  # Orange for moving static
        else:
            glColor3f(0.7, 0.7, 0.7)  # Gray for static

        # Draw static body indicator (square)
        size = 20

        glBegin(GL_LINE_LOOP)
        glVertex2f(-size, -size)
        glVertex2f(size, -size)
        glVertex2f(size, size)
        glVertex2f(-size, size)
        glEnd()

        # Draw "S" in center
        glBegin(GL_LINES)
        # S shape (simplified)
        glVertex2f(-4, 6)
        glVertex2f(4, 6)
        glVertex2f(-4, 6)
        glVertex2f(-4, 0)
        glVertex2f(-4, 0)
        glVertex2f(4, 0)
        glVertex2f(4, 0)
        glVertex2f(4, -6)
        glVertex2f(4, -6)
        glVertex2f(-4, -6)
        glEnd()

    def draw_kinematic_body(self, node_data: Dict[str, Any]):
        """Draw KinematicBody2D node"""
        glColor3f(1.0, 0.0, 1.0)  # Magenta for kinematic

        # Draw kinematic body indicator (diamond)
        size = 20

        glBegin(GL_LINE_LOOP)
        glVertex2f(0, size)
        glVertex2f(size, 0)
        glVertex2f(0, -size)
        glVertex2f(-size, 0)
        glEnd()

        # Draw "K" in center
        glBegin(GL_LINES)
        # K shape
        glVertex2f(-6, -8)
        glVertex2f(-6, 8)
        glVertex2f(-6, 0)
        glVertex2f(6, 8)
        glVertex2f(-6, 0)
        glVertex2f(6, -8)
        glEnd()

    def draw_light2d(self, node_data: Dict[str, Any]):
        """Draw Light2D node"""
        color = node_data.get("color", [1.0, 1.0, 1.0, 1.0])
        energy = node_data.get("energy", 1.0)
        range_value = node_data.get("range", 200.0)
        mode = node_data.get("mode", "Additive")

        # Set color based on light properties
        glColor3f(color[0] * energy, color[1] * energy, color[2] * energy)

        # Draw light range circle
        glBegin(GL_LINE_LOOP)
        segments = 32
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = range_value * math.cos(angle)
            y = range_value * math.sin(angle)
            glVertex2f(x, y)
        glEnd()

        # Draw light center
        glBegin(GL_LINES)
        # Cross pattern
        glVertex2f(-10, 0)
        glVertex2f(10, 0)
        glVertex2f(0, -10)
        glVertex2f(0, 10)
        glEnd()

        # Draw mode indicator
        if mode == "Additive":
            # Draw "+" symbol
            glBegin(GL_LINES)
            glVertex2f(-5, -15)
            glVertex2f(5, -15)
            glVertex2f(0, -20)
            glVertex2f(0, -10)
            glEnd()
        elif mode == "Subtractive":
            # Draw "-" symbol
            glBegin(GL_LINES)
            glVertex2f(-5, -15)
            glVertex2f(5, -15)
            glEnd()

    def draw_tilemap(self, node_data: Dict[str, Any]):
        """Draw TileMap node"""
        cell_size = node_data.get("cell_size", [32.0, 32.0])
        tiles = node_data.get("tiles", {})
        modulate = node_data.get("modulate", [1.0, 1.0, 1.0, 1.0])

        # Set color
        glColor3f(modulate[0], modulate[1], modulate[2])

        # Draw grid for tilemap
        if tiles:
            # Find bounds of tiles
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')

            for key in tiles.keys():
                x, y = map(int, key.split(','))
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

            # Draw grid lines
            glBegin(GL_LINES)
            for x in range(min_x, max_x + 2):
                world_x = x * cell_size[0]
                glVertex2f(world_x, min_y * cell_size[1])
                glVertex2f(world_x, (max_y + 1) * cell_size[1])

            for y in range(min_y, max_y + 2):
                world_y = y * cell_size[1]
                glVertex2f(min_x * cell_size[0], world_y)
                glVertex2f((max_x + 1) * cell_size[0], world_y)
            glEnd()

            # Draw filled tiles
            glColor3f(0.8, 0.8, 0.8)
            for key, tile_id in tiles.items():
                if tile_id >= 0:
                    x, y = map(int, key.split(','))
                    world_x = x * cell_size[0]
                    world_y = y * cell_size[1]

                    glBegin(GL_QUADS)
                    glVertex2f(world_x, world_y)
                    glVertex2f(world_x + cell_size[0], world_y)
                    glVertex2f(world_x + cell_size[0], world_y + cell_size[1])
                    glVertex2f(world_x, world_y + cell_size[1])
                    glEnd()
        else:
            # Draw placeholder grid
            glBegin(GL_LINE_LOOP)
            glVertex2f(0, 0)
            glVertex2f(cell_size[0] * 3, 0)
            glVertex2f(cell_size[0] * 3, cell_size[1] * 3)
            glVertex2f(0, cell_size[1] * 3)
            glEnd()

    def draw_raycast2d(self, node_data: Dict[str, Any]):
        """Draw RayCast2D node"""
        cast_to = node_data.get("cast_to", [100.0, 0.0])
        enabled = node_data.get("enabled", True)

        # Set color based on enabled state
        if enabled:
            glColor3f(0.0, 1.0, 0.0)  # Green when enabled
        else:
            glColor3f(0.5, 0.5, 0.5)  # Gray when disabled

        # Draw ray line
        glBegin(GL_LINES)
        glVertex2f(0, 0)
        glVertex2f(cast_to[0], cast_to[1])
        glEnd()

        # Draw arrowhead at the end
        import math
        length = math.sqrt(cast_to[0]**2 + cast_to[1]**2)
        if length > 0:
            # Normalize direction
            dir_x = cast_to[0] / length
            dir_y = cast_to[1] / length

            # Arrow size
            arrow_size = 10

            # Calculate arrow points
            end_x = cast_to[0]
            end_y = cast_to[1]

            # Arrow wings
            wing1_x = end_x - arrow_size * (dir_x * 0.8 + dir_y * 0.6)
            wing1_y = end_y - arrow_size * (dir_y * 0.8 - dir_x * 0.6)
            wing2_x = end_x - arrow_size * (dir_x * 0.8 - dir_y * 0.6)
            wing2_y = end_y - arrow_size * (dir_y * 0.8 + dir_x * 0.6)

            glBegin(GL_LINES)
            glVertex2f(end_x, end_y)
            glVertex2f(wing1_x, wing1_y)
            glVertex2f(end_x, end_y)
            glVertex2f(wing2_x, wing2_y)
            glEnd()

    def draw_path2d(self, node_data: Dict[str, Any]):
        """Draw Path2D node"""
        curve = node_data.get("curve", [])
        show_curve = node_data.get("show_curve", True)

        if not show_curve or not curve:
            # Draw placeholder
            glColor3f(0.8, 0.4, 0.8)  # Purple for path
            glBegin(GL_LINE_LOOP)
            glVertex2f(-10, -10)
            glVertex2f(10, -10)
            glVertex2f(10, 10)
            glVertex2f(-10, 10)
            glEnd()
            return

        # Draw path curve
        glColor3f(0.8, 0.4, 0.8)  # Purple for path

        if len(curve) >= 2:
            glBegin(GL_LINE_STRIP)
            for point in curve:
                glVertex2f(point[0], point[1])
            glEnd()

        # Draw control points
        glColor3f(1.0, 0.8, 1.0)  # Light purple for points
        for point in curve:
            glBegin(GL_LINE_LOOP)
            size = 3
            glVertex2f(point[0] - size, point[1] - size)
            glVertex2f(point[0] + size, point[1] - size)
            glVertex2f(point[0] + size, point[1] + size)
            glVertex2f(point[0] - size, point[1] + size)
            glEnd()

    def draw_pathfollow2d(self, node_data: Dict[str, Any]):
        """Draw PathFollow2D node"""
        offset = node_data.get("offset", 0.0)
        unit_offset = node_data.get("unit_offset", 0.0)
        allow_rotate = node_data.get("allow_rotate", False)

        # Draw follower indicator
        glColor3f(0.4, 0.8, 0.8)  # Cyan for follower

        # Draw diamond shape
        size = 8
        glBegin(GL_LINE_LOOP)
        glVertex2f(0, size)
        glVertex2f(size, 0)
        glVertex2f(0, -size)
        glVertex2f(-size, 0)
        glEnd()

        # Draw rotation indicator if enabled
        if allow_rotate:
            glBegin(GL_LINES)
            glVertex2f(0, 0)
            glVertex2f(size + 5, 0)
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
        """Handle mouse press with improved safety checks"""
        try:
            self.last_mouse_pos = event.position()

            if event.button() == Qt.MouseButton.MiddleButton:
                self.is_panning = True
            elif event.button() == Qt.MouseButton.LeftButton:
                # Convert screen coordinates to world coordinates
                world_pos = self.screen_to_world(event.position().x(), event.position().y())

                # Check for gizmo interaction first
                if self.selected_node and isinstance(self.selected_node, dict):
                    gizmo_type = self.check_gizmo_hit(world_pos[0], world_pos[1])
                    if gizmo_type:
                        if gizmo_type == "move":
                            self.is_dragging = True
                        elif gizmo_type == "rotate":
                            self.is_rotating = True
                        elif gizmo_type == "scale":
                            self.is_scaling = True

                        self.drag_start_pos = world_pos
                        # All nodes now use the same position property
                        node_pos = self.selected_node.get("position", [0, 0])

                        if isinstance(node_pos, list) and len(node_pos) >= 2:
                            self.drag_start_node_pos = [float(node_pos[0]), float(node_pos[1])]
                        else:
                            self.drag_start_node_pos = [0.0, 0.0]
                        return

                # Check for node selection
                clicked_node = self.get_node_at_position(world_pos[0], world_pos[1])
                if clicked_node and isinstance(clicked_node, dict):
                    # If we clicked on a different node, select it
                    if self.selected_node != clicked_node:
                        self.selected_node = clicked_node
                        self.node_selected.emit(clicked_node)

                    # Always allow dragging when clicking on a node (even if no gizmo is hit)
                    # This allows dragging by clicking anywhere on the node body
                    self.is_dragging = True
                    self.drag_start_pos = world_pos
                    # All nodes use the same position property now
                    node_pos = clicked_node.get("position", [0, 0])
                    if isinstance(node_pos, list) and len(node_pos) >= 2:
                        self.drag_start_node_pos = [float(node_pos[0]), float(node_pos[1])]
                    else:
                        self.drag_start_node_pos = [0.0, 0.0]
                else:
                    self.selected_node = None

                self.update()
        except Exception as e:
            print(f"Error in mousePressEvent: {e}")
            import traceback
            traceback.print_exc()
            # Reset states to prevent stuck interactions
            self.is_dragging = False
            self.is_rotating = False
            self.is_scaling = False
            self.is_panning = False
    
    def mouseMoveEvent(self, event):
        """Handle mouse move with improved safety checks"""
        try:
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
            elif self.is_dragging and self.selected_node and isinstance(self.selected_node, dict):
                # Handle node dragging with safety checks
                world_pos = self.screen_to_world(event.position().x(), event.position().y())

                if (self.drag_start_pos and self.drag_start_node_pos is not None and
                    isinstance(self.drag_start_pos, (list, tuple)) and len(self.drag_start_pos) >= 2 and
                    isinstance(self.drag_start_node_pos, list) and len(self.drag_start_node_pos) >= 2):

                    # Calculate delta movement in world space
                    delta_x = world_pos[0] - self.drag_start_pos[0]
                    delta_y = world_pos[1] - self.drag_start_pos[1]

                    # Calculate new position based on node type
                    follow_viewport = self.selected_node.get("follow_viewport", False)

                    if follow_viewport:
                        # For UI nodes, convert world delta to UI delta
                        # World delta is in world coordinates, need to convert to UI coordinates
                        # Use the same scaling as the coordinate conversion
                        ui_delta_x = delta_x * self.game_width / self.view_width
                        ui_delta_y = -delta_y * self.game_height / self.view_height  # Flip Y

                        new_pos = [
                            self.drag_start_node_pos[0] + ui_delta_x,
                            self.drag_start_node_pos[1] + ui_delta_y
                        ]

                        # Clamp to game bounds for UI nodes
                        new_pos[0] = max(0, min(new_pos[0], self.game_width))
                        new_pos[1] = max(0, min(new_pos[1], self.game_height))

                        self.selected_node["position"] = new_pos
                        delta_for_children = [ui_delta_x, ui_delta_y]
                    else:
                        # For regular nodes, use world coordinates directly
                        new_pos = [
                            self.drag_start_node_pos[0] + delta_x,
                            self.drag_start_node_pos[1] + delta_y
                        ]
                        self.selected_node["position"] = new_pos
                        delta_for_children = [delta_x, delta_y]

                    position_property = "position"

                    # Apply recursive transformation to children with safety checks
                    try:
                        self.apply_recursive_transform(self.selected_node, position_property, delta_for_children)
                    except Exception as e:
                        print(f"Error in recursive transform during drag: {e}")
                        # Continue without crashing - just skip child updates

                    # Emit signal for inspector update
                    try:
                        self.node_modified.emit(self.selected_node, position_property, new_pos)
                    except Exception as e:
                        print(f"Error emitting node_modified signal: {e}")

                self.update()
            elif self.is_rotating and self.selected_node and isinstance(self.selected_node, dict):
                # Handle node rotation with safety checks
                world_pos = self.screen_to_world(event.position().x(), event.position().y())

                if self.drag_start_pos and isinstance(self.drag_start_pos, (list, tuple)) and len(self.drag_start_pos) >= 2:
                    node_pos = self.selected_node.get("position", [0, 0])
                    if isinstance(node_pos, list) and len(node_pos) >= 2:
                        # Calculate angles from node center
                        start_angle = math.atan2(self.drag_start_pos[1] - node_pos[1], self.drag_start_pos[0] - node_pos[0])
                        current_angle = math.atan2(world_pos[1] - node_pos[1], world_pos[0] - node_pos[0])

                        # Calculate rotation delta
                        rotation_delta = current_angle - start_angle

                        # Update node rotation
                        current_rotation = self.selected_node.get("rotation", 0.0)
                        new_rotation = current_rotation + rotation_delta
                        self.selected_node["rotation"] = new_rotation

                        # Apply recursive transformation to children
                        try:
                            self.apply_recursive_transform(self.selected_node, "rotation", rotation_delta)
                        except Exception as e:
                            print(f"Error in recursive transform during rotation: {e}")

                        # Update start angle for next frame
                        self.drag_start_pos = world_pos

                        # Emit signal for inspector update
                        try:
                            self.node_modified.emit(self.selected_node, "rotation", new_rotation)
                        except Exception as e:
                            print(f"Error emitting rotation signal: {e}")

                self.update()
            elif self.is_scaling and self.selected_node and isinstance(self.selected_node, dict):
                # Handle node scaling with safety checks
                world_pos = self.screen_to_world(event.position().x(), event.position().y())

                if self.drag_start_pos and isinstance(self.drag_start_pos, (list, tuple)) and len(self.drag_start_pos) >= 2:
                    node_pos = self.selected_node.get("position", [0, 0])
                    if isinstance(node_pos, list) and len(node_pos) >= 2:
                        # Calculate distances from node center
                        start_distance = math.sqrt((self.drag_start_pos[0] - node_pos[0])**2 + (self.drag_start_pos[1] - node_pos[1])**2)
                        current_distance = math.sqrt((world_pos[0] - node_pos[0])**2 + (world_pos[1] - node_pos[1])**2)

                        if start_distance > 0:
                            # Calculate scale factor
                            scale_factor = current_distance / start_distance

                            # Update node scale
                            current_scale = self.selected_node.get("scale", [1.0, 1.0])
                            if isinstance(current_scale, list) and len(current_scale) >= 2:
                                new_scale = [current_scale[0] * scale_factor, current_scale[1] * scale_factor]
                                self.selected_node["scale"] = new_scale

                                # Apply recursive transformation to children
                                try:
                                    self.apply_recursive_transform(self.selected_node, "scale", [scale_factor, scale_factor])
                                except Exception as e:
                                    print(f"Error in recursive transform during scaling: {e}")

                                # Update start position for next frame
                                self.drag_start_pos = world_pos

                                # Emit signal for inspector update
                                try:
                                    self.node_modified.emit(self.selected_node, "scale", new_scale)
                                except Exception as e:
                                    print(f"Error emitting scale signal: {e}")

                self.update()

            self.last_mouse_pos = event.position()
        except Exception as e:
            print(f"Error in mouseMoveEvent: {e}")
            import traceback
            traceback.print_exc()
            # Reset states to prevent stuck interactions
            self.is_dragging = False
            self.is_rotating = False
            self.is_scaling = False

    def apply_recursive_transform(self, parent_node: Dict[str, Any], transform_type: str, delta, visited_nodes=None):
        """Apply transformation recursively to all children with improved safety checks"""
        # Initialize visited nodes set if None
        if visited_nodes is None:
            visited_nodes = set()

        # Skip if node is None or not a dict
        if not isinstance(parent_node, dict):
            return

        # Get a unique identifier for this node based on its position in the hierarchy
        node_path = parent_node.get("name", "") + str(parent_node.get("position", [0, 0]))
        if node_path in visited_nodes:
            return

        visited_nodes.add(node_path)

        try:
            # Validate input parameters
            if not isinstance(parent_node, dict):
                print(f"Warning: Invalid parent node type: {type(parent_node)}")
                return

            if transform_type not in ["position", "rotation", "scale"]:
                print(f"Warning: Invalid transform type: {transform_type}")
                return

            # Get children safely
            children = parent_node.get("children", [])
            if not isinstance(children, list):
                print(f"Warning: Invalid children type: {type(children)}")
                return

            # Process each child
            for child in children:
                if not isinstance(child, dict):
                    print(f"Warning: Skipping invalid child node type: {type(child)}")
                    continue

                # Ensure child has required properties with safe defaults
                self._ensure_node_properties(child)

                # Apply transformation based on type
                if transform_type == "position":
                    self._apply_position_transform(child, delta)
                elif transform_type == "rotation":
                    self._apply_rotation_transform(parent_node, child, delta)
                elif transform_type == "scale":
                    self._apply_scale_transform(parent_node, child, delta)
                else:
                    print(f"Warning: Invalid transform type: {transform_type}")

                # Recursively apply to grandchildren (with visited tracking)
                self.apply_recursive_transform(child, transform_type, delta, visited_nodes.copy())

        except Exception as e:
            print(f"Error in apply_recursive_transform: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up visited tracking for this branch
            visited_nodes.discard(node_path)

    def _ui_to_world_coords(self, ui_position: list) -> list:
        """Convert UI coordinates (game bounds space) to editor world coordinates"""
        # UI coordinates are in game bounds space (0,0 at top-left, Y increases downward)
        # Editor world coordinates are centered at (0,0), Y increases upward

        # Scale UI coordinates to world coordinates based on current view
        # UI coordinates are in game bounds (0 to game_width, 0 to game_height)
        # World coordinates are in view bounds (-view_width/2 to +view_width/2, etc.)

        # Convert UI position to normalized coordinates (0 to 1)
        norm_x = ui_position[0] / self.game_width
        norm_y = ui_position[1] / self.game_height

        # Convert to world coordinates
        world_x = (norm_x - 0.5) * self.view_width
        world_y = (0.5 - norm_y) * self.view_height  # Flip Y axis

        return [world_x, world_y]

    def _world_to_ui_coords(self, world_position):
        """Convert editor world coordinates to UI coordinates (game bounds space)"""
        # World coordinates are in view bounds (-view_width/2 to +view_width/2, etc.)
        # UI coordinates are in game bounds space (0,0 at top-left), Y increases downward

        # Convert world coordinates to normalized coordinates (0 to 1)
        norm_x = (world_position[0] / self.view_width) + 0.5
        norm_y = 0.5 - (world_position[1] / self.view_height)  # Flip Y axis

        # Convert to UI coordinates
        ui_x = norm_x * self.game_width
        ui_y = norm_y * self.game_height

        return [ui_x, ui_y]



    def _ensure_node_properties(self, node: Dict[str, Any]):
        """Ensure node has all required properties with safe defaults"""
        node_type = node.get("type", "")

        # All nodes now use position, rotation, scale consistently
        if "position" not in node or not isinstance(node["position"], list) or len(node["position"]) < 2:
            node["position"] = [0.0, 0.0]

        if "rotation" not in node or not isinstance(node["rotation"], (int, float)):
            node["rotation"] = 0.0

        if "scale" not in node or not isinstance(node["scale"], list) or len(node["scale"]) < 2:
            node["scale"] = [1.0, 1.0]

        # UI nodes also need size property
        if self._is_ui_node(node_type):
            if "size" not in node or not isinstance(node["size"], list) or len(node["size"]) < 2:
                node["size"] = [100.0, 100.0]

            # Ensure follow_viewport property exists
            if "follow_viewport" not in node:
                node["follow_viewport"] = True  # Default for UI nodes

            try:
                node["position"] = [float(node["position"][0]), float(node["position"][1])]
                node["size"] = [float(node["size"][0]), float(node["size"][1])]
                node["rotation"] = float(node["rotation"])
                node["scale"] = [float(node["scale"][0]), float(node["scale"][1])]
            except (ValueError, TypeError, IndexError) as e:
                print(f"Warning: Failed to convert node properties to float: {e}")
                node["position"] = [0.0, 0.0]
                node["size"] = [100.0, 100.0] if self._is_ui_node(node_type) else None
                node["rotation"] = 0.0
                node["scale"] = [1.0, 1.0]
        else:
            try:
                node["position"] = [float(node["position"][0]), float(node["position"][1])]
                node["rotation"] = float(node["rotation"])
                node["scale"] = [float(node["scale"][0]), float(node["scale"][1])]
            except (ValueError, TypeError, IndexError) as e:
                print(f"Warning: Failed to convert node properties to float: {e}")
                node["position"] = [0.0, 0.0]
                node["rotation"] = 0.0
                node["scale"] = [1.0, 1.0]

            # Ensure position and scale are mutable lists with float values
            try:
                node["position"] = [float(node["position"][0]), float(node["position"][1])]
                node["scale"] = [float(node["scale"][0]), float(node["scale"][1])]
                node["rotation"] = float(node["rotation"])
            except (ValueError, TypeError, IndexError) as e:
                print(f"Warning: Failed to convert node properties to float: {e}")
                # Reset to safe defaults
                node["position"] = [0.0, 0.0]
                node["scale"] = [1.0, 1.0]
                node["rotation"] = 0.0

    def _apply_position_transform(self, child: Dict[str, Any], delta):
        """Apply position transformation to a child node"""
        try:
            if not isinstance(delta, list) or len(delta) < 2:
                print(f"Warning: Invalid position delta: {delta}")
                return

            current_pos = child["position"]
            new_pos = [current_pos[0] + float(delta[0]), current_pos[1] + float(delta[1])]
            child["position"] = new_pos

            # Emit signal for this child if it's currently selected
            if child == self.selected_node:
                self.node_modified.emit(child, "position", new_pos)

        except Exception as e:
            print(f"Error applying position transform: {e}")



    def _apply_rotation_transform(self, parent_node: Dict[str, Any], child: Dict[str, Any], delta):
        """Apply rotation transformation to a child node"""
        try:
            if not isinstance(delta, (int, float)):
                print(f"Warning: Invalid rotation delta: {delta}")
                return

            parent_pos = parent_node.get("position", [0.0, 0.0])
            if not isinstance(parent_pos, list) or len(parent_pos) < 2:
                parent_pos = [0.0, 0.0]

            current_pos = child["position"]
            current_rotation = child["rotation"]

            # Calculate relative position from parent
            rel_x = current_pos[0] - parent_pos[0]
            rel_y = current_pos[1] - parent_pos[1]

            # Rotate the relative position
            import math
            cos_delta = math.cos(float(delta))
            sin_delta = math.sin(float(delta))
            new_rel_x = rel_x * cos_delta - rel_y * sin_delta
            new_rel_y = rel_x * sin_delta + rel_y * cos_delta

            # Update child position and rotation
            new_pos = [parent_pos[0] + new_rel_x, parent_pos[1] + new_rel_y]
            new_rotation = current_rotation + float(delta)

            child["position"] = new_pos
            child["rotation"] = new_rotation

            # Emit signals for this child if it's currently selected
            if child == self.selected_node:
                self.node_modified.emit(child, "position", new_pos)
                self.node_modified.emit(child, "rotation", new_rotation)

        except Exception as e:
            print(f"Error applying rotation transform: {e}")

    def _apply_scale_transform(self, parent_node: Dict[str, Any], child: Dict[str, Any], delta):
        """Apply scale transformation to a child node"""
        try:
            if not isinstance(delta, list) or len(delta) < 2:
                print(f"Warning: Invalid scale delta: {delta}")
                return

            parent_pos = parent_node.get("position", [0.0, 0.0])
            if not isinstance(parent_pos, list) or len(parent_pos) < 2:
                parent_pos = [0.0, 0.0]

            current_pos = child["position"]
            current_scale = child["scale"]

            # Scale position relative to parent
            rel_x = current_pos[0] - parent_pos[0]
            rel_y = current_pos[1] - parent_pos[1]
            new_pos = [parent_pos[0] + rel_x * float(delta[0]), parent_pos[1] + rel_y * float(delta[1])]

            # Scale the child's scale
            new_scale = [current_scale[0] * float(delta[0]), current_scale[1] * float(delta[1])]

            child["position"] = new_pos
            child["scale"] = new_scale

            # Emit signals for this child if it's currently selected
            if child == self.selected_node:
                self.node_modified.emit(child, "position", new_pos)
                self.node_modified.emit(child, "scale", new_scale)

        except Exception as e:
            print(f"Error applying scale transform: {e}")

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
        node_type = node.get("type", "Node")

        # All nodes now use the same position property
        position = node.get("position", [0, 0])

        # Handle coordinate conversion based on follow_viewport setting
        follow_viewport = node.get("follow_viewport", False)
        if follow_viewport:
            # Convert viewport coordinates to world coordinates for comparison
            position = self._ui_to_world_coords(position)

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

        elif hasattr(node, 'size') or 'size' in node:
            # Check node bounds using size property (for UI nodes and others with size)
            size = node.get("size", [100.0, 30.0])

            # Nodes with size are centered on their position
            left = -size[0] / 2
            right = size[0] / 2
            bottom = -size[1] / 2
            top = size[1] / 2

            return left <= local_x <= right and bottom <= local_y <= top

        elif node_type == "Node2D":
            # Check small area around node center
            return abs(local_x) <= 10 and abs(local_y) <= 10

        else:
            # Default node hit area
            return abs(local_x) <= 8 and abs(local_y) <= 8

    def _is_ui_node(self, node_type: str) -> bool:
        """Check if a node type is a UI node - dynamic detection"""
        # Get node definition from registry
        from core.node_registry import get_node_registry
        registry = get_node_registry()
        node_def = registry.get_node_definition(node_type)

        if node_def:
            # Check if it's in UI category
            from core.node_registry import NodeCategory
            return node_def.category == NodeCategory.UI

        # Fallback to hardcoded list for unknown nodes
        ui_node_types = [
            "Control", "Panel", "Label", "Button", "ColorRect", "TextureRect",
            "ProgressBar", "VBoxContainer", "HBoxContainer", "CenterContainer",
            "GridContainer", "RichTextLabel", "PanelContainer", "NinePatchRect",
            "ItemList", "LineEdit", "CheckBox", "Slider", "ScrollContainer",
            "HSeparator", "VSeparator"
        ]
        return node_type in ui_node_types

    def check_gizmo_hit(self, world_x: float, world_y: float) -> Optional[str]:
        """Check if a gizmo handle is hit"""
        if not self.selected_node:
            return None

        # All nodes use the same position property now
        position = self.selected_node.get("position", [0, 0])

        # Handle coordinate conversion based on follow_viewport setting
        follow_viewport = self.selected_node.get("follow_viewport", False)
        if follow_viewport:
            # Convert viewport coordinates to world coordinates for comparison
            position = self._ui_to_world_coords(position)

        local_x = world_x - position[0]
        local_y = world_y - position[1]

        # Scale gizmo size based on zoom for better responsiveness
        base_gizmo_size = 8.0  # Increased base size
        zoom_adjusted_gizmo_size = base_gizmo_size / self.zoom

        # Scale handle distance based on zoom
        base_handle_distance = 40.0  # Increased distance
        zoom_adjusted_handle_distance = base_handle_distance / self.zoom

        # Check scale handles (corners) - larger hit areas
        corner_positions = [
            (zoom_adjusted_handle_distance, zoom_adjusted_handle_distance),
            (-zoom_adjusted_handle_distance, zoom_adjusted_handle_distance),
            (zoom_adjusted_handle_distance, -zoom_adjusted_handle_distance),
            (-zoom_adjusted_handle_distance, -zoom_adjusted_handle_distance)
        ]

        for corner_x, corner_y in corner_positions:
            if (abs(local_x - corner_x) <= zoom_adjusted_gizmo_size and
                abs(local_y - corner_y) <= zoom_adjusted_gizmo_size):
                return "scale"

        # Check rotation handle - larger tolerance
        rotation_distance = math.sqrt(local_x**2 + local_y**2)
        rotation_tolerance = zoom_adjusted_gizmo_size * 1.5  # Increased tolerance
        if abs(rotation_distance - self.rotation_handle_distance) <= rotation_tolerance:
            return "rotate"

        # Check move handle (center area) - larger area
        move_area_size = 20.0 / self.zoom  # Scale with zoom
        if abs(local_x) <= move_area_size and abs(local_y) <= move_area_size:
            return "move"

        return None

    def draw_selection_gizmos(self):
        """Draw selection and transformation gizmos"""
        if not self.selected_node:
            return

        # All nodes use the same position property now
        position = self.selected_node.get("position", [0, 0])

        # Handle coordinate conversion based on follow_viewport setting
        follow_viewport = self.selected_node.get("follow_viewport", False)
        if follow_viewport:
            # Convert viewport coordinates to world coordinates for drawing
            position = self._ui_to_world_coords(position)

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
        elif node_type in ["Button", "Panel", "Label", "ColorRect", "TextureRect", "ProgressBar", "VBoxContainer", "HBoxContainer", "CenterContainer", "GridContainer", "RichTextLabel", "PanelContainer", "NinePatchRect", "ItemList"]:
            # Draw around UI node bounds
            size = self.selected_node.get("size", [100.0, 30.0])

            # Convert UI size to world scale for proper gizmo sizing
            world_scale_x = size[0] / self.game_width * self.view_width
            world_scale_y = size[1] / self.game_height * self.view_height

            # UI nodes are centered on their position in the new coordinate system
            left = -world_scale_x / 2
            right = world_scale_x / 2
            bottom = -world_scale_y / 2
            top = world_scale_y / 2

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

        # Scale gizmo size based on zoom for better visibility
        base_gizmo_size = 6.0  # Increased base size
        zoom_adjusted_gizmo_size = base_gizmo_size / self.zoom

        # Scale handle distance based on zoom
        base_handle_distance = 40.0  # Increased distance
        zoom_adjusted_handle_distance = base_handle_distance / self.zoom

        # Corner positions
        corners = [
            (zoom_adjusted_handle_distance, zoom_adjusted_handle_distance),
            (-zoom_adjusted_handle_distance, zoom_adjusted_handle_distance),
            (zoom_adjusted_handle_distance, -zoom_adjusted_handle_distance),
            (-zoom_adjusted_handle_distance, -zoom_adjusted_handle_distance)
        ]

        for x, y in corners:
            glBegin(GL_LINE_LOOP)
            glVertex2f(x - zoom_adjusted_gizmo_size, y - zoom_adjusted_gizmo_size)
            glVertex2f(x + zoom_adjusted_gizmo_size, y - zoom_adjusted_gizmo_size)
            glVertex2f(x + zoom_adjusted_gizmo_size, y + zoom_adjusted_gizmo_size)
            glVertex2f(x - zoom_adjusted_gizmo_size, y + zoom_adjusted_gizmo_size)
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
