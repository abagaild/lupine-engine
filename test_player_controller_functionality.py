#!/usr/bin/env python3
"""
Test script to verify PlayerController prefab functionality
"""

import sys
import os
import tempfile
import json
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_player_controller_instantiation():
    """Test that PlayerController can be instantiated from prefab"""
    print("Testing PlayerController instantiation...")
    
    try:
        from core.scene import Node
        from core.node_registry import get_node_registry
        
        # Create a temporary project for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"

            # Create full project structure
            from core.project import LupineProject
            project = LupineProject(str(project_path))
            project.create_new_project("Test Project", "Test Description")

            # This will copy all node definitions including KinematicBody2D
            prefabs_dir = project_path / "prefabs"

            # Set up node registry with project path
            registry = get_node_registry(project_path)

            # Load PlayerController prefab
            player_controller_json = prefabs_dir / "PlayerController.json"
            if not player_controller_json.exists():
                print("❌ PlayerController.json not found")
                return False
            
            with open(player_controller_json, 'r') as f:
                prefab_data = json.load(f)
            
            # Create PlayerController instance
            player_controller = Node.from_dict(prefab_data)
            
            if player_controller is None:
                print("❌ Failed to create PlayerController instance")
                return False
            
            print("✅ PlayerController instance created successfully")
            
            # Check basic properties
            if player_controller.name == "PlayerController":
                print("✅ PlayerController has correct name")
            else:
                print(f"❌ PlayerController has wrong name: {player_controller.name}")
                return False
            
            if player_controller.type == "KinematicBody2D":
                print("✅ PlayerController has correct type")
            else:
                print(f"❌ PlayerController has wrong type: {player_controller.type}")
                return False
            
            # Check children
            expected_children = ["Sprite", "CollisionShape", "InteractionArea"]
            actual_children = [child.name for child in player_controller.children]
            
            for expected_child in expected_children:
                if expected_child in actual_children:
                    print(f"✅ Found expected child: {expected_child}")
                else:
                    print(f"❌ Missing expected child: {expected_child}")
                    return False
            
            # Check that children have correct types
            sprite_child = next((child for child in player_controller.children if child.name == "Sprite"), None)
            if sprite_child and sprite_child.type == "Sprite":
                print("✅ Sprite child has correct type")
            else:
                print("❌ Sprite child missing or wrong type")
                return False
            
            collision_child = next((child for child in player_controller.children if child.name == "CollisionShape"), None)
            if collision_child and collision_child.type == "CollisionShape2D":
                print("✅ CollisionShape child has correct type")
            else:
                print("❌ CollisionShape child missing or wrong type")
                return False
            
            area_child = next((child for child in player_controller.children if child.name == "InteractionArea"), None)
            if area_child and area_child.type == "Area2D":
                print("✅ InteractionArea child has correct type")
            else:
                print("❌ InteractionArea child missing or wrong type")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ PlayerController instantiation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_player_controller_properties():
    """Test that PlayerController has expected properties"""
    print("\nTesting PlayerController properties...")
    
    try:
        from core.scene import Node
        
        # Load PlayerController prefab
        prefab_json = Path("prefabs/PlayerController.json")
        if not prefab_json.exists():
            print("❌ PlayerController.json not found in engine")
            return False
        
        with open(prefab_json, 'r') as f:
            prefab_data = json.load(f)
        
        # Create PlayerController instance
        player_controller = Node.from_dict(prefab_data)
        
        # Debug: Print all available attributes
        print(f"PlayerController type: {type(player_controller)}")
        print(f"PlayerController attributes: {[attr for attr in dir(player_controller) if not attr.startswith('_')]}")

        # Check physics properties
        expected_properties = {
            "collision_layer": 2,
            "collision_mask": 1,
            "safe_margin": 0.08
        }

        for prop_name, expected_value in expected_properties.items():
            if hasattr(player_controller, prop_name):
                actual_value = getattr(player_controller, prop_name)
                if actual_value == expected_value:
                    print(f"✅ {prop_name}: {actual_value}")
                else:
                    print(f"❌ {prop_name}: expected {expected_value}, got {actual_value}")
                    return False
            else:
                # Check if it's in properties dictionary
                if hasattr(player_controller, 'properties') and prop_name in player_controller.properties:
                    actual_value = player_controller.properties[prop_name]
                    if actual_value == expected_value:
                        print(f"✅ {prop_name} (in properties): {actual_value}")
                    else:
                        print(f"❌ {prop_name} (in properties): expected {expected_value}, got {actual_value}")
                        return False
                else:
                    print(f"❌ Missing property: {prop_name}")
                    print(f"   Available properties: {getattr(player_controller, 'properties', {})}")
                    return False
        
        # Check script path
        if hasattr(player_controller, 'script_path'):
            if player_controller.script_path == "prefabs/PlayerController.lsc":
                print("✅ Script path is correct")
            else:
                print(f"❌ Wrong script path: {player_controller.script_path}")
                return False
        else:
            print("❌ Missing script_path property")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ PlayerController properties test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_player_controllers():
    """Test that multiple PlayerController instances are unique"""
    print("\nTesting multiple PlayerController instances...")
    
    try:
        from core.scene import Node
        
        # Load PlayerController prefab
        prefab_json = Path("prefabs/PlayerController.json")
        if not prefab_json.exists():
            print("❌ PlayerController.json not found in engine")
            return False
        
        with open(prefab_json, 'r') as f:
            prefab_data = json.load(f)
        
        # Create two PlayerController instances
        player1_data = prefab_data.copy()
        player1_data["name"] = "Player1"
        player1_data["position"] = [100, 100]
        
        player2_data = prefab_data.copy()
        player2_data["name"] = "Player2"
        player2_data["position"] = [200, 200]
        
        player1 = Node.from_dict(player1_data)
        player2 = Node.from_dict(player2_data)
        
        # Check that they have different names
        if player1.name != player2.name:
            print("✅ Players have different names")
        else:
            print("❌ Players have same name")
            return False
        
        # Check that they have different positions
        if hasattr(player1, 'position') and hasattr(player2, 'position'):
            if player1.position != player2.position:
                print("✅ Players have different positions")
            else:
                print("❌ Players have same position")
                return False
        
        # Test that modifying one doesn't affect the other
        if hasattr(player1, 'position'):
            original_player2_position = player2.position.copy() if hasattr(player2, 'position') else None
            player1.position[0] = 999
            
            if original_player2_position and player2.position == original_player2_position:
                print("✅ Modifying player1 position doesn't affect player2")
            else:
                print("❌ Modifying player1 position affected player2")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Multiple PlayerController test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all PlayerController functionality tests"""
    print("=" * 60)
    print("LUPINE ENGINE PLAYERCONTROLLER FUNCTIONALITY TEST")
    print("=" * 60)
    
    tests = [
        test_player_controller_instantiation,
        test_player_controller_properties,
        test_multiple_player_controllers
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All PlayerController functionality tests passed!")
        print("\n✅ PlayerController Features Verified:")
        print("  • Proper instantiation from prefab JSON")
        print("  • Correct node hierarchy (KinematicBody2D with children)")
        print("  • Physics properties (collision layers, safe margin)")
        print("  • Script path assignment")
        print("  • Multiple instance uniqueness")
        print("  • Property isolation between instances")
        return True
    else:
        print("❌ Some PlayerController functionality tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
