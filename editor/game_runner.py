"""
Game Runner Widget for Lupine Engine
Handles game execution and runtime display using the new streamlined game engine
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QFont

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
            # Create runner script
            runner_script = self.create_runner_script()
            
            # Create QProcess for better control
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
            import traceback
            error_msg = f"Failed to start game: {e}\n{traceback.format_exc()}"
            self.error_received.emit(error_msg)
            self.finished.emit(1)
    
    def create_runner_script(self) -> str:
        """Create a temporary runner script using the new streamlined game engine"""
        project_path = str(self.project.project_path).replace('\\', '\\\\')
        scene_path = self.scene_path.replace('\\', '\\\\')

        # Get the Lupine Engine path (where this script is located)
        lupine_engine_path = str(Path(__file__).parent.parent).replace('\\', '\\\\')

        # Create a simple runner script that uses the new game engine
        template = f'''
import sys
import os
from pathlib import Path

# Add both the Lupine Engine path and project path to sys.path
sys.path.insert(0, r"{lupine_engine_path}")
sys.path.insert(0, r"{project_path}")

try:
    from core.simple_game_runner import run_game
    
    # Run the game using the new streamlined engine
    exit_code = run_game(r"{project_path}", r"{scene_path}", r"{lupine_engine_path}")
    sys.exit(exit_code)
    
except Exception as e:
    print(f"Failed to start game: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''

        # Write to temporary file
        runner_path = self.project.project_path / "temp_runner.py"
        with open(runner_path, 'w') as f:
            f.write(template)
        
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
