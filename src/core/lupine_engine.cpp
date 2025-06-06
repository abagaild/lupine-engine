/**
 * Lupine Engine - Core Engine Implementation
 */

#include "lupine_engine.h"
#include "platform/platform.h"
#include "rendering/renderer.h"
#include "audio/audio_system.h"
#include "physics/physics_world.h"
#include "input/input_manager.h"
#include "scripting/script_runtime.h"
#include "scene/node.h"
#include "scene/scene.h"

#include <iostream>
#include <chrono>
#include <thread>

namespace lupine {

    // Static instance for global access
    LupineEngine* LupineEngine::instance_ = nullptr;

    //=============================================================================
    // SystemManager Implementation
    //=============================================================================

    SystemManager::SystemManager(const EngineConfig& config) : config_(config) {
    }

    SystemManager::~SystemManager() {
        cleanup();
    }

    bool SystemManager::initialize() {
        if (systems_initialized_) {
            return true;
        }

        std::cout << "[SystemManager] Initializing engine systems..." << std::endl;

        // Initialize platform (required first)
        if (!initialize_platform()) {
            std::cerr << "[SystemManager] Failed to initialize platform" << std::endl;
            return false;
        }

        // Initialize renderer (required)
        if (!initialize_renderer()) {
            std::cerr << "[SystemManager] Failed to initialize renderer" << std::endl;
            return false;
        }

        // Initialize audio system
        if (config_.enable_audio && !initialize_audio()) {
            std::cerr << "[SystemManager] Failed to initialize audio system" << std::endl;
            return false;
        }

        // Initialize physics system
        if (config_.enable_physics && !initialize_physics()) {
            std::cerr << "[SystemManager] Failed to initialize physics system" << std::endl;
            return false;
        }

        // Initialize input system
        if (!initialize_input()) {
            std::cerr << "[SystemManager] Failed to initialize input system" << std::endl;
            return false;
        }

        // Initialize scripting system
        if (config_.enable_python && !initialize_scripting()) {
            std::cerr << "[SystemManager] Failed to initialize scripting system" << std::endl;
            return false;
        }

        systems_initialized_ = true;
        std::cout << "[SystemManager] All systems initialized successfully" << std::endl;
        return true;
    }

    void SystemManager::cleanup() {
        if (!systems_initialized_) {
            return;
        }

        std::cout << "[SystemManager] Cleaning up engine systems..." << std::endl;

        script_runtime_.reset();
        input_manager_.reset();
        physics_world_.reset();
        audio_system_.reset();
        renderer_.reset();
        platform_.reset();

        systems_initialized_ = false;
    }

    void SystemManager::update(float delta_time) {
        if (!systems_initialized_) {
            return;
        }

        // Update audio system
        if (audio_system_) {
            audio_system_->update();
        }

        // Update input system
        if (input_manager_) {
            input_manager_->update();
        }

        // Update scripting system
        if (script_runtime_) {
            script_runtime_->update_time(delta_time);
        }

        // Update physics system
        if (physics_world_) {
            physics_world_->step(delta_time);
        }
    }

    bool SystemManager::initialize_platform() {
        // Create platform instance
        platform_ = Platform::create();
        if (!platform_) {
            std::cerr << "[SystemManager] Failed to create platform instance" << std::endl;
            return false;
        }

        // Configure platform
        WindowConfig window_config;
        window_config.title = "Lupine Engine";
        window_config.width = config_.window_width;
        window_config.height = config_.window_height;
        window_config.game_bounds_width = config_.game_bounds_width;
        window_config.game_bounds_height = config_.game_bounds_height;
        window_config.scaling_mode = config_.scaling_mode;
        window_config.scaling_filter = config_.scaling_filter;
        window_config.vsync = config_.vsync;

        // Initialize platform
        if (!platform_->initialize(window_config)) {
            std::cerr << "[SystemManager] Failed to initialize platform" << std::endl;
            return false;
        }

        // Create window
        if (!platform_->create_window()) {
            std::cerr << "[SystemManager] Failed to create window" << std::endl;
            return false;
        }

        // Create OpenGL context
        if (!platform_->create_opengl_context()) {
            std::cerr << "[SystemManager] Failed to create OpenGL context" << std::endl;
            return false;
        }

        // Set up event callback
        platform_->set_event_callback([this](const InputEvent& event) {
            handle_platform_event(event);
        });

        // Show window
        platform_->show_window();

        std::cout << "[SystemManager] Platform initialized successfully" << std::endl;
        return true;
    }

