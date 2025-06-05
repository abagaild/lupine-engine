#!/usr/bin/env python3
"""
Test script for the Enhanced Visual Script Editor
Demonstrates the Blueprint-style visual scripting functionality
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

def main():
    """Main function to test the visual script editor"""
    app = QApplication(sys.argv)
    app.setApplicationName("Lupine Engine - Visual Script Editor Test")
    
    try:
        # Import the enhanced visual script editor
        from editor.ui.enhanced_visual_script_editor import EnhancedVisualScriptEditor
        
        # Create a mock project for testing
        class MockProject:
            def __init__(self):
                self.project_path = project_root
            
            def get_absolute_path(self, relative_path: str) -> Path:
                return self.project_path / relative_path
        
        # Create the editor
        mock_project = MockProject()
        editor = EnhancedVisualScriptEditor(mock_project)
        
        # Show the editor
        editor.show()
        
        print("Enhanced Visual Script Editor opened successfully!")
        print("Features available:")
        print("- Blueprint-style visual scripting")
        print("- Drag and drop blocks from library")
        print("- Connect blocks with execution and data flows")
        print("- Real-time Python code generation")
        print("- Save/load visual scripts")
        print("- Export to Python files")
        print("- Component blocks for data input (String, Integer, Float, Boolean, etc.)")
        print("- Math and comparison blocks")
        print("- Direct input editing in blocks")
        print("- Keyboard shortcuts (Ctrl+Z/Y, Ctrl+C/V, Del)")
        print("")
        print("Instructions:")
        print("1. Drag blocks from the Block Library on the left")
        print("2. Connect blocks by clicking on their pins")
        print("3. Edit values directly in input blocks")
        print("4. Use the 'Generated Code' tab to see Python output")
        print("5. Save your visual script using File > Save")
        print("6. Export to Python using File > Export to Python")
        print("")
        print("Keyboard Shortcuts:")
        print("- Ctrl+Z: Undo")
        print("- Ctrl+Y: Redo")
        print("- Ctrl+C: Copy selected block")
        print("- Ctrl+V: Paste block")
        print("- Del: Delete selected block")
        print("- Ctrl+A: Select all blocks")
        
        # Run the application
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure PyQt6 is installed: pip install PyQt6")
        return 1
    except Exception as e:
        print(f"Error starting visual script editor: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()
