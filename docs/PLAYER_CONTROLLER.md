# PlayerController Prefab

The PlayerController is a comprehensive, feature-rich player controller prefab for the Lupine Engine that handles input, collision, interaction, and sprint mechanics using proper LSC syntax.

## Features

### 🎮 Input Handling
- **Movement**: WASD/Arrow keys for movement
- **Sprint**: Shift key for sprinting with speed multiplier
- **Jump**: Space key for platformer mode
- **Interact**: E key for interacting with objects
- **Action-based**: Uses Lupine Engine's input action system

### 🏃 Movement Modes
- **Top-down 4-direction**: Cardinal directions only
- **Top-down 8-direction**: Full 8-directional movement with diagonal normalization
- **Platformer**: Gravity-based movement with jumping
- **Side-scroller**: Horizontal movement with gravity

### ⚡ Sprint System
- **Speed Multiplier**: Configurable sprint speed boost
- **Stamina System**: Optional stamina consumption while sprinting
- **Acceleration Boost**: Faster acceleration when sprinting

### 🤝 Interaction System
- **Area2D Detection**: Automatic detection of nearby interactable objects
- **Smart Selection**: Automatically selects closest interactable
- **Signal-based**: Emits signals for UI integration
- **Extensible**: Easy to add new interactable object types

### 🎯 Collision Detection
- **KinematicBody2D**: Physics-based collision with move_and_slide
- **Configurable Layers**: Separate collision layers for player and interactions
- **Safe Movement**: Built-in collision margin for smooth movement

## Usage

### Adding to Scene

1. **From Prefab**: Load `prefabs/PlayerController.json` in your scene
2. **Manual Setup**: Create a KinematicBody2D and attach `prefabs/PlayerController.lsc`

### Configuration

The PlayerController uses export variables organized in groups:

#### Controller Settings
```lsc
export var controller_type: String = "topdown_8dir"  # Movement mode
export var enable_animations: bool = true  # Animation integration
```

#### Movement
```lsc
export var base_speed: float = 200.0  # Base movement speed
export var acceleration: float = 800.0  # Acceleration rate
export var friction: float = 1000.0  # Deceleration rate
export var max_speed: float = 400.0  # Maximum speed
```

#### Sprint
```lsc
export var can_sprint: bool = true  # Enable sprinting
export var sprint_speed_multiplier: float = 1.8  # Sprint speed boost
export var sprint_stamina_enabled: bool = false  # Enable stamina system
export var max_stamina: float = 100.0  # Maximum stamina
```

#### Platformer
```lsc
export var jump_height: float = 300.0  # Jump velocity
export var gravity: float = 980.0  # Gravity force
export var coyote_time: float = 0.1  # Jump grace period
```

### Node Structure

The PlayerController prefab includes:

```
PlayerController (KinematicBody2D)
├── Sprite (Sprite) - Visual representation
├── AnimatedSprite (AnimatedSprite) - Animation support
├── CollisionShape2D - Player collision
└── InteractionArea (Area2D)
    └── InteractionShape (CollisionShape2D) - Interaction detection
```

### Creating Interactable Objects

Interactable objects must implement:

```lsc
extends StaticBody2D  # Or any physics body

# Required method
func can_interact() -> bool:
    return true  # Return whether this object can be interacted with

# Required method
func interact(player):
    print("Player interacted with ", name)
    # Handle interaction logic here

# Optional: Get interaction prompt text
func get_interaction_text() -> String:
    return "Press E to interact"
```

Set the object's collision_layer to 8 (interaction layer) so the PlayerController can detect it.

## Signals

The PlayerController emits several signals for UI and game logic integration:

```lsc
signal stamina_changed(new_stamina, max_stamina)  # Stamina updates
signal interaction_available(interactable)  # When near interactable
signal interaction_unavailable()  # When leaving interactable
signal movement_state_changed(state)  # Movement state changes
```

## Public Methods

### Movement Control
```lsc
set_controller_type(new_type: String)  # Change movement mode
add_speed_modifier(modifier: float, duration: float)  # Temporary speed boost
```

### State Queries
```lsc
get_movement_state() -> String  # "idle", "walking", "running", "jumping", "falling"
get_facing_direction() -> Vector2  # Direction player is facing
is_moving() -> bool  # Whether player is moving
```

### Interaction
```lsc
can_interact() -> bool  # Whether player can interact
get_current_interactable()  # Get current interactable object
```

### Stamina
```lsc
get_stamina_percentage() -> float  # Stamina as 0.0-1.0
set_stamina(new_stamina: float)  # Set stamina value
restore_stamina()  # Fully restore stamina
```

### Debug
```lsc
get_debug_info() -> Dictionary  # Get debug information
```

## Example Usage

### Basic Setup
```lsc
# In your scene script
func _ready():
    var player = get_node("Player")
    
    # Connect to player signals
    player.connect("interaction_available", self, "_on_interaction_available")
    player.connect("stamina_changed", self, "_on_stamina_changed")
    
    # Configure player
    player.set_controller_type("topdown_8dir")
    player.can_sprint = true
    player.sprint_stamina_enabled = true

func _on_interaction_available(interactable):
    # Show interaction UI
    ui_prompt.text = interactable.get_interaction_text()
    ui_prompt.visible = true

func _on_stamina_changed(current, maximum):
    # Update stamina bar
    stamina_bar.value = current / maximum
```

### Creating Custom Interactables
```lsc
# Custom door script
extends StaticBody2D

export var is_locked: bool = false
export var key_required: String = "red_key"

func can_interact() -> bool:
    return true

func interact(player):
    if is_locked:
        if player.has_item(key_required):
            is_locked = false
            print("Door unlocked!")
        else:
            print("Door is locked. Need ", key_required)
    else:
        print("Door opened!")
        # Open door logic here

func get_interaction_text() -> String:
    return "Press E to open door" if not is_locked else "Press E (locked)"
```

## Demo Scene

Run `examples/player_controller_demo.json` to see the PlayerController in action with:
- Movement and sprint mechanics
- Collision with walls and platforms
- Interaction with chest and NPC
- Camera following

## Input Actions

The PlayerController uses these input actions (defined in the engine):
- `move_left`, `move_right`, `move_up`, `move_down` - Movement
- `run` - Sprint
- `jump` - Jump (platformer mode)
- `interact` - Interact with objects

## Tips

1. **Performance**: Disable `enable_animations` if not using animated sprites
2. **Stamina**: Enable `sprint_stamina_enabled` for more strategic gameplay
3. **Collision Layers**: Use layer 2 for player, layer 1 for environment, layer 8 for interactables
4. **Controller Types**: Switch between types at runtime for different gameplay sections
5. **Interaction Range**: Adjust InteractionArea CollisionShape2D radius to change interaction distance