    void SystemManager::handle_platform_event(const InputEvent& event) {
        // Handle window close event
        if (event.type == InputEventType::WINDOW_CLOSE) {
            // Signal the engine to stop running
            if (LupineEngine::get_instance()) {
                LupineEngine::get_instance()->set_running(false);
            }
            return;
        }

        // Forward input events to input manager
        if (input_manager_) {
            // TODO: Forward event to input manager when implemented
        }

        // Handle window resize
        if (event.type == InputEventType::WINDOW_RESIZE) {
            // TODO: Update renderer viewport when implemented
            std::cout << "[SystemManager] Window resized to " << event.window_size.x << "x" << event.window_size.y << std::endl;
        }
    }

    bool SystemManager::initialize_renderer() {
        RendererConfig renderer_config;
        renderer_config.window_width = config_.window_width;
        renderer_config.window_height = config_.window_height;
        renderer_config.game_bounds_width = config_.game_bounds_width;
        renderer_config.game_bounds_height = config_.game_bounds_height;
        renderer_config.scaling_mode = config_.scaling_mode;
        renderer_config.scaling_filter = config_.scaling_filter;
        renderer_config.vsync = config_.vsync;

        renderer_ = std::make_unique<Renderer>(renderer_config);
        return renderer_->initialize();
    }

    bool SystemManager::initialize_audio() {
        // TODO: Implement audio system initialization
        std::cout << "[SystemManager] Audio system initialization not yet implemented" << std::endl;
        return true;
    }

    bool SystemManager::initialize_physics() {
        // TODO: Implement physics system initialization
        std::cout << "[SystemManager] Physics system initialization not yet implemented" << std::endl;
        return true;
    }

    bool SystemManager::initialize_input() {
        // TODO: Implement input system initialization
        std::cout << "[SystemManager] Input system initialization not yet implemented" << std::endl;
        return true;
    }

    bool SystemManager::initialize_scripting() {
        // TODO: Implement scripting system initialization
        std::cout << "[SystemManager] Scripting system initialization not yet implemented" << std::endl;
        return true;
    }

    //=============================================================================
    // LupineEngine Implementation
    //=============================================================================

    LupineEngine::LupineEngine(const EngineConfig& config) : config_(config) {
        instance_ = this;
        systems_ = std::make_unique<SystemManager>(config);
    }

    LupineEngine::~LupineEngine() {
        shutdown();
        instance_ = nullptr;
    }

    bool LupineEngine::initialize() {
        if (initialized_) {
            return true;
        }

        std::cout << "[LupineEngine] Initializing engine..." << std::endl;

        // Initialize systems (includes platform initialization)
        if (!systems_->initialize()) {
            std::cerr << "[LupineEngine] Failed to initialize systems" << std::endl;
            return false;
        }

        // Load scene
        if (!config_.scene_path.empty()) {
            if (!load_scene(config_.scene_path)) {
                std::cerr << "[LupineEngine] Failed to load scene: " << config_.scene_path << std::endl;
                return false;
            }
        }

        initialized_ = true;
        std::cout << "[LupineEngine] Engine initialized successfully" << std::endl;
        return true;
    }

    void LupineEngine::run() {
        if (!initialized_) {
            std::cerr << "[LupineEngine] Engine not initialized" << std::endl;
            return;
        }

        std::cout << "[LupineEngine] Starting main loop..." << std::endl;
        running_ = true;
        main_loop();
    }

    void LupineEngine::shutdown() {
        if (!initialized_) {
            return;
        }

        std::cout << "[LupineEngine] Shutting down engine..." << std::endl;
        running_ = false;

        // Cleanup systems (includes platform cleanup)
        systems_->cleanup();

        initialized_ = false;
    }

    bool LupineEngine::load_scene(const std::string& scene_path) {
        std::cout << "[LupineEngine] Loading scene: " << scene_path << std::endl;
        
        // TODO: Implement scene loading
        current_scene_ = std::make_unique<Scene>("MainScene");
        
        // Create a simple test node for now
        auto root_node = std::make_shared<Node2D>("Root");
        current_scene_->add_root_node(root_node);
        
        setup_scene();
        
        std::cout << "[LupineEngine] Scene loaded successfully" << std::endl;
        return true;
    }

    void LupineEngine::reload_scene() {
        if (!config_.scene_path.empty()) {
            load_scene(config_.scene_path);
        }
    }

    bool LupineEngine::change_scene(const std::string& scene_path) {
        config_.scene_path = scene_path;
        return load_scene(scene_path);
    }

    Node* LupineEngine::get_node(const std::string& path) const {
        if (!current_scene_) {
            return nullptr;
        }
        return current_scene_->get_node(path);
    }

    Node* LupineEngine::find_node_by_name(const std::string& name) const {
        if (!current_scene_) {
            return nullptr;
        }
        return current_scene_->find_node(name);
    }



