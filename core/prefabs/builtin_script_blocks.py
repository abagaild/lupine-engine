"""
Builtin Visual Script Blocks for Lupine Engine
Provides common script blocks for visual scripting
"""

import uuid
from .prefab_system import VisualScriptBlock, VisualScriptBlockType, VisualScriptInput, VisualScriptOutput


def create_builtin_script_blocks():
    """Create all builtin script blocks"""
    blocks = []

    # Flow Control
    blocks.extend(create_flow_control_blocks())

    # Actions
    blocks.extend(create_action_blocks())

    # Conditions
    blocks.extend(create_condition_blocks())

    # Variables
    blocks.extend(create_variable_blocks())

    # Events
    blocks.extend(create_event_blocks())

    # Enhanced blocks with execution pins
    blocks.extend(create_enhanced_blocks())

    # Component blocks for data input
    blocks.extend(create_component_blocks())

    # Math and logic blocks
    blocks.extend(create_math_blocks())

    return blocks


def create_enhanced_blocks():
    """Create enhanced blocks with proper execution pins"""
    blocks = []

    # Start Event
    start_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Start",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Entry point for script execution",
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template="# Script starts here",
        color="#7ED321"
    )
    blocks.append(start_block)

    # Enhanced Print with execution
    print_exec_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Print (Exec)",
        category="Actions",
        block_type=VisualScriptBlockType.ACTION,
        description="Print a message with execution flow",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("message", "string", "Hello World!", "Message to print")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template="""print({message})""",
        color="#4ECDC4"
    )
    blocks.append(print_exec_block)

    # Enhanced If with execution
    if_exec_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="If (Exec)",
        category="Flow Control",
        block_type=VisualScriptBlockType.FLOW,
        description="Conditional execution with execution flow",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("condition", "boolean", True, "Condition to check")
        ],
        outputs=[
            VisualScriptOutput("true", "exec", "Execute if true", is_execution_pin=True),
            VisualScriptOutput("false", "exec", "Execute if false", is_execution_pin=True)
        ],
        code_template="""if {condition}:
    # True branch
else:
    # False branch""",
        color="#F5A623"
    )
    blocks.append(if_exec_block)

    # Custom Python Code block
    custom_code_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Custom Python",
        category="Events",
        block_type=VisualScriptBlockType.CUSTOM,
        description="Execute custom Python code",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("code", "string", "# Custom Python code here\npass", "Python code to execute")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("result", "any", "Code execution result")
        ],
        code_template='{code}',
        color="#FF6B6B"
    )
    blocks.append(custom_code_block)

    # Event Handler Blocks

    # Ready Event
    ready_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Ready",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Called when node enters the scene tree",
        inputs=[],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template='# Node ready',
        color="#4CAF50"
    )
    blocks.append(ready_block)

    # Process Event
    process_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Process",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Called every frame",
        inputs=[],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("delta", "number", "Frame delta time")
        ],
        code_template='# Process frame',
        color="#4CAF50"
    )
    blocks.append(process_block)

    # Physics Process Event
    physics_process_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Physics Process",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Called every physics frame",
        inputs=[],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("delta", "number", "Physics delta time")
        ],
        code_template='# Physics process',
        color="#4CAF50"
    )
    blocks.append(physics_process_block)

    # Input Event
    input_event_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Input Event",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Handle input events",
        inputs=[
            VisualScriptInput("key", "string", "space", "Key to listen for (space, enter, escape, etc.)")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("pressed", "boolean", "True if key was pressed"),
            VisualScriptOutput("released", "boolean", "True if key was released")
        ],
        code_template='if is_action_just_pressed("{key}"): pass',
        color="#FF9800"
    )
    blocks.append(input_event_block)

    # Mouse Click Event
    click_event_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="On Click",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Handle mouse click events",
        inputs=[
            VisualScriptInput("button", "string", "left", "Mouse button (left, right, middle)")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("position", "vector2", "Click position"),
            VisualScriptOutput("global_position", "vector2", "Global click position")
        ],
        code_template='if event.type == "mouse_button" and event.button == "{button}" and event.pressed: pass',
        color="#E91E63"
    )
    blocks.append(click_event_block)

    # Hover Event
    hover_event_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="On Hover",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Handle mouse hover events",
        inputs=[],
        outputs=[
            VisualScriptOutput("exec_enter", "exec", "Mouse entered", is_execution_pin=True),
            VisualScriptOutput("exec_exit", "exec", "Mouse exited", is_execution_pin=True),
            VisualScriptOutput("position", "vector2", "Mouse position")
        ],
        code_template='# Handle hover events',
        color="#9C27B0"
    )
    blocks.append(hover_event_block)

    # Body Entered Event (for Area2D)
    body_entered_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="On Body Entered",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Called when a body enters this area",
        inputs=[],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("body", "node", "The body that entered")
        ],
        code_template='# Body entered area',
        color="#00BCD4"
    )
    blocks.append(body_entered_block)

    # Body Exited Event (for Area2D)
    body_exited_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="On Body Exited",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Called when a body exits this area",
        inputs=[],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("body", "node", "The body that exited")
        ],
        code_template='# Body exited area',
        color="#00BCD4"
    )
    blocks.append(body_exited_block)

    # Interact Event
    interact_event_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="On Interact",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Handle interaction events",
        inputs=[
            VisualScriptInput("interaction_key", "string", "e", "Key for interaction")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("interactor", "node", "The node that interacted")
        ],
        code_template='if is_action_just_pressed("{interaction_key}") and can_interact(): pass',
        color="#795548"
    )
    blocks.append(interact_event_block)

    # Audio Blocks

    # Play Audio
    play_audio_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Play Audio",
        category="Audio",
        block_type=VisualScriptBlockType.ACTION,
        description="Play an audio file",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("audio_path", "path", "audio/sound.wav", "Path to audio file"),
            VisualScriptInput("volume", "number", 1.0, "Volume (0.0 to 1.0)"),
            VisualScriptInput("loop", "boolean", False, "Loop the audio")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template='play_audio("{audio_path}", volume={volume}, loop={loop})',
        color="#FF5722"
    )
    blocks.append(play_audio_block)

    # Stop Audio
    stop_audio_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Stop Audio",
        category="Audio",
        block_type=VisualScriptBlockType.ACTION,
        description="Stop playing audio",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("audio_path", "path", "audio/sound.wav", "Path to audio file to stop")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template='stop_audio("{audio_path}")',
        color="#FF5722"
    )
    blocks.append(stop_audio_block)

    # Set Audio Volume
    set_volume_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Set Audio Volume",
        category="Audio",
        block_type=VisualScriptBlockType.ACTION,
        description="Set audio volume",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("volume", "number", 1.0, "Volume (0.0 to 1.0)")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template='set_master_volume({volume})',
        color="#FF5722"
    )
    blocks.append(set_volume_block)

    # Animation Blocks

    # Play Animation
    play_animation_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Play Animation",
        category="Animation",
        block_type=VisualScriptBlockType.ACTION,
        description="Play an animation",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("animation_name", "string", "idle", "Name of animation to play"),
            VisualScriptInput("loop", "boolean", True, "Loop the animation"),
            VisualScriptInput("speed", "number", 1.0, "Animation speed multiplier")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("finished", "exec", "Animation finished", is_execution_pin=True)
        ],
        code_template='play_animation("{animation_name}", loop={loop}, speed={speed})',
        color="#3F51B5"
    )
    blocks.append(play_animation_block)

    # Stop Animation
    stop_animation_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Stop Animation",
        category="Animation",
        block_type=VisualScriptBlockType.ACTION,
        description="Stop current animation",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True)
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template='stop_animation()',
        color="#3F51B5"
    )
    blocks.append(stop_animation_block)

    # Default Animations

    # Fade In Animation
    fade_in_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Fade In",
        category="Animation",
        block_type=VisualScriptBlockType.ACTION,
        description="Fade in the node",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("duration", "number", 1.0, "Fade duration in seconds")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("finished", "exec", "Fade finished", is_execution_pin=True)
        ],
        code_template='fade_in(duration={duration})',
        color="#9C27B0"
    )
    blocks.append(fade_in_block)

    # Fade Out Animation
    fade_out_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Fade Out",
        category="Animation",
        block_type=VisualScriptBlockType.ACTION,
        description="Fade out the node",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("duration", "number", 1.0, "Fade duration in seconds")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("finished", "exec", "Fade finished", is_execution_pin=True)
        ],
        code_template='fade_out(duration={duration})',
        color="#9C27B0"
    )
    blocks.append(fade_out_block)

    # Move To Animation
    move_to_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Move To",
        category="Animation",
        block_type=VisualScriptBlockType.ACTION,
        description="Move node to position",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("target_x", "number", 0.0, "Target X position"),
            VisualScriptInput("target_y", "number", 0.0, "Target Y position"),
            VisualScriptInput("duration", "number", 1.0, "Movement duration"),
            VisualScriptInput("easing", "string", "ease_in_out", "Easing type")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("finished", "exec", "Movement finished", is_execution_pin=True)
        ],
        code_template='move_to([{target_x}, {target_y}], duration={duration}, easing="{easing}")',
        color="#9C27B0"
    )
    blocks.append(move_to_block)

    # Scale Animation
    scale_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Scale To",
        category="Animation",
        block_type=VisualScriptBlockType.ACTION,
        description="Scale node to size",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("scale_x", "number", 1.0, "Target X scale"),
            VisualScriptInput("scale_y", "number", 1.0, "Target Y scale"),
            VisualScriptInput("duration", "number", 1.0, "Scale duration")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("finished", "exec", "Scale finished", is_execution_pin=True)
        ],
        code_template='scale_to([{scale_x}, {scale_y}], duration={duration})',
        color="#9C27B0"
    )
    blocks.append(scale_block)

    # Rotate Animation
    rotate_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Rotate To",
        category="Animation",
        block_type=VisualScriptBlockType.ACTION,
        description="Rotate node to angle",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("angle", "number", 0.0, "Target angle in degrees"),
            VisualScriptInput("duration", "number", 1.0, "Rotation duration")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True),
            VisualScriptOutput("finished", "exec", "Rotation finished", is_execution_pin=True)
        ],
        code_template='rotate_to({angle}, duration={duration})',
        color="#9C27B0"
    )
    blocks.append(rotate_block)

    # Node Property Blocks

    # Get Property
    get_property_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Get Property",
        category="Properties",
        block_type=VisualScriptBlockType.VARIABLE,
        description="Get a node property value",
        inputs=[
            VisualScriptInput("node", "node", "self", "Target node"),
            VisualScriptInput("property_name", "string", "position", "Property name")
        ],
        outputs=[
            VisualScriptOutput("value", "any", "Property value")
        ],
        code_template='get_property({node}, "{property_name}")',
        color="#FFEB3B"
    )
    blocks.append(get_property_block)

    # Set Property
    set_property_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Set Property",
        category="Properties",
        block_type=VisualScriptBlockType.ACTION,
        description="Set a node property value",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("node", "node", "self", "Target node"),
            VisualScriptInput("property_name", "string", "position", "Property name"),
            VisualScriptInput("value", "any", None, "New value")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template='set_property({node}, "{property_name}", {value})',
        color="#FFEB3B"
    )
    blocks.append(set_property_block)

    # Get Position
    get_position_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Get Position",
        category="Properties",
        block_type=VisualScriptBlockType.VARIABLE,
        description="Get node position",
        inputs=[
            VisualScriptInput("node", "node", "self", "Target node")
        ],
        outputs=[
            VisualScriptOutput("position", "vector2", "Node position"),
            VisualScriptOutput("x", "number", "X coordinate"),
            VisualScriptOutput("y", "number", "Y coordinate")
        ],
        code_template='get_position({node})',
        color="#FFEB3B"
    )
    blocks.append(get_position_block)

    # Set Position
    set_position_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Set Position",
        category="Properties",
        block_type=VisualScriptBlockType.ACTION,
        description="Set node position",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("node", "node", "self", "Target node"),
            VisualScriptInput("x", "number", 0.0, "X coordinate"),
            VisualScriptInput("y", "number", 0.0, "Y coordinate")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template='set_position({node}, [{x}, {y}])',
        color="#FFEB3B"
    )
    blocks.append(set_position_block)

    # Get Scale
    get_scale_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Get Scale",
        category="Properties",
        block_type=VisualScriptBlockType.VARIABLE,
        description="Get node scale",
        inputs=[
            VisualScriptInput("node", "node", "self", "Target node")
        ],
        outputs=[
            VisualScriptOutput("scale", "vector2", "Node scale"),
            VisualScriptOutput("x", "number", "X scale"),
            VisualScriptOutput("y", "number", "Y scale")
        ],
        code_template='get_scale({node})',
        color="#FFEB3B"
    )
    blocks.append(get_scale_block)

    # Set Scale
    set_scale_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Set Scale",
        category="Properties",
        block_type=VisualScriptBlockType.ACTION,
        description="Set node scale",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("node", "node", "self", "Target node"),
            VisualScriptInput("x", "number", 1.0, "X scale"),
            VisualScriptInput("y", "number", 1.0, "Y scale")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template='set_scale({node}, [{x}, {y}])',
        color="#FFEB3B"
    )
    blocks.append(set_scale_block)

    # Get Rotation
    get_rotation_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Get Rotation",
        category="Properties",
        block_type=VisualScriptBlockType.VARIABLE,
        description="Get node rotation",
        inputs=[
            VisualScriptInput("node", "node", "self", "Target node")
        ],
        outputs=[
            VisualScriptOutput("rotation", "number", "Rotation in degrees")
        ],
        code_template='get_rotation({node})',
        color="#FFEB3B"
    )
    blocks.append(get_rotation_block)

    # Set Rotation
    set_rotation_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Set Rotation",
        category="Properties",
        block_type=VisualScriptBlockType.ACTION,
        description="Set node rotation",
        inputs=[
            VisualScriptInput("exec", "exec", None, "Execution input", is_execution_pin=True),
            VisualScriptInput("node", "node", "self", "Target node"),
            VisualScriptInput("rotation", "number", 0.0, "Rotation in degrees")
        ],
        outputs=[
            VisualScriptOutput("exec", "exec", "Execution output", is_execution_pin=True)
        ],
        code_template='set_rotation({node}, {rotation})',
        color="#FFEB3B"
    )
    blocks.append(set_rotation_block)

    return blocks


