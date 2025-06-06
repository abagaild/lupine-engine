/**
 * Basic test to verify core Lupine Engine architecture
 * This test doesn't require external libraries and can be compiled standalone
 */

#include "src/core/core_types.h"
#include "src/core/lupine_engine.h"
#include <iostream>
#include <cassert>

using namespace lupine;

void test_core_types() {
    std::cout << "Testing core types..." << std::endl;
    
    // Test Vector2
    Vector2 v1(3.0f, 4.0f);
    Vector2 v2(1.0f, 2.0f);
    Vector2 v3 = v1 + v2;
    
    assert(v3.x == 4.0f && v3.y == 6.0f);
    assert(v1.length() == 5.0f);
    
    // Test Color
    Color red = Color::RED;
    assert(red.r == 1.0f && red.g == 0.0f && red.b == 0.0f);
    
    // Test Transform2D
    Transform2D transform;
    Vector2 point(1.0f, 0.0f);
    Vector2 transformed = transform.transform_point(point);
    assert(transformed.x == 1.0f && transformed.y == 0.0f);
    
    // Test Rect2
    Rect2 rect(0.0f, 0.0f, 10.0f, 10.0f);
    assert(rect.has_point(Vector2(5.0f, 5.0f)));
    assert(!rect.has_point(Vector2(15.0f, 15.0f)));
    
    std::cout << "✅ Core types test passed!" << std::endl;
}

void test_variant_system() {
    std::cout << "Testing variant system..." << std::endl;
    
    Variant v1(42);
    Variant v2(3.14f);
    Variant v3("Hello");
    Variant v4(Vector2(1.0f, 2.0f));
    
    assert(v1.get_type() == Variant::INT);
    assert(v1.as_int() == 42);
    
    assert(v2.get_type() == Variant::FLOAT);
    assert(v2.as_float() == 3.14f);
    
    assert(v3.get_type() == Variant::STRING);
    assert(v3.as_string() == "Hello");
    
    assert(v4.get_type() == Variant::VECTOR2);
    Vector2 vec = v4.as_vector2();
    assert(vec.x == 1.0f && vec.y == 2.0f);
    
    std::cout << "✅ Variant system test passed!" << std::endl;
}

void test_signal_system() {
    std::cout << "Testing signal system..." << std::endl;
    
    Signal signal;
    bool callback_called = false;
    
    signal.connect([&callback_called](const std::vector<Variant>& args) {
        callback_called = true;
    });
    
    signal.emit();
    assert(callback_called);
    
    std::cout << "✅ Signal system test passed!" << std::endl;
}

void test_engine_creation() {
    std::cout << "Testing engine creation..." << std::endl;
    
    EngineConfig config;
    config.project_path = ".";
    config.window_width = 800;
    config.window_height = 600;
    config.enable_python = false;  // Disable Python for this test
    config.enable_audio = false;   // Disable audio for this test
    config.enable_physics = false; // Disable physics for this test
    
    auto engine = std::make_unique<LupineEngine>(config);
    assert(engine != nullptr);
    
    // Test engine instance access
    assert(LupineEngine::get_instance() == engine.get());
    
    std::cout << "✅ Engine creation test passed!" << std::endl;
}

void test_math_utilities() {
    std::cout << "Testing math utilities..." << std::endl;
    
    // Test math constants and functions
    assert(Math::deg_to_rad(180.0f) == Math::PI);
    assert(Math::rad_to_deg(Math::PI) == 180.0f);
    assert(Math::lerp(0.0f, 10.0f, 0.5f) == 5.0f);
    assert(Math::clamp(15.0f, 0.0f, 10.0f) == 10.0f);
    assert(Math::abs(-5.0f) == 5.0f);
    assert(Math::sign(-3.0f) == -1.0f);
    assert(Math::sign(3.0f) == 1.0f);
    assert(Math::sign(0.0f) == 0.0f);
    
    std::cout << "✅ Math utilities test passed!" << std::endl;
}

void test_string_utilities() {
    std::cout << "Testing string utilities..." << std::endl;
    
    // Test string splitting
    std::vector<String> parts = StringUtils::split("hello,world,test", ",");
    assert(parts.size() == 3);
    assert(parts[0] == "hello");
    assert(parts[1] == "world");
    assert(parts[2] == "test");
    
    // Test string joining
    String joined = StringUtils::join(parts, "-");
    assert(joined == "hello-world-test");
    
    // Test case conversion
    assert(StringUtils::to_lower("HELLO") == "hello");
    assert(StringUtils::to_upper("hello") == "HELLO");
    
    // Test string checks
    assert(StringUtils::starts_with("hello world", "hello"));
    assert(StringUtils::ends_with("hello world", "world"));
    
    // Test trimming
    assert(StringUtils::trim("  hello  ") == "hello");
    
    std::cout << "✅ String utilities test passed!" << std::endl;
}

int main() {
    std::cout << "=== Lupine Engine C++ Core Tests ===" << std::endl;
    std::cout << std::endl;
    
    try {
        test_core_types();
        test_variant_system();
        test_signal_system();
        test_math_utilities();
        test_string_utilities();
        test_engine_creation();
        
        std::cout << std::endl;
        std::cout << "🎉 All tests passed! Core architecture is working correctly." << std::endl;
        std::cout << std::endl;
        std::cout << "Next steps:" << std::endl;
        std::cout << "1. Implement OpenGL rendering" << std::endl;
        std::cout << "2. Add Python integration" << std::endl;
        std::cout << "3. Complete audio and physics systems" << std::endl;
        
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "❌ Test failed with exception: " << e.what() << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "❌ Test failed with unknown exception" << std::endl;
        return 1;
    }
}
