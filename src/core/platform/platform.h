#pragma once

/**
 * Lupine Engine - Platform Abstraction Layer
 * 
 * Cross-platform interface for window management, OpenGL context, and input handling.
 * Based on the Python engine's platform requirements but designed for C++.
 */

#include "../core_types.h"
#include <functional>
#include <memory>

namespace lupine {

    // Forward declarations
    class InputEvent;
    
    /**
     * Platform-specific window configuration
     */
    struct WindowConfig {
        String title = "Lupine Engine";
        int width = 1280;
        int height = 720;
        int game_bounds_width = 1920;
        int game_bounds_height = 1080;
        String scaling_mode = "stretch";  // stretch, letterbox, crop
        String scaling_filter = "linear"; // linear, nearest
        bool fullscreen = false;
        bool resizable = true;
        bool vsync = true;
        bool show_cursor = true;
        Vector2 position = Vector2(-1, -1);  // -1 means center
    };

    /**
     * Input event types
     */
    enum class InputEventType {
        KEY_PRESS,
        KEY_RELEASE,
        MOUSE_BUTTON_PRESS,
        MOUSE_BUTTON_RELEASE,
        MOUSE_MOTION,
        MOUSE_WHEEL,
        WINDOW_RESIZE,
        WINDOW_CLOSE,
        GAMEPAD_BUTTON_PRESS,
        GAMEPAD_BUTTON_RELEASE,
        GAMEPAD_AXIS_MOTION
    };

    /**
     * Input event structure
     */
    class InputEvent {
    public:
        InputEventType type;
        uint32_t timestamp = 0;
        
        // Key events
        int key_code = 0;
        int scan_code = 0;
        uint32_t modifiers = 0;
        bool repeat = false;
        
        // Mouse events
        int mouse_button = 0;
        Vector2 mouse_position = Vector2::ZERO;
        Vector2 mouse_delta = Vector2::ZERO;
        Vector2 wheel_delta = Vector2::ZERO;
        
        // Window events
        Vector2 window_size = Vector2::ZERO;
        
        // Gamepad events
        int gamepad_id = 0;
        int gamepad_button = 0;
        int gamepad_axis = 0;
        real_t axis_value = 0.0f;
        
        InputEvent(InputEventType event_type) : type(event_type) {}
    };

    /**
     * Platform interface - abstract base class for platform implementations
     */
    class Platform {
    public:
        using EventCallback = std::function<void(const InputEvent&)>;
        
        virtual ~Platform() = default;
        
        // Window management
        virtual bool initialize(const WindowConfig& config) = 0;
        virtual void shutdown() = 0;
        virtual bool create_window() = 0;
        virtual void destroy_window() = 0;
        virtual void show_window() = 0;
        virtual void hide_window() = 0;
        virtual void set_window_title(const String& title) = 0;
        virtual void set_window_size(int width, int height) = 0;
        virtual void set_window_position(int x, int y) = 0;
        virtual Vector2 get_window_size() const = 0;
        virtual Vector2 get_window_position() const = 0;
        virtual bool is_window_focused() const = 0;
        virtual bool is_window_minimized() const = 0;
        virtual void set_fullscreen(bool fullscreen) = 0;
        virtual bool is_fullscreen() const = 0;
        
        // OpenGL context
        virtual bool create_opengl_context() = 0;
        virtual void destroy_opengl_context() = 0;
        virtual void swap_buffers() = 0;
        virtual void set_vsync(bool enabled) = 0;
        virtual bool is_vsync_enabled() const = 0;
        
        // Event handling
        virtual void poll_events() = 0;
        virtual void set_event_callback(const EventCallback& callback) = 0;
        
        // Input state
        virtual bool is_key_pressed(int key_code) const = 0;
        virtual bool is_mouse_button_pressed(int button) const = 0;
        virtual Vector2 get_mouse_position() const = 0;
        virtual void set_mouse_position(const Vector2& position) = 0;
        virtual void set_cursor_visible(bool visible) = 0;
        virtual bool is_cursor_visible() const = 0;
        
        // Clipboard
        virtual String get_clipboard_text() const = 0;
        virtual void set_clipboard_text(const String& text) = 0;
        
        // File system
        virtual String get_executable_path() const = 0;
        virtual String get_user_data_dir() const = 0;
        virtual bool file_exists(const String& path) const = 0;
        virtual bool directory_exists(const String& path) const = 0;
        
