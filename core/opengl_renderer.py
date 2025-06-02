"""
OpenGL Renderer for Pygame-based Game Runner
Handles low-level OpenGL operations for sprite rendering, camera management, etc.
"""

import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
from pathlib import Path
from typing import Dict, Tuple, Optional, List


class Texture:
    """OpenGL texture wrapper"""
    
    def __init__(self, texture_id: int, width: int, height: int):
        self.id = texture_id
        self.width = width
        self.height = height
    
    def bind(self):
        """Bind this texture for rendering"""
        glBindTexture(GL_TEXTURE_2D, self.id)
    
    def unbind(self):
        """Unbind texture"""
        glBindTexture(GL_TEXTURE_2D, 0)


class Camera2D:
    """2D Camera for OpenGL rendering"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
        self.rotation = 0.0
    
    def set_position(self, x: float, y: float):
        """Set camera position"""
        self.x = x
        self.y = y
    
    def set_zoom(self, zoom: float):
        """Set camera zoom level"""
        self.zoom = max(0.1, min(10.0, zoom))
    
    def apply_transform(self):
        """Apply camera transformation to OpenGL matrix"""
        glLoadIdentity()

        # Apply zoom
        glScalef(self.zoom, self.zoom, 1.0)

        # Apply rotation
        if self.rotation != 0:
            glRotatef(self.rotation, 0, 0, 1)

        # Apply translation (negative because we move the world, not the camera)
        # Note: Y is NOT inverted here because our projection already handles the coordinate system
        glTranslatef(-self.x, -self.y, 0)


class OpenGLRenderer:
    """Main OpenGL renderer for the game"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.textures: Dict[str, Texture] = {}
        self.camera = Camera2D(width, height)

        # Initialize pygame font system for text rendering
        pygame.font.init()
        self.default_font = pygame.font.Font(None, 24)
        self.font_cache: Dict[Tuple[str, int], pygame.font.Font] = {}

        # Initialize OpenGL settings
        self.setup_opengl()
    
    def setup_opengl(self):
        """Initialize OpenGL settings"""
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Enable 2D textures
        glEnable(GL_TEXTURE_2D)
        
        # Set clear color (dark gray)
        glClearColor(0.2, 0.2, 0.2, 1.0)
        
        # Setup 2D projection
        self.setup_2d_projection()
    
    def setup_2d_projection(self):
        """Setup 2D orthographic projection to match scene view exactly"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # Use the same coordinate system as scene view
        # (0,0) at center, Y+ up, X+ right, no additional scaling
        half_width = self.width / 2
        half_height = self.height / 2

        # Standard orthographic projection - matches scene view exactly
        glOrtho(-half_width, half_width, -half_height, half_height, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def resize(self, width: int, height: int):
        """Handle window resize"""
        self.width = width
        self.height = height
        self.camera.width = width
        self.camera.height = height
        
        glViewport(0, 0, width, height)
        self.setup_2d_projection()
    
    def clear(self):
        """Clear the screen"""
        glClear(GL_COLOR_BUFFER_BIT)
    
    def load_texture(self, path: str) -> Optional[Texture]:
        """Load a texture from file - matches scene view loading exactly"""
        if path in self.textures:
            return self.textures[path]

        try:
            # Load image with PIL - same as scene view
            image = Image.open(path)
            image = image.convert("RGBA")  # Ensure RGBA format

            # Flip vertically to match OpenGL coordinate system (same as scene view)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

            width, height = image.size
            image_data = np.array(image, dtype=np.uint8)

            # Generate OpenGL texture
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)

            # Set texture parameters - same as scene view
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            # Upload texture data
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                        GL_RGBA, GL_UNSIGNED_BYTE, image_data)

            glBindTexture(GL_TEXTURE_2D, 0)

            texture = Texture(texture_id, width, height)
            self.textures[path] = texture
            return texture

        except Exception as e:
            print(f"Failed to load texture {path}: {e}")
            return None
    
    def draw_sprite(self, texture_path: str, x: float, y: float,
                   width: Optional[float] = None, height: Optional[float] = None,
                   rotation: float = 0.0, alpha: float = 1.0):
        """Draw a sprite at the given position"""
        texture = self.load_texture(texture_path)
        if not texture:
            return
        
        # Use texture dimensions if width/height not specified
        if width is None:
            width = texture.width
        if height is None:
            height = texture.height
        
        # Calculate half dimensions for centering
        half_width = width / 2
        half_height = height / 2
        
        glPushMatrix()
        
        # Apply transformations
        glTranslatef(x, y, 0)
        if rotation != 0:
            glRotatef(rotation, 0, 0, 1)
        
        # Set color with alpha
        glColor4f(1.0, 1.0, 1.0, alpha)
        
        # Bind texture and draw quad
        texture.bind()
        
        glBegin(GL_QUADS)
        # Use same texture coordinates as scene view (no Y flip)
        glTexCoord2f(0, 0); glVertex2f(-half_width, -half_height)
        glTexCoord2f(1, 0); glVertex2f(half_width, -half_height)
        glTexCoord2f(1, 1); glVertex2f(half_width, half_height)
        glTexCoord2f(0, 1); glVertex2f(-half_width, half_height)
        glEnd()
        
        texture.unbind()
        glPopMatrix()
    
    def draw_rectangle(self, x: float, y: float, width: float, height: float, 
                      color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                      filled: bool = True):
        """Draw a colored rectangle"""
        glDisable(GL_TEXTURE_2D)
        glColor4f(*color)
        
        half_width = width / 2
        half_height = height / 2
        
        glPushMatrix()
        glTranslatef(x, y, 0)
        
        if filled:
            glBegin(GL_QUADS)
        else:
            glBegin(GL_LINE_LOOP)
        
        glVertex2f(-half_width, -half_height)
        glVertex2f(half_width, -half_height)
        glVertex2f(half_width, half_height)
        glVertex2f(-half_width, half_height)
        glEnd()
        
        glPopMatrix()
        glEnable(GL_TEXTURE_2D)
    
    def begin_camera(self):
        """Begin rendering with camera transform"""
        glPushMatrix()
        self.camera.apply_transform()
    
    def end_camera(self):
        """End camera rendering"""
        glPopMatrix()

    def draw_ui_sprite(self, texture_path: str, x: float, y: float,
                      width: Optional[float] = None, height: Optional[float] = None,
                      rotation: float = 0.0, alpha: float = 1.0):
        """Draw a UI sprite (no camera transform, screen coordinates)"""
        texture = self.load_texture(texture_path)
        if not texture:
            return

        # Use texture dimensions if width/height not specified
        if width is None:
            width = texture.width
        if height is None:
            height = texture.height

        # UI coordinates: (0,0) is top-left, Y increases downward
        # Convert to OpenGL coordinates where (0,0) is center, Y increases upward
        gl_x = x + width / 2 - self.width / 2
        gl_y = self.height / 2 - (y + height / 2)

        # Calculate half dimensions for centering
        half_width = width / 2
        half_height = height / 2

        glPushMatrix()

        # Apply transformations
        glTranslatef(gl_x, gl_y, 0)
        if rotation != 0:
            glRotatef(rotation, 0, 0, 1)

        # Set color with alpha
        glColor4f(1.0, 1.0, 1.0, alpha)

        # Bind texture and draw quad
        texture.bind()

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(-half_width, -half_height)
        glTexCoord2f(1, 0); glVertex2f(half_width, -half_height)
        glTexCoord2f(1, 1); glVertex2f(half_width, half_height)
        glTexCoord2f(0, 1); glVertex2f(-half_width, half_height)
        glEnd()

        texture.unbind()
        glPopMatrix()

    def draw_ui_rectangle(self, x: float, y: float, width: float, height: float,
                         color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                         filled: bool = True):
        """Draw a UI rectangle (no camera transform, screen coordinates)"""
        glDisable(GL_TEXTURE_2D)
        glColor4f(*color)

        # UI coordinates: (0,0) is top-left, Y increases downward
        # Convert to OpenGL coordinates where (0,0) is center, Y increases upward
        gl_x = x + width / 2 - self.width / 2
        gl_y = self.height / 2 - (y + height / 2)

        half_width = width / 2
        half_height = height / 2

        glPushMatrix()
        glTranslatef(gl_x, gl_y, 0)

        if filled:
            glBegin(GL_QUADS)
        else:
            glBegin(GL_LINE_LOOP)

        glVertex2f(-half_width, -half_height)
        glVertex2f(half_width, -half_height)
        glVertex2f(half_width, half_height)
        glVertex2f(-half_width, half_height)
        glEnd()

        glPopMatrix()
        glEnable(GL_TEXTURE_2D)

    def get_font(self, font_name: Optional[str] = None, font_size: int = 24) -> pygame.font.Font:
        """Get a font from cache or create new one"""
        key = (font_name or "default", font_size)
        if key not in self.font_cache:
            if font_name and font_name != "default":
                try:
                    self.font_cache[key] = pygame.font.Font(font_name, font_size)
                except:
                    # Fallback to default font
                    self.font_cache[key] = pygame.font.Font(None, font_size)
            else:
                self.font_cache[key] = pygame.font.Font(None, font_size)
        return self.font_cache[key]

    def create_text_texture(self, text: str, font: pygame.font.Font,
                           color: Tuple[int, int, int, int] = (255, 255, 255, 255)) -> Optional[Texture]:
        """Create a texture from text using pygame font rendering"""
        try:
            # Render text to pygame surface
            text_surface = font.render(text, True, color[:3])

            # Convert to RGBA format
            text_surface = text_surface.convert_alpha()
            width, height = text_surface.get_size()

            # Get raw pixel data
            text_data = pygame.image.tostring(text_surface, 'RGBA', True)

            # Create OpenGL texture
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)

            # Set texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            # Upload texture data
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                        GL_RGBA, GL_UNSIGNED_BYTE, text_data)

            glBindTexture(GL_TEXTURE_2D, 0)

            return Texture(texture_id, width, height)

        except Exception as e:
            print(f"Failed to create text texture: {e}")
            return None

    def draw_ui_text(self, text: str, x: float, y: float,
                    font_name: Optional[str] = None, font_size: int = 24,
                    color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)):
        """Draw text at UI coordinates"""
        if not text:
            return

        # Get font and create text texture
        font = self.get_font(font_name, font_size)

        # Convert color to 0-255 range for pygame
        pygame_color = (int(color[0] * 255), int(color[1] * 255),
                       int(color[2] * 255), int(color[3] * 255))

        # Create a unique key for caching text textures
        text_key = f"text_{text}_{font_name}_{font_size}_{pygame_color}"

        if text_key not in self.textures:
            text_texture = self.create_text_texture(text, font, pygame_color)
            if text_texture:
                self.textures[text_key] = text_texture

        text_texture = self.textures.get(text_key)
        if not text_texture:
            return

        # Draw the text texture
        self.draw_ui_texture(text_texture, x, y, color[3])

    def draw_ui_texture(self, texture: Texture, x: float, y: float, alpha: float = 1.0):
        """Draw a texture at UI coordinates"""
        # UI coordinates: (0,0) is top-left, Y increases downward
        # Convert to OpenGL coordinates where (0,0) is center, Y increases upward
        gl_x = x + texture.width / 2 - self.width / 2
        gl_y = self.height / 2 - (y + texture.height / 2)

        # Calculate half dimensions for centering
        half_width = texture.width / 2
        half_height = texture.height / 2

        glPushMatrix()

        # Apply transformations
        glTranslatef(gl_x, gl_y, 0)

        # Set color with alpha
        glColor4f(1.0, 1.0, 1.0, alpha)

        # Bind texture and draw quad
        texture.bind()

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(-half_width, -half_height)
        glTexCoord2f(1, 0); glVertex2f(half_width, -half_height)
        glTexCoord2f(1, 1); glVertex2f(half_width, half_height)
        glTexCoord2f(0, 1); glVertex2f(-half_width, half_height)
        glEnd()

        texture.unbind()
        glPopMatrix()

    def resize(self, width: int, height: int):
        """Handle window resize"""
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        self.setup_2d_projection()

    def cleanup(self):
        """Clean up OpenGL resources"""
        for texture in self.textures.values():
            glDeleteTextures([texture.id])
        self.textures.clear()
