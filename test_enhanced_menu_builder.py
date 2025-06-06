#!/usr/bin/env python3
"""
Test script for the enhanced Menu/HUD Builder
Tests undo/redo, clipboard, animation support, and scene templates
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from core.project import LupineProject
from editor.menu_hud_builder import MenuHudBuilderWindow


def test_enhanced_menu_builder():
    """Test the enhanced menu/HUD builder functionality"""
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create a test project
    project_path = project_root / "test_project"
    project = LupineProject(str(project_path))
    
    if not project.load_project():
        print("Warning: Could not load test project, creating minimal project")
        # Create minimal project structure for testing
        project.config = {
            "name": "Test Project",
            "version": "1.0.0",
            "main_scene": "scenes/Main.scene"
        }
    
    # Create and show the enhanced menu builder window
    builder_window = MenuHudBuilderWindow(project)
    builder_window.show()
    
    print("Enhanced Menu/HUD Builder Test")
    print("=" * 40)
    print("Features to test:")
    print("1. Undo/Redo (Ctrl+Z, Ctrl+Y)")
    print("   - Add some UI elements")
    print("   - Move them around")
    print("   - Test undo/redo functionality")
    print()
    print("2. Clipboard Operations (Ctrl+C, Ctrl+X, Ctrl+V)")
    print("   - Select a UI element")
    print("   - Copy it with Ctrl+C")
    print("   - Paste it with Ctrl+V")
    print()
    print("3. Animation Settings")
    print("   - Select a UI element")
    print("   - Go to the 'Animations' tab")
    print("   - Set animations for different events")
    print()
    print("4. Create New Scene Templates")
    print("   - Use File > Create New menu")
    print("   - Try 'New Menu Scene', 'New Dialogue Scene', etc.")
    print("   - UI elements should be positioned in world space")
    print("   - follow_viewport elements should move with camera")
    print()
    print("5. Drag and Drop")
    print("   - Drag prefabs from the library to the scene")
    print("   - Test different UI element types")
    print("   - UI should render at correct world positions")
    print()
    print("6. World Space UI Positioning")
    print("   - UI elements use world space coordinates")
    print("   - follow_viewport maintains relative position to camera")
    print("   - No complex UI positioning logic")
    print()
    print("Press Ctrl+C to exit the test")
    
    # Run the application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    test_enhanced_menu_builder()
