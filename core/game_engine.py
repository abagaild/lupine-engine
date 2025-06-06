"""
Core Game Engine for Lupine Engine
Manages all game systems and provides a clean interface for game execution
"""

import pygame
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Tuple
from pygame.locals import *
from OpenGL.GL import *

# Import core systems
from .shared_renderer import SharedRenderer
from .openal_audio import OpenALAudioSystem
from .scene import Scene, Node, Node2D, Camera2D

# Optional imports with fallbacks
try:
    from .input_manager import InputManager
    INPUT_MANAGER_AVAILABLE = True
except ImportError:
    INPUT_MANAGER_AVAILABLE = False

# Global game engine instance registry
_global_game_engine = None

def get_global_game_engine():
    """Get the global game engine instance"""
    return _global_game_engine

def set_global_game_engine(engine):
    """Set the global game engine instance"""
    global _global_game_engine
    _global_game_engine = engine

try:
    from .physics import PhysicsWorld
    PHYSICS_AVAILABLE = True
except ImportError as e:
    PHYSICS_AVAILABLE = False
    print(f"[DEBUG] Physics system import failed: {e}")

try:
    from .python_runtime import PythonScriptRuntime, PythonScriptInstance
    PYTHON_RUNTIME_AVAILABLE = True
except ImportError:
    PYTHON_RUNTIME_AVAILABLE = False

try:
    from .input_constants import *
    INPUT_CONSTANTS_AVAILABLE = True
except ImportError:
    INPUT_CONSTANTS_AVAILABLE = False


class SimpleCamera:
    """Simple camera implementation for game rendering"""

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0

    def set_position(self, x: float, y: float):
        """Set camera position"""
        self.x = x
        self.y = y

    def set_zoom(self, zoom: float):
        """Set camera zoom"""
        self.zoom = zoom

    def get_position(self) -> Tuple[float, float]:
        """Get camera position"""
        return (self.x, self.y)

    def get_zoom(self) -> float:
        """Get camera zoom"""
        return self.zoom


class GameSystemManager:
    """Manages initialization and lifecycle of game systems"""
    
    def __init__(self, project_path: str, width: int = 1280, height: int = 720):
        self.project_path = Path(project_path)
        self.width = width
        self.height = height
        
        # System instances
        self.renderer: Optional[SharedRenderer] = None
        self.audio_system: Optional[OpenALAudioSystem] = None
        self.input_manager: Optional[InputManager] = None
        self.physics_world: Optional[PhysicsWorld] = None
        self.python_runtime: Optional[PythonScriptRuntime] = None
        
        # Game state
        self.game_bounds_width = 1920
        self.game_bounds_height = 1080
        self.scaling_mode = "stretch"  # stretch, letterbox, or crop
        self.scaling_filter = "linear"  # linear or nearest
        self.running = False
        
        # Initialize systems
        self._initialize_systems()
    
    def _initialize_systems(self):
        """Initialize all game systems"""
        try:
            # Renderer (required)
            self.renderer = SharedRenderer(self.width, self.height, str(self.project_path), auto_setup_gl=True, scaling_filter=self.scaling_filter)
            print("[OK] Renderer initialized")

            # Audio system
            self.audio_system = OpenALAudioSystem()
            print("[OK] Audio system initialized")

            # Input manager
            if INPUT_MANAGER_AVAILABLE:
                self.input_manager = InputManager(self.project_path)
                print("[OK] Input manager initialized")

            # Physics world
            if PHYSICS_AVAILABLE:
                self.physics_world = PhysicsWorld()
                print("[OK] Physics world initialized")

            # Python runtime
            if PYTHON_RUNTIME_AVAILABLE:
                self.python_runtime = PythonScriptRuntime(game_runtime=None)  # Will be set by game engine
                print("[OK] Python runtime initialized")
            
            # Load project settings
            self._load_project_settings()
            
        except Exception as e:
            print(f"Error initializing game systems: {e}")
            raise
    
    def _load_project_settings(self):
        """Load project-specific settings"""
        try:
            project_file = self.project_path / "project.lupine"
            if project_file.exists():
                with open(project_file, 'r') as f:
                    project_data = json.load(f)
                
                display_settings = project_data.get("settings", {}).get("display", {})
                self.game_bounds_width = display_settings.get("width", 1920)
                self.game_bounds_height = display_settings.get("height", 1080)
                self.scaling_mode = display_settings.get("scaling_mode", "stretch")
                self.scaling_filter = display_settings.get("scaling_filter", "linear")
                
                print(f"[OK] Project settings loaded: {self.game_bounds_width}x{self.game_bounds_height}")
        except Exception as e:
            print(f"Warning: Could not load project settings: {e}")

    def cleanup(self):
        """Cleanup all systems"""
        if self.audio_system:
            self.audio_system.cleanup()
        if self.physics_world:
            # Physics cleanup if needed
            pass
        print("[OK] Game systems cleaned up")


