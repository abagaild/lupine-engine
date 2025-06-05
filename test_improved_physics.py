#!/usr/bin/env python3
"""
Test script for the improved physics implementation, especially shape_cast functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_shape_cast_improvements():
    """Test the improved shape_cast implementation"""
    print("Testing improved physics shape_cast implementation...")
    
    try:
        from core.physics import PhysicsWorld, PhysicsBody, PhysicsBodyType
        from nodes.base.Node2D import Node2D
        from nodes.node2d.KinematicBody2D import KinematicBody2D
        from nodes.node2d.StaticBody2D import StaticBody2D
        
        # Create physics world
        physics_world = PhysicsWorld()
        print("✓ Physics world created")
        
        # Create test nodes with collision shapes
        from nodes.node2d.CollisionShape2D import CollisionShape2D

        kinematic_node = KinematicBody2D("TestKinematic")
        kinematic_node.position = [100.0, 100.0]

        # Add collision shape to kinematic
        kinematic_shape = CollisionShape2D("KinematicShape")
        kinematic_shape.shape = "rectangle"
        kinematic_shape.size = [32.0, 32.0]
        kinematic_node.add_child(kinematic_shape)

        static_node = StaticBody2D("TestStatic")
        static_node.position = [200.0, 100.0]

        # Add collision shape to static
        static_shape = CollisionShape2D("StaticShape")
        static_shape.shape = "rectangle"
        static_shape.size = [64.0, 64.0]
        static_node.add_child(static_shape)
        
        # Add physics bodies
        kinematic_body = physics_world.add_node(kinematic_node)
        static_body = physics_world.add_node(static_node)
        
        print("✓ Physics bodies created")
        
        # Test 1: Basic shape cast with no collision
        print("\nTest 1: Shape cast with no collision")
        result = physics_world.shape_cast(
            "rectangle",
            (32.0, 32.0),
            (50.0, 50.0),
            (80.0, 50.0),
            exclude_body=kinematic_body
        )
        
        if result is None:
            print("✓ No collision detected as expected")
        else:
            print(f"✗ Unexpected collision: {result}")
        
        # Test 2: Shape cast with collision
        print("\nTest 2: Shape cast with collision")
        result = physics_world.shape_cast(
            "rectangle",
            (32.0, 32.0),
            (100.0, 100.0),
            (200.0, 100.0),
            exclude_body=kinematic_body
        )
        
        if result is not None:
            print(f"✓ Collision detected: distance={result['distance']:.3f}, normal={result['normal']}")
            print(f"  Point: {result['point']}, Body: {result['body'].node.name if result['body'] else 'None'}")
        else:
            print("✗ Expected collision but none detected")
        
        # Test 3: Circle shape cast
        print("\nTest 3: Circle shape cast")
        result = physics_world.shape_cast(
            "circle",
            (32.0, 32.0),  # Diameter
            (100.0, 100.0),
            (200.0, 100.0),
            exclude_body=kinematic_body
        )
        
        if result is not None:
            print(f"✓ Circle collision detected: distance={result['distance']:.3f}")
        else:
            print("✗ Expected circle collision but none detected")
        
        # Test 4: Large movement delta (should be handled by stepped collision detection)
        print("\nTest 4: Large movement delta")
        result = physics_world.shape_cast(
            "rectangle",
            (32.0, 32.0),
            (0.0, 100.0),
            (500.0, 100.0),  # Large movement
            exclude_body=kinematic_body
        )
        
        if result is not None:
            print(f"✓ Large movement collision detected: distance={result['distance']:.3f}")
        else:
            print("✗ Expected collision with large movement but none detected")
        
        # Test 5: Shape cast all (multiple collisions)
        print("\nTest 5: Shape cast all")
        
        # Add another static body
        static_node2 = StaticBody2D("TestStatic2")
        static_node2.position = [300.0, 100.0]

        # Add collision shape to second static body
        static_shape2 = CollisionShape2D("StaticShape2")
        static_shape2.shape = "rectangle"
        static_shape2.size = [64.0, 64.0]
        static_node2.add_child(static_shape2)

        static_body2 = physics_world.add_node(static_node2)
        
        results = physics_world.shape_cast_all(
            "rectangle",
            (32.0, 32.0),
            (100.0, 100.0),
            (400.0, 100.0),
            exclude_body=kinematic_body
        )
        
        print(f"✓ Found {len(results)} collisions:")
        for i, result in enumerate(results):
            print(f"  {i+1}. Distance: {result['distance']:.3f}, Body: {result['body'].node.name if result['body'] else 'None'}")
        
        # Test 6: Test move function
        print("\nTest 6: Test move function")
        if kinematic_body:
            collision = physics_world.test_move(kinematic_body, (100.0, 0.0))

            if collision is not None:
                print(f"✓ Test move detected collision: distance={collision['distance']:.3f}")
            else:
                print("✗ Expected test move collision but none detected")
        else:
            print("✗ Kinematic body not created")
        
        # Test 7: Zero movement (overlap check)
        print("\nTest 7: Zero movement overlap check")
        result = physics_world.shape_cast(
            "rectangle",
            (32.0, 32.0),
            (200.0, 100.0),  # Same position as static body
            (200.0, 100.0),  # No movement
            exclude_body=kinematic_body
        )
        
        if result is not None:
            print(f"✓ Overlap detected: {result['body'].node.name if result['body'] else 'None'}")
        else:
            print("✗ Expected overlap but none detected")
        
        print("\n🎉 All shape_cast improvement tests completed!")
        
    except Exception as e:
        print(f"✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

def test_kinematic_body_improvements():
    """Test the improved KinematicBody2D collision detection"""
    print("\nTesting KinematicBody2D improvements...")
    
    try:
        from core.physics import PhysicsWorld, PhysicsBodyType
        from nodes.node2d.KinematicBody2D import KinematicBody2D
        from nodes.node2d.StaticBody2D import StaticBody2D
        from nodes.node2d.CollisionShape2D import CollisionShape2D
        
        # Create physics world
        physics_world = PhysicsWorld()

        # Set up a mock game engine so KinematicBody2D can find the physics world
        class MockSystems:
            def __init__(self, physics_world):
                self.physics_world = physics_world

        class MockGameEngine:
            def __init__(self, physics_world):
                self.systems = MockSystems(physics_world)

        # Set up global game engine
        import core.game_engine
        core.game_engine._global_game_engine = MockGameEngine(physics_world)
        
        # Create kinematic body with collision shape
        kinematic = KinematicBody2D("Player")
        kinematic.position = [100.0, 100.0]
        
        collision_shape = CollisionShape2D("PlayerCollision")
        collision_shape.shape = "rectangle"
        collision_shape.size = [32.0, 32.0]
        kinematic.add_child(collision_shape)
        
        # Create static obstacle
        obstacle = StaticBody2D("Obstacle")
        obstacle.position = [200.0, 100.0]
        
        obstacle_shape = CollisionShape2D("ObstacleCollision")
        obstacle_shape.shape = "rectangle"
        obstacle_shape.size = [64.0, 64.0]
        obstacle.add_child(obstacle_shape)
        
        # Add to physics world
        physics_world.add_node(kinematic)
        physics_world.add_node(obstacle)
        
        print("✓ Test scene created")
        
        # Test move_and_slide with collision
        print("\nTesting move_and_slide with collision...")
        velocity = [120.0, 0.0]  # Move right towards obstacle
        
        # This should detect collision and slide
        remaining_velocity = kinematic.move_and_slide(velocity)
        
        print(f"✓ Move and slide completed")
        print(f"  Original velocity: {velocity}")
        print(f"  Remaining velocity: {remaining_velocity}")
        print(f"  Final position: {kinematic.position}")
        
        # Test move_and_collide
        print("\nTesting move_and_collide...")
        kinematic.position = [100.0, 100.0]  # Reset position
        
        collision_info = kinematic.move_and_collide([120.0, 0.0])
        
        if collision_info:
            print(f"✓ Collision detected:")
            print(f"  Collider: {collision_info['collider'].name}")
            print(f"  Position: {collision_info['position']}")
            print(f"  Normal: {collision_info['normal']}")
        else:
            print("✗ Expected collision but none detected")
        
        print("\n🎉 KinematicBody2D improvement tests completed!")
        
    except Exception as e:
        print(f"✗ KinematicBody2D test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("IMPROVED PHYSICS IMPLEMENTATION TESTS")
    print("=" * 60)
    
    test_shape_cast_improvements()
    test_kinematic_body_improvements()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)
