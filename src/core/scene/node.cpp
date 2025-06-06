/**
 * Lupine Engine - Node System Implementation
 */

#include "node.h"
#include "../lupine_engine.h"
#include <algorithm>
#include <iostream>

namespace lupine {

    //=============================================================================
    // Node Implementation
    //=============================================================================

    Node::Node(const String& name) : name_(name), type_("Node") {
    }

    Node::~Node() {
        // Cleanup children
        for (auto& child : children_) {
            if (child) {
                child->set_parent(nullptr);
            }
        }
        children_.clear();
    }

    void Node::add_child(std::shared_ptr<Node> child) {
        if (!child) {
            return;
        }

        // Remove from previous parent
        if (child->parent_) {
            child->parent_->remove_child(child);
        }

        // Add to this node
        children_.push_back(child);
        child->set_parent(this);

        // Notify tree events
        if (in_tree_) {
            child->_propagate_enter_tree();
        }
    }

    void Node::remove_child(std::shared_ptr<Node> child) {
        if (!child) {
            return;
        }

        auto it = std::find(children_.begin(), children_.end(), child);
        if (it != children_.end()) {
            // Notify tree events
            if (child->in_tree_) {
                child->_propagate_exit_tree();
            }

            child->set_parent(nullptr);
            children_.erase(it);
        }
    }

    void Node::remove_child(const String& name) {
        auto child = get_child(name);
        if (child) {
            remove_child(child);
        }
    }

    std::shared_ptr<Node> Node::get_child(const String& name) const {
        for (const auto& child : children_) {
            if (child && child->get_name() == name) {
                return child;
            }
        }
        return nullptr;
    }

    std::shared_ptr<Node> Node::get_child(int index) const {
        if (index >= 0 && index < static_cast<int>(children_.size())) {
            return children_[index];
        }
        return nullptr;
    }

    String Node::get_path() const {
        if (!parent_) {
            return "/" + name_;
        }
        return parent_->get_path() + "/" + name_;
    }

    Node* Node::get_node(const String& path) const {
        if (path.empty()) {
            return const_cast<Node*>(this);
        }

        if (path[0] == '/') {
            // Absolute path - find root and search from there
            Node* root = const_cast<Node*>(this);
            while (root->parent_) {
                root = root->parent_;
            }
            return root->get_node(path.substr(1));
        }

        // Relative path
        size_t slash_pos = path.find('/');
        if (slash_pos == String::npos) {
            // Single node name
            auto child = get_child(path);
            return child.get();
        } else {
            // Multiple levels
            String first_part = path.substr(0, slash_pos);
            String remaining = path.substr(slash_pos + 1);
            auto child = get_child(first_part);
            if (child) {
                return child->get_node(remaining);
            }
        }

        return nullptr;
    }

    Node* Node::find_node(const String& name, bool recursive) const {
        // Check direct children first
        for (const auto& child : children_) {
            if (child && child->get_name() == name) {
                return child.get();
            }
        }

        // Recursive search
        if (recursive) {
            for (const auto& child : children_) {
                if (child) {
                    Node* found = child->find_node(name, true);
                    if (found) {
                        return found;
                    }
                }
            }
        }

        return nullptr;
    }

    void Node::add_to_group(const String& group) {
        auto it = std::find(groups_.begin(), groups_.end(), group);
        if (it == groups_.end()) {
            groups_.push_back(group);
        }
    }

    void Node::remove_from_group(const String& group) {
        auto it = std::find(groups_.begin(), groups_.end(), group);
        if (it != groups_.end()) {
            groups_.erase(it);
        }
    }

    bool Node::is_in_group(const String& group) const {
        return std::find(groups_.begin(), groups_.end(), group) != groups_.end();
    }

    void Node::set_property(const String& name, const Variant& value) {
        properties_[name] = value;
    }

    Variant Node::get_property(const String& name) const {
        auto it = properties_.find(name);
        if (it != properties_.end()) {
            return it->second;
        }
        return Variant();
    }

