# Global Systems in Lupine Engine

The Lupine Engine provides two powerful global systems for managing shared state and functionality across your game: **Singletons** and **Global Variables**.

## Overview

- **Singletons**: Python scripts that are automatically loaded at game start and remain accessible throughout the game's lifetime
- **Global Variables**: Typed variables that can be accessed and modified from any script in your game

Both systems are managed through the **Global Manager** tool accessible from the Tools menu in the editor.

## Singletons

Singletons are similar to Godot's autoload system. They allow you to create persistent objects that can be accessed from anywhere in your game.

### Creating a Singleton

1. Create a Python script file in your project
2. Open **Tools > Global Manager** in the editor
3. Go to the **Singletons** tab
4. Click **Add Singleton**
5. Set the name and script path
6. Enable the singleton

### Singleton Script Structure

Your singleton script can be structured in several ways:

#### Option 1: Class with Same Name as Singleton
```python
class GameManager:
    def __init__(self):
        self.score = 0
        print("GameManager initialized!")
    
    def _singleton_init(self):
        """Called when singleton is loaded by engine"""
        print("GameManager ready!")
    
    def _singleton_cleanup(self):
        """Called when singleton is destroyed"""
        print("GameManager cleanup")
```

#### Option 2: Standard Class Names
```python
class Singleton:  # or Main, or Global
    def __init__(self):
        self.data = {}
```

#### Option 3: Module-Level Functions
```python
# The module itself becomes the singleton
score = 0

def add_score(points):
    global score
    score += points
```

### Using Singletons in Scripts

```python
from core.globals.singleton_manager import get_singleton

# Get singleton instance
game_manager = get_singleton("GameManager")

if game_manager:
    game_manager.add_score(100)
    state = game_manager.get_game_state()
```

### Singleton Lifecycle Methods

- `_singleton_init()`: Called when the singleton is first loaded
- `_singleton_cleanup()`: Called when the singleton is being destroyed

## Global Variables

Global variables provide a type-safe way to share data across your entire game.

### Supported Types

- **Int**: Integer numbers
- **Float**: Decimal numbers  
- **String**: Text values
- **Bool**: True/False values
- **Color**: RGBA color values (0.0-1.0)
- **Vector2**: 2D coordinates [x, y]
- **Vector3**: 3D coordinates [x, y, z]
- **Path**: File paths
- **Resource**: Resource file paths

### Creating Global Variables

1. Open **Tools > Global Manager** in the editor
2. Go to the **Global Variables** tab
3. Click **Add Variable**
4. Set name, type, value, and description
5. Save the variable

### Using Global Variables in Scripts

```python
from core.globals.variables_manager import get_global_var, set_global_var

# Get variable values
max_health = get_global_var("max_health")
player_speed = get_global_var("player_speed")
game_title = get_global_var("game_title")

# Set variable values
set_global_var("current_level", 5)
set_global_var("player_name", "Alice")

# Use in game logic
if get_global_var("debug_mode"):
    print("Debug mode enabled!")
```

## Project Configuration

Global systems are stored in your project's `project.json` file under the `globals` section:

```json
{
  "globals": {
    "singletons": [
      {
        "name": "GameManager",
        "script_path": "scripts/game_manager.py",
        "enabled": true
      }
    ],
    "variables": [
      {
        "name": "max_health",
        "type": "int",
        "value": 100,
        "description": "Maximum player health",
        "default_value": 100
      }
    ]
  }
}
```

## Best Practices

### Singletons

1. **Keep them focused**: Each singleton should have a specific responsibility
2. **Use descriptive names**: Names should clearly indicate the singleton's purpose
3. **Handle initialization**: Use `_singleton_init()` for setup that requires other systems
4. **Clean up resources**: Use `_singleton_cleanup()` to properly release resources
5. **Avoid circular dependencies**: Be careful about singletons depending on each other

### Global Variables

1. **Use appropriate types**: Choose the most specific type for your data
2. **Provide descriptions**: Document what each variable is used for
3. **Set sensible defaults**: Default values should be safe for your game
4. **Group related variables**: Use consistent naming for related variables
5. **Avoid overuse**: Not everything needs to be global

## Example Use Cases

### Singletons
- Game state management (score, level, lives)
- Audio management (music, sound effects)
- Save/load system
- Input handling
- Scene management
- Network communication

### Global Variables
- Game settings (difficulty, volume levels)
- Player preferences (controls, graphics settings)
- Game constants (max health, speed multipliers)
- Debug flags
- UI configuration
- Balance parameters

## Integration with Game Runtime

Both systems are automatically initialized when your game starts:

1. **Singletons** are loaded in alphabetical order by name
2. **Global Variables** are available immediately
3. Both can be accessed from any script during gameplay

The systems are thread-safe and designed for high performance with lazy loading and caching.

## Troubleshooting

### Singleton Not Found
- Check that the singleton is enabled in the Global Manager
- Verify the script path is correct and the file exists
- Ensure the script has a valid class or module structure

### Variable Not Found
- Check that the variable exists in the Global Manager
- Verify the variable name spelling
- Ensure the project has been saved after adding the variable

### Import Errors
- Make sure you're importing from the correct modules
- Check that the core.globals module is available in your project
- Verify your Python path includes the engine core modules
