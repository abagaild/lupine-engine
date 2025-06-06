#pragma once

/**
 * Lupine Engine - Python Script Runtime
 * 
 * Embedded Python interpreter for user scripting.
 * This is the C++ equivalent of the Python PythonScriptRuntime class.
 */

#include "../core_types.h"
#include <memory>
#include <unordered_map>
#include <functional>

#ifdef PYTHON_ENABLED
#include <Python.h>
#endif

namespace lupine {

    // Forward declarations
    class Node;
    class LupineEngine;

    /**
     * Export variable information for Python scripts
     */
    struct ExportVariable {
        String name;
        String type;
        Variant default_value;
        String hint;
        String hint_string;
        bool exported = true;
    };

    /**
     * Export group information for organizing variables in the editor
     */
    struct ExportGroup {
        String name;
        String prefix;
    };

    /**
     * Python script instance attached to a node
     */
    class ScriptInstance {
    public:
        ScriptInstance(Node* node, const String& script_path);
        ~ScriptInstance();

        // Script execution
        bool load_and_execute(const String& script_content);
        bool reload();

        // Method calling
        bool has_method(const String& method_name) const;
        Variant call_method(const String& method_name, const std::vector<Variant>& args = {});

        // Property access
        bool has_property(const String& property_name) const;
        Variant get_property(const String& property_name) const;
        void set_property(const String& property_name, const Variant& value);

        // Export variables
        const std::unordered_map<String, ExportVariable>& get_export_variables() const { return export_variables_; }
        const std::vector<ExportGroup>& get_export_groups() const { return export_groups_; }

        // Script info
        const String& get_script_path() const { return script_path_; }
        Node* get_node() const { return node_; }
        bool is_valid() const { return valid_; }
        bool is_ready_called() const { return ready_called_; }
        void set_ready_called(bool called) { ready_called_ = called; }

        // Lifecycle
        void call_ready();
        void call_process(real_t delta);
        void call_physics_process(real_t delta);
        void call_input(const class InputEvent& event);

    private:
        Node* node_;
        String script_path_;
        bool valid_ = false;
        bool ready_called_ = false;
        
        std::unordered_map<String, ExportVariable> export_variables_;
        std::vector<ExportGroup> export_groups_;
        
#ifdef PYTHON_ENABLED
        PyObject* module_ = nullptr;
        PyObject* namespace_ = nullptr;
        std::unordered_map<String, PyObject*> cached_methods_;
#endif

        bool parse_export_variables(const String& script_content);
        void setup_namespace();
        void cleanup_python_objects();
    };

    /**
     * Python script runtime system
     */
    class ScriptRuntime {
    public:
        explicit ScriptRuntime(LupineEngine* engine);
        ~ScriptRuntime();

        // Runtime management
        bool initialize();
        void cleanup();
        void update_time(real_t delta_time);

        // Script execution
        std::unique_ptr<ScriptInstance> create_script_instance(Node* node, const String& script_path);
        bool execute_script(const String& script_content, ScriptInstance* instance);

        // Built-in functions
        void add_builtin_function(const String& name, std::function<Variant(const std::vector<Variant>&)> func);
        void remove_builtin_function(const String& name);

        // Global variables
        void set_global_variable(const String& name, const Variant& value);
        Variant get_global_variable(const String& name) const;

        // Time access
        real_t get_delta_time() const { return delta_time_; }
        real_t get_runtime_time() const { return runtime_time_; }

        // Engine access
        LupineEngine* get_engine() const { return engine_; }

        // State
        bool is_initialized() const { return initialized_; }

    private:
        LupineEngine* engine_;
        bool initialized_ = false;
        real_t delta_time_ = 0.0f;
        real_t runtime_time_ = 0.0f;
        
        std::unordered_map<String, std::function<Variant(const std::vector<Variant>&)>> builtin_functions_;
        std::unordered_map<String, Variant> global_variables_;

#ifdef PYTHON_ENABLED
        PyObject* main_module_ = nullptr;
        PyObject* global_namespace_ = nullptr;
        PyObject* builtins_module_ = nullptr;
#endif

        bool setup_python_interpreter();
        void setup_builtin_functions();
        void setup_engine_bindings();
        void cleanup_python();
        
        String process_script_content(const String& content);
        std::pair<std::unordered_map<String, ExportVariable>, std::vector<ExportGroup>> 
            parse_export_variables(const String& script_content);

#ifdef PYTHON_ENABLED
        // Python C API helpers
        static PyObject* python_builtin_wrapper(PyObject* self, PyObject* args);
        static Variant python_object_to_variant(PyObject* obj);
        static PyObject* variant_to_python_object(const Variant& variant);
#endif
    };

    /**
     * Input event for script callbacks
     */
    class InputEvent {
    public:
        enum Type {
            KEY,
            MOUSE_BUTTON,
            MOUSE_MOTION,
            JOYSTICK_BUTTON,
            JOYSTICK_MOTION
        };

        Type get_type() const { return type_; }
        bool is_pressed() const { return pressed_; }
        bool is_echo() const { return echo_; }

        // Key events
        int get_keycode() const { return keycode_; }
        int get_modifiers() const { return modifiers_; }

        // Mouse events
        int get_button_index() const { return button_index_; }
        Vector2 get_position() const { return position_; }
        Vector2 get_relative() const { return relative_; }

        // Factory methods
        static InputEvent create_key_event(int keycode, bool pressed, int modifiers = 0, bool echo = false);
        static InputEvent create_mouse_button_event(int button, bool pressed, const Vector2& position);
        static InputEvent create_mouse_motion_event(const Vector2& position, const Vector2& relative);

    private:
        Type type_;
        bool pressed_ = false;
        bool echo_ = false;
        
        // Key data
        int keycode_ = 0;
        int modifiers_ = 0;
        
        // Mouse data
        int button_index_ = 0;
        Vector2 position_;
        Vector2 relative_;
    };

    /**
     * Script utilities
     */
    namespace ScriptUtils {
        // Export variable parsing
        String extract_export_type(const String& line);
        Variant parse_default_value(const String& type, const String& value_str);
        String extract_hint_string(const String& line);
        
        // Script processing
        String remove_export_decorators(const String& script_content);
        String convert_lupine_syntax(const String& script_content);
        
        // Path utilities
        String resolve_script_path(const String& project_path, const String& script_path);
        bool is_valid_script_file(const String& path);
    }

} // namespace lupine
