#!/usr/bin/env python3
"""
Test script to verify that all physics and collision nodes are properly implemented
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_physics_nodes():
    """Test that all physics nodes can be imported and instantiated"""
    print("Testing physics and collision nodes implementation...")
    
    try:
        # Test importing from core.scene
        from core.scene import (CollisionShape2D, CollisionPolygon2D, Area2D, 
                               RigidBody2D, StaticBody2D, KinematicBody2D)
        print("✅ Successfully imported all physics node classes")
        
        # Test node instantiation
        nodes_to_test = [
            ("CollisionShape2D", CollisionShape2D),
            ("CollisionPolygon2D", CollisionPolygon2D),
            ("Area2D", Area2D),
            ("RigidBody2D", RigidBody2D),
            ("StaticBody2D", StaticBody2D),
            ("KinematicBody2D", KinematicBody2D)
        ]
        
        for node_name, node_class in nodes_to_test:
            try:
                instance = node_class(f"Test{node_name}")
                print(f"✅ Successfully created {node_name} instance")
                
                # Test basic properties
                assert hasattr(instance, 'type'), f"{node_name} missing 'type' attribute"
                assert instance.type == node_name, f"{node_name} has incorrect type: {instance.type}"
                assert hasattr(instance, 'script_path'), f"{node_name} missing 'script_path' attribute"
                assert hasattr(instance, 'to_dict'), f"{node_name} missing 'to_dict' method"
                
                # Test serialization
                data = instance.to_dict()
                assert isinstance(data, dict), f"{node_name} to_dict() should return dictionary"
                print(f"✅ {node_name} serialization works")
                
            except Exception as e:
                print(f"❌ Failed to create {node_name}: {e}")
                return False
        
        print("✅ All physics nodes instantiated successfully")
        
    except ImportError as e:
        print(f"❌ Failed to import physics nodes: {e}")
        return False
    
    return True

def test_node_registry():
    """Test that physics nodes are properly registered"""
    print("\nTesting node registry...")
    
    try:
        from core.node_registry import get_node_registry
        
        # Get registry instance
        registry = get_node_registry()
        all_nodes = registry.get_all_nodes()
        
        # Check that physics nodes are registered
        physics_nodes = ["Area2D", "CollisionShape2D", "CollisionPolygon2D", 
                        "RigidBody2D", "StaticBody2D", "KinematicBody2D"]
        
        for node_name in physics_nodes:
            if node_name in all_nodes:
                node_def = all_nodes[node_name]
                print(f"✅ {node_name} registered in category: {node_def.category.value}")
                
                # Test node creation through registry
                try:
                    instance = registry.create_node_instance(node_name, f"Test{node_name}")
                    print(f"✅ {node_name} created through registry")
                except Exception as e:
                    print(f"❌ Failed to create {node_name} through registry: {e}")
                    return False
            else:
                print(f"❌ {node_name} not found in registry")
                return False
        
        print("✅ All physics nodes properly registered")
        
    except Exception as e:
        print(f"❌ Node registry test failed: {e}")
        return False
    
    return True

def test_lsc_scripts():
    """Test that LSC script files exist and are readable"""
    print("\nTesting LSC script files...")
    
    physics_scripts = [
        "nodes/Area2D.lsc",
        "nodes/CollisionShape2D.lsc", 
        "nodes/CollisionPolygon2D.lsc",
        "nodes/RigidBody2D.lsc",
        "nodes/StaticBody2D.lsc",
        "nodes/KinematicBody2D.lsc"
    ]
    
    for script_path in physics_scripts:
        try:
            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Basic validation
                assert len(content) > 0, f"{script_path} is empty"
                assert "extends Node2D" in content, f"{script_path} should extend Node2D"
                assert "export_group" in content, f"{script_path} should have export groups"
                
                print(f"✅ {script_path} exists and is valid")
            else:
                print(f"❌ {script_path} not found")
                return False
                
        except Exception as e:
            print(f"❌ Error reading {script_path}: {e}")
            return False
    
    print("✅ All LSC script files are valid")
    return True

def test_physics_properties():
    """Test that physics nodes have expected properties"""
    print("\nTesting physics node properties...")
    
    try:
        from core.scene import (CollisionShape2D, CollisionPolygon2D, Area2D, 
                               RigidBody2D, StaticBody2D, KinematicBody2D)
        
        # Test CollisionShape2D properties
        collision_shape = CollisionShape2D("TestShape")
        expected_shape_props = ['shape', 'disabled', 'size', 'radius', 'debug_color']
        for prop in expected_shape_props:
            assert hasattr(collision_shape, prop), f"CollisionShape2D missing property: {prop}"
        print("✅ CollisionShape2D has expected properties")
        
        # Test Area2D properties
        area = Area2D("TestArea")
        expected_area_props = ['monitoring', 'monitorable', 'collision_layer', 'collision_mask', 'gravity']
        for prop in expected_area_props:
            assert hasattr(area, prop), f"Area2D missing property: {prop}"
        print("✅ Area2D has expected properties")
        
        # Test RigidBody2D properties
        rigid_body = RigidBody2D("TestRigidBody")
        expected_rigid_props = ['mode', 'mass', 'gravity_scale', 'collision_layer']
        for prop in expected_rigid_props:
            assert hasattr(rigid_body, prop), f"RigidBody2D missing property: {prop}"
        print("✅ RigidBody2D has expected properties")
        
        # Test StaticBody2D properties
        static_body = StaticBody2D("TestStaticBody")
        expected_static_props = ['collision_layer', 'constant_linear_velocity']
        for prop in expected_static_props:
            assert hasattr(static_body, prop), f"StaticBody2D missing property: {prop}"
        print("✅ StaticBody2D has expected properties")
        
        # Test KinematicBody2D properties
        kinematic_body = KinematicBody2D("TestKinematicBody")
        expected_kinematic_props = ['collision_layer', 'safe_margin']
        for prop in expected_kinematic_props:
            assert hasattr(kinematic_body, prop), f"KinematicBody2D missing property: {prop}"
        print("✅ KinematicBody2D has expected properties")
        
        print("✅ All physics nodes have expected properties")
        
    except Exception as e:
        print(f"❌ Physics properties test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("LUPINE ENGINE PHYSICS NODES TEST")
    print("=" * 60)
    
    tests = [
        test_physics_nodes,
        test_node_registry,
        test_lsc_scripts,
        test_physics_properties
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
        print("🎉 All physics nodes implemented successfully!")
        return True
    else:
        print("❌ Some tests failed. Check implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
