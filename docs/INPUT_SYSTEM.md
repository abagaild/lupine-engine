# Lupine Engine Input System

The Lupine Engine features a comprehensive input system similar to Godot's, with support for input actions, key mapping, and both keyboard and mouse input.

## Features

- **Action-based input system** - Map multiple keys to named actions
- **Godot-like input constants** - Familiar key and mouse button constants
- **Input mapping dialog** - Visual configuration of input actions
- **"Just pressed/released" detection** - Frame-perfect input detection
- **Mouse input support** - Full mouse button and position tracking
- **Modifier key support** - Shift, Ctrl, Alt, Meta key combinations
- **Project-specific input maps** - Save/load input configurations per project

## Input Actions

### Default Actions

The engine comes with these pre-configured actions:

**UI Actions:**
- `ui_accept` - Enter, Space, Numpad Enter
- `ui_cancel` - Escape
- `ui_left` - Left Arrow, A
- `ui_right` - Right Arrow, D
- `ui_up` - Up Arrow, W
- `ui_down` - Down Arrow, S

**Movement Actions:**
- `move_left` - Left Arrow, A
- `move_right` - Right Arrow, D
- `move_up` - Up Arrow, W
- `move_down` - Down Arrow, S

**Game Actions:**
- `jump` - Space
- `interact` - E, Enter
- `run` - Shift
- `pause` - Escape, P

### Using Actions in LSC Scripts

```lsc
# Check if action is currently pressed
if is_action_pressed("move_left"):
    position.x -= speed * delta

# Check if action was just pressed this frame
if is_action_just_pressed("jump"):
    velocity.y = jump_force

# Check if action was just released this frame
if is_action_just_released("interact"):
    stop_interaction()

# Get action strength (0.0 to 1.0, useful for analog inputs)
var run_strength = get_action_strength("run")
```

## Input Constants

### Key Constants

```lsc
# Letter keys
KEY_A, KEY_B, KEY_C, ..., KEY_Z

# Number keys
KEY_0, KEY_1, KEY_2, ..., KEY_9

# Arrow keys
KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN

# Modifier keys
KEY_SHIFT, KEY_CTRL, KEY_ALT, KEY_META

# Special keys
KEY_SPACE, KEY_ENTER, KEY_ESCAPE, KEY_TAB, KEY_BACKSPACE

# Function keys
KEY_F1, KEY_F2, ..., KEY_F12
```

### Mouse Button Constants

```lsc
MOUSE_BUTTON_LEFT      # Left mouse button
MOUSE_BUTTON_RIGHT     # Right mouse button
MOUSE_BUTTON_MIDDLE    # Middle mouse button (wheel click)
MOUSE_BUTTON_WHEEL_UP  # Mouse wheel up
MOUSE_BUTTON_WHEEL_DOWN # Mouse wheel down
```

### Using Raw Key Input

```lsc
# Check if specific key is pressed
if is_key_pressed(KEY_W):
    move_forward()

# Check if mouse button is pressed
if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
    fire_weapon()

# Get mouse position
var mouse_pos = get_mouse_position()
```

## Input Events in Scripts

Your LSC scripts can handle input events directly:

```lsc
# Called when any key is pressed
func on_key_press(key: int, modifiers: int):
    if key == KEY_SPACE:
        print("Space pressed!")

# Called when any key is released
func on_key_release(key: int, modifiers: int):
    if key == KEY_ESCAPE:
        pause_game()

# Called when mouse button is pressed
func on_mouse_press(button: int, position: Vector2):
    if button == MOUSE_BUTTON_LEFT:
        handle_click(position)
```

## Configuring Input Actions

### Using the Input Actions Dialog

1. Open the editor
2. Go to **Tools > Input Actions**
3. Add, remove, or modify actions
4. Assign multiple keys to each action
5. Save your configuration

### Input Map File

Input actions are saved to `input_map.json` in your project directory:

```json
{
  "move_left": {
    "name": "move_left",
    "events": [
      {
        "type": "key",
        "code": 65361,
        "modifiers": []
      },
      {
        "type": "key", 
        "code": 97,
        "modifiers": []
      }
    ],
    "deadzone": 0.2
  }
}
```

## Advanced Usage

### Custom Input Combinations

```lsc
# Check for modifier key combinations
if is_key_pressed(KEY_CTRL) and is_action_just_pressed("ui_accept"):
    # Ctrl+Enter combination
    execute_command()

# Check for Shift+Click
if is_key_pressed(KEY_SHIFT) and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
    multi_select()
```

### Mouse Position Tracking

```lsc
func _process(delta):
    var mouse_pos = get_mouse_position()
    var global_mouse_pos = get_global_mouse_position()
    
    # Update cursor or UI elements
    cursor.position = mouse_pos
```

## PlayerController Integration

The PlayerController prefab has been updated to use the action system:

```lsc
# Movement is now action-based
if is_action_pressed("move_left"):
    input_vector.x -= 1

# Interaction uses actions
if is_action_just_pressed("interact"):
    _handle_interaction()

# Jump for platformer mode
if is_action_just_pressed("jump"):
    _handle_jump()
```

## Best Practices

1. **Use actions instead of raw keys** - More flexible and user-configurable
2. **Use "just pressed" for one-time events** - Like jumping or menu navigation
3. **Use "pressed" for continuous actions** - Like movement or firing
4. **Provide default key bindings** - But allow users to customize them
5. **Test with different input devices** - Keyboard, mouse, gamepad support coming soon

## Migration from Old System

If you have existing scripts using the old input system:

**Old:**
```lsc
if get_global_input("w"):
    move_up()
```

**New:**
```lsc
if is_action_pressed("move_up"):
    move_up()
```

The new system is more powerful and user-friendly!
