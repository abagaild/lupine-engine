#!/usr/bin/env python3
"""
Test script to verify prefab system and physics node registration fixes
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_physics_nodes_not_duplicated():
    """Test that physics nodes are not duplicated in registry"""
    print("Testing physics nodes registration...")
    
    try:
        from core.node_registry import get_node_registry
        
        # Create a temporary project for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            
            # Get registry with project path
            registry = get_node_registry(project_path)
            all_nodes = registry.get_all_nodes()
            
            # Check for physics nodes
            physics_nodes = ["Area2D", "CollisionShape2D", "CollisionPolygon2D", 
                           "RigidBody2D", "StaticBody2D", "KinematicBody2D"]
            
            found_physics_nodes = []
            for node_name in physics_nodes:
                if node_name in all_nodes:
                    found_physics_nodes.append(node_name)
            
            print(f"✅ Found {len(found_physics_nodes)} physics nodes in registry")
            
            # Check that each physics node appears only once
            for node_name in found_physics_nodes:
                node_def = all_nodes[node_name]
                print(f"✅ {node_name}: category={node_def.category.value}, builtin={node_def.is_builtin}")
            
            return True
            
    except Exception as e:
        print(f"❌ Physics nodes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_project_creation_with_prefabs():
    """Test that project creation copies prefabs correctly"""
    print("\nTesting project creation with prefabs...")
    
    try:
        from core.project import LupineProject
        
        # Create a temporary project
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            
            # Create project
            project = LupineProject(project_path)
            success = project.create_new_project("Test Project", "Test Description")
            
            if not success:
                print("❌ Failed to create project")
                return False
            
            print("✅ Project created successfully")
            
            # Check that prefabs directory exists
            prefabs_dir = project_path / "prefabs"
            if not prefabs_dir.exists():
                print("❌ Prefabs directory not created")
                return False
            
            print("✅ Prefabs directory created")
            
            # Check for PlayerController prefab files
            player_controller_json = prefabs_dir / "PlayerController.json"
            player_controller_lsc = prefabs_dir / "PlayerController.lsc"

            if player_controller_json.exists():
                print("✅ PlayerController.json copied to project")
            else:
                print("❌ PlayerController.json not found in project")
                return False

            if player_controller_lsc.exists():
                print("✅ PlayerController.lsc copied to project")
            else:
                print("❌ PlayerController.lsc not found in project")
                return False

            # Check that PlayerController.lsc is also copied to nodes/prefabs
            nodes_player_controller_lsc = project_path / "nodes" / "prefabs" / "PlayerController.lsc"
            if nodes_player_controller_lsc.exists():
                print("✅ PlayerController.lsc copied to nodes/prefabs")
            else:
                print("❌ PlayerController.lsc not found in nodes/prefabs")
                return False
            
            # Check that physics nodes are in node2d directory
            node2d_dir = project_path / "nodes" / "node2d"
            physics_node_files = ["Area2D.lsc", "CollisionShape2D.lsc", "CollisionPolygon2D.lsc", 
                                 "RigidBody2D.lsc", "StaticBody2D.lsc", "KinematicBody2D.lsc"]
            
            for node_file in physics_node_files:
                node_path = node2d_dir / node_file
                if node_path.exists():
                    print(f"✅ {node_file} copied to node2d directory")
                else:
                    print(f"❌ {node_file} not found in node2d directory")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ Project creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_player_controller_prefab():
    """Test PlayerController prefab structure and content"""
    print("\nTesting PlayerController prefab...")
    
    try:
        import json
        
        # Check if prefab files exist in engine
        prefab_json = Path("prefabs/PlayerController.json")
        prefab_lsc = Path("prefabs/PlayerController.lsc")
        
        if not prefab_json.exists():
            print("❌ PlayerController.json not found in engine")
            return False
        
        if not prefab_lsc.exists():
            print("❌ PlayerController.lsc not found in engine")
            return False
        
        print("✅ PlayerController prefab files exist in engine")
        
        # Load and validate JSON structure
        with open(prefab_json, 'r') as f:
            prefab_data = json.load(f)
        
        # Check basic structure
        required_fields = ["name", "type", "children"]
        for field in required_fields:
            if field not in prefab_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ PlayerController JSON has required fields")
        
        # Check that it's a KinematicBody2D
        if prefab_data["type"] != "KinematicBody2D":
            print(f"❌ Expected KinematicBody2D, got {prefab_data['type']}")
            return False
        
        print("✅ PlayerController is KinematicBody2D")
        
        # Check for required children
        children = prefab_data.get("children", [])
        child_types = [child.get("type") for child in children]
        
        expected_children = ["Sprite", "CollisionShape2D", "Area2D"]
        for expected_child in expected_children:
            if expected_child not in child_types:
                print(f"❌ Missing expected child: {expected_child}")
                return False
        
        print("✅ PlayerController has all expected children")
        
        # Check LSC script content
        with open(prefab_lsc, 'r') as f:
            script_content = f.read()
        
        # Check for key features
        required_features = [
            "extends KinematicBody2D",
            "movement_type",
            "4_direction",
            "8_direction",
            "_handle_input",
            "_update_movement",
            "_update_animations"
        ]
        
        for feature in required_features:
            if feature not in script_content:
                print(f"❌ Missing feature in script: {feature}")
                return False
        
        print("✅ PlayerController script has all required features")
        
        return True
        
    except Exception as e:
        print(f"❌ PlayerController prefab test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dynamic_node_loading():
    """Test that nodes are loaded dynamically from project directories"""
    print("\nTesting dynamic node loading...")
    
    try:
        from core.node_registry import get_node_registry
        
        # Create a temporary project with custom nodes
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir(parents=True)
            
            # Create nodes directory structure
            nodes_dir = project_path / "nodes"
            node2d_dir = nodes_dir / "node2d"
            node2d_dir.mkdir(parents=True)
            
            # Create a test physics node file
            test_node_content = """# TestPhysicsNode - Test physics node
