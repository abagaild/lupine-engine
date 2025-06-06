#pragma once

/**
 * Lupine Engine - Node System
 * 
 * Base node class and scene graph system.
 * This is the C++ equivalent of the Python Node classes.
 */

#include "../core_types.h"
#include <memory>
#include <vector>
#include <unordered_map>
#include <functional>

namespace lupine {

    // Forward declarations
    class ScriptInstance;
    class LupineEngine;

    /**
     * Base Node class - fundamental building block of the scene tree
     */
    class Node {
    public:
        Node(const String& name = "Node");
        virtual ~Node();

        // Node hierarchy
        void add_child(std::shared_ptr<Node> child);
        void remove_child(std::shared_ptr<Node> child);
        void remove_child(const String& name);
        std::shared_ptr<Node> get_child(const String& name) const;
        std::shared_ptr<Node> get_child(int index) const;
        int get_child_count() const { return static_cast<int>(children_.size()); }
        const std::vector<std::shared_ptr<Node>>& get_children() const { return children_; }
        
        Node* get_parent() const { return parent_; }
        void set_parent(Node* parent) { parent_ = parent; }
        
        // Node identification
        const String& get_name() const { return name_; }
        void set_name(const String& name) { name_ = name; }
        
        const String& get_type() const { return type_; }
        
        String get_path() const;
        Node* get_node(const String& path) const;
        Node* find_node(const String& name, bool recursive = true) const;

        // Node state
        bool is_visible() const { return visible_; }
        void set_visible(bool visible) { visible_ = visible; }
        
        bool is_process_enabled() const { return process_enabled_; }
        void set_process_enabled(bool enabled) { process_enabled_ = enabled; }
        
        bool is_physics_process_enabled() const { return physics_process_enabled_; }
        void set_physics_process_enabled(bool enabled) { physics_process_enabled_ = enabled; }

        // Groups
        void add_to_group(const String& group);
        void remove_from_group(const String& group);
        bool is_in_group(const String& group) const;
        const std::vector<String>& get_groups() const { return groups_; }

        // Properties
        void set_property(const String& name, const Variant& value);
        Variant get_property(const String& name) const;
        bool has_property(const String& name) const;
        const std::unordered_map<String, Variant>& get_properties() const { return properties_; }

        // Signals
        Signal& get_signal(const String& name);
        void emit_signal(const String& name, const std::vector<Variant>& args = {});
        bool has_signal(const String& name) const;

        // Script system
        void attach_script(const String& script_path);
        void detach_script();
        bool has_script() const { return script_instance_ != nullptr; }
        ScriptInstance* get_script_instance() const { return script_instance_.get(); }

        // Lifecycle callbacks (virtual methods that can be overridden)
        virtual void _ready() {}
        virtual void _process(real_t delta) {}
        virtual void _physics_process(real_t delta) {}
        virtual void _input(const class InputEvent& event) {}
        virtual void _unhandled_input(const class InputEvent& event) {}
        virtual void _draw() {}

        // Internal engine callbacks
        void _internal_ready();
        void _internal_process(real_t delta);
        void _internal_physics_process(real_t delta);
        void _internal_input(const class InputEvent& event);

        // Tree notifications
        virtual void _enter_tree() {}
        virtual void _exit_tree() {}
        virtual void _tree_entered() {}
        virtual void _tree_exiting() {}

        // Serialization
        virtual void save_to_dict(std::unordered_map<String, Variant>& dict) const;
        virtual void load_from_dict(const std::unordered_map<String, Variant>& dict);

        // Engine access
        LupineEngine* get_engine() const;

    protected:
        String name_;
        String type_;
        Node* parent_ = nullptr;
        std::vector<std::shared_ptr<Node>> children_;
        
        bool visible_ = true;
        bool process_enabled_ = true;
        bool physics_process_enabled_ = true;
        bool ready_called_ = false;
        bool in_tree_ = false;
        
        std::vector<String> groups_;
        std::unordered_map<String, Variant> properties_;
        std::unordered_map<String, Signal> signals_;
        
        std::unique_ptr<ScriptInstance> script_instance_;

        // Helper methods
        void _propagate_ready();
        void _propagate_enter_tree();
        void _propagate_exit_tree();
    };

    /**
     * Node2D - Base class for 2D nodes
     */
    class Node2D : public Node {
    public:
        Node2D(const String& name = "Node2D");
        virtual ~Node2D() = default;

        // Transform
        const Vector2& get_position() const { return position_; }
        void set_position(const Vector2& position) { position_ = position; update_transform(); }
        
        real_t get_rotation() const { return rotation_; }
        void set_rotation(real_t rotation) { rotation_ = rotation; update_transform(); }
        
        const Vector2& get_scale() const { return scale_; }
        void set_scale(const Vector2& scale) { scale_ = scale; update_transform(); }
        
        int get_z_index() const { return z_index_; }
        void set_z_index(int z_index) { z_index_ = z_index; }
        
