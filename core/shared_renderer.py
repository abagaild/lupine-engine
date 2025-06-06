"""
Shared OpenGL Renderer for Lupine Engine
Provides consistent rendering between editor and game runner
"""

import math
import os
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from OpenGL.GL import *
import numpy as np

try:
    import pygame
    pygame.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available, text rendering will be limited")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available, texture loading may be limited")


class SharedRenderer:
    """Shared OpenGL renderer for consistent rendering between editor and game runner"""
    
    def __init__(self, width: int, height: int, project_path: Optional[str] = None, auto_setup_gl: bool = False, scaling_filter: str = "linear"):
        self.width = width
        self.height = height
        self.project_path = Path(project_path) if project_path else None
        self.scaling_filter = scaling_filter  # "linear" or "nearest"

        # Texture cache
        self.texture_cache = {}  # path -> (texture_id, width, height)

        # Font cache for text rendering
        self.font_cache = {}  # (font_name, size) -> pygame.font.Font
        self.text_texture_cache = {}  # (text, font_name, size, color) -> (texture_id, width, height)

        # Initialize OpenGL settings only if requested and context is available
        if auto_setup_gl:
            self.setup_opengl()
    
    def setup_opengl(self):
        """Initialize OpenGL settings"""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_TEXTURE_2D)

        # Setup 2D projection matrix
        self.setup_2d_projection()

    def setup_2d_projection(self):
        """Setup 2D orthographic projection"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # Set up orthographic projection (0,0 at top-left, like most 2D engines)
        glOrtho(0, self.width, self.height, 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Set viewport
        glViewport(0, 0, self.width, self.height)
    
    def clear(self, color: Tuple[float, float, float, float] = (0.1, 0.1, 0.15, 1.0)):
        """Clear the screen with the specified color"""
        glClearColor(*color)
        glClear(GL_COLOR_BUFFER_BIT)
    
    def load_texture(self, texture_path: str) -> Optional[Tuple[int, int, int]]:
        """Load a texture from file and return (texture_id, width, height)"""
        if not texture_path:
            return None
        
        # Check cache first
        if texture_path in self.texture_cache:
            return self.texture_cache[texture_path]
        
        try:
            # Convert to absolute path
            if not Path(texture_path).is_absolute() and self.project_path:
                full_path = self.project_path / texture_path
            else:
                full_path = Path(texture_path)
            
            if not full_path.exists():
                print(f"Texture file not found: {full_path}")
                return None
            
            if PIL_AVAILABLE:
                return self._load_texture_pil(full_path, texture_path)
            else:
                return self._load_texture_pygame(full_path, texture_path)
                
        except Exception as e:
            print(f"Error loading texture {texture_path}: {e}")
            return None
    
    def _load_texture_pil(self, full_path: Path, texture_path: str) -> Optional[Tuple[int, int, int]]:
        """Load texture using PIL/Pillow"""
        # Load image using PIL
        pil_image = Image.open(str(full_path))
        
        # Convert to RGBA if not already
        if pil_image.mode != 'RGBA':
            pil_image = pil_image.convert('RGBA')
        
        # Get image data
        width, height = pil_image.size
        
        # Flip image vertically for OpenGL (PIL loads top-to-bottom, OpenGL expects bottom-to-top)
        pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)
        image_data = pil_image.tobytes()
        
        # Generate OpenGL texture
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # Set texture parameters based on scaling filter
        if self.scaling_filter == "nearest":
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        else:  # linear
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
    
    def _load_texture_pygame(self, full_path: Path, texture_path: str) -> Optional[Tuple[int, int, int]]:
        """Load texture using pygame as fallback"""
        if not PYGAME_AVAILABLE:
            return None
            
        # Load image using pygame
        surface = pygame.image.load(str(full_path))
        
        # Convert to RGBA format
        surface = surface.convert_alpha()
        width, height = surface.get_size()
        
        # Get image data
        image_data = pygame.image.tostring(surface, 'RGBA', True)
        
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
    
    def draw_sprite(self, texture_path: str, x: float, y: float,
                   width: Optional[float] = None, height: Optional[float] = None,
                   rotation: float = 0.0, alpha: float = 1.0):
        """Draw a sprite at the given position"""
        texture_info = self.load_texture(texture_path)
        if not texture_info:
            # Draw a colored rectangle as fallback (light gray instead of pink)
            self.draw_rectangle(x, y, width or 64, height or 64, (0.8, 0.8, 0.8, alpha))
            return

        texture_id, tex_width, tex_height = texture_info

        # Use texture dimensions if width/height not specified
        if width is None:
            width = tex_width
        if height is None:
            height = tex_height

        # Calculate half dimensions for centering
        half_width = width / 2
        half_height = height / 2

        glPushMatrix()

        # Apply transformations
        glTranslatef(x, y, 0)
        if rotation != 0:
            glRotatef(rotation, 0, 0, 1)

        # Bind texture and set color
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor4f(1.0, 1.0, 1.0, alpha)

        # Draw textured quad
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-half_width, -half_height)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(half_width, -half_height)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(half_width, half_height)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-half_width, half_height)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        glPopMatrix()

    def draw_texture_rect(self, texture_path: str, x: float, y: float,
                         width: float, height: float,
                         stretch_mode: str = "stretch",
                         flip_h: bool = False, flip_v: bool = False,
                         modulate_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                         uv_offset: Tuple[float, float] = (0.0, 0.0),
                         uv_scale: Tuple[float, float] = (1.0, 1.0),
                         rotation: float = 0.0,
                         region_rect: Optional[Tuple[float, float, float, float]] = None):
        """Draw a texture rectangle with advanced features"""
        texture_info = self.load_texture(texture_path)
        if not texture_info:
            # Draw a colored rectangle as fallback
            self.draw_rectangle(x, y, width, height, (0.8, 0.8, 0.8, modulate_color[3]))
            return

        texture_id, tex_width, tex_height = texture_info

        # Calculate half dimensions for centering
        half_width = width / 2
        half_height = height / 2

        glPushMatrix()

        # Apply transformations
        glTranslatef(x, y, 0)
        if rotation != 0:
            glRotatef(rotation, 0, 0, 1)

        # Bind texture and set color with modulation
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor4f(modulate_color[0], modulate_color[1], modulate_color[2], modulate_color[3])

        # Calculate UV coordinates based on stretch mode and other parameters
        u1, v1, u2, v2 = self._calculate_uv_coordinates(
            stretch_mode, width, height, tex_width, tex_height,
            flip_h, flip_v, uv_offset, uv_scale, region_rect
        )

        # Draw textured quad (flip V coordinates for UI coordinate system)
        glBegin(GL_QUADS)
        glTexCoord2f(u1, v2)  # Top-left
        glVertex2f(-half_width, -half_height)
        glTexCoord2f(u2, v2)  # Top-right
        glVertex2f(half_width, -half_height)
        glTexCoord2f(u2, v1)  # Bottom-right
        glVertex2f(half_width, half_height)
        glTexCoord2f(u1, v1)  # Bottom-left
        glVertex2f(-half_width, half_height)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        glPopMatrix()

    def _calculate_uv_coordinates(self, stretch_mode: str, width: float, height: float,
                                 tex_width: int, tex_height: int,
                                 flip_h: bool, flip_v: bool,
                                 uv_offset: Tuple[float, float],
                                 uv_scale: Tuple[float, float],
                                 region_rect: Optional[Tuple[float, float, float, float]]) -> Tuple[float, float, float, float]:
        """Calculate UV coordinates for texture rendering"""
        # Start with base UV coordinates
        if region_rect:
            # Use region if specified (normalized coordinates)
            u1, v1 = region_rect[0], region_rect[1]
            u2, v2 = region_rect[0] + region_rect[2], region_rect[1] + region_rect[3]
        else:
            u1, v1, u2, v2 = 0.0, 0.0, 1.0, 1.0

        # Apply stretch mode
        if stretch_mode == "tile":
            # Tile the texture based on size ratio
            tile_x = width / tex_width
            tile_y = height / tex_height
            u2 = u1 + tile_x
            v2 = v1 + tile_y
        elif stretch_mode in ["keep", "keep_centered"]:
            # Keep original texture size, potentially centered
            scale_x = tex_width / width
            scale_y = tex_height / height
            if stretch_mode == "keep_centered":
                # Center the texture
                offset_x = (1.0 - scale_x) / 2.0
                offset_y = (1.0 - scale_y) / 2.0
                u1 += offset_x
                v1 += offset_y
                u2 = u1 + scale_x
                v2 = v1 + scale_y
            else:
                u2 = u1 + scale_x
                v2 = v1 + scale_y
        elif stretch_mode in ["keep_aspect", "keep_aspect_centered"]:
            # Keep aspect ratio
            aspect_ratio = tex_width / tex_height
            target_aspect = width / height

            if aspect_ratio > target_aspect:
                # Texture is wider, fit to width
                scale = width / tex_width
                scaled_height = tex_height * scale
                if stretch_mode == "keep_aspect_centered":
                    offset_y = (height - scaled_height) / (2.0 * height)
                    v1 += offset_y
                    v2 = v1 + (scaled_height / height)
            else:
                # Texture is taller, fit to height
                scale = height / tex_height
                scaled_width = tex_width * scale
                if stretch_mode == "keep_aspect_centered":
                    offset_x = (width - scaled_width) / (2.0 * width)
                    u1 += offset_x
                    u2 = u1 + (scaled_width / width)

        # Apply UV offset and scale
        u_range = u2 - u1
        v_range = v2 - v1
        u1 = u1 + uv_offset[0] * u_range
        v1 = v1 + uv_offset[1] * v_range
        u2 = u1 + u_range * uv_scale[0]
        v2 = v1 + v_range * uv_scale[1]

        # Apply flipping
        if flip_h:
            u1, u2 = u2, u1
        if flip_v:
            v1, v2 = v2, v1

        return u1, v1, u2, v2

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
    
    def draw_circle(self, x: float, y: float, radius: float,
                   color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                   filled: bool = True, segments: int = 32):
        """Draw a circle"""
        glDisable(GL_TEXTURE_2D)
        glColor4f(*color)
        
        glPushMatrix()
        glTranslatef(x, y, 0)
        
        if filled:
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(0, 0)  # Center vertex
        else:
            glBegin(GL_LINE_LOOP)
        
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            px = radius * math.cos(angle)
            py = radius * math.sin(angle)
            glVertex2f(px, py)
        
        glEnd()
        glPopMatrix()
        glEnable(GL_TEXTURE_2D)

    def draw_rounded_rectangle(self, x: float, y: float, width: float, height: float,
                              radius: float = 4.0,
                              color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                              filled: bool = True, segments: int = 8):
        """Draw a rounded rectangle"""
        glDisable(GL_TEXTURE_2D)
        glColor4f(*color)

        half_width = width / 2
        half_height = height / 2

        # Clamp radius to not exceed half the smaller dimension
        max_radius = min(half_width, half_height)
        radius = min(radius, max_radius)

        glPushMatrix()
        glTranslatef(x, y, 0)

        if filled:
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(0, 0)  # Center vertex for fan
        else:
            glBegin(GL_LINE_LOOP)

        # Generate vertices for rounded rectangle
        # Start from top-right corner and go clockwise

        # Top-right corner arc
        corner_x = half_width - radius
        corner_y = -half_height + radius
        for i in range(segments + 1):
            angle = -math.pi/2 + i * (math.pi/2) / segments
            px = corner_x + radius * math.cos(angle)
            py = corner_y + radius * math.sin(angle)
            glVertex2f(px, py)

        # Bottom-right corner arc
        corner_x = half_width - radius
        corner_y = half_height - radius
        for i in range(segments + 1):
            angle = 0 + i * (math.pi/2) / segments
            px = corner_x + radius * math.cos(angle)
            py = corner_y + radius * math.sin(angle)
            glVertex2f(px, py)

        # Bottom-left corner arc
        corner_x = -half_width + radius
        corner_y = half_height - radius
        for i in range(segments + 1):
            angle = math.pi/2 + i * (math.pi/2) / segments
            px = corner_x + radius * math.cos(angle)
            py = corner_y + radius * math.sin(angle)
            glVertex2f(px, py)

        # Top-left corner arc
        corner_x = -half_width + radius
        corner_y = -half_height + radius
        for i in range(segments + 1):
            angle = math.pi + i * (math.pi/2) / segments
            px = corner_x + radius * math.cos(angle)
            py = corner_y + radius * math.sin(angle)
            glVertex2f(px, py)

        glEnd()
        glPopMatrix()
        glEnable(GL_TEXTURE_2D)

    def get_font(self, font_name: Optional[str] = None, font_size: int = 14):
        """Get a pygame font for text rendering with improved font loading"""
        if not PYGAME_AVAILABLE:
            return None

        font_key = (font_name, font_size)
        if font_key not in self.font_cache:
            try:
                if font_name and font_name.strip():
                    # Try to load custom font file first
                    if self.project_path and not os.path.isabs(font_name):
                        # Make relative paths relative to project
                        font_path = self.project_path / font_name
                    else:
                        font_path = Path(font_name)

                    if font_path.exists() and font_path.suffix.lower() in ['.ttf', '.otf', '.ttc']:
                        # Load custom font file
                        font = pygame.font.Font(str(font_path), font_size)
                        print(f"[OK] Loaded custom font: {font_path}")
                    else:
                        # Try as system font name
                        try:
                            font = pygame.font.SysFont(font_name, font_size)
                            print(f"[OK] Loaded system font: {font_name}")
                        except:
                            # If system font fails, try common font names
                            common_fonts = [
                                'Arial', 'Helvetica', 'Times New Roman', 'Courier New',
                                'Verdana', 'Georgia', 'Comic Sans MS', 'Impact',
                                'Trebuchet MS', 'Tahoma', 'Calibri'
                            ]

                            font = None
                            for common_font in common_fonts:
                                try:
                                    font = pygame.font.SysFont(common_font, font_size)
                                    print(f"[OK] Fallback to system font: {common_font}")
                                    break
                                except:
                                    continue

                            if font is None:
                                # Final fallback to default font
                                font = pygame.font.Font(None, font_size)
                                print(f"[OK] Using default font")
                else:
                    # Use default font
                    font = pygame.font.Font(None, font_size)

                self.font_cache[font_key] = font
            except Exception as e:
                print(f"Error loading font {font_name}: {e}")
                # Fallback to default font
                try:
                    font = pygame.font.Font(None, font_size)
                    self.font_cache[font_key] = font
                except Exception as e2:
                    print(f"Error loading default font: {e2}")
                    return None

        return self.font_cache[font_key]

    def get_available_system_fonts(self) -> List[str]:
        """Get list of available system fonts"""
        if not PYGAME_AVAILABLE:
            return []

        try:
            return pygame.font.get_fonts()
        except Exception as e:
            print(f"Error getting system fonts: {e}")
            return []

    def get_font_info(self, font_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a font"""
        info = {
            "name": font_name or "default",
            "available": False,
            "is_system_font": False,
            "is_custom_font": False,
            "path": None
        }

        if not PYGAME_AVAILABLE:
            return info

        try:
            if font_name and font_name.strip():
                # Check if it's a custom font file
                if self.project_path and not os.path.isabs(font_name):
                    font_path = self.project_path / font_name
                else:
                    font_path = Path(font_name)

                if font_path.exists() and font_path.suffix.lower() in ['.ttf', '.otf', '.ttc']:
                    info["available"] = True
                    info["is_custom_font"] = True
                    info["path"] = str(font_path)
                else:
                    # Check if it's a system font
                    system_fonts = self.get_available_system_fonts()
                    if font_name.lower() in [f.lower() for f in system_fonts]:
                        info["available"] = True
                        info["is_system_font"] = True
            else:
                # Default font is always available
                info["available"] = True

        except Exception as e:
            print(f"Error getting font info for {font_name}: {e}")

        return info

    def get_text_size(self, text: str, font_name: Optional[str] = None, font_size: int = 14) -> tuple:
        """Get the size of rendered text"""
        if not PYGAME_AVAILABLE:
            # Fallback calculation
            return (font_size * 0.6 * len(text), font_size)

        font = self.get_font(font_name, font_size)
        if font:
            try:
                return font.size(text)
            except Exception as e:
                print(f"Error getting text size: {e}")
                # Fallback calculation
                return (font_size * 0.6 * len(text), font_size)

        # Fallback calculation
        return (font_size * 0.6 * len(text), font_size)

    def create_text_texture(self, text: str, font, color: tuple) -> Optional[Tuple[int, int, int]]:
        """Create an OpenGL texture from text using pygame font"""
        if not PYGAME_AVAILABLE or not font:
            return None

        try:
            # Render text to pygame surface
            text_surface = font.render(text, True, color[:3])  # RGB only for pygame

            # Convert to RGBA format (don't flip vertically for UI coordinate system)
            text_data = pygame.image.tostring(text_surface, 'RGBA', False)
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

            return (texture_id, text_width, text_height)

        except Exception as e:
            print(f"Error creating text texture: {e}")
            return None

    def draw_text(self, text: str, x: float, y: float, font_name: Optional[str] = None,
                 font_size: int = 14, color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)):
        """Draw text using OpenGL with pygame font rendering"""
        if not text or not PYGAME_AVAILABLE:
            return

        # Create cache key
        pygame_color = (int(color[0] * 255), int(color[1] * 255),
                       int(color[2] * 255), int(color[3] * 255))
        text_key = (text, font_name, font_size, pygame_color)

        # Check cache
        if text_key not in self.text_texture_cache:
            font = self.get_font(font_name, font_size)
            if font:
                texture_info = self.create_text_texture(text, font, pygame_color)
                if texture_info:
                    self.text_texture_cache[text_key] = texture_info

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

    def draw_line(self, x1: float, y1: float, x2: float, y2: float,
                 color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                 width: float = 1.0):
        """Draw a line"""
        glDisable(GL_TEXTURE_2D)
        glColor4f(*color)
        glLineWidth(width)

        glBegin(GL_LINES)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glEnd()

        glLineWidth(1.0)
        glEnable(GL_TEXTURE_2D)

    def cleanup(self):
        """Clean up OpenGL resources"""
        # Delete textures
        for texture_info in self.texture_cache.values():
            if texture_info:
                texture_id = texture_info[0]
                glDeleteTextures(1, [texture_id])

        for texture_info in self.text_texture_cache.values():
            if texture_info:
                texture_id = texture_info[0]
                glDeleteTextures(1, [texture_id])

        self.texture_cache.clear()
        self.text_texture_cache.clear()
        self.font_cache.clear()