def create_component_blocks():
    """Create component blocks for data input"""
    blocks = []

    # String Input
    string_input_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="String",
        category="Input",
        block_type=VisualScriptBlockType.INPUT,
        description="String value input",
        inputs=[
            VisualScriptInput("value", "string", "Hello World", "String value")
        ],
        outputs=[
            VisualScriptOutput("string", "string", "String output")
        ],
        code_template='"{value}"',
        color="#FF69B4"
    )
    blocks.append(string_input_block)

    # Integer Input
    int_input_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Integer",
        category="Input",
        block_type=VisualScriptBlockType.INPUT,
        description="Integer value input",
        inputs=[
            VisualScriptInput("value", "number", 0, "Integer value")
        ],
        outputs=[
            VisualScriptOutput("int", "number", "Integer output")
        ],
        code_template='{value}',
        color="#00FF00"
    )
    blocks.append(int_input_block)

    # Float Input
    float_input_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Float",
        category="Input",
        block_type=VisualScriptBlockType.INPUT,
        description="Float value input",
        inputs=[
            VisualScriptInput("value", "number", 0.0, "Float value")
        ],
        outputs=[
            VisualScriptOutput("float", "number", "Float output")
        ],
        code_template='{value}',
        color="#00FF00"
    )
    blocks.append(float_input_block)

    # Boolean Input
    bool_input_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Boolean",
        category="Input",
        block_type=VisualScriptBlockType.INPUT,
        description="Boolean value input",
        inputs=[
            VisualScriptInput("value", "boolean", True, "Boolean value")
        ],
        outputs=[
            VisualScriptOutput("bool", "boolean", "Boolean output")
        ],
        code_template='{value}',
        color="#FF0000"
    )
    blocks.append(bool_input_block)

    # Vector2 Input
    vector2_input_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Vector2",
        category="Input",
        block_type=VisualScriptBlockType.INPUT,
        description="2D vector input",
        inputs=[
            VisualScriptInput("x", "number", 0.0, "X coordinate"),
            VisualScriptInput("y", "number", 0.0, "Y coordinate")
        ],
        outputs=[
            VisualScriptOutput("vector", "vector2", "Vector2 output")
        ],
        code_template='({x}, {y})',
        color="#8000FF"
    )
    blocks.append(vector2_input_block)

    # Color Input
    color_input_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Color",
        category="Input",
        block_type=VisualScriptBlockType.INPUT,
        description="Color value input",
        inputs=[
            VisualScriptInput("r", "number", 255, "Red (0-255)"),
            VisualScriptInput("g", "number", 255, "Green (0-255)"),
            VisualScriptInput("b", "number", 255, "Blue (0-255)"),
            VisualScriptInput("a", "number", 255, "Alpha (0-255)")
        ],
        outputs=[
            VisualScriptOutput("color", "color", "Color output")
        ],
        code_template='({r}, {g}, {b}, {a})',
        color="#FF8000"
    )
    blocks.append(color_input_block)

    return blocks


