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

        runner_content = f'''
import sys
import os
sys.path.insert(0, r"{project_path}")

import arcade
import json
from pathlib import Path

# Import LSC runtime for script execution
try:
    from core.lsc import LSCRuntime, LSCInterpreter, execute_lsc_script
    from core.scene import Scene, Node, Node2D, Sprite, Camera2D
    LSC_AVAILABLE = True
except ImportError as e:
    print(f"LSC not available: {{e}}")
    LSC_AVAILABLE = False

class LupineGameWindow(arcade.Window):
    def __init__(self):
        super().__init__(1920, 1080, "Lupine Engine - Game Runner")  # 16:9 aspect ratio
        self.scene = None
        self.scene_data = None
        self.camera = None
        self.sprite_lists = {{}}
        self.textures = {{}}

        # LSC Runtime for script execution
        if LSC_AVAILABLE:
            self.lsc_runtime = LSCRuntime(game_runtime=self)
            # Add game runtime methods to LSC scope
            self.setup_lsc_builtins()
        else:
            self.lsc_runtime = None

        self.load_scene()

    def setup_lsc_builtins(self):
        """Setup additional built-in functions for LSC scripts"""
        if not self.lsc_runtime:
            return

        # Add game-specific functions to global scope
        builtins = {{
            'get_node': self.get_node,
            'find_node': self.find_node_by_name,
            'create_sprite': self.create_sprite,
            'is_key_pressed': self.is_key_pressed,
            'change_scene': self.change_scene,
            'reload_scene': self.reload_scene,
            'get_scene': self.get_scene,
            'get_delta_time': lambda: self.lsc_runtime.delta_time if self.lsc_runtime else 0.0,
            'get_fps': lambda: 1.0 / self.lsc_runtime.delta_time if self.lsc_runtime and self.lsc_runtime.delta_time > 0 else 0.0,
        }}

        for name, func in builtins.items():
            self.lsc_runtime.global_scope.define(name, func)

    def load_scene(self):
        try:
            scene_file = r"{scene_file_path}"
            with open(scene_file, 'r') as f:
                self.scene_data = json.load(f)
            print(f"Loaded scene: {{self.scene_data.get('name', 'Unknown')}}")

            # Load scene using proper Scene class
            if LSC_AVAILABLE:
                self.scene = Scene.load_from_file(scene_file)
                self.setup_scene()
            else:
                print("LSC not available, using basic scene rendering")

        except Exception as e:
            print(f"Error loading scene: {{e}}")
            # Create a default scene if loading fails
            self.scene_data = {{
                "name": "Default",
                "nodes": [{{
                    "name": "Main",
                    "type": "Node2D",
                    "position": [0, 0],
                    "children": []
                }}]
            }}

    def setup_scene(self):
        """Setup the scene with proper sprite lists and cameras"""
        if not self.scene:
            return

        # Find cameras in the scene
        self.find_cameras(self.scene.root)

        # Create sprite lists for different node types
        self.sprite_lists = {{
            "sprites": arcade.SpriteList(),
            "ui": arcade.SpriteList()
        }}

        # Setup nodes and load their scripts
        self.setup_node(self.scene.root)

    def find_cameras(self, node):
        """Find and setup cameras in the scene"""
        if isinstance(node, Camera2D) and node.current:
            self.camera = arcade.Camera2D()
            # Set camera position based on node position
            self.camera.position = node.position
            print(f"Found active camera: {{node.name}} at {{node.position}}")

        for child in node.children:
            self.find_cameras(child)

    def setup_node(self, node):
        """Setup a node and its children, including script loading"""
        try:
            # Load and execute node script if it exists
            if node.script_path and self.lsc_runtime:
                script_file = Path(r"{project_path}") / node.script_path
                if script_file.exists():
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

                        # Execute script
                        execute_lsc_script(script_content, self.lsc_runtime)

                        # Attach script instance to node
                        node.script_instance = script_instance

                        # Call on_ready if it exists
                        if script_instance.scope.has('on_ready'):
                            script_instance.call_method('on_ready')
                            script_instance.ready_called = True

                        print(f"Loaded script for {{node.name}}: {{node.script_path}}")

                    finally:
                        # Restore scope
                        self.lsc_runtime.current_scope = old_scope

            # Setup sprite nodes
            if isinstance(node, Sprite):
                self.setup_sprite_node(node)

        except Exception as e:
            print(f"Error setting up node {{node.name}}: {{e}}")

        # Setup children
        for child in node.children:
            self.setup_node(child)

    def setup_sprite_node(self, sprite_node):
        """Setup a sprite node with proper texture loading"""
        try:
            if sprite_node.texture:
                # Load texture if not already loaded
                texture_path = Path(r"{project_path}") / sprite_node.texture
                if texture_path.exists() and str(texture_path) not in self.textures:
                    self.textures[str(texture_path)] = arcade.load_texture(str(texture_path))
                    print(f"Loaded texture: {{texture_path}}")

                # Create arcade sprite
                if str(texture_path) in self.textures:
                    arcade_sprite = arcade.Sprite()
                    arcade_sprite.texture = self.textures[str(texture_path)]
                    arcade_sprite.center_x = sprite_node.position[0]
                    arcade_sprite.center_y = sprite_node.position[1]
                    arcade_sprite.angle = sprite_node.rotation
                    arcade_sprite.scale = sprite_node.scale[0]  # Use X scale

                    self.sprite_lists["sprites"].append(arcade_sprite)

        except Exception as e:
            print(f"Error setting up sprite {{sprite_node.name}}: {{e}}")

    def setup(self):
        arcade.set_background_color(arcade.color.DARK_GRAY)
        print("Game setup complete")
        print("ESC to exit")

    def on_draw(self):
        self.clear()

        # Use camera if available
        if self.camera:
            self.camera.use()

        # Draw sprite lists (proper game objects)
        for sprite_list in self.sprite_lists.values():
            sprite_list.draw()

        # Draw scene nodes (fallback for basic rendering)
        if self.scene_data and not LSC_AVAILABLE:
            nodes = self.scene_data.get("nodes", [])
            for node in nodes:
                self.draw_node_fallback(node)

        # Draw UI overlay (always drawn without camera)
        if self.camera:
            # Reset to default camera for UI
            arcade.get_window().ctx.default_camera.use()

        self.draw_ui()

    def draw_node_fallback(self, node_data):
        """Fallback node rendering when LSC is not available"""
        position = node_data.get("position", [0, 0])
        node_type = node_data.get("type", "Node")

        # Center position on screen
        x = position[0] + self.width // 2
        y = position[1] + self.height // 2

        if node_type == "Node2D":
            arcade.draw_circle_filled(x, y, 8, arcade.color.WHITE)
            arcade.draw_text(node_data.get("name", "Node"), x + 15, y,
                           arcade.color.WHITE, 12)
        elif node_type == "Sprite":
            size = node_data.get("size", [64, 64])
            # Use the correct arcade function: draw_lbwh_rectangle_filled(left, bottom, width, height, color)
            arcade.draw_lbwh_rectangle_filled(x - size[0]//2, y - size[1]//2, size[0], size[1], arcade.color.GREEN)
            arcade.draw_text(node_data.get("name", "Sprite"), x + size[0]//2 + 10, y,
                           arcade.color.WHITE, 12)
        elif node_type == "Camera2D":
            # Use the correct arcade function: draw_lbwh_rectangle_outline(left, bottom, width, height, color, border_width)
            arcade.draw_lbwh_rectangle_outline(x - 30, y - 20, 60, 40, arcade.color.YELLOW, 3)
            arcade.draw_text(node_data.get("name", "Camera"), x + 35, y,
                           arcade.color.YELLOW, 12)
        elif node_type == "Area2D":
            arcade.draw_circle_outline(x, y, 30, arcade.color.BLUE, 3)
            arcade.draw_text(node_data.get("name", "Area"), x + 35, y,
                           arcade.color.BLUE, 12)

        # Draw children
        for child in node_data.get("children", []):
            self.draw_node_fallback(child)

    def draw_ui(self):
        """Draw UI overlay"""
        arcade.draw_text("Lupine Engine - Game Runner", 10, self.height - 30,
                        arcade.color.WHITE, 16)

        # Show camera info if available
        if self.camera:
            arcade.draw_text(f"Camera: {{self.camera.position}}", 10, self.height - 50,
                            arcade.color.WHITE, 12)

        arcade.draw_text("ESC: Exit", 10, 10, arcade.color.WHITE, 12)

    def on_update(self, delta_time):
        """Update game logic and run scripts"""
        # Update LSC runtime timing
        if self.lsc_runtime:
            self.lsc_runtime.update_time(delta_time)

        # Update sprite lists
        for sprite_list in self.sprite_lists.values():
            sprite_list.on_update(delta_time)

        # Call script update methods if available
        if self.lsc_runtime and self.scene:
            self.update_node_scripts(self.scene.root, delta_time)

    def update_node_scripts(self, node, delta_time):
        """Update scripts attached to nodes"""
        try:
            # Call on_update method if the node has a script
            if hasattr(node, 'script_instance'):
                node.script_instance.call_method('on_update', delta_time)
        except Exception as e:
            print(f"Error updating script for {{node.name}}: {{e}}")

        # Update children
        for child in node.children:
            self.update_node_scripts(child, delta_time)

    def on_key_press(self, key, modifiers):
        """Handle key press events"""
        if key == arcade.key.ESCAPE:
            self.close()

        # Forward input to LSC runtime for script handling
        if self.lsc_runtime:
            # Store key state for script access
            if not hasattr(self, 'pressed_keys'):
                self.pressed_keys = set()
            self.pressed_keys.add(key)

            # Call script input handlers
            if self.scene:
                self.handle_node_input(self.scene.root, 'on_key_press', key, modifiers)

    def on_key_release(self, key, modifiers):
        """Handle key release events"""
        if hasattr(self, 'pressed_keys'):
            self.pressed_keys.discard(key)

        # Forward input to LSC runtime
        if self.lsc_runtime and self.scene:
            self.handle_node_input(self.scene.root, 'on_key_release', key, modifiers)

    def handle_node_input(self, node, method_name, *args):
        """Handle input events for node scripts"""
        try:
            if hasattr(node, 'script_instance'):
                node.script_instance.call_method(method_name, *args)
        except Exception as e:
            print(f"Error handling input for {{node.name}}: {{e}}")

        # Handle input for children
        for child in node.children:
            self.handle_node_input(child, method_name, *args)

    def is_key_pressed(self, key):
        """Check if a key is currently pressed (for script access)"""
        return hasattr(self, 'pressed_keys') and key in self.pressed_keys

    # Game runtime methods for LSC scripts
    def change_scene(self, scene_path):
        """Change to a different scene"""
        try:
            print(f"Changing scene to: {{scene_path}}")
            # This would be implemented to actually change scenes
            # For now, just log the request
        except Exception as e:
            print(f"Error changing scene: {{e}}")

    def reload_scene(self):
        """Reload the current scene"""
        try:
            print("Reloading current scene")
            self.load_scene()
        except Exception as e:
            print(f"Error reloading scene: {{e}}")

    def get_scene(self):
        """Get the current scene"""
        return self.scene

    def get_node(self, name):
        """Get a node by name"""
        if self.scene:
            return self.find_node_by_name(self.scene.root, name)
        return None

    def find_node_by_name(self, node, name):
        """Recursively find a node by name"""
        if isinstance(node, str):
            # If called with just a name, search from root
            if self.scene:
                return self.find_node_by_name(self.scene.root, node)
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
                full_path = Path(r"{project_path}") / texture_path
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
            print(f"Error creating sprite: {{e}}")
        return None

def main():
    try:
        game = LupineGameWindow()
        game.setup()
        arcade.run()
    except Exception as e:
        print(f"Game error: {{e}}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''
        
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
