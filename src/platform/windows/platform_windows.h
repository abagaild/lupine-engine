#pragma once

/**
 * Lupine Engine - Windows Platform Implementation
 * 
 * Windows-specific implementation of the platform abstraction layer.
 * Uses Win32 API for window management and WGL for OpenGL context.
 */

#ifdef WINDOWS_ENABLED

#include "../../core/platform/platform.h"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <unordered_map>
#include <unordered_set>

namespace lupine {

    /**
     * Windows platform implementation
     */
    class PlatformWindows : public Platform {
    public:
        PlatformWindows();
        virtual ~PlatformWindows();

        // Platform interface implementation
        bool initialize(const WindowConfig& config) override;
        void shutdown() override;
        bool create_window() override;
        void destroy_window() override;
        void show_window() override;
        void hide_window() override;
        void set_window_title(const String& title) override;
        void set_window_size(int width, int height) override;
        void set_window_position(int x, int y) override;
        Vector2 get_window_size() const override;
        Vector2 get_window_position() const override;
        bool is_window_focused() const override;
        bool is_window_minimized() const override;
        void set_fullscreen(bool fullscreen) override;
        bool is_fullscreen() const override;

        // OpenGL context
        bool create_opengl_context() override;
        void destroy_opengl_context() override;
        void swap_buffers() override;
        void set_vsync(bool enabled) override;
        bool is_vsync_enabled() const override;

        // Event handling
        void poll_events() override;
        void set_event_callback(const EventCallback& callback) override;

        // Input state
        bool is_key_pressed(int key_code) const override;
        bool is_mouse_button_pressed(int button) const override;
        Vector2 get_mouse_position() const override;
        void set_mouse_position(const Vector2& position) override;
        void set_cursor_visible(bool visible) override;
        bool is_cursor_visible() const override;

        // Clipboard
        String get_clipboard_text() const override;
        void set_clipboard_text(const String& text) override;

        // File system
        String get_executable_path() const override;
        String get_user_data_dir() const override;
        bool file_exists(const String& path) const override;
        bool directory_exists(const String& path) const override;

        // Time
        uint64_t get_ticks_msec() const override;
        uint64_t get_ticks_usec() const override;
        void delay_msec(uint32_t msec) const override;

        // System info
        String get_platform_name() const override { return "Windows"; }
        int get_processor_count() const override;
        uint64_t get_memory_usage() const override;

    private:
        HWND hwnd_ = nullptr;
        HDC hdc_ = nullptr;
        HGLRC hglrc_ = nullptr;
        HINSTANCE hinstance_ = nullptr;
        
        bool fullscreen_ = false;
        bool cursor_visible_ = true;
        bool vsync_enabled_ = true;
        
        // Window state for fullscreen toggle
        RECT windowed_rect_ = {};
        DWORD windowed_style_ = 0;
        
        // Input state
        std::unordered_set<int> pressed_keys_;
        std::unordered_set<int> pressed_mouse_buttons_;
        Vector2 mouse_position_ = Vector2::ZERO;
        
        // Key mapping
        std::unordered_map<WPARAM, int> key_map_;
        
        // Performance counter for high-resolution timing
        LARGE_INTEGER performance_frequency_;
        LARGE_INTEGER performance_counter_start_;
        
        // Window class registration
        static const wchar_t* WINDOW_CLASS_NAME;
        static bool class_registered_;
        
        // Helper methods
        bool register_window_class();
        void unregister_window_class();
        void setup_key_mapping();
        void update_window_style();
        void center_window();
        int translate_key(WPARAM wparam, LPARAM lparam);
        int translate_mouse_button(WPARAM wparam);
        uint32_t get_current_modifiers();
        
        // OpenGL setup
        bool setup_pixel_format();
        bool create_opengl_context_core();
        bool load_wgl_extensions();
        
        // WGL function pointers
        typedef BOOL (WINAPI *PFNWGLSWAPINTERVALEXTPROC)(int interval);
        typedef int (WINAPI *PFNWGLGETSWAPINTERVALEXTPROC)(void);
        typedef HGLRC (WINAPI *PFNWGLCREATECONTEXTATTRIBSARBPROC)(HDC hDC, HGLRC hShareContext, const int *attribList);
        
        PFNWGLSWAPINTERVALEXTPROC wglSwapIntervalEXT = nullptr;
        PFNWGLGETSWAPINTERVALEXTPROC wglGetSwapIntervalEXT = nullptr;
        PFNWGLCREATECONTEXTATTRIBSARBPROC wglCreateContextAttribsARB = nullptr;
        
        // Window procedure
        static LRESULT CALLBACK window_proc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam);
        LRESULT handle_message(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam);
        
        // Event handling helpers
        void handle_key_event(WPARAM wparam, LPARAM lparam, bool pressed);
        void handle_mouse_button_event(WPARAM wparam, LPARAM lparam, bool pressed);
        void handle_mouse_motion_event(LPARAM lparam);
        void handle_mouse_wheel_event(WPARAM wparam, LPARAM lparam);
        void handle_window_resize_event(LPARAM lparam);
    };

} // namespace lupine

#endif // WINDOWS_ENABLED
