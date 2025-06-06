#pragma once

/**
 * Lupine Engine - Core Types and Utilities
 * 
 * Fundamental types, math structures, and utility classes used throughout the engine.
 */

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <unordered_map>
#include <cmath>

namespace lupine {

    // Basic types
    using real_t = float;
    using String = std::string;
    
    // Forward declarations
    class Node;
    class Variant;

    /**
     * 2D Vector class
     */
    struct Vector2 {
        real_t x = 0.0f;
        real_t y = 0.0f;

        Vector2() = default;
        Vector2(real_t x_, real_t y_) : x(x_), y(y_) {}

        Vector2 operator+(const Vector2& other) const { return Vector2(x + other.x, y + other.y); }
        Vector2 operator-(const Vector2& other) const { return Vector2(x - other.x, y - other.y); }
        Vector2 operator*(real_t scalar) const { return Vector2(x * scalar, y * scalar); }
        Vector2 operator/(real_t scalar) const { return Vector2(x / scalar, y / scalar); }
        
        Vector2& operator+=(const Vector2& other) { x += other.x; y += other.y; return *this; }
        Vector2& operator-=(const Vector2& other) { x -= other.x; y -= other.y; return *this; }
        Vector2& operator*=(real_t scalar) { x *= scalar; y *= scalar; return *this; }
        Vector2& operator/=(real_t scalar) { x /= scalar; y /= scalar; return *this; }

        bool operator==(const Vector2& other) const { return x == other.x && y == other.y; }
        bool operator!=(const Vector2& other) const { return !(*this == other); }

        real_t length() const { return std::sqrt(x * x + y * y); }
        real_t length_squared() const { return x * x + y * y; }
        Vector2 normalized() const { 
            real_t len = length(); 
            return len > 0 ? *this / len : Vector2(); 
        }
        real_t dot(const Vector2& other) const { return x * other.x + y * other.y; }
        real_t distance_to(const Vector2& other) const { return (*this - other).length(); }
        
        static const Vector2 ZERO;
        static const Vector2 ONE;
        static const Vector2 UP;
        static const Vector2 DOWN;
        static const Vector2 LEFT;
        static const Vector2 RIGHT;
    };

    /**
     * Rectangle structure
     */
    struct Rect2 {
        Vector2 position;
        Vector2 size;

        Rect2() = default;
        Rect2(real_t x, real_t y, real_t width, real_t height) 
            : position(x, y), size(width, height) {}
        Rect2(const Vector2& pos, const Vector2& sz) : position(pos), size(sz) {}

        real_t get_area() const { return size.x * size.y; }
        bool has_point(const Vector2& point) const {
            return point.x >= position.x && point.x < position.x + size.x &&
                   point.y >= position.y && point.y < position.y + size.y;
        }
        bool intersects(const Rect2& other) const {
            return !(position.x >= other.position.x + other.size.x ||
                     position.x + size.x <= other.position.x ||
                     position.y >= other.position.y + other.size.y ||
                     position.y + size.y <= other.position.y);
        }
        Vector2 get_center() const { return position + size * 0.5f; }
    };

    /**
     * Color structure (RGBA)
     */
    struct Color {
        real_t r = 1.0f;
        real_t g = 1.0f;
        real_t b = 1.0f;
        real_t a = 1.0f;

        Color() = default;
        Color(real_t r_, real_t g_, real_t b_, real_t a_ = 1.0f) : r(r_), g(g_), b(b_), a(a_) {}

        Color operator*(real_t scalar) const { return Color(r * scalar, g * scalar, b * scalar, a); }
        Color operator+(const Color& other) const { return Color(r + other.r, g + other.g, b + other.b, a + other.a); }

        uint32_t to_rgba32() const {
            return (uint32_t(r * 255) << 24) | (uint32_t(g * 255) << 16) | 
                   (uint32_t(b * 255) << 8) | uint32_t(a * 255);
        }

        static const Color WHITE;
        static const Color BLACK;
        static const Color RED;
        static const Color GREEN;
        static const Color BLUE;
        static const Color TRANSPARENT;
    };

    /**
     * Transform2D for 2D transformations
     */
    struct Transform2D {
        Vector2 x = Vector2(1, 0);  // Right vector
        Vector2 y = Vector2(0, 1);  // Up vector  
        Vector2 origin = Vector2(0, 0);  // Translation

        Transform2D() = default;
        Transform2D(real_t rotation, const Vector2& position);
        Transform2D(real_t rotation, const Vector2& scale, real_t skew, const Vector2& position);

        Vector2 transform_point(const Vector2& point) const {
            return Vector2(x.dot(point), y.dot(point)) + origin;
        }

        Transform2D operator*(const Transform2D& other) const;
        Transform2D inverse() const;
        
