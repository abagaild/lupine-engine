"""
Simple Game Runner Script
Uses the new streamlined game engine for running games
"""

import sys
from pathlib import Path
from typing import Optional

# Set up global exception handling early
try:
    from .exception_handler import setup_global_exception_handling
    setup_global_exception_handling()
except ImportError:
    # Handle case when run as script directly
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from core.exception_handler import setup_global_exception_handling
    setup_global_exception_handling()

# Add the project root to Python path
def setup_paths(project_path: str, lupine_engine_path: str):
    """Setup Python paths for the game runner"""
    sys.path.insert(0, lupine_engine_path)
    sys.path.insert(0, project_path)

def run_game(project_path: str, scene_path: str, lupine_engine_path: Optional[str] = None):
    """Run a game with the specified project and scene"""

    print(f"[SIMPLE_GAME_RUNNER] run_game called")
    print(f"[SIMPLE_GAME_RUNNER] project_path: {project_path}")
    print(f"[SIMPLE_GAME_RUNNER] scene_path: {scene_path}")
    print(f"[SIMPLE_GAME_RUNNER] lupine_engine_path: {lupine_engine_path}")

    # Auto-detect lupine engine path if not provided
    if lupine_engine_path is None:
        # Assume this script is in core/ directory of lupine engine
        lupine_engine_path = str(Path(__file__).parent.parent)
        print(f"[SIMPLE_GAME_RUNNER] Auto-detected engine path: {lupine_engine_path}")

    # Setup paths
    print(f"[SIMPLE_GAME_RUNNER] Setting up paths...")
    setup_paths(project_path, lupine_engine_path)
    print(f"[SIMPLE_GAME_RUNNER] Paths set up successfully")

    try:
        # Import the game engine
        print(f"[SIMPLE_GAME_RUNNER] Importing LupineGameEngine...")
        from core.game_engine import LupineGameEngine
        print(f"[SIMPLE_GAME_RUNNER] Successfully imported LupineGameEngine")

        print(f"[GAME] Starting Lupine Game Engine")
        print(f"[GAME] Project: {project_path}")
        print(f"[GAME] Scene: {scene_path}")
        print(f"[GAME] Engine: {lupine_engine_path}")
        print("-" * 50)

        # Create and run the game engine
        print(f"[SIMPLE_GAME_RUNNER] Creating LupineGameEngine instance...")
        engine = LupineGameEngine(project_path, scene_path)
        print(f"[SIMPLE_GAME_RUNNER] LupineGameEngine created, calling run()...")
        engine.run()

        print("[GAME] Game finished successfully")

    except KeyboardInterrupt:
        print("\n[GAME] Game interrupted by user")
    except Exception as e:
        print(f"[ERROR] Error running game: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def main():
    """Main entry point for the game runner"""
    if len(sys.argv) < 3:
        print("Usage: python simple_game_runner.py <project_path> <scene_path> [lupine_engine_path]")
        print("Example: python simple_game_runner.py /path/to/project scenes/Main.scene")
        return 1
    
    project_path = sys.argv[1]
    scene_path = sys.argv[2]
    lupine_engine_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    return run_game(project_path, scene_path, lupine_engine_path)

if __name__ == "__main__":
    sys.exit(main())
