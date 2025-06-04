# Advanced Player Controller

A comprehensive, production-ready player controller prefab for Lupine Engine with multiple movement modes and advanced features.

## Features

### Movement Modes
- **4-Directional**: Grid-based movement (no diagonals)
- **8-Directional**: Full directional movement with normalized diagonals
- **Platformer**: Gravity-based movement with jumping and wall interactions
- **Sidescroller**: Horizontal-focused movement with responsive controls

### Advanced Mechanics
- **Coyote Time**: Grace period after leaving ground where jump is still allowed
- **Jump Buffering**: Remember jump input briefly before landing
- **Variable Jump Height**: Hold jump for higher jumps, release for shorter ones
- **Wall Jumping**: Jump off walls when wall jumping is enabled
- **Wall Sliding**: Slide down walls at controlled speed
- **Air Control**: Reduced movement control while airborne
- **Ground/Wall Detection**: Automatic collision detection using Area2D sensors

## Prefab Structure

```
Player (KinematicBody2D) - Main physics body
├── Sprite - Visual representation
├── CollisionShape2D - Main collision shape (32x48 rectangle)
├── GroundDetector (Area2D) - Detects ground contact
│   └── GroundShape (CollisionShape2D)
├── WallDetectorLeft (Area2D) - Detects left wall contact
│   └── WallShapeLeft (CollisionShape2D)
└── WallDetectorRight (Area2D) - Detects right wall contact
    └── WallShapeRight (CollisionShape2D)
```

## Export Variables

### Movement Configuration
- `movement_mode`: Movement mode ["4_directional", "8_directional", "platformer", "sidescroller"]
- `speed`: Base movement speed (300.0 pixels/second)
- `acceleration`: Acceleration rate (1500.0)
- `friction`: Friction/deceleration rate (1200.0)

### Platformer/Sidescroller Settings
- `gravity`: Gravity strength (980.0 pixels/second²)
- `jump_velocity`: Initial jump velocity (-400.0, negative = up)
- `max_fall_speed`: Maximum falling speed (600.0)
- `wall_jump_velocity`: Horizontal velocity for wall jumps (300.0)
- `wall_slide_speed`: Speed when sliding down walls (100.0)

### Advanced Features
- `coyote_time`: Grace period after leaving ground (0.1 seconds)
- `jump_buffer_time`: Jump input buffer time (0.1 seconds)
- `variable_jump_height`: Enable variable jump height (true)
- `wall_jumping_enabled`: Enable wall jumping mechanics (true)
- `air_control`: Air movement control factor 0-1 (0.8)

### Input Settings
- `jump_key`: Key for jumping ("KEY_SPACE")
- `left_key`: Key for moving left ("KEY_A")
- `right_key`: Key for moving right ("KEY_D")
- `up_key`: Key for moving up ("KEY_W")
- `down_key`: Key for moving down ("KEY_S")

### Debug
- `debug_mode`: Show debug information (false)

## Usage

### Basic Setup
1. Add the AdvancedPlayerController prefab to your scene
2. Set the desired movement mode in the inspector
3. Adjust speed and physics parameters as needed
4. The controller is ready to use!

### Movement Mode Details

#### 4-Directional Movement
- Perfect for grid-based games
- Prioritizes horizontal movement over vertical
- No diagonal movement
- Smooth acceleration/deceleration

#### 8-Directional Movement
- Full directional movement
- Normalized diagonal movement (prevents faster diagonal speed)
- Ideal for top-down games
- Smooth acceleration/deceleration

#### Platformer Movement
- Gravity-based physics
- Jump mechanics with variable height
- Wall jumping and wall sliding
- Coyote time and jump buffering
- Air control for mid-air adjustments

#### Sidescroller Movement
- Horizontal-focused movement
- Faster acceleration for responsive controls
- Higher friction for snappy movement
- Gravity and jumping like platformer mode

### Public API Methods

```python
# Movement mode control
get_movement_mode()           # Get current movement mode
set_movement_mode(new_mode)   # Change movement mode

# Velocity control
get_velocity()                # Get current velocity vector
set_velocity(new_velocity)    # Set velocity vector

# State queries
is_grounded()                 # Check if on ground
is_against_wall()             # Check if against any wall

# Actions
jump()                        # Force a jump
stop()                        # Stop all movement
teleport(new_position)        # Teleport to position
```

## Collision Setup

The prefab includes automatic collision detection using Area2D sensors:

- **GroundDetector**: Positioned below the player to detect ground contact
- **WallDetectorLeft/Right**: Positioned on sides to detect wall contact
- **Main CollisionShape2D**: Handles actual physics collisions

Make sure your level geometry has appropriate collision layers that match the detector settings.

## Customization Tips

### Adjusting Physics Feel
- **Snappy Movement**: Increase acceleration, increase friction
- **Floaty Movement**: Decrease gravity, increase air control
- **Responsive Jumping**: Decrease coyote time, increase jump buffer time
- **Heavy Character**: Increase gravity, decrease jump velocity

### Input Customization
- Change key bindings in the export variables
- Add gamepad support by modifying the `_get_input_vector()` function
- Implement custom input actions for special abilities

### Animation Integration
- Use the `facing_direction` variable for sprite flipping
- Check movement state variables for animation triggers
- Hook into the collision callbacks for landing/wall hit effects

## Performance Notes

- Uses `move_and_slide()` for physics-based collision handling
- Efficient collision detection using Area2D sensors
- Minimal computational overhead with smart timer management
- Scales well for multiple player instances

## Compatibility

- Works with all Lupine Engine physics bodies
- Compatible with the collision system and polygon builder
- Integrates seamlessly with the scene system
- Supports the export variable system for easy customization

This prefab provides a solid foundation for any 2D game requiring player movement, from simple top-down games to complex platformers.
