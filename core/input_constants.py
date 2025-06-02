"""
Input Constants for Lupine Engine
Provides Godot-like constants for keys and mouse buttons
"""

import arcade

# Mouse button constants (Godot-like)
MOUSE_BUTTON_LEFT = 1
MOUSE_BUTTON_RIGHT = 2
MOUSE_BUTTON_MIDDLE = 3
MOUSE_BUTTON_WHEEL_UP = 4
MOUSE_BUTTON_WHEEL_DOWN = 5
MOUSE_BUTTON_WHEEL_LEFT = 6
MOUSE_BUTTON_WHEEL_RIGHT = 7
MOUSE_BUTTON_XBUTTON1 = 8
MOUSE_BUTTON_XBUTTON2 = 9

# Key constants (Godot-like names mapped to arcade keys)
KEY_ESCAPE = arcade.key.ESCAPE
KEY_TAB = arcade.key.TAB
KEY_BACKTAB = arcade.key.TAB  # Shift+Tab
KEY_BACKSPACE = arcade.key.BACKSPACE
KEY_ENTER = arcade.key.ENTER
KEY_INSERT = arcade.key.INSERT
KEY_DELETE = arcade.key.DELETE
KEY_PAUSE = arcade.key.PAUSE
KEY_PRINT = arcade.key.PRINT
KEY_HOME = arcade.key.HOME
KEY_END = arcade.key.END
KEY_LEFT = arcade.key.LEFT
KEY_UP = arcade.key.UP
KEY_RIGHT = arcade.key.RIGHT
KEY_DOWN = arcade.key.DOWN
KEY_PAGEUP = arcade.key.PAGEUP
KEY_PAGEDOWN = arcade.key.PAGEDOWN

# Shift keys
KEY_SHIFT = arcade.key.LSHIFT
KEY_LSHIFT = arcade.key.LSHIFT
KEY_RSHIFT = arcade.key.RSHIFT

# Control keys
KEY_CTRL = arcade.key.LCTRL
KEY_LCTRL = arcade.key.LCTRL
KEY_RCTRL = arcade.key.RCTRL

# Alt keys
KEY_ALT = arcade.key.LALT
KEY_LALT = arcade.key.LALT
KEY_RALT = arcade.key.RALT

# Meta/Windows keys
KEY_META = arcade.key.LMETA
KEY_LMETA = arcade.key.LMETA
KEY_RMETA = arcade.key.RMETA

# Function keys
KEY_F1 = arcade.key.F1
KEY_F2 = arcade.key.F2
KEY_F3 = arcade.key.F3
KEY_F4 = arcade.key.F4
KEY_F5 = arcade.key.F5
KEY_F6 = arcade.key.F6
KEY_F7 = arcade.key.F7
KEY_F8 = arcade.key.F8
KEY_F9 = arcade.key.F9
KEY_F10 = arcade.key.F10
KEY_F11 = arcade.key.F11
KEY_F12 = arcade.key.F12

# Number keys
KEY_0 = arcade.key.KEY_0
KEY_1 = arcade.key.KEY_1
KEY_2 = arcade.key.KEY_2
KEY_3 = arcade.key.KEY_3
KEY_4 = arcade.key.KEY_4
KEY_5 = arcade.key.KEY_5
KEY_6 = arcade.key.KEY_6
KEY_7 = arcade.key.KEY_7
KEY_8 = arcade.key.KEY_8
KEY_9 = arcade.key.KEY_9

# Letter keys
KEY_A = arcade.key.A
KEY_B = arcade.key.B
KEY_C = arcade.key.C
KEY_D = arcade.key.D
KEY_E = arcade.key.E
KEY_F = arcade.key.F
KEY_G = arcade.key.G
KEY_H = arcade.key.H
KEY_I = arcade.key.I
KEY_J = arcade.key.J
KEY_K = arcade.key.K
KEY_L = arcade.key.L
KEY_M = arcade.key.M
KEY_N = arcade.key.N
KEY_O = arcade.key.O
KEY_P = arcade.key.P
KEY_Q = arcade.key.Q
KEY_R = arcade.key.R
KEY_S = arcade.key.S
KEY_T = arcade.key.T
KEY_U = arcade.key.U
KEY_V = arcade.key.V
KEY_W = arcade.key.W
KEY_X = arcade.key.X
KEY_Y = arcade.key.Y
KEY_Z = arcade.key.Z

# Special characters
KEY_SPACE = arcade.key.SPACE
KEY_EXCLAM = arcade.key.EXCLAMATION
KEY_QUOTEDBL = arcade.key.DOUBLEQUOTE
KEY_NUMBERSIGN = arcade.key.HASH
KEY_DOLLAR = arcade.key.DOLLAR
KEY_PERCENT = arcade.key.PERCENT
KEY_AMPERSAND = arcade.key.AMPERSAND
KEY_APOSTROPHE = arcade.key.APOSTROPHE
KEY_PARENLEFT = arcade.key.PARENLEFT
KEY_PARENRIGHT = arcade.key.PARENRIGHT
KEY_ASTERISK = arcade.key.ASTERISK
KEY_PLUS = arcade.key.PLUS
KEY_COMMA = arcade.key.COMMA
KEY_MINUS = arcade.key.MINUS
KEY_PERIOD = arcade.key.PERIOD
KEY_SLASH = arcade.key.SLASH

