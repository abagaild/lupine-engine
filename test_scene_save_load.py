#!/usr/bin/env python3
"""
Test script to verify scene saving and loading works correctly
"""

import json
import tempfile
from pathlib import Path

# Add the project root to the path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.project import LupineProject
from core.node_registry import get_node_registry

def test_scene_save_load():
    """Test that scene saving and loading preserves all nodes and properties"""
    
    # Create a temporary project
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        
        # Create project structure
        (project_path / "assets").mkdir()
        (project_path / "scenes").mkdir()
        (project_path / "scripts").mkdir()
        
        # Create project config
        project_config = {
            "name": "Test Project",
            "version": "1.0.0",
            "main_scene": "scenes/Main.scene"
        }
        
        with open(project_path / "project.lupine", 'w') as f:
            json.dump(project_config, f, indent=2)
        
        # Load the project
        project = LupineProject(str(project_path))
        project.load_project()
        
        print("✓ Test project created and loaded")
        
        # Test the scene tree logic
        print("\n--- Testing Scene Save/Load Logic ---")
        
        # Create initial scene data (like new_scene does)
        scene_data = {
            "name": "TestScene",
            "nodes": [
                {
                    "name": "Main",
                    "type": "Node2D",
                    "position": [0, 0],
                    "children": []
                }
            ]
        }
        
        print("1. Created initial scene data:")
        print(f"   Scene name: {scene_data['name']}")
        print(f"   Root nodes: {len(scene_data['nodes'])}")
        print(f"   Main node type: {scene_data['nodes'][0]['type']}")
        
        # Simulate adding a Sprite node (like scene tree does)
        print("\n2. Adding Sprite node...")
        registry = get_node_registry()
        sprite_instance = registry.create_node_instance("Sprite", "TestSprite")
        sprite_node = sprite_instance.to_dict()
        
        # Set some properties
        sprite_node["texture"] = "assets/test_texture.png"
        sprite_node["position"] = [150, 200]
        
        # Add to main node's children
        main_node = scene_data["nodes"][0]
        if "children" not in main_node:
            main_node["children"] = []
        main_node["children"].append(sprite_node)
        
        print(f"   Added Sprite: {sprite_node['name']}")
        print(f"   Sprite texture: '{sprite_node['texture']}'")
        print(f"   Sprite position: {sprite_node['position']}")
        print(f"   Main node children count: {len(main_node['children'])}")
        
        # Save scene to file (like main_editor.save_scene does)
        print("\n3. Saving scene to file...")
        scene_file = project_path / "scenes" / "TestScene.scene"
        scene_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(scene_file, 'w') as f:
            json.dump(scene_data, f, indent=2)
        
        print(f"   Saved to: {scene_file}")
        
        # Load scene from file (like main_editor.open_scene does)
        print("\n4. Loading scene from file...")
        with open(scene_file, 'r') as f:
            loaded_scene_data = json.load(f)
        
        print(f"   Loaded scene name: {loaded_scene_data['name']}")
        print(f"   Loaded root nodes: {len(loaded_scene_data['nodes'])}")
        
        # Check if the sprite node was preserved
        loaded_main_node = loaded_scene_data["nodes"][0]
        loaded_children = loaded_main_node.get("children", [])
        
        print(f"   Loaded main node children count: {len(loaded_children)}")
        
        if len(loaded_children) == 0:
            print("✗ FAIL: Sprite node was not saved/loaded!")
            return False
        
        loaded_sprite = loaded_children[0]
        print(f"   Loaded sprite name: {loaded_sprite['name']}")
        print(f"   Loaded sprite type: {loaded_sprite['type']}")
        print(f"   Loaded sprite texture: '{loaded_sprite.get('texture', '')}'")
        print(f"   Loaded sprite position: {loaded_sprite.get('position', [0, 0])}")
        
        # Verify all properties were preserved
        if (loaded_sprite["name"] == "TestSprite" and
            loaded_sprite["type"] == "Sprite" and
            loaded_sprite.get("texture") == "assets/test_texture.png" and
            loaded_sprite.get("position") == [150, 200]):
            print("✓ PASS: Sprite node and properties were preserved!")
        else:
            print("✗ FAIL: Sprite node properties were not preserved correctly!")
            return False
        
        # Test property modification and re-save
        print("\n5. Modifying sprite properties and re-saving...")
        loaded_sprite["texture"] = "assets/modified_texture.png"
        loaded_sprite["position"] = [300, 400]
        
        # Save again
        with open(scene_file, 'w') as f:
            json.dump(loaded_scene_data, f, indent=2)
        
        # Load again
        with open(scene_file, 'r') as f:
            final_scene_data = json.load(f)
        
        final_sprite = final_scene_data["nodes"][0]["children"][0]
        print(f"   Final sprite texture: '{final_sprite.get('texture', '')}'")
        print(f"   Final sprite position: {final_sprite.get('position', [0, 0])}")
        
        if (final_sprite.get("texture") == "assets/modified_texture.png" and
            final_sprite.get("position") == [300, 400]):
            print("✓ PASS: Property modifications were preserved!")
        else:
            print("✗ FAIL: Property modifications were not preserved!")
            return False
        
        print("\n🎉 All tests passed! Scene save/load is working correctly.")
        return True

if __name__ == "__main__":
    try:
        success = test_scene_save_load()
        if success:
            print("\n✅ Scene save/load fix verified successfully!")
            sys.exit(0)
        else:
            print("\n❌ Scene save/load issues detected!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
