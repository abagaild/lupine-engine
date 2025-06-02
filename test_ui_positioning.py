#!/usr/bin/env python3
"""
Test script to verify UI positioning works correctly between scene view and game runner.
This script runs the test_anchor_ui.json scene to check if UI elements appear in the correct positions.
"""

import sys
import os
from pathlib import Path

# Add the current directory to sys.path so we can import from the engine
sys.path.insert(0, str(Path(__file__).parent))

# Import the game runner components
from editor.game_runner import LupineGameWindow

def main():
    """Run the anchor test scene"""
    try:
        # Get the current directory as project path
        project_path = str(Path(__file__).parent)
        scene_file = str(Path(__file__).parent / "test_anchor_ui.json")
        
        print(f"Project path: {project_path}")
        print(f"Scene file: {scene_file}")
        
        # Check if scene file exists
        if not Path(scene_file).exists():
            print(f"ERROR: Scene file not found: {scene_file}")
            return
        
        # Create game window
        game = LupineGameWindow(project_path)
        
        # Override the load_scene method to use our specific scene file
        def load_test_scene():
            print("Loading test scene...")
            try:
                import json
                with open(scene_file, 'r') as f:
                    game.scene_data = json.load(f)
                print(f"Loaded scene: {game.scene_data.get('scene_name', 'Unknown')}")
                print(f"Scene nodes: {len(game.scene_data.get('nodes', []))}")
                
                # Try to load using Scene class
                try:
                    from core.scene import Scene
                    game.scene = Scene.load_from_file(scene_file)
                    print(f"Scene object loaded successfully! Root nodes: {len(game.scene.root_nodes)}")
                    game.setup_scene()
                except Exception as scene_error:
                    print(f"Failed to load Scene object: {scene_error}")
                    import traceback
                    traceback.print_exc()
                    print("Falling back to basic scene rendering")
                    game.scene = None
                    
            except Exception as e:
                print(f"Error loading test scene: {e}")
                import traceback
                traceback.print_exc()
        
        # Replace the load_scene method
        game.load_scene = load_test_scene
        
        # Setup and run the game
        game.setup()
        print("\n" + "="*50)
        print("ANCHOR TEST SCENE RUNNING")
        print("Expected UI elements:")
        print("1. MainPanel at (50, 50) with size 400x300 - blue panel")
        print("2. TitleLabel stretched across top - 'Anchor Test Panel'")
        print("3. CenterButton in center - 'Centered'")
        print("4. BottomRightButton in bottom-right - 'Bottom Right'")
        print("="*50)
        print("Press ESC to exit")
        print("="*50 + "\n")
        
        game.run()
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