# Brackets and braces
KEY_BRACKETLEFT = arcade.key.BRACKETLEFT
KEY_BACKSLASH = arcade.key.BACKSLASH
KEY_BRACKETRIGHT = arcade.key.BRACKETRIGHT
KEY_ASCIICIRCUM = arcade.key.ASCIICIRCUM
KEY_UNDERSCORE = arcade.key.UNDERSCORE
KEY_GRAVE = arcade.key.GRAVE
KEY_BRACELEFT = arcade.key.BRACELEFT
KEY_BAR = arcade.key.BAR
KEY_BRACERIGHT = arcade.key.BRACERIGHT
KEY_ASCIITILDE = arcade.key.ASCIITILDE

# Numpad keys
KEY_KP_0 = arcade.key.NUM_0
KEY_KP_1 = arcade.key.NUM_1
KEY_KP_2 = arcade.key.NUM_2
KEY_KP_3 = arcade.key.NUM_3
KEY_KP_4 = arcade.key.NUM_4
KEY_KP_5 = arcade.key.NUM_5
KEY_KP_6 = arcade.key.NUM_6
KEY_KP_7 = arcade.key.NUM_7
KEY_KP_8 = arcade.key.NUM_8
KEY_KP_9 = arcade.key.NUM_9
KEY_KP_PERIOD = arcade.key.NUM_DECIMAL
KEY_KP_DIVIDE = arcade.key.NUM_DIVIDE
KEY_KP_MULTIPLY = arcade.key.NUM_MULTIPLY
KEY_KP_MINUS = arcade.key.NUM_SUBTRACT
KEY_KP_PLUS = arcade.key.NUM_ADD
KEY_KP_ENTER = arcade.key.NUM_ENTER

# Lock keys
KEY_CAPSLOCK = arcade.key.CAPSLOCK
KEY_NUMLOCK = arcade.key.NUMLOCK
KEY_SCROLLLOCK = arcade.key.SCROLLLOCK

# Key name mappings for display and configuration
KEY_NAMES = {
    # Mouse buttons
    MOUSE_BUTTON_LEFT: "Left Mouse Button",
    MOUSE_BUTTON_RIGHT: "Right Mouse Button", 
    MOUSE_BUTTON_MIDDLE: "Middle Mouse Button",
    MOUSE_BUTTON_WHEEL_UP: "Mouse Wheel Up",
    MOUSE_BUTTON_WHEEL_DOWN: "Mouse Wheel Down",
    MOUSE_BUTTON_WHEEL_LEFT: "Mouse Wheel Left",
    MOUSE_BUTTON_WHEEL_RIGHT: "Mouse Wheel Right",
    MOUSE_BUTTON_XBUTTON1: "Mouse X Button 1",
    MOUSE_BUTTON_XBUTTON2: "Mouse X Button 2",
    
    # Special keys
    KEY_ESCAPE: "Escape",
    KEY_TAB: "Tab",
    KEY_BACKSPACE: "Backspace",
    KEY_ENTER: "Enter",
    KEY_SPACE: "Space",
    KEY_DELETE: "Delete",
    KEY_INSERT: "Insert",
    KEY_HOME: "Home",
    KEY_END: "End",
    KEY_PAGEUP: "Page Up",
    KEY_PAGEDOWN: "Page Down",
    
    # Arrow keys
    KEY_LEFT: "Left Arrow",
    KEY_RIGHT: "Right Arrow",
    KEY_UP: "Up Arrow",
    KEY_DOWN: "Down Arrow",
    
    # Modifier keys
    KEY_SHIFT: "Shift",
    KEY_LSHIFT: "Left Shift",
    KEY_RSHIFT: "Right Shift",
    KEY_CTRL: "Ctrl",
    KEY_LCTRL: "Left Ctrl",
    KEY_RCTRL: "Right Ctrl",
    KEY_ALT: "Alt",
    KEY_LALT: "Left Alt",
    KEY_RALT: "Right Alt",
    KEY_META: "Meta",
    KEY_LMETA: "Left Meta",
    KEY_RMETA: "Right Meta",
    
    # Function keys
    KEY_F1: "F1", KEY_F2: "F2", KEY_F3: "F3", KEY_F4: "F4",
    KEY_F5: "F5", KEY_F6: "F6", KEY_F7: "F7", KEY_F8: "F8",
    KEY_F9: "F9", KEY_F10: "F10", KEY_F11: "F11", KEY_F12: "F12",
    
    # Number keys
    KEY_0: "0", KEY_1: "1", KEY_2: "2", KEY_3: "3", KEY_4: "4",
    KEY_5: "5", KEY_6: "6", KEY_7: "7", KEY_8: "8", KEY_9: "9",
    
    # Letter keys
    KEY_A: "A", KEY_B: "B", KEY_C: "C", KEY_D: "D", KEY_E: "E",
    KEY_F: "F", KEY_G: "G", KEY_H: "H", KEY_I: "I", KEY_J: "J",
    KEY_K: "K", KEY_L: "L", KEY_M: "M", KEY_N: "N", KEY_O: "O",
    KEY_P: "P", KEY_Q: "Q", KEY_R: "R", KEY_S: "S", KEY_T: "T",
    KEY_U: "U", KEY_V: "V", KEY_W: "W", KEY_X: "X", KEY_Y: "Y", KEY_Z: "Z",
}

def get_key_name(key_code: int) -> str:
    """Get the display name for a key code"""
    return KEY_NAMES.get(key_code, f"Key {key_code}")

def get_key_code_by_name(name: str) -> int:
    """Get key code by display name"""
    for code, display_name in KEY_NAMES.items():
        if display_name.lower() == name.lower():
            return code
    return -1
