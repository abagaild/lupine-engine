#!/usr/bin/env python3
"""
Test scene for Button rendering and interaction
Creates a simple scene with buttons to test visual feedback and signals
"""

import sys
import os
import json

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from nodes.ui.Button import Button
from nodes.ui.Label import Label
from nodes.audio.AudioStreamPlayer import AudioStreamPlayer

def create_test_scene():
    """Create a test scene with buttons and labels"""
    
    # Create scene data structure
    scene_data = {
        "name": "ButtonTestScene",
        "root_nodes": []
    }
    
    # Create a test button
    test_button = Button("TestButton")
    test_button.set_text("Click Me!")
    test_button.position = [100, 100]
    test_button.size = [200, 50]
    test_button.follow_viewport = True  # Viewport-relative positioning
    test_button.bg_color = [0.2, 0.4, 0.8, 1.0]  # Blue background
    test_button.bg_color_hover = [0.3, 0.5, 0.9, 1.0]  # Lighter blue on hover
    test_button.bg_color_pressed = [0.1, 0.3, 0.7, 1.0]  # Darker blue when pressed
    test_button.font_color = [1.0, 1.0, 1.0, 1.0]  # White text
    test_button.border_width = 2.0
    test_button.border_color = [0.8, 0.8, 0.8, 1.0]  # Light gray border
    test_button.border_radius = 8.0
    
    # Create a flat button
    flat_button = Button("FlatButton")
    flat_button.set_text("Flat Button")
    flat_button.position = [100, 200]
    flat_button.size = [200, 50]
    flat_button.follow_viewport = True
    flat_button.flat = True
    flat_button.font_color = [0.2, 0.8, 0.2, 1.0]  # Green text
    flat_button.font_color_hover = [0.3, 0.9, 0.3, 1.0]  # Lighter green on hover
    flat_button.border_width = 0.0  # No border for flat button

    # Create a disabled button
    disabled_button = Button("DisabledButton")
    disabled_button.set_text("Disabled")
    disabled_button.position = [100, 300]
    disabled_button.size = [200, 50]
    disabled_button.follow_viewport = True
    disabled_button.disabled = True
    disabled_button.bg_color_disabled = [0.1, 0.1, 0.1, 1.0]  # Very dark background
    disabled_button.font_color_disabled = [0.4, 0.4, 0.4, 1.0]  # Dark gray text

    # Create a toggle button
    toggle_button = Button("ToggleButton")
    toggle_button.set_text("Toggle Me")
    toggle_button.position = [100, 400]
    toggle_button.size = [200, 50]
    toggle_button.follow_viewport = True
    toggle_button.toggle_mode = True
    toggle_button.bg_color = [0.8, 0.4, 0.2, 1.0]  # Orange background
    toggle_button.bg_color_pressed = [0.6, 0.3, 0.1, 1.0]  # Darker orange when toggled

    # Create a world-space button (for testing)
    world_button = Button("WorldButton")
    world_button.set_text("World Space")
    world_button.position = [500, 300]
    world_button.size = [150, 40]
    world_button.follow_viewport = False  # World-space positioning
    world_button.bg_color = [0.6, 0.2, 0.8, 1.0]  # Purple background

    # Create a label for instructions
    instruction_label = Label("Instructions")
    instruction_label.text = "Test different button states and interactions"
    instruction_label.position = [100, 50]
    instruction_label.size = [400, 30]
    instruction_label.follow_viewport = True
    instruction_label.font_color = [1.0, 1.0, 0.0, 1.0]  # Yellow text
    instruction_label.font_size = 16
    
    # Create an audio player for button click sounds
    audio_player = AudioStreamPlayer("ButtonClickSound")
    # Note: No actual audio file set for this test
    
    # Convert nodes to dictionary format for scene file
    scene_data["root_nodes"] = [
        instruction_label.to_dict(),
        test_button.to_dict(),
        flat_button.to_dict(),
        disabled_button.to_dict(),
        toggle_button.to_dict(),
        world_button.to_dict(),
        audio_player.to_dict()
    ]
    
    return scene_data

def save_test_scene():
    """Save the test scene to a file"""
    scene_data = create_test_scene()
    
    # Create scenes directory if it doesn't exist
    scenes_dir = os.path.join(project_root, "scenes")
    os.makedirs(scenes_dir, exist_ok=True)
    
    # Save scene file
    scene_file = os.path.join(scenes_dir, "ButtonTest.scene")
    with open(scene_file, 'w') as f:
        json.dump(scene_data, f, indent=2)
    
    print(f"Test scene saved to: {scene_file}")
    return scene_file

def create_button_test_script():
    """Create a test script that handles button signals"""
    script_content = '''# Button Test Script
# Handles button click events and provides feedback

def _on_ready():
    """Called when the script is ready"""
    print("Button test script ready!")
    
    # Connect button signals
    test_button = get_node("TestButton")
    if test_button:
        test_button.connect("pressed", self, "_on_test_button_pressed")
        test_button.connect("button_down", self, "_on_button_down")
        test_button.connect("button_up", self, "_on_button_up")
    
    flat_button = get_node("FlatButton")
    if flat_button:
        flat_button.connect("pressed", self, "_on_flat_button_pressed")
    
    toggle_button = get_node("ToggleButton")
    if toggle_button:
        toggle_button.connect("toggled", self, "_on_toggle_button_toggled")

def _on_test_button_pressed():
    """Handle test button press"""
    print("Test button was pressed!")
    
    # Play click sound
    audio_player = get_node("ButtonClickSound")
    if audio_player:
        # audio_player.play()  # Uncomment when audio file is available
        pass

def _on_flat_button_pressed():
    """Handle flat button press"""
    print("Flat button was pressed!")

def _on_toggle_button_toggled(pressed):
    """Handle toggle button state change"""
    state = "ON" if pressed else "OFF"
    print(f"Toggle button is now: {state}")
    
    # Update button text to reflect state
    toggle_button = get_node("ToggleButton")
    if toggle_button:
        toggle_button.set_text(f"Toggle: {state}")

def _on_button_down():
    """Handle button down event"""
    print("Button down!")

def _on_button_up():
    """Handle button up event"""
    print("Button up!")
'''
    
    # Create scripts directory if it doesn't exist
    scripts_dir = os.path.join(project_root, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    
    # Save script file
    script_file = os.path.join(scripts_dir, "ButtonTestScript.py")
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    print(f"Test script saved to: {script_file}")
    return script_file

if __name__ == "__main__":
    print("Creating button test scene...")
    
    # Create and save the test scene
    scene_file = save_test_scene()
    
    # Create the test script
    script_file = create_button_test_script()
    
    print("\nTest scene and script created successfully!")
    print(f"Scene file: {scene_file}")
    print(f"Script file: {script_file}")
    print("\nTo test:")
    print("1. Open the Lupine Engine editor")
    print("2. Load the ButtonTest.scene file")
    print("3. Run the scene to test button interactions")
