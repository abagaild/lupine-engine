"""
Project Settings Dialog for Lupine Engine
Allows editing of project configuration including display, audio, input, and physics settings
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QGroupBox, QPushButton, QLabel, QMessageBox,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.project import LupineProject


class ProjectSettingsDialog(QDialog):
    """Dialog for editing project settings"""
    
    def __init__(self, project: LupineProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.settings = project.config.copy()  # Work with a copy
        
        self.setWindowTitle("Project Settings")
        self.setModal(True)
        self.resize(700, 600)

        # Apply styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
            }
        """)

        self.setup_ui()
        self.load_settings()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_display_tab()
        self.create_audio_tab()
        self.create_input_tab()
        self.create_physics_tab()
        self.create_export_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def create_general_tab(self):
        """Create the general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Project Information
        info_group = QGroupBox("Project Information")
        info_layout = QFormLayout(info_group)
        
        self.project_name_edit = QLineEdit()
        info_layout.addRow("Project Name:", self.project_name_edit)
        
        self.project_description_edit = QLineEdit()
        info_layout.addRow("Description:", self.project_description_edit)
        
        self.project_version_edit = QLineEdit()
        info_layout.addRow("Version:", self.project_version_edit)
        
        self.main_scene_edit = QLineEdit()
        info_layout.addRow("Main Scene:", self.main_scene_edit)
        
        layout.addWidget(info_group)
        
        # Engine Information (read-only)
        engine_group = QGroupBox("Engine Information")
        engine_layout = QFormLayout(engine_group)
        
        engine_version_label = QLabel("1.0.0")
        engine_version_label.setStyleSheet("color: #888;")
        engine_layout.addRow("Engine Version:", engine_version_label)
        
        layout.addWidget(engine_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "General")
    
    def create_display_tab(self):
        """Create the display settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Window Settings
        window_group = QGroupBox("Window Settings")
        window_layout = QFormLayout(window_group)
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(320, 7680)
        self.window_width_spin.setSingleStep(1)
        window_layout.addRow("Width:", self.window_width_spin)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(240, 4320)
        self.window_height_spin.setSingleStep(1)
        window_layout.addRow("Height:", self.window_height_spin)
        
        self.fullscreen_check = QCheckBox()
        window_layout.addRow("Fullscreen:", self.fullscreen_check)
        
        self.resizable_check = QCheckBox()
        window_layout.addRow("Resizable:", self.resizable_check)
        
        layout.addWidget(window_group)
        
        # Scaling Settings
        scaling_group = QGroupBox("Scaling Settings")
        scaling_layout = QFormLayout(scaling_group)
        
        self.scaling_mode_combo = QComboBox()
        self.scaling_mode_combo.addItems(["stretch", "letterbox", "crop"])
        scaling_layout.addRow("Scaling Mode:", self.scaling_mode_combo)
        
        self.scaling_filter_combo = QComboBox()
        self.scaling_filter_combo.addItems(["linear", "nearest"])
        scaling_layout.addRow("Scaling Filter:", self.scaling_filter_combo)
        
        layout.addWidget(scaling_group)
        
        # Add help text
        help_label = QLabel(
            "• Stretch: Stretches game to fill window (may distort)\n"
            "• Letterbox: Maintains aspect ratio with black bars\n"
            "• Crop: Crops game view to fill window\n\n"
            "• Linear: Smooth scaling (good for most games)\n"
            "• Nearest: Pixel-perfect scaling (good for pixel art)"
        )
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Display")
    
    def create_audio_tab(self):
        """Create the audio settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Volume Settings
        volume_group = QGroupBox("Volume Settings")
        volume_layout = QFormLayout(volume_group)
        
        self.master_volume_spin = QDoubleSpinBox()
        self.master_volume_spin.setRange(0.0, 1.0)
        self.master_volume_spin.setSingleStep(0.1)
        self.master_volume_spin.setDecimals(2)
        volume_layout.addRow("Master Volume:", self.master_volume_spin)
        
        self.music_volume_spin = QDoubleSpinBox()
        self.music_volume_spin.setRange(0.0, 1.0)
        self.music_volume_spin.setSingleStep(0.1)
        self.music_volume_spin.setDecimals(2)
        volume_layout.addRow("Music Volume:", self.music_volume_spin)
        
        self.sfx_volume_spin = QDoubleSpinBox()
        self.sfx_volume_spin.setRange(0.0, 1.0)
        self.sfx_volume_spin.setSingleStep(0.1)
        self.sfx_volume_spin.setDecimals(2)
        volume_layout.addRow("SFX Volume:", self.sfx_volume_spin)
        
        layout.addWidget(volume_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Audio")
    
    def create_input_tab(self):
        """Create the input settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Input Settings
        input_group = QGroupBox("Input Settings")
        input_layout = QFormLayout(input_group)
        
        self.deadzone_spin = QDoubleSpinBox()
        self.deadzone_spin.setRange(0.0, 1.0)
        self.deadzone_spin.setSingleStep(0.05)
        self.deadzone_spin.setDecimals(2)
        input_layout.addRow("Controller Deadzone:", self.deadzone_spin)
        
        layout.addWidget(input_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Input")
    
    def create_physics_tab(self):
        """Create the physics settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Physics Settings
        physics_group = QGroupBox("Physics Settings")
        physics_layout = QFormLayout(physics_group)
        
        self.gravity_x_spin = QDoubleSpinBox()
        self.gravity_x_spin.setRange(-9999.0, 9999.0)
        self.gravity_x_spin.setSingleStep(10.0)
        physics_layout.addRow("Gravity X:", self.gravity_x_spin)
        
        self.gravity_y_spin = QDoubleSpinBox()
        self.gravity_y_spin.setRange(-9999.0, 9999.0)
        self.gravity_y_spin.setSingleStep(10.0)
        physics_layout.addRow("Gravity Y:", self.gravity_y_spin)
        
        self.timestep_spin = QDoubleSpinBox()
        self.timestep_spin.setRange(0.001, 1.0)
        self.timestep_spin.setSingleStep(0.001)
        self.timestep_spin.setDecimals(6)
        physics_layout.addRow("Physics Timestep:", self.timestep_spin)
        
        layout.addWidget(physics_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Physics")
    
    def create_export_tab(self):
        """Create the export settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Export Settings
        export_group = QGroupBox("Export Settings")
        export_layout = QFormLayout(export_group)
        
        self.icon_path_edit = QLineEdit()
        export_layout.addRow("Icon Path:", self.icon_path_edit)
        
        # Platform checkboxes
        platforms_group = QGroupBox("Target Platforms")
        platforms_layout = QVBoxLayout(platforms_group)
        
        self.windows_check = QCheckBox("Windows")
        platforms_layout.addWidget(self.windows_check)
        
        self.linux_check = QCheckBox("Linux")
        platforms_layout.addWidget(self.linux_check)
        
        self.mac_check = QCheckBox("macOS")
        platforms_layout.addWidget(self.mac_check)
        
        layout.addWidget(export_group)
        layout.addWidget(platforms_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Export")
    
    def load_settings(self):
        """Load current settings into the UI"""
        config = self.settings
        
        # General
        self.project_name_edit.setText(config.get("name", ""))
        self.project_description_edit.setText(config.get("description", ""))
        self.project_version_edit.setText(config.get("version", "1.0.0"))
        self.main_scene_edit.setText(config.get("main_scene", ""))
        
        # Display
        display = config.get("settings", {}).get("display", {})
        self.window_width_spin.setValue(display.get("width", 1920))
        self.window_height_spin.setValue(display.get("height", 1080))
        self.fullscreen_check.setChecked(display.get("fullscreen", False))
        self.resizable_check.setChecked(display.get("resizable", True))
        
        scaling_mode = display.get("scaling_mode", "stretch")
        index = self.scaling_mode_combo.findText(scaling_mode)
        if index >= 0:
            self.scaling_mode_combo.setCurrentIndex(index)
        
        scaling_filter = display.get("scaling_filter", "linear")
        index = self.scaling_filter_combo.findText(scaling_filter)
        if index >= 0:
            self.scaling_filter_combo.setCurrentIndex(index)
        
        # Audio
        audio = config.get("settings", {}).get("audio", {})
        self.master_volume_spin.setValue(audio.get("master_volume", 1.0))
        self.music_volume_spin.setValue(audio.get("music_volume", 0.8))
        self.sfx_volume_spin.setValue(audio.get("sfx_volume", 1.0))
        
        # Input
        input_settings = config.get("settings", {}).get("input", {})
        self.deadzone_spin.setValue(input_settings.get("deadzone", 0.2))
        
        # Physics
        physics = config.get("settings", {}).get("physics", {})
        gravity = physics.get("gravity", [0, 980])
        self.gravity_x_spin.setValue(gravity[0] if len(gravity) > 0 else 0)
        self.gravity_y_spin.setValue(gravity[1] if len(gravity) > 1 else 980)
        self.timestep_spin.setValue(physics.get("timestep", 0.016666))
        
        # Export
        export_settings = config.get("export", {})
        self.icon_path_edit.setText(export_settings.get("icon", "icon.png"))
        
        platforms = export_settings.get("platforms", ["windows", "linux", "mac"])
        self.windows_check.setChecked("windows" in platforms)
        self.linux_check.setChecked("linux" in platforms)
        self.mac_check.setChecked("mac" in platforms)

    def save_settings(self):
        """Save settings and close dialog"""
        try:
            # Update settings from UI
            self.settings["name"] = self.project_name_edit.text()
            self.settings["description"] = self.project_description_edit.text()
            self.settings["version"] = self.project_version_edit.text()
            self.settings["main_scene"] = self.main_scene_edit.text()

            # Ensure settings structure exists
            if "settings" not in self.settings:
                self.settings["settings"] = {}

            # Display settings
            if "display" not in self.settings["settings"]:
                self.settings["settings"]["display"] = {}

            display = self.settings["settings"]["display"]
            display["width"] = self.window_width_spin.value()
            display["height"] = self.window_height_spin.value()
            display["fullscreen"] = self.fullscreen_check.isChecked()
            display["resizable"] = self.resizable_check.isChecked()
            display["scaling_mode"] = self.scaling_mode_combo.currentText()
            display["scaling_filter"] = self.scaling_filter_combo.currentText()

            # Audio settings
            if "audio" not in self.settings["settings"]:
                self.settings["settings"]["audio"] = {}

            audio = self.settings["settings"]["audio"]
            audio["master_volume"] = self.master_volume_spin.value()
            audio["music_volume"] = self.music_volume_spin.value()
            audio["sfx_volume"] = self.sfx_volume_spin.value()

            # Input settings
            if "input" not in self.settings["settings"]:
                self.settings["settings"]["input"] = {}

            input_settings = self.settings["settings"]["input"]
            input_settings["deadzone"] = self.deadzone_spin.value()

            # Physics settings
            if "physics" not in self.settings["settings"]:
                self.settings["settings"]["physics"] = {}

            physics = self.settings["settings"]["physics"]
            physics["gravity"] = [self.gravity_x_spin.value(), self.gravity_y_spin.value()]
            physics["timestep"] = self.timestep_spin.value()

            # Export settings
            if "export" not in self.settings:
                self.settings["export"] = {}

            export_settings = self.settings["export"]
            export_settings["icon"] = self.icon_path_edit.text()

            platforms = []
            if self.windows_check.isChecked():
                platforms.append("windows")
            if self.linux_check.isChecked():
                platforms.append("linux")
            if self.mac_check.isChecked():
                platforms.append("mac")
            export_settings["platforms"] = platforms

            # Save to project file
            self.project.config = self.settings
            self.project.save_project()

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project settings:\n{str(e)}")

    def reset_to_defaults(self):
        """Reset all settings to default values"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Reset to default configuration
            self.settings = {
                "name": self.project.config.get("name", ""),
                "description": "",
                "version": "1.0.0",
                "engine_version": "1.0.0",
                "main_scene": "",
                "settings": {
                    "display": {
                        "width": 1920,
                        "height": 1080,
                        "fullscreen": False,
                        "resizable": True,
                        "scaling_mode": "stretch",
                        "scaling_filter": "linear"
                    },
                    "audio": {
                        "master_volume": 1.0,
                        "music_volume": 0.8,
                        "sfx_volume": 1.0
                    },
                    "input": {
                        "deadzone": 0.2
                    },
                    "physics": {
                        "gravity": [0, 980],
                        "timestep": 0.016666
                    }
                },
                "export": {
                    "platforms": ["windows", "linux", "mac"],
                    "icon": "icon.png"
                }
            }

            # Reload UI with default values
            self.load_settings()

    def connect_signals(self):
        """Connect UI signals for validation and updates"""
        # Connect validation signals
        self.project_name_edit.textChanged.connect(self.validate_form)
        self.window_width_spin.valueChanged.connect(self.validate_form)
        self.window_height_spin.valueChanged.connect(self.validate_form)

        # Connect preset buttons for common resolutions
        self.add_resolution_presets()

    def add_resolution_presets(self):
        """Add preset buttons for common resolutions"""
        # Find the display tab and add preset buttons
        display_tab = self.tab_widget.widget(1)  # Display is the second tab
        if display_tab:
            layout = display_tab.layout()

            # Create preset group
            preset_group = QGroupBox("Resolution Presets")
            preset_layout = QHBoxLayout(preset_group)

            presets = [
                ("HD", 1280, 720),
                ("Full HD", 1920, 1080),
                ("2K", 2560, 1440),
                ("4K", 3840, 2160)
            ]

            for name, width, height in presets:
                btn = QPushButton(f"{name}\n{width}x{height}")
                btn.clicked.connect(lambda _, w=width, h=height: self.set_resolution(w, h))
                preset_layout.addWidget(btn)

            # Insert before the help text
            layout.insertWidget(2, preset_group)

    def set_resolution(self, width: int, height: int):
        """Set resolution from preset"""
        self.window_width_spin.setValue(width)
        self.window_height_spin.setValue(height)

    def validate_form(self):
        """Validate form inputs and enable/disable save button"""
        valid = True

        # Check project name
        if not self.project_name_edit.text().strip():
            valid = False

        # Check resolution
        if self.window_width_spin.value() < 320 or self.window_height_spin.value() < 240:
            valid = False

        self.save_btn.setEnabled(valid)

    def get_current_settings_summary(self):
        """Get a summary of current settings for display"""
        display = self.settings.get("settings", {}).get("display", {})
        return (
            f"Resolution: {display.get('width', 1920)}x{display.get('height', 1080)}\n"
            f"Scaling: {display.get('scaling_mode', 'stretch')} ({display.get('scaling_filter', 'linear')})\n"
            f"Fullscreen: {'Yes' if display.get('fullscreen', False) else 'No'}"
        )
