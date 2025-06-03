"""
Game Runner Widget for Lupine Engine
Handles game execution and runtime display
"""

import os
import subprocess
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QSplitter, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtOpenGLWidgets import QOpenGLWidget

from core.project import LupineProject


class GameProcess(QThread):
    """Thread for running the game process"""
    
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    finished = pyqtSignal(int)
    
    def __init__(self, project: LupineProject, scene_path: str):
        super().__init__()
        self.project = project
        self.scene_path = scene_path
        self.process = None
    
    def run(self):
        """Run the game process"""
        try:
            # Create a simple game runner script
            runner_script = self.create_runner_script()
            
            # Start the process
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.read_stdout)
            self.process.readyReadStandardError.connect(self.read_stderr)
            self.process.finished.connect(self.on_finished)
            
            # Run Python with the runner script
            python_exe = sys.executable
            self.process.start(python_exe, [runner_script])
            
            # Wait for process to finish
            self.process.waitForFinished(-1)
            
        except Exception as e:
            self.error_received.emit(f"Failed to start game: {e}")
    
    def create_runner_script(self) -> str:
        """Create a temporary runner script"""
        project_path = str(self.project.project_path).replace('\\', '\\\\')
        scene_file_path = str(self.project.get_absolute_path(self.scene_path)).replace('\\', '\\\\')

        # Get the Lupine Engine path (where this script is located)
        import os
        lupine_engine_path = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '\\\\')

        # Create the template with placeholders
        template = '''
import sys
import os
# Add both the Lupine Engine path and project path to sys.path
sys.path.insert(0, r"{lupine_engine_path}")
sys.path.insert(0, r"{project_path}")

import pygame
import json
from pathlib import Path
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Import our new rendering and audio systems
from core.opengl_renderer import OpenGLRenderer
from core.openal_audio import OpenALAudioSystem

# Import input constants at module level
try:
    from core.input_constants import *
    INPUT_CONSTANTS_AVAILABLE = True
except ImportError as e:
    print(f"Input constants not available: {e}")
    INPUT_CONSTANTS_AVAILABLE = False

# Import Python runtime for script execution
try:
    from core.python_runtime import PythonScriptRuntime, PythonScriptInstance
    from core.scene import Scene, Node, Node2D, Sprite, Camera2D
    PYTHON_RUNTIME_AVAILABLE = True
except ImportError as e:
    print(f"Python runtime not available: {e}")
    PYTHON_RUNTIME_AVAILABLE = False

class LupineGameWindow:
    def __init__(self, project_path: str):
        print("DEBUG: LupineGameWindow.__init__() called")

        # Initialize Pygame
        pygame.init()

        # Set up OpenGL context
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)

        # Create window
        self.width = 1280
        self.height = 720
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption("Lupine Engine - Game Runner")

        # Game bounds for UI scaling (from project settings or default)
        self.game_bounds_width = 1920  # Base resolution width
        self.game_bounds_height = 1080  # Base resolution height
        self.load_game_bounds_from_project()

        print("DEBUG: Pygame window initialized")
        self.project_path = project_path  # Store project path for texture loading
        self.scene = None
        self.scene_data = None
        self.camera = None
        self.running = True
        self.clock = pygame.time.Clock()

        # Initialize rendering and audio systems
        self.renderer = OpenGLRenderer(self.width, self.height)
        self.audio_system = OpenALAudioSystem()

        # Initialize texture cache for fallback rendering
        self.textures = {}

        print("DEBUG: Renderer and audio systems initialized")

        # Physics system
        try:
            from core.physics import PhysicsWorld
            self.physics_world = PhysicsWorld()
            self.physics_enabled = True
            print("Physics system initialized")
        except ImportError as e:
            print(f"Physics system not available: {e}")
            self.physics_world = None
            self.physics_enabled = False

        # Input system
        try:
            from core.input_manager import InputManager
            from pathlib import Path
            project_path_obj = Path(self.project_path)
            self.input_manager = InputManager(project_path_obj)
            self.pressed_keys = set()
            self.mouse_buttons = set()
            self.mouse_position = (0, 0)
            self.current_modifiers = set()
            print("Input system initialized")

            # Debug: Show available actions
            actions = self.input_manager.get_all_actions()
            print(f"Available input actions: {list(actions.keys())}")

            # Debug: Show move_left action details
            move_left = actions.get("move_left")
            if move_left:
                print(f"move_left action events: {[f'type={e.type}, code={e.code}' for e in move_left.events]}")

        except ImportError as e:
            print(f"Input system not available: {e}")
            self.input_manager = None
        except Exception as e:
            print(f"Error initializing input system: {e}")
            import traceback
            traceback.print_exc()
            self.input_manager = None

        # Python Runtime for script execution
        if PYTHON_RUNTIME_AVAILABLE:
            self.python_runtime = PythonScriptRuntime(game_runtime=self)
            # Add game runtime methods to Python scope
            self.setup_python_builtins()
        else:
            self.python_runtime = None

        # LSC runtime compatibility (for backward compatibility)
        self.lsc_runtime = self.python_runtime

        print("DEBUG: About to call load_scene()")
        self.load_scene()
        print("DEBUG: load_scene() completed")

    def setup_python_builtins(self):
        """Setup additional built-in functions for Python scripts"""
        if not self.python_runtime:
            return

        # Add game-specific functions to global scope
        builtins = {
            "get_node": self.get_node,
            "find_node": self.find_node_by_name,
            "create_sprite": self.create_sprite,
            "is_key_pressed": self.is_key_pressed,
            "change_scene": self.change_scene,
            "reload_scene": self.reload_scene,
            "get_scene": self.get_scene,
            "get_delta_time": lambda: self.python_runtime.delta_time if self.python_runtime else 0.0,
            "get_runtime_time": lambda: self.python_runtime.get_runtime_time() if self.python_runtime else 0.0,
            "get_fps": lambda: 1.0 / self.python_runtime.delta_time if self.python_runtime and self.python_runtime.delta_time > 0 else 0.0,

            # Input action functions
            "is_action_pressed": self.is_action_pressed,
            "is_action_just_pressed": self.is_action_just_pressed,
            "is_action_just_released": self.is_action_just_released,
            "get_action_strength": self.get_action_strength,
            "is_mouse_button_pressed": self.is_mouse_button_pressed,
            "get_mouse_position": self.get_mouse_position,
            "get_global_mouse_position": self.get_global_mouse_position,
        }

        # Add input constants if available
        if INPUT_CONSTANTS_AVAILABLE:
            input_constants = {
                # Mouse button constants
                "MOUSE_BUTTON_LEFT": MOUSE_BUTTON_LEFT,
                "MOUSE_BUTTON_RIGHT": MOUSE_BUTTON_RIGHT,
                "MOUSE_BUTTON_MIDDLE": MOUSE_BUTTON_MIDDLE,
                "MOUSE_BUTTON_WHEEL_UP": MOUSE_BUTTON_WHEEL_UP,
                "MOUSE_BUTTON_WHEEL_DOWN": MOUSE_BUTTON_WHEEL_DOWN,

                # Common key constants
                "KEY_ESCAPE": KEY_ESCAPE,
                "KEY_ENTER": KEY_ENTER,
                "KEY_SPACE": KEY_SPACE,
                "KEY_SHIFT": KEY_SHIFT,
                "KEY_CTRL": KEY_CTRL,
                "KEY_ALT": KEY_ALT,

                # Arrow keys
                "KEY_LEFT": KEY_LEFT,
                "KEY_RIGHT": KEY_RIGHT,
                "KEY_UP": KEY_UP,
                "KEY_DOWN": KEY_DOWN,

                # WASD keys
                "KEY_W": KEY_W,
                "KEY_A": KEY_A,
                "KEY_S": KEY_S,
                "KEY_D": KEY_D,

                # Other common keys
                "KEY_E": KEY_E,
                "KEY_F": KEY_F,
                "KEY_Q": KEY_Q,
                "KEY_R": KEY_R,
                "KEY_T": KEY_T,

                # Function keys
                "KEY_F1": KEY_F1,
                "KEY_F2": KEY_F2,
                "KEY_F3": KEY_F3,
                "KEY_F4": KEY_F4,
                "KEY_F5": KEY_F5,
                "KEY_F6": KEY_F6,
                "KEY_F7": KEY_F7,
                "KEY_F8": KEY_F8,
                "KEY_F9": KEY_F9,
                "KEY_F10": KEY_F10,
                "KEY_F11": KEY_F11,
                "KEY_F12": KEY_F12,
            }
            builtins.update(input_constants)

        for name, func in builtins.items():
            self.python_runtime.add_builtin(name, func)

    def load_game_bounds_from_project(self):
        """Load game bounds from project settings"""
        try:
            project_file = Path(self.project_path) / "project.lupine"
            if project_file.exists():
                with open(project_file, 'r') as f:
                    project_data = json.load(f)

                # Get display settings
                display_settings = project_data.get("settings", {}).get("display", {})
                self.game_bounds_width = display_settings.get("width", 1920)
                self.game_bounds_height = display_settings.get("height", 1080)

                print(f"Loaded game bounds from project: {self.game_bounds_width}x{self.game_bounds_height}")
            else:
                print(f"Project file not found, using default game bounds: {self.game_bounds_width}x{self.game_bounds_height}")
        except Exception as e:
            print(f"Error loading project settings: {e}, using default game bounds")
            self.game_bounds_width = 1920
            self.game_bounds_height = 1080



    def load_scene(self):
        print("DEBUG: load_scene() called")
        try:
            scene_file = r"{scene_file_path}"
            print(f"DEBUG: Scene file path: {scene_file}")
            with open(scene_file, 'r') as f:
                self.scene_data = json.load(f)
            print(f"DEBUG: JSON loaded successfully")
            print(f"Loaded scene: {self.scene_data.get('name', 'Unknown')}")
            print(f"Scene file: {scene_file}")
            print(f"Scene nodes: {len(self.scene_data.get('nodes', []))}")

            # Load scene using proper Scene class
            if PYTHON_RUNTIME_AVAILABLE:
                print("Python runtime is available, attempting to load Scene object...")
                try:
                    self.scene = Scene.load_from_file(scene_file)
                    print(f"Scene object loaded successfully! Root nodes: {len(self.scene.root_nodes)}")
                    self.setup_scene()
                except Exception as scene_error:
                    print(f"Failed to load Scene object: {scene_error}")
                    import traceback
                    traceback.print_exc()
                    print("Falling back to basic scene rendering")
                    self.scene = None
            else:
                print("Python runtime not available, using basic scene rendering")

        except Exception as e:
            print(f"Error loading scene: {e}")
            # Create a default scene if loading fails
            self.scene_data = {
                "name": "Default",
                "nodes": [{
                    "name": "Main",
                    "type": "Node2D",
                    "position": [0, 0],
                    "children": []
                }]
            }

    def setup_scene(self):
        """Setup the scene with proper rendering and cameras"""
        # Initialize sprite tracking (no longer using Arcade sprite lists)
        self.sprites = []
        self.ui_elements = []

        # Find cameras in the scene
        if self.scene:
            for root_node in self.scene.root_nodes:
                self.find_cameras(root_node)
                # Setup nodes and load their scripts
                self.setup_node(root_node)
        elif self.scene_data:
            # Fallback to scene data if Scene object not available
            nodes = self.scene_data.get("nodes", [])
            for node in nodes:
                self.find_cameras(node)

    def find_cameras(self, node):
        """Find and setup cameras in the scene"""
        # Handle both node objects and scene data dictionaries
        if hasattr(node, 'type') and node.type == "Camera2D" and getattr(node, 'current', False):
            # Node object case
            self.camera = self.renderer.camera
            # Use world coordinates directly
            self.camera.set_position(node.position[0], node.position[1])
            if hasattr(node, 'zoom'):
                zoom_val = node.zoom[0] if isinstance(node.zoom, list) else node.zoom
                self.camera.set_zoom(zoom_val)
            print(f"Found active camera: {node.name} at {node.position}")
        elif isinstance(node, dict) and node.get("type") == "Camera2D" and node.get("current", False):
            # Scene data dictionary case
            self.camera = self.renderer.camera
            position = node.get("position", [0.0, 0.0])
            zoom = node.get("zoom", [1.0, 1.0])
            offset = node.get("offset", [0.0, 0.0])

            # Apply camera offset
            camera_x = position[0] + offset[0]
            camera_y = position[1] + offset[1]

            self.camera.set_position(camera_x, camera_y)
            zoom_val = zoom[0] if isinstance(zoom, list) else zoom  # Use X zoom for uniform scaling
            self.camera.set_zoom(zoom_val)
            print(f"Found active camera: {node.get('name', 'Camera2D')} at world {position}, final {(camera_x, camera_y)} with zoom {zoom}")

        # Recursively check children
        if hasattr(node, 'children'):
            for child in node.children:
                self.find_cameras(child)
        elif isinstance(node, dict) and "children" in node:
            for child in node["children"]:
                self.find_cameras(child)

    def setup_node(self, node):
        """Setup a node and its children, including script loading"""
        try:
            print(f"Setting up node: {node.name} (type: {getattr(node, 'type', 'Unknown')})")

            # Load and execute node script if it exists
            if hasattr(node, 'script_path') and node.script_path:
                print(f"Node {node.name} has script_path: {node.script_path}")
                if self.python_runtime:
                    script_file = Path(self.project_path) / node.script_path
                    print(f"Looking for script file: {script_file}")
                    if script_file.exists():
                        print(f"Script file exists, loading...")
                        with open(script_file, 'r') as f:
                            script_content = f.read()

                        # Create script instance for this node
                        script_instance = PythonScriptInstance(node, node.script_path, self.python_runtime)

                        try:
                            # Execute script
                            success = self.python_runtime.execute_script(script_content, script_instance)

                            # Attach script instance to node
                            node.script_instance = script_instance

                            if success:
                                # Call ready method if it exists (support both _ready and _on_ready)
                                ready_called = False
                                if script_instance.has_method('_ready'):
                                    print(f"Calling _ready for {node.name}")
                                    script_instance.call_method('_ready')
                                    script_instance.ready_called = True
                                    ready_called = True
                                elif script_instance.has_method('_on_ready'):
                                    print(f"Calling _on_ready for {node.name}")
                                    script_instance.call_method('_on_ready')
                                    script_instance.ready_called = True
                                    ready_called = True

                                if not ready_called:
                                    print(f"No _ready or _on_ready method found for {node.name}")

                                print(f"SUCCESS: Loaded script for {node.name}: {node.script_path}")
                            else:
                                print(f"Failed to execute script for {node.name}")

                        except Exception as e:
                            print(f"Error loading script for {node.name}: {e}")
                            # Don't crash the entire game - continue with other nodes
                            # Create a minimal script instance so the node still works
                            node.script_instance = script_instance
                    else:
                        print(f"Script file not found: {script_file}")
                else:
                    print(f"Python runtime not available for {node.name}")
            else:
                print(f"Node {node.name} has no script_path")

            # Setup sprite nodes (including AnimatedSprite)
            if isinstance(node, Sprite):
                self.setup_sprite_node(node)

            # Setup UI nodes for rendering
            if hasattr(node, 'type'):
                if node.type == "TextureRect":
                    self.setup_texture_rect_node(node)
                elif node.type == "Panel":
                    self.setup_panel_node(node)
                elif node.type in ["Button", "Label", "ColorRect"]:
                    self.setup_ui_node(node)

            # Setup physics nodes
            if self.physics_enabled and self.physics_world:
                from core.scene import RigidBody2D, StaticBody2D, KinematicBody2D, Area2D
                if isinstance(node, (RigidBody2D, StaticBody2D, KinematicBody2D, Area2D)):
                    self.setup_physics_node(node)

        except Exception as e:
            print(f"Error setting up node {node.name}: {e}")

        # Setup children
        for child in node.children:
            self.setup_node(child)

    def setup_physics_node(self, node):
        """Setup physics for a physics node"""
        try:
            if self.physics_world:
                physics_body = self.physics_world.add_node(node)
                if physics_body:
                    print(f"Added physics body for {node.name}")

                    # Setup collision callbacks for RigidBody2D
                    from core.scene import RigidBody2D
                    if isinstance(node, RigidBody2D):
                        def collision_callback(other_body, contact):
                            # Call LSC collision methods if available
                            if hasattr(node, 'script_instance'):
                                try:
                                    node.script_instance.call_method('_on_body_contact',
                                                                   other_body.node,
                                                                   contact.point,
                                                                   contact.normal,
                                                                   contact.impulse)
                                except:
                                    pass  # Method might not exist

                        physics_body.collision_callbacks.append(collision_callback)

        except Exception as e:
            print(f"Error setting up physics for {node.name}: {e}")

    def setup_sprite_node(self, sprite_node):
        """Setup a sprite node with proper texture loading - simplified"""
        try:
            print(f"Setting up sprite: {sprite_node.name}")

            # Get texture path
            texture_path = getattr(sprite_node, 'texture', None)

            # Get actual texture size if available
            actual_width = 64  # Default
            actual_height = 64  # Default

            if texture_path:
                # Try to get actual texture dimensions
                try:
                    from PIL import Image
                    full_path = str(Path(self.project_path) / texture_path)
                    if Path(full_path).exists():
                        with Image.open(full_path) as img:
                            actual_width, actual_height = img.size
                        print(f"Loaded texture size: {actual_width}x{actual_height}")
                except Exception as e:
                    print(f"Could not get texture size: {e}")

            # Create sprite data using actual texture size
            sprite_data = {
                'texture_path': texture_path,
                'position': [sprite_node.position[0], sprite_node.position[1]],
                'size': [actual_width, actual_height],
                'rotation': getattr(sprite_node, 'rotation', 0),
                'alpha': 1.0
            }

            # Apply scale if present
            if hasattr(sprite_node, 'scale') and sprite_node.scale:
                sprite_data['size'] = [actual_width * sprite_node.scale[0], actual_height * sprite_node.scale[1]]

            # Apply modulation (alpha)
            if hasattr(sprite_node, 'modulate') and sprite_node.modulate and len(sprite_node.modulate) > 3:
                sprite_data['alpha'] = sprite_node.modulate[3]

            # Store reference to original node for updates
            sprite_data['lupine_node'] = sprite_node
            sprite_node.sprite_data = sprite_data

            # Add to sprite list
            self.sprites.append(sprite_data)
            print(f"Added sprite {sprite_node.name} with size {sprite_data['size']} at position {sprite_data['position']}")

        except Exception as e:
            print(f"Error setting up sprite {sprite_node.name}: {e}")
            import traceback
            traceback.print_exc()

    def setup_texture_rect_node(self, texture_rect_node):
        """Setup a TextureRect node for UI rendering"""
        try:
            print(f"Setting up TextureRect: {texture_rect_node.name}")

            # Get texture path
            texture_path = getattr(texture_rect_node, 'texture', None)

            # Get position and size from UI node properties
            world_position = getattr(texture_rect_node, 'position', [0, 0])
            rect_size = getattr(texture_rect_node, 'rect_size', [100, 100])

            # Get anchor properties
            anchor_left = getattr(texture_rect_node, 'anchor_left', 0.0)
            anchor_top = getattr(texture_rect_node, 'anchor_top', 0.0)
            anchor_right = getattr(texture_rect_node, 'anchor_right', 0.0)
            anchor_bottom = getattr(texture_rect_node, 'anchor_bottom', 0.0)

            # Get margin properties
            margin_left = getattr(texture_rect_node, 'margin_left', 0.0)
            margin_top = getattr(texture_rect_node, 'margin_top', 0.0)
            margin_right = getattr(texture_rect_node, 'margin_right', 0.0)
            margin_bottom = getattr(texture_rect_node, 'margin_bottom', 0.0)

            # Special handling for full-screen background textures
            # If the texture rect is sized to match the game bounds and positioned at center,
            # treat it as a background that should fill the entire screen
            is_background = (
                rect_size[0] >= self.game_bounds_width * 0.9 and  # Close to full width
                rect_size[1] >= self.game_bounds_height * 0.9 and  # Close to full height
                abs(world_position[0]) < 50 and  # Close to center X
                abs(world_position[1]) < 50 and  # Close to center Y
                anchor_left == 0.0 and anchor_top == 0.0 and
                anchor_right == 0.0 and anchor_bottom == 0.0  # Default anchors
            )

            if is_background:
                # For background textures, position at (0,0) and use full game bounds size
                ui_position = [0, 0]
                actual_width = self.game_bounds_width
                actual_height = self.game_bounds_height
                print(f"Detected background texture {texture_rect_node.name}, using full screen: {actual_width}x{actual_height}")
            else:
                # Calculate final position using anchors and margins
                ui_position = self.calculate_ui_position_with_anchors(
                    world_position, rect_size,
                    anchor_left, anchor_top, anchor_right, anchor_bottom,
                    margin_left, margin_top, margin_right, margin_bottom
                )

                # Get actual texture size if available
                actual_width = rect_size[0]
                actual_height = rect_size[1]

            if texture_path and not is_background:
                # Try to get actual texture dimensions (only for non-background textures)
                try:
                    from PIL import Image
                    full_path = str(Path(self.project_path) / texture_path)
                    if Path(full_path).exists():
                        with Image.open(full_path) as img:
                            tex_width, tex_height = img.size
                        print(f"Loaded texture size: {tex_width}x{tex_height}")

                        # For TextureRect, use the rect_size unless it's default
                        if rect_size == [100, 100]:  # Default size
                            actual_width, actual_height = tex_width, tex_height
                except Exception as e:
                    print(f"Could not get texture size: {e}")

            # Create UI element data for TextureRect
            ui_element_data = {
                'type': 'TextureRect',
                'texture_path': texture_path,
                'position': [ui_position[0], ui_position[1]],
                'size': [actual_width, actual_height],
                'stretch_mode': getattr(texture_rect_node, 'stretch_mode', 'stretch'),
                'flip_h': getattr(texture_rect_node, 'flip_h', False),
                'flip_v': getattr(texture_rect_node, 'flip_v', False),
                'alpha': 1.0
            }

            # Store reference to original node for updates
            ui_element_data['lupine_node'] = texture_rect_node
            texture_rect_node.ui_element_data = ui_element_data

            # Add to UI elements list
            self.ui_elements.append(ui_element_data)
            print(f"Added TextureRect {texture_rect_node.name} with size {ui_element_data['size']} at position {ui_element_data['position']}")

        except Exception as e:
            print(f"Error setting up TextureRect {texture_rect_node.name}: {e}")
            import traceback
            traceback.print_exc()

    def setup_panel_node(self, panel_node):
        """Setup a Panel node for UI rendering"""
        try:
            print(f"Setting up Panel: {panel_node.name}")

            # Get panel properties
            world_position = getattr(panel_node, 'position', [0, 0])
            rect_size = getattr(panel_node, 'rect_size', [100, 100])

            # Get anchor properties
            anchor_left = getattr(panel_node, 'anchor_left', 0.0)
            anchor_top = getattr(panel_node, 'anchor_top', 0.0)
            anchor_right = getattr(panel_node, 'anchor_right', 0.0)
            anchor_bottom = getattr(panel_node, 'anchor_bottom', 0.0)

            # Get margin properties
            margin_left = getattr(panel_node, 'margin_left', 0.0)
            margin_top = getattr(panel_node, 'margin_top', 0.0)
            margin_right = getattr(panel_node, 'margin_right', 0.0)
            margin_bottom = getattr(panel_node, 'margin_bottom', 0.0)

            # Calculate final position using anchors and margins
            ui_position = self.calculate_ui_position_with_anchors(
                world_position, rect_size,
                anchor_left, anchor_top, anchor_right, anchor_bottom,
                margin_left, margin_top, margin_right, margin_bottom
            )

            panel_color = getattr(panel_node, 'panel_color', [0.2, 0.2, 0.2, 1.0])
            corner_radius = getattr(panel_node, 'corner_radius', 0.0)
            border_width = getattr(panel_node, 'border_width', 0.0)
            border_color = getattr(panel_node, 'border_color', [0.0, 0.0, 0.0, 1.0])

            # Create UI element data for Panel
            ui_element_data = {
                'type': 'Panel',
                'position': [ui_position[0], ui_position[1]],
                'size': [rect_size[0], rect_size[1]],
                'panel_color': panel_color,
                'corner_radius': corner_radius,
                'border_width': border_width,
                'border_color': border_color,
                'alpha': panel_color[3] if len(panel_color) > 3 else 1.0
            }

            # Store reference to original node for updates
            ui_element_data['lupine_node'] = panel_node
            panel_node.ui_element_data = ui_element_data

            # Add to UI elements list
            self.ui_elements.append(ui_element_data)
            print(f"Added Panel {panel_node.name} with size {ui_element_data['size']} at position {ui_element_data['position']}")

        except Exception as e:
            print(f"Error setting up Panel {panel_node.name}: {e}")
            import traceback
            traceback.print_exc()

    def setup_ui_node(self, ui_node):
        """Setup a generic UI node for rendering"""
        try:
            print(f"Setting up UI node: {ui_node.name} ({ui_node.type})")

            # Get common UI properties
            world_position = getattr(ui_node, 'position', [0, 0])
            rect_size = getattr(ui_node, 'rect_size', [100, 100])

            # Get anchor properties
            anchor_left = getattr(ui_node, 'anchor_left', 0.0)
            anchor_top = getattr(ui_node, 'anchor_top', 0.0)
            anchor_right = getattr(ui_node, 'anchor_right', 0.0)
            anchor_bottom = getattr(ui_node, 'anchor_bottom', 0.0)

            # Get margin properties
            margin_left = getattr(ui_node, 'margin_left', 0.0)
            margin_top = getattr(ui_node, 'margin_top', 0.0)
            margin_right = getattr(ui_node, 'margin_right', 0.0)
            margin_bottom = getattr(ui_node, 'margin_bottom', 0.0)

            # Calculate final position using anchors and margins
            ui_position = self.calculate_ui_position_with_anchors(
                world_position, rect_size,
                anchor_left, anchor_top, anchor_right, anchor_bottom,
                margin_left, margin_top, margin_right, margin_bottom
            )

            # Create UI element data
            ui_element_data = {
                'type': ui_node.type,
                'position': [ui_position[0], ui_position[1]],
                'size': [rect_size[0], rect_size[1]],
                'alpha': 1.0
            }

            # Add type-specific properties
            if ui_node.type == "Button":
                ui_element_data.update({
                    'text': getattr(ui_node, 'text', 'Button'),
                    'button_color': getattr(ui_node, 'button_color', [0.4, 0.4, 0.4, 1.0]),
                    'text_color': getattr(ui_node, 'text_color', [1.0, 1.0, 1.0, 1.0]),
                    'font_size': getattr(ui_node, 'font_size', 16)
                })
            elif ui_node.type == "Label":
                ui_element_data.update({
                    'text': getattr(ui_node, 'text', 'Label'),
                    'font_size': getattr(ui_node, 'font_size', 14),
                    'text_color': getattr(ui_node, 'text_color', [1.0, 1.0, 1.0, 1.0])
                })
            elif ui_node.type == "ColorRect":
                ui_element_data.update({
                    'color': getattr(ui_node, 'color', [1.0, 1.0, 1.0, 1.0])
                })

            # Store reference to original node for updates
            ui_element_data['lupine_node'] = ui_node
            ui_node.ui_element_data = ui_element_data

            # Add to UI elements list
            self.ui_elements.append(ui_element_data)
            print(f"Added {ui_node.type} {ui_node.name} with size {ui_element_data['size']} at position {ui_element_data['position']}")

        except Exception as e:
            print(f"Error setting up UI node {ui_node.name}: {e}")
            import traceback
            traceback.print_exc()

    def setup(self):
        """Initialize the game"""
        print("Game setup complete")
        print("ESC to exit")

    def run(self):
        """Main game loop"""
        print("Starting game loop...")

        while self.running:
            # Calculate delta time
            delta_time = self.clock.tick(60) / 1000.0  # 60 FPS, convert to seconds

            # Handle events
            self.handle_events()

            # Update game logic
            self.update(delta_time)

            # Render
            self.draw()

            # Swap buffers
            pygame.display.flip()

        # Cleanup
        self.cleanup()
        pygame.quit()

    def handle_events(self):
        """Handle Pygame events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                self.on_key_press(event.key, pygame.key.get_mods())
            elif event.type == KEYUP:
                self.on_key_release(event.key, pygame.key.get_mods())
            elif event.type == MOUSEBUTTONDOWN:
                self.on_mouse_press(event.pos[0], event.pos[1], event.button, 0)
            elif event.type == MOUSEBUTTONUP:
                self.on_mouse_release(event.pos[0], event.pos[1], event.button, 0)
            elif event.type == MOUSEMOTION:
                self.on_mouse_motion(event.pos[0], event.pos[1], event.rel[0], event.rel[1])
            elif event.type == VIDEORESIZE:
                self.on_resize(event.w, event.h)

    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse button press"""
        self.mouse_buttons.add(button)
        self.mouse_position = (x, y)

        # Update input manager
        if self.input_manager:
            self.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

        # Forward to LSC runtime
        if self.lsc_runtime and self.scene:
            for root_node in self.scene.root_nodes:
                self.handle_node_input(root_node, 'on_mouse_press', button, pos)

    def on_mouse_release(self, x, y, button, modifiers):
        """Handle mouse button release"""
        self.mouse_buttons.discard(button)
        self.mouse_position = (x, y)

        # Update input manager
        if self.input_manager:
            self.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

    def on_mouse_motion(self, x, y, dx, dy):
        """Handle mouse motion"""
        self.mouse_position = (x, y)

    def on_resize(self, width, height):
        """Handle window resize"""
        self.width = width
        self.height = height
        self.renderer.resize(width, height)
        print(f"Window resized to {width}x{height}")

    def get_ui_scale_factors(self):
        """Get UI scaling factors based on current window size vs game bounds"""
        scale_x = self.width / self.game_bounds_width
        scale_y = self.height / self.game_bounds_height
        return scale_x, scale_y

    def scale_ui_position(self, position):
        """Scale UI position from game bounds to current window size"""
        scale_x, scale_y = self.get_ui_scale_factors()
        return [position[0] * scale_x, position[1] * scale_y]

    def scale_ui_size(self, size):
        """Scale UI size from game bounds to current window size"""
        scale_x, scale_y = self.get_ui_scale_factors()
        return [size[0] * scale_x, size[1] * scale_y]

    def world_to_ui_coordinates(self, world_position):
        """Convert world coordinates to UI coordinates"""
        # For UI nodes, the scene view position should directly translate to UI coordinates
        # The scene view shows UI elements as they should appear in the game bounds
        # So we need to map the scene view coordinate system to the UI coordinate system

        # Scene view coordinates: (0,0) = center, Y increases upward
        # UI coordinates: (0,0) = top-left, Y increases downward
        # Game bounds represent the UI coordinate space

        # Convert from scene view space to UI space
        ui_x = world_position[0] + self.game_bounds_width / 2
        ui_y = self.game_bounds_height / 2 - world_position[1]

        return [ui_x, ui_y]

    def calculate_ui_position_with_anchors(self, world_position, rect_size,
                                         anchor_left, anchor_top, anchor_right, anchor_bottom,
                                         margin_left, margin_top, margin_right, margin_bottom):
        """Calculate UI position using anchors and margins like Godot"""
        # Parent size is the game bounds (viewport size)
        parent_width = self.game_bounds_width
        parent_height = self.game_bounds_height

        # Calculate anchor positions
        anchor_left_pos = anchor_left * parent_width
        anchor_top_pos = anchor_top * parent_height
        anchor_right_pos = anchor_right * parent_width
        anchor_bottom_pos = anchor_bottom * parent_height

        # If anchors are the same (normal positioning), use position + margins
        if anchor_left == anchor_right and anchor_top == anchor_bottom:
            # For default anchors (0,0,0,0), directly convert scene position to UI coordinates
            if anchor_left == 0.0 and anchor_top == 0.0:
                # Direct translation from scene view to UI coordinates
                ui_pos = self.world_to_ui_coordinates(world_position)
                final_x = ui_pos[0] + margin_left
                final_y = ui_pos[1] + margin_top
            else:
                # For non-zero anchors, position relative to anchor point
                ui_pos = self.world_to_ui_coordinates(world_position)
                final_x = anchor_left_pos + ui_pos[0] + margin_left
                final_y = anchor_top_pos + ui_pos[1] + margin_top
        else:
            # Stretched anchors - calculate based on anchor rectangle
            final_x = anchor_left_pos + margin_left
            final_y = anchor_top_pos + margin_top

            # For stretched elements, size is determined by anchor rectangle
            if anchor_left != anchor_right:
                rect_size[0] = anchor_right_pos - anchor_left_pos - margin_left - margin_right
            if anchor_top != anchor_bottom:
                rect_size[1] = anchor_bottom_pos - anchor_top_pos - margin_top - margin_bottom

        return [final_x, final_y]

    def cleanup(self):
        """Clean up resources"""
        if self.renderer:
            self.renderer.cleanup()
        if self.audio_system:
            self.audio_system.cleanup()

    def draw(self):
        """Main draw method - simplified"""
        # Clear the screen
        self.renderer.clear()

        # Use camera if available
        if self.camera:
            self.renderer.begin_camera()

        # Draw sprites directly - no complex fallback systems
        for sprite_data in self.sprites:
            self.draw_sprite_data(sprite_data)

        # End camera rendering
        if self.camera:
            self.renderer.end_camera()

        # Draw minimal UI overlay
        self.draw_ui()

    def draw_sprite_data(self, sprite_data):
        """Draw a sprite using our renderer"""
        try:
            texture_path = sprite_data.get('texture_path')
            position = sprite_data.get('position', [0, 0])
            size = sprite_data.get('size', [64, 64])
            rotation = sprite_data.get('rotation', 0)
            alpha = sprite_data.get('alpha', 1.0)

            if texture_path:
                full_path = str(Path(self.project_path) / texture_path)
                self.renderer.draw_sprite(
                    full_path, position[0], position[1],
                    size[0], size[1], rotation, alpha
                )
            else:
                # Draw placeholder rectangle
                color = sprite_data.get('color', (0.0, 1.0, 0.0, alpha))
                self.renderer.draw_rectangle(
                    position[0], position[1], size[0], size[1],
                    color, filled=True
                )
        except Exception as e:
            print(f"Error drawing sprite: {e}")













    def draw_ui(self):
        """Draw UI elements including TextureRect"""
        # Draw TextureRect and other UI elements
        for ui_element in self.ui_elements:
            self.draw_ui_element(ui_element)

    def draw_ui_element(self, ui_element):
        """Draw a UI element using our renderer with proper scaling"""
        try:
            element_type = ui_element.get('type', 'Unknown')

            # Get base position and size
            base_position = ui_element.get('position', [0, 0])
            base_size = ui_element.get('size', [100, 100])

            # Apply UI scaling
            scaled_position = self.scale_ui_position(base_position)
            scaled_size = self.scale_ui_size(base_size)

            if element_type == 'TextureRect':
                texture_path = ui_element.get('texture_path')
                alpha = ui_element.get('alpha', 1.0)

                if texture_path:
                    full_path = str(Path(self.project_path) / texture_path)
                    # Use UI coordinate system (no camera transformation)
                    self.renderer.draw_ui_sprite(
                        full_path, scaled_position[0], scaled_position[1],
                        scaled_size[0], scaled_size[1], 0.0, alpha
                    )
                else:
                    # Draw placeholder rectangle for TextureRect without texture
                    color = (0.8, 0.8, 0.8, alpha)
                    self.renderer.draw_ui_rectangle(
                        scaled_position[0], scaled_position[1], scaled_size[0], scaled_size[1],
                        color, filled=True
                    )

            elif element_type == 'Panel':
                panel_color = ui_element.get('panel_color', [0.2, 0.2, 0.2, 1.0])
                border_width = ui_element.get('border_width', 0.0)
                border_color = ui_element.get('border_color', [0.0, 0.0, 0.0, 1.0])

                # Draw panel background
                self.renderer.draw_ui_rectangle(
                    scaled_position[0], scaled_position[1], scaled_size[0], scaled_size[1],
                    tuple(panel_color), filled=True
                )

                # Draw border if specified
                if border_width > 0:
                    scaled_border_width = border_width * min(self.get_ui_scale_factors())
                    # Draw border as outline
                    self.renderer.draw_ui_rectangle(
                        scaled_position[0], scaled_position[1], scaled_size[0], scaled_size[1],
                        tuple(border_color), filled=False
                    )

            elif element_type == 'Button':
                button_color = ui_element.get('button_color', [0.4, 0.4, 0.4, 1.0])
                text = ui_element.get('text', 'Button')
                text_color = ui_element.get('text_color', [1.0, 1.0, 1.0, 1.0])

                # Draw button background
                self.renderer.draw_ui_rectangle(
                    scaled_position[0], scaled_position[1], scaled_size[0], scaled_size[1],
                    tuple(button_color), filled=True
                )

                # Draw button text
                if text:
                    # Get font size from UI element or use default
                    base_font_size = ui_element.get('font_size', 16)

                    # Scale font size with UI scaling
                    scale_x, scale_y = self.get_ui_scale_factors()
                    scaled_font_size = int(base_font_size * min(scale_x, scale_y))

                    # Get actual text dimensions for proper centering
                    font = self.renderer.get_font(None, scaled_font_size)
                    text_width, text_height = font.size(text)

                    # Center text in button
                    text_x = scaled_position[0] + (scaled_size[0] - text_width) / 2
                    text_y = scaled_position[1] + (scaled_size[1] - text_height) / 2
                    self.renderer.draw_ui_text(
                        text, text_x, text_y,
                        font_size=scaled_font_size, color=tuple(text_color)
                    )

            elif element_type == 'ColorRect':
                color = ui_element.get('color', [1.0, 1.0, 1.0, 1.0])

                # Draw colored rectangle
                self.renderer.draw_ui_rectangle(
                    scaled_position[0], scaled_position[1], scaled_size[0], scaled_size[1],
                    tuple(color), filled=True
                )

            elif element_type == 'Label':
                text = ui_element.get('text', 'Label')
                text_color = ui_element.get('text_color', [1.0, 1.0, 1.0, 1.0])
                base_font_size = ui_element.get('font_size', 14)

                # Draw label text
                if text:
                    # Scale font size with UI scaling
                    scale_x, scale_y = self.get_ui_scale_factors()
                    scaled_font_size = int(base_font_size * min(scale_x, scale_y))

                    self.renderer.draw_ui_text(
                        text, scaled_position[0], scaled_position[1],
                        font_size=scaled_font_size, color=tuple(text_color)
                    )

        except Exception as e:
            print(f"Error drawing UI element: {e}")

    def on_resize(self, width, height):
        """Handle window resize - simplified"""
        self.width = width
        self.height = height
        self.renderer.resize(width, height)
        print(f"Window resized to {width}x{height}")

    def update(self, delta_time):
        """Update game logic and run scripts"""
        # Update audio system
        if self.audio_system:
            self.audio_system.update()

        # Update input manager every frame (important for "just pressed/released" detection)
        if self.input_manager:
            self.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

        # Update Python runtime timing
        if self.python_runtime:
            self.python_runtime.update_time(delta_time)

        # Call script update methods if available (before physics to allow script-driven movement)
        if self.python_runtime and self.scene:
            for root_node in self.scene.root_nodes:
                self.update_node_scripts(root_node, delta_time)

        # Update physics simulation (after scripts so script movement can be processed)
        if self.physics_enabled and self.physics_world:
            self.physics_world.step(delta_time)

        # Update sprites
        for sprite_data in self.sprites:
            # Update sprite data if needed
            if 'lupine_node' in sprite_data:
                node = sprite_data['lupine_node']
                # Sync position from node to sprite data
                sprite_data['position'] = [node.position[0], node.position[1]]

        # Ensure all sprite positions are synchronized with their nodes
        self.synchronize_sprite_positions()

        # DEBUG: Force update PlayerController sprite position
        self.debug_force_player_sprite_update()

    def synchronize_sprite_positions(self):
        """Ensure all arcade sprites are positioned correctly based on their node positions"""
        try:
            if not self.scene:
                return

            for root_node in self.scene.root_nodes:
                self._sync_node_sprite_position(root_node)
        except Exception as e:
            print(f"Error synchronizing sprite positions: {e}")

    def _sync_node_sprite_position(self, node):
        """Recursively synchronize sprite positions for a node and its children"""
        try:
            # Update this node's sprite if it has one
            if hasattr(node, 'sprite_data') and node.sprite_data:
                # Get the node's current position (handle both Vector2 and list/tuple)
                if hasattr(node, 'position'):
                    if hasattr(node.position, 'x'):  # Vector2 object
                        new_x, new_y = node.position.x, node.position.y
                    elif isinstance(node.position, (list, tuple)) and len(node.position) >= 2:
                        new_x, new_y = node.position[0], node.position[1]
                    else:
                        return  # Invalid position format

                    # Only update if position has changed significantly (to avoid unnecessary updates)
                    old_pos = node.sprite_data['position']
                    if (abs(old_pos[0] - new_x) > 1.0 or abs(old_pos[1] - new_y) > 1.0):

                        # Don't sync if the node position is very close to zero (likely being reset)
                        # and the sprite is not at zero (likely moved by script)
                        if (abs(new_x) < 0.1 and abs(new_y) < 0.1 and
                            (abs(old_pos[0]) > 1.0 or abs(old_pos[1]) > 1.0)):
                            # Skip this sync - the node position is being reset but sprite has moved
                            print(f"SYNC: Skipping reset for {node.name} - sprite at {old_pos}, node at ({new_x}, {new_y})")
                            return

                        node.sprite_data['position'] = [new_x, new_y]

                        # Debug output for position changes
                        print(f"SYNC: Updated sprite {node.name} from {old_pos} to ({new_x}, {new_y})")

            # Recursively update children
            if hasattr(node, 'children'):
                for child in node.children:
                    self._sync_node_sprite_position(child)

        except Exception as e:
            print(f"Error syncing sprite position for node {getattr(node, 'name', 'unknown')}: {e}")

    def debug_force_player_sprite_update(self):
        """DEBUG: Force update PlayerController sprite position to test visual movement"""
        try:
            if not self.scene:
                return

            # Find the PlayerController node
            player_node = None
            for root_node in self.scene.root_nodes:
                player_node = self._find_node_by_name(root_node, "PlayerController")
                if player_node:
                    break

            if not player_node:
                return

            # Check if PlayerController has runtime position
            if hasattr(player_node, '_runtime_position'):
                runtime_pos = player_node._runtime_position

                # Update PlayerController's own sprite if it exists
                if hasattr(player_node, 'sprite_data') and player_node.sprite_data:
                    old_pos = player_node.sprite_data['position']
                    player_node.sprite_data['position'] = [runtime_pos.x, runtime_pos.y]
                    print(f"DEBUG FORCE: Updated PlayerController sprite from {old_pos} to ({runtime_pos.x}, {runtime_pos.y})")

                # Also update all child sprites
                if hasattr(player_node, 'children'):
                    for child in player_node.children:
                        if hasattr(child, 'sprite_data') and child.sprite_data:
                            old_pos = child.sprite_data['position']
                            child.sprite_data['position'] = [runtime_pos.x, runtime_pos.y]
                            print(f"DEBUG FORCE: Updated child {child.name} sprite from {old_pos} to ({runtime_pos.x}, {runtime_pos.y})")

                # Also check all sprites
                for sprite_data in self.sprites:
                    if 'lupine_node' in sprite_data:
                        node = sprite_data['lupine_node']
                        if hasattr(node, 'name') and node.name == "PlayerController":
                            old_pos = sprite_data['position']
                            sprite_data['position'] = [runtime_pos.x, runtime_pos.y]
                            print(f"DEBUG FORCE: Updated sprite PlayerController from {old_pos} to ({runtime_pos.x}, {runtime_pos.y})")
                        elif hasattr(node, 'parent') and hasattr(node.parent, 'name') and node.parent.name == "PlayerController":
                            old_pos = sprite_data['position']
                            sprite_data['position'] = [runtime_pos.x, runtime_pos.y]
                            print(f"DEBUG FORCE: Updated sprite child {node.name} from {old_pos} to ({runtime_pos.x}, {runtime_pos.y})")

        except Exception as e:
            print(f"Error in debug_force_player_sprite_update: {e}")

    def _find_node_by_name(self, node, name):
        """Recursively find a node by name"""
        if hasattr(node, 'name') and node.name == name:
            return node

        if hasattr(node, 'children'):
            for child in node.children:
                result = self._find_node_by_name(child, name)
                if result:
                    return result

        return None

    def update_node_scripts(self, node, delta_time):
        """Update scripts attached to nodes"""
        try:
            # Call script update methods if the node has a script
            if hasattr(node, 'script_instance') and node.script_instance is not None:
                # Call _process method (Godot-style update method)
                if hasattr(node.script_instance, 'has_method') and node.script_instance.has_method('_process'):
                    node.script_instance.call_method('_process', delta_time)
                elif hasattr(node.script_instance, 'has_method') and node.script_instance.has_method('process'):
                    node.script_instance.call_method('process', delta_time)

                # Call _physics_process method (Godot-style physics update method)
                if hasattr(node.script_instance, 'has_method') and node.script_instance.has_method('_physics_process'):
                    node.script_instance.call_method('_physics_process', delta_time)
                elif hasattr(node.script_instance, 'has_method') and node.script_instance.has_method('physics_process'):
                    node.script_instance.call_method('physics_process', delta_time)

                # Also call on_update for compatibility
                if hasattr(node.script_instance, 'has_method') and node.script_instance.has_method('on_update'):
                    node.script_instance.call_method('on_update', delta_time)

        except Exception as e:
            print(f"Error updating script for {node.name}: {e}")
            import traceback
            traceback.print_exc()

        # Update children
        if hasattr(node, 'children'):
            for child in node.children:
                self.update_node_scripts(child, delta_time)



    def on_key_press(self, key, modifiers):
        """Handle key press events"""
        if key == pygame.K_ESCAPE:
            self.running = False

        # Debug: Show key press
        print(f"Key pressed: {key} (A={pygame.K_a}, LEFT={pygame.K_LEFT})")

        # Update input state
        self.pressed_keys.add(key)
        self._update_modifiers(modifiers)

        # Update input manager
        if self.input_manager:
            self.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

            # Debug: Check if actions are triggered
            if self.input_manager.is_action_pressed("move_left"):
                print("move_left action is now active!")
            if self.input_manager.is_action_pressed("ui_left"):
                print("ui_left action is now active!")

        # Forward input to LSC runtime for script handling
        if self.lsc_runtime and self.scene:
            for root_node in self.scene.root_nodes:
                self.handle_node_input(root_node, 'on_key_press', key, modifiers)

    def on_key_release(self, key, modifiers):
        """Handle key release events"""
        self.pressed_keys.discard(key)
        self._update_modifiers(modifiers)

        # Update input manager
        if self.input_manager:
            self.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

        # Forward input to LSC runtime
        if self.lsc_runtime and self.scene:
            for root_node in self.scene.root_nodes:
                self.handle_node_input(root_node, 'on_key_release', key, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse press events"""
        # Update mouse state
        self.mouse_buttons.add(button)
        self.mouse_position = (x, y)
        self._update_modifiers(modifiers)

        # Update input manager
        if self.input_manager:
            self.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

        # Forward to UI nodes for button interactions
        if self.scene:
            for root_node in self.scene.root_nodes:
                self.handle_mouse_event(root_node, 'on_mouse_press', x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        """Handle mouse release events"""
        # Update mouse state
        self.mouse_buttons.discard(button)
        self.mouse_position = (x, y)
        self._update_modifiers(modifiers)

        # Update input manager
        if self.input_manager:
            self.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

        # Forward to UI nodes for button interactions
        if self.scene:
            for root_node in self.scene.root_nodes:
                self.handle_mouse_event(root_node, 'on_mouse_release', x, y, button, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        """Handle mouse motion events"""
        # Update mouse position
        self.mouse_position = (x, y)

        # Update input manager
        if self.input_manager:
            self.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

        # Update hover states for UI nodes
        if self.scene:
            for root_node in self.scene.root_nodes:
                self.update_mouse_hover(root_node, x, y)

    def handle_mouse_event(self, node, method_name, x, y, button, modifiers):
        """Handle mouse events for nodes"""
        try:
            # Check if this is a UI node that can handle mouse events
            if hasattr(node, 'type') and node.type in ['Button', 'Panel', 'Label']:
                # Convert screen coordinates to UI coordinates
                ui_x, ui_y = self.screen_to_ui_coordinates(x, y)

                # Check if mouse is over this UI node
                if self.is_point_in_ui_node(node, ui_x, ui_y):
                    if hasattr(node, 'script_instance') and node.script_instance is not None:
                        # Call the mouse event method
                        if hasattr(node.script_instance, 'call_method'):
                            node.script_instance.call_method(method_name, button, [ui_x, ui_y])

                        # For buttons, also update internal state
                        if node.type == 'Button':
                            if method_name == 'on_mouse_press':
                                node._is_mouse_pressed = True
                            elif method_name == 'on_mouse_release':
                                node._is_mouse_pressed = False
        except Exception as e:
            print(f"Error handling mouse event for {node.name}: {e}")

        # Handle mouse events for children
        if hasattr(node, 'children'):
            for child in node.children:
                self.handle_mouse_event(child, method_name, x, y, button, modifiers)

    def update_mouse_hover(self, node, x, y):
        """Update hover state for UI nodes"""
        try:
            if hasattr(node, 'type') and node.type in ['Button', 'Panel', 'Label']:
                # Convert screen coordinates to UI coordinates
                ui_x, ui_y = self.screen_to_ui_coordinates(x, y)

                # Check if mouse is over this UI node
                was_hovered = getattr(node, '_is_hovered', False)
                is_hovered = self.is_point_in_ui_node(node, ui_x, ui_y)

                if is_hovered != was_hovered:
                    node._is_hovered = is_hovered

                    # Call hover events if node has script
                    if hasattr(node, 'script_instance') and node.script_instance is not None:
                        if hasattr(node.script_instance, 'call_method'):
                            if is_hovered:
                                node.script_instance.call_method('mouse_entered')
                            else:
                                node.script_instance.call_method('mouse_exited')
        except Exception as e:
            print(f"Error updating hover for {node.name}: {e}")

        # Update hover for children
        if hasattr(node, 'children'):
            for child in node.children:
                self.update_mouse_hover(child, x, y)

    def screen_to_ui_coordinates(self, screen_x, screen_y):
        """Convert screen coordinates to UI coordinates"""
        # UI coordinates are relative to the game area
        game_area = getattr(self, 'game_area', {"width": self.width, "height": self.height, "offset_x": 0, "offset_y": 0})

        # Adjust for game area offset
        ui_x = screen_x - game_area['offset_x']
        ui_y = screen_y - game_area['offset_y']

        # Convert to UI coordinate system (0,0 at top-left of game area)
        return ui_x, ui_y

    def is_point_in_ui_node(self, node, ui_x, ui_y):
        """Check if a point is inside a UI node's bounds"""
        try:
            position = getattr(node, 'position', [0, 0])
            rect_size = getattr(node, 'rect_size', [100, 30])

            # UI nodes use position as top-left corner
            left = position[0]
            right = position[0] + rect_size[0]
            top = position[1]
            bottom = position[1] + rect_size[1]

            return left <= ui_x <= right and top <= ui_y <= bottom
        except Exception as e:
            print(f"Error checking point in UI node: {e}")
            return False

    def handle_node_input(self, node, method_name, *args):
        """Handle input events for node scripts"""
        try:
            if hasattr(node, 'script_instance') and node.script_instance is not None:
                if hasattr(node.script_instance, 'call_method'):
                    node.script_instance.call_method(method_name, *args)
        except Exception as e:
            print(f"Error handling input for {node.name}: {e}")

        # Handle input for children
        if hasattr(node, 'children'):
            for child in node.children:
                self.handle_node_input(child, method_name, *args)

    def _update_modifiers(self, modifiers):
        """Update current modifier keys state"""
        self.current_modifiers.clear()

        # Convert pygame modifiers to string set
        if modifiers & pygame.KMOD_SHIFT:
            self.current_modifiers.add("shift")
        if modifiers & pygame.KMOD_CTRL:
            self.current_modifiers.add("ctrl")
        if modifiers & pygame.KMOD_ALT:
            self.current_modifiers.add("alt")
        if modifiers & pygame.KMOD_META:  # Meta/Cmd key
            self.current_modifiers.add("meta")

    def is_key_pressed(self, key):
        """Check if a key is currently pressed (for script access)"""
        return key in self.pressed_keys

    # Input action methods for LSC scripts
    def is_action_pressed(self, action_name):
        """Check if an action is currently pressed"""
        if self.input_manager:
            result = self.input_manager.is_action_pressed(action_name)
            # Debug output for troubleshooting
            if result and action_name in ["move_left", "move_right", "move_up", "move_down", "ui_left", "ui_right", "ui_up", "ui_down"]:
                print(f"Action '{action_name}' is pressed! Keys: {self.pressed_keys}")
            return result
        else:
            print("Warning: Input manager not available")
            return False

    def is_action_just_pressed(self, action_name):
        """Check if an action was just pressed this frame"""
        if self.input_manager:
            return self.input_manager.is_action_just_pressed(action_name)
        return False

    def is_action_just_released(self, action_name):
        """Check if an action was just released this frame"""
        if self.input_manager:
            return self.input_manager.is_action_just_released(action_name)
        return False

    def get_action_strength(self, action_name):
        """Get the strength of an action (0.0 to 1.0)"""
        if self.input_manager:
            return self.input_manager.get_action_strength(action_name)
        return 0.0

    def is_mouse_button_pressed(self, button):
        """Check if a mouse button is currently pressed"""
        if self.input_manager:
            return self.input_manager.is_mouse_button_pressed(button)
        return False

    def get_mouse_position(self):
        """Get current mouse position"""
        if self.input_manager:
            return self.input_manager.get_mouse_position()
        return (0, 0)

    def get_global_mouse_position(self):
        """Get global mouse position"""
        if self.input_manager:
            return self.input_manager.get_global_mouse_position()
        return (0, 0)

    # Game runtime methods for LSC scripts
    def change_scene(self, scene_path):
        """Change to a different scene"""
        try:
            print(f"Changing scene to: {scene_path}")
            # This would be implemented to actually change scenes
            # For now, just log the request
        except Exception as e:
            print(f"Error changing scene: {e}")

    def reload_scene(self):
        """Reload the current scene"""
        try:
            print("Reloading current scene")
            self.load_scene()
        except Exception as e:
            print(f"Error reloading scene: {e}")

    def get_scene(self):
        """Get the current scene"""
        return self.scene

    def get_node(self, name):
        """Get a node by name"""
        if self.scene:
            for root_node in self.scene.root_nodes:
                result = self.find_node_by_name(root_node, name)
                if result:
                    return result
        return None

    def find_node_by_name(self, node, name):
        """Recursively find a node by name"""
        if isinstance(node, str):
            # If called with just a name, search from root
            if self.scene:
                for root_node in self.scene.root_nodes:
                    result = self.find_node_by_name(root_node, node)
                    if result:
                        return result
            return None

        if node.name == name:
            return node
        for child in node.children:
            result = self.find_node_by_name(child, name)
            if result:
                return result
        return None

    def find_node(self, name):
        """Find node by name (alias for LSC compatibility)"""
        return self.find_node_by_name(name)

    def get_tree(self):
        """Get the scene tree (for LSC compatibility)"""
        return self.scene

    def create_sprite(self, texture_path, x=0, y=0):
        """Create a new sprite at runtime"""
        try:
            full_path = Path(self.project_path) / texture_path
            if full_path.exists():
                sprite_data = {
                    'texture_path': texture_path,
                    'position': [x, y],
                    'size': [64, 64],  # Default size
                    'rotation': 0,
                    'alpha': 1.0
                }
                self.sprites.append(sprite_data)
                return sprite_data
        except Exception as e:
            print(f"Error creating sprite: {e}")
        return None

def main():
    try:
        game = LupineGameWindow(r"{project_path}")
        game.setup()
        game.run()
    except Exception as e:
        print(f"Game error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''

        # Format the template with actual values using string replacement
        runner_content = template.replace("{lupine_engine_path}", lupine_engine_path)
        runner_content = runner_content.replace("{project_path}", project_path)
        runner_content = runner_content.replace("{scene_file_path}", scene_file_path)

        # Write to temporary file
        runner_path = self.project.project_path / "temp_runner.py"
        with open(runner_path, 'w') as f:
            f.write(runner_content)
        
        return str(runner_path)
    
    def read_stdout(self):
        """Read stdout from process"""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self.output_received.emit(data)
    
    def read_stderr(self):
        """Read stderr from process"""
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self.error_received.emit(data)
    
    def on_finished(self, exit_code):
        """Handle process finished"""
        self.finished.emit(exit_code)
    
    def stop(self):
        """Stop the game process"""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()


class GameRunnerWidget(QWidget):
    """Widget for running and monitoring games"""
    
    def __init__(self, project: LupineProject):
        super().__init__()
        self.project = project
        self.current_process = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Control bar
        controls_layout = QHBoxLayout()
        
        self.run_scene_btn = QPushButton("Run Current Scene")
        self.run_scene_btn.clicked.connect(self.run_current_scene)
        controls_layout.addWidget(self.run_scene_btn)
        
        self.run_main_btn = QPushButton("Run Main Scene")
        self.run_main_btn.clicked.connect(self.run_main_scene)
        controls_layout.addWidget(self.run_main_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_game)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #b0b0b0;")
        controls_layout.addWidget(self.status_label)
        
        layout.addLayout(controls_layout)
        
        # Splitter for game view and output
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Game preview area (placeholder)
        self.game_preview = QFrame()
        self.game_preview.setMinimumHeight(200)
        self.game_preview.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                border-radius: 4px;
            }
        """)
        
        preview_layout = QVBoxLayout(self.game_preview)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        preview_label = QLabel("Game Preview")
        preview_label.setStyleSheet("color: #b0b0b0; font-size: 14px;")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_label)
        
        preview_info = QLabel("Game will run in a separate window")
        preview_info.setStyleSheet("color: #808080; font-size: 10px;")
        preview_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_info)
        
        splitter.addWidget(self.game_preview)
        
        # Output area
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.setContentsMargins(0, 0, 0, 0)
        
        output_label = QLabel("Game Output")
        output_label.setStyleSheet("font-weight: bold; color: #e0e0e0;")
        output_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setMaximumHeight(150)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #555555;
            }
        """)
        output_layout.addWidget(self.output_text)
        
        splitter.addWidget(output_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 150])
        
        layout.addWidget(splitter)
    
    def run_scene(self, scene_path: str):
        """Run a specific scene"""
        if self.current_process and self.current_process.isRunning():
            self.stop_game()
        
        self.status_label.setText(f"Running: {scene_path}")
        self.output_text.clear()
        self.log_output(f"Starting scene: {scene_path}")
        
        # Start game process
        self.current_process = GameProcess(self.project, scene_path)
        self.current_process.output_received.connect(self.log_output)
        self.current_process.error_received.connect(self.log_error)
        self.current_process.finished.connect(self.on_game_finished)
        
        self.current_process.start()
        
        # Update UI
        self.run_scene_btn.setEnabled(False)
        self.run_main_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def run_current_scene(self):
        """Run the current scene"""
        # Get current scene from parent editor
        parent = self.parent()
        while parent and not hasattr(parent, 'current_scene'):
            parent = parent.parent()

        if parent and hasattr(parent, 'current_scene') and parent.current_scene:
            self.run_scene(parent.current_scene)
        else:
            self.log_error("No scene is currently open!")
    
    def run_main_scene(self):
        """Run the main scene"""
        main_scene = self.project.get_main_scene()
        if main_scene:
            self.run_scene(main_scene)
        else:
            self.log_error("No main scene set for this project")
    
    def stop_game(self):
        """Stop the running game"""
        if self.current_process:
            self.current_process.stop()
            self.current_process.wait(3000)  # Wait up to 3 seconds
            
            if self.current_process.isRunning():
                self.current_process.terminate()
        
        self.on_game_finished(0)
    
    def on_game_finished(self, exit_code: int):
        """Handle game process finished"""
        self.status_label.setText("Ready")
        
        if exit_code == 0:
            self.log_output("Game finished successfully")
        else:
            self.log_error(f"Game finished with exit code: {exit_code}")
        
        # Update UI
        self.run_scene_btn.setEnabled(True)
        self.run_main_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Clean up temporary files
        temp_runner = self.project.project_path / "temp_runner.py"
        if temp_runner.exists():
            try:
                temp_runner.unlink()
            except:
                pass
    
    def log_output(self, message: str):
        """Log output message"""
        self.output_text.append(f"[INFO] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def log_error(self, message: str):
        """Log error message"""
        self.output_text.append(f"[ERROR] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