def create_math_blocks():
    """Create mathematical operation blocks"""
    blocks = []

    # Add
    add_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Add",
        category="Math",
        block_type=VisualScriptBlockType.MATH,
        description="Add two numbers",
        inputs=[
            VisualScriptInput("a", "number", 0, "First number"),
            VisualScriptInput("b", "number", 0, "Second number")
        ],
        outputs=[
            VisualScriptOutput("result", "number", "Sum result")
        ],
        code_template='{a} + {b}',
        color="#00FFFF"
    )
    blocks.append(add_block)

    # Subtract
    subtract_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Subtract",
        category="Math",
        block_type=VisualScriptBlockType.MATH,
        description="Subtract two numbers",
        inputs=[
            VisualScriptInput("a", "number", 0, "First number"),
            VisualScriptInput("b", "number", 0, "Second number")
        ],
        outputs=[
            VisualScriptOutput("result", "number", "Difference result")
        ],
        code_template='{a} - {b}',
        color="#00FFFF"
    )
    blocks.append(subtract_block)

    # Multiply
    multiply_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Multiply",
        category="Math",
        block_type=VisualScriptBlockType.MATH,
        description="Multiply two numbers",
        inputs=[
            VisualScriptInput("a", "number", 1, "First number"),
            VisualScriptInput("b", "number", 1, "Second number")
        ],
        outputs=[
            VisualScriptOutput("result", "number", "Product result")
        ],
        code_template='{a} * {b}',
        color="#00FFFF"
    )
    blocks.append(multiply_block)

    # Divide
    divide_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Divide",
        category="Math",
        block_type=VisualScriptBlockType.MATH,
        description="Divide two numbers",
        inputs=[
            VisualScriptInput("a", "number", 1, "Dividend"),
            VisualScriptInput("b", "number", 1, "Divisor")
        ],
        outputs=[
            VisualScriptOutput("result", "number", "Quotient result")
        ],
        code_template='{a} / {b}',
        color="#00FFFF"
    )
    blocks.append(divide_block)

    # Comparison blocks
    equals_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Equals",
        category="Math",
        block_type=VisualScriptBlockType.MATH,
        description="Check if two values are equal",
        inputs=[
            VisualScriptInput("a", "any", 0, "First value"),
            VisualScriptInput("b", "any", 0, "Second value")
        ],
        outputs=[
            VisualScriptOutput("result", "boolean", "True if equal")
        ],
        code_template='{a} == {b}',
        color="#FF0000"
    )
    blocks.append(equals_block)

    # Greater than
    greater_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Greater Than",
        category="Math",
        block_type=VisualScriptBlockType.MATH,
        description="Check if first value is greater than second",
        inputs=[
            VisualScriptInput("a", "number", 0, "First number"),
            VisualScriptInput("b", "number", 0, "Second number")
        ],
        outputs=[
            VisualScriptOutput("result", "boolean", "True if a > b")
        ],
        code_template='{a} > {b}',
        color="#FF0000"
    )
    blocks.append(greater_block)

    # Less than
    less_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Less Than",
        category="Math",
        block_type=VisualScriptBlockType.MATH,
        description="Check if first value is less than second",
        inputs=[
            VisualScriptInput("a", "number", 0, "First number"),
            VisualScriptInput("b", "number", 0, "Second number")
        ],
        outputs=[
            VisualScriptOutput("result", "boolean", "True if a < b")
        ],
        code_template='{a} < {b}',
        color="#FF0000"
    )
    blocks.append(less_block)

    return blocks


