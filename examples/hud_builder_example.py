"""
Example: Using the Menu and HUD Builder
Demonstrates how to create a simple game HUD with health bar, score display, and menu buttons
"""

import sys
from pathlib import Path

# Add the engine root to the path
engine_root = Path(__file__).parent.parent
sys.path.insert(0, str(engine_root))

from PyQt6.QtWidgets import QApplication
from core.project import LupineProject
from editor.menu_hud_builder import MenuHudBuilder
from core.ui.ui_prefabs import get_prefab
from core.ui.variable_binding import VariableBinding, BindingType, get_binding_manager
from core.globals.variables_manager import initialize_variables_manager


def create_sample_hud():
    """Create a sample HUD layout programmatically"""
    
    # Initialize variable system
    project_path = engine_root / "examples" / "sample_project"
    variables_manager = initialize_variables_manager(str(project_path))
    
    # Add some sample global variables
    variables_manager.add_variable("player_health", "int", 85, "Player's current health")
    variables_manager.add_variable("player_max_health", "int", 100, "Player's maximum health")
    variables_manager.add_variable("player_score", "int", 1250, "Player's current score")
    variables_manager.add_variable("player_level", "int", 5, "Player's current level")
    
    # Create HUD scene data
    hud_scene = {
        "name": "GameHUD",
        "nodes": [
            {
                "name": "HUD_Root",
                "type": "Control",
                "position": [0, 0],
                "size": [1920, 1080],
                "follow_viewport": True,
                "children": []
            }
        ]
    }
    
    # Add health bar (top-left)
    health_bar_prefab = get_prefab("HealthBar")
    if health_bar_prefab:
        health_bar = health_bar_prefab.create_instance("HealthBar")
        health_bar["position"] = [20, 20]
        health_bar["variable_bindings"] = [
            {
                "binding_type": "progress",
                "variable_name": "player_health",
                "property_name": "value",
                "format_string": "{value}"
            }
        ]
        hud_scene["nodes"][0]["children"].append(health_bar)
    
    # Add score display (top-right)
    score_display_prefab = get_prefab("ScoreDisplay")
    if score_display_prefab:
        score_display = score_display_prefab.create_instance("ScoreDisplay")
        score_display["position"] = [1700, 20]
        score_display["variable_bindings"] = [
            {
                "binding_type": "display",
                "variable_name": "player_score",
                "property_name": "text",
                "format_string": "Score: {value:,}"
            }
        ]
        hud_scene["nodes"][0]["children"].append(score_display)
    
    # Add menu button (bottom-center)
    menu_button_prefab = get_prefab("MenuButton")
    if menu_button_prefab:
        menu_button = menu_button_prefab.create_instance("MenuButton")
        menu_button["position"] = [860, 1000]
        menu_button["text"] = "Main Menu"
        menu_button["event_bindings"] = [
            {
                "event_name": "on_click",
                "code_snippet": "print('Returning to main menu...')\n# change_scene('scenes/main_menu.scene')",
                "audio_file": "sounds/ui_click.wav",
                "enabled": True
            }
        ]
        hud_scene["nodes"][0]["children"].append(menu_button)
    
    return hud_scene


def main():
    """Main function to demonstrate the HUD builder"""
    app = QApplication(sys.argv)
    
    # Create a sample project
    project_path = engine_root / "examples" / "sample_project"
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Create project file if it doesn't exist
    project_file = project_path / "project.lupine"
    if not project_file.exists():
        project_data = {
            "name": "Sample Project",
            "version": "1.0.0",
            "main_scene": "scenes/main.scene",
            "settings": {
                "display": {
                    "width": 1920,
                    "height": 1080,
                    "fullscreen": False
                }
            }
        }
        import json
        with open(project_file, 'w') as f:
            json.dump(project_data, f, indent=2)
    
    # Load the project
    project = LupineProject(str(project_path))
    project.load_project()
    
    # Create the HUD builder
    hud_builder = MenuHudBuilder(project)
    
    # Load the sample HUD
    sample_hud = create_sample_hud()
    hud_builder.preview_widget.set_scene_data(sample_hud)
    
    # Show the builder
    hud_builder.show()
    hud_builder.resize(1200, 800)
    hud_builder.setWindowTitle("Menu and HUD Builder - Sample HUD")
    
    print("🎮 Sample HUD loaded in the builder!")
    print("📝 Features demonstrated:")
    print("   • Health bar with variable binding")
    print("   • Score display with formatting")
    print("   • Menu button with click event")
    print("   • Multi-resolution preview")
    print("   • Variable binding testing")
    print("\n💡 Try these actions:")
    print("   1. Select elements to see their properties")
    print("   2. Go to Variables tab to see bindings")
    print("   3. Go to Events tab to see event handlers")
    print("   4. Test variable bindings with different values")
    print("   5. Change resolution to see responsive behavior")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
