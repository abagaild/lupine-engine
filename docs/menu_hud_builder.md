# Menu and HUD Builder

The Menu and HUD Builder is a comprehensive tool for creating user interfaces in Lupine Engine. It provides a drag-and-drop interface for building menus, HUDs, and other UI layouts with advanced features like variable bindings and event handling.

## Features

### 🎨 **Drag-and-Drop Interface**
- **Prefab Library**: Categorized collection of UI prefabs
- **Visual Preview**: Real-time preview with camera bounds
- **Grid Snapping**: Precise positioning with grid alignment
- **Multi-Resolution Support**: Test layouts at different resolutions

### 🔗 **Variable Binding System**
- **Display Bindings**: Show global variable values in UI elements
- **Visibility Bindings**: Show/hide elements based on conditions
- **Enable Bindings**: Enable/disable elements dynamically
- **Progress Bindings**: Update progress bars from variables
- **Color Bindings**: Change colors based on variable values

### ⚡ **Event System**
- **Visual Event Configuration**: Configure events through UI
- **Code Snippet Generation**: Auto-generate Python scripts
- **Audio Integration**: Attach sound effects to events
- **Template System**: Quick setup with common event patterns

## Getting Started

### Opening the Tool
1. Open Lupine Engine Editor
2. Go to **Tools** → **Menu and HUD Builder**
3. The tool opens as a dockable window

### Interface Layout

#### Left Panel: Prefab Library
- **Categories**: Buttons, Displays, Progress Bars, Containers, etc.
- **Search**: Filter prefabs by name or description
- **Drag-and-Drop**: Drag prefabs to the preview area

#### Center Panel: Preview
- **Camera Bounds**: Shows the game's viewport area
- **Grid**: Optional grid for precise positioning
- **Resolution Selector**: Test different screen sizes
- **Drop Zone**: Drop prefabs here to add them to the layout

#### Right Panel: Inspector
- **Properties Tab**: Standard node properties
- **Variables Tab**: Configure variable bindings
- **Events Tab**: Set up event handlers and code snippets

## Built-in Prefabs

### Buttons
- **SimpleButton**: Basic button with text and click handling
- **MenuButton**: Styled menu button with hover effects
- **InventorySlot**: Inventory slot for items with drag support

### Displays
- **HealthDisplay**: Health display with icon and text
- **ScoreDisplay**: Score display with formatting
- **DialogueBox**: Dialogue box with speaker and text

### Progress Bars
- **HealthBar**: Health progress bar with color transitions
- **ExperienceBar**: XP progress bar with text display

### Containers
- **Panel**: Basic container with background styling

## Variable Binding

### Setting Up Bindings
1. Select a UI element in the preview
2. Go to the **Variables** tab
3. Click **Add** to create a new binding
4. Configure the binding type and variable

### Binding Types

#### Display Binding
Shows variable values as text:
```python
# Example: Show player health
Variable: player_health
Format: "Health: {value}"
Result: "Health: 85"
```

#### Visibility Binding
Show/hide elements based on conditions:
```python
# Example: Show element only when health > 0
Variable: player_health
Condition: "{value} > 0"
```

#### Progress Binding
Update progress bars from variables:
```python
# Example: Health bar
Variable: player_health
Max Variable: player_max_health
```

### Testing Bindings
Use the test section to preview bindings:
1. Select a variable name
2. Enter a test value
3. Click **Test** to see the result

## Event Handling

### Adding Events
1. Select a UI element
2. Go to the **Events** tab
3. Click **Add** or use quick action buttons
4. Configure the event in the dialog

### Event Types
- **on_click**: When element is clicked
- **on_hover**: When mouse hovers over element
- **on_release**: When mouse button is released
- **on_focus**: When element gains focus
- **on_value_changed**: When value changes (progress bars)

### Code Snippets
Write Python code that executes when events occur:

```python
# Example: Button click handler
print(f'{self.name} was clicked!')
set_global_var('button_clicks', get_global_var('button_clicks') + 1)
```

### Audio Integration
Attach sound effects to events:
1. In the event dialog, go to the **Audio** tab
2. Browse for an audio file
3. The sound will play when the event occurs

### Code Templates
Use built-in templates for common actions:
- **Print Message**: Simple debug output
- **Change Scene**: Navigate to different scenes
- **Play Sound**: Play audio effects
- **Update Variable**: Modify global variables
- **Show/Hide Element**: Control element visibility
- **Enable/Disable Element**: Control element interaction

## Advanced Features

### Script Generation
Generate complete Python scripts from event bindings:
1. Configure events for a UI element
2. Click **Generate Script File**
3. Review and save the generated script

### Custom Prefabs
Create your own prefabs by:
1. Building a UI layout
2. Saving it as a scene file
3. Adding it to the prefabs directory

### Multi-Resolution Testing
Test your UI at different resolutions:
1. Use the resolution dropdown in the preview
2. Common resolutions: 1920x1080, 1280x720, 1024x768
3. Ensure UI scales properly

## Best Practices

### Layout Design
- **Anchor Points**: Use proper anchoring for responsive design
- **Consistent Spacing**: Maintain consistent margins and padding
- **Visual Hierarchy**: Use size and color to guide user attention

### Variable Bindings
- **Meaningful Names**: Use descriptive variable names
- **Error Handling**: Test with edge cases (null, negative values)
- **Performance**: Avoid excessive bindings on frequently updated variables

### Event Handling
- **Keep It Simple**: Write concise, focused event handlers
- **Error Handling**: Include try-catch blocks for robust code
- **Audio Feedback**: Provide audio feedback for user interactions

### Testing
- **Multiple Resolutions**: Test on different screen sizes
- **Variable Ranges**: Test with min/max variable values
- **Edge Cases**: Test with empty or null variables

## Integration with Game

### Saving Layouts
Save your HUD layouts as scene files that can be loaded in your game:
1. Click **Save HUD** in the builder
2. Choose a location in your project
3. Load the scene in your game code

### Global Variables
Ensure your game sets up the global variables used in bindings:
```python
# In your game initialization
set_global_var('player_health', 100)
set_global_var('player_max_health', 100)
set_global_var('player_score', 0)
```

### Event Integration
The generated event code integrates with your game's event system automatically.

## Troubleshooting

### Common Issues
- **Prefab not appearing**: Check if it's within camera bounds
- **Binding not working**: Verify variable name matches exactly
- **Event not firing**: Ensure event is enabled and element is interactive

### Performance Tips
- **Limit Bindings**: Don't bind every property to variables
- **Optimize Updates**: Use appropriate update frequencies
- **Test Early**: Test performance with realistic data

## Future Enhancements

Planned features for future versions:
- **Animation System**: Tween animations for UI elements
- **Theme System**: Consistent styling across UI elements
- **Layout Containers**: Automatic layout management
- **Responsive Design**: Advanced responsive layout tools
- **Component System**: Reusable UI components