def create_flow_control_blocks():
    """Create flow control blocks"""
    blocks = []
    
    # If Statement
    if_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="If",
        category="Flow Control",
        block_type=VisualScriptBlockType.FLOW,
        description="Execute code if condition is true",
        inputs=[
            VisualScriptInput("condition", "boolean", description="Condition to check")
        ],
        outputs=[
            VisualScriptOutput("true", "flow", "Execute if true"),
            VisualScriptOutput("false", "flow", "Execute if false")
        ],
        code_template="""if {condition}:
    {true_flow}
else:
    {false_flow}""",
        color="#FF6B6B"
    )
    blocks.append(if_block)
    
    # While Loop
    while_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="While",
        category="Flow Control",
        block_type=VisualScriptBlockType.FLOW,
        description="Repeat code while condition is true",
        inputs=[
            VisualScriptInput("condition", "boolean", description="Loop condition")
        ],
        outputs=[
            VisualScriptOutput("loop", "flow", "Execute in loop"),
            VisualScriptOutput("exit", "flow", "Execute after loop")
        ],
        code_template="""while {condition}:
    {loop_flow}
{exit_flow}""",
        color="#FF6B6B"
    )
    blocks.append(while_block)
    
    # Wait
    wait_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Wait",
        category="Flow Control",
        block_type=VisualScriptBlockType.ACTION,
        description="Wait for specified time",
        inputs=[
            VisualScriptInput("time", "number", 1.0, "Time to wait in seconds")
        ],
        outputs=[
            VisualScriptOutput("finished", "flow", "Execute after wait")
        ],
        code_template="""await wait({time})
{finished_flow}""",
        color="#FF6B6B"
    )
    blocks.append(wait_block)
    
    return blocks