        bool is_z_relative() const { return z_relative_; }
        void set_z_relative(bool relative) { z_relative_ = relative; }

        // Global transform
        Vector2 get_global_position() const;
        void set_global_position(const Vector2& position);
        real_t get_global_rotation() const;
        Vector2 get_global_scale() const;
        
        Transform2D get_transform() const { return transform_; }
        void set_transform(const Transform2D& transform);
        Transform2D get_global_transform() const;

        // Transform utilities
        Vector2 to_local(const Vector2& global_point) const;
        Vector2 to_global(const Vector2& local_point) const;
        
        void translate(const Vector2& offset) { set_position(position_ + offset); }
        void rotate(real_t angle) { set_rotation(rotation_ + angle); }
        void scale_by(const Vector2& factor) { set_scale(Vector2(scale_.x * factor.x, scale_.y * factor.y)); }

        // Serialization
        void save_to_dict(std::unordered_map<String, Variant>& dict) const override;
        void load_from_dict(const std::unordered_map<String, Variant>& dict) override;

    protected:
        Vector2 position_ = Vector2::ZERO;
        real_t rotation_ = 0.0f;
        Vector2 scale_ = Vector2::ONE;
        int z_index_ = 0;
        bool z_relative_ = true;
        
        Transform2D transform_ = Transform2D::IDENTITY;
        mutable Transform2D global_transform_ = Transform2D::IDENTITY;
        mutable bool global_transform_dirty_ = true;
        
        void update_transform();
        void _update_global_transform() const;
    };

    /**
     * Camera2D - 2D camera node
     */
    class Camera2D : public Node2D {
    public:
        Camera2D(const String& name = "Camera2D");
        virtual ~Camera2D() = default;

        // Camera properties
        bool is_current() const { return current_; }
        void set_current(bool current);
        
        real_t get_zoom() const { return zoom_; }
        void set_zoom(real_t zoom) { zoom_ = zoom; }
        
        const Vector2& get_offset() const { return offset_; }
        void set_offset(const Vector2& offset) { offset_ = offset; }
        
        bool is_enabled() const { return enabled_; }
        void set_enabled(bool enabled) { enabled_ = enabled; }

        // Camera limits
        void set_limit(int side, int limit);
        int get_limit(int side) const;
        
        bool is_limit_smoothing_enabled() const { return limit_smoothing_enabled_; }
        void set_limit_smoothing_enabled(bool enabled) { limit_smoothing_enabled_ = enabled; }

        // Camera smoothing
        bool is_smoothing_enabled() const { return smoothing_enabled_; }
        void set_smoothing_enabled(bool enabled) { smoothing_enabled_ = enabled; }
        
        real_t get_smoothing_speed() const { return smoothing_speed_; }
        void set_smoothing_speed(real_t speed) { smoothing_speed_ = speed; }

        // Camera utilities
        Vector2 get_camera_screen_center() const;
        void force_update_scroll();
        void make_current();

        // Serialization
        void save_to_dict(std::unordered_map<String, Variant>& dict) const override;
        void load_from_dict(const std::unordered_map<String, Variant>& dict) override;

    private:
        bool current_ = false;
        real_t zoom_ = 1.0f;
        Vector2 offset_ = Vector2::ZERO;
        bool enabled_ = true;
        
        // Limits
        int limit_left_ = -10000000;
        int limit_top_ = -10000000;
        int limit_right_ = 10000000;
        int limit_bottom_ = 10000000;
        bool limit_smoothing_enabled_ = false;
        
        // Smoothing
        bool smoothing_enabled_ = false;
        real_t smoothing_speed_ = 5.0f;
    };

    /**
     * Scene - Container for the scene tree
     */
    class Scene {
    public:
        Scene(const String& name = "Scene");
        ~Scene();

        // Scene management
        const String& get_name() const { return name_; }
        void set_name(const String& name) { name_ = name; }
        
        void add_root_node(std::shared_ptr<Node> node);
        void remove_root_node(std::shared_ptr<Node> node);
        const std::vector<std::shared_ptr<Node>>& get_root_nodes() const { return root_nodes_; }
        
        Node* find_node(const String& name) const;
        Node* get_node(const String& path) const;
        
        // Scene lifecycle
        void _ready();
        void _process(real_t delta);
        void _physics_process(real_t delta);
        void _input(const class InputEvent& event);

        // Serialization
        bool save_to_file(const String& path) const;
        bool load_from_file(const String& path);
        void save_to_dict(std::unordered_map<String, Variant>& dict) const;
        void load_from_dict(const std::unordered_map<String, Variant>& dict);

    private:
        String name_;
        std::vector<std::shared_ptr<Node>> root_nodes_;
        
        void _process_node_recursive(Node* node, real_t delta);
        void _physics_process_node_recursive(Node* node, real_t delta);
        void _input_node_recursive(Node* node, const class InputEvent& event);
    };

} // namespace lupine
