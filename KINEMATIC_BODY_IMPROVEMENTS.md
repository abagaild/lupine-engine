# KinematicBody2D and Physics System Improvements

This document outlines the comprehensive improvements made to the KinematicBody2D implementation and the physics system in Lupine Engine.

## Overview

The KinematicBody2D node has been significantly enhanced with better collision detection, state tracking, performance optimizations, and more robust physics integration.

## Key Improvements

### 1. Enhanced Collision Detection

#### Improved Shape Detection
- **Automatic shape type detection**: Automatically detects circle, rectangle, and polygon shapes
- **Accurate size calculation**: Calculates bounding boxes for complex polygon shapes
- **Better shape casting**: Uses appropriate shape types for collision detection

#### Collision Classification
- **Smart collision type detection**: Automatically classifies collisions as floor, wall, or ceiling
- **Configurable floor angle**: Uses `floor_max_angle` property to determine what counts as floor
- **Accurate normal vectors**: Stores and provides access to collision normals

### 2. Performance Optimizations

#### Reduced Debug Output
- **Configurable debug logging**: Debug output can be enabled/disabled per body
- **Performance-focused**: Minimal logging by default to improve performance
- **Selective debugging**: Only log when explicitly enabled with `set_debug_enabled(True)`

#### Better Delta Time Handling
- **Accurate timing**: Uses actual delta time instead of hardcoded 1/60 seconds
- **Flexible movement**: Supports variable frame rates and timing
- **Consistent physics**: Better integration with physics world timing

### 3. Collision State Tracking

#### Real-time State Information
```python
# Check collision states
is_on_floor = kinematic.is_on_floor()
is_on_wall = kinematic.is_on_wall()
is_on_ceiling = kinematic.is_on_ceiling()

# Get collision normals
floor_normal = kinematic.get_floor_normal()
wall_normal = kinematic.get_wall_normal()
ceiling_normal = kinematic.get_ceiling_normal()
```

#### Motion Tracking
```python
# Get the actual motion that occurred
last_motion = kinematic.get_last_motion()

# Get floor velocity (for moving platforms)
floor_velocity = kinematic.get_floor_velocity()
```

### 4. Enhanced Movement Methods

#### Improved move_and_slide()
```python
# Enhanced move_and_slide with delta time support
remaining_velocity = kinematic.move_and_slide(
    velocity=[100.0, 0.0],
    floor_normal=[0.0, -1.0],  # Optional custom floor normal
    delta_time=1.0/60.0        # Actual frame delta time
)
```

**Features:**
- Proper collision state tracking during movement
- Configurable safe margin for collision avoidance
- Better sliding mechanics with friction application
- Support for custom floor normals

#### Enhanced move_and_collide()
```python
# Move and get detailed collision information
collision_info = kinematic.move_and_collide(
    velocity=[50.0, 0.0],
    delta_time=1.0/60.0
)

if collision_info:
    collider = collision_info['collider']
    position = collision_info['position']
    normal = collision_info['normal']
    travel = collision_info['travel']
    remainder = collision_info['remainder']
```

### 5. New Utility Methods

#### Floor Snapping
```python
# Snap to floor if within range (useful for slopes)
snapped = kinematic.apply_floor_snap(snap_length=32.0)
```

#### Debug Control
```python
# Enable/disable debug logging
kinematic.set_debug_enabled(True)
```

### 6. Physics System Enhancements

#### Collision Layer Utilities
```python
# Check if two layers can collide
can_collide = physics_world.check_collision_layers(layer1, mask1, layer2, mask2)

# Bit manipulation for collision layers
new_layer = physics_world.set_collision_layer_bit(layer, bit_index, True)
bit_value = physics_world.get_collision_layer_bit(layer, bit_index)
```

#### Overlap Detection
```python
# Get all bodies overlapping with a specific body
overlapping_bodies = physics_world.get_overlapping_bodies(physics_body)
```

#### Better Timing
- **Adaptive delta time**: Physics world uses actual delta time with safety caps
- **Smoother simulation**: Better integration with variable frame rates

### 7. New Export Variables

#### Safe Margin
```python
"safe_margin": {
    "type": "float",
    "value": 0.08,
    "description": "Collision margin for safe movement"
}
```

This property controls how close the kinematic body can get to other objects before being considered in collision.

### 8. Enhanced Serialization

#### Complete State Preservation
The serialization now includes all new properties:
- `safe_margin`
- `_last_motion`
- `_floor_normal`, `_wall_normal`, `_ceiling_normal`
- `_floor_velocity`
- `_debug_enabled`

## Usage Examples

### Basic Player Controller
```python
class PlayerController:
    def __init__(self, kinematic_body):
        self.body = kinematic_body
        self.body.set_debug_enabled(False)  # Disable debug for performance
        self.velocity = [0.0, 0.0]
        self.speed = 200.0
        self.jump_force = 400.0
        self.gravity = 980.0
    
    def _physics_process(self, delta_time):
        # Handle input
        if Input.is_action_pressed("move_left"):
            self.velocity[0] = -self.speed
        elif Input.is_action_pressed("move_right"):
            self.velocity[0] = self.speed
        else:
            self.velocity[0] = 0.0
        
        # Apply gravity
        if not self.body.is_on_floor():
            self.velocity[1] += self.gravity * delta_time
        
        # Jump
        if Input.is_action_just_pressed("jump") and self.body.is_on_floor():
            self.velocity[1] = -self.jump_force
        
        # Move with collision
        self.velocity = self.body.move_and_slide(self.velocity, delta_time=delta_time)
        
        # Optional: Snap to floor on slopes
        if self.velocity[1] >= 0:
            self.body.apply_floor_snap(8.0)
```

### Collision Detection
```python
# Check for specific collision types
if kinematic.is_on_floor():
    print("Player is on the ground")
    floor_normal = kinematic.get_floor_normal()
    print(f"Floor angle: {math.degrees(math.atan2(floor_normal[1], floor_normal[0]))}")

if kinematic.is_on_wall():
    print("Player is touching a wall")
    wall_normal = kinematic.get_wall_normal()
    # Could implement wall jumping here

# Get detailed movement information
last_motion = kinematic.get_last_motion()
if abs(last_motion[0]) < 0.1 and abs(last_motion[1]) < 0.1:
    print("Player movement was blocked")
```

## Performance Benefits

1. **Reduced logging overhead**: Debug output only when needed
2. **Better collision detection**: More accurate with fewer false positives
3. **Efficient state tracking**: Collision states updated only during movement
4. **Optimized physics integration**: Better synchronization with physics world
5. **Configurable precision**: Safe margin allows tuning collision precision vs performance

## Backward Compatibility

All existing KinematicBody2D functionality remains unchanged. The improvements are additive and don't break existing code. Old scenes and scripts will continue to work without modification.

## Testing

Run the test suite to verify all improvements:
```bash
python test_kinematic_improvements.py
```

This comprehensive test covers all new features and ensures they work correctly together.
