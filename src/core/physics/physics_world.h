#pragma once

/**
 * Lupine Engine - Physics System
 * 
 * Box2D-based physics system for 2D physics simulation.
 * This is the C++ equivalent of the Python physics system.
 */

#include "../core_types.h"
#include <memory>
#include <vector>
#include <unordered_map>

namespace lupine {

    // Forward declarations
    class PhysicsBody;
    class CollisionShape;

    /**
     * Physics body types
     */
    enum class BodyType {
        STATIC,
        KINEMATIC,
        DYNAMIC
    };

    /**
     * Collision shape base class
     */
    class CollisionShape {
    public:
        enum Type {
            RECTANGLE,
            CIRCLE,
            POLYGON
        };

        CollisionShape(Type type) : type_(type) {}
        virtual ~CollisionShape() = default;

        Type get_type() const { return type_; }
        virtual Vector2 get_size() const = 0;

    protected:
        Type type_;
    };

    /**
     * Rectangle collision shape
     */
    class RectangleShape : public CollisionShape {
    public:
        RectangleShape(const Vector2& size) : CollisionShape(RECTANGLE), size_(size) {}
        Vector2 get_size() const override { return size_; }
        void set_size(const Vector2& size) { size_ = size; }

    private:
        Vector2 size_;
    };

    /**
     * Circle collision shape
     */
    class CircleShape : public CollisionShape {
    public:
        CircleShape(real_t radius) : CollisionShape(CIRCLE), radius_(radius) {}
        Vector2 get_size() const override { return Vector2(radius_ * 2, radius_ * 2); }
        real_t get_radius() const { return radius_; }
        void set_radius(real_t radius) { radius_ = radius; }

    private:
        real_t radius_;
    };

    /**
     * Physics body for rigid body simulation
     */
    class PhysicsBody {
    public:
        PhysicsBody(BodyType type);
        ~PhysicsBody();

        // Body properties
        BodyType get_type() const { return type_; }
        void set_type(BodyType type);

        Vector2 get_position() const { return position_; }
        void set_position(const Vector2& position);

        real_t get_rotation() const { return rotation_; }
        void set_rotation(real_t rotation);

        Vector2 get_linear_velocity() const { return linear_velocity_; }
        void set_linear_velocity(const Vector2& velocity);

        real_t get_angular_velocity() const { return angular_velocity_; }
        void set_angular_velocity(real_t velocity);

        // Physical properties
        real_t get_mass() const { return mass_; }
        void set_mass(real_t mass);

        real_t get_friction() const { return friction_; }
        void set_friction(real_t friction);

        real_t get_restitution() const { return restitution_; }
        void set_restitution(real_t restitution);

        real_t get_linear_damping() const { return linear_damping_; }
        void set_linear_damping(real_t damping);

        real_t get_angular_damping() const { return angular_damping_; }
        void set_angular_damping(real_t damping);

        // Collision shape
        void set_collision_shape(Ref<CollisionShape> shape);
        Ref<CollisionShape> get_collision_shape() const { return shape_; }

        // Forces and impulses
        void apply_force(const Vector2& force, const Vector2& point = Vector2::ZERO);
        void apply_impulse(const Vector2& impulse, const Vector2& point = Vector2::ZERO);
        void apply_torque(real_t torque);

        // State
        bool is_sleeping() const { return sleeping_; }
        void set_sleeping(bool sleeping) { sleeping_ = sleeping; }

        bool is_enabled() const { return enabled_; }
        void set_enabled(bool enabled) { enabled_ = enabled; }

        uint32_t get_body_id() const { return body_id_; }

    private:
        BodyType type_;
        uint32_t body_id_ = 0;
        void* box2d_body_ = nullptr;  // b2Body*

        // Transform
        Vector2 position_ = Vector2::ZERO;
        real_t rotation_ = 0.0f;

        // Dynamics
        Vector2 linear_velocity_ = Vector2::ZERO;
        real_t angular_velocity_ = 0.0f;

        // Physical properties
        real_t mass_ = 1.0f;
        real_t friction_ = 0.3f;
        real_t restitution_ = 0.0f;
        real_t linear_damping_ = 0.0f;
        real_t angular_damping_ = 0.0f;

        // Shape
        Ref<CollisionShape> shape_;

        // State
        bool sleeping_ = false;
        bool enabled_ = true;
    };

    /**
     * Physics world configuration
     */
    struct PhysicsConfig {
        Vector2 gravity = Vector2(0.0f, 9.8f);
        int velocity_iterations = 8;
        int position_iterations = 3;
        real_t time_step = 1.0f / 60.0f;
        bool allow_sleeping = true;
    };

    /**
     * Main physics world class
     */
    class PhysicsWorld {
    public:
        explicit PhysicsWorld(const PhysicsConfig& config = PhysicsConfig());
        ~PhysicsWorld();

        // Initialization
        bool initialize();
        void cleanup();

        // Simulation
        void step(real_t delta_time);
        void set_paused(bool paused) { paused_ = paused; }
        bool is_paused() const { return paused_; }

        // Body management
        Ref<PhysicsBody> create_body(BodyType type);
        void destroy_body(Ref<PhysicsBody> body);

        // World properties
        Vector2 get_gravity() const { return config_.gravity; }
        void set_gravity(const Vector2& gravity);

        // Configuration
        const PhysicsConfig& get_config() const { return config_; }
        bool is_initialized() const { return initialized_; }

        // Statistics
        int get_body_count() const { return static_cast<int>(bodies_.size()); }

    private:
        PhysicsConfig config_;
        bool initialized_ = false;
        bool paused_ = false;

        // Box2D world
        void* box2d_world_ = nullptr;  // b2World*

        // Bodies
        std::vector<Ref<PhysicsBody>> bodies_;
        uint32_t next_body_id_ = 1;

        // Internal methods
        bool setup_box2d();
        void cleanup_box2d();
        void update_bodies();
    };

} // namespace lupine
