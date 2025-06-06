#pragma once

/**
 * Lupine Engine - Core Engine Header
 * 
 * Main engine class that orchestrates all subsystems and manages the game loop.
 * This is the C++ equivalent of the Python LupineGameEngine class.
 */

#include <memory>
#include <string>
#include <vector>
#include <unordered_map>
#include <functional>
#include "core_types.h"

// Forward declarations
namespace lupine {
    class Platform;
    class InputEvent;
    class Renderer;
    class AudioSystem;
    class PhysicsWorld;
    class InputManager;
    class ScriptRuntime;
    class Scene;
    class Node;
    class Camera2D;
    
    /**
     * Main engine configuration structure
     */
    struct EngineConfig {
        std::string project_path;
        std::string scene_path;
        int window_width = 1280;
        int window_height = 720;
        int game_bounds_width = 1920;
        int game_bounds_height = 1080;
        std::string scaling_mode = "stretch";  // stretch, letterbox, crop
        std::string scaling_filter = "linear"; // linear, nearest
        bool enable_python = true;
        bool enable_physics = true;
        bool enable_audio = true;
        int target_fps = 60;
        bool vsync = true;
    };

    /**
     * System manager that handles initialization and lifecycle of all engine systems
     */
    class SystemManager {
    public:
        SystemManager(const EngineConfig& config);
        ~SystemManager();

        bool initialize();
        void cleanup();
        void update(float delta_time);

        // System accessors
        Platform* get_platform() const { return platform_.get(); }
        Renderer* get_renderer() const { return renderer_.get(); }
        AudioSystem* get_audio_system() const { return audio_system_.get(); }
        PhysicsWorld* get_physics_world() const { return physics_world_.get(); }
        InputManager* get_input_manager() const { return input_manager_.get(); }
        ScriptRuntime* get_script_runtime() const { return script_runtime_.get(); }

        // Configuration
        const EngineConfig& get_config() const { return config_; }

        // Event handling
        void handle_platform_event(const InputEvent& event);

    private:
        EngineConfig config_;

        // Core systems
        std::unique_ptr<Platform> platform_;
        std::unique_ptr<Renderer> renderer_;
        std::unique_ptr<AudioSystem> audio_system_;
        std::unique_ptr<PhysicsWorld> physics_world_;
        std::unique_ptr<InputManager> input_manager_;
        std::unique_ptr<ScriptRuntime> script_runtime_;

        bool systems_initialized_ = false;

        bool initialize_platform();
        bool initialize_renderer();
        bool initialize_audio();
        bool initialize_physics();
        bool initialize_input();
        bool initialize_scripting();
    };

    /**
     * Main Lupine Engine class
     * 
     * This is the core engine that manages the game loop, systems, and scene.
     * Equivalent to the Python LupineGameEngine class.
     */
    class LupineEngine {
    public:
        explicit LupineEngine(const EngineConfig& config);
        ~LupineEngine();

        // Engine lifecycle
        bool initialize();
        void run();
        void shutdown();

        // Scene management
        bool load_scene(const std::string& scene_path);
        void reload_scene();
        bool change_scene(const std::string& scene_path);
        Scene* get_current_scene() const { return current_scene_.get(); }

        // Node management
        Node* get_node(const std::string& path) const;
        Node* find_node_by_name(const std::string& name) const;

        // System access
        SystemManager* get_systems() const { return systems_.get(); }
        
        // Engine state
        bool is_running() const { return running_; }
        void set_running(bool running) { running_ = running; }
        float get_delta_time() const { return delta_time_; }
        float get_fps() const { return fps_; }
        double get_runtime_time() const { return runtime_time_; }

        // Input state (for Python bindings)
        bool is_key_pressed(int key) const;
        bool is_mouse_button_pressed(int button) const;
        std::pair<float, float> get_mouse_position() const;
        std::pair<float, float> get_global_mouse_position() const;

        // Action system
        bool is_action_pressed(const std::string& action) const;
        bool is_action_just_pressed(const std::string& action) const;
        bool is_action_just_released(const std::string& action) const;
        float get_action_strength(const std::string& action) const;

        // Camera management
        Camera2D* get_current_camera() const { return current_camera_; }
        void set_current_camera(Camera2D* camera) { current_camera_ = camera; }

        // Global engine instance (for Python bindings)
        static LupineEngine* get_instance() { return instance_; }

    private:
        static LupineEngine* instance_;
        
        EngineConfig config_;
        std::unique_ptr<SystemManager> systems_;
        std::unique_ptr<Scene> current_scene_;
        Camera2D* current_camera_ = nullptr;
        
        // Engine state
        bool running_ = false;
        bool initialized_ = false;
        float delta_time_ = 0.0f;
        float fps_ = 0.0f;
        double runtime_time_ = 0.0;
        
        // Timing
        uint64_t last_frame_time_ = 0;
        uint64_t frame_count_ = 0;
        float fps_accumulator_ = 0.0f;
        
        // Core engine methods
        void main_loop();
        void handle_events();
        void update(float delta_time);
        void render();
        void calculate_fps();
        
        // Scene setup
        void setup_scene();
        void setup_node_recursive(Node* node);
        void update_node_scripts_recursive(Node* node, float delta_time);
        
        // Camera management
        void find_cameras_recursive(Node* node);
        void setup_viewport_and_projection();
    };

    /**
     * Engine initialization helper
     */
    class EngineBuilder {
    public:
        EngineBuilder& set_project_path(const std::string& path) {
            config_.project_path = path;
            return *this;
        }
        
        EngineBuilder& set_scene_path(const std::string& path) {
            config_.scene_path = path;
            return *this;
        }
        
        EngineBuilder& set_window_size(int width, int height) {
            config_.window_width = width;
            config_.window_height = height;
            return *this;
        }
        
        EngineBuilder& set_game_bounds(int width, int height) {
            config_.game_bounds_width = width;
            config_.game_bounds_height = height;
            return *this;
        }
        
        EngineBuilder& set_scaling_mode(const std::string& mode) {
            config_.scaling_mode = mode;
            return *this;
        }
        
        EngineBuilder& set_scaling_filter(const std::string& filter) {
            config_.scaling_filter = filter;
            return *this;
        }
        
        EngineBuilder& enable_python(bool enable = true) {
            config_.enable_python = enable;
            return *this;
        }
        
        EngineBuilder& enable_physics(bool enable = true) {
            config_.enable_physics = enable;
            return *this;
        }
        
        EngineBuilder& enable_audio(bool enable = true) {
            config_.enable_audio = enable;
            return *this;
        }
        
        EngineBuilder& set_target_fps(int fps) {
            config_.target_fps = fps;
            return *this;
        }
        
        EngineBuilder& enable_vsync(bool enable = true) {
            config_.vsync = enable;
            return *this;
        }
        
        std::unique_ptr<LupineEngine> build() {
            return std::make_unique<LupineEngine>(config_);
        }
        
    private:
        EngineConfig config_;
    };

} // namespace lupine
