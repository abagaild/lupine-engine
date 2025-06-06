#pragma once

/**
 * Lupine Engine - Input Management System
 * 
 * Input handling and action mapping system.
 * This is the C++ equivalent of the Python input system.
 */

#include "../core_types.h"
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace lupine {

    /**
     * Input action definition
     */
    struct InputAction {
        String name;
        std::vector<int> keys;
        std::vector<int> mouse_buttons;
        real_t deadzone = 0.1f;
    };

    /**
     * Input manager for handling keyboard, mouse, and gamepad input
     */
    class InputManager {
    public:
        InputManager();
        ~InputManager();

        // Initialization
        bool initialize();
        void cleanup();
        void update();

        // Raw input state
        bool is_key_pressed(int key_code) const;
        bool is_key_just_pressed(int key_code) const;
        bool is_key_just_released(int key_code) const;

        bool is_mouse_button_pressed(int button) const;
        bool is_mouse_button_just_pressed(int button) const;
        bool is_mouse_button_just_released(int button) const;

        Vector2 get_mouse_position() const { return mouse_position_; }
        Vector2 get_mouse_delta() const { return mouse_delta_; }
        Vector2 get_mouse_wheel_delta() const { return mouse_wheel_delta_; }

        // Action system
        void add_action(const String& name, const InputAction& action);
        void remove_action(const String& name);
        bool has_action(const String& name) const;

        bool is_action_pressed(const String& action) const;
        bool is_action_just_pressed(const String& action) const;
        bool is_action_just_released(const String& action) const;
        real_t get_action_strength(const String& action) const;

        // Input mapping
        void map_key_to_action(const String& action, int key_code);
        void map_mouse_button_to_action(const String& action, int button);
        void unmap_key_from_action(const String& action, int key_code);
        void unmap_mouse_button_from_action(const String& action, int button);

        // Configuration
        void load_input_map(const String& path);
        void save_input_map(const String& path);

        // State
        bool is_initialized() const { return initialized_; }

    private:
        bool initialized_ = false;

        // Current frame input state
        std::unordered_set<int> pressed_keys_;
        std::unordered_set<int> pressed_mouse_buttons_;
        Vector2 mouse_position_ = Vector2::ZERO;
        Vector2 mouse_delta_ = Vector2::ZERO;
        Vector2 mouse_wheel_delta_ = Vector2::ZERO;

        // Previous frame input state (for "just pressed/released" detection)
        std::unordered_set<int> prev_pressed_keys_;
        std::unordered_set<int> prev_pressed_mouse_buttons_;

        // Action system
        std::unordered_map<String, InputAction> actions_;
        std::unordered_set<String> pressed_actions_;
        std::unordered_set<String> prev_pressed_actions_;

        // Internal methods
        void update_input_state();
        void update_actions();
        bool evaluate_action(const InputAction& action) const;
        real_t calculate_action_strength(const InputAction& action) const;
    };

} // namespace lupine
