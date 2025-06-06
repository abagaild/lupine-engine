/**
 * Lupine Engine - Windows Platform Window Procedure
 * 
 * Window message handling and OpenGL setup for Windows platform.
 */

#ifdef WINDOWS_ENABLED

#include "platform_windows.h"
#include <iostream>

namespace lupine {

    LRESULT CALLBACK PlatformWindows::window_proc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
        PlatformWindows* platform = nullptr;
        
        if (msg == WM_CREATE) {
            CREATESTRUCT* create_struct = reinterpret_cast<CREATESTRUCT*>(lparam);
            platform = static_cast<PlatformWindows*>(create_struct->lpCreateParams);
            SetWindowLongPtr(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(platform));
        } else {
            platform = reinterpret_cast<PlatformWindows*>(GetWindowLongPtr(hwnd, GWLP_USERDATA));
        }
        
        if (platform) {
            return platform->handle_message(hwnd, msg, wparam, lparam);
        }
        
        return DefWindowProc(hwnd, msg, wparam, lparam);
    }

    LRESULT PlatformWindows::handle_message(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
        switch (msg) {
            case WM_CLOSE:
                if (event_callback_) {
                    InputEvent event(InputEventType::WINDOW_CLOSE);
                    event_callback_(event);
                }
                return 0;

            case WM_SIZE:
                handle_window_resize_event(lparam);
                return 0;

            case WM_KEYDOWN:
            case WM_SYSKEYDOWN:
                handle_key_event(wparam, lparam, true);
                return 0;

            case WM_KEYUP:
            case WM_SYSKEYUP:
                handle_key_event(wparam, lparam, false);
                return 0;

            case WM_LBUTTONDOWN:
            case WM_RBUTTONDOWN:
            case WM_MBUTTONDOWN:
            case WM_XBUTTONDOWN:
                handle_mouse_button_event(wparam, lparam, true);
                return 0;

            case WM_LBUTTONUP:
            case WM_RBUTTONUP:
            case WM_MBUTTONUP:
            case WM_XBUTTONUP:
                handle_mouse_button_event(wparam, lparam, false);
                return 0;

            case WM_MOUSEMOVE:
                handle_mouse_motion_event(lparam);
                return 0;

            case WM_MOUSEWHEEL:
            case WM_MOUSEHWHEEL:
                handle_mouse_wheel_event(wparam, lparam);
                return 0;

            case WM_SETFOCUS:
                // Window gained focus
                return 0;

            case WM_KILLFOCUS:
                // Window lost focus - clear input state
                pressed_keys_.clear();
                pressed_mouse_buttons_.clear();
                return 0;

            default:
                return DefWindowProc(hwnd, msg, wparam, lparam);
        }
    }

    void PlatformWindows::handle_key_event(WPARAM wparam, LPARAM lparam, bool pressed) {
        int key_code = translate_key(wparam, lparam);
        if (key_code == KeyCode::UNKNOWN) {
            return;
        }

        if (pressed) {
            pressed_keys_.insert(key_code);
        } else {
            pressed_keys_.erase(key_code);
        }

        if (event_callback_) {
            InputEvent event(pressed ? InputEventType::KEY_PRESS : InputEventType::KEY_RELEASE);
            event.key_code = key_code;
            event.scan_code = (lparam >> 16) & 0xFF;
            event.modifiers = get_current_modifiers();
            event.repeat = pressed && (lparam & (1 << 30)) != 0;
            event.timestamp = static_cast<uint32_t>(get_ticks_msec());
            event_callback_(event);
        }
    }

    void PlatformWindows::handle_mouse_button_event(WPARAM wparam, LPARAM lparam, bool pressed) {
        int button = 0;
        
        // Determine which button was pressed/released
        switch (HIWORD(wparam)) {
            case 0: // Left, right, or middle button
                if (pressed) {
                    if (wparam & MK_LBUTTON) button = MouseButton::LEFT;
                    else if (wparam & MK_RBUTTON) button = MouseButton::RIGHT;
                    else if (wparam & MK_MBUTTON) button = MouseButton::MIDDLE;
                } else {
                    // For button up events, we need to check the message type
                    UINT msg = 0;
                    if (GetMessage(reinterpret_cast<MSG*>(&msg), hwnd_, 0, 0)) {
                        // This is a simplified approach - in practice you'd track this differently
                        button = MouseButton::LEFT; // Default assumption
                    }
                }
                break;
            case XBUTTON1:
                button = MouseButton::X1;
                break;
            case XBUTTON2:
                button = MouseButton::X2;
                break;
        }

        if (button == 0) {
            return;
        }

        if (pressed) {
            pressed_mouse_buttons_.insert(button);
            SetCapture(hwnd_);
        } else {
            pressed_mouse_buttons_.erase(button);
            if (pressed_mouse_buttons_.empty()) {
                ReleaseCapture();
            }
        }

        if (event_callback_) {
            InputEvent event(pressed ? InputEventType::MOUSE_BUTTON_PRESS : InputEventType::MOUSE_BUTTON_RELEASE);
            event.mouse_button = button;
            event.mouse_position = Vector2(GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam));
            event.modifiers = get_current_modifiers();
            event.timestamp = static_cast<uint32_t>(get_ticks_msec());
            event_callback_(event);
        }
    }

    void PlatformWindows::handle_mouse_motion_event(LPARAM lparam) {
        Vector2 new_position(GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam));
        Vector2 delta = new_position - mouse_position_;
        mouse_position_ = new_position;

        if (event_callback_) {
            InputEvent event(InputEventType::MOUSE_MOTION);
            event.mouse_position = new_position;
            event.mouse_delta = delta;
            event.modifiers = get_current_modifiers();
            event.timestamp = static_cast<uint32_t>(get_ticks_msec());
            event_callback_(event);
        }
    }

    void PlatformWindows::handle_mouse_wheel_event(WPARAM wparam, LPARAM lparam) {
        float delta = GET_WHEEL_DELTA_WPARAM(wparam) / static_cast<float>(WHEEL_DELTA);
        
        if (event_callback_) {
            InputEvent event(InputEventType::MOUSE_WHEEL);
            event.mouse_position = Vector2(GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam));
            
            // Convert screen coordinates to client coordinates
            POINT pt = { static_cast<LONG>(event.mouse_position.x), static_cast<LONG>(event.mouse_position.y) };
            ScreenToClient(hwnd_, &pt);
            event.mouse_position = Vector2(pt.x, pt.y);
            
            // Determine wheel direction
            UINT msg = 0;
            if (GetMessage(reinterpret_cast<MSG*>(&msg), hwnd_, 0, 0)) {
                if (msg == WM_MOUSEWHEEL) {
                    event.wheel_delta = Vector2(0.0f, delta);
                } else if (msg == WM_MOUSEHWHEEL) {
                    event.wheel_delta = Vector2(delta, 0.0f);
                }
            }
            
            event.modifiers = get_current_modifiers();
            event.timestamp = static_cast<uint32_t>(get_ticks_msec());
            event_callback_(event);
        }
    }

    void PlatformWindows::handle_window_resize_event(LPARAM lparam) {
        Vector2 new_size(LOWORD(lparam), HIWORD(lparam));
        
        if (event_callback_) {
            InputEvent event(InputEventType::WINDOW_RESIZE);
            event.window_size = new_size;
            event.timestamp = static_cast<uint32_t>(get_ticks_msec());
            event_callback_(event);
        }
    }

} // namespace lupine

#endif // WINDOWS_ENABLED
