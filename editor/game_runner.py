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

class LupineGameWindow(arcade.Window):
    def __init__(self):
        super().__init__(1920, 1080, "Lupine Engine - Game Runner")  # 16:9 aspect ratio
        self.scene_data = None
        self.camera_x = 0
        self.camera_y = 0
        self.load_scene()

    def load_scene(self):
        try:
            scene_file = r"{scene_file_path}"
            with open(scene_file, 'r') as f:
                self.scene_data = json.load(f)
            print(f"Loaded scene: {{self.scene_data.get('name', 'Unknown')}}")
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

    def setup(self):
        arcade.set_background_color(arcade.color.DARK_GRAY)
        print("Game setup complete")
        print("Controls: WASD to move camera, ESC to exit")

    def on_draw(self):
        self.clear()

        # Draw grid
        self.draw_grid()

        # Draw scene nodes
        if self.scene_data:
            nodes = self.scene_data.get("nodes", [])
            for node in nodes:
                self.draw_node(node)

        # Draw UI overlay
        self.draw_ui()

    def draw_grid(self):
        # Draw a simple grid
        grid_size = 100
        for x in range(-2000, 2000, grid_size):
            arcade.draw_line(x - self.camera_x, -2000 - self.camera_y,
                           x - self.camera_x, 2000 - self.camera_y,
                           arcade.color.DARK_GRAY, 1)
        for y in range(-2000, 2000, grid_size):
            arcade.draw_line(-2000 - self.camera_x, y - self.camera_y,
                           2000 - self.camera_x, y - self.camera_y,
                           arcade.color.DARK_GRAY, 1)

    def draw_node(self, node_data):
        # Simple node rendering with camera offset
        position = node_data.get("position", [0, 0])
        node_type = node_data.get("type", "Node")

        # Apply camera transform
        x = position[0] + self.width // 2 - self.camera_x
        y = position[1] + self.height // 2 - self.camera_y

        if node_type == "Node2D":
            arcade.draw_circle_filled(x, y, 8, arcade.color.WHITE)
            arcade.draw_text(node_data.get("name", "Node"), x + 15, y,
                           arcade.color.WHITE, 12)
        elif node_type == "Sprite":
            size = node_data.get("size", [64, 64])
            arcade.draw_rectangle_filled(x, y, size[0], size[1], arcade.color.GREEN)
            arcade.draw_text(node_data.get("name", "Sprite"), x + size[0]//2 + 10, y,
                           arcade.color.WHITE, 12)
        elif node_type == "Camera2D":
            arcade.draw_rectangle_outline(x, y, 60, 40, arcade.color.YELLOW, 3)
            arcade.draw_text(node_data.get("name", "Camera"), x + 35, y,
                           arcade.color.YELLOW, 12)
        elif node_type == "Area2D":
            arcade.draw_circle_outline(x, y, 30, arcade.color.BLUE, 3)
            arcade.draw_text(node_data.get("name", "Area"), x + 35, y,
                           arcade.color.BLUE, 12)

        # Draw children
        for child in node_data.get("children", []):
            self.draw_node(child)

    def draw_ui(self):
        # Draw UI overlay
        arcade.draw_text("Lupine Engine - Game Runner", 10, self.height - 30,
                        arcade.color.WHITE, 16)
        arcade.draw_text(f"Camera: ({{self.camera_x}}, {{self.camera_y}})", 10, self.height - 50,
                        arcade.color.WHITE, 12)
        arcade.draw_text("WASD: Move Camera | ESC: Exit", 10, 10,
                        arcade.color.WHITE, 12)

    def on_update(self, delta_time):
        # Basic camera movement
        camera_speed = 200 * delta_time

        # Initialize pressed_keys if it doesn't exist
        if not hasattr(self, 'pressed_keys'):
            self.pressed_keys = set()

        if arcade.key.W in self.pressed_keys:
            self.camera_y += camera_speed
        if arcade.key.S in self.pressed_keys:
            self.camera_y -= camera_speed
        if arcade.key.A in self.pressed_keys:
            self.camera_x -= camera_speed
        if arcade.key.D in self.pressed_keys:
            self.camera_x += camera_speed

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.close()

        if not hasattr(self, 'pressed_keys'):
            self.pressed_keys = set()
        self.pressed_keys.add(key)

    def on_key_release(self, key, modifiers):
        if hasattr(self, 'pressed_keys'):
            self.pressed_keys.discard(key)

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
