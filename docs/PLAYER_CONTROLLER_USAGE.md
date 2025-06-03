# PlayerController Usage Guide

The PlayerController is a comprehensive, fully-featured player controller for the Lupine Engine that supports multiple movement modes and advanced features.

## Features

### 🎮 Movement Modes
- **8-Directional Top-down**: Full 8-directional movement with diagonal normalization
- **4-Directional Top-down**: Cardinal directions only (up, down, left, right)
- **Sidescroller**: Horizontal movement with gravity and jumping
- **Platformer**: Full 2D movement with gravity, jumping, and advanced platformer mechanics

### ⚡ Advanced Features
- **Sprint System**: Configurable sprint speed with optional stamina consumption
- **Jump Mechanics**: Coyote time, jump buffering, and variable jump height
- **Interaction System**: Automatic detection and interaction with nearby objects
- **Physics Integration**: Full collision detection with KinematicBody2D
- **Animation Support**: Movement state tracking for animation integration
- **Debug Mode**: Visual debugging tools for development

## Quick Start

### 1. Adding to Your Scene

**Option A: Use the Prefab**
```json
// Load the prefab in your scene
{
  "name": "Player",
  "type": "KinematicBody2D",
  "script": "nodes/prefabs/PlayerController.lsc",
  // ... prefab configuration
}
```

**Option B: Manual Setup**
1. Create a KinematicBody2D node
2. Attach the `nodes/prefabs/PlayerController.lsc` script
3. Add a CollisionShape2D child node
4. Add a Sprite2D child node for visuals

### 2. Basic Configuration

```lsc
# Set movement mode
player.set_controller_type("topdown_8dir")  # or "topdown_4dir", "sidescroller", "platformer"

# Configure movement
player.base_speed = 200.0
player.acceleration = 800.0
player.friction = 1000.0

# Enable sprint with stamina
player.can_sprint = true
player.sprint_stamina_enabled = true
player.max_stamina = 100.0
```

## Movement Modes

### Top-down 8-Directional
```lsc
player.set_controller_type("topdown_8dir")
```
- Full 8-directional movement
- Diagonal movement is normalized
- No gravity
- Perfect for RPGs, twin-stick shooters

### Top-down 4-Directional
```lsc
player.set_controller_type("topdown_4dir")
```
- Cardinal directions only
- Classic retro game feel
- No diagonal movement
- Perfect for grid-based games

### Sidescroller
```lsc
player.set_controller_type("sidescroller")
```
- Horizontal movement only
- Gravity and jumping
- Classic side-scrolling platformer feel
- Perfect for Mario-style games

### Platformer
```lsc
player.set_controller_type("platformer")
```
- Full 2D movement with gravity
- Advanced jump mechanics
- Coyote time and jump buffering
- Perfect for modern platformers

## Input Controls

The PlayerController uses the engine's input action system:

- **Movement**: `move_left`, `move_right`, `move_up`, `move_down`
- **Sprint**: `run` (Shift key)
- **Jump**: `jump` (Space key) - Platformer modes only
- **Interact**: `interact` (E key)

## Configuration Options

### Movement Settings
```lsc
export var base_speed: float = 200.0          # Base movement speed
export var acceleration: float = 800.0        # Acceleration rate
export var friction: float = 1000.0           # Deceleration rate
export var max_speed: float = 400.0           # Maximum speed
```

### Sprint System
```lsc
export var can_sprint: bool = true                    # Enable sprinting
export var sprint_speed_multiplier: float = 1.8      # Sprint speed boost
export var sprint_stamina_enabled: bool = false      # Enable stamina system
export var max_stamina: float = 100.0                # Maximum stamina
export var stamina_drain_rate: float = 20.0          # Stamina drain per second
export var stamina_regen_rate: float = 15.0          # Stamina regen per second
```

### Platformer Physics
```lsc
export var gravity: float = 980.0             # Gravity force
export var jump_height: float = 400.0         # Jump velocity
export var max_fall_speed: float = 1000.0     # Terminal velocity
export var coyote_time: float = 0.1           # Jump grace period
export var jump_buffer_time: float = 0.1      # Jump input buffering
```

## Signals

Connect to these signals for UI and game logic integration:

```lsc
# Movement state changes
player.connect("movement_state_changed", self, "_on_movement_state_changed")

# Stamina updates
player.connect("stamina_changed", self, "_on_stamina_changed")

# Interaction system
player.connect("interaction_available", self, "_on_interaction_available")
player.connect("interaction_unavailable", self, "_on_interaction_unavailable")

# Platformer events
player.connect("jumped", self, "_on_player_jumped")
player.connect("landed", self, "_on_player_landed")
```

## Public API

### Movement Control
```lsc
player.set_controller_type("platformer")      # Change movement mode
player.get_movement_state()                   # Get current state: "idle", "walking", "running", "jumping", "falling"
player.get_velocity()                         # Get current velocity
player.is_moving()                            # Check if player is moving
```

### Stamina Management
```lsc
player.get_stamina_percentage()               # Get stamina as 0.0-1.0
player.set_stamina(50.0)                      # Set stamina amount
player.add_stamina(25.0)                      # Add stamina
```

### Interaction System
```lsc
player.can_interact()                         # Check if interaction available
player.get_interaction_text()                 # Get interaction prompt text
```

### Debug Tools
```lsc
player.debug_mode = true                      # Enable visual debugging
player.print_debug_info()                     # Print debug information
```

## Creating Interactable Objects

To make objects interactable with the PlayerController:

```lsc
# In your interactable object script
extends StaticBody2D

func interact(player):
    print("Player interacted with ", name)
    # Your interaction logic here

func get_interaction_text() -> String:
    return "Press E to interact"
```

Set the object's collision_layer to 8 (interaction layer).

## Example Usage

```lsc
# In your scene script
func _ready():
    var player = get_node("PlayerController")
    
    # Configure for top-down RPG
    player.set_controller_type("topdown_8dir")
    player.can_sprint = true
    player.sprint_stamina_enabled = true
    
    # Connect signals
    player.connect("stamina_changed", self, "_update_stamina_bar")
    player.connect("interaction_available", self, "_show_interaction_prompt")
    player.connect("interaction_unavailable", self, "_hide_interaction_prompt")

func _update_stamina_bar(current, maximum):
    stamina_bar.value = current / maximum

func _show_interaction_prompt(interactable):
    interaction_label.text = interactable.get_interaction_text()
    interaction_label.visible = true

func _hide_interaction_prompt():
    interaction_label.visible = false
```

## Demo Scene

Run `scenes/PlayerControllerDemo.json` to see the PlayerController in action with collision walls and debug visualization enabled.

## Tips

1. **Use debug mode** during development to visualize movement vectors
2. **Adjust physics values** based on your game's feel requirements
3. **Connect to signals** for responsive UI updates
4. **Test different movement modes** to find the best fit for your game
5. **Use the interaction system** for NPCs, chests, doors, etc.

The PlayerController is designed to be flexible and extensible - modify the script as needed for your specific game requirements!
