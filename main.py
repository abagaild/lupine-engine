#!/usr/bin/env python3
"""
Lupine Engine - Main Entry Point
A powerful game engine combining the flexibility of Godot/Unreal with the ease of Ren'py/RPG Maker
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up global exception handling BEFORE importing anything else
from core.exception_handler import setup_global_exception_handling
setup_global_exception_handling()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from editor.ui.theme import LupineTheme
from editor.project_manager.project_manager import ProjectManager


def main():
    """Main entry point for Lupine Engine"""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Lupine Engine")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Lupine Studios")

    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Apply theme
    LupineTheme.apply_theme(app)

    # Create and show project manager
    project_manager = ProjectManager()
    project_manager.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