        // Time
        virtual uint64_t get_ticks_msec() const = 0;
        virtual uint64_t get_ticks_usec() const = 0;
        virtual void delay_msec(uint32_t msec) const = 0;
        
        // System info
        virtual String get_platform_name() const = 0;
        virtual int get_processor_count() const = 0;
        virtual uint64_t get_memory_usage() const = 0;
        
        // Static factory method
        static std::unique_ptr<Platform> create();
        
    protected:
        WindowConfig config_;
        EventCallback event_callback_;
        bool initialized_ = false;
        bool window_created_ = false;
        bool opengl_context_created_ = false;
    };

    /**
     * Key codes (based on SDL2 scancodes for consistency)
     */
    namespace KeyCode {
        constexpr int UNKNOWN = 0;
        constexpr int A = 4;
        constexpr int B = 5;
        constexpr int C = 6;
        constexpr int D = 7;
        constexpr int E = 8;
        constexpr int F = 9;
        constexpr int G = 10;
        constexpr int H = 11;
        constexpr int I = 12;
        constexpr int J = 13;
        constexpr int K = 14;
        constexpr int L = 15;
        constexpr int M = 16;
        constexpr int N = 17;
        constexpr int O = 18;
        constexpr int P = 19;
        constexpr int Q = 20;
        constexpr int R = 21;
        constexpr int S = 22;
        constexpr int T = 23;
        constexpr int U = 24;
        constexpr int V = 25;
        constexpr int W = 26;
        constexpr int X = 27;
        constexpr int Y = 28;
        constexpr int Z = 29;
        
        constexpr int NUM_1 = 30;
        constexpr int NUM_2 = 31;
        constexpr int NUM_3 = 32;
        constexpr int NUM_4 = 33;
        constexpr int NUM_5 = 34;
        constexpr int NUM_6 = 35;
        constexpr int NUM_7 = 36;
        constexpr int NUM_8 = 37;
        constexpr int NUM_9 = 38;
        constexpr int NUM_0 = 39;
        
        constexpr int RETURN = 40;
        constexpr int ESCAPE = 41;
        constexpr int BACKSPACE = 42;
        constexpr int TAB = 43;
        constexpr int SPACE = 44;
        
        constexpr int F1 = 58;
        constexpr int F2 = 59;
        constexpr int F3 = 60;
        constexpr int F4 = 61;
        constexpr int F5 = 62;
        constexpr int F6 = 63;
        constexpr int F7 = 64;
        constexpr int F8 = 65;
        constexpr int F9 = 66;
        constexpr int F10 = 67;
        constexpr int F11 = 68;
        constexpr int F12 = 69;
        
        constexpr int RIGHT = 79;
        constexpr int LEFT = 80;
        constexpr int DOWN = 81;
        constexpr int UP = 82;
        
        constexpr int LCTRL = 224;
        constexpr int LSHIFT = 225;
        constexpr int LALT = 226;
        constexpr int RCTRL = 228;
        constexpr int RSHIFT = 229;
        constexpr int RALT = 230;
    }

    /**
     * Mouse button codes
     */
    namespace MouseButton {
        constexpr int LEFT = 1;
        constexpr int MIDDLE = 2;
        constexpr int RIGHT = 3;
        constexpr int X1 = 4;
        constexpr int X2 = 5;
    }

    /**
     * Modifier key flags
     */
    namespace ModifierKey {
        constexpr uint32_t NONE = 0;
        constexpr uint32_t LSHIFT = 1 << 0;
        constexpr uint32_t RSHIFT = 1 << 1;
        constexpr uint32_t LCTRL = 1 << 2;
        constexpr uint32_t RCTRL = 1 << 3;
        constexpr uint32_t LALT = 1 << 4;
        constexpr uint32_t RALT = 1 << 5;
        constexpr uint32_t LGUI = 1 << 6;
        constexpr uint32_t RGUI = 1 << 7;
        constexpr uint32_t NUM = 1 << 8;
        constexpr uint32_t CAPS = 1 << 9;
        constexpr uint32_t MODE = 1 << 10;
        constexpr uint32_t SCROLL = 1 << 11;
        
        constexpr uint32_t CTRL = LCTRL | RCTRL;
        constexpr uint32_t SHIFT = LSHIFT | RSHIFT;
        constexpr uint32_t ALT = LALT | RALT;
        constexpr uint32_t GUI = LGUI | RGUI;
    }

} // namespace lupine
