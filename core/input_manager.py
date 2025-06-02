"""
Input Manager for Lupine Engine
Handles input actions, key mapping, and input state management
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from core.input_constants import *

@dataclass
class InputEvent:
    """Represents an input event (key or mouse button)"""
    type: str  # "key" or "mouse"
    code: int  # Key code or mouse button code
    modifiers: List[str] = None  # List of modifier keys: "shift", "ctrl", "alt", "meta"
    
    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = []
    
    def matches(self, pressed_keys: Set[int], mouse_buttons: Set[int], current_modifiers: Set[str]) -> bool:
        """Check if this input event matches the current input state"""
        # Check if the main key/button is pressed
        if self.type == "key" and self.code not in pressed_keys:
            return False
        elif self.type == "mouse" and self.code not in mouse_buttons:
            return False
        
        # Check modifiers
        required_modifiers = set(self.modifiers)
        return required_modifiers.issubset(current_modifiers)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InputEvent':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class InputAction:
    """Represents an input action with multiple possible input events"""
    name: str
    events: List[InputEvent]
    deadzone: float = 0.2  # For analog inputs
    
    def __post_init__(self):
        if not self.events:
            self.events = []
    
    def is_pressed(self, pressed_keys: Set[int], mouse_buttons: Set[int], modifiers: Set[str]) -> bool:
        """Check if any of the action's events are currently pressed"""
        return any(event.matches(pressed_keys, mouse_buttons, modifiers) for event in self.events)
    
    def get_strength(self, pressed_keys: Set[int], mouse_buttons: Set[int], modifiers: Set[str]) -> float:
        """Get the strength of the action (0.0 to 1.0)"""
        if self.is_pressed(pressed_keys, mouse_buttons, modifiers):
            return 1.0
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "events": [event.to_dict() for event in self.events],
            "deadzone": self.deadzone
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InputAction':
        """Create from dictionary"""
        events = [InputEvent.from_dict(event_data) for event_data in data.get("events", [])]
        return cls(
            name=data["name"],
            events=events,
            deadzone=data.get("deadzone", 0.2)
        )

