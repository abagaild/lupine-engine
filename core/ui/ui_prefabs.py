"""
UI Prefab Definitions for Lupine Engine
Defines built-in UI prefabs for the Menu and HUD Builder
"""

from typing import Dict, Any, List, Optional
from enum import Enum


class PrefabCategory(Enum):
    """Categories for UI prefabs"""
    BUTTONS = "Buttons"
    DISPLAYS = "Displays"
    BARS = "Progress Bars"
    CONTAINERS = "Containers"
    INPUT = "Input"
    LAYOUT = "Layout"
    CUSTOM = "Custom"


class UIPrefab:
    """Represents a UI prefab with configuration and default properties"""
    
    def __init__(self, name: str, category: PrefabCategory, description: str,
                 base_node_type: str, default_properties: Dict[str, Any],
                 prefab_settings: Optional[Dict[str, Any]] = None,
                 variable_bindings: Optional[List[str]] = None,
                 event_bindings: Optional[List[str]] = None):
        self.name = name
        self.category = category
        self.description = description
        self.base_node_type = base_node_type
        self.default_properties = default_properties
        self.prefab_settings = prefab_settings or {}
        self.variable_bindings = variable_bindings or []
        self.event_bindings = event_bindings or []
    
    def create_instance(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a node instance from this prefab"""
        instance_name = name or self.name
        
        # Start with base node structure
        instance = {
            "name": instance_name,
            "type": self.base_node_type,
            "children": [],
            "prefab_type": self.name,
            "prefab_settings": self.prefab_settings.copy()
        }
        
        # Apply default properties
        instance.update(self.default_properties)
        
        return instance


# Built-in UI Prefabs
BUILTIN_PREFABS = {
    # BUTTONS
    "SimpleButton": UIPrefab(
        name="SimpleButton",
        category=PrefabCategory.BUTTONS,
        description="Basic button with text and click handling",
        base_node_type="Button",
        default_properties={
            "text": "Button",
            "size": [120, 40],
            "bg_color": [0.3, 0.3, 0.3, 1.0],
            "border_width": 2.0,
            "border_color": [0.6, 0.6, 0.6, 1.0],
            "corner_radius": 4.0,
            "font_size": 14
        },
        prefab_settings={
            "default_on_click": "print('Button clicked!')",
            "hover_sound": "",
            "click_sound": "",
            "enable_condition": ""
        },
        event_bindings=["on_click", "on_hover", "on_release"]
    ),
    
    "MenuButton": UIPrefab(
        name="MenuButton",
        category=PrefabCategory.BUTTONS,
        description="Styled menu button with hover effects",
        base_node_type="Button",
        default_properties={
            "text": "Menu Item",
            "size": [200, 50],
            "bg_color": [0.2, 0.2, 0.2, 0.8],
            "bg_color_hover": [0.3, 0.3, 0.3, 0.9],
            "border_width": 1.0,
            "border_color": [0.5, 0.5, 0.5, 1.0],
            "corner_radius": 8.0,
            "font_size": 16,
            "font_color": [1.0, 1.0, 1.0, 1.0]
        },
        prefab_settings={
            "default_on_click": "# Menu navigation code here",
            "hover_sound": "ui_hover.wav",
            "click_sound": "ui_click.wav",
            "enable_condition": ""
        },
        event_bindings=["on_click", "on_hover", "on_release"]
    ),
    
    # DISPLAYS
    "HealthDisplay": UIPrefab(
        name="HealthDisplay",
        category=PrefabCategory.DISPLAYS,
        description="Health display with icon and text",
        base_node_type="Panel",
        default_properties={
            "size": [150, 30],
            "bg_color": [0.1, 0.1, 0.1, 0.8],
            "border_width": 1.0,
            "corner_radius": 4.0
        },
        prefab_settings={
            "health_variable": "player_health",
            "max_health_variable": "player_max_health",
            "display_format": "{current}/{max}",
            "icon_path": "icons/heart.png",
            "low_health_threshold": 0.25,
            "low_health_color": [1.0, 0.2, 0.2, 1.0]
        },
        variable_bindings=["health_variable", "max_health_variable"]
    ),
    
    "ScoreDisplay": UIPrefab(
        name="ScoreDisplay",
        category=PrefabCategory.DISPLAYS,
        description="Score display with label and value",
        base_node_type="Label",
        default_properties={
            "text": "Score: 0",
            "size": [120, 25],
            "font_size": 16,
            "font_color": [1.0, 1.0, 1.0, 1.0],
            "text_align": "left"
        },
        prefab_settings={
            "score_variable": "player_score",
            "display_format": "Score: {value}",
            "number_format": "0"
        },
        variable_bindings=["score_variable"]
    ),
    
    # PROGRESS BARS
    "HealthBar": UIPrefab(
        name="HealthBar",
        category=PrefabCategory.BARS,
        description="Health progress bar with customizable colors",
        base_node_type="ProgressBar",
        default_properties={
            "size": [200, 20],
            "min_value": 0.0,
            "max_value": 100.0,
            "value": 100.0,
            "fill_color": [0.2, 0.8, 0.2, 1.0],
            "bg_color": [0.2, 0.2, 0.2, 0.8],
            "border_width": 1.0,
            "border_color": [0.5, 0.5, 0.5, 1.0]
        },
        prefab_settings={
            "health_variable": "player_health",
            "max_health_variable": "player_max_health",
            "low_health_color": [0.8, 0.2, 0.2, 1.0],
            "medium_health_color": [0.8, 0.8, 0.2, 1.0],
            "high_health_color": [0.2, 0.8, 0.2, 1.0],
            "low_threshold": 0.25,
            "medium_threshold": 0.5,
            "animate_changes": True
        },
        variable_bindings=["health_variable", "max_health_variable"]
    ),
    
    "ExperienceBar": UIPrefab(
        name="ExperienceBar",
        category=PrefabCategory.BARS,
        description="Experience/XP progress bar",
        base_node_type="ProgressBar",
        default_properties={
            "size": [300, 15],
            "min_value": 0.0,
            "max_value": 100.0,
            "value": 0.0,
            "fill_color": [0.2, 0.2, 0.8, 1.0],
            "bg_color": [0.1, 0.1, 0.1, 0.8],
            "border_width": 1.0
        },
        prefab_settings={
            "xp_variable": "player_xp",
            "xp_max_variable": "player_xp_max",
            "show_text": True,
            "text_format": "{current}/{max} XP",
            "animate_changes": True
        },
        variable_bindings=["xp_variable", "xp_max_variable"]
    ),
    
    # CONTAINERS
    "DialogueBox": UIPrefab(
        name="DialogueBox",
        category=PrefabCategory.CONTAINERS,
        description="Dialogue box with text and speaker name",
        base_node_type="Panel",
        default_properties={
            "size": [600, 150],
            "position": [50, 400],
            "bg_color": [0.1, 0.1, 0.1, 0.9],
            "border_width": 2.0,
            "border_color": [0.6, 0.6, 0.6, 1.0],
            "corner_radius": 8.0
        },
        prefab_settings={
            "speaker_variable": "dialogue_speaker",
            "text_variable": "dialogue_text",
            "auto_advance": False,
            "advance_delay": 3.0,
            "typewriter_effect": True,
            "typewriter_speed": 0.05
        },
        variable_bindings=["speaker_variable", "text_variable"]
    ),
    
    "InventorySlot": UIPrefab(
        name="InventorySlot",
        category=PrefabCategory.CONTAINERS,
        description="Inventory slot for items",
        base_node_type="Button",
        default_properties={
            "size": [64, 64],
            "bg_color": [0.2, 0.2, 0.2, 0.8],
            "border_width": 2.0,
            "border_color": [0.4, 0.4, 0.4, 1.0],
            "corner_radius": 4.0
        },
        prefab_settings={
            "item_variable": "",
            "slot_index": 0,
            "show_quantity": True,
            "empty_texture": "ui/empty_slot.png",
            "highlight_on_hover": True
        },
        variable_bindings=["item_variable"],
        event_bindings=["on_click", "on_hover", "on_drag"]
    ),

    # INPUT CONTROLS
    "TextInput": UIPrefab(
        name="TextInput",
        category=PrefabCategory.INPUT,
        description="Text input field with validation",
        base_node_type="LineEdit",
        default_properties={
            "size": [200, 30],
            "text": "",
            "placeholder_text": "Enter text...",
            "bg_color": [0.1, 0.1, 0.1, 0.9],
            "border_width": 1.0,
            "border_color": [0.5, 0.5, 0.5, 1.0],
            "font_size": 12
        },
        prefab_settings={
            "max_length": 100,
            "validation_pattern": "",
            "auto_save_variable": "",
            "clear_on_submit": False
        },
        variable_bindings=["auto_save_variable"],
        event_bindings=["on_text_changed", "on_submit", "on_focus", "on_blur"]
    ),

    "Slider": UIPrefab(
        name="Slider",
        category=PrefabCategory.INPUT,
        description="Value slider with customizable range",
        base_node_type="HSlider",
        default_properties={
            "size": [200, 20],
            "min_value": 0.0,
            "max_value": 100.0,
            "value": 50.0,
            "step": 1.0
        },
        prefab_settings={
            "bound_variable": "",
            "show_value": True,
            "value_format": "{value:.0f}",
            "live_update": True
        },
        variable_bindings=["bound_variable"],
        event_bindings=["on_value_changed", "on_drag_started", "on_drag_ended"]
    ),

    # LAYOUT CONTAINERS
    "HorizontalContainer": UIPrefab(
        name="HorizontalContainer",
        category=PrefabCategory.LAYOUT,
        description="Horizontal layout container",
        base_node_type="HBoxContainer",
        default_properties={
            "size": [300, 50],
            "separation": 10,
            "alignment": "center"
        },
        prefab_settings={
            "auto_resize": True,
            "equal_spacing": False,
            "padding": 5
        }
    ),

    "VerticalContainer": UIPrefab(
        name="VerticalContainer",
        category=PrefabCategory.LAYOUT,
        description="Vertical layout container",
        base_node_type="VBoxContainer",
        default_properties={
            "size": [100, 300],
            "separation": 10,
            "alignment": "center"
        },
        prefab_settings={
            "auto_resize": True,
            "equal_spacing": False,
            "padding": 5
        }
    ),

    "GridContainer": UIPrefab(
        name="GridContainer",
        category=PrefabCategory.LAYOUT,
        description="Grid layout container",
        base_node_type="GridContainer",
        default_properties={
            "size": [300, 200],
            "columns": 3,
            "separation": [10, 10]
        },
        prefab_settings={
            "auto_resize": True,
            "equal_cell_size": False
        }
    ),

    # DISPLAY ELEMENTS
    "ImageDisplay": UIPrefab(
        name="ImageDisplay",
        category=PrefabCategory.DISPLAYS,
        description="Image display with texture binding",
        base_node_type="TextureRect",
        default_properties={
            "size": [100, 100],
            "texture": "",
            "stretch_mode": "keep_aspect_centered"
        },
        prefab_settings={
            "texture_variable": "",
            "fallback_texture": "ui/missing_image.png",
            "auto_size": False
        },
        variable_bindings=["texture_variable"]
    ),

    "StatusIcon": UIPrefab(
        name="StatusIcon",
        category=PrefabCategory.DISPLAYS,
        description="Status icon that changes based on conditions",
        base_node_type="TextureRect",
        default_properties={
            "size": [32, 32],
            "texture": "ui/status_normal.png"
        },
        prefab_settings={
            "status_variable": "",
            "normal_texture": "ui/status_normal.png",
            "warning_texture": "ui/status_warning.png",
            "error_texture": "ui/status_error.png",
            "warning_threshold": 0.3,
            "error_threshold": 0.1
        },
        variable_bindings=["status_variable"]
    ),

    "Timer": UIPrefab(
        name="Timer",
        category=PrefabCategory.DISPLAYS,
        description="Timer display with countdown/countup",
        base_node_type="Label",
        default_properties={
            "text": "00:00",
            "size": [80, 25],
            "font_size": 16,
            "font_color": [1.0, 1.0, 1.0, 1.0],
            "text_align": "center"
        },
        prefab_settings={
            "time_variable": "",
            "format": "mm:ss",
            "countdown": True,
            "show_milliseconds": False,
            "warning_time": 10.0,
            "warning_color": [1.0, 0.5, 0.0, 1.0]
        },
        variable_bindings=["time_variable"]
    )
}


def get_prefabs_by_category(category: PrefabCategory) -> List[UIPrefab]:
    """Get all prefabs in a specific category"""
    return [prefab for prefab in BUILTIN_PREFABS.values() if prefab.category == category]


def get_all_categories() -> List[PrefabCategory]:
    """Get all available prefab categories"""
    return list(PrefabCategory)


def get_prefab(name: str) -> Optional[UIPrefab]:
    """Get a prefab by name"""
    return BUILTIN_PREFABS.get(name)


# Animation presets for UI elements
UI_ANIMATION_PRESETS = {
    "bounce": {
        "name": "Bounce",
        "description": "Bounce scale animation for feedback",
        "duration": 0.5,
        "properties": {
            "scale": {
                "keyframes": [
                    {"time": 0.0, "value": [1.0, 1.0]},
                    {"time": 0.3, "value": [1.2, 1.2]},
                    {"time": 0.6, "value": [0.9, 0.9]},
                    {"time": 1.0, "value": [1.0, 1.0]}
                ]
            }
        }
    },

    "fade_in": {
        "name": "Fade In",
        "description": "Fade in from transparent to opaque",
        "duration": 1.0,
        "properties": {
            "modulate": {
                "keyframes": [
                    {"time": 0.0, "value": [1.0, 1.0, 1.0, 0.0]},
                    {"time": 1.0, "value": [1.0, 1.0, 1.0, 1.0]}
                ]
            }
        }
    },

    "fade_out": {
        "name": "Fade Out",
        "description": "Fade out from opaque to transparent",
        "duration": 1.0,
        "properties": {
            "modulate": {
                "keyframes": [
                    {"time": 0.0, "value": [1.0, 1.0, 1.0, 1.0]},
                    {"time": 1.0, "value": [1.0, 1.0, 1.0, 0.0]}
                ]
            }
        }
    },

    "pulse": {
        "name": "Pulse",
        "description": "Pulsing alpha animation",
        "duration": 2.0,
        "loop": True,
        "properties": {
            "modulate": {
                "keyframes": [
                    {"time": 0.0, "value": [1.0, 1.0, 1.0, 1.0]},
                    {"time": 1.0, "value": [1.0, 1.0, 1.0, 0.3]},
                    {"time": 2.0, "value": [1.0, 1.0, 1.0, 1.0]}
                ]
            }
        }
    },

    "slide_in_left": {
        "name": "Slide In Left",
        "description": "Slide in from the left side",
        "duration": 0.8,
        "properties": {
            "position": {
                "keyframes": [
                    {"time": 0.0, "value": [-200.0, 0.0]},
                    {"time": 1.0, "value": [0.0, 0.0]}
                ]
            }
        }
    },

    "slide_in_right": {
        "name": "Slide In Right",
        "description": "Slide in from the right side",
        "duration": 0.8,
        "properties": {
            "position": {
                "keyframes": [
                    {"time": 0.0, "value": [200.0, 0.0]},
                    {"time": 1.0, "value": [0.0, 0.0]}
                ]
            }
        }
    },

    "slide_in_top": {
        "name": "Slide In Top",
        "description": "Slide in from the top",
        "duration": 0.8,
        "properties": {
            "position": {
                "keyframes": [
                    {"time": 0.0, "value": [0.0, -200.0]},
                    {"time": 1.0, "value": [0.0, 0.0]}
                ]
            }
        }
    },

    "slide_in_bottom": {
        "name": "Slide In Bottom",
        "description": "Slide in from the bottom",
        "duration": 0.8,
        "properties": {
            "position": {
                "keyframes": [
                    {"time": 0.0, "value": [0.0, 200.0]},
                    {"time": 1.0, "value": [0.0, 0.0]}
                ]
            }
        }
    },

    "scale_up": {
        "name": "Scale Up",
        "description": "Scale up from small to normal size",
        "duration": 0.6,
        "properties": {
            "scale": {
                "keyframes": [
                    {"time": 0.0, "value": [0.0, 0.0]},
                    {"time": 1.0, "value": [1.0, 1.0]}
                ]
            }
        }
    },

    "scale_down": {
        "name": "Scale Down",
        "description": "Scale down from normal to small size",
        "duration": 0.6,
        "properties": {
            "scale": {
                "keyframes": [
                    {"time": 0.0, "value": [1.0, 1.0]},
                    {"time": 1.0, "value": [0.0, 0.0]}
                ]
            }
        }
    },

    "shake": {
        "name": "Shake",
        "description": "Shake animation for attention",
        "duration": 0.5,
        "properties": {
            "position": {
                "keyframes": [
                    {"time": 0.0, "value": [0.0, 0.0]},
                    {"time": 0.1, "value": [5.0, 0.0]},
                    {"time": 0.2, "value": [-5.0, 0.0]},
                    {"time": 0.3, "value": [3.0, 0.0]},
                    {"time": 0.4, "value": [-3.0, 0.0]},
                    {"time": 0.5, "value": [0.0, 0.0]}
                ]
            }
        }
    },

    "glow": {
        "name": "Glow",
        "description": "Glowing color animation",
        "duration": 1.5,
        "loop": True,
        "properties": {
            "modulate": {
                "keyframes": [
                    {"time": 0.0, "value": [1.0, 1.0, 1.0, 1.0]},
                    {"time": 0.75, "value": [1.5, 1.5, 1.0, 1.0]},
                    {"time": 1.5, "value": [1.0, 1.0, 1.0, 1.0]}
                ]
            }
        }
    }
}


def get_ui_animation_presets() -> Dict[str, Dict]:
    """Get all available UI animation presets"""
    return UI_ANIMATION_PRESETS


def get_ui_animation_preset(name: str) -> Optional[Dict]:
    """Get a specific UI animation preset by name"""
    return UI_ANIMATION_PRESETS.get(name)


def get_ui_animation_preset_names() -> List[str]:
    """Get list of all UI animation preset names"""
    return list(UI_ANIMATION_PRESETS.keys())
