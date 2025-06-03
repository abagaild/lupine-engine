#!/usr/bin/env python3
"""
Test script for SimplePlayerController inheritance
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.lsc.runtime import LSCRuntime
from core.lsc.interpreter import execute_lsc_script

def test_player_controller_inheritance():
    """Test SimplePlayerController inheritance"""
    print("Testing SimplePlayerController Inheritance...")
    
    # Create runtime
    runtime = LSCRuntime()
    runtime.initialize_inheritance_manager(project_root)
    
    # Load the actual SimplePlayerController script
    script_path = project_root / "nodes" / "prefabs" / "SimplePlayerController.lsc"
    
    if not script_path.exists():
        print(f"✗ Script file not found: {script_path}")
        return
        
    with open(script_path, 'r') as f:
        script_content = f.read()
    
    print(f"✓ Loaded script: {script_path}")
    
    try:
        # Parse extends clause
        base_class = runtime.inheritance_manager.parse_extends_from_script(script_content)
        print(f"✓ Detected base class: {base_class}")
        
        # Create a mock node
        class MockNode:
            def __init__(self):
                self.name = "SimplePlayerController"
                self.position = [100, 100]
                self.rotation = 0
                self.scale = [1, 1]
        
        mock_node = MockNode()
        
        # Create script instance with inheritance
        from core.lsc.runtime import LSCScriptInstance
        script_instance = LSCScriptInstance(mock_node, str(script_path), runtime, base_class)
        
        if script_instance.scope:
            print("✓ Script instance created with inheritance")
            
            # Set up runtime scope
            old_scope = runtime.current_scope
            runtime.current_scope = script_instance.scope
            
            try:
                # Add node reference to scope
                script_instance.scope.define('self', mock_node)
                script_instance.scope.define('node', mock_node)
                script_instance.scope.define('position', mock_node.position)
                script_instance.scope.define('rotation', mock_node.rotation)
                script_instance.scope.define('scale', mock_node.scale)
                
                # Execute the script
                execute_lsc_script(script_content, runtime)
                print("✓ Script executed successfully")
                
                # Test if methods are available
                methods_to_test = ['_ready', '_physics_process', '_handle_input', '_handle_movement']
                for method_name in methods_to_test:
                    if script_instance.scope.has(method_name):
                        method = script_instance.scope.get(method_name)
                        if callable(method):
                            print(f"✓ Method {method_name} is available and callable")
                        else:
                            print(f"✗ Method {method_name} exists but is not callable")
                    else:
                        print(f"✗ Method {method_name} not found")
                
                # Test super object
                if script_instance.scope.has('super'):
                    super_obj = script_instance.scope.get('super')
                    print("✓ Super object available")
                    
                    # Test calling super._ready()
                    try:
                        super_obj._ready()
                        print("✓ super._ready() called successfully")
                    except Exception as e:
                        print(f"✗ Error calling super._ready(): {e}")
                else:
                    print("✗ Super object not found")
                
                # Test calling _ready method
                try:
                    script_instance.call_method('_ready')
                    print("✓ _ready method called successfully")
                except Exception as e:
                    print(f"✗ Error calling _ready: {e}")
                
                # Test calling _physics_process method
                try:
                    script_instance.call_method('_physics_process', 0.016)
                    print("✓ _physics_process method called successfully")
                except Exception as e:
                    print(f"✗ Error calling _physics_process: {e}")
                    
                # Test export variables
                export_vars = ['speed', 'acceleration', 'friction', 'debug_mode']
                for var_name in export_vars:
                    if script_instance.scope.has(var_name):
                        value = script_instance.scope.get(var_name)
                        print(f"✓ Export variable {var_name} = {value}")
                    else:
                        print(f"✗ Export variable {var_name} not found")
                        
            finally:
                # Restore scope
                runtime.current_scope = old_scope
                
        else:
            print("✗ Failed to create script instance scope")
            
    except Exception as e:
        print(f"✗ Error testing inheritance: {e}")
        import traceback
        traceback.print_exc()

def test_inheritance_chain():
    """Test the full inheritance chain for SimplePlayerController"""
    print("\nTesting Full Inheritance Chain...")
    
    # Create runtime
    runtime = LSCRuntime()
    runtime.initialize_inheritance_manager(project_root)
    
    try:
        # Resolve KinematicBody2D class (what SimplePlayerController extends)
        kinematic_class = runtime.inheritance_manager.resolve_class("KinematicBody2D")
        
        if kinematic_class:
            print("✓ KinematicBody2D class resolved")
            
            # Get the full inheritance chain
            chain = runtime.inheritance_manager._get_class_chain(kinematic_class)
            print(f"✓ Full inheritance chain: {' -> '.join([cls.name for cls in chain])}")
            
            # Show what each class in the chain provides
            for cls in chain:
                print(f"  {cls.name}:")
                if cls.script_path:
                    print(f"    Script: {cls.script_path}")
                else:
                    print(f"    Built-in class")
                    
                methods = list(cls.methods.keys())
                properties = list(cls.properties.keys())
                
                if methods:
                    print(f"    Methods: {', '.join(methods[:5])}{'...' if len(methods) > 5 else ''}")
                if properties:
                    print(f"    Properties: {', '.join(properties[:5])}{'...' if len(properties) > 5 else ''}")
                    
        else:
            print("✗ Failed to resolve KinematicBody2D class")
            
    except Exception as e:
        print(f"✗ Error testing inheritance chain: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_player_controller_inheritance()
    test_inheritance_chain()
    print("\nSimplePlayerController inheritance test completed!")
