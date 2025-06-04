#!/usr/bin/env python3
"""
Test script for Button signals and AudioStreamPlayer
This script creates a simple scene with a button and audio player to test functionality
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from nodes.ui.Button import Button
from nodes.audio.AudioStreamPlayer import AudioStreamPlayer
from nodes.base.Node import Node

def test_button_signals():
    """Test button signal connections and emission"""
    print("=== Testing Button Signals ===")
    
    # Create a button
    button = Button("TestButton")
    button.set_text("Click Me!")
    button.rect_position = [100, 100]
    button.rect_size = [200, 50]
    
    # Create a simple signal handler
    def on_button_pressed():
        print("Button pressed signal received!")
    
    def on_button_down():
        print("Button down signal received!")
    
    def on_button_up():
        print("Button up signal received!")
    
    # Create a target node for signal connections
    target_node = Node("SignalTarget")
    
    # Add methods to the target node
    target_node.on_button_pressed = on_button_pressed
    target_node.on_button_down = on_button_down
    target_node.on_button_up = on_button_up
    
    # Connect signals
    button.connect("pressed", target_node, "on_button_pressed")
    button.connect("button_down", target_node, "on_button_down")
    button.connect("button_up", target_node, "on_button_up")
    
    print(f"Button created: {button}")
    print(f"Button signals: {list(button._signals.keys())}")
    print(f"Button connections: {button._signals}")
    
    # Test button initialization
    try:
        button._ready()
        print("Button _ready() called successfully")
    except Exception as e:
        print(f"Error in button _ready(): {e}")
    
    # Test programmatic click
    print("\n--- Testing programmatic click ---")
    try:
        button.click()
        print("Programmatic click completed")
    except Exception as e:
        print(f"Error in programmatic click: {e}")
    
    # Test manual signal emission
    print("\n--- Testing manual signal emission ---")
    try:
        button.emit_signal("pressed")
        print("Manual signal emission completed")
    except Exception as e:
        print(f"Error in manual signal emission: {e}")
    
    # Test mouse events
    print("\n--- Testing mouse events ---")
    try:
        # Simulate mouse enter
        button._on_mouse_entered()
        print(f"Mouse entered - hovered: {button._is_hovered}")
        
        # Simulate mouse click
        button._handle_button_down()
        print(f"Button down - pressed: {button._is_pressed}")
        
        button._handle_button_up()
        print(f"Button up - pressed: {button._is_pressed}")
        
        # Simulate mouse exit
        button._on_mouse_exited()
        print(f"Mouse exited - hovered: {button._is_hovered}")
        
    except Exception as e:
        print(f"Error in mouse event simulation: {e}")

def test_audio_stream_player():
    """Test AudioStreamPlayer creation and initialization"""
    print("\n=== Testing AudioStreamPlayer ===")
    
    try:
        # Create an audio stream player
        audio_player = AudioStreamPlayer("TestAudio")
        print(f"AudioStreamPlayer created: {audio_player}")
        print(f"Audio signals: {list(audio_player._signals.keys())}")
        
        # Test initialization
        audio_player._ready()
        print("AudioStreamPlayer _ready() called successfully")
        
        # Test basic properties
        print(f"Stream: {audio_player.stream}")
        print(f"Volume: {audio_player.volume_db}")
        print(f"Playing: {audio_player.playing}")
        print(f"Autoplay: {audio_player.autoplay}")
        
        # Test serialization
        audio_dict = audio_player.to_dict()
        print(f"AudioStreamPlayer serialized successfully: {len(audio_dict)} properties")
        
        # Test deserialization
        new_audio = AudioStreamPlayer.from_dict(audio_dict)
        print(f"AudioStreamPlayer deserialized successfully: {new_audio}")
        
    except Exception as e:
        print(f"Error testing AudioStreamPlayer: {e}")
        import traceback
        traceback.print_exc()

def test_button_serialization():
    """Test Button serialization and deserialization"""
    print("\n=== Testing Button Serialization ===")
    
    try:
        # Create a button with custom properties
        button = Button("SerializationTest")
        button.set_text("Serialize Me!")
        button.rect_position = [50, 75]
        button.rect_size = [150, 40]
        button.disabled = False
        button.flat = True
        button._is_hovered = True  # Set some visual state
        
        # Test serialization
        button_dict = button.to_dict()
        print(f"Button serialized successfully: {len(button_dict)} properties")
        print(f"Visual state included: _is_hovered={button_dict.get('_is_hovered')}")
        
        # Test deserialization
        new_button = Button.from_dict(button_dict)
        print(f"Button deserialized successfully: {new_button}")
        print(f"Text preserved: {new_button.text}")
        print(f"Position preserved: {new_button.rect_position}")
        print(f"Size preserved: {new_button.rect_size}")
        
    except Exception as e:
        print(f"Error testing Button serialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting Button and AudioStreamPlayer tests...")
    
    test_button_signals()
    test_audio_stream_player()
    test_button_serialization()
    
    print("\nTests completed!")
