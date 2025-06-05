# Scriptable Objects System Documentation

## Overview

The Scriptable Objects system provides a data-driven approach to creating and managing game objects in Lupine Engine. It consists of templates that define the structure and behavior of object types, and instances that contain specific data for individual objects.

## System Architecture

### Core Components

1. **ScriptableObjectField** (`core/scriptable_objects/field.py`)
   - Defines individual fields with types, default values, and validation
   - Supports multiple field types: string, int, float, bool, color, path, image, sprite_sheet, nodepath, vector2, vector3, array, object
   - Includes custom code snippets for field-specific behavior

2. **ScriptableObjectTemplate** (`core/scriptable_objects/template.py`)
   - Defines the structure of a scriptable object type
   - Contains multiple fields and base code
   - Generates Python code for the template
   - Supports categorization and versioning

3. **ScriptableObjectInstance** (`core/scriptable_objects/instance.py`)
   - Represents a specific instance of a template
   - Stores actual data values for each field
   - Supports cloning and validation against templates

4. **ScriptableObjectManager** (`core/scriptable_objects/manager.py`)
   - Manages all templates and instances for a project
   - Handles loading/saving to disk
   - Organizes data in project/data/templates and project/data/instances directories

### UI Components

1. **ScriptableObjectTemplateEditor** (`editor/scriptable_objects/template_editor.py`)
   - Complete UI for creating and editing templates
   - Field management with drag-and-drop reordering
   - Live code preview
   - Template duplication and deletion

2. **DatabaseManager** (`editor/scriptable_objects/database_manager.py`)
   - Tree view of all templates and instances
   - Instance creation, editing, and deletion
   - Dynamic form generation based on template fields
   - Support for all field types with appropriate widgets

## Features Implemented

### ✅ Template Management
- Create, edit, delete, and duplicate templates
- Field management with multiple data types
- Custom code snippets per field and template
- Categorization and organization
- Live Python code generation and preview

### ✅ Field Types
- **String**: Text input with validation
- **Int/Float**: Numeric input with range controls
- **Bool**: Checkbox input
- **Color**: Color picker with RGBA support
- **Path/Image/Sprite Sheet**: File browser integration
- **NodePath**: Node selection (UI ready)
- **Vector2/Vector3**: Multi-component numeric input
- **Array/Object**: JSON-based complex data (basic support)

### ✅ Instance Management
- Create instances from templates
- Edit instance data with type-appropriate widgets
- Clone and delete instances
- Automatic validation against templates
- Organized storage by template type

### ✅ Editor Integration
- Added to Tools menu in main editor
- Dockable windows that integrate with existing UI
- Consistent styling with engine theme
- Real-time updates and validation

### ✅ Data Persistence
- JSON-based storage for templates and instances
- Automatic Python code generation
- Project-relative file organization
- Backup and recovery support

## Usage Guide

### Creating Templates

1. Open **Tools > Scriptable Object Templates**
2. Click **New Template** and enter a name
3. In the **Template Info** tab:
   - Set description, category, and version
   - Add base code if needed
4. In the **Fields** tab:
   - Click **Add Field** to create new fields
   - Configure field name, type, default value, and description
   - Organize fields into groups
   - Add custom code snippets for specific fields
5. Use **Code Preview** tab to see generated Python code
6. Click **Save Template** to persist changes

### Managing Instances

1. Open **Tools > Database Manager**
2. Select a template in the tree to enable instance creation
3. Click **New Instance** to create an instance
4. Edit instance data using the generated form
5. Use **Save Instance** to persist changes
6. **Duplicate** or **Delete** instances as needed

### Field Types Guide

- **String**: Simple text input
- **Int**: Integer with spinner controls
- **Float**: Decimal number with precision controls
- **Bool**: Checkbox for true/false values
- **Color**: Color picker button with RGBA values
- **Path**: File path with browse button
- **Image**: Image file path with preview (planned)
- **Sprite Sheet**: Sprite sheet file with frame selection (planned)
- **NodePath**: Node selection from scene tree (planned)
- **Vector2**: X,Y coordinate input
- **Vector3**: X,Y,Z coordinate input
- **Array**: JSON array editor (basic)
- **Object**: JSON object editor (basic)

## Example Templates

The system includes example templates demonstrating common use cases:

1. **Item Template**: Game items with display properties, economy values, and stacking
2. **Character Template**: NPCs and players with stats, position, and behavior
3. **Quest Template**: Missions with objectives, rewards, and requirements
4. **Weapon Template**: Combat equipment with damage stats and properties

Run `python examples/scriptable_objects_demo.py` to generate example data.

## Integration with Game Engine

### Runtime Usage

Templates generate Python classes that can be used in game scripts:

```python
# Load an instance
item = load_scriptable_object("Item", "health_potion_001")

# Access properties
print(item.display_name)  # "Health Potion"
print(item.value)         # 25

# Call custom methods
display_text = item.get_display_text()
can_stack = item.can_stack_with(other_item)
```

### Scene Integration

Scriptable objects can be attached to scene nodes:

```python
# In a node script
def _ready():
    # Load character data
    self.character_data = load_scriptable_object("Character", "village_elder")
    self.health = self.character_data.health
    self.position = self.character_data.position
```

## File Organization

