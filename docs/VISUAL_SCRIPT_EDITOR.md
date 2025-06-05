# Enhanced Visual Script Editor

The Enhanced Visual Script Editor is a Blueprint-style visual scripting system for Lupine Engine that allows users to create scripts using a node-based interface similar to Unreal Engine's Blueprints.

## Features

### Core Functionality
- **Blueprint-style Interface**: Drag-and-drop visual scripting with nodes and connections
- **Dual Mode**: Switch between visual editor and generated Python code
- **Real-time Code Generation**: See Python code generated from your visual script
- **Type-safe Connections**: Color-coded pins with type validation
- **Execution Flow**: White execution pins for control flow, colored pins for data

### Block Types
- **Flow Control**: If statements, loops, while loops
- **Actions**: Print, scene changes, sound playback, dialogue
- **Conditions**: Number comparisons, variable checks, item checks
- **Variables**: Get/set variables, mathematical operations
- **Events**: Start events, timers, input handling

### Advanced Features
- **Connection Validation**: Prevents incompatible type connections
- **Visual Feedback**: Temporary connections while connecting pins
- **Block Library**: Categorized blocks with search functionality
- **Properties Panel**: Detailed information about selected blocks
- **Save/Load**: Save visual scripts as .vscript files
- **Export**: Generate standalone Python files

## Getting Started

### Opening the Editor
1. Launch Lupine Engine Editor
2. Go to **Tools > Visual Script Editor**
3. The Enhanced Visual Script Editor will open in a new window

### Basic Workflow
1. **Add Blocks**: Drag blocks from the Block Library to the canvas
2. **Connect Blocks**: Click on output pins and drag to input pins
3. **Configure Properties**: Select blocks to view/edit properties
4. **Generate Code**: Switch to "Generated Code" tab to see Python output
5. **Save Script**: Use File > Save to save your visual script
6. **Export**: Use File > Export to Python to create a .py file

## Block Library

### Flow Control
- **Start**: Entry point for script execution
- **If (Exec)**: Conditional execution with true/false branches
- **For Loop**: Loop for a specified number of iterations
- **While Loop**: Loop while condition is true

### Actions
- **Print (Exec)**: Print messages with execution flow
- **Change Scene**: Navigate to different scenes
- **Play Sound**: Play audio files
- **Show Dialogue**: Display dialogue text
- **Move Node**: Animate node movement

### Conditions
- **Compare Numbers**: Mathematical comparisons (==, !=, <, >, <=, >=)
- **Check Variable**: Verify variable existence and values
- **Has Item**: Check player inventory

### Variables
- **Set Variable**: Store values in variables
- **Get Variable**: Retrieve variable values
- **Add to Variable**: Increment numeric variables

### Events
- **Emit Signal**: Send signals to other systems
- **On Timer**: Execute code on timer intervals
- **On Input**: Respond to player input

## Pin Types and Colors

### Execution Pins (White)
- Control the flow of execution
- Connect output execution pins to input execution pins
- Only one connection per input execution pin

### Data Pins (Colored)
- **String** (Pink): Text values
- **Number** (Green): Numeric values
- **Boolean** (Red): True/false values
- **Node** (Blue): Game object references
- **Scene** (Purple): Scene references
- **Variable** (Yellow): Variable references
- **Any** (Gray): Accepts any type

## Code Generation

The visual script editor generates clean, readable Python code:

```python
class GeneratedScript:
    """Generated script class from visual blocks"""
    
    def __init__(self, node):
        self.node = node
        self._setup_variables()
    
    def _setup_variables(self):
        """Setup variables from data blocks"""
        # Variable initialization here
    
    def execute(self):
        """Execute the visual script logic"""
        # Generated execution flow here
```

## File Formats

### Visual Script Files (.vscript)
JSON format containing:
- Block definitions and positions
- Connection information
- Block properties and values

### Generated Python Files (.py)
Standard Python files that can be:
- Used as node scripts in Lupine Engine
- Modified manually if needed
- Integrated with existing code

## Best Practices

### Organization
- Use meaningful block names
- Group related functionality
- Keep execution chains readable
- Use comments (block descriptions)

### Performance
- Avoid circular references
- Minimize complex nested conditions
- Use appropriate data types
- Cache frequently accessed values

### Debugging
- Use Print blocks for debugging
- Check the Generated Code tab for issues
- Validate all connections before running
- Test with simple scripts first

## Integration with Lupine Engine

### Node Scripts
Visual scripts can be attached to nodes:
1. Generate Python code from visual script
2. Save as .py file in scripts directory
3. Attach to node using Script Dialog
4. Script will execute with node lifecycle

### Project Integration
- Scripts saved in project's scripts directory
- Automatic discovery by script system
- Integration with build system
- Support for multiple scripts per node

## Extending the System

### Custom Blocks
Create custom blocks by:
1. Defining VisualScriptBlock instances
2. Adding to builtin_script_blocks.py
3. Implementing code templates
4. Registering with block library

### New Pin Types
Add new data types by:
1. Updating type color mappings
2. Adding validation logic
3. Implementing code generation
4. Testing compatibility

## Troubleshooting

### Common Issues
- **Blocks not connecting**: Check pin type compatibility
- **Code not generating**: Verify all required inputs are connected
- **Script not running**: Check for syntax errors in generated code
- **Performance issues**: Reduce number of blocks or simplify logic

### Error Messages
- **"Circular reference detected"**: Remove loops in execution flow
- **"Type mismatch"**: Connect compatible pin types
- **"Missing input"**: Connect all required input pins
- **"Invalid template"**: Check block code template syntax

## Future Enhancements

### Planned Features
- Custom user-defined blocks
- Visual debugging with breakpoints
- Animation timeline integration
- Advanced data structures (arrays, objects)
- Function definitions and calls
- Class inheritance support
- Live preview in game runner

### Community Contributions
- Block library extensions
- Template improvements
- UI/UX enhancements
- Documentation updates
- Bug fixes and optimizations

## Support

For help with the Visual Script Editor:
1. Check this documentation
2. Review example scripts
3. Test with simple blocks first
4. Report issues on GitHub
5. Join the community forums
