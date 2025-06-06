/**
 * Lupine Engine - Windows Platform Implementation
 */

#ifdef WINDOWS_ENABLED

#include "platform_windows.h"
#include <iostream>
#include <sstream>
#include <GL/gl.h>
#include <GL/wglext.h>

namespace lupine {

    // Static members
    const wchar_t* PlatformWindows::WINDOW_CLASS_NAME = L"LupineEngineWindow";
    bool PlatformWindows::class_registered_ = false;

    PlatformWindows::PlatformWindows() {
        hinstance_ = GetModuleHandle(nullptr);
        
        // Initialize performance counter
        QueryPerformanceFrequency(&performance_frequency_);
        QueryPerformanceCounter(&performance_counter_start_);
        
        setup_key_mapping();
    }

    PlatformWindows::~PlatformWindows() {
        shutdown();
    }

    bool PlatformWindows::initialize(const WindowConfig& config) {
        if (initialized_) {
            return true;
        }

        config_ = config;

        if (!register_window_class()) {
            std::cerr << "[Platform] Failed to register window class" << std::endl;
            return false;
        }

        initialized_ = true;
        return true;
    }

    void PlatformWindows::shutdown() {
        if (!initialized_) {
            return;
        }

        destroy_opengl_context();
        destroy_window();
        unregister_window_class();
        
        initialized_ = false;
    }

    bool PlatformWindows::create_window() {
        if (window_created_) {
            return true;
        }

        DWORD style = WS_OVERLAPPEDWINDOW;
        DWORD ex_style = WS_EX_APPWINDOW | WS_EX_WINDOWEDGE;

        if (config_.fullscreen) {
            style = WS_POPUP;
            ex_style = WS_EX_APPWINDOW;
        }

        // Calculate window size including borders
        RECT rect = { 0, 0, config_.width, config_.height };
        AdjustWindowRectEx(&rect, style, FALSE, ex_style);
        
        int window_width = rect.right - rect.left;
        int window_height = rect.bottom - rect.top;

        // Convert title to wide string
        std::wstring wide_title;
        wide_title.assign(config_.title.begin(), config_.title.end());

        // Create window
        hwnd_ = CreateWindowExW(
            ex_style,
            WINDOW_CLASS_NAME,
            wide_title.c_str(),
            style,
            CW_USEDEFAULT, CW_USEDEFAULT,
            window_width, window_height,
            nullptr, nullptr,
            hinstance_,
            this  // Pass this pointer to WM_CREATE
        );

        if (!hwnd_) {
            std::cerr << "[Platform] Failed to create window. Error: " << GetLastError() << std::endl;
            return false;
        }

        // Get device context
        hdc_ = GetDC(hwnd_);
        if (!hdc_) {
            std::cerr << "[Platform] Failed to get device context" << std::endl;
            destroy_window();
            return false;
        }

        // Center window if not fullscreen
        if (!config_.fullscreen) {
            center_window();
        }

        window_created_ = true;
        return true;
    }

    void PlatformWindows::destroy_window() {
        if (!window_created_) {
            return;
        }

        if (hdc_) {
            ReleaseDC(hwnd_, hdc_);
            hdc_ = nullptr;
        }

        if (hwnd_) {
            DestroyWindow(hwnd_);
            hwnd_ = nullptr;
        }

        window_created_ = false;
    }

    void PlatformWindows::show_window() {
        if (hwnd_) {
            ShowWindow(hwnd_, SW_SHOW);
            SetForegroundWindow(hwnd_);
            SetFocus(hwnd_);
        }
    }

    void PlatformWindows::hide_window() {
        if (hwnd_) {
            ShowWindow(hwnd_, SW_HIDE);
        }
    }

    void PlatformWindows::set_window_title(const String& title) {
        if (hwnd_) {
            std::wstring wide_title;
            wide_title.assign(title.begin(), title.end());
            SetWindowTextW(hwnd_, wide_title.c_str());
        }
        config_.title = title;
    }

