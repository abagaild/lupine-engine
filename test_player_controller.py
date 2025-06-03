#!/usr/bin/env python3
"""
Test script for PlayerController prefab
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_player_controller_prefab():
    """Test PlayerController prefab creation"""
    print("Testing PlayerController prefab...")
    
    try:
        # Import required modules
        from core.node_registry import NodeRegistry
        from core.project import LupineProject
        from core.scene import Scene
        
        # Create a mock project
        project_path = project_root
        project = LupineProject(project_path)
        
        # Initialize node registry with project path
        registry = NodeRegistry(project_path)
        
        # Load prefabs
        prefabs_dir = project_path / "nodes" / "prefabs"
        print(f"Loading prefabs from: {prefabs_dir}")
        registry.load_prefabs_from_directory(prefabs_dir)
        
        # Check if PlayerController is registered
        player_controller_def = registry.get_node_definition("PlayerController")
        if player_controller_def:
            print(f"✓ PlayerController prefab found: {player_controller_def.name}")
            print(f"  Class: {player_controller_def.class_name}")
            print(f"  Script: {player_controller_def.script_path}")
        else:
            print("✗ PlayerController prefab not found!")
            return False
        
        # Try to create an instance
        print("\nCreating PlayerController instance...")
        player_instance = registry.create_node_instance("PlayerController", "TestPlayer")
        
        if player_instance:
            print(f"✓ PlayerController instance created: {player_instance.name}")
            print(f"  Type: {player_instance.type}")
            print(f"  Script path: {getattr(player_instance, 'script_path', 'None')}")
            print(f"  Children count: {len(player_instance.children)}")
            
            # Check children
            for i, child in enumerate(player_instance.children):
                print(f"  Child {i}: {child.name} ({child.type})")
            
            # Check properties
            if hasattr(player_instance, 'properties'):
                print(f"  Properties: {player_instance.properties}")
            
            # Check if it's a KinematicBody2D
            from core.scene import KinematicBody2D
            if isinstance(player_instance, KinematicBody2D):
                print("✓ Instance is correctly a KinematicBody2D")
            else:
                print(f"✗ Instance is {type(player_instance)}, not KinematicBody2D")
            
            return True
        else:
            print("✗ Failed to create PlayerController instance!")
            return False
            
    except Exception as e:
        print(f"✗ Error testing PlayerController: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scene_loading():
    """Test loading a scene with PlayerController"""
    print("\n" + "="*50)
    print("Testing scene loading with PlayerController...")
    
    try:
        from core.scene import Scene
        from core.node_registry import get_node_registry

        # Initialize the global registry with project path so scene loading can use it
        registry = get_node_registry(project_root)

        # Load the test scene
        scene_file = project_root / "test_player_controller.json"
        if not scene_file.exists():
            print(f"✗ Test scene file not found: {scene_file}")
            return False

        scene = Scene.load_from_file(str(scene_file))
        if scene:
            print(f"✓ Scene loaded: {scene.name}")
            print(f"  Root nodes: {len(scene.root_nodes)}")
            
            # Find PlayerController node
            def find_player_controller(node, depth=0):
                indent = "  " * depth
                print(f"{indent}Checking node: {node.name} (type: {node.type})")
                if node.type == "PlayerController":
                    return node
                for child in node.children:
                    result = find_player_controller(child, depth + 1)
                    if result:
                        return result
                return None

            player_node = None
            for root in scene.root_nodes:
                player_node = find_player_controller(root)
                if player_node:
                    break
            
            if player_node:
                print(f"✓ PlayerController found in scene: {player_node.name}")
                print(f"  Type: {player_node.type}")
                print(f"  Script path: {getattr(player_node, 'script_path', 'None')}")
                print(f"  Children: {len(player_node.children)}")
                return True
            else:
                print("✗ PlayerController not found in scene!")
                return False
        else:
            print("✗ Failed to load scene!")
            return False
            
    except Exception as e:
        print(f"✗ Error testing scene loading: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("PlayerController Prefab Test")
    print("="*50)
    
    success1 = test_player_controller_prefab()
    success2 = test_scene_loading()
    
    print("\n" + "="*50)
    if success1 and success2:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
        sys.exit(1)