def create_action_blocks():
    """Create action blocks"""
    blocks = []
    
    # Print Message
    print_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Print",
        category="Actions",
        block_type=VisualScriptBlockType.ACTION,
        description="Print a message to console",
        inputs=[
            VisualScriptInput("message", "string", "Hello World!", "Message to print")
        ],
        code_template="""print({message})""",
        color="#4ECDC4"
    )
    blocks.append(print_block)
    
    # Change Scene
    change_scene_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Change Scene",
        category="Actions",
        block_type=VisualScriptBlockType.ACTION,
        description="Change to a different scene",
        inputs=[
            VisualScriptInput("scene_path", "path", "", "Path to scene file")
        ],
        code_template="""change_scene("{scene_path}")""",
        color="#4ECDC4"
    )
    blocks.append(change_scene_block)
    
    # Play Sound
    play_sound_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Play Sound",
        category="Actions",
        block_type=VisualScriptBlockType.ACTION,
        description="Play a sound effect",
        inputs=[
            VisualScriptInput("sound_path", "path", "", "Path to sound file"),
            VisualScriptInput("volume", "number", 1.0, "Volume (0.0 to 1.0)")
        ],
        code_template="""play_sound("{sound_path}", {volume})""",
        color="#4ECDC4"
    )
    blocks.append(play_sound_block)
    
    # Show Dialogue
    show_dialogue_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Show Dialogue",
        category="Actions",
        block_type=VisualScriptBlockType.ACTION,
        description="Show dialogue text",
        inputs=[
            VisualScriptInput("speaker", "string", "", "Speaker name"),
            VisualScriptInput("text", "string", "", "Dialogue text")
        ],
        code_template="""show_dialogue("{speaker}", "{text}")""",
        color="#4ECDC4"
    )
    blocks.append(show_dialogue_block)
    
    # Move Node
    move_node_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Move Node",
        category="Actions",
        block_type=VisualScriptBlockType.ACTION,
        description="Move a node to a position",
        inputs=[
            VisualScriptInput("node", "node", description="Node to move"),
            VisualScriptInput("position", "vector2", [0, 0], "Target position"),
            VisualScriptInput("duration", "number", 1.0, "Movement duration")
        ],
        code_template="""move_node({node}, {position}, {duration})""",
        color="#4ECDC4"
    )
    blocks.append(move_node_block)
    
    return blocks