class InputManager:
    """Manages input actions and input state"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path
        self.actions: Dict[str, InputAction] = {}
        
        # Current input state
        self.pressed_keys: Set[int] = set()
        self.mouse_buttons: Set[int] = set()
        self.mouse_position: Tuple[float, float] = (0.0, 0.0)
        self.current_modifiers: Set[str] = set()
        
        # Input state tracking for "just pressed/released"
        self.previous_keys: Set[int] = set()
        self.previous_mouse_buttons: Set[int] = set()
        self.previous_actions: Set[str] = set()
        self.current_actions: Set[str] = set()
        
        # Load default actions
        self._load_default_actions()
        
        # Load project-specific actions if available
        if self.project_path:
            self.load_actions()
    
    def _load_default_actions(self):
        """Load default input actions"""
        default_actions = [
            InputAction("ui_accept", [
                InputEvent("key", KEY_ENTER),
                InputEvent("key", KEY_SPACE),
                InputEvent("key", KEY_KP_ENTER)
            ]),
            InputAction("ui_cancel", [
                InputEvent("key", KEY_ESCAPE)
            ]),
            InputAction("ui_left", [
                InputEvent("key", KEY_LEFT),
                InputEvent("key", KEY_A)
            ]),
            InputAction("ui_right", [
                InputEvent("key", KEY_RIGHT),
                InputEvent("key", KEY_D)
            ]),
            InputAction("ui_up", [
                InputEvent("key", KEY_UP),
                InputEvent("key", KEY_W)
            ]),
            InputAction("ui_down", [
                InputEvent("key", KEY_DOWN),
                InputEvent("key", KEY_S)
            ]),
            InputAction("move_left", [
                InputEvent("key", KEY_LEFT),
                InputEvent("key", KEY_A)
            ]),
            InputAction("move_right", [
                InputEvent("key", KEY_RIGHT),
                InputEvent("key", KEY_D)
            ]),
            InputAction("move_up", [
                InputEvent("key", KEY_UP),
                InputEvent("key", KEY_W)
            ]),
            InputAction("move_down", [
                InputEvent("key", KEY_DOWN),
                InputEvent("key", KEY_S)
            ]),
            InputAction("jump", [
                InputEvent("key", KEY_SPACE)
            ]),
            InputAction("interact", [
                InputEvent("key", KEY_E),
                InputEvent("key", KEY_ENTER)
            ]),
            InputAction("run", [
                InputEvent("key", KEY_SHIFT)
            ]),
            InputAction("pause", [
                InputEvent("key", KEY_ESCAPE),
                InputEvent("key", KEY_P)
            ])
        ]
        
        for action in default_actions:
            self.actions[action.name] = action
    
    def update_input_state(self, pressed_keys: Set[int], mouse_buttons: Set[int], 
                          mouse_pos: Tuple[float, float], modifiers: Set[str]):
        """Update the current input state"""
        # Store previous state
        self.previous_keys = self.pressed_keys.copy()
        self.previous_mouse_buttons = self.mouse_buttons.copy()
        self.previous_actions = self.current_actions.copy()
        
        # Update current state
        self.pressed_keys = pressed_keys.copy()
        self.mouse_buttons = mouse_buttons.copy()
        self.mouse_position = mouse_pos
        self.current_modifiers = modifiers.copy()
        
        # Update current actions
        self.current_actions = set()
        for action_name, action in self.actions.items():
            if action.is_pressed(self.pressed_keys, self.mouse_buttons, self.current_modifiers):
                self.current_actions.add(action_name)
    
    def is_action_pressed(self, action_name: str) -> bool:
        """Check if an action is currently pressed"""
        return action_name in self.current_actions
    
    def is_action_just_pressed(self, action_name: str) -> bool:
        """Check if an action was just pressed this frame"""
        return action_name in self.current_actions and action_name not in self.previous_actions
    
    def is_action_just_released(self, action_name: str) -> bool:
        """Check if an action was just released this frame"""
        return action_name not in self.current_actions and action_name in self.previous_actions
    
    def get_action_strength(self, action_name: str) -> float:
        """Get the strength of an action (0.0 to 1.0)"""
        action = self.actions.get(action_name)
        if action:
            return action.get_strength(self.pressed_keys, self.mouse_buttons, self.current_modifiers)
        return 0.0
    
    def is_key_pressed(self, key_code: int) -> bool:
        """Check if a specific key is pressed"""
        return key_code in self.pressed_keys
    
    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if a specific mouse button is pressed"""
        return button in self.mouse_buttons
    
    def get_mouse_position(self) -> Tuple[float, float]:
        """Get current mouse position"""
        return self.mouse_position
    
    def get_global_mouse_position(self) -> Tuple[float, float]:
        """Get global mouse position (same as get_mouse_position for now)"""
        return self.mouse_position
    
    def add_action(self, action: InputAction):
        """Add or update an input action"""
        self.actions[action.name] = action
    
    def remove_action(self, action_name: str):
        """Remove an input action"""
        if action_name in self.actions:
            del self.actions[action_name]
    
    def get_action(self, action_name: str) -> Optional[InputAction]:
        """Get an input action by name"""
        return self.actions.get(action_name)
    
    def get_all_actions(self) -> Dict[str, InputAction]:
        """Get all input actions"""
        return self.actions.copy()
    
    def save_actions(self):
        """Save actions to project file"""
        if not self.project_path:
            return
        
        input_map_file = self.project_path / "input_map.json"
        
        # Convert actions to serializable format
        actions_data = {}
        for name, action in self.actions.items():
            actions_data[name] = action.to_dict()
        
        try:
            with open(input_map_file, 'w') as f:
                json.dump(actions_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save input actions: {e}")
    
    def load_actions(self):
        """Load actions from project file"""
        if not self.project_path:
            return
        
        input_map_file = self.project_path / "input_map.json"
        
        if not input_map_file.exists():
            return
        
        try:
            with open(input_map_file, 'r') as f:
                actions_data = json.load(f)
            
            # Load actions from data
            for name, action_data in actions_data.items():
                action = InputAction.from_dict(action_data)
                self.actions[name] = action
                
        except Exception as e:
            print(f"Failed to load input actions: {e}")
