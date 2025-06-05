"""
Build Dialog for Lupine Engine
Provides UI for building games into standalone executables
"""

import os
import sys
import threading
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox, QTabWidget, QWidget,
    QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from core.build_system import GameBuilder, BuildError


class BuildWorker(QThread):
    """Worker thread for building games"""
    
    progress_updated = pyqtSignal(str, int)  # message, progress
    build_finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, builder: GameBuilder):
        super().__init__()
        self.builder = builder
        self.builder.set_progress_callback(self.on_progress)
    
    def on_progress(self, message: str, progress: int):
        """Handle progress updates from builder"""
        self.progress_updated.emit(message, progress)
    
    def run(self):
        """Run the build process"""
        try:
            success = self.builder.build()
            if success:
                output_path = self.builder.get_output_path()
                self.build_finished.emit(True, f"Build completed successfully!\nOutput: {output_path}")
            else:
                self.build_finished.emit(False, "Build failed for unknown reason")
        except BuildError as e:
            self.build_finished.emit(False, str(e))
        except Exception as e:
            self.build_finished.emit(False, f"Unexpected error: {e}")


class BuildDialog(QDialog):
    """Dialog for configuring and running game builds"""
    
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.builder: Optional[GameBuilder] = None
        self.build_worker: Optional[BuildWorker] = None
        
        self.setWindowTitle(f"Build Game - {project.config.get('name', 'Untitled')}")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Build settings tab
        self.create_build_settings_tab()
        
        # Advanced settings tab
        self.create_advanced_settings_tab()
        
        # Progress tab
        self.create_progress_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.build_button = QPushButton("Build Game")
        self.build_button.clicked.connect(self.start_build)
        button_layout.addWidget(self.build_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def create_build_settings_tab(self):
        """Create the build settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout(output_group)
        
        self.output_dir_edit = QLineEdit()
        output_dir_button = QPushButton("Browse...")
        output_dir_button.clicked.connect(self.browse_output_dir)
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(output_dir_button)
        
        output_layout.addRow("Output Directory:", output_dir_layout)
        
        # Platform selection
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["windows", "linux", "mac", "browser"])
        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)
        output_layout.addRow("Target Platform:", self.platform_combo)
        
        # Build type
        self.build_type_combo = QComboBox()
        self.build_type_combo.addItems(["release", "debug"])
        output_layout.addRow("Build Type:", self.build_type_combo)
        
        layout.addWidget(output_group)
        
        # Executable settings
        exe_group = QGroupBox("Executable Settings")
        exe_layout = QFormLayout(exe_group)
        
        self.one_file_check = QCheckBox("Create single executable file")
        self.one_file_check.setChecked(True)
        exe_layout.addRow("", self.one_file_check)
        
        self.include_console_check = QCheckBox("Include console window")
        exe_layout.addRow("", self.include_console_check)
        
        # Icon selection
        self.icon_path_edit = QLineEdit()
        icon_button = QPushButton("Browse...")
        icon_button.clicked.connect(self.browse_icon)
        
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(self.icon_path_edit)
        icon_layout.addWidget(icon_button)
        
        exe_layout.addRow("Icon File:", icon_layout)
        
        layout.addWidget(exe_group)

        # Browser settings (initially hidden)
        self.browser_group = QGroupBox("Browser Settings")
        browser_layout = QFormLayout(self.browser_group)

        self.browser_width_spin = QSpinBox()
        self.browser_width_spin.setRange(320, 3840)
        self.browser_width_spin.setValue(1920)
        browser_layout.addRow("Game Width:", self.browser_width_spin)

        self.browser_height_spin = QSpinBox()
        self.browser_height_spin.setRange(240, 2160)
        self.browser_height_spin.setValue(1080)
        browser_layout.addRow("Game Height:", self.browser_height_spin)

        self.browser_fullscreen_check = QCheckBox("Allow fullscreen")
        browser_layout.addRow("", self.browser_fullscreen_check)

        layout.addWidget(self.browser_group)
        self.browser_group.setVisible(False)  # Hidden by default

        layout.addStretch()
        self.tab_widget.addTab(tab, "Build Settings")
    
    def create_advanced_settings_tab(self):
        """Create the advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # PyInstaller settings
        pyinstaller_group = QGroupBox("PyInstaller Settings")
        pyinstaller_layout = QFormLayout(pyinstaller_group)
        
        self.exclude_modules_edit = QLineEdit()
        self.exclude_modules_edit.setPlaceholderText("module1,module2,module3")
        pyinstaller_layout.addRow("Exclude Modules:", self.exclude_modules_edit)
        
        layout.addWidget(pyinstaller_group)
        
        # Additional files
        files_group = QGroupBox("Additional Files")
        files_layout = QVBoxLayout(files_group)
        
        files_info = QLabel("Additional files to include with the build (not yet implemented)")
        files_info.setStyleSheet("color: gray; font-style: italic;")
        files_layout.addWidget(files_info)
        
        layout.addWidget(files_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Advanced")
    
    def create_progress_tab(self):
        """Create the progress tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to build")
        layout.addWidget(self.status_label)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_output)
        
        self.tab_widget.addTab(tab, "Progress")
    
    def load_settings(self):
        """Load settings from project configuration"""
        # Set default output directory
        default_output = self.project.project_path / "builds"
        self.output_dir_edit.setText(str(default_output))
        
        # Load export settings from project
        export_settings = self.project.config.get("export", {})
        
        # Set icon if specified
        icon_file = export_settings.get("icon", "")
        if icon_file:
            icon_path = self.project.project_path / icon_file
            if icon_path.exists():
                self.icon_path_edit.setText(str(icon_path))
        
        # Set platform based on current system
        current_platform = "windows" if sys.platform == "win32" else "linux" if sys.platform.startswith("linux") else "mac"
        platform_index = self.platform_combo.findText(current_platform)
        if platform_index >= 0:
            self.platform_combo.setCurrentIndex(platform_index)
    
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", 
            self.output_dir_edit.text()
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def browse_icon(self):
        """Browse for icon file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon File", 
            str(self.project.project_path),
            "Icon Files (*.ico *.png *.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            self.icon_path_edit.setText(file_path)

    def on_platform_changed(self, platform: str):
        """Handle platform selection change"""
        is_browser = platform == "browser"

        # Show/hide browser-specific settings
        self.browser_group.setVisible(is_browser)

        # Disable desktop-specific settings for browser builds
        self.one_file_check.setEnabled(not is_browser)
        self.include_console_check.setEnabled(not is_browser)

        if is_browser:
            # Set browser-friendly defaults
            self.one_file_check.setChecked(False)
            self.include_console_check.setChecked(False)

    def start_build(self):
        """Start the build process"""
        try:
            # Validate settings
            if not self.output_dir_edit.text().strip():
                QMessageBox.warning(self, "Invalid Settings", "Please specify an output directory.")
                return
            
            # Create builder
            self.builder = GameBuilder(
                str(self.project.project_path),
                None  # Auto-detect engine path
            )
            
            # Configure builder
            platform = self.platform_combo.currentText()
            build_config = {
                "output_dir": Path(self.output_dir_edit.text()),
                "platform": platform,
                "build_type": self.build_type_combo.currentText(),
                "one_file": self.one_file_check.isChecked(),
                "include_console": self.include_console_check.isChecked(),
                "icon_path": self.icon_path_edit.text() if self.icon_path_edit.text().strip() else None,
                "exclude_modules": [m.strip() for m in self.exclude_modules_edit.text().split(",") if m.strip()]
            }

            # Add browser-specific settings
            if platform == "browser":
                build_config.update({
                    "browser_width": self.browser_width_spin.value(),
                    "browser_height": self.browser_height_spin.value(),
                    "browser_fullscreen": self.browser_fullscreen_check.isChecked()
                })
            
            self.builder.configure_build(**build_config)
            
            # Switch to progress tab
            self.tab_widget.setCurrentIndex(2)
            
            # Setup UI for building
            self.build_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.log_output.clear()
            
            # Start build worker
            self.build_worker = BuildWorker(self.builder)
            self.build_worker.progress_updated.connect(self.on_progress_updated)
            self.build_worker.build_finished.connect(self.on_build_finished)
            self.build_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Build Error", f"Failed to start build: {e}")
    
    def on_progress_updated(self, message: str, progress: int):
        """Handle progress updates"""
        self.status_label.setText(message)
        if progress >= 0:
            self.progress_bar.setValue(progress)
        
        # Add to log
        self.log_output.append(f"[{progress}%] {message}")
        
        # Auto-scroll to bottom
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_output.setTextCursor(cursor)
    
    def on_build_finished(self, success: bool, message: str):
        """Handle build completion"""
        self.progress_bar.setVisible(False)
        self.build_button.setEnabled(True)
        self.close_button.setEnabled(True)
        
        if success:
            self.status_label.setText("Build completed successfully!")
            self.log_output.append("\n" + "="*50)
            self.log_output.append("BUILD SUCCESSFUL!")
            self.log_output.append("="*50)
            self.log_output.append(message)
            
            # Show success message
            QMessageBox.information(self, "Build Complete", message)
        else:
            self.status_label.setText("Build failed!")
            self.log_output.append("\n" + "="*50)
            self.log_output.append("BUILD FAILED!")
            self.log_output.append("="*50)
            self.log_output.append(message)
            
            # Show error message
            QMessageBox.critical(self, "Build Failed", message)