def create_condition_blocks():
    """Create condition blocks"""
    blocks = []
    
    # Compare Numbers
    compare_numbers_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Compare Numbers",
        category="Conditions",
        block_type=VisualScriptBlockType.CONDITION,
        description="Compare two numbers",
        inputs=[
            VisualScriptInput("value1", "number", 0, "First value"),
            VisualScriptInput("operator", "string", "==", "Comparison operator", 
                            options=["==", "!=", "<", ">", "<=", ">="]),
            VisualScriptInput("value2", "number", 0, "Second value")
        ],
        outputs=[
            VisualScriptOutput("result", "boolean", "Comparison result")
        ],
        code_template="""{value1} {operator} {value2}""",
        color="#FFD93D"
    )
    blocks.append(compare_numbers_block)
    
    # Check Variable
    check_variable_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Check Variable",
        category="Conditions",
        block_type=VisualScriptBlockType.CONDITION,
        description="Check if variable exists and has value",
        inputs=[
            VisualScriptInput("variable_name", "string", "", "Variable name"),
            VisualScriptInput("expected_value", "string", "", "Expected value (optional)")
        ],
        outputs=[
            VisualScriptOutput("result", "boolean", "Check result")
        ],
        code_template="""check_variable("{variable_name}", "{expected_value}")""",
        color="#FFD93D"
    )
    blocks.append(check_variable_block)
    
    # Has Item
    has_item_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Has Item",
        category="Conditions",
        block_type=VisualScriptBlockType.CONDITION,
        description="Check if player has item",
        inputs=[
            VisualScriptInput("item_id", "string", "", "Item ID to check"),
            VisualScriptInput("quantity", "number", 1, "Required quantity")
        ],
        outputs=[
            VisualScriptOutput("result", "boolean", "Check result")
        ],
        code_template="""has_item("{item_id}", {quantity})""",
        color="#FFD93D"
    )
    blocks.append(has_item_block)
    
    return blocks