    void LupineEngine::main_loop() {
        auto last_time = std::chrono::high_resolution_clock::now();
        
        while (running_) {
            auto current_time = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration_cast<std::chrono::microseconds>(current_time - last_time);
            delta_time_ = duration.count() / 1000000.0f;
            last_time = current_time;
            
            runtime_time_ += delta_time_;
            
            // Handle events
            handle_events();
            
            // Update
            update(delta_time_);
            
            // Render
            render();
            
            // Calculate FPS
            calculate_fps();
            
            // Cap framerate
            if (config_.target_fps > 0) {
                float target_frame_time = 1.0f / config_.target_fps;
                if (delta_time_ < target_frame_time) {
                    float sleep_time = target_frame_time - delta_time_;
                    std::this_thread::sleep_for(std::chrono::duration<float>(sleep_time));
                }
            }
        }
    }

    void LupineEngine::handle_events() {
        auto* platform = systems_->get_platform();
        if (platform) {
            platform->poll_events();
        }
    }

    void LupineEngine::update(float delta_time) {
        // Update systems
        systems_->update(delta_time);
        
        // Update scene
        if (current_scene_) {
            current_scene_->_process(delta_time);
            current_scene_->_physics_process(delta_time);
        }
    }

    void LupineEngine::render() {
        if (!systems_->get_renderer()) {
            return;
        }
        
        auto* renderer = systems_->get_renderer();
        
        // Begin frame
        renderer->begin_frame();
        renderer->clear();
        
        // Setup camera and projection
        setup_viewport_and_projection();
        
        // TODO: Render scene
        
        // End frame
        renderer->end_frame();
        renderer->present();

        // Swap buffers
        auto* platform = systems_->get_platform();
        if (platform) {
            platform->swap_buffers();
        }
    }

    void LupineEngine::calculate_fps() {
        frame_count_++;
        fps_accumulator_ += delta_time_;
        
        if (fps_accumulator_ >= 1.0f) {
            fps_ = frame_count_ / fps_accumulator_;
            frame_count_ = 0;
            fps_accumulator_ = 0.0f;
        }
    }

    void LupineEngine::setup_scene() {
        if (!current_scene_) {
            return;
        }
        
        // Setup all nodes in the scene
        for (const auto& root_node : current_scene_->get_root_nodes()) {
            setup_node_recursive(root_node.get());
        }
        
        // Find cameras
        for (const auto& root_node : current_scene_->get_root_nodes()) {
            find_cameras_recursive(root_node.get());
        }
        
        // Call ready on all nodes
        current_scene_->_ready();
    }

    void LupineEngine::setup_node_recursive(Node* node) {
        if (!node) {
            return;
        }
        
        // TODO: Setup node-specific functionality
        
        // Setup children
        for (const auto& child : node->get_children()) {
            setup_node_recursive(child.get());
        }
    }

    void LupineEngine::find_cameras_recursive(Node* node) {
        if (!node) {
            return;
        }
        
        // Check if this node is a Camera2D
        if (auto* camera = dynamic_cast<Camera2D*>(node)) {
            if (camera->is_current()) {
                current_camera_ = camera;
            }
        }
        
        // Check children
        for (const auto& child : node->get_children()) {
            find_cameras_recursive(child.get());
        }
    }

    void LupineEngine::setup_viewport_and_projection() {
        if (!systems_->get_renderer()) {
            return;
        }
        
        auto* renderer = systems_->get_renderer();
        renderer->setup_2d_projection();
        
        if (current_camera_) {
            renderer->setup_camera(current_camera_);
        }
    }

    // Input methods using platform abstraction
    bool LupineEngine::is_key_pressed(int key) const {
        auto* platform = systems_->get_platform();
        return platform ? platform->is_key_pressed(key) : false;
    }

    bool LupineEngine::is_mouse_button_pressed(int button) const {
        auto* platform = systems_->get_platform();
        return platform ? platform->is_mouse_button_pressed(button) : false;
    }

    std::pair<float, float> LupineEngine::get_mouse_position() const {
        auto* platform = systems_->get_platform();
        if (platform) {
            Vector2 pos = platform->get_mouse_position();
            return {pos.x, pos.y};
        }
        return {0.0f, 0.0f};
    }

    std::pair<float, float> LupineEngine::get_global_mouse_position() const {
        // For now, same as local mouse position
        return get_mouse_position();
    }

    bool LupineEngine::is_action_pressed(const std::string& action) const {
        // TODO: Implement
        return false;
    }

    bool LupineEngine::is_action_just_pressed(const std::string& action) const {
        // TODO: Implement
        return false;
    }

    bool LupineEngine::is_action_just_released(const std::string& action) const {
        // TODO: Implement
        return false;
    }

    float LupineEngine::get_action_strength(const std::string& action) const {
        // TODO: Implement
        return 0.0f;
    }

} // namespace lupine