    bool Node::has_property(const String& name) const {
        return properties_.find(name) != properties_.end();
    }

    Signal& Node::get_signal(const String& name) {
        return signals_[name];
    }

    void Node::emit_signal(const String& name, const std::vector<Variant>& args) {
        auto it = signals_.find(name);
        if (it != signals_.end()) {
            it->second.emit(args);
        }
    }

    bool Node::has_signal(const String& name) const {
        return signals_.find(name) != signals_.end();
    }

    void Node::attach_script(const String& script_path) {
        // TODO: Implement script attachment
        std::cout << "[Node] Script attachment not yet implemented: " << script_path << std::endl;
    }

    void Node::detach_script() {
        script_instance_.reset();
    }

    void Node::_internal_ready() {
        if (ready_called_) {
            return;
        }

        _ready();
        ready_called_ = true;

        // Call ready on children
        for (const auto& child : children_) {
            if (child) {
                child->_internal_ready();
            }
        }
    }

    void Node::_internal_process(real_t delta) {
        if (!process_enabled_ || !visible_) {
            return;
        }

        _process(delta);

        // Process children
        for (const auto& child : children_) {
            if (child) {
                child->_internal_process(delta);
            }
        }
    }

    void Node::_internal_physics_process(real_t delta) {
        if (!physics_process_enabled_ || !visible_) {
            return;
        }

        _physics_process(delta);

        // Process children
        for (const auto& child : children_) {
            if (child) {
                child->_internal_physics_process(delta);
            }
        }
    }

    void Node::_internal_input(const InputEvent& event) {
        _input(event);

        // Process children
        for (const auto& child : children_) {
            if (child) {
                child->_internal_input(event);
            }
        }
    }

    void Node::save_to_dict(std::unordered_map<String, Variant>& dict) const {
        dict["name"] = Variant(name_);
        dict["type"] = Variant(type_);
        dict["visible"] = Variant(visible_);
        dict["process_enabled"] = Variant(process_enabled_);
        dict["physics_process_enabled"] = Variant(physics_process_enabled_);

        // TODO: Save properties, groups, etc.
    }

    void Node::load_from_dict(const std::unordered_map<String, Variant>& dict) {
        auto it = dict.find("name");
        if (it != dict.end()) {
            name_ = it->second.as_string();
        }

        it = dict.find("visible");
        if (it != dict.end()) {
            visible_ = it->second.as_bool();
        }

        it = dict.find("process_enabled");
        if (it != dict.end()) {
            process_enabled_ = it->second.as_bool();
        }

        it = dict.find("physics_process_enabled");
        if (it != dict.end()) {
            physics_process_enabled_ = it->second.as_bool();
        }

        // TODO: Load properties, groups, etc.
    }

    LupineEngine* Node::get_engine() const {
        return LupineEngine::get_instance();
    }

    void Node::_propagate_ready() {
        if (!ready_called_) {
            _internal_ready();
        }
    }

    void Node::_propagate_enter_tree() {
        in_tree_ = true;
        _enter_tree();
        _tree_entered();

        for (const auto& child : children_) {
            if (child) {
                child->_propagate_enter_tree();
            }
        }
    }

    void Node::_propagate_exit_tree() {
        _tree_exiting();
        _exit_tree();
        in_tree_ = false;

        for (const auto& child : children_) {
            if (child) {
                child->_propagate_exit_tree();
            }
        }
    }

    //=============================================================================
    // Node2D Implementation
    //=============================================================================

    Node2D::Node2D(const String& name) : Node(name) {
        type_ = "Node2D";
        update_transform();
    }

    Vector2 Node2D::get_global_position() const {
        _update_global_transform();
        return global_transform_.origin;
    }

    void Node2D::set_global_position(const Vector2& position) {
        if (parent_) {
            Node2D* parent_2d = dynamic_cast<Node2D*>(parent_);
            if (parent_2d) {
                Transform2D parent_global = parent_2d->get_global_transform();
                set_position(parent_global.inverse().transform_point(position));
                return;
            }
        }
        set_position(position);
    }

