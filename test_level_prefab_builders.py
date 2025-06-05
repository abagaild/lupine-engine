"""
Test script for Level Builder and Prefab Builder
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from core.project import LupineProject


def create_test_project():
    """Create a test project"""
    project_path = project_root / "test_project"
    if not project_path.exists():
        project_path.mkdir()

        # Create project structure
        (project_path / "scenes").mkdir(exist_ok=True)
        (project_path / "scripts").mkdir(exist_ok=True)
        (project_path / "levels").mkdir(exist_ok=True)
        (project_path / "prefabs").mkdir(exist_ok=True)
        (project_path / "data").mkdir(exist_ok=True)
        (project_path / "data" / "script_blocks").mkdir(exist_ok=True)
        (project_path / "nodes").mkdir(exist_ok=True)

        # Create project config
        project_config = {
            "name": "Test Project",
            "description": "Test project for Level and Prefab Builders",
            "version": "1.0.0",
            "engine_version": "1.0.0",
            "main_scene": "",
            "settings": {
                "display": {
                    "width": 1920,
                    "height": 1080,
                    "fullscreen": False
                }
            }
        }

        import json
        with open(project_path / "project.lupine", 'w') as f:
            json.dump(project_config, f, indent=2)

    return str(project_path)


def test_level_builder():
    """Test the Level Builder"""
    try:
        from editor.level_builder import LevelBuilderWindow

        project_path = create_test_project()
        project = LupineProject(project_path)
        project.load_project()

        level_builder = LevelBuilderWindow(project)
        level_builder.show()

        print("✓ Level Builder created successfully!")
        return level_builder

    except Exception as e:
        print(f"✗ Level Builder failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_prefab_builder():
    """Test the Prefab Builder"""
    try:
        from editor.prefab_builder import PrefabBuilderWindow

        project_path = create_test_project()
        project = LupineProject(project_path)
        project.load_project()

        prefab_builder = PrefabBuilderWindow(project)
        prefab_builder.show()

        print("✓ Prefab Builder created successfully!")
        return prefab_builder

    except Exception as e:
        print(f"✗ Prefab Builder failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_level_to_scene_export():
    """Test exporting levels to scene files"""
    try:
        from core.level.level_manager import LevelManager
        from core.level.level_system import Level, LevelEvent, EventTrigger
        import uuid

        project_path = create_test_project()
        level_manager = LevelManager(project_path)

        # Create a test level
        level = level_manager.create_level("TestLevel", 10, 8)

        # Add some test events
        event1 = LevelEvent(
            id=str(uuid.uuid4()),
            name="NPC",
            position=(2, 3),
            trigger=EventTrigger.PLAYER_INTERACT,
            raw_script='''
def on_interact(player):
    print("Hello, player!")
'''
        )

        event2 = LevelEvent(
            id=str(uuid.uuid4()),
            name="Chest",
            position=(5, 6),
            trigger=EventTrigger.PLAYER_INTERACT,
            raw_script='''
def on_interact(player):
    print("You found a treasure!")
'''
        )

        level.add_event(event1)
        level.add_event(event2)

        # Save the level
        level_manager.save_level(level)

        print("✓ Test level created and saved successfully!")

        # Test export to scene
        scene_data = export_level_to_scene(level)

        # Save as scene file
        scene_path = Path(project_path) / "scenes" / f"{level.name}.scene"
        with open(scene_path, 'w') as f:
            import json
            json.dump(scene_data, f, indent=2)

        print(f"✓ Level exported to scene file: {scene_path}")
        return True

    except Exception as e:
        print(f"✗ Level to scene export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def export_level_to_scene(level):
    """Export a level to standard scene format"""
    scene_data = {
        "name": level.name,
        "nodes": []
    }

    # Create root node
    root_node = {
        "name": level.name,
        "type": "Node2D",
        "position": [0, 0],
        "children": []
    }

    # Add level background if any
    if level.background_image:
        bg_node = {
            "name": "Background",
            "type": "Sprite2D",
            "position": [0, 0],
            "texture": level.background_image,
            "children": []
        }
        root_node["children"].append(bg_node)

    # Convert events to scene nodes
    for layer in level.layers:
        if not layer.visible:
            continue

        # Create layer node
        layer_node = {
            "name": f"Layer_{layer.name}",
            "type": "Node2D",
            "position": [0, 0],
            "children": []
        }

        # Add events as child nodes
        for event in layer.events:
            event_node = {
                "name": event.name,
                "type": "Area2D",  # Most events are interactive areas
                "position": [
                    event.position[0] * level.cell_size,
                    event.position[1] * level.cell_size
                ],
                "children": []
            }

            # Add collision shape
            collision_node = {
                "name": "CollisionShape2D",
                "type": "CollisionShape2D",
                "position": [0, 0],
                "shape": "rectangle",
                "size": [
                    event.size[0] * level.cell_size,
                    event.size[1] * level.cell_size
                ],
                "children": []
            }
            event_node["children"].append(collision_node)

            # Add sprite if specified
            if event.sprite_texture:
                sprite_node = {
                    "name": "Sprite",
                    "type": "Sprite2D",
                    "position": [0, 0],
                    "texture": event.sprite_texture,
                    "children": []
                }
                event_node["children"].append(sprite_node)

            # Add script if any
            if event.raw_script:
                # Convert event script to node script format
                node_script = f'''# Event: {event.name}
# Trigger: {event.trigger.value}

{event.raw_script}

# Event trigger handling
def _ready():
    if hasattr(self, 'body_entered'):
        body_entered.connect(_on_body_entered)

def _on_body_entered(body):
    if body.name == "Player":
        if hasattr(self, 'on_interact'):
            on_interact(body)
'''

                # Save script to file
                script_filename = f"{event.name}_{event.id[:8]}.py"
                event_node["script"] = f"scripts/{script_filename}"

                # Note: In a full implementation, we would save the script file here

            # Add event metadata
            event_node["event_data"] = {
                "trigger": event.trigger.value,
                "through": event.through,
                "visible": event.visible,
                "notes": event.notes,
                "tags": event.tags
            }

            layer_node["children"].append(event_node)

        if layer_node["children"]:  # Only add layer if it has events
            root_node["children"].append(layer_node)

    scene_data["nodes"].append(root_node)
    return scene_data


if __name__ == "__main__":
    print("Testing Level Builder and Prefab Builder...")

    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # Test components
    print("\n1. Testing Level Builder...")
    level_builder = test_level_builder()

    print("\n2. Testing Prefab Builder...")
    prefab_builder = test_prefab_builder()

    print("\n3. Testing Level to Scene Export...")
    export_success = test_level_to_scene_export()

    if level_builder and prefab_builder and export_success:
        print("\n✓ All tests passed!")
        print("\nBoth tools are now running. You can test:")
        print("- Level Builder: Create levels, place events, visual scripting")
        print("- Prefab Builder: Create prefabs, define properties, visual scripts")
        print("- Level Export: Levels can be exported to standard scene files")

        # Run the application
        sys.exit(app.exec())
    else:
        print("\n✗ Some tests failed. Check the errors above.")
        sys.exit(1)
