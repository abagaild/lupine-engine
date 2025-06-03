#!/usr/bin/env python3
"""
Test script for LSC inheritance system
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.lsc.runtime import LSCRuntime
from core.lsc.interpreter import execute_lsc_script

def test_inheritance():
    """Test the inheritance system"""
    print("Testing LSC Inheritance System...")
    
    # Create runtime
    runtime = LSCRuntime()
    runtime.initialize_inheritance_manager(project_root)
    
    # Test script that extends KinematicBody2D
    test_script = """
extends KinematicBody2D

export var test_speed: float = 100.0

func _ready():
    super._ready()
    print("Child _ready called!")
    print("Test speed: ", test_speed)

func _physics_process(delta: float):
    super._physics_process(delta)
    print("Child _physics_process called with delta: ", delta)

func custom_method():
    print("Custom method called!")
    return "custom_result"
"""
    
    try:
        # Execute the script
        execute_lsc_script(test_script, runtime)
        print("✓ Script executed successfully")
        
        # Check if inheritance manager was used
        if runtime.inheritance_manager:
            print("✓ Inheritance manager is available")
            
            # Test class resolution
            kinematic_class = runtime.inheritance_manager.get_class("KinematicBody2D")
            if kinematic_class:
                print("✓ KinematicBody2D class resolved")
                print(f"  Base class: {kinematic_class.base_class.name if kinematic_class.base_class else 'None'}")
            else:
                print("✗ Failed to resolve KinematicBody2D class")
                
        else:
            print("✗ Inheritance manager not available")
            
    except Exception as e:
        print(f"✗ Error executing script: {e}")
        import traceback
        traceback.print_exc()

def test_super_calls():
    """Test super method calls"""
    print("\nTesting Super Method Calls...")
    
    # Create runtime
    runtime = LSCRuntime()
    runtime.initialize_inheritance_manager(project_root)
    
    # Create a script instance to test super calls
    from core.lsc.runtime import LSCScriptInstance
    
    # Mock node object
    class MockNode:
        def __init__(self):
            self.name = "TestNode"
            self.position = [0, 0]
    
    mock_node = MockNode()
    
    try:
        # Create script instance with inheritance
        script_instance = LSCScriptInstance(mock_node, "test_script.lsc", runtime, "KinematicBody2D")
        
        if script_instance.scope:
            print("✓ Script instance created with inheritance scope")
            
            # Check if super object exists
            if script_instance.scope.has('super'):
                super_obj = script_instance.scope.get('super')
                print("✓ Super object available")
                
                # Test super method calls
                try:
                    super_obj._ready()
                    print("✓ super._ready() called successfully")
                except Exception as e:
                    print(f"✗ Error calling super._ready(): {e}")
                    
                try:
                    super_obj._physics_process(0.016)
                    print("✓ super._physics_process() called successfully")
                except Exception as e:
                    print(f"✗ Error calling super._physics_process(): {e}")
                    
            else:
                print("✗ Super object not found in scope")
        else:
            print("✗ Failed to create inheritance scope")
            
    except Exception as e:
        print(f"✗ Error creating script instance: {e}")
        import traceback
        traceback.print_exc()

def test_class_chain():
    """Test class inheritance chain"""
    print("\nTesting Class Inheritance Chain...")
    
    # Create runtime
    runtime = LSCRuntime()
    runtime.initialize_inheritance_manager(project_root)
    
    try:
        # Test the inheritance chain for KinematicBody2D
        kinematic_class = runtime.inheritance_manager.resolve_class("KinematicBody2D")
        
        if kinematic_class:
            print("✓ KinematicBody2D class resolved")
            
            # Get the inheritance chain
            chain = runtime.inheritance_manager._get_class_chain(kinematic_class)
            print(f"✓ Inheritance chain: {' -> '.join([cls.name for cls in chain])}")
            
            # Test method resolution
            if kinematic_class.base_class:
                print(f"✓ Base class: {kinematic_class.base_class.name}")
            else:
                print("✗ No base class found")
                
        else:
            print("✗ Failed to resolve KinematicBody2D class")
            
    except Exception as e:
        print(f"✗ Error testing class chain: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_inheritance()
    test_super_calls()
    test_class_chain()
    print("\nInheritance system test completed!")
