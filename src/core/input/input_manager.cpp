/**
 * Lupine Engine - Input Manager Implementation
 */

#include "input_manager.h"
#include <iostream>
#include <algorithm>

namespace lupine {

    InputManager::InputManager() {
    }

    InputManager::~InputManager() {
        cleanup();
    }

    bool InputManager::initialize() {
        if (initialized_) {
            return true;
        }

        std::cout << "[InputManager] Initializing input manager..." << std::endl;

        // TODO: Setup default input actions
        // Add common actions like "ui_accept", "ui_cancel", etc.

        initialized_ = true;
        std::cout << "[InputManager] Input manager initialized successfully" << std::endl;
        return true;
    }

    void InputManager::cleanup() {
        if (!initialized_) {
            return;
        }

        std::cout << "[InputManager] Cleaning up input manager..." << std::endl;

        actions_.clear();
        pressed_keys_.clear();
        pressed_mouse_buttons_.clear();
        pressed_actions_.clear();

        initialized_ = false;
    }

    void InputManager::update() {
        if (!initialized_) {
            return;
        }

        // Store previous frame state
        prev_pressed_keys_ = pressed_keys_;
        prev_pressed_mouse_buttons_ = pressed_mouse_buttons_;
        prev_pressed_actions_ = pressed_actions_;

        // Update input state from platform
        update_input_state();

        // Update actions
        update_actions();

        // Reset frame-specific deltas
        mouse_delta_ = Vector2::ZERO;
        mouse_wheel_delta_ = Vector2::ZERO;
    }

    bool InputManager::is_key_pressed(int key_code) const {
        return pressed_keys_.find(key_code) != pressed_keys_.end();
    }

    bool InputManager::is_key_just_pressed(int key_code) const {
        return is_key_pressed(key_code) && 
               prev_pressed_keys_.find(key_code) == prev_pressed_keys_.end();
    }

    bool InputManager::is_key_just_released(int key_code) const {
        return !is_key_pressed(key_code) && 
               prev_pressed_keys_.find(key_code) != prev_pressed_keys_.end();
    }

    bool InputManager::is_mouse_button_pressed(int button) const {
        return pressed_mouse_buttons_.find(button) != pressed_mouse_buttons_.end();
    }

    bool InputManager::is_mouse_button_just_pressed(int button) const {
        return is_mouse_button_pressed(button) && 
               prev_pressed_mouse_buttons_.find(button) == prev_pressed_mouse_buttons_.end();
    }

    bool InputManager::is_mouse_button_just_released(int button) const {
        return !is_mouse_button_pressed(button) && 
               prev_pressed_mouse_buttons_.find(button) != prev_pressed_mouse_buttons_.end();
    }

    void InputManager::add_action(const String& name, const InputAction& action) {
        actions_[name] = action;
    }

    void InputManager::remove_action(const String& name) {
        actions_.erase(name);
        pressed_actions_.erase(name);
        prev_pressed_actions_.erase(name);
    }

    bool InputManager::has_action(const String& name) const {
        return actions_.find(name) != actions_.end();
    }

    bool InputManager::is_action_pressed(const String& action) const {
        return pressed_actions_.find(action) != pressed_actions_.end();
    }

    bool InputManager::is_action_just_pressed(const String& action) const {
        return is_action_pressed(action) && 
               prev_pressed_actions_.find(action) == prev_pressed_actions_.end();
    }

    bool InputManager::is_action_just_released(const String& action) const {
        return !is_action_pressed(action) && 
               prev_pressed_actions_.find(action) != prev_pressed_actions_.end();
    }

    real_t InputManager::get_action_strength(const String& action) const {
        auto it = actions_.find(action);
        if (it == actions_.end()) {
            return 0.0f;
        }

        return calculate_action_strength(it->second);
    }

    void InputManager::map_key_to_action(const String& action, int key_code) {
        auto it = actions_.find(action);
        if (it != actions_.end()) {
            auto& keys = it->second.keys;
            if (std::find(keys.begin(), keys.end(), key_code) == keys.end()) {
                keys.push_back(key_code);
            }
        }
    }

    void InputManager::map_mouse_button_to_action(const String& action, int button) {
        auto it = actions_.find(action);
        if (it != actions_.end()) {
            auto& buttons = it->second.mouse_buttons;
            if (std::find(buttons.begin(), buttons.end(), button) == buttons.end()) {
                buttons.push_back(button);
            }
        }
    }

    void InputManager::unmap_key_from_action(const String& action, int key_code) {
        auto it = actions_.find(action);
        if (it != actions_.end()) {
            auto& keys = it->second.keys;
            keys.erase(std::remove(keys.begin(), keys.end(), key_code), keys.end());
        }
    }

    void InputManager::unmap_mouse_button_from_action(const String& action, int button) {
        auto it = actions_.find(action);
        if (it != actions_.end()) {
            auto& buttons = it->second.mouse_buttons;
            buttons.erase(std::remove(buttons.begin(), buttons.end(), button), buttons.end());
        }
    }

    void InputManager::load_input_map(const String& path) {
        // TODO: Load input map from file
        std::cout << "[InputManager] Input map loading not yet implemented: " << path << std::endl;
    }

    void InputManager::save_input_map(const String& path) {
        // TODO: Save input map to file
        std::cout << "[InputManager] Input map saving not yet implemented: " << path << std::endl;
    }

    void InputManager::update_input_state() {
        // TODO: Get input state from platform layer
        // This would typically be called by the platform event handler
        // For now, this is a stub
    }

    void InputManager::update_actions() {
        pressed_actions_.clear();

        for (const auto& [name, action] : actions_) {
            if (evaluate_action(action)) {
                pressed_actions_.insert(name);
            }
        }
    }

    bool InputManager::evaluate_action(const InputAction& action) const {
        // Check if any mapped key is pressed
        for (int key : action.keys) {
            if (is_key_pressed(key)) {
                return true;
            }
        }

        // Check if any mapped mouse button is pressed
        for (int button : action.mouse_buttons) {
            if (is_mouse_button_pressed(button)) {
                return true;
            }
        }

        return false;
    }

    real_t InputManager::calculate_action_strength(const InputAction& action) const {
        if (evaluate_action(action)) {
            return 1.0f;  // Digital input, so either 0 or 1
        }
        return 0.0f;
    }

} // namespace lupine