```
project/
├── data/
│   ├── templates/
│   │   ├── Item.json          # Template definition
│   │   ├── Item.py            # Generated Python class
│   │   ├── Character.json
│   │   ├── Character.py
│   │   └── ...
│   └── instances/
│       ├── Item/
│       │   ├── health_potion.json
│       │   ├── magic_sword.json
│       │   └── ...
│       ├── Character/
│       │   ├── village_elder.json
│       │   └── ...
│       └── ...
```

## Performance Considerations

- Templates are loaded once at startup
- Instances are loaded on-demand
- JSON parsing is cached for frequently accessed objects
- Large arrays/objects should use external file references
- Consider using binary serialization for production builds

## Best Practices

### Template Design
- Use descriptive field names and descriptions
- Group related fields together
- Provide sensible default values
- Add validation through custom code
- Keep templates focused on single responsibilities

### Instance Management
- Use consistent naming conventions
- Organize instances by logical categories
- Validate data before saving
- Use version control for template changes
- Document custom code thoroughly

### Performance
- Avoid deeply nested object structures
- Use references instead of embedding large data
- Cache frequently accessed instances
- Consider lazy loading for large datasets
- Profile memory usage with many instances

## Still To Be Implemented

### High Priority

#### 1. Runtime Loading System
- **ScriptableObjectLoader** class for loading instances at runtime
- Integration with game engine's resource system
- Caching and memory management
- Async loading for large datasets

#### 2. Enhanced Field Types
- **NodePath**: Integration with scene tree for node selection
- **Image Preview**: Thumbnail display in database manager
- **Sprite Sheet Editor**: Frame selection and animation preview
- **Audio**: Audio file selection with preview
- **Resource References**: Links to other scriptable objects

#### 3. Advanced Editor Features
- **Field Reordering**: Drag-and-drop field arrangement in template editor
- **Template Inheritance**: Base templates with derived types
- **Import/Export**: Template and instance import/export functionality
- **Search and Filter**: Find instances by field values
- **Bulk Operations**: Multi-select and batch editing

#### 4. Validation and Error Handling
- **Real-time Validation**: Live validation as user types
- **Error Reporting**: Detailed error messages with suggestions
- **Data Migration**: Handle template changes gracefully
- **Backup System**: Automatic backups before major changes

### Medium Priority

#### 5. Advanced Data Types
- **Enums**: Dropdown selection from predefined values
- **Ranges**: Min/max value pairs
- **Curves**: Animation curves and gradients
- **References**: Links to other templates/instances
- **Collections**: Typed arrays with specific element types

#### 6. Code Generation Improvements
- **Custom Base Classes**: User-defined base classes for templates
- **Method Templates**: Predefined method patterns
- **Code Validation**: Syntax checking for custom code
- **Documentation Generation**: Auto-generated API docs

#### 7. Database Features
- **Query System**: SQL-like queries for finding instances
- **Relationships**: Foreign key relationships between objects
- **Indexing**: Performance optimization for large datasets
- **Transactions**: Atomic operations for data consistency

#### 8. Integration Features
- **Scene Binding**: Direct attachment to scene nodes
- **Asset Pipeline**: Integration with asset import system
- **Version Control**: Git-friendly serialization
- **Collaboration**: Multi-user editing support

### Low Priority

#### 9. Advanced UI Features
- **Custom Widgets**: User-defined field editors
- **Themes**: Customizable UI appearance
- **Layouts**: Flexible form layouts
- **Scripting**: Lua/Python scripting for custom behavior

#### 10. Export and Deployment
- **Binary Serialization**: Compact runtime format
- **Compression**: Reduced file sizes
- **Encryption**: Secure data storage
- **Platform Optimization**: Platform-specific optimizations

#### 11. Developer Tools
- **Profiler**: Performance analysis tools
- **Debugger**: Runtime debugging support
- **Analytics**: Usage statistics and optimization hints
- **Documentation**: Interactive help system

## Known Issues and Limitations

### Current Limitations
1. **Array/Object editing** is basic JSON text editing
2. **No undo/redo** system in editors
3. **Limited validation** for complex field types
4. **No template versioning** or migration system
5. **Basic error handling** in UI components

### Planned Fixes
1. **Rich editors** for complex data types
2. **Command pattern** for undo/redo functionality
3. **Comprehensive validation** framework
4. **Version management** system
5. **Robust error handling** with user-friendly messages

## Testing and Quality Assurance

### Automated Tests Needed
- Unit tests for core classes
- Integration tests for manager operations
- UI tests for editor components
- Performance tests for large datasets
- Validation tests for all field types

### Manual Testing Checklist
- [ ] Create and edit templates
- [ ] Add all field types
- [ ] Create and edit instances
- [ ] Save and load data
- [ ] Test error conditions
- [ ] Verify code generation
- [ ] Check UI responsiveness
- [ ] Test with large datasets

## Contributing

### Code Style
- Follow existing Python conventions
- Use type hints for all public methods
- Document all classes and methods
- Write unit tests for new features
- Follow Qt naming conventions for UI

### Adding New Field Types
1. Add enum value to `FieldType`
2. Implement validation in `ScriptableObjectField`
3. Add widget creation in `InstanceEditorWidget`
4. Update template editor field widget
5. Add tests and documentation

### Extending the System
- New field types should inherit from base patterns
- UI components should follow existing design
- Data formats should be backward compatible
- Performance should be considered for all changes
- Documentation should be updated with changes
