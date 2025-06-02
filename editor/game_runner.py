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

import arcade
import json
from pathlib import Path

# Import input constants at module level
try:
    from core.input_constants import *
    INPUT_CONSTANTS_AVAILABLE = True
except ImportError as e:
    print(f"Input constants not available: {e}")
    INPUT_CONSTANTS_AVAILABLE = False

# Import LSC runtime for script execution
try:
    from core.lsc import LSCRuntime, LSCInterpreter
    from core.lsc.interpreter import execute_lsc_script
    from core.scene import Scene, Node, Node2D, Sprite, Camera2D
    LSC_AVAILABLE = True
except ImportError as e:
    print(f"LSC not available: {e}")
    LSC_AVAILABLE = False

class LupineGameWindow(arcade.Window):
    def __init__(self, project_path: str):
        print("DEBUG: LupineGameWindow.__init__() called")
        super().__init__(1280, 720, "Lupine Engine - Game Runner", resizable=True)  # 16:9 aspect ratio, smaller and resizable
        print("DEBUG: Arcade window initialized")
        self.project_path = project_path  # Store project path for texture loading
        self.scene = None
        self.scene_data = None
        self.camera = None
        self.sprite_lists = {}
        self.textures = {}
        self.text_objects = {}  # Cache for text objects to improve performance

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

        # LSC Runtime for script execution
        if LSC_AVAILABLE:
            self.lsc_runtime = LSCRuntime(game_runtime=self)
            # Add game runtime methods to LSC scope
            self.setup_lsc_builtins()
        else:
            self.lsc_runtime = None

        print("DEBUG: About to call load_scene()")
        self.load_scene()
        print("DEBUG: load_scene() completed")

    def setup_lsc_builtins(self):
        """Setup additional built-in functions for LSC scripts"""
        if not self.lsc_runtime:
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
            "get_delta_time": lambda: self.lsc_runtime.delta_time if self.lsc_runtime else 0.0,
            "get_runtime_time": lambda: self.lsc_runtime.get_runtime_time() if self.lsc_runtime else 0.0,
            "get_fps": lambda: 1.0 / self.lsc_runtime.delta_time if self.lsc_runtime and self.lsc_runtime.delta_time > 0 else 0.0,

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
            self.lsc_runtime.global_scope.define(name, func)

    def get_text_object(self, text, font_size=12, color=arcade.color.WHITE):
        """Get or create a cached text object for better performance"""
        key = f"{text}_{font_size}_{color}"
        if key not in self.text_objects:
            self.text_objects[key] = arcade.Text(
                text=text,
                x=0,
                y=0,
                color=color,
                font_size=font_size
            )
        return self.text_objects[key]

    def draw_cached_text(self, text, x, y, color=arcade.color.WHITE, font_size=12):
        """Draw text using cached Text objects for better performance"""
        try:
            # Create a cache key
            cache_key = f"{text}_{font_size}_{color}"

            # Check if we have a cached text object
            if cache_key not in self.text_objects:
                # Create new Text object with correct parameters for arcade 3.2.0
                self.text_objects[cache_key] = arcade.Text(
                    text=str(text),
                    x=0,
                    y=0,
                    color=color,
                    font_size=font_size
                )

            # Update position and draw
            text_obj = self.text_objects[cache_key]
            text_obj.x = x
            text_obj.y = y
            text_obj.draw()

        except Exception as e:
            print(f"Error drawing text '{text}': {e}")
            # Fallback to basic draw_text
            try:
                arcade.draw_text(str(text), float(x), float(y), arcade.color.WHITE, 12)
            except Exception as e2:
                print(f"Text drawing fallback also failed: {e2}")

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
            if LSC_AVAILABLE:
                print("LSC is available, attempting to load Scene object...")
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
                print("LSC not available, using basic scene rendering")

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
        """Setup the scene with proper sprite lists and cameras"""
        # Create sprite lists for different node types
        self.sprite_lists = {
            "sprites": arcade.SpriteList(),
            "ui": arcade.SpriteList()
        }

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
            self.camera = arcade.Camera2D()
            # Use world coordinates directly - no screen offset conversion
            self.camera.position = (node.position[0], node.position[1])
            if hasattr(node, 'zoom'):
                self.camera.zoom = node.zoom[0] if isinstance(node.zoom, list) else node.zoom
            print(f"Found active camera: {node.name} at {node.position}")
        elif isinstance(node, dict) and node.get("type") == "Camera2D" and node.get("current", False):
            # Scene data dictionary case
            self.camera = arcade.Camera2D()
            position = node.get("position", [0.0, 0.0])
            zoom = node.get("zoom", [1.0, 1.0])
            offset = node.get("offset", [0.0, 0.0])

            # Arcade Camera2D position is the center of the view in world coordinates
            # Apply camera offset - no Y inversion needed as Arcade uses same coordinate system
            camera_x = position[0] + offset[0]
            camera_y = position[1] + offset[1]

            self.camera.position = (camera_x, camera_y)
            self.camera.zoom = zoom[0] if isinstance(zoom, list) else zoom  # Use X zoom for uniform scaling
            print(f"Found active camera: {node.get('name', 'Camera2D')} at world {position}, arcade {(camera_x, camera_y)} with zoom {zoom}")

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
                if self.lsc_runtime:
                    script_file = Path(r"{project_path}") / node.script_path
                    print(f"Looking for script file: {script_file}")
                    if script_file.exists():
                        print(f"Script file exists, loading...")
                        with open(script_file, 'r') as f:
                            script_content = f.read()

                        # Create script instance for this node
                        from core.lsc.runtime import LSCScriptInstance
                        script_instance = LSCScriptInstance(node, node.script_path, self.lsc_runtime)

                        # Execute the script in the script instance's scope
                        old_scope = self.lsc_runtime.current_scope
                        self.lsc_runtime.current_scope = script_instance.scope

                        try:
                            # Add node reference to script scope
                            script_instance.scope.define('self', node)
                            script_instance.scope.define('node', node)

                            # Expose common node properties directly to scope
                            # Note: Don't expose position directly as it can cause reference issues
                            # Scripts should use self.position or node.position instead

                            # Execute script
                            execute_lsc_script(script_content, self.lsc_runtime)

                            # Attach script instance to node
                            node.script_instance = script_instance

                            # Call on_ready if it exists
                            if script_instance.scope.has('on_ready'):
                                print(f"Calling on_ready for {node.name}")
                                script_instance.call_method('on_ready')
                                script_instance.ready_called = True
                            else:
                                print(f"No on_ready method found for {node.name}")

                            print(f"SUCCESS: Loaded script for {node.name}: {node.script_path}")

                        except Exception as e:
                            print(f"Error loading script for {node.name}: {e}")
                            # Don't crash the entire game - continue with other nodes
                            # Create a minimal script instance so the node still works
                            node.script_instance = script_instance
                        finally:
                            # Restore scope
                            self.lsc_runtime.current_scope = old_scope
                    else:
                        print(f"Script file not found: {script_file}")
                else:
                    print(f"LSC runtime not available for {node.name}")
            else:
                print(f"Node {node.name} has no script_path")

            # Setup sprite nodes (including AnimatedSprite)
            if isinstance(node, Sprite):
                self.setup_sprite_node(node)

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
        """Setup a sprite node with proper texture loading"""
        try:
            texture_path = getattr(sprite_node, 'texture', None)
            if texture_path:
                # Load texture if not already loaded
                full_texture_path = Path(self.project_path) / texture_path
                if full_texture_path.exists():
                    texture_key = str(full_texture_path)
                    if texture_key not in self.textures:
                        self.textures[texture_key] = arcade.load_texture(str(full_texture_path))
                        print(f"Loaded texture: {full_texture_path}")

                    # Create arcade sprite with proper properties
                    if texture_key in self.textures:
                        arcade_sprite = arcade.Sprite()
                        # Each sprite gets its own texture reference to avoid sharing issues
                        arcade_sprite.texture = self.textures[texture_key]

                        # Set position using world coordinates directly
                        arcade_sprite.center_x = sprite_node.position[0]
                        arcade_sprite.center_y = sprite_node.position[1]

                        # Set rotation and scale
                        arcade_sprite.angle = getattr(sprite_node, 'rotation', 0)
                        scale = getattr(sprite_node, 'scale', [1.0, 1.0])
                        arcade_sprite.scale = scale[0] if isinstance(scale, list) else scale

                        # Set modulation/color if available
                        modulate = getattr(sprite_node, 'modulate', [1.0, 1.0, 1.0, 1.0])
                        if len(modulate) >= 3:
                            # Convert to 0-255 range
                            arcade_sprite.color = (
                                int(modulate[0] * 255),
                                int(modulate[1] * 255),
                                int(modulate[2] * 255)
                            )

                        # Set alpha if available
                        if len(modulate) >= 4:
                            arcade_sprite.alpha = int(modulate[3] * 255)

                        # Store reference to original node for updates
                        arcade_sprite.lupine_node = sprite_node
                        sprite_node.arcade_sprite = arcade_sprite

                        self.sprite_lists["sprites"].append(arcade_sprite)
                        print(f"Created arcade sprite for {sprite_node.name} with texture {texture_path} at world ({sprite_node.position[0]}, {sprite_node.position[1]})")
                else:
                    print(f"Texture file not found: {full_texture_path}")
            else:
                # Create a placeholder sprite without texture
                arcade_sprite = arcade.Sprite()
                arcade_sprite.center_x = sprite_node.position[0]
                arcade_sprite.center_y = sprite_node.position[1]
                # Create a unique placeholder texture for each sprite
                placeholder_name = f"placeholder_{sprite_node.name}_{id(sprite_node)}"
                arcade_sprite.texture = arcade.Texture.create_empty(placeholder_name, (64, 64))

                # Store reference to original node for updates
                arcade_sprite.lupine_node = sprite_node
                sprite_node.arcade_sprite = arcade_sprite

                self.sprite_lists["sprites"].append(arcade_sprite)
                print(f"Created placeholder sprite for {sprite_node.name} (no texture)")

        except Exception as e:
            print(f"Error setting up sprite {sprite_node.name}: {e}")
            import traceback
            traceback.print_exc()

    def setup(self):
        arcade.set_background_color(arcade.color.DARK_GRAY)

        # Set proper OpenGL blend mode to avoid white film
        self.ctx.enable(self.ctx.BLEND)
        self.ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA

        # Initialize camera viewport if camera exists
        if self.camera:
            # Use Arcade's match_window method for proper camera setup
            self.camera.match_window(viewport=True, projection=True, scissor=True, position=False)
            print(f"Camera initialized with viewport: {self.camera.viewport}, position: {self.camera.position}")

        print("Game setup complete")
        print("ESC to exit")

    def on_draw(self):
        self.clear()

        # Set proper blend mode for rendering
        self.ctx.enable(self.ctx.BLEND)
        self.ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA

        # Use camera if available
        if self.camera:
            self.camera.use()
            # Debug: Print camera info occasionally
            if hasattr(self, '_debug_counter'):
                self._debug_counter += 1
            else:
                self._debug_counter = 0

            if self._debug_counter % 60 == 0:  # Print every 60 frames (1 second at 60fps)
                print(f"Camera position: {self.camera.position}, viewport: {self.camera.viewport}")

        # Draw sprite lists (proper game objects with textures)
        for sprite_list in self.sprite_lists.values():
            sprite_list.draw()

        # Draw scene nodes (fallback for basic rendering with texture support)
        if self.scene_data:
            nodes = self.scene_data.get("nodes", [])
            for node in nodes:
                self.draw_node_fallback(node)

        # Draw UI overlay (always drawn without camera)
        if self.camera:
            # Reset to default camera for UI
            if hasattr(self.ctx, 'default_camera'):
                self.ctx.default_camera.use()
            elif hasattr(self.ctx, '_default_camera'):
                self.ctx._default_camera.use()
            else:
                # Fallback - create a new camera for UI
                ui_camera = arcade.Camera2D()
                ui_camera.match_window()
                ui_camera.use()

        self.draw_ui()

    def calculate_ui_position(self, position, rect_size=None):
        """Calculate UI position relative to game viewport with support for percentage positioning"""
        game_area = getattr(self, 'game_area', {"width": self.width, "height": self.height, "offset_x": 0, "offset_y": 0})

        # Support for percentage-based positioning (0.0-1.0 range)
        # If position values are between 0 and 1, treat as percentages
        x_pos = position[0]
        y_pos = position[1]

        # Convert percentage to absolute position
        if 0.0 <= x_pos <= 1.0:
            x_pos = x_pos * game_area['width']
        if 0.0 <= y_pos <= 1.0:
            y_pos = y_pos * game_area['height']

        # Calculate final screen position
        ui_x = game_area['offset_x'] + x_pos
        ui_y = game_area['offset_y'] + y_pos

        return ui_x, ui_y

    def calculate_ui_size(self, rect_size, base_size=None):
        """Calculate UI size with support for percentage-based sizing"""
        game_area = getattr(self, 'game_area', {"width": self.width, "height": self.height, "offset_x": 0, "offset_y": 0})

        width = rect_size[0]
        height = rect_size[1]

        # Support percentage-based sizing (0.0-1.0 range)
        if 0.0 <= width <= 1.0:
            width = width * game_area['width']
        if 0.0 <= height <= 1.0:
            height = height * game_area['height']

        return width, height

    def draw_node_fallback(self, node_data):
        """Fallback node rendering with proper texture support"""
        position = node_data.get("position", [0, 0])
        node_type = node_data.get("type", "Node")

        # Use world coordinates directly
        x = position[0]
        y = position[1]

        if node_type == "Node2D":
            # Node2D nodes are invisible containers - no rendering needed
            pass
        elif node_type == "Sprite":
            self.draw_sprite_fallback(node_data, x, y)
        elif node_type == "AnimatedSprite":
            self.draw_animated_sprite_fallback(node_data, x, y)
        elif node_type == "Camera2D":
            # Camera2D nodes are invisible in game - no rendering needed
            pass
        elif node_type == "Area2D":
            # Area2D nodes are invisible in game - no rendering needed
            pass
        elif node_type == "CollisionShape2D":
            self.draw_collision_shape_fallback(node_data, x, y)
        elif node_type == "CollisionPolygon2D":
            self.draw_collision_polygon_fallback(node_data, x, y)
        elif node_type == "RigidBody2D" or node_type == "StaticBody2D" or node_type == "KinematicBody2D":
            # Physics bodies are invisible containers - no rendering needed
            pass
        elif node_type == "Control":
            self.draw_control_fallback(node_data, x, y)
        elif node_type == "Panel":
            self.draw_panel_fallback(node_data, x, y)
        elif node_type == "Label":
            self.draw_label_fallback(node_data, x, y)
        elif node_type == "Button":
            self.draw_button_fallback(node_data, x, y)
        elif node_type == "CanvasLayer":
            self.draw_canvas_layer_fallback(node_data, x, y)

        # Draw children
        for child in node_data.get("children", []):
            self.draw_node_fallback(child)

    def draw_sprite_fallback(self, node_data, x, y):
        """Draw sprite with actual texture if available"""
        texture_path = node_data.get("texture", "")
        size = node_data.get("size", [64, 64])

        # Try to load and draw the actual texture
        if texture_path:
            try:
                # Load texture if not already loaded
                full_path = Path(r"{project_path}") / texture_path
                if full_path.exists():
                    if str(full_path) not in self.textures:
                        self.textures[str(full_path)] = arcade.load_texture(str(full_path))
                        print(f"Loaded fallback texture: {full_path}")

                    # Draw the texture
                    if str(full_path) in self.textures:
                        texture = self.textures[str(full_path)]

                        # Get actual texture size
                        tex_width = texture.width
                        tex_height = texture.height

                        # Use texture size or specified size
                        draw_width = size[0] if size != [64, 64] else tex_width
                        draw_height = size[1] if size != [64, 64] else tex_height

                        # Draw texture using arcade's correct function
                        try:
                            # Create rectangle for texture drawing (centered on x, y)
                            rect = arcade.LBWH(x - draw_width//2, y - draw_height//2, draw_width, draw_height)
                            # Use the correct arcade.draw_texture_rect function
                            arcade.draw_texture_rect(texture, rect)
                        except Exception as e:
                            print(f"Error drawing texture: {e}")
                            # Fallback - draw a colored rectangle instead
                            arcade.draw_lbwh_rectangle_filled(x - draw_width//2, y - draw_height//2, draw_width, draw_height, arcade.color.BLUE)
                        return

            except Exception as e:
                print(f"Error loading texture {texture_path}: {e}")

        # Fallback to colored rectangle if no texture
        arcade.draw_lbwh_rectangle_filled(x - size[0]//2, y - size[1]//2, size[0], size[1], arcade.color.GREEN)

    def draw_animated_sprite_fallback(self, node_data, x, y):
        """Draw AnimatedSprite with animation indicators"""
        # First draw as a regular sprite
        self.draw_sprite_fallback(node_data, x, y)

        # Add animation indicators
        playing = node_data.get("playing", False)
        anim_name = node_data.get("animation", "default")

        # Draw animation status indicator
        if playing:
            # Draw play triangle (green)
            arcade.draw_triangle_filled(x - 40, y - 8, x - 40, y + 8, x - 32, y, arcade.color.GREEN)
        else:
            # Draw pause bars (yellow)
            arcade.draw_lbwh_rectangle_filled(x - 42, y - 8, 3, 16, arcade.color.YELLOW)
            arcade.draw_lbwh_rectangle_filled(x - 37, y - 8, 3, 16, arcade.color.YELLOW)

        # Draw animation name (simplified)
        self.draw_cached_text(f"Anim: {anim_name}", x - 60, y - 20, arcade.color.CYAN, 10)

    def draw_control_fallback(self, node_data, x, y):
        """Draw Control node (base UI node)"""
        # Get control properties - Controls use position (UI coordinate system)
        position = node_data.get("position", [0.0, 0.0])
        rect_size = node_data.get("rect_size", [100.0, 100.0])

        # Calculate UI position and size with percentage support
        ui_x, ui_y = self.calculate_ui_position(position, rect_size)
        ui_width, ui_height = self.calculate_ui_size(rect_size)

        # Control nodes are typically invisible containers - no rendering needed
        # But we store the calculated position for child elements if needed

    def draw_panel_fallback(self, node_data, x, y):
        """Draw Panel node"""
        # Get panel properties - Panels use position (UI coordinate system)
        position = node_data.get("position", [0.0, 0.0])
        rect_size = node_data.get("rect_size", [100.0, 100.0])
        panel_color = node_data.get("panel_color", [0.2, 0.2, 0.2, 1.0])
        border_width = node_data.get("border_width", 0.0)
        border_color = node_data.get("border_color", [0.0, 0.0, 0.0, 1.0])

        # Calculate UI position and size with percentage support
        ui_x, ui_y = self.calculate_ui_position(position, rect_size)
        ui_width, ui_height = self.calculate_ui_size(rect_size)

        # Convert colors to arcade format (0-255)
        panel_arcade_color = (
            int(panel_color[0] * 255),
            int(panel_color[1] * 255),
            int(panel_color[2] * 255),
            int(panel_color[3] * 255)
        )

        # Draw panel background
        arcade.draw_lbwh_rectangle_filled(
            ui_x, ui_y, ui_width, ui_height,
            panel_arcade_color
        )

        # Draw border if enabled
        if border_width > 0:
            border_arcade_color = (
                int(border_color[0] * 255),
                int(border_color[1] * 255),
                int(border_color[2] * 255)
            )
            arcade.draw_lbwh_rectangle_outline(
                ui_x, ui_y, ui_width, ui_height,
                border_arcade_color, int(border_width)
            )



    def draw_label_fallback(self, node_data, x, y):
        """Draw Label node"""
        # Get label properties - Labels can use either position or rect_position
        position = node_data.get("position", node_data.get("rect_position", [0.0, 0.0]))
        rect_size = node_data.get("rect_size", [100.0, 50.0])
        text = node_data.get("text", "Label")
        font_color = node_data.get("font_color", [1.0, 1.0, 1.0, 1.0])
        h_align = node_data.get("h_align", "Left")
        v_align = node_data.get("v_align", "Top")

        # Calculate UI position and size with percentage support
        ui_x, ui_y = self.calculate_ui_position(position, rect_size)
        ui_width, ui_height = self.calculate_ui_size(rect_size)

        # Convert font color to arcade format
        font_arcade_color = (
            int(font_color[0] * 255),
            int(font_color[1] * 255),
            int(font_color[2] * 255)
        )

        # Calculate text position based on alignment within the rect (centered on position)
        text_x = ui_x - ui_width/2 + 5  # Default left alignment with padding
        if h_align == "Center":
            # Center text within the rect
            text_x = ui_x
        elif h_align == "Right":
            # Right align text within the rect
            text_x = ui_x + ui_width/2 - 5

        text_y = ui_y + ui_height/2 - 15  # Default top alignment (arcade uses bottom-left origin)
        if v_align == "Center":
            # Center text vertically within the rect
            text_y = ui_y
        elif v_align == "Bottom":
            # Bottom align text within the rect
            text_y = ui_y - ui_height/2 + 15

        # Draw the actual text with proper font size and font
        actual_font_size = node_data.get("font_size", 14)
        font_name = node_data.get("font", "Arial")  # Default to Arial

        # Support percentage-based font sizing (relative to game height)
        if 0.0 <= actual_font_size <= 1.0:
            game_area = getattr(self, 'game_area', {"width": self.width, "height": self.height, "offset_x": 0, "offset_y": 0})
            actual_font_size = actual_font_size * game_area['height']

        # For now, use the font size - font family support would require more complex text rendering
        self.draw_cached_text(text, text_x, text_y, font_arcade_color, actual_font_size)

    def draw_button_fallback(self, node_data, x, y):
        """Draw Button node with interactive states"""
        # Get button properties - Buttons use position (UI coordinate system)
        position = node_data.get("position", [0.0, 0.0])
        rect_size = node_data.get("rect_size", [100.0, 30.0])
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

        # Calculate UI position and size with percentage support
        ui_x, ui_y = self.calculate_ui_position(position, rect_size)
        ui_width, ui_height = self.calculate_ui_size(rect_size)

        # Determine current button color based on state
        if disabled:
            current_color = disabled_color
        elif is_mouse_pressed or (toggle_mode and pressed):
            current_color = pressed_color
        elif is_hovered:
            current_color = hover_color
        else:
            current_color = normal_color

        # Convert colors to arcade format (0-255)
        button_arcade_color = (
            int(current_color[0] * 255),
            int(current_color[1] * 255),
            int(current_color[2] * 255),
            int(current_color[3] * 255)
        )

        font_arcade_color = (
            int(font_color[0] * 255),
            int(font_color[1] * 255),
            int(font_color[2] * 255)
        )

        # Draw button background
        arcade.draw_lbwh_rectangle_filled(
            ui_x, ui_y, ui_width, ui_height,
            button_arcade_color
        )

        # Draw border if enabled
        if border_width > 0:
            border_arcade_color = (
                int(border_color[0] * 255),
                int(border_color[1] * 255),
                int(border_color[2] * 255)
            )
            arcade.draw_lbwh_rectangle_outline(
                ui_x, ui_y, ui_width, ui_height,
                border_arcade_color, int(border_width)
            )

        # Draw button text (centered)
        text_x = ui_x + ui_width / 2
        text_y = ui_y + ui_height / 2

        # Handle font size
        actual_font_size = node_data.get("font_size", 14)

        # Support percentage-based font sizing (relative to game height)
        if 0.0 <= actual_font_size <= 1.0:
            game_area = getattr(self, 'game_area', {"width": self.width, "height": self.height, "offset_x": 0, "offset_y": 0})
            actual_font_size = actual_font_size * game_area['height']

        # Draw the button text centered
        self.draw_cached_text(text, text_x, text_y, font_arcade_color, actual_font_size)

    def draw_canvas_layer_fallback(self, node_data, x, y):
        """Draw CanvasLayer node"""
        # Get canvas layer properties
        layer_index = node_data.get("layer", 1)
        offset = node_data.get("offset", [0.0, 0.0])
        rotation = node_data.get("rotation", 0.0)
        scale = node_data.get("scale", [1.0, 1.0])
        follow_viewport_enable = node_data.get("follow_viewport_enable", False)

        # Adjust position for layer coordinates
        layer_x = x + offset[0]
        layer_y = y + offset[1]

        # CanvasLayer nodes are invisible containers for UI layering - no rendering needed

    def draw_ui(self):
        """Draw UI overlay - minimal for clean game view"""
        # Only show essential controls
        self.draw_cached_text("ESC: Exit", 10, 10, arcade.color.WHITE, 12)

    def on_resize(self, width, height):
        """Handle window resize events with aspect ratio maintenance"""
        super().on_resize(width, height)

        # Clear text cache when window is resized to avoid positioning issues
        self.text_objects.clear()

        # Maintain 16:9 aspect ratio with letterboxing/pillarboxing
        target_aspect = 16.0 / 9.0
        current_aspect = width / height

        if current_aspect > target_aspect:
            # Window is too wide - add pillarboxing (black bars on sides)
            game_height = height
            game_width = int(height * target_aspect)
            offset_x = (width - game_width) // 2
            offset_y = 0
        else:
            # Window is too tall - add letterboxing (black bars on top/bottom)
            game_width = width
            game_height = int(width / target_aspect)
            offset_x = 0
            offset_y = (height - game_height) // 2

        # Store the game area dimensions for UI positioning
        self.game_area = {
            "width": game_width,
            "height": game_height,
            "offset_x": offset_x,
            "offset_y": offset_y
        }

        # Update camera viewport if camera exists
        if self.camera:
            # Use Arcade's match_window method instead of update_values to avoid Rect issues
            try:
                self.camera.match_window(viewport=True, projection=True, scissor=True, position=False)
            except Exception as e:
                print(f"Camera viewport update failed: {e}")
                # Fallback - just continue without viewport update

    def on_update(self, delta_time):
        """Update game logic and run scripts"""
        # Update input manager every frame (important for "just pressed/released" detection)
        if self.input_manager:
            self.input_manager.update_input_state(
                self.pressed_keys, self.mouse_buttons,
                self.mouse_position, self.current_modifiers
            )

        # Update LSC runtime timing
        if self.lsc_runtime:
            self.lsc_runtime.update_time(delta_time)

        # Update physics simulation
        if self.physics_enabled and self.physics_world:
            self.physics_world.step(delta_time)

        # Update sprites in sprite lists
        for sprite_list in self.sprite_lists.values():
            for sprite in sprite_list:
                if hasattr(sprite, 'on_update'):
                    sprite.on_update(delta_time)

        # Call script update methods if available
        if self.lsc_runtime and self.scene:
            for root_node in self.scene.root_nodes:
                self.update_node_scripts(root_node, delta_time)

    def update_node_scripts(self, node, delta_time):
        """Update scripts attached to nodes"""
        try:
            # Call script update methods if the node has a script
            if hasattr(node, 'script_instance'):
                # Call _process method (Godot-style update method)
                node.script_instance.call_method('_process', delta_time)
                # Call _physics_process method (Godot-style physics update method)
                node.script_instance.call_method('_physics_process', delta_time)
                # Also call on_update for compatibility
                node.script_instance.call_method('on_update', delta_time)
        except Exception as e:
            print(f"Error updating script for {node.name}: {e}")

        # Update children
        for child in node.children:
            self.update_node_scripts(child, delta_time)

    def draw_collision_shape_fallback(self, node_data: dict[str, any], x: float, y: float):
        """Draw collision shape for debugging"""
        shape_type = node_data.get("shape", "rectangle")
        debug_color = node_data.get("debug_color", [0.0, 0.6, 0.7, 0.5])
        disabled = node_data.get("disabled", False)

        if disabled:
            return  # Don't draw disabled shapes

        # Set debug color
        rect = arcade.XYWH(x - 16, y - 16, 32, 32)
        arcade.draw_rect_outline(rect, arcade.color.CYAN, 2)

        if shape_type == "rectangle":
            size = node_data.get("size", [32, 32])
            width, height = size[0], size[1]
            rect = arcade.XYWH(x - width/2, y - height/2, width, height)
            arcade.draw_rect_outline(rect, arcade.color.CYAN, 2)

        elif shape_type == "circle":
            radius = node_data.get("radius", 16.0)
            arcade.draw_circle_outline(x, y, radius, arcade.color.CYAN, 2)

        elif shape_type == "capsule":
            radius = node_data.get("capsule_radius", 16.0)
            height = node_data.get("height", 32.0)
            # Draw capsule as circle with lines
            arcade.draw_circle_outline(x, y - height/2 + radius, radius, arcade.color.CYAN, 2)
            arcade.draw_circle_outline(x, y + height/2 - radius, radius, arcade.color.CYAN, 2)
            arcade.draw_line(x - radius, y - height/2 + radius, x - radius, y + height/2 - radius, arcade.color.CYAN, 2)
            arcade.draw_line(x + radius, y - height/2 + radius, x + radius, y + height/2 - radius, arcade.color.CYAN, 2)

        elif shape_type == "segment":
            point_a = node_data.get("point_a", [0, 0])
            point_b = node_data.get("point_b", [32, 0])
            arcade.draw_line(x + point_a[0], y + point_a[1], x + point_b[0], y + point_b[1], arcade.color.CYAN, 3)

    def draw_collision_polygon_fallback(self, node_data: dict[str, any], x: float, y: float):
        """Draw collision polygon for debugging"""
        polygon = node_data.get("polygon", [[0, 0], [32, 0], [32, 32], [0, 32]])
        debug_color = node_data.get("debug_color", [0.0, 0.6, 0.7, 0.5])
        disabled = node_data.get("disabled", False)

        if disabled or len(polygon) < 3:
            return  # Don't draw disabled or invalid polygons

        # Convert polygon to world coordinates
        points = []
        for vertex in polygon:
            if isinstance(vertex, list) and len(vertex) >= 2:
                points.append((x + vertex[0], y + vertex[1]))

        if len(points) >= 3:
            # Draw polygon outline
            for i in range(len(points)):
                start = points[i]
                end = points[(i + 1) % len(points)]
                arcade.draw_line(start[0], start[1], end[0], end[1], arcade.color.CYAN, 2)

    def on_key_press(self, key, modifiers):
        """Handle key press events"""
        if key == arcade.key.ESCAPE:
            self.close()

        # Debug: Show key press
        print(f"Key pressed: {key} (A={arcade.key.A}, LEFT={arcade.key.LEFT})")

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
                    if hasattr(node, 'script_instance'):
                        # Call the mouse event method
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
                    if hasattr(node, 'script_instance'):
                        if is_hovered:
                            node.script_instance.call_method('mouse_entered')
                        else:
                            node.script_instance.call_method('mouse_exited')
        except Exception as e:
            print(f"Error updating hover for {node.name}: {e}")

        # Update hover for children
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
            if hasattr(node, 'script_instance'):
                node.script_instance.call_method(method_name, *args)
        except Exception as e:
            print(f"Error handling input for {node.name}: {e}")

        # Handle input for children
        for child in node.children:
            self.handle_node_input(child, method_name, *args)

    def _update_modifiers(self, modifiers):
        """Update current modifier keys state"""
        self.current_modifiers.clear()

        # Convert arcade modifiers to string set
        if modifiers & arcade.key.MOD_SHIFT:
            self.current_modifiers.add("shift")
        if modifiers & arcade.key.MOD_CTRL:
            self.current_modifiers.add("ctrl")
        if modifiers & arcade.key.MOD_ALT:
            self.current_modifiers.add("alt")
        if modifiers & arcade.key.MOD_ACCEL:  # Meta/Cmd key
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
            if texture_path not in self.textures:
                full_path = Path(self.project_path) / texture_path
                if full_path.exists():
                    self.textures[texture_path] = arcade.load_texture(str(full_path))

            if texture_path in self.textures:
                sprite = arcade.Sprite()
                sprite.texture = self.textures[texture_path]
                sprite.center_x = x
                sprite.center_y = y
                self.sprite_lists["sprites"].append(sprite)
                return sprite
        except Exception as e:
            print(f"Error creating sprite: {e}")
        return None

def main():
    try:
        game = LupineGameWindow(r"{project_path}")
        game.setup()
        arcade.run()
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