        void set_rotation(real_t rotation);
        real_t get_rotation() const;
        void set_scale(const Vector2& scale);
        Vector2 get_scale() const;

        static const Transform2D IDENTITY;
    };

    /**
     * Variant type for dynamic values (simplified version)
     */
    class Variant {
    public:
        enum Type {
            NIL,
            BOOL,
            INT,
            FLOAT,
            STRING,
            VECTOR2,
            RECT2,
            COLOR,
            OBJECT
        };

        Variant() : type_(NIL) {}
        Variant(bool value) : type_(BOOL), bool_value_(value) {}
        Variant(int value) : type_(INT), int_value_(value) {}
        Variant(real_t value) : type_(FLOAT), float_value_(value) {}
        Variant(const String& value) : type_(STRING), string_value_(value) {}
        Variant(const Vector2& value) : type_(VECTOR2), vector2_value_(value) {}
        Variant(const Rect2& value) : type_(RECT2), rect2_value_(value) {}
        Variant(const Color& value) : type_(COLOR), color_value_(value) {}
        Variant(Node* value) : type_(OBJECT), object_value_(value) {}

        Type get_type() const { return type_; }
        
        bool as_bool() const { return type_ == BOOL ? bool_value_ : false; }
        int as_int() const { return type_ == INT ? int_value_ : 0; }
        real_t as_float() const { return type_ == FLOAT ? float_value_ : 0.0f; }
        String as_string() const { return type_ == STRING ? string_value_ : ""; }
        Vector2 as_vector2() const { return type_ == VECTOR2 ? vector2_value_ : Vector2(); }
        Rect2 as_rect2() const { return type_ == RECT2 ? rect2_value_ : Rect2(); }
        Color as_color() const { return type_ == COLOR ? color_value_ : Color(); }
        Node* as_object() const { return type_ == OBJECT ? object_value_ : nullptr; }

    private:
        Type type_ = NIL;
        union {
            bool bool_value_;
            int int_value_;
            real_t float_value_;
            Node* object_value_;
        };
        String string_value_;
        Vector2 vector2_value_;
        Rect2 rect2_value_;
        Color color_value_;
    };

    /**
     * Signal system for node communication
     */
    class Signal {
    public:
        using Callback = std::function<void(const std::vector<Variant>&)>;
        
        void connect(const Callback& callback) {
            callbacks_.push_back(callback);
        }
        
        void emit(const std::vector<Variant>& args = {}) {
            for (const auto& callback : callbacks_) {
                callback(args);
            }
        }
        
        void disconnect_all() {
            callbacks_.clear();
        }
        
    private:
        std::vector<Callback> callbacks_;
    };

    /**
     * Resource reference system
     */
    template<typename T>
    class Ref {
    public:
        Ref() = default;
        Ref(T* ptr) : ptr_(ptr) {}
        Ref(std::shared_ptr<T> ptr) : shared_ptr_(ptr), ptr_(ptr.get()) {}

        T* operator->() const { return ptr_; }
        T& operator*() const { return *ptr_; }
        T* get() const { return ptr_; }
        
        bool is_valid() const { return ptr_ != nullptr; }
        bool is_null() const { return ptr_ == nullptr; }
        
        operator bool() const { return is_valid(); }

    private:
        std::shared_ptr<T> shared_ptr_;
        T* ptr_ = nullptr;
    };

    /**
     * Utility functions
     */
    namespace Math {
        constexpr real_t PI = 3.14159265359f;
        constexpr real_t TAU = PI * 2.0f;
        constexpr real_t DEG_TO_RAD = PI / 180.0f;
        constexpr real_t RAD_TO_DEG = 180.0f / PI;

        inline real_t deg_to_rad(real_t degrees) { return degrees * DEG_TO_RAD; }
        inline real_t rad_to_deg(real_t radians) { return radians * RAD_TO_DEG; }
        inline real_t lerp(real_t from, real_t to, real_t weight) { return from + (to - from) * weight; }
        inline real_t clamp(real_t value, real_t min, real_t max) { 
            return value < min ? min : (value > max ? max : value); 
        }
        inline real_t abs(real_t value) { return value < 0 ? -value : value; }
        inline real_t sign(real_t value) { return value < 0 ? -1.0f : (value > 0 ? 1.0f : 0.0f); }
    }

    /**
     * String utilities
     */
    namespace StringUtils {
        std::vector<String> split(const String& str, const String& delimiter);
        String join(const std::vector<String>& parts, const String& separator);
        String to_lower(const String& str);
        String to_upper(const String& str);
        bool starts_with(const String& str, const String& prefix);
        bool ends_with(const String& str, const String& suffix);
        String trim(const String& str);
    }

} // namespace lupine