def create_variable_blocks():
    """Create variable blocks"""
    blocks = []
    
    # Set Variable
    set_variable_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Set Variable",
        category="Variables",
        block_type=VisualScriptBlockType.VARIABLE,
        description="Set a variable value",
        inputs=[
            VisualScriptInput("variable_name", "string", "", "Variable name"),
            VisualScriptInput("value", "string", "", "Variable value")
        ],
        code_template="""set_variable("{variable_name}", {value})""",
        color="#6BCF7F"
    )
    blocks.append(set_variable_block)
    
    # Get Variable
    get_variable_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Get Variable",
        category="Variables",
        block_type=VisualScriptBlockType.VARIABLE,
        description="Get a variable value",
        inputs=[
            VisualScriptInput("variable_name", "string", "", "Variable name"),
            VisualScriptInput("default_value", "string", "", "Default value if not found")
        ],
        outputs=[
            VisualScriptOutput("value", "string", "Variable value")
        ],
        code_template="""get_variable("{variable_name}", {default_value})""",
        color="#6BCF7F"
    )
    blocks.append(get_variable_block)
    
    # Add to Variable
    add_to_variable_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Add to Variable",
        category="Variables",
        block_type=VisualScriptBlockType.VARIABLE,
        description="Add value to a numeric variable",
        inputs=[
            VisualScriptInput("variable_name", "string", "", "Variable name"),
            VisualScriptInput("amount", "number", 1, "Amount to add")
        ],
        code_template="""add_to_variable("{variable_name}", {amount})""",
        color="#6BCF7F"
    )
    blocks.append(add_to_variable_block)
    
    return blocks


def create_event_blocks():
    """Create event blocks"""
    blocks = []
    
    # Emit Signal
    emit_signal_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="Emit Signal",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Emit a signal",
        inputs=[
            VisualScriptInput("signal_name", "string", "", "Signal name"),
            VisualScriptInput("data", "string", "", "Signal data (optional)")
        ],
        code_template="""emit_signal("{signal_name}", {data})""",
        color="#A8E6CF"
    )
    blocks.append(emit_signal_block)
    
    # On Timer
    on_timer_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="On Timer",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Execute code on timer",
        inputs=[
            VisualScriptInput("interval", "number", 1.0, "Timer interval in seconds"),
            VisualScriptInput("repeat", "boolean", True, "Repeat timer")
        ],
        outputs=[
            VisualScriptOutput("timeout", "flow", "Execute on timeout")
        ],
        code_template="""start_timer({interval}, {repeat}, lambda: {timeout_flow})""",
        color="#A8E6CF"
    )
    blocks.append(on_timer_block)
    
    # On Input
    on_input_block = VisualScriptBlock(
        id=str(uuid.uuid4()),
        name="On Input",
        category="Events",
        block_type=VisualScriptBlockType.EVENT,
        description="Execute code on input",
        inputs=[
            VisualScriptInput("input_action", "string", "", "Input action name"),
            VisualScriptInput("event_type", "string", "pressed", "Event type", 
                            options=["pressed", "released", "held"])
        ],
        outputs=[
            VisualScriptOutput("triggered", "flow", "Execute on input")
        ],
        code_template="""on_input("{input_action}", "{event_type}", lambda: {triggered_flow})""",
        color="#A8E6CF"
    )
    blocks.append(on_input_block)
    
    return blocks
