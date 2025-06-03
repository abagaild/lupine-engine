# SimplePlayerController Prefab

A simplified player controller prefab designed for testing basic movement and collision in the Lupine Engine. This is a stripped-down version of the full PlayerController, focusing only on essential movement functionality.

## Features

- **Basic 8-directional topdown movement** with WASD/Arrow keys
- **Large collision zone** (64x64 pixels) for easy collision testing
- **Simple acceleration and friction** physics
- **Debug visualization** showing velocity and input vectors
- **Colored sprite** (bright blue) for easy visibility
- **No complex features** - no sprint, stamina, interactions, or animations

## Quick Start

### 1. Using the Prefab

Load the prefab in your scene:
```json
{
  "name": "Player",
  "type": "SimplePlayerController",
  "position": [400.0, 300.0],
  "properties": {
    "speed": 200.0,
    "debug_mode": true
  }
}
```

### 2. Test Scene

Use the included test scene `test_simple_player_controller.json` which includes:
- SimplePlayerController in the center
- Boundary walls for collision testing
- A center obstacle to test navigation

### 3. Controls

- **WASD** or **Arrow Keys** - Move in 8 directions
- Movement is normalized for diagonal directions
- Smooth acceleration and friction

## Configuration

### Movement Properties
- `speed` (float, default: 200.0) - Maximum movement speed
- `acceleration` (float, default: 800.0) - How quickly the player accelerates
- `friction` (float, default: 1000.0) - How quickly the player stops
- `debug_mode` (bool, default: true) - Show debug vectors

### Collision
- **Collision Shape**: 64x64 pixel rectangle
- **Collision Layer**: 1 (default player layer)
- **Collision Mask**: 1 (collides with default layer)

## Debug Features

When `debug_mode` is enabled, you'll see:
- **Red line** - Current velocity vector (length = 50 pixels max)
- **Blue line** - Current input vector (length = 40 pixels max)
- **Green outline** - Collision shape boundary

## Public API

```lsc
# Get current movement state
var velocity = player.get_velocity()
var input = player.get_input_vector()
var moving = player.is_moving()

# Print debug information
player.print_debug_info()
```

## Differences from Full PlayerController

**Removed Features:**
- Sprint system and stamina
- Multiple movement modes (platformer, sidescroller)
- Interaction system
- Animation support
- Complex state tracking
- Signal emissions
- Jump mechanics

**Simplified Features:**
- Only topdown 8-directional movement
- Basic physics (acceleration/friction)
- Single collision shape
- Simple debug visualization

## Use Cases

Perfect for:
- **Testing collision systems** - Large collision zone makes it easy to test
- **Prototyping movement** - Quick setup without complex features
- **Learning the engine** - Simple, readable code
- **Basic games** - When you don't need advanced features
- **Movement debugging** - Clear visual feedback

## Files

- `nodes/prefabs/SimplePlayerController.lsc` - Main script
- `nodes/prefabs/SimplePlayerController.json` - Prefab definition
- `test_simple_player_controller.json` - Test scene with walls
- `docs/SIMPLE_PLAYER_CONTROLLER.md` - This documentation

## Extending

To add features:
1. Copy the SimplePlayerController files
2. Rename them (e.g., MyPlayerController)
3. Add your custom features to the script
4. Update the prefab JSON to reference your new script

The SimplePlayerController is designed to be a starting point for custom player controllers!
