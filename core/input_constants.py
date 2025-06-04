"""
Input Constants for Lupine Engine
Provides Godot-like constants for keys and mouse buttons
"""

import pygame

# Mouse button constants (Godot-like, mapped to pygame)
MOUSE_BUTTON_LEFT = 1
MOUSE_BUTTON_RIGHT = 3
MOUSE_BUTTON_MIDDLE = 2
MOUSE_BUTTON_WHEEL_UP = 4
MOUSE_BUTTON_WHEEL_DOWN = 5
MOUSE_BUTTON_WHEEL_LEFT = 6
MOUSE_BUTTON_WHEEL_RIGHT = 7
MOUSE_BUTTON_XBUTTON1 = 8
MOUSE_BUTTON_XBUTTON2 = 9

# Key constants (Godot-like names mapped to pygame keys)
KEY_ESCAPE = pygame.K_ESCAPE
KEY_TAB = pygame.K_TAB
KEY_BACKTAB = pygame.K_TAB  # Shift+Tab
KEY_BACKSPACE = pygame.K_BACKSPACE
KEY_ENTER = pygame.K_RETURN
KEY_INSERT = pygame.K_INSERT
KEY_DELETE = pygame.K_DELETE
KEY_PAUSE = pygame.K_PAUSE
KEY_PRINT = pygame.K_PRINT
KEY_HOME = pygame.K_HOME
KEY_END = pygame.K_END
KEY_LEFT = pygame.K_LEFT
KEY_UP = pygame.K_UP
KEY_RIGHT = pygame.K_RIGHT
KEY_DOWN = pygame.K_DOWN
KEY_PAGEUP = pygame.K_PAGEUP
KEY_PAGEDOWN = pygame.K_PAGEDOWN

# Shift keys
KEY_SHIFT = pygame.K_LSHIFT
KEY_LSHIFT = pygame.K_LSHIFT
KEY_RSHIFT = pygame.K_RSHIFT

# Control keys
KEY_CTRL = pygame.K_LCTRL
KEY_LCTRL = pygame.K_LCTRL
KEY_RCTRL = pygame.K_RCTRL

# Alt keys
KEY_ALT = pygame.K_LALT
KEY_LALT = pygame.K_LALT
KEY_RALT = pygame.K_RALT

# Meta/Windows keys
KEY_META = pygame.K_LMETA
KEY_LMETA = pygame.K_LMETA
KEY_RMETA = pygame.K_RMETA

# Function keys
KEY_F1 = pygame.K_F1
KEY_F2 = pygame.K_F2
KEY_F3 = pygame.K_F3
KEY_F4 = pygame.K_F4
KEY_F5 = pygame.K_F5
KEY_F6 = pygame.K_F6
KEY_F7 = pygame.K_F7
KEY_F8 = pygame.K_F8
KEY_F9 = pygame.K_F9
KEY_F10 = pygame.K_F10
KEY_F11 = pygame.K_F11
KEY_F12 = pygame.K_F12

# Number keys
KEY_0 = pygame.K_0
KEY_1 = pygame.K_1
KEY_2 = pygame.K_2
KEY_3 = pygame.K_3
KEY_4 = pygame.K_4
KEY_5 = pygame.K_5
KEY_6 = pygame.K_6
KEY_7 = pygame.K_7
KEY_8 = pygame.K_8
KEY_9 = pygame.K_9

# Letter keys
KEY_A = pygame.K_a
KEY_B = pygame.K_b
KEY_C = pygame.K_c
KEY_D = pygame.K_d
KEY_E = pygame.K_e
KEY_F = pygame.K_f
KEY_G = pygame.K_g
KEY_H = pygame.K_h
KEY_I = pygame.K_i
KEY_J = pygame.K_j
KEY_K = pygame.K_k
KEY_L = pygame.K_l
KEY_M = pygame.K_m
KEY_N = pygame.K_n
KEY_O = pygame.K_o
KEY_P = pygame.K_p
KEY_Q = pygame.K_q
KEY_R = pygame.K_r
KEY_S = pygame.K_s
KEY_T = pygame.K_t
KEY_U = pygame.K_u
KEY_V = pygame.K_v
KEY_W = pygame.K_w
KEY_X = pygame.K_x
KEY_Y = pygame.K_y
KEY_Z = pygame.K_z

# Special characters
KEY_SPACE = pygame.K_SPACE
KEY_EXCLAM = pygame.K_EXCLAIM
KEY_QUOTEDBL = pygame.K_QUOTEDBL
KEY_NUMBERSIGN = pygame.K_HASH
KEY_DOLLAR = pygame.K_DOLLAR
KEY_PERCENT = pygame.K_PERCENT
KEY_AMPERSAND = pygame.K_AMPERSAND
KEY_APOSTROPHE = pygame.K_QUOTE
KEY_PARENLEFT = pygame.K_LEFTPAREN
KEY_PARENRIGHT = pygame.K_RIGHTPAREN
KEY_ASTERISK = pygame.K_ASTERISK
KEY_PLUS = pygame.K_PLUS
KEY_COMMA = pygame.K_COMMA
KEY_MINUS = pygame.K_MINUS
KEY_PERIOD = pygame.K_PERIOD
KEY_SLASH = pygame.K_SLASH

# Brackets and braces
KEY_BRACKETLEFT = pygame.K_LEFTBRACKET
KEY_BACKSLASH = pygame.K_BACKSLASH
KEY_BRACKETRIGHT = pygame.K_RIGHTBRACKET
KEY_ASCIICIRCUM = pygame.K_CARET
KEY_UNDERSCORE = pygame.K_UNDERSCORE
KEY_GRAVE = pygame.K_BACKQUOTE
# Note: pygame doesn't have separate constants for braces, they're shift+bracket
KEY_BRACELEFT = pygame.K_LEFTBRACKET  # {
KEY_BAR = pygame.K_BACKSLASH  # |
KEY_BRACERIGHT = pygame.K_RIGHTBRACKET  # }
KEY_ASCIITILDE = pygame.K_BACKQUOTE  # ~

# Numpad keys
KEY_KP_0 = pygame.K_KP0
KEY_KP_1 = pygame.K_KP1
KEY_KP_2 = pygame.K_KP2
KEY_KP_3 = pygame.K_KP3
KEY_KP_4 = pygame.K_KP4
KEY_KP_5 = pygame.K_KP5
KEY_KP_6 = pygame.K_KP6
KEY_KP_7 = pygame.K_KP7
KEY_KP_8 = pygame.K_KP8
KEY_KP_9 = pygame.K_KP9
KEY_KP_PERIOD = pygame.K_KP_PERIOD
KEY_KP_DIVIDE = pygame.K_KP_DIVIDE
KEY_KP_MULTIPLY = pygame.K_KP_MULTIPLY
KEY_KP_MINUS = pygame.K_KP_MINUS
KEY_KP_PLUS = pygame.K_KP_PLUS
KEY_KP_ENTER = pygame.K_KP_ENTER

# Lock keys
KEY_CAPSLOCK = pygame.K_CAPSLOCK
KEY_NUMLOCK = pygame.K_NUMLOCK
KEY_SCROLLLOCK = pygame.K_SCROLLOCK

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
