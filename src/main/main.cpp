/**
 * Lupine Engine - Main Entry Point
 * 
 * C++ main function that initializes and runs the Lupine Engine.
 * This replaces the Python main.py entry point.
 */

#include <iostream>
#include <string>
#include <memory>
#include <filesystem>

#include "../core/lupine_engine.h"
#include "../core/core_types.h"

#ifdef TOOLS_ENABLED
#include "../editor/editor_main.h"
#endif

using namespace lupine;

namespace {
    void print_usage(const char* program_name) {
        std::cout << "Lupine Engine - C++ Game Engine\n";
        std::cout << "Usage: " << program_name << " [options] [project_path] [scene_path]\n\n";
        std::cout << "Options:\n";
        std::cout << "  --help, -h          Show this help message\n";
        std::cout << "  --version, -v       Show version information\n";
        std::cout << "  --windowed          Run in windowed mode\n";
        std::cout << "  --fullscreen        Run in fullscreen mode\n";
        std::cout << "  --width <width>     Set window width\n";
        std::cout << "  --height <height>   Set window height\n";
        std::cout << "  --fps <fps>         Set target FPS\n";
        std::cout << "  --no-vsync          Disable VSync\n";
        std::cout << "  --no-python         Disable Python scripting\n";
        std::cout << "  --no-audio          Disable audio system\n";
        std::cout << "  --no-physics        Disable physics system\n";
#ifdef TOOLS_ENABLED
        std::cout << "  --editor            Launch editor mode\n";
        std::cout << "  --project-manager   Launch project manager\n";
#endif
        std::cout << "\nExamples:\n";
        std::cout << "  " << program_name << " /path/to/project scenes/main.scene\n";
        std::cout << "  " << program_name << " --editor /path/to/project\n";
        std::cout << "  " << program_name << " --windowed --width 1024 --height 768 .\n";
    }

    void print_version() {
        std::cout << "Lupine Engine v1.0.0\n";
        std::cout << "Built with C++17\n";
#ifdef PYTHON_ENABLED
        std::cout << "Python scripting: Enabled\n";
#else
        std::cout << "Python scripting: Disabled\n";
#endif
#ifdef OPENGL_ENABLED
        std::cout << "OpenGL rendering: Enabled\n";
#endif
#ifdef OPENAL_ENABLED
        std::cout << "OpenAL audio: Enabled\n";
#endif
#ifdef BOX2D_ENABLED
        std::cout << "Box2D physics: Enabled\n";
#endif
    }

    struct CommandLineArgs {
        std::string project_path = ".";
        std::string scene_path = "";
        bool show_help = false;
        bool show_version = false;
        bool editor_mode = false;
        bool project_manager = false;
        bool windowed = false;
        bool fullscreen = false;
        int window_width = 1280;
        int window_height = 720;
        int target_fps = 60;
        bool vsync = true;
        bool enable_python = true;
        bool enable_audio = true;
        bool enable_physics = true;
    };

    CommandLineArgs parse_arguments(int argc, char* argv[]) {
        CommandLineArgs args;
        
        for (int i = 1; i < argc; ++i) {
            std::string arg = argv[i];
            
            if (arg == "--help" || arg == "-h") {
                args.show_help = true;
            } else if (arg == "--version" || arg == "-v") {
                args.show_version = true;
            } else if (arg == "--windowed") {
                args.windowed = true;
            } else if (arg == "--fullscreen") {
                args.fullscreen = true;
            } else if (arg == "--width" && i + 1 < argc) {
                args.window_width = std::stoi(argv[++i]);
            } else if (arg == "--height" && i + 1 < argc) {
                args.window_height = std::stoi(argv[++i]);
            } else if (arg == "--fps" && i + 1 < argc) {
                args.target_fps = std::stoi(argv[++i]);
            } else if (arg == "--no-vsync") {
                args.vsync = false;
            } else if (arg == "--no-python") {
                args.enable_python = false;
            } else if (arg == "--no-audio") {
                args.enable_audio = false;
            } else if (arg == "--no-physics") {
                args.enable_physics = false;
#ifdef TOOLS_ENABLED
            } else if (arg == "--editor") {
                args.editor_mode = true;
            } else if (arg == "--project-manager") {
                args.project_manager = true;
#endif
            } else if (!arg.empty() && arg[0] != '-') {
                // Positional arguments
                if (args.project_path == ".") {
                    args.project_path = arg;
                } else if (args.scene_path.empty()) {
                    args.scene_path = arg;
                }
            }
        }
        
        return args;
    }

    bool validate_project_path(const std::string& path) {
        std::filesystem::path project_path(path);
        std::filesystem::path project_file = project_path / "project.lupine";
        
        if (!std::filesystem::exists(project_file)) {
            std::cerr << "Error: No project.lupine file found in " << path << std::endl;
            std::cerr << "Please specify a valid Lupine Engine project directory." << std::endl;
            return false;
        }
        
        return true;
    }
}

int main(int argc, char* argv[]) {
    try {
        // Parse command line arguments
        CommandLineArgs args = parse_arguments(argc, argv);
        
        if (args.show_help) {
            print_usage(argv[0]);
            return 0;
        }
        
        if (args.show_version) {
            print_version();
            return 0;
        }

#ifdef TOOLS_ENABLED
        // Launch project manager if requested
        if (args.project_manager) {
            return lupine::editor::run_project_manager();
        }
        
        // Launch editor if requested
        if (args.editor_mode) {
            if (!validate_project_path(args.project_path)) {
                return 1;
            }
            return lupine::editor::run_editor(args.project_path);
        }
#endif

        // Validate project path for game mode
        if (!validate_project_path(args.project_path)) {
            return 1;
        }

        // If no scene specified, try to find main scene from project settings
        std::string scene_path = args.scene_path;
        if (scene_path.empty()) {
            // TODO: Load project.lupine and get main scene
            scene_path = "scenes/main.scene";  // Default fallback
        }

        // Create engine configuration
        EngineConfig config;
        config.project_path = args.project_path;
        config.scene_path = scene_path;
        config.window_width = args.window_width;
        config.window_height = args.window_height;
        config.target_fps = args.target_fps;
        config.vsync = args.vsync;
        config.enable_python = args.enable_python;
        config.enable_audio = args.enable_audio;
        config.enable_physics = args.enable_physics;

        // Create and initialize engine
        std::cout << "Starting Lupine Engine..." << std::endl;
        std::cout << "Project: " << config.project_path << std::endl;
        std::cout << "Scene: " << config.scene_path << std::endl;
        std::cout << "Resolution: " << config.window_width << "x" << config.window_height << std::endl;
        
        auto engine = std::make_unique<LupineEngine>(config);
        
        if (!engine->initialize()) {
            std::cerr << "Failed to initialize Lupine Engine" << std::endl;
            return 1;
        }
        
        // Run the game
        engine->run();
        
        // Cleanup
        engine->shutdown();
        
        std::cout << "Lupine Engine shutdown complete." << std::endl;
        return 0;
        
    } catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "Unknown fatal error occurred" << std::endl;
        return 1;
    }
}