    void PlatformWindows::set_window_size(int width, int height) {
        if (!hwnd_ || fullscreen_) {
            return;
        }

        RECT rect = { 0, 0, width, height };
        DWORD style = GetWindowLong(hwnd_, GWL_STYLE);
        DWORD ex_style = GetWindowLong(hwnd_, GWL_EXSTYLE);
        
        AdjustWindowRectEx(&rect, style, FALSE, ex_style);
        
        SetWindowPos(hwnd_, nullptr, 0, 0, 
                    rect.right - rect.left, rect.bottom - rect.top,
                    SWP_NOMOVE | SWP_NOZORDER);
        
        config_.width = width;
        config_.height = height;
    }

    void PlatformWindows::set_window_position(int x, int y) {
        if (hwnd_ && !fullscreen_) {
            SetWindowPos(hwnd_, nullptr, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER);
        }
    }

    Vector2 PlatformWindows::get_window_size() const {
        if (!hwnd_) {
            return Vector2(config_.width, config_.height);
        }

        RECT rect;
        GetClientRect(hwnd_, &rect);
        return Vector2(rect.right - rect.left, rect.bottom - rect.top);
    }

    Vector2 PlatformWindows::get_window_position() const {
        if (!hwnd_) {
            return Vector2::ZERO;
        }

        RECT rect;
        GetWindowRect(hwnd_, &rect);
        return Vector2(rect.left, rect.top);
    }

    bool PlatformWindows::is_window_focused() const {
        return hwnd_ && GetForegroundWindow() == hwnd_;
    }

    bool PlatformWindows::is_window_minimized() const {
        return hwnd_ && IsIconic(hwnd_);
    }

    void PlatformWindows::set_fullscreen(bool fullscreen) {
        if (!hwnd_ || fullscreen_ == fullscreen) {
            return;
        }

        if (fullscreen) {
            // Save current window state
            GetWindowRect(hwnd_, &windowed_rect_);
            windowed_style_ = GetWindowLong(hwnd_, GWL_STYLE);

            // Get monitor info
            HMONITOR monitor = MonitorFromWindow(hwnd_, MONITOR_DEFAULTTOPRIMARY);
            MONITORINFO monitor_info = { sizeof(monitor_info) };
            GetMonitorInfo(monitor, &monitor_info);

            // Set fullscreen style
            SetWindowLong(hwnd_, GWL_STYLE, WS_POPUP);
            SetWindowPos(hwnd_, HWND_TOP,
                        monitor_info.rcMonitor.left, monitor_info.rcMonitor.top,
                        monitor_info.rcMonitor.right - monitor_info.rcMonitor.left,
                        monitor_info.rcMonitor.bottom - monitor_info.rcMonitor.top,
                        SWP_FRAMECHANGED);
        } else {
            // Restore windowed mode
            SetWindowLong(hwnd_, GWL_STYLE, windowed_style_);
            SetWindowPos(hwnd_, nullptr,
                        windowed_rect_.left, windowed_rect_.top,
                        windowed_rect_.right - windowed_rect_.left,
                        windowed_rect_.bottom - windowed_rect_.top,
                        SWP_FRAMECHANGED);
        }

        fullscreen_ = fullscreen;
        config_.fullscreen = fullscreen;
    }

    bool PlatformWindows::is_fullscreen() const {
        return fullscreen_;
    }

    bool PlatformWindows::create_opengl_context() {
        if (opengl_context_created_ || !hdc_) {
            return opengl_context_created_;
        }

        if (!setup_pixel_format()) {
            std::cerr << "[Platform] Failed to setup pixel format" << std::endl;
            return false;
        }

        // Create temporary context for loading extensions
        HGLRC temp_context = wglCreateContext(hdc_);
        if (!temp_context) {
            std::cerr << "[Platform] Failed to create temporary OpenGL context" << std::endl;
            return false;
        }

        wglMakeCurrent(hdc_, temp_context);
        
        // Load WGL extensions
        if (!load_wgl_extensions()) {
            std::cerr << "[Platform] Failed to load WGL extensions" << std::endl;
            wglMakeCurrent(nullptr, nullptr);
            wglDeleteContext(temp_context);
            return false;
        }

        // Create core context if available
        if (wglCreateContextAttribsARB) {
            if (!create_opengl_context_core()) {
                std::cerr << "[Platform] Failed to create core OpenGL context, using compatibility" << std::endl;
                hglrc_ = temp_context;
            } else {
                wglMakeCurrent(nullptr, nullptr);
                wglDeleteContext(temp_context);
            }
        } else {
            hglrc_ = temp_context;
        }

        wglMakeCurrent(hdc_, hglrc_);
        
        // Set VSync
        set_vsync(config_.vsync);

        opengl_context_created_ = true;
        return true;
    }

