#!/usr/bin/env python3
"""
Test script to debug physics collision shape issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.physics import PhysicsWorld
from nodes.node2d.KinematicBody2D import KinematicBody2D
from nodes.node2d.StaticBody2D import StaticBody2D
from nodes.node2d.CollisionShape2D import CollisionShape2D

def test_physics_shapes():
    """Test physics shape creation and detection"""
    print("=== Physics Shape Debug Test ===")
    
    # Create physics world
    physics_world = PhysicsWorld()
    print(f"Physics world created: {physics_world}")
    
    # Create kinematic body (player)
    player = KinematicBody2D("TestPlayer")
    player.position = [0.0, 0.0]
    print(f"Created player: {player.name} at {player.position}")
    
    # Create collision shape for player
    player_shape = CollisionShape2D("PlayerShape")
    player_shape.shape = "rectangle"
    player_shape.size = [32.0, 32.0]
    player.add_child(player_shape)
    print(f"Added collision shape to player: {player_shape.name} ({player_shape.shape}, size: {player_shape.size})")
    
    # Create static body (floor)
    floor = StaticBody2D("TestFloor")
    floor.position = [0.0, -100.0]  # Below player
    print(f"Created floor: {floor.name} at {floor.position}")
    
    # Create collision shape for floor
    floor_shape = CollisionShape2D("FloorShape")
    floor_shape.shape = "rectangle"
    floor_shape.size = [200.0, 32.0]
    floor.add_child(floor_shape)
    print(f"Added collision shape to floor: {floor_shape.name} ({floor_shape.shape}, size: {floor_shape.size})")
    
    # Add bodies to physics world
    print("\n=== Adding bodies to physics world ===")
    player_body = physics_world.add_node(player)
    floor_body = physics_world.add_node(floor)
    
    print(f"Player physics body: {player_body}")
    print(f"Player has {len(player_body.pymunk_shapes) if player_body and player_body.pymunk_shapes else 0} shapes")
    
    print(f"Floor physics body: {floor_body}")
    print(f"Floor has {len(floor_body.pymunk_shapes) if floor_body and floor_body.pymunk_shapes else 0} shapes")
    
    # Test shape cast
    print("\n=== Testing shape cast ===")
    result = physics_world.shape_cast(
        "rectangle",
        (32.0, 32.0),
        (0.0, 0.0),      # Start at player position
        (0.0, -150.0),   # Move down towards floor
        exclude_body=player_body
    )
    
    if result:
        print(f"Shape cast hit: {result}")
    else:
        print("Shape cast found no collision")
    
    print("\n=== Test complete ===")

if __name__ == "__main__":
    test_physics_shapes()
