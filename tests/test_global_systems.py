"""
Test script for Global Systems in Lupine Engine
Run this to verify that singletons and global variables work correctly
"""

import tempfile
import shutil
import json
import sys
from pathlib import Path

# Add the engine root to Python path
engine_root = Path(__file__).parent.parent
sys.path.insert(0, str(engine_root))

def test_singleton_manager():
    """Test the singleton manager functionality"""
    print("Testing Singleton Manager...")
    
    # Create temporary project directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create project.json
        project_config = {
            "name": "Test Project",
            "globals": {
                "singletons": [],
                "variables": []
            }
        }
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_config, f)
        
        # Create test singleton script
        singleton_script = '''
class TestSingleton:
    def __init__(self):
        self.value = 42
        self.initialized = False
    
    def _singleton_init(self):
        self.initialized = True
        print("TestSingleton initialized!")
    
    def get_value(self):
        return self.value
    
    def set_value(self, value):
        self.value = value
'''
        
        script_path = project_path / "test_singleton.py"
        with open(script_path, 'w') as f:
            f.write(singleton_script)
        
        # Test singleton manager
        from core.globals.singleton_manager import SingletonManager
        
        manager = SingletonManager(str(project_path))
        
        # Add singleton
        success = manager.add_singleton("TestSingleton", "test_singleton.py", True)
        assert success, "Failed to add singleton"
        print("✓ Singleton added successfully")
        
        # Initialize singletons
        manager.initialize_all()
        
        # Get singleton instance
        instance = manager.get_singleton("TestSingleton")
        assert instance is not None, "Failed to get singleton instance"
        assert instance.value == 42, "Singleton value incorrect"
        assert instance.initialized, "Singleton not initialized"
        print("✓ Singleton instance retrieved and initialized")
        
        # Test singleton methods
        instance.set_value(100)
        assert instance.get_value() == 100, "Singleton method failed"
        print("✓ Singleton methods work correctly")
        
        # Save and reload
        manager.save_singletons()
        
        # Create new manager and load
        manager2 = SingletonManager(str(project_path))
        singletons = manager2.get_all_singletons()
        assert len(singletons) == 1, "Failed to load singleton from file"
        assert singletons[0].name == "TestSingleton", "Singleton name incorrect"
        print("✓ Singleton persistence works")
        
        print("Singleton Manager tests passed!\n")


def test_variables_manager():
    """Test the variables manager functionality"""
    print("Testing Variables Manager...")
    
    # Create temporary project directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create project.json
        project_config = {
            "name": "Test Project",
            "globals": {
                "singletons": [],
                "variables": []
            }
        }
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_config, f)
        
        # Test variables manager
        from core.globals.variables_manager import VariablesManager, VariableType
        
        manager = VariablesManager(str(project_path))
        
        # Add different types of variables
        success = manager.add_variable("test_int", VariableType.INT, 42, "Test integer")
        assert success, "Failed to add int variable"
        
        success = manager.add_variable("test_float", VariableType.FLOAT, 3.14, "Test float")
        assert success, "Failed to add float variable"
        
        success = manager.add_variable("test_string", VariableType.STRING, "Hello", "Test string")
        assert success, "Failed to add string variable"
        
        success = manager.add_variable("test_bool", VariableType.BOOL, True, "Test boolean")
        assert success, "Failed to add bool variable"
        
        success = manager.add_variable("test_color", VariableType.COLOR, [1.0, 0.5, 0.0, 1.0], "Test color")
        assert success, "Failed to add color variable"
        
        success = manager.add_variable("test_vector2", VariableType.VECTOR2, [10.0, 20.0], "Test vector2")
        assert success, "Failed to add vector2 variable"
        
        print("✓ Variables added successfully")
        
        # Test getting variables
        assert manager.get_value("test_int") == 42, "Int variable incorrect"
        assert manager.get_value("test_float") == 3.14, "Float variable incorrect"
        assert manager.get_value("test_string") == "Hello", "String variable incorrect"
        assert manager.get_value("test_bool") == True, "Bool variable incorrect"
        assert manager.get_value("test_color") == [1.0, 0.5, 0.0, 1.0], "Color variable incorrect"
        assert manager.get_value("test_vector2") == [10.0, 20.0], "Vector2 variable incorrect"
        print("✓ Variable values retrieved correctly")
        
        # Test setting variables
        success = manager.set_value("test_int", 100)
        assert success, "Failed to set int variable"
        assert manager.get_value("test_int") == 100, "Int variable not updated"
        
        success = manager.set_value("test_string", "World")
        assert success, "Failed to set string variable"
        assert manager.get_value("test_string") == "World", "String variable not updated"
        print("✓ Variable values updated correctly")
        
        # Test variable validation
        success = manager.set_value("test_int", "not a number")
        assert not success, "Should have failed to set invalid int value"
        print("✓ Variable validation works")
        
        # Save and reload
        manager.save_variables()
        
        # Create new manager and load
        manager2 = VariablesManager(str(project_path))
        variables = manager2.get_all_variables()
        assert len(variables) == 6, "Failed to load variables from file"
        
        # Check loaded values
        assert manager2.get_value("test_int") == 100, "Loaded int variable incorrect"
        assert manager2.get_value("test_string") == "World", "Loaded string variable incorrect"
        print("✓ Variable persistence works")
        
        print("Variables Manager tests passed!\n")


def test_convenience_functions():
    """Test the convenience functions"""
    print("Testing Convenience Functions...")
    
    # Create temporary project directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create project.json
        project_config = {
            "name": "Test Project",
            "globals": {
                "singletons": [],
                "variables": []
            }
        }
        
        with open(project_path / "project.json", 'w') as f:
            json.dump(project_config, f)
        
        # Initialize managers
        from core.globals.singleton_manager import initialize_singleton_manager, get_singleton
        from core.globals.variables_manager import initialize_variables_manager, get_global_var, set_global_var
        
        singleton_manager = initialize_singleton_manager(str(project_path))
        variables_manager = initialize_variables_manager(str(project_path))
        
        # Test convenience functions
        from core.globals.variables_manager import VariableType
        variables_manager.add_variable("test_var", VariableType.INT, 123)
        
        # Test global variable convenience functions
        value = get_global_var("test_var")
        assert value == 123, "get_global_var failed"
        
        success = set_global_var("test_var", 456)
        assert success, "set_global_var failed"
        
        value = get_global_var("test_var")
        assert value == 456, "set_global_var didn't update value"
        
        print("✓ Convenience functions work correctly")
        
        print("Convenience Functions tests passed!\n")


if __name__ == "__main__":
    print("Running Global Systems Tests...\n")
    
    try:
        test_singleton_manager()
        test_variables_manager()
        test_convenience_functions()
        
        print("🎉 All tests passed! Global Systems are working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
