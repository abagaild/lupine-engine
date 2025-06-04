# Button Test Script
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