    void PlatformWindows::destroy_opengl_context() {
        if (!opengl_context_created_) {
            return;
        }

        wglMakeCurrent(nullptr, nullptr);
        
        if (hglrc_) {
            wglDeleteContext(hglrc_);
            hglrc_ = nullptr;
        }

        opengl_context_created_ = false;
    }

    void PlatformWindows::swap_buffers() {
        if (hdc_) {
            SwapBuffers(hdc_);
        }
    }

    void PlatformWindows::set_vsync(bool enabled) {
        if (wglSwapIntervalEXT) {
            wglSwapIntervalEXT(enabled ? 1 : 0);
            vsync_enabled_ = enabled;
        }
    }

    bool PlatformWindows::is_vsync_enabled() const {
        if (wglGetSwapIntervalEXT) {
            return wglGetSwapIntervalEXT() != 0;
        }
        return vsync_enabled_;
    }

    void PlatformWindows::poll_events() {
        MSG msg;
        while (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    void PlatformWindows::set_event_callback(const EventCallback& callback) {
        event_callback_ = callback;
    }

    bool PlatformWindows::is_key_pressed(int key_code) const {
        return pressed_keys_.find(key_code) != pressed_keys_.end();
    }

    bool PlatformWindows::is_mouse_button_pressed(int button) const {
        return pressed_mouse_buttons_.find(button) != pressed_mouse_buttons_.end();
    }

    Vector2 PlatformWindows::get_mouse_position() const {
        return mouse_position_;
    }

    void PlatformWindows::set_mouse_position(const Vector2& position) {
        if (hwnd_) {
            POINT pt = { static_cast<LONG>(position.x), static_cast<LONG>(position.y) };
            ClientToScreen(hwnd_, &pt);
            SetCursorPos(pt.x, pt.y);
        }
    }

    void PlatformWindows::set_cursor_visible(bool visible) {
        if (cursor_visible_ != visible) {
            ShowCursor(visible ? TRUE : FALSE);
            cursor_visible_ = visible;
        }
    }

    bool PlatformWindows::is_cursor_visible() const {
        return cursor_visible_;
    }

    String PlatformWindows::get_clipboard_text() const {
        if (!OpenClipboard(hwnd_)) {
            return "";
        }

        HANDLE data = GetClipboardData(CF_UNICODETEXT);
        if (!data) {
            CloseClipboard();
            return "";
        }

        wchar_t* text = static_cast<wchar_t*>(GlobalLock(data));
        if (!text) {
            CloseClipboard();
            return "";
        }

        // Convert wide string to UTF-8
        int size = WideCharToMultiByte(CP_UTF8, 0, text, -1, nullptr, 0, nullptr, nullptr);
        String result(size - 1, '\0');
        WideCharToMultiByte(CP_UTF8, 0, text, -1, &result[0], size, nullptr, nullptr);

        GlobalUnlock(data);
        CloseClipboard();
        return result;
    }

    void PlatformWindows::set_clipboard_text(const String& text) {
        if (!OpenClipboard(hwnd_)) {
            return;
        }

        EmptyClipboard();

        // Convert UTF-8 to wide string
        int size = MultiByteToWideChar(CP_UTF8, 0, text.c_str(), -1, nullptr, 0);
        wchar_t* wide_text = new wchar_t[size];
        MultiByteToWideChar(CP_UTF8, 0, text.c_str(), -1, wide_text, size);

        HGLOBAL mem = GlobalAlloc(GMEM_MOVEABLE, size * sizeof(wchar_t));
        if (mem) {
            wchar_t* dest = static_cast<wchar_t*>(GlobalLock(mem));
            wcscpy_s(dest, size, wide_text);
            GlobalUnlock(mem);
            SetClipboardData(CF_UNICODETEXT, mem);
        }

        delete[] wide_text;
        CloseClipboard();
    }

    String PlatformWindows::get_executable_path() const {
        wchar_t path[MAX_PATH];
        GetModuleFileNameW(nullptr, path, MAX_PATH);

        // Convert to UTF-8
        int size = WideCharToMultiByte(CP_UTF8, 0, path, -1, nullptr, 0, nullptr, nullptr);
        String result(size - 1, '\0');
        WideCharToMultiByte(CP_UTF8, 0, path, -1, &result[0], size, nullptr, nullptr);

        return result;
    }

    String PlatformWindows::get_user_data_dir() const {
        wchar_t* path;
        if (SHGetKnownFolderPath(FOLDERID_RoamingAppData, 0, nullptr, &path) == S_OK) {
            // Convert to UTF-8
            int size = WideCharToMultiByte(CP_UTF8, 0, path, -1, nullptr, 0, nullptr, nullptr);
            String result(size - 1, '\0');
            WideCharToMultiByte(CP_UTF8, 0, path, -1, &result[0], size, nullptr, nullptr);

            CoTaskMemFree(path);
            return result + "\\LupineEngine";
        }
        return "";
    }

    bool PlatformWindows::file_exists(const String& path) const {
        DWORD attrib = GetFileAttributesA(path.c_str());
        return (attrib != INVALID_FILE_ATTRIBUTES && !(attrib & FILE_ATTRIBUTE_DIRECTORY));
    }

    bool PlatformWindows::directory_exists(const String& path) const {
        DWORD attrib = GetFileAttributesA(path.c_str());
        return (attrib != INVALID_FILE_ATTRIBUTES && (attrib & FILE_ATTRIBUTE_DIRECTORY));
    }

    uint64_t PlatformWindows::get_ticks_msec() const {
        LARGE_INTEGER current;
        QueryPerformanceCounter(&current);
        return ((current.QuadPart - performance_counter_start_.QuadPart) * 1000) / performance_frequency_.QuadPart;
    }

    uint64_t PlatformWindows::get_ticks_usec() const {
        LARGE_INTEGER current;
        QueryPerformanceCounter(&current);
        return ((current.QuadPart - performance_counter_start_.QuadPart) * 1000000) / performance_frequency_.QuadPart;
    }

    void PlatformWindows::delay_msec(uint32_t msec) const {
        Sleep(msec);
    }

    int PlatformWindows::get_processor_count() const {
        SYSTEM_INFO sys_info;
        GetSystemInfo(&sys_info);
        return sys_info.dwNumberOfProcessors;
    }

    uint64_t PlatformWindows::get_memory_usage() const {
        PROCESS_MEMORY_COUNTERS pmc;
        if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc))) {
            return pmc.WorkingSetSize;
        }
        return 0;
    }

    // Helper methods implementation
    bool PlatformWindows::register_window_class() {
        if (class_registered_) {
            return true;
        }

        WNDCLASSEXW wc = {};
        wc.cbSize = sizeof(WNDCLASSEXW);
        wc.style = CS_HREDRAW | CS_VREDRAW | CS_OWNDC;
        wc.lpfnWndProc = window_proc;
        wc.hInstance = hinstance_;
        wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
        wc.hbrBackground = nullptr;
        wc.lpszClassName = WINDOW_CLASS_NAME;
        wc.hIcon = LoadIcon(nullptr, IDI_APPLICATION);
        wc.hIconSm = LoadIcon(nullptr, IDI_APPLICATION);

        if (!RegisterClassExW(&wc)) {
            return false;
        }

        class_registered_ = true;
        return true;
    }

    void PlatformWindows::unregister_window_class() {
        if (class_registered_) {
            UnregisterClassW(WINDOW_CLASS_NAME, hinstance_);
            class_registered_ = false;
        }
    }

    void PlatformWindows::setup_key_mapping() {
        // Map Windows virtual key codes to our key codes
        key_map_[VK_ESCAPE] = KeyCode::ESCAPE;
        key_map_[VK_RETURN] = KeyCode::RETURN;
        key_map_[VK_BACK] = KeyCode::BACKSPACE;
        key_map_[VK_TAB] = KeyCode::TAB;
        key_map_[VK_SPACE] = KeyCode::SPACE;

        // Function keys
        key_map_[VK_F1] = KeyCode::F1;
        key_map_[VK_F2] = KeyCode::F2;
        key_map_[VK_F3] = KeyCode::F3;
        key_map_[VK_F4] = KeyCode::F4;
        key_map_[VK_F5] = KeyCode::F5;
        key_map_[VK_F6] = KeyCode::F6;
        key_map_[VK_F7] = KeyCode::F7;
        key_map_[VK_F8] = KeyCode::F8;
        key_map_[VK_F9] = KeyCode::F9;
        key_map_[VK_F10] = KeyCode::F10;
        key_map_[VK_F11] = KeyCode::F11;
        key_map_[VK_F12] = KeyCode::F12;

        // Arrow keys
        key_map_[VK_LEFT] = KeyCode::LEFT;
        key_map_[VK_RIGHT] = KeyCode::RIGHT;
        key_map_[VK_UP] = KeyCode::UP;
        key_map_[VK_DOWN] = KeyCode::DOWN;

        // Letters
        for (int i = 0; i < 26; ++i) {
            key_map_['A' + i] = KeyCode::A + i;
        }

        // Numbers
        for (int i = 0; i < 10; ++i) {
            key_map_['0' + i] = KeyCode::NUM_0 + i;
        }

        // Modifiers
        key_map_[VK_LCONTROL] = KeyCode::LCTRL;
        key_map_[VK_RCONTROL] = KeyCode::RCTRL;
        key_map_[VK_LSHIFT] = KeyCode::LSHIFT;
        key_map_[VK_RSHIFT] = KeyCode::RSHIFT;
        key_map_[VK_LMENU] = KeyCode::LALT;
        key_map_[VK_RMENU] = KeyCode::RALT;
    }

    void PlatformWindows::center_window() {
        if (!hwnd_) {
            return;
        }

        RECT window_rect;
        GetWindowRect(hwnd_, &window_rect);

        int window_width = window_rect.right - window_rect.left;
        int window_height = window_rect.bottom - window_rect.top;

        int screen_width = GetSystemMetrics(SM_CXSCREEN);
        int screen_height = GetSystemMetrics(SM_CYSCREEN);

        int x = (screen_width - window_width) / 2;
        int y = (screen_height - window_height) / 2;

        SetWindowPos(hwnd_, nullptr, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER);
    }

    int PlatformWindows::translate_key(WPARAM wparam, LPARAM lparam) {
        auto it = key_map_.find(wparam);
        if (it != key_map_.end()) {
            return it->second;
        }
        return KeyCode::UNKNOWN;
    }

    int PlatformWindows::translate_mouse_button(WPARAM wparam) {
        if (wparam & MK_LBUTTON) return MouseButton::LEFT;
        if (wparam & MK_RBUTTON) return MouseButton::RIGHT;
        if (wparam & MK_MBUTTON) return MouseButton::MIDDLE;
        if (wparam & MK_XBUTTON1) return MouseButton::X1;
        if (wparam & MK_XBUTTON2) return MouseButton::X2;
        return 0;
    }

    uint32_t PlatformWindows::get_current_modifiers() {
        uint32_t modifiers = ModifierKey::NONE;

        if (GetKeyState(VK_LSHIFT) & 0x8000) modifiers |= ModifierKey::LSHIFT;
        if (GetKeyState(VK_RSHIFT) & 0x8000) modifiers |= ModifierKey::RSHIFT;
        if (GetKeyState(VK_LCONTROL) & 0x8000) modifiers |= ModifierKey::LCTRL;
        if (GetKeyState(VK_RCONTROL) & 0x8000) modifiers |= ModifierKey::RCTRL;
        if (GetKeyState(VK_LMENU) & 0x8000) modifiers |= ModifierKey::LALT;
        if (GetKeyState(VK_RMENU) & 0x8000) modifiers |= ModifierKey::RALT;
        if (GetKeyState(VK_CAPITAL) & 0x0001) modifiers |= ModifierKey::CAPS;
        if (GetKeyState(VK_NUMLOCK) & 0x0001) modifiers |= ModifierKey::NUM;

        return modifiers;
    }

} // namespace lupine

#endif // WINDOWS_ENABLED
