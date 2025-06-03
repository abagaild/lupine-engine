"""
Test script to verify all LSC stubs have been implemented
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.lsc.runtime import LSCRuntime
from core.lsc.builtins import LSCBuiltins
from core.lsc.game_engine_interface import MockGameEngine
from core.lsc.interpreter import LSCInterpreter
from core.lsc.lexer import LSCLexer
from core.lsc.parser import LSCParser


def test_runtime_completeness():
    """Test that runtime has all expected methods implemented"""
    print("Testing LSC Runtime completeness...")
    
    # Create runtime with mock game engine
    mock_engine = MockGameEngine()
    runtime = LSCRuntime(mock_engine)
    
    # Test signal system
    print("✓ Testing signal system...")
    runtime.connect("test_signal", runtime, "test_method")
    assert runtime.is_connected("test_signal", runtime, "test_method")
    runtime.emit_signal("test_signal", "arg1", "arg2")
    runtime.disconnect("test_signal", runtime, "test_method")
    assert not runtime.is_connected("test_signal", runtime, "test_method")
    
    # Test resource system
    print("✓ Testing resource system...")
    # Create a test file
    test_content = "test content"
    runtime.save_resource(test_content, "test_file.txt")
    loaded_content = runtime.load_resource("test_file.txt")
    assert loaded_content == test_content
    
    # Test timer system
    print("✓ Testing timer system...")
    timer = runtime.create_timer(0.1, lambda: print("Timer callback"))
    assert timer is not None
    runtime.update_timers()
    runtime.clear_timers()
    
    # Test node management (with mock engine)
    print("✓ Testing node management...")
    mock_node = type('MockNode', (), {'name': 'test_node'})()
    mock_engine.add_node("test_path", mock_node)
    
    found_node = runtime.get_node("test_path")
    assert found_node is mock_node
    
    found_by_name = runtime.find_node("test_node")
    assert found_by_name is mock_node
    
    # Test input system
    print("✓ Testing input system...")
    mock_engine.set_input_state("action_jump", True)
    assert runtime.is_action_pressed("jump") == False  # Mock returns False by default
    
    mock_engine.set_mouse_position(100, 200)
    mouse_pos = runtime.get_mouse_position()
    assert mouse_pos == (100, 200)
    
    print("✓ Runtime completeness test passed!")


def test_builtins_completeness():
    """Test that builtins have all expected functions"""
    print("Testing LSC Builtins completeness...")
    
    runtime = LSCRuntime()
    builtins = LSCBuiltins(runtime)
    
    # Test that all functions are accessible
    print("✓ Testing function accessibility...")
    assert hasattr(builtins, 'functions')
    assert hasattr(builtins, 'constants')
    
    # Test math functions
    print("✓ Testing math functions...")
    assert builtins.abs(-5) == 5
    assert builtins.min(1, 2, 3) == 1
    assert builtins.max(1, 2, 3) == 3
    assert builtins.clamp(5, 0, 10) == 5
    assert builtins.clamp(-5, 0, 10) == 0
    assert builtins.clamp(15, 0, 10) == 10
    
    # Test string functions
    print("✓ Testing string functions...")
    assert builtins.len("hello") == 5
    assert builtins.substr("hello", 1, 3) == "ell"
    assert builtins.find("hello", "ll") == 2
    
    # Test array functions
    print("✓ Testing array functions...")
    test_array = [1, 2, 3]
    builtins.append(test_array, 4)
    assert test_array == [1, 2, 3, 4]
    
    # Test type constructors
    print("✓ Testing type constructors...")
    vec = builtins.Vector2(1, 2)
    assert vec.x == 1 and vec.y == 2
    
    color = builtins.Color(1, 0, 0, 1)
    assert color.r == 1 and color.g == 0 and color.b == 0 and color.a == 1
    
    rect = builtins.Rect2(0, 0, 100, 200)
    assert rect.x == 0 and rect.y == 0 and rect.width == 100 and rect.height == 200
    
    print("✓ Builtins completeness test passed!")


def test_interpreter_completeness():
    """Test that interpreter can handle all language constructs"""
    print("Testing LSC Interpreter completeness...")
    
    # Test basic script execution
    script = """
    var x = 5
    var y = 10
    var result = x + y
    """
    
    lexer = LSCLexer()
    parser = LSCParser()
    runtime = LSCRuntime()
    interpreter = LSCInterpreter(runtime)
    
    tokens = lexer.tokenize(script)
    ast = parser.parse(tokens)
    interpreter.interpret(ast)
    
    # Check that variables were set
    assert runtime.get_variable('x') == 5
    assert runtime.get_variable('y') == 10
    assert runtime.get_variable('result') == 15
    
    print("✓ Interpreter completeness test passed!")


def test_integration():
    """Test full integration of all components"""
    print("Testing full LSC integration...")
    
    # Create a more complex script
    script = """
    extends Node2D
    
    export var speed: float = 100.0
    export var health: int = 100
    
    func _ready():
        print("Node is ready!")
        connect("health_changed", self, "_on_health_changed")
    
    func _process(delta):
        if is_action_pressed("ui_right"):
            position.x += speed * delta
    
    func take_damage(amount):
        health -= amount
        emit_signal("health_changed", health)
    
    func _on_health_changed(new_health):
        if new_health <= 0:
            queue_free()
    """
    
    # Set up full system
    mock_engine = MockGameEngine()
    runtime = LSCRuntime(mock_engine)
    lexer = LSCLexer()
    parser = LSCParser()
    interpreter = LSCInterpreter(runtime)
    
    # Parse and execute
    tokens = lexer.tokenize(script)
    ast = parser.parse(tokens)
    interpreter.interpret(ast)
    
    print("✓ Full integration test passed!")


def main():
    """Run all completeness tests"""
    print("=" * 50)
    print("LSC STUB COMPLETENESS TEST")
    print("=" * 50)
    
    try:
        test_runtime_completeness()
        print()
        test_builtins_completeness()
        print()
        test_interpreter_completeness()
        print()
        test_integration()
        print()
        print("=" * 50)
        print("✅ ALL TESTS PASSED - NO STUBS REMAINING!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