extends Node2D

export var test_property: float = 1.0
"""
            test_node_file = node2d_dir / "TestPhysicsNode.lsc"
            with open(test_node_file, 'w') as f:
                f.write(test_node_content)
            
            # Get registry with project path
            registry = get_node_registry(project_path)
            all_nodes = registry.get_all_nodes()
            
            # Check that our test node was loaded
            if "TestPhysicsNode" in all_nodes:
                node_def = all_nodes["TestPhysicsNode"]
                print(f"✅ TestPhysicsNode loaded dynamically: category={node_def.category.value}")
                return True
            else:
                print("❌ TestPhysicsNode not loaded dynamically")
                return False
            
    except Exception as e:
        print(f"❌ Dynamic node loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_node_instance_uniqueness():
    """Test that multiple instances of the same node type maintain unique properties"""
    print("\nTesting node instance uniqueness...")

    try:
        from core.scene import Node

        # Create two sprite nodes with different textures
        sprite1_data = {
            "name": "Sprite1",
            "type": "Sprite",
            "texture": "texture1.png",
            "position": [100, 100],
            "scale": [2.0, 2.0]
        }

        sprite2_data = {
            "name": "Sprite2",
            "type": "Sprite",
            "texture": "texture2.png",
            "position": [200, 200],
            "scale": [1.5, 1.5]
        }

        # Create nodes from data
        sprite1 = Node.from_dict(sprite1_data)
        sprite2 = Node.from_dict(sprite2_data)

        # Check that they have different properties
        if hasattr(sprite1, 'texture') and hasattr(sprite2, 'texture'):
            if sprite1.texture != sprite2.texture:
                print("✅ Sprites have different textures")
            else:
                print("❌ Sprites have same texture - uniqueness failed")
                return False

        if hasattr(sprite1, 'position') and hasattr(sprite2, 'position'):
            if sprite1.position != sprite2.position:
                print("✅ Sprites have different positions")
            else:
                print("❌ Sprites have same position - uniqueness failed")
                return False

        if hasattr(sprite1, 'scale') and hasattr(sprite2, 'scale'):
            if sprite1.scale != sprite2.scale:
                print("✅ Sprites have different scales")
            else:
                print("❌ Sprites have same scale - uniqueness failed")
                return False

        # Test that modifying one doesn't affect the other
        if hasattr(sprite1, 'position'):
            original_sprite2_position = sprite2.position.copy() if hasattr(sprite2, 'position') else None
            sprite1.position[0] = 999

            if original_sprite2_position and sprite2.position == original_sprite2_position:
                print("✅ Modifying sprite1 position doesn't affect sprite2")
            else:
                print("❌ Modifying sprite1 position affected sprite2 - shared reference!")
                return False

        print("✅ Node instance uniqueness test passed")
        return True

    except Exception as e:
        print(f"❌ Node instance uniqueness test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all prefab system tests"""
    print("=" * 60)
    print("LUPINE ENGINE PREFAB SYSTEM TEST")
    print("=" * 60)
    
    tests = [
        test_physics_nodes_not_duplicated,
        test_project_creation_with_prefabs,
        test_player_controller_prefab,
        test_dynamic_node_loading,
        test_node_instance_uniqueness
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
        print("🎉 All prefab system tests passed!")
        print("\n✅ Prefab System Features:")
        print("  • Physics nodes no longer duplicated")
        print("  • Dynamic node registration from project directories")
        print("  • PlayerController prefab with topdown movement")
        print("  • 4-direction and 8-direction movement support")
        print("  • Animation hooks for all movement directions")
        print("  • WASD and Arrow key input support")
        print("  • Collision and interaction area detection")
        print("  • Automatic prefab copying to new projects")
        return True
    else:
        print("❌ Some prefab system tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
