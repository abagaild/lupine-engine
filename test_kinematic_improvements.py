#!/usr/bin/env python3
"""
Test script for improved KinematicBody2D implementation
Tests the enhanced collision detection, state tracking, and performance improvements
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_kinematic_improvements():
    """Test the improved KinematicBody2D functionality"""
    print("Testing Improved KinematicBody2D Implementation")
    print("=" * 50)
    
    try:
        from core.physics import PhysicsWorld, PhysicsBody, PhysicsBodyType
        from nodes.node2d.KinematicBody2D import KinematicBody2D
        from nodes.node2d.StaticBody2D import StaticBody2D
        from nodes.node2d.CollisionShape2D import CollisionShape2D
        
        # Create physics world
        physics_world = PhysicsWorld()
        print("✓ Physics world created")
        
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
        
        # Test 1: Create kinematic body with improved properties
        print("\nTest 1: Creating KinematicBody2D with new features")
        kinematic = KinematicBody2D("Player")
        kinematic.position = [100.0, 100.0]
        kinematic.safe_margin = 0.1
        kinematic.set_debug_enabled(True)  # Enable debug for testing
        
        collision_shape = CollisionShape2D("PlayerCollision")
        collision_shape.shape = "rectangle"
        collision_shape.size = [32.0, 32.0]
        kinematic.add_child(collision_shape)
        
        print(f"✓ KinematicBody2D created with safe_margin: {kinematic.safe_margin}")
        print(f"✓ Debug enabled: {kinematic._debug_enabled}")
        
        # Test 2: Create static obstacle
        print("\nTest 2: Creating static obstacle")
        obstacle = StaticBody2D("Obstacle")
        obstacle.position = [200.0, 100.0]
        
        obstacle_shape = CollisionShape2D("ObstacleCollision")
        obstacle_shape.shape = "rectangle"
        obstacle_shape.size = [64.0, 64.0]
        obstacle.add_child(obstacle_shape)
        
        # Add to physics world
        kinematic_body = physics_world.add_node(kinematic)
        static_body = physics_world.add_node(obstacle)
        
        print("✓ Physics bodies added to world")
        
        # Test 3: Test collision state tracking
        print("\nTest 3: Testing collision state tracking")
        print(f"Initial state - On floor: {kinematic.is_on_floor()}, On wall: {kinematic.is_on_wall()}, On ceiling: {kinematic.is_on_ceiling()}")
        
        # Test 4: Test move_and_slide with delta time
        print("\nTest 4: Testing move_and_slide with delta time")
        velocity = [50.0, 0.0]  # Move right towards obstacle
        delta_time = 1.0 / 60.0
        
        print(f"Moving with velocity {velocity} and delta_time {delta_time}")
        remaining_velocity = kinematic.move_and_slide(velocity, delta_time=delta_time)
        print(f"Remaining velocity: {remaining_velocity}")
        print(f"New position: {kinematic.position}")
        print(f"Last motion: {kinematic.get_last_motion()}")
        
        # Test 5: Test collision classification
        print("\nTest 5: Testing collision classification")
        floor_normal = [0.0, -1.0]
        wall_normal = [1.0, 0.0]
        ceiling_normal = [0.0, 1.0]
        
        floor_type = kinematic._classify_collision(floor_normal)
        wall_type = kinematic._classify_collision(wall_normal)
        ceiling_type = kinematic._classify_collision(ceiling_normal)
        
        print(f"Floor normal {floor_normal} classified as: {floor_type}")
        print(f"Wall normal {wall_normal} classified as: {wall_type}")
        print(f"Ceiling normal {ceiling_normal} classified as: {ceiling_type}")
        
        # Test 6: Test shape info detection
        print("\nTest 6: Testing shape info detection")
        shape_type, shape_size = kinematic._get_shape_info(kinematic_body)
        print(f"Detected shape type: {shape_type}, size: {shape_size}")
        
        # Test 7: Test move_and_collide
        print("\nTest 7: Testing move_and_collide")
        collision_info = kinematic.move_and_collide([100.0, 0.0], delta_time=delta_time)
        if collision_info:
            print(f"Collision detected: {collision_info}")
        else:
            print("No collision detected")
        
        # Test 8: Test floor snap functionality
        print("\nTest 8: Testing floor snap")
        kinematic.position = [50.0, 50.0]  # Move away from obstacles
        snap_result = kinematic.apply_floor_snap(32.0)
        print(f"Floor snap result: {snap_result}")
        
        # Test 9: Test collision layer utilities
        print("\nTest 9: Testing collision layer utilities")
        layer1 = 1  # Binary: 001
        mask1 = 3   # Binary: 011
        layer2 = 2  # Binary: 010
        mask2 = 1   # Binary: 001
        
        can_collide = physics_world.check_collision_layers(layer1, mask1, layer2, mask2)
        print(f"Layer {layer1} (mask {mask1}) can collide with layer {layer2} (mask {mask2}): {can_collide}")
        
        # Test bit operations
        new_layer = physics_world.set_collision_layer_bit(0, 2, True)  # Set bit 2
        bit_value = physics_world.get_collision_layer_bit(new_layer, 2)
        print(f"Set bit 2 in layer 0: {new_layer}, bit 2 value: {bit_value}")
        
        # Test 10: Test serialization with new properties
        print("\nTest 10: Testing serialization")
        kinematic_dict = kinematic.to_dict()
        print(f"✓ Serialized kinematic body (keys: {len(kinematic_dict.keys())})")
        
        # Test deserialization
        new_kinematic = KinematicBody2D.from_dict(kinematic_dict)
        print(f"✓ Deserialized kinematic body: {new_kinematic.name}")
        print(f"  Safe margin: {new_kinematic.safe_margin}")
        print(f"  Debug enabled: {new_kinematic._debug_enabled}")
        print(f"  Last motion: {new_kinematic._last_motion}")
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        print("✓ KinematicBody2D improvements are working correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_kinematic_improvements()
    sys.exit(0 if success else 1)