    real_t Node2D::get_global_rotation() const {
        _update_global_transform();
        return global_transform_.get_rotation();
    }

    Vector2 Node2D::get_global_scale() const {
        _update_global_transform();
        return global_transform_.get_scale();
    }

    void Node2D::set_transform(const Transform2D& transform) {
        transform_ = transform;
        position_ = transform.origin;
        rotation_ = transform.get_rotation();
        scale_ = transform.get_scale();
        global_transform_dirty_ = true;
    }

    Transform2D Node2D::get_global_transform() const {
        _update_global_transform();
        return global_transform_;
    }

    Vector2 Node2D::to_local(const Vector2& global_point) const {
        return get_global_transform().inverse().transform_point(global_point);
    }

    Vector2 Node2D::to_global(const Vector2& local_point) const {
        return get_global_transform().transform_point(local_point);
    }

    void Node2D::save_to_dict(std::unordered_map<String, Variant>& dict) const {
        Node::save_to_dict(dict);
        dict["position"] = Variant(position_);
        dict["rotation"] = Variant(rotation_);
        dict["scale"] = Variant(scale_);
        dict["z_index"] = Variant(z_index_);
        dict["z_relative"] = Variant(z_relative_);
    }

    void Node2D::load_from_dict(const std::unordered_map<String, Variant>& dict) {
        Node::load_from_dict(dict);

        auto it = dict.find("position");
        if (it != dict.end()) {
            position_ = it->second.as_vector2();
        }

        it = dict.find("rotation");
        if (it != dict.end()) {
            rotation_ = it->second.as_float();
        }

        it = dict.find("scale");
        if (it != dict.end()) {
            scale_ = it->second.as_vector2();
        }

        it = dict.find("z_index");
        if (it != dict.end()) {
            z_index_ = it->second.as_int();
        }

        it = dict.find("z_relative");
        if (it != dict.end()) {
            z_relative_ = it->second.as_bool();
        }

        update_transform();
    }

    void Node2D::update_transform() {
        transform_ = Transform2D(rotation_, position_);
        transform_.set_scale(scale_);
        global_transform_dirty_ = true;
    }

    void Node2D::_update_global_transform() const {
        if (!global_transform_dirty_) {
            return;
        }

        if (parent_) {
            Node2D* parent_2d = dynamic_cast<Node2D*>(parent_);
            if (parent_2d) {
                global_transform_ = parent_2d->get_global_transform() * transform_;
            } else {
                global_transform_ = transform_;
            }
        } else {
            global_transform_ = transform_;
        }

        global_transform_dirty_ = false;
    }

    //=============================================================================
    // Camera2D Implementation
    //=============================================================================

    Camera2D::Camera2D(const String& name) : Node2D(name) {
        type_ = "Camera2D";
    }

    void Camera2D::set_current(bool current) {
        current_ = current;
        if (current) {
            make_current();
        }
    }

    void Camera2D::set_limit(int side, int limit) {
        switch (side) {
            case 0: limit_left_ = limit; break;
            case 1: limit_top_ = limit; break;
            case 2: limit_right_ = limit; break;
            case 3: limit_bottom_ = limit; break;
        }
    }

    int Camera2D::get_limit(int side) const {
        switch (side) {
            case 0: return limit_left_;
            case 1: return limit_top_;
            case 2: return limit_right_;
            case 3: return limit_bottom_;
            default: return 0;
        }
    }

    Vector2 Camera2D::get_camera_screen_center() const {
        return get_global_position() + offset_;
    }

    void Camera2D::force_update_scroll() {
        // TODO: Implement camera scroll update
    }

    void Camera2D::make_current() {
        current_ = true;
        auto* engine = get_engine();
        if (engine) {
            engine->set_current_camera(this);
        }
    }

