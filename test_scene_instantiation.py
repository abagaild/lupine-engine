#!/usr/bin/env python3
"""
Test script for scene instantiation system
"""

import sys
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.project import LupineProject, set_current_project
from core.scene.scene_manager import SceneManager
from core.node_registry import DynamicNodeRegistry
from nodes.base.SceneInstance import SceneInstance


def test_scene_instantiation():
    """Test the scene instantiation system"""
    print("Testing Scene Instantiation System")
    print("=" * 40)
    
    # Create a test project
    project_path = Path(__file__).parent
    project = LupineProject(str(project_path))
    project.load_project()
    set_current_project(project)
    
    # Initialize node registry
    registry = DynamicNodeRegistry()
    registry.set_project_path(project_path)
    
    # Test 1: Create a scene instance
    print("\n1. Creating SceneInstance node...")
    scene_instance = SceneInstance("PlayerInstance")
    scene_instance.set_scene_file("scenes/TestPlayer.scene")
    
    print(f"   Scene path: {scene_instance.get_scene_file()}")
    print(f"   Instance ID: {scene_instance.get_instance_id()}")
    print(f"   Children count: {len(scene_instance.children)}")
    
    # Test 2: Convert to dict and back
    print("\n2. Testing serialization...")
    scene_data = scene_instance.to_dict()
    print(f"   Serialized data keys: {list(scene_data.keys())}")
    
    # Create new instance from dict
    new_instance = SceneInstance.from_dict(scene_data)
    print(f"   Restored scene path: {new_instance.get_scene_file()}")
    print(f"   Restored children count: {len(new_instance.children)}")
    
    # Test 3: Test scene manager instantiation
    print("\n3. Testing scene manager instantiation...")
    scene_manager = project.scene_manager
    available_scenes = scene_manager.get_available_scenes()
    print(f"   Available scenes: {available_scenes}")
    
    if "scenes/TestPlayer.scene" in available_scenes:
        instantiated = scene_manager.instantiate_scene("scenes/TestPlayer.scene", "TestInstance")
        if instantiated:
            print(f"   Successfully instantiated scene")
            print(f"   Instance type: {type(instantiated).__name__}")
            print(f"   Instance children: {len(instantiated.children)}")
        else:
            print("   Failed to instantiate scene")
    else:
        print("   TestPlayer.scene not found in available scenes")
    
    # Test 4: Test node registry scene loading
    print("\n4. Testing node registry scene detection...")
    registry.load_scene_files()
    scene_nodes = [name for name, node_def in registry._node_definitions.items() 
                   if node_def.category.value == "Scenes"]
    print(f"   Scene nodes found: {scene_nodes}")
    
    # Test 5: Create scene instance through registry
    print("\n5. Testing registry scene instance creation...")
    if scene_nodes:
        scene_key = scene_nodes[0]
        registry_instance = registry.create_node_instance(scene_key, "RegistryInstance")
        if registry_instance:
            print(f"   Created instance through registry: {type(registry_instance).__name__}")
            print(f"   Scene path: {registry_instance.get_scene_file()}")
        else:
            print("   Failed to create instance through registry")
    
    print("\n" + "=" * 40)
    print("Scene instantiation test completed!")


if __name__ == "__main__":
    test_scene_instantiation()
