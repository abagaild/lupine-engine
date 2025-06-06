/**
 * Lupine Engine - Physics World Implementation
 */

#include "physics_world.h"
#include <iostream>
#include <algorithm>

namespace lupine {

    //=============================================================================
    // PhysicsBody Implementation
    //=============================================================================

    PhysicsBody::PhysicsBody(BodyType type) : type_(type) {
        body_id_ = 0; // Will be set by PhysicsWorld
        // TODO: Create Box2D body
        std::cout << "[PhysicsBody] Physics body creation not yet implemented" << std::endl;
    }

    PhysicsBody::~PhysicsBody() {
        // TODO: Destroy Box2D body
    }

    void PhysicsBody::set_type(BodyType type) {
        type_ = type;
        // TODO: Update Box2D body type
    }

    void PhysicsBody::set_position(const Vector2& position) {
        position_ = position;
        if (box2d_body_) {
            // TODO: Set Box2D body position
            // b2Vec2 pos(position.x, position.y);
            // static_cast<b2Body*>(box2d_body_)->SetTransform(pos, rotation_);
        }
    }

    void PhysicsBody::set_rotation(real_t rotation) {
        rotation_ = rotation;
        if (box2d_body_) {
            // TODO: Set Box2D body rotation
            // b2Vec2 pos(position_.x, position_.y);
            // static_cast<b2Body*>(box2d_body_)->SetTransform(pos, rotation);
        }
    }

    void PhysicsBody::set_linear_velocity(const Vector2& velocity) {
        linear_velocity_ = velocity;
        if (box2d_body_) {
            // TODO: Set Box2D body linear velocity
            // b2Vec2 vel(velocity.x, velocity.y);
            // static_cast<b2Body*>(box2d_body_)->SetLinearVelocity(vel);
        }
    }

    void PhysicsBody::set_angular_velocity(real_t velocity) {
        angular_velocity_ = velocity;
        if (box2d_body_) {
            // TODO: Set Box2D body angular velocity
            // static_cast<b2Body*>(box2d_body_)->SetAngularVelocity(velocity);
        }
    }

    void PhysicsBody::set_mass(real_t mass) {
        mass_ = mass;
        // TODO: Update Box2D body mass data
    }

    void PhysicsBody::set_friction(real_t friction) {
        friction_ = friction;
        // TODO: Update Box2D fixture friction
    }

    void PhysicsBody::set_restitution(real_t restitution) {
        restitution_ = restitution;
        // TODO: Update Box2D fixture restitution
    }

    void PhysicsBody::set_linear_damping(real_t damping) {
        linear_damping_ = damping;
        if (box2d_body_) {
            // TODO: Set Box2D body linear damping
            // static_cast<b2Body*>(box2d_body_)->SetLinearDamping(damping);
        }
    }

    void PhysicsBody::set_angular_damping(real_t damping) {
        angular_damping_ = damping;
        if (box2d_body_) {
            // TODO: Set Box2D body angular damping
            // static_cast<b2Body*>(box2d_body_)->SetAngularDamping(damping);
        }
    }

    void PhysicsBody::set_collision_shape(Ref<CollisionShape> shape) {
        shape_ = shape;
        // TODO: Create Box2D fixture from shape
    }

    void PhysicsBody::apply_force(const Vector2& force, const Vector2& point) {
        if (box2d_body_) {
            // TODO: Apply force to Box2D body
            // b2Vec2 f(force.x, force.y);
            // b2Vec2 p(point.x, point.y);
            // static_cast<b2Body*>(box2d_body_)->ApplyForce(f, p, true);
        }
    }

    void PhysicsBody::apply_impulse(const Vector2& impulse, const Vector2& point) {
        if (box2d_body_) {
            // TODO: Apply impulse to Box2D body
            // b2Vec2 i(impulse.x, impulse.y);
            // b2Vec2 p(point.x, point.y);
            // static_cast<b2Body*>(box2d_body_)->ApplyLinearImpulse(i, p, true);
        }
    }

    void PhysicsBody::apply_torque(real_t torque) {
        if (box2d_body_) {
            // TODO: Apply torque to Box2D body
            // static_cast<b2Body*>(box2d_body_)->ApplyTorque(torque, true);
        }
    }

    //=============================================================================
    // PhysicsWorld Implementation
    //=============================================================================

    PhysicsWorld::PhysicsWorld(const PhysicsConfig& config) : config_(config) {
    }

    PhysicsWorld::~PhysicsWorld() {
        cleanup();
    }

    bool PhysicsWorld::initialize() {
        if (initialized_) {
            return true;
        }

        std::cout << "[PhysicsWorld] Initializing Box2D physics world..." << std::endl;

        if (!setup_box2d()) {
            std::cerr << "[PhysicsWorld] Failed to setup Box2D" << std::endl;
            return false;
        }

        initialized_ = true;
        std::cout << "[PhysicsWorld] Physics world initialized successfully" << std::endl;
        return true;
    }

    void PhysicsWorld::cleanup() {
        if (!initialized_) {
            return;
        }

        std::cout << "[PhysicsWorld] Cleaning up physics world..." << std::endl;

        // Clear bodies
        bodies_.clear();

        // Cleanup Box2D
        cleanup_box2d();

        initialized_ = false;
    }

    void PhysicsWorld::step(real_t delta_time) {
        if (!initialized_ || paused_) {
            return;
        }

        if (box2d_world_) {
            // TODO: Step Box2D world
            // static_cast<b2World*>(box2d_world_)->Step(delta_time, 
            //     config_.velocity_iterations, config_.position_iterations);
        }

        // Update body transforms
        update_bodies();
    }

    Ref<PhysicsBody> PhysicsWorld::create_body(BodyType type) {
        auto body = std::make_shared<PhysicsBody>(type);
        body->body_id_ = next_body_id_++;
        bodies_.push_back(Ref<PhysicsBody>(body));
        return Ref<PhysicsBody>(body);
    }

    void PhysicsWorld::destroy_body(Ref<PhysicsBody> body) {
        if (!body) {
            return;
        }

        bodies_.erase(
            std::remove_if(bodies_.begin(), bodies_.end(),
                          [&body](const Ref<PhysicsBody>& b) {
                              return b.get() == body.get();
                          }),
            bodies_.end());
    }

    void PhysicsWorld::set_gravity(const Vector2& gravity) {
        config_.gravity = gravity;
        if (box2d_world_) {
            // TODO: Set Box2D world gravity
            // b2Vec2 g(gravity.x, gravity.y);
            // static_cast<b2World*>(box2d_world_)->SetGravity(g);
        }
    }

    bool PhysicsWorld::setup_box2d() {
        // TODO: Create Box2D world
        std::cout << "[PhysicsWorld] Box2D setup not yet implemented" << std::endl;
        return true;
    }

    void PhysicsWorld::cleanup_box2d() {
        // TODO: Destroy Box2D world
        if (box2d_world_) {
            // delete static_cast<b2World*>(box2d_world_);
            box2d_world_ = nullptr;
        }
    }

    void PhysicsWorld::update_bodies() {
        // TODO: Update body transforms from Box2D
        for (auto& body : bodies_) {
            if (body && body->box2d_body_) {
                // Get transform from Box2D body and update our body
                // const b2Transform& transform = static_cast<b2Body*>(body->box2d_body_)->GetTransform();
                // body->position_ = Vector2(transform.p.x, transform.p.y);
                // body->rotation_ = transform.q.GetAngle();
            }
        }
    }

} // namespace lupine