class LupineGameEngine:
    """Main game engine class that orchestrates all systems and manages the game loop"""
    
    def __init__(self, project_path: str, scene_path: str):
        self.project_path = Path(project_path)
        self.scene_path = scene_path

        # Set this as the global game engine instance
        set_global_game_engine(self)

        # Initialize Pygame and OpenGL
        self._initialize_pygame()

        # Initialize game systems
        self.systems = GameSystemManager(str(self.project_path), self.width, self.height)

        # Game state
        self.scene: Optional[Scene] = None
        self.camera: Optional[Any] = None
        self.clock = pygame.time.Clock()
        self.running = True

        # Rendering data
        self.sprites: List[Dict[str, Any]] = []
        self.ui_elements: List[Dict[str, Any]] = []

        # Input state
        self.pressed_keys: Set[int] = set()
        self.mouse_buttons: Set[int] = set()
        self.mouse_position: Tuple[float, float] = (0.0, 0.0)
        self.current_modifiers: Set[str] = set()

        # Setup Python runtime integration
        if self.systems.python_runtime:
            self.systems.python_runtime.game_runtime = self
            self._setup_python_builtins()

        # Load the scene
        self._load_scene()
    
    def _initialize_pygame(self):
        """Initialize Pygame and OpenGL context"""
        pygame.init()

        # Set up OpenGL context
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)

        # Load game bounds from project settings for window size
        self.width, self.height = self._load_game_bounds_from_project()

        # Create window
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE
        )
        pygame.display.set_caption("Lupine Engine - Game Runner")

        print(f"[OK] Pygame and OpenGL initialized - Window: {self.width}x{self.height}")

    def _load_game_bounds_from_project(self) -> tuple[int, int]:
        """Load game bounds from project settings"""
        try:
            project_file = self.project_path / "project.lupine"
            if project_file.exists():
                import json
                with open(project_file, 'r') as f:
                    project_data = json.load(f)

                display_settings = project_data.get("settings", {}).get("display", {})
                width = display_settings.get("width", 1920)  # Default to 1920x1080 if not set
                height = display_settings.get("height", 1080)

                print(f"[Game Engine] Loaded game bounds from project: {width}x{height}")
                return width, height
        except Exception as e:
            print(f"Warning: Could not load game bounds from project settings: {e}")

        # Fallback to default 1920x1080
        return 1920, 1080

    def _setup_python_builtins(self):
        """Setup built-in functions for Python scripts"""
        if not self.systems.python_runtime:
            return
        
        # Core game functions
        builtins = {
            "get_node": self.get_node,
            "find_node": self.find_node_by_name,
            "change_scene": self.change_scene,
            "reload_scene": self.reload_scene,
            "get_scene": self.get_scene,
            "get_delta_time": lambda: self.systems.python_runtime.delta_time if self.systems.python_runtime else 0.0,
            "get_runtime_time": lambda: self.systems.python_runtime.get_runtime_time() if self.systems.python_runtime else 0.0,
            "get_fps": lambda: 1.0 / self.systems.python_runtime.delta_time if self.systems.python_runtime and self.systems.python_runtime.delta_time > 0 else 0.0,
        }
        
        # Input functions
        if self.systems.input_manager:
            builtins.update({
                "is_action_pressed": self.is_action_pressed,
                "is_action_just_pressed": self.is_action_just_pressed,
                "is_action_just_released": self.is_action_just_released,
                "get_action_strength": self.get_action_strength,
                "is_key_pressed": self.is_key_pressed,
                "is_mouse_button_pressed": self.is_mouse_button_pressed,
                "get_mouse_position": self.get_mouse_position,
                "get_global_mouse_position": self.get_global_mouse_position,
            })
        
        # Input constants
        if INPUT_CONSTANTS_AVAILABLE:
            builtins.update({
                "MOUSE_BUTTON_LEFT": MOUSE_BUTTON_LEFT,
                "MOUSE_BUTTON_RIGHT": MOUSE_BUTTON_RIGHT,
                "MOUSE_BUTTON_MIDDLE": MOUSE_BUTTON_MIDDLE,
                "KEY_ESCAPE": KEY_ESCAPE,
                "KEY_ENTER": KEY_ENTER,
                "KEY_SPACE": KEY_SPACE,
                "KEY_LEFT": KEY_LEFT,
                "KEY_RIGHT": KEY_RIGHT,
                "KEY_UP": KEY_UP,
                "KEY_DOWN": KEY_DOWN,
                "KEY_W": KEY_W,
                "KEY_A": KEY_A,
                "KEY_S": KEY_S,
                "KEY_D": KEY_D,
            })
        
        # Register all builtins
        for name, func in builtins.items():
            self.systems.python_runtime.add_builtin(name, func)
    
    def _load_scene(self):
        """Load the specified scene"""
        try:
            scene_file = self.project_path / self.scene_path
            if not scene_file.exists():
                raise FileNotFoundError(f"Scene file not found: {scene_file}")
            
            if PYTHON_RUNTIME_AVAILABLE:
                self.scene = Scene.load_from_file(str(scene_file))
                print(f"[OK] Scene loaded: {self.scene.name} ({len(self.scene.root_nodes)} root nodes)")
                self._setup_scene()
            else:
                print("Warning: Python runtime not available, scene loading limited")

        except Exception as e:
            print(f"Error loading scene: {e}")
            # Create minimal fallback scene
            self._create_fallback_scene()

    def _create_fallback_scene(self):
        """Create a minimal fallback scene if loading fails"""
        if PYTHON_RUNTIME_AVAILABLE:
            self.scene = Scene("Fallback")
            root_node = Node2D("Main")
            self.scene.add_root_node(root_node)
            print("[OK] Fallback scene created")
    
    def _setup_scene(self):
        """Setup the loaded scene"""
        if not self.scene:
            return
        
        # Clear previous data
        self.sprites.clear()
        self.ui_elements.clear()
        
        # Setup all nodes
        for root_node in self.scene.root_nodes:
            self._setup_node_recursive(root_node)
            self._find_cameras_recursive(root_node)
    
    def _setup_node_recursive(self, node: Node):
        """Setup a node and all its children"""
        try:
            # Load and execute scripts (both legacy single script and new multiple scripts)
            has_legacy_script = hasattr(node, 'script_path') and node.script_path
            has_new_scripts = (getattr(node, 'scripts', None) or node.properties.get('scripts', []))

            if (has_legacy_script or has_new_scripts) and self.systems.python_runtime:
                self._load_node_script(node)

            # Setup node-specific functionality
            self._setup_node_type(node)

            # Call the node's _ready method if it exists (for custom node classes)
            if hasattr(node, '_ready') and callable(getattr(node, '_ready')):
                try:
                    node._ready()
                except Exception as e:
                    print(f"Error calling _ready on {node.name}: {e}")

            # Setup children
            for child in node.children:
                self._setup_node_recursive(child)

        except Exception as e:
            print(f"Error setting up node {getattr(node, 'name', 'Unknown')}: {e}")

    def _load_node_script(self, node: Node):
        """Load and execute scripts for a node (supports multiple scripts)"""
        try:
            if not self.systems.python_runtime:
                return

            # Initialize script instances list
            script_instances = []

            # Handle multiple scripts (new format)
            scripts = getattr(node, 'scripts', None) or node.properties.get('scripts', [])

            if scripts:
                for script_info in scripts:
                    script_path = script_info.get('path', '')
                    if script_path:
                        success = self._load_single_script(node, script_path, script_instances)
                        if success:
                            print(f"[OK] Script loaded for {node.name}: {script_path}")
                        else:
                            print(f"Failed to execute script for {node.name}: {script_path}")

            # Handle legacy single script (backward compatibility)
            elif node.script_path:
                success = self._load_single_script(node, node.script_path, script_instances)
                if success:
                    print(f"[OK] Script loaded for {node.name}: {node.script_path}")
                else:
                    print(f"Failed to execute script for {node.name}")

            # Store script instances on node
            if script_instances:
                setattr(node, 'script_instances', script_instances)
                # Keep backward compatibility with single script_instance
                setattr(node, 'script_instance', script_instances[0])
            else:
                setattr(node, 'script_instances', [])
                setattr(node, 'script_instance', None)

        except Exception as e:
            print(f"Error loading scripts for {node.name}: {e}")
            import traceback
            traceback.print_exc()

    def _load_single_script(self, node: Node, script_path: str, script_instances: list) -> bool:
        """Load and execute a single script file"""
        try:
            script_file = self.project_path / script_path
            if not script_file.exists():
                print(f"Script file not found: {script_file}")
                return False

            with open(script_file, 'r') as f:
                script_content = f.read()

            # Create script instance
            script_instance = PythonScriptInstance(node, script_path, self.systems.python_runtime)

            # Execute script
            success = self.systems.python_runtime.execute_script(script_content, script_instance)

            if success:
                script_instances.append(script_instance)

                # Call ready method
                if script_instance.has_method('_ready'):
                    script_instance.call_method('_ready')
                    script_instance.ready_called = True
                elif script_instance.has_method('_on_ready'):
                    script_instance.call_method('_on_ready')
                    script_instance.ready_called = True

            return success

        except Exception as e:
            print(f"Error loading single script {script_path} for {node.name}: {e}")
            return False

    def _setup_node_type(self, node: Node):
        """Setup node based on its type"""
        if not hasattr(node, 'type'):
            return

        node_type = node.type

        # Sprite nodes
        if node_type in ["Sprite", "AnimatedSprite"]:
            self._setup_sprite_node(node)

        # UI nodes
        elif node_type in ["TextureRect", "Panel", "Button", "Label", "ColorRect", "Control", "ProgressBar",
                          "NinePatchRect", "VBoxContainer", "HBoxContainer", "CenterContainer", "GridContainer",
                          "PanelContainer", "LineEdit", "CheckBox", "Slider", "ScrollContainer", "HSeparator",
                          "VSeparator", "RichTextLabel", "ItemList"]:
            self._setup_ui_node(node)

        # Audio nodes
        elif node_type == "AudioStreamPlayer":
            self._setup_audio_node(node)

        # Animation nodes
        elif node_type == "AnimationPlayer":
            self._setup_animation_player_node(node)

        # Camera nodes
        elif node_type == "Camera2D":
            self._setup_camera_node(node)

        # Physics nodes - check both explicit types and physics_body_type property
        elif self.systems.physics_world and (
            node_type in ["RigidBody2D", "StaticBody2D", "KinematicBody2D", "Area2D"] or
            hasattr(node, 'physics_body_type')
        ):
            self._setup_physics_node(node)

        # Light nodes
        elif node_type == "Light2D":
            self._setup_light_node(node)

        # TileMap nodes
        elif node_type == "TileMap":
            self._setup_tilemap_node(node)

        # RayCast nodes
        elif node_type == "RayCast2D":
            self._setup_raycast_node(node)

        # Path nodes
        elif node_type in ["Path2D", "PathFollow2D"]:
            self._setup_path_node(node)

    def _setup_sprite_node(self, node: Node):
        """Setup a sprite node for rendering"""
        try:
            # Handle both 'texture' and 'texture_path' properties
            # Check multiple possible texture property names
            texture_path = (
                getattr(node, 'texture_path', '') or
                getattr(node, 'texture', '') or
                node.properties.get('texture', '') or
                node.properties.get('texture_path', '')
            )

            # Debug: Only warn if no texture found
            if not texture_path:
                print(f"[DEBUG] Sprite {node.name} has no texture path")

            sprite_data = {
                'lupine_node': node,
                'texture_path': texture_path,
                'position': list(node.position) if hasattr(node, 'position') else [0, 0],
                'scale': list(getattr(node, 'scale', [1, 1])),
                'rotation': getattr(node, 'rotation', 0),
                'modulate': list(getattr(node, 'modulate', [1, 1, 1, 1])),
                'visible': getattr(node, 'visible', True),
            }
            self.sprites.append(sprite_data)
            print(f"[OK] Sprite node setup: {node.name} (texture: {texture_path})")

            # Also recursively setup any child sprites
            self._setup_child_sprites_recursive(node)

        except Exception as e:
            print(f"Error setting up sprite node {node.name}: {e}")

    def _setup_child_sprites_recursive(self, node: Node):
        """Recursively setup sprite nodes in children"""
        try:
            for child in node.children:
                if hasattr(child, 'type') and child.type == "Sprite":
                    # Setup child sprite
                    self._setup_sprite_node(child)
                else:
                    # Continue recursively for non-sprite children
                    self._setup_child_sprites_recursive(child)
        except Exception as e:
            print(f"Error setting up child sprites for {node.name}: {e}")

    def _setup_ui_node(self, node: Node):
        """Setup a UI node for rendering"""
        try:
            # UI nodes use position and size (simplified positioning)
            position = list(getattr(node, 'position', [0, 0]))
            size = list(getattr(node, 'size', [100, 100]))
            follow_viewport = getattr(node, 'follow_viewport', True)

            ui_data = {
                'lupine_node': node,
                'type': node.type,
                'position': position,
                'size': size,
                'follow_viewport': follow_viewport,
                'visible': getattr(node, 'visible', True),
                'modulate': list(getattr(node, 'modulate', [1, 1, 1, 1])),
            }

            # Type-specific properties
            if node.type == "TextureRect":
                ui_data['texture_path'] = getattr(node, 'texture_path', '')
            elif node.type == "Label":
                ui_data['text'] = getattr(node, 'text', '')
                ui_data['font_path'] = getattr(node, 'font_path', '')
                ui_data['font_size'] = getattr(node, 'font_size', 14)
                ui_data['font_color'] = list(getattr(node, 'font_color', [1, 1, 1, 1]))
                ui_data['align'] = getattr(node, 'align', 'left')
                ui_data['valign'] = getattr(node, 'valign', 'top')
            elif node.type == "Button":
                ui_data['text'] = getattr(node, 'text', 'Button')
                ui_data['font_path'] = getattr(node, 'font_path', '')
                ui_data['font_size'] = getattr(node, 'font_size', 14)
                ui_data['font_color'] = list(getattr(node, 'font_color', [1, 1, 1, 1]))
                ui_data['font_color_hover'] = list(getattr(node, 'font_color_hover', [0.9, 0.9, 0.9, 1]))
                ui_data['font_color_pressed'] = list(getattr(node, 'font_color_pressed', [0.8, 0.8, 0.8, 1]))
                ui_data['font_color_disabled'] = list(getattr(node, 'font_color_disabled', [0.5, 0.5, 0.5, 1]))
                ui_data['bg_color'] = list(getattr(node, 'bg_color', [0.3, 0.3, 0.3, 1]))
                ui_data['bg_color_hover'] = list(getattr(node, 'bg_color_hover', [0.4, 0.4, 0.4, 1]))
                ui_data['bg_color_pressed'] = list(getattr(node, 'bg_color_pressed', [0.2, 0.2, 0.2, 1]))
                ui_data['bg_color_disabled'] = list(getattr(node, 'bg_color_disabled', [0.15, 0.15, 0.15, 1]))
                ui_data['border_width'] = getattr(node, 'border_width', 1.0)
                ui_data['border_color'] = list(getattr(node, 'border_color', [0.6, 0.6, 0.6, 1]))
                ui_data['border_radius'] = getattr(node, 'border_radius', 4.0)
                ui_data['flat'] = getattr(node, 'flat', False)
                ui_data['disabled'] = getattr(node, 'disabled', False)
                ui_data['text_align'] = getattr(node, 'text_align', 'center')
                # Include visual state for rendering
                ui_data['_is_hovered'] = getattr(node, '_is_hovered', False)
                ui_data['_is_pressed'] = getattr(node, '_is_pressed', False)
            elif node.type == "ColorRect":
                ui_data['color'] = list(getattr(node, 'color', [1, 1, 1, 1]))
                ui_data['gradient_enabled'] = getattr(node, 'gradient_enabled', False)
                ui_data['border_enabled'] = getattr(node, 'border_enabled', False)
                ui_data['corner_radius'] = getattr(node, 'corner_radius', 0.0)
            elif node.type == "Panel":
                ui_data['background_color'] = list(getattr(node, 'background_color', [0.2, 0.2, 0.2, 0.8]))
                ui_data['border_width'] = getattr(node, 'border_width', 1.0)
                ui_data['border_color'] = list(getattr(node, 'border_color', [0.5, 0.5, 0.5, 1.0]))
                ui_data['corner_radius'] = getattr(node, 'corner_radius', 4.0)
                ui_data['padding_left'] = getattr(node, 'padding_left', 8.0)
                ui_data['padding_top'] = getattr(node, 'padding_top', 8.0)
                ui_data['padding_right'] = getattr(node, 'padding_right', 8.0)
                ui_data['padding_bottom'] = getattr(node, 'padding_bottom', 8.0)
            elif node.type == "TextureRect":
                ui_data['texture_path'] = getattr(node, 'texture_path', None)
                ui_data['stretch_mode'] = getattr(node, 'stretch_mode', 'stretch')
                ui_data['modulate_color'] = list(getattr(node, 'modulate_color', [1, 1, 1, 1]))
                ui_data['uv_offset'] = list(getattr(node, 'uv_offset', [0, 0]))
                ui_data['uv_scale'] = list(getattr(node, 'uv_scale', [1, 1]))
            elif node.type == "NinePatchRect":
                ui_data['texture_path'] = getattr(node, 'texture_path', None)
                ui_data['patch_margin_left'] = getattr(node, 'patch_margin_left', 0)
                ui_data['patch_margin_top'] = getattr(node, 'patch_margin_top', 0)
                ui_data['patch_margin_right'] = getattr(node, 'patch_margin_right', 0)
                ui_data['patch_margin_bottom'] = getattr(node, 'patch_margin_bottom', 0)
                ui_data['draw_center'] = getattr(node, 'draw_center', True)
            elif node.type in ["VBoxContainer", "HBoxContainer"]:
                ui_data['separation'] = getattr(node, 'separation', 4.0)
                ui_data['alignment'] = getattr(node, 'alignment', 'top' if node.type == "VBoxContainer" else 'left')
                ui_data['padding_left'] = getattr(node, 'padding_left', 0.0)
                ui_data['padding_top'] = getattr(node, 'padding_top', 0.0)
                ui_data['padding_right'] = getattr(node, 'padding_right', 0.0)
                ui_data['padding_bottom'] = getattr(node, 'padding_bottom', 0.0)
            elif node.type == "CenterContainer":
                ui_data['use_top_left'] = getattr(node, 'use_top_left', False)
                ui_data['padding_left'] = getattr(node, 'padding_left', 0.0)
                ui_data['padding_top'] = getattr(node, 'padding_top', 0.0)
                ui_data['padding_right'] = getattr(node, 'padding_right', 0.0)
                ui_data['padding_bottom'] = getattr(node, 'padding_bottom', 0.0)
            elif node.type == "LineEdit":
                ui_data['text'] = getattr(node, 'text', '')
                ui_data['placeholder_text'] = getattr(node, 'placeholder_text', 'Enter text...')
                ui_data['secret'] = getattr(node, 'secret', False)
                ui_data['editable'] = getattr(node, 'editable', True)
                ui_data['font_size'] = getattr(node, 'font_size', 14)
                ui_data['text_color'] = list(getattr(node, 'text_color', [0.9, 0.9, 0.9, 1.0]))
                ui_data['background_color'] = list(getattr(node, 'background_color', [0.1, 0.1, 0.1, 1.0]))
                ui_data['border_color'] = list(getattr(node, 'border_color', [0.4, 0.4, 0.4, 1.0]))
                ui_data['cursor_position'] = getattr(node, 'cursor_position', 0)
            elif node.type == "CheckBox":
                ui_data['button_pressed'] = getattr(node, 'button_pressed', False)
                ui_data['disabled'] = getattr(node, 'disabled', False)
                ui_data['text'] = getattr(node, 'text', 'CheckBox')
                ui_data['font_size'] = getattr(node, 'font_size', 14)
                ui_data['text_color'] = list(getattr(node, 'text_color', [0.9, 0.9, 0.9, 1.0]))
                ui_data['checkbox_size'] = getattr(node, 'checkbox_size', 16.0)
                ui_data['check_color'] = list(getattr(node, 'check_color', [0.2, 0.8, 0.2, 1.0]))
                ui_data['_is_hovered'] = getattr(node, '_is_hovered', False)
                ui_data['_is_pressed'] = getattr(node, '_is_pressed', False)

            self.ui_elements.append(ui_data)

            # Store a reference to the UI data in the node for dynamic updates
            # This allows nodes like Button to update their visual state in real-time
            if hasattr(node, '_update_visual_state'):
                node._ui_data_ref = ui_data

            print(f"[OK] UI node setup: {node.name} ({node.type}) at {position} size {size}")
        except Exception as e:
            print(f"Error setting up UI node {node.name}: {e}")
            import traceback
            traceback.print_exc()

    def _setup_audio_node(self, node: Node):
        """Setup an audio node"""
        try:
            print(f"[OK] Audio node setup: {node.name} (type: {node.type})")

            # The AudioStreamPlayer will handle its own initialization in _ready()
            # Just ensure it has access to the audio system
            if self.systems.audio_system:
                print(f"[AudioStreamPlayer] Audio system available for {node.name}")
            else:
                print(f"[AudioStreamPlayer] Warning: No audio system available for {node.name}")

        except Exception as e:
            print(f"Error setting up audio node {node.name}: {e}")
            import traceback
            traceback.print_exc()

    def _setup_animation_player_node(self, node: Node):
        """Setup an AnimationPlayer node"""
        try:
            print(f"[OK] AnimationPlayer node setup: {node.name} (type: {node.type})")

            # The AnimationPlayer will handle its own initialization in _ready()
            # No special setup required here

        except Exception as e:
            print(f"Error setting up AnimationPlayer node {node.name}: {e}")
            import traceback
            traceback.print_exc()

    def _setup_camera_node(self, node: Node):
        """Setup a camera node"""
        try:
            if getattr(node, 'current', False):
                # Create a simple camera object
                self.camera = SimpleCamera()
                if hasattr(node, 'position'):
                    self.camera.set_position(node.position[0], node.position[1])
                if hasattr(node, 'zoom'):
                    zoom_val = node.zoom[0] if isinstance(node.zoom, list) else node.zoom
                    self.camera.set_zoom(zoom_val)
                print(f"[OK] Active camera setup: {node.name}")
        except Exception as e:
            print(f"Error setting up camera node {node.name}: {e}")

    def _setup_physics_node(self, node: Node):
        """Setup a physics node"""
        try:
            if self.systems.physics_world:
                # Debug output for custom physics nodes
                node_type = getattr(node, 'type', 'Unknown')
                physics_body_type = getattr(node, 'physics_body_type', None)
                if physics_body_type:
                    print(f"[DEBUG] Setting up custom physics node: {node.name} (type: {node_type}, physics_body_type: {physics_body_type})")

                physics_body = self.systems.physics_world.add_node(node)
                # Ensure the physics body position is synced with the node position
                if physics_body:
                    physics_body.update_from_node()
                    print(f"[OK] Physics node setup: {node.name} (type: {node_type}) at position {getattr(node, 'position', [0, 0])}")
                else:
                    print(f"[WARNING] Failed to create physics body for {node.name} (type: {node_type})")
        except Exception as e:
            print(f"Error setting up physics node {node.name}: {e}")
            import traceback
            traceback.print_exc()

    def _setup_light_node(self, node: Node):
        """Setup a Light2D node"""
        try:
            # Add to lights list for rendering
            if not hasattr(self, 'lights'):
                self.lights = []

            light_data = {
                'lupine_node': node,
                'position': getattr(node, 'position', [0, 0]),
                'color': getattr(node, 'color', [1.0, 1.0, 1.0, 1.0]),
                'energy': getattr(node, 'energy', 1.0),
                'range': getattr(node, 'range', 200.0),
                'mode': getattr(node, 'mode', 'Additive'),
                'texture': getattr(node, 'texture', ''),
                'shadow_enabled': getattr(node, 'shadow_enabled', False),
                'visible': True
            }

            self.lights.append(light_data)
            print(f"[OK] Light2D setup: {node.name}")
        except Exception as e:
            print(f"Error setting up Light2D {node.name}: {e}")

    def _setup_tilemap_node(self, node: Node):
        """Setup a TileMap node"""
        try:
            # Add to tilemaps list for rendering
            if not hasattr(self, 'tilemaps'):
                self.tilemaps = []

            tilemap_data = {
                'lupine_node': node,
                'position': getattr(node, 'position', [0, 0]),
                'tileset': getattr(node, 'tileset', ''),
                'cell_size': getattr(node, 'cell_size', [32.0, 32.0]),
                'tiles': getattr(node, '_tiles', {}),
                'modulate': getattr(node, 'modulate', [1.0, 1.0, 1.0, 1.0]),
                'opacity': getattr(node, 'opacity', 1.0),
                'visible': True
            }

            self.tilemaps.append(tilemap_data)
            print(f"[OK] TileMap setup: {node.name}")
        except Exception as e:
            print(f"Error setting up TileMap {node.name}: {e}")

    def _setup_raycast_node(self, node: Node):
        """Setup a RayCast2D node"""
        try:
            # RayCast2D nodes don't need special rendering setup
            # They integrate with the physics system for collision detection
            print(f"[OK] RayCast2D setup: {node.name}")
        except Exception as e:
            print(f"Error setting up RayCast2D {node.name}: {e}")

    def _setup_path_node(self, node: Node):
        """Setup Path2D or PathFollow2D nodes"""
        try:
            node_type = getattr(node, 'type', 'Unknown')

            if node_type == "PathFollow2D":
                # PathFollow2D needs to find its parent Path2D
                parent = getattr(node, 'parent', None)
                if parent and getattr(parent, 'type', None) == "Path2D":
                    if hasattr(node, 'set_path_to_follow'):
                        node.set_path_to_follow(parent)

            print(f"[OK] {node_type} setup: {node.name}")
        except Exception as e:
            print(f"Error setting up path node {node.name}: {e}")

    def _find_cameras_recursive(self, node: Node):
        """Find cameras in the scene hierarchy"""
        if hasattr(node, 'type') and node.type == "Camera2D" and getattr(node, 'current', False):
            self._setup_camera_node(node)

        for child in node.children:
            self._find_cameras_recursive(child)

    # Game loop methods
    def run(self):
        """Main game loop"""
        print("[GAME] Starting game loop...")

        try:
            while self.running:
                # Calculate delta time
                delta_time = self.clock.tick(60) / 1000.0

                # Handle events
                self._handle_events()

                # Update game logic
                self._update(delta_time)

                # Render
                self._render()

                # Swap buffers
                pygame.display.flip()

        except Exception as e:
            print(f"Error in game loop: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self._cleanup()

    def _handle_events(self):
        """Handle Pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.pressed_keys.add(event.key)
                self._on_key_press(event.key, pygame.key.get_mods())
            elif event.type == pygame.KEYUP:
                self.pressed_keys.discard(event.key)
                self._on_key_release(event.key, pygame.key.get_mods())
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_buttons.add(event.button)
                self._on_mouse_press(event.pos[0], event.pos[1], event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_buttons.discard(event.button)
                self._on_mouse_release(event.pos[0], event.pos[1], event.button)
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_position = event.pos
                self._on_mouse_motion(event.pos[0], event.pos[1], event.rel[0], event.rel[1])
            elif event.type == pygame.VIDEORESIZE:
                self._on_resize(event.w, event.h)

    def _update(self, delta_time: float):
        """Update game logic"""
        # Update systems
        if self.systems.audio_system:
            self.systems.audio_system.update()

        if self.systems.input_manager:
            self.systems.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

        if self.systems.python_runtime:
            self.systems.python_runtime.update_time(delta_time)

        # Update scripts
        if self.systems.python_runtime and self.scene:
            for root_node in self.scene.root_nodes:
                self._update_node_scripts_recursive(root_node, delta_time)

        # Update physics
        if self.systems.physics_world:
            self.systems.physics_world.step(delta_time)

        # Sync sprite positions
        self._sync_sprite_positions()

    def _render(self):
        """Render the game using SharedRenderer like scene view"""
        if not self.systems.renderer:
            return

        # Clear screen
        self.systems.renderer.clear()

        # Setup viewport and projection based on camera or game bounds
        self._setup_unified_projection()

        # Render scene nodes directly using SharedRenderer
        if self.scene and hasattr(self.scene, 'root_nodes'):
            for root_node in self.scene.root_nodes:
                self._render_node_hierarchy(root_node)

    def _update_node_scripts_recursive(self, node: Node, delta_time: float):
        """Update scripts for a node and its children"""
        try:
            # First, call the node's own lifecycle methods if they exist
            # This handles custom node classes like player controllers
            try:
                if hasattr(node, '_process') and callable(getattr(node, '_process')):
                    node._process(delta_time)
                if hasattr(node, '_physics_process') and callable(getattr(node, '_physics_process')):
                    node._physics_process(delta_time)
            except Exception as e:
                print(f"Error calling node methods on {node.name}: {e}")

            # Then update all script instances for this node
            script_instances = getattr(node, 'script_instances', [])
            if script_instances:
                for script_instance in script_instances:
                    # Call process method if available
                    if script_instance.has_method('_process'):
                        script_instance.call_method('_process', delta_time)
                    elif script_instance.has_method('_on_process'):
                        script_instance.call_method('_on_process', delta_time)

                    # Call physics process method if available
                    if script_instance.has_method('_physics_process'):
                        script_instance.call_method('_physics_process', delta_time)
                    elif script_instance.has_method('_on_physics_process'):
                        script_instance.call_method('_on_physics_process', delta_time)

            # Backward compatibility: handle single script_instance
            elif hasattr(node, 'script_instance') and node.script_instance:
                script_instance = node.script_instance

                # Call process method if available
                if script_instance.has_method('_process'):
                    script_instance.call_method('_process', delta_time)
                elif script_instance.has_method('_on_process'):
                    script_instance.call_method('_on_process', delta_time)

                # Call physics process method if available
                if script_instance.has_method('_physics_process'):
                    script_instance.call_method('_physics_process', delta_time)
                elif script_instance.has_method('_on_physics_process'):
                    script_instance.call_method('_on_physics_process', delta_time)

            # Update children
            for child in node.children:
                self._update_node_scripts_recursive(child, delta_time)

        except Exception as e:
            print(f"Error updating scripts for node {getattr(node, 'name', 'Unknown')}: {e}")

    def _sync_sprite_positions(self):
        """Synchronize sprite positions with their nodes"""
        for sprite_data in self.sprites:
            if 'lupine_node' in sprite_data:
                node = sprite_data['lupine_node']
                if hasattr(node, 'position'):
                    # Calculate global position for child sprites
                    global_position = self._get_global_position(node)
                    sprite_data['position'] = list(global_position)

                    # Also sync other properties that might have changed
                    sprite_data['scale'] = list(getattr(node, 'scale', [1, 1]))
                    sprite_data['rotation'] = getattr(node, 'rotation', 0)
                    sprite_data['modulate'] = list(getattr(node, 'modulate', [1, 1, 1, 1]))
                    sprite_data['visible'] = getattr(node, 'visible', True)

    def _get_global_position(self, node):
        """Get the global position of a node (including parent transforms)"""
        if not hasattr(node, 'position'):
            return [0, 0]

        position = list(node.position)

        # Walk up the parent chain to accumulate transforms
        current_parent = getattr(node, 'parent', None)
        while current_parent and hasattr(current_parent, 'position'):
            parent_pos = current_parent.position
            position[0] += parent_pos[0]
            position[1] += parent_pos[1]
            current_parent = getattr(current_parent, 'parent', None)

        return position

    def _render_sprite(self, sprite_data: Dict[str, Any]):
        """Render a single sprite"""
        if not self.systems.renderer:
            return

        try:
            texture_path = sprite_data.get('texture_path', '')
            position = sprite_data.get('position', [0, 0])
            scale = sprite_data.get('scale', [1, 1])
            rotation = sprite_data.get('rotation', 0)
            modulate = sprite_data.get('modulate', [1, 1, 1, 1])

            # Debug output for empty textures
            if not texture_path:
                print(f"Warning: Sprite at {position} has no texture path")

            # Calculate size based on scale
            # For now, use default size if not specified
            width = 64 * scale[0]
            height = 64 * scale[1]

            self.systems.renderer.draw_sprite(
                texture_path, position[0], position[1],
                width, height, rotation, modulate[3]
            )
        except Exception as e:
            print(f"Error rendering sprite: {e}")

    def _render_ui_element(self, ui_data: Dict[str, Any]):
        """Render a single UI element with proper scaling"""
        if not self.systems.renderer:
            return

        try:
            ui_type = ui_data.get('type', '')
            position = ui_data.get('position', [0, 0])
            size = ui_data.get('size', [100, 100])
            follow_viewport = ui_data.get('follow_viewport', True)
            modulate = ui_data.get('modulate', [1, 1, 1, 1])

            # Handle positioning based on follow_viewport setting
            if follow_viewport:
                # Scale UI elements from game bounds to actual window size (viewport-relative)
                scaled_pos = self._scale_ui_position(position)
                scaled_size = self._scale_ui_size(size)
            else:
                # Use world coordinates (affected by camera)
                if self.camera:
                    # Apply camera transform to world-space UI elements
                    camera_x, camera_y = self.camera.get_position()
                    zoom = self.camera.get_zoom()
                    scaled_pos = [(position[0] - camera_x) * zoom + self.width / 2,
                                  (position[1] - camera_y) * zoom + self.height / 2]
                    scaled_size = [size[0] * zoom, size[1] * zoom]
                else:
                    # No camera, use position as-is
                    scaled_pos = position
                    scaled_size = size

            if ui_type == "TextureRect":
                texture_path = ui_data.get('texture_path', '')
                # Convert top-left position to center position for SharedRenderer
                center_x = scaled_pos[0] + scaled_size[0] / 2
                center_y = scaled_pos[1] + scaled_size[1] / 2
                self.systems.renderer.draw_sprite(
                    texture_path, center_x, center_y,
                    scaled_size[0], scaled_size[1], 0, modulate[3]
                )
            elif ui_type == "ColorRect":
                color = ui_data.get('color', [1, 1, 1, 1])
                # Convert top-left position to center position for SharedRenderer
                center_x = scaled_pos[0] + scaled_size[0] / 2
                center_y = scaled_pos[1] + scaled_size[1] / 2
                self.systems.renderer.draw_rectangle(
                    center_x, center_y, scaled_size[0], scaled_size[1], color
                )
            elif ui_type == "Label":
                text = ui_data.get('text', '')
                font_path = ui_data.get('font_path', '')
                font_size = ui_data.get('font_size', 14)
                font_color = ui_data.get('font_color', modulate)
                align = ui_data.get('align', 'left')
                valign = ui_data.get('valign', 'top')
                scaled_font_size = self._scale_ui_font_size(font_size)

                # Calculate text position based on alignment
                text_x, text_y = self._calculate_text_position(
                    text, scaled_pos, scaled_size, align, valign, font_path, scaled_font_size
                )

                self.systems.renderer.draw_text(
                    text, text_x, text_y, font_path, scaled_font_size, font_color
                )
            elif ui_type == "Button":
                # Get button state for visual feedback
                is_hovered = ui_data.get('_is_hovered', False)
                is_pressed = ui_data.get('_is_pressed', False)
                disabled = ui_data.get('disabled', False)
                flat = ui_data.get('flat', False)

                # Choose colors based on state
                if disabled:
                    bg_color = ui_data.get('bg_color_disabled', [0.15, 0.15, 0.15, 1])
                    font_color = ui_data.get('font_color_disabled', [0.5, 0.5, 0.5, 1])
                elif is_pressed:
                    bg_color = ui_data.get('bg_color_pressed', [0.2, 0.2, 0.2, 1])
                    font_color = ui_data.get('font_color_pressed', [0.8, 0.8, 0.8, 1])
                elif is_hovered:
                    bg_color = ui_data.get('bg_color_hover', [0.4, 0.4, 0.4, 1])
                    font_color = ui_data.get('font_color_hover', [0.9, 0.9, 0.9, 1])
                else:
                    bg_color = ui_data.get('bg_color', [0.3, 0.3, 0.3, 1])
                    font_color = ui_data.get('font_color', [1, 1, 1, 1])

                # Render button background (unless flat)
                if not flat:
                    # Convert top-left position to center position for SharedRenderer
                    center_x = scaled_pos[0] + scaled_size[0] / 2
                    center_y = scaled_pos[1] + scaled_size[1] / 2
                    self.systems.renderer.draw_rectangle(
                        center_x, center_y, scaled_size[0], scaled_size[1], bg_color
                    )

                    # Draw border
                    border_width = ui_data.get('border_width', 1.0)
                    border_color = ui_data.get('border_color', [0.6, 0.6, 0.6, 1])
                    if border_width > 0:
                        # Draw border as outline with center-based positioning
                        # Top border
                        top_center_x = scaled_pos[0] + scaled_size[0] / 2
                        top_center_y = scaled_pos[1] + border_width / 2
                        self.systems.renderer.draw_rectangle(
                            top_center_x, top_center_y, scaled_size[0], border_width, border_color
                        )
                        # Bottom border
                        bottom_center_x = scaled_pos[0] + scaled_size[0] / 2
                        bottom_center_y = scaled_pos[1] + scaled_size[1] - border_width / 2
                        self.systems.renderer.draw_rectangle(
                            bottom_center_x, bottom_center_y, scaled_size[0], border_width, border_color
                        )
                        # Left border
                        left_center_x = scaled_pos[0] + border_width / 2
                        left_center_y = scaled_pos[1] + scaled_size[1] / 2
                        self.systems.renderer.draw_rectangle(
                            left_center_x, left_center_y, border_width, scaled_size[1], border_color
                        )
                        # Right border
                        right_center_x = scaled_pos[0] + scaled_size[0] - border_width / 2
                        right_center_y = scaled_pos[1] + scaled_size[1] / 2
                        self.systems.renderer.draw_rectangle(
                            right_center_x, right_center_y, border_width, scaled_size[1], border_color
                        )

                # Render button text
                text = ui_data.get('text', 'Button')
                font_path = ui_data.get('font_path', '')
                font_size = ui_data.get('font_size', 14)
                text_align = ui_data.get('text_align', 'center')
                scaled_font_size = self._scale_ui_font_size(font_size)

                # Calculate text position based on alignment
                text_x, text_y = self._calculate_text_position(
                    text, scaled_pos, scaled_size, text_align, 'center', font_path, scaled_font_size
                )

                self.systems.renderer.draw_text(
                    text, text_x, text_y, font_path, scaled_font_size, font_color
                )
        except Exception as e:
            print(f"Error rendering UI element ({ui_type}): {e}")
            import traceback
            traceback.print_exc()

    def _setup_viewport_and_projection(self):
        """Setup viewport and projection matrix based on camera or game bounds"""
        try:
            import OpenGL.GL as gl

            # Set viewport to window size
            gl.glViewport(0, 0, self.width, self.height)

            # Setup projection matrix
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()

            if self.camera:
                # Use camera-based projection
                cam_pos = self.camera.get_position()
                zoom = self.camera.get_zoom()

                # Calculate view bounds based on camera
                view_width = self.width / zoom
                view_height = self.height / zoom

                left = cam_pos[0] - view_width / 2
                right = cam_pos[0] + view_width / 2
                bottom = cam_pos[1] - view_height / 2
                top = cam_pos[1] + view_height / 2

                gl.glOrtho(left, right, bottom, top, -1, 1)
            else:
                # Use game bounds for projection (centered at origin)
                half_width = self.width / 2
                half_height = self.height / 2
                gl.glOrtho(-half_width, half_width, -half_height, half_height, -1, 1)

            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

        except ImportError:
            # Fallback if OpenGL not available
            pass
        except Exception as e:
            print(f"Error setting up viewport: {e}")

    def _setup_ui_projection(self):
        """Setup projection matrix for UI rendering (screen space)"""
        try:
            import OpenGL.GL as gl

            # UI always uses screen space coordinates
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()

            # Screen space: (0,0) at top-left, (width, height) at bottom-right
            gl.glOrtho(0, self.width, self.height, 0, -1, 1)

            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()

        except ImportError:
            # Fallback if OpenGL not available
            pass
        except Exception as e:
            print(f"Error setting up UI projection: {e}")

    def _scale_ui_position(self, position: List[float]) -> List[float]:
        """Scale UI position from game bounds coordinates to actual window coordinates"""
        # Get game bounds from project settings
        game_bounds_width = self.systems.game_bounds_width
        game_bounds_height = self.systems.game_bounds_height

        # Calculate scale factors
        scale_x = self.width / game_bounds_width
        scale_y = self.height / game_bounds_height

        # Scale position - UI coordinates are top-left origin, so no Y flip needed
        scaled_x = position[0] * scale_x
        scaled_y = position[1] * scale_y

        return [scaled_x, scaled_y]

    def _scale_ui_size(self, size: List[float]) -> List[float]:
        """Scale UI size from game bounds coordinates to actual window coordinates"""
        # Get game bounds from project settings
        game_bounds_width = self.systems.game_bounds_width
        game_bounds_height = self.systems.game_bounds_height

        # Calculate scale factors
        scale_x = self.width / game_bounds_width
        scale_y = self.height / game_bounds_height

        # Scale size
        scaled_width = size[0] * scale_x
        scaled_height = size[1] * scale_y

        return [scaled_width, scaled_height]

    def _scale_ui_font_size(self, font_size: int) -> int:
        """Scale UI font size based on window scaling"""
        # Get game bounds from project settings
        game_bounds_height = self.systems.game_bounds_height

        # Calculate scale factor based on height (more consistent for text)
        scale_y = self.height / game_bounds_height

        # Scale font size
        scaled_font_size = int(font_size * scale_y)

        return max(1, scaled_font_size)  # Ensure minimum font size of 1

    def _calculate_text_position(self, text: str, pos: list, size: list,
                               align: str, valign: str, font_path: str, font_size: int) -> tuple:
        """Calculate text position based on alignment with improved text metrics"""
        # Try to get actual text dimensions from renderer
        text_width = font_size * 0.6 * len(text)  # Fallback calculation
        text_height = font_size

        # Try to get more accurate text dimensions if renderer supports it
        if hasattr(self.systems.renderer, 'get_text_size'):
            try:
                actual_width, actual_height = self.systems.renderer.get_text_size(text, font_path, font_size)
                text_width = actual_width
                text_height = actual_height
            except:
                pass  # Use fallback calculation

        # Calculate horizontal position (pos is top-left corner)
        padding = 5  # Consistent padding
        if align == "center":
            text_x = pos[0] + (size[0] - text_width) / 2
        elif align == "right":
            text_x = pos[0] + size[0] - text_width - padding
        else:  # left
            text_x = pos[0] + padding

        # Calculate vertical position (pos is top-left corner)
        if valign == "center":
            text_y = pos[1] + (size[1] - text_height) / 2
        elif valign == "bottom":
            text_y = pos[1] + size[1] - text_height - padding
        else:  # top
            text_y = pos[1] + padding

        return text_x, text_y

    def _on_key_press(self, key: int, modifiers: int):
        """Handle key press events"""
        # Convert modifiers to set
        self.current_modifiers.clear()
        if modifiers & pygame.KMOD_SHIFT:
            self.current_modifiers.add('shift')
        if modifiers & pygame.KMOD_CTRL:
            self.current_modifiers.add('ctrl')
        if modifiers & pygame.KMOD_ALT:
            self.current_modifiers.add('alt')

    def _on_key_release(self, key: int, modifiers: int):
        """Handle key release events"""
        # Update modifiers
        self._on_key_press(key, modifiers)

    def _on_mouse_press(self, x: float, y: float, button: int):
        """Handle mouse press events"""
        # Handle UI input events
        self._handle_ui_mouse_event(x, y, "mouse_button", {"button": button, "pressed": True})

    def _on_mouse_release(self, x: float, y: float, button: int):
        """Handle mouse release events"""
        # Handle UI input events
        self._handle_ui_mouse_event(x, y, "mouse_button", {"button": button, "pressed": False})

    def _on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Handle mouse motion events"""
        # Update mouse hover states for UI elements
        self._update_ui_mouse_hover(x, y)

    def _on_resize(self, width: int, height: int):
        """Handle window resize events"""
        self.width = width
        self.height = height
        if self.systems.renderer:
            self.systems.renderer.width = width
            self.systems.renderer.height = height

    def _handle_ui_mouse_event(self, x: float, y: float, event_type: str, event_data: Dict[str, Any]):
        """Handle mouse events for UI elements"""
        if not self.scene:
            return

        # Find UI controls that contain this point (handles both coordinate systems)
        ui_controls = self._get_ui_controls_at_point(x, y)

        # Send event to the topmost UI control
        for control in ui_controls:
            if hasattr(control, '_handle_input_event'):
                # Convert coordinates based on the control's follow_viewport setting
                if getattr(control, 'follow_viewport', True):
                    game_x, game_y = self._screen_to_game_coords(x, y)
                else:
                    game_x, game_y = self._screen_to_world_coords(x, y)

                event = {
                    "type": event_type,
                    "position": [game_x, game_y],
                    **event_data
                }
                control._handle_input_event(event)
                # Stop propagation if mouse filter is "stop"
                if hasattr(control, 'mouse_filter') and control.mouse_filter == "stop":
                    break

    def _update_ui_mouse_hover(self, x: float, y: float):
        """Update mouse hover states for UI elements"""
        if not self.scene:
            return

        # Get all UI controls
        all_ui_controls = self._get_all_ui_controls()

        # Update hover states
        for control in all_ui_controls:
            if hasattr(control, 'contains_point') and hasattr(control, '_handle_mouse_enter') and hasattr(control, '_handle_mouse_exit'):
                # Convert coordinates based on the control's follow_viewport setting
                if getattr(control, 'follow_viewport', True):
                    test_x, test_y = self._screen_to_game_coords(x, y)
                else:
                    test_x, test_y = self._screen_to_world_coords(x, y)

                is_inside = control.contains_point([test_x, test_y])
                was_inside = getattr(control, '_mouse_inside', False)

                if is_inside and not was_inside:
                    control._handle_mouse_enter()
                elif not is_inside and was_inside:
                    control._handle_mouse_exit()

    def _screen_to_game_coords(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to game coordinates for UI elements"""
        # For viewport-following UI elements, convert from screen to game bounds
        game_bounds_width = self.systems.game_bounds_width
        game_bounds_height = self.systems.game_bounds_height

        # Calculate scale factors
        scale_x = game_bounds_width / self.width
        scale_y = game_bounds_height / self.height

        # Convert screen coordinates to game bounds coordinates
        game_x = screen_x * scale_x
        game_y = screen_y * scale_y

        return game_x, game_y

    def _screen_to_world_coords(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates for world-space UI elements"""
        if self.camera:
            # Apply inverse camera transform
            camera_x, camera_y = self.camera.get_position()
            zoom = self.camera.get_zoom()

            # Convert screen to world coordinates
            world_x = (screen_x - self.width / 2) / zoom + camera_x
            world_y = (screen_y - self.height / 2) / zoom + camera_y

            return world_x, world_y
        else:
            # No camera, screen coordinates are world coordinates
            return screen_x, screen_y

    def _get_ui_controls_at_point(self, screen_x: float, screen_y: float) -> List[Any]:
        """Get UI controls that contain the given screen point, sorted by z-order (topmost first)"""
        controls = []
        if not self.scene:
            return controls

        # Recursively check all nodes
        def check_node(node):
            # Check if this is a UI control
            if hasattr(node, 'contains_point') and hasattr(node, 'position') and hasattr(node, 'size'):
                # Convert screen coordinates to the appropriate coordinate system for this control
                if getattr(node, 'follow_viewport', True):
                    # Viewport-relative control
                    test_x, test_y = self._screen_to_game_coords(screen_x, screen_y)
                else:
                    # World-space control
                    test_x, test_y = self._screen_to_world_coords(screen_x, screen_y)

                if node.contains_point([test_x, test_y]):
                    controls.append(node)

            # Check children
            for child in getattr(node, 'children', []):
                check_node(child)

        for root_node in self.scene.root_nodes:
            check_node(root_node)

        # Sort by z-order (reverse order so topmost is first)
        # For now, just reverse the list - could be improved with actual z-order
        return list(reversed(controls))

    def _get_all_ui_controls(self) -> List[Any]:
        """Get all UI controls in the scene"""
        controls = []
        if not self.scene:
            return controls

        # Recursively collect all UI controls
        def collect_ui_controls(node):
            # Check if this is a UI control
            if hasattr(node, 'position') and hasattr(node, 'size') and hasattr(node, 'follow_viewport'):
                controls.append(node)

            # Check children
            for child in getattr(node, 'children', []):
                collect_ui_controls(child)

        for root_node in self.scene.root_nodes:
            collect_ui_controls(root_node)

        return controls

    def _cleanup(self):
        """Cleanup resources"""
        self.systems.cleanup()
        pygame.quit()
        print("[OK] Game engine cleaned up")

    # Input system integration methods
    def get_node(self, path: str) -> Optional[Node]:
        """Get a node by path"""
        if not self.scene:
            return None

        # Simple implementation - find by name in root nodes
        for root_node in self.scene.root_nodes:
            if root_node.name == path:
                return root_node
            # Could add recursive search here
        return None

    def find_node_by_name(self, name: str) -> Optional[Node]:
        """Find a node by name"""
        return self.get_node(name)

    def get_scene(self) -> Optional[Scene]:
        """Get the current scene"""
        return self.scene

    def change_scene(self, scene_path: str):
        """Change to a different scene"""
        try:
            self.scene_path = scene_path
            self._load_scene()
            print(f"[OK] Scene changed to: {scene_path}")
        except Exception as e:
            print(f"Error changing scene: {e}")

    def reload_scene(self):
        """Reload the current scene"""
        self.change_scene(self.scene_path)

    # Input methods
    def is_action_pressed(self, action_name: str) -> bool:
        """Check if an action is currently pressed"""
        if self.systems.input_manager:
            return self.systems.input_manager.is_action_pressed(action_name)
        return False

    def is_action_just_pressed(self, action_name: str) -> bool:
        """Check if an action was just pressed this frame"""
        if self.systems.input_manager:
            return self.systems.input_manager.is_action_just_pressed(action_name)
        return False

    def is_action_just_released(self, action_name: str) -> bool:
        """Check if an action was just released this frame"""
        if self.systems.input_manager:
            return self.systems.input_manager.is_action_just_released(action_name)
        return False

    def get_action_strength(self, action_name: str) -> float:
        """Get the strength of an action (0.0 to 1.0)"""
        if self.systems.input_manager:
            return self.systems.input_manager.get_action_strength(action_name)
        return 0.0

    def is_key_pressed(self, key_code: int) -> bool:
        """Check if a specific key is pressed"""
        if self.systems.input_manager:
            return self.systems.input_manager.is_key_pressed(key_code)
        return key_code in self.pressed_keys

    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if a mouse button is pressed"""
        return button in self.mouse_buttons

    def get_mouse_position(self) -> Tuple[float, float]:
        """Get current mouse position"""
        return self.mouse_position

    def get_global_mouse_position(self) -> Tuple[float, float]:
        """Get global mouse position (same as local for now)"""
        return self.mouse_position