    void Camera2D::save_to_dict(std::unordered_map<String, Variant>& dict) const {
        Node2D::save_to_dict(dict);
        dict["current"] = Variant(current_);
        dict["zoom"] = Variant(zoom_);
        dict["offset"] = Variant(offset_);
        dict["enabled"] = Variant(enabled_);
    }

    void Camera2D::load_from_dict(const std::unordered_map<String, Variant>& dict) {
        Node2D::load_from_dict(dict);

        auto it = dict.find("current");
        if (it != dict.end()) {
            set_current(it->second.as_bool());
        }

        it = dict.find("zoom");
        if (it != dict.end()) {
            zoom_ = it->second.as_float();
        }

        it = dict.find("offset");
        if (it != dict.end()) {
            offset_ = it->second.as_vector2();
        }

        it = dict.find("enabled");
        if (it != dict.end()) {
            enabled_ = it->second.as_bool();
        }
    }

    //=============================================================================
    // Scene Implementation
    //=============================================================================

    Scene::Scene(const String& name) : name_(name) {
    }

    Scene::~Scene() {
        root_nodes_.clear();
    }

    void Scene::add_root_node(std::shared_ptr<Node> node) {
        if (!node) {
            return;
        }

        root_nodes_.push_back(node);
        node->_propagate_enter_tree();
    }

    void Scene::remove_root_node(std::shared_ptr<Node> node) {
        if (!node) {
            return;
        }

        auto it = std::find(root_nodes_.begin(), root_nodes_.end(), node);
        if (it != root_nodes_.end()) {
            node->_propagate_exit_tree();
            root_nodes_.erase(it);
        }
    }

    Node* Scene::find_node(const String& name) const {
        for (const auto& root_node : root_nodes_) {
            if (root_node && root_node->get_name() == name) {
                return root_node.get();
            }
            Node* found = root_node->find_node(name, true);
            if (found) {
                return found;
            }
        }
        return nullptr;
    }

    Node* Scene::get_node(const String& path) const {
        if (path.empty() || path[0] != '/') {
            return nullptr;
        }

        String remaining = path.substr(1);
        if (remaining.empty()) {
            return nullptr;
        }

        size_t slash_pos = remaining.find('/');
        String root_name = (slash_pos == String::npos) ? remaining : remaining.substr(0, slash_pos);

        for (const auto& root_node : root_nodes_) {
            if (root_node && root_node->get_name() == root_name) {
                if (slash_pos == String::npos) {
                    return root_node.get();
                } else {
                    return root_node->get_node(remaining.substr(slash_pos + 1));
                }
            }
        }

        return nullptr;
    }

    void Scene::_ready() {
        for (const auto& root_node : root_nodes_) {
            if (root_node) {
                root_node->_propagate_ready();
            }
        }
    }

    void Scene::_process(real_t delta) {
        for (const auto& root_node : root_nodes_) {
            if (root_node) {
                root_node->_internal_process(delta);
            }
        }
    }

    void Scene::_physics_process(real_t delta) {
        for (const auto& root_node : root_nodes_) {
            if (root_node) {
                root_node->_internal_physics_process(delta);
            }
        }
    }

    void Scene::_input(const InputEvent& event) {
        for (const auto& root_node : root_nodes_) {
            if (root_node) {
                root_node->_internal_input(event);
            }
        }
    }

    bool Scene::save_to_file(const String& path) const {
        // TODO: Implement scene serialization
        std::cout << "[Scene] Scene serialization not yet implemented" << std::endl;
        return false;
    }

    bool Scene::load_from_file(const String& path) {
        // TODO: Implement scene deserialization
        std::cout << "[Scene] Scene deserialization not yet implemented" << std::endl;
        return false;
    }

    void Scene::save_to_dict(std::unordered_map<String, Variant>& dict) const {
        dict["name"] = Variant(name_);
        // TODO: Save root nodes
    }

    void Scene::load_from_dict(const std::unordered_map<String, Variant>& dict) {
        auto it = dict.find("name");
        if (it != dict.end()) {
            name_ = it->second.as_string();
        }
        // TODO: Load root nodes
    }

} // namespace lupine
