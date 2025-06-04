"""
Light2D node implementation for Lupine Engine
Emits 2D light affecting Canvas and CanvasItems
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List


class Light2D(Node2D):
    """
    Light2D: Emits a 2D light mask that affects shaders or CanvasModulate.
    Supports shadows (stubbed), range, energy, and blend modes.
    """

    def __init__(self, name: str = "Light2D"):
        super().__init__(name)
        self.type = "Light2D"

        # Export variables for editor
        self.export_variables = {
            "texture": {
                "type": "path",
                "value": "",
                "filter": "*.png,*.jpg,*.jpeg",
                "description": "Light texture (white mask → full light)"
            },
            "color": {
                "type": "color",
                "value": [1.0, 1.0, 1.0, 1.0],
                "description": "Tint color for the light"
            },
            "energy": {
                "type": "float",
                "value": 1.0,
                "description": "Brightness multiplier"
            },
            "mode": {
                "type": "enum",
                "value": "Additive",
                "options": ["Additive", "Subtractive", "Mix"],
                "description": "Blend mode"
            },
            "height": {
                "type": "float",
                "value": 0.0,
                "description": "Z-depth for shadow layering"
            },
            "range": {
                "type": "float",
                "value": 200.0,
                "description": "How far the light reaches (in pixels)"
            },
            "shadow_enabled": {
                "type": "bool",
                "value": False,
                "description": "Enable shadow casting"
            },
            "shadow_buffer_size": {
                "type": "int",
                "value": 256,
                "description": "Resolution for shadow map"
            },
            "shadow_smooth": {
                "type": "float",
                "value": 0.0,
                "description": "Blur radius for soft shadows"
            },
            "shadow_color": {
                "type": "color",
                "value": [0.0, 0.0, 0.0, 1.0],
                "description": "Color of shadowed areas"
            }
        }

        # Core properties
        self.texture: str = ""
        self.color: List[float] = [1.0, 1.0, 1.0, 1.0]
        self.energy: float = 1.0
        self.mode: str = "Additive"
        self.height: float = 0.0
        self.range: float = 200.0
        self.shadow_enabled: bool = False
        self.shadow_buffer_size: int = 256
        self.shadow_smooth: float = 0.0
        self.shadow_color: List[float] = [0.0, 0.0, 0.0, 1.0]

        # Runtime shadow offset (stubbed)
        self._shadow_offset: List[float] = [0.0, 0.0]

        # Built-in signals
        self.add_signal("light_entered")
        self.add_signal("light_exited")

    def set_texture(self, path: str):
        """Set the light’s mask texture path (loads at runtime)."""
        self.texture = path
        # In a full implementation, load the texture and generate mask

    def set_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Set the light color"""
        self.color = [r, g, b, a]

    def get_color(self) -> List[float]:
        """Get the light color"""
        return self.color.copy()

    def set_energy(self, energy: float):
        """Set the light energy/intensity"""
        self.energy = max(0.0, energy)

    def get_energy(self) -> float:
        """Get the light energy/intensity"""
        return self.energy

    def set_range(self, range_value: float):
        """Set the light range"""
        self.range = max(0.0, range_value)

    def get_range(self) -> float:
        """Get the light range"""
        return self.range

    def set_mode(self, mode: str):
        """Set the light blend mode"""
        valid_modes = ["Additive", "Subtractive", "Mix"]
        if mode in valid_modes:
            self.mode = mode
        else:
            print(f"Warning: Invalid Light2D mode '{mode}'. Valid modes: {valid_modes}")

    def get_mode(self) -> str:
        """Get the light blend mode"""
        return self.mode

    def set_shadow_enabled(self, enabled: bool):
        """Enable or disable shadow casting"""
        self.shadow_enabled = enabled

    def is_shadow_enabled(self) -> bool:
        """Check if shadow casting is enabled"""
        return self.shadow_enabled

    def set_shadow_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Set the shadow color"""
        self.shadow_color = [r, g, b, a]

    def get_shadow_color(self) -> List[float]:
        """Get the shadow color"""
        return self.shadow_color.copy()

    def get_light_mask_rect(self) -> List[float]:
        """Get the rectangle that encompasses the light's effect"""
        # Calculate the bounding rectangle for the light effect
        x = self.position[0] - self.range
        y = self.position[1] - self.range
        width = self.range * 2
        height = self.range * 2
        return [x, y, width, height]

    def is_position_in_light(self, pos: List[float]) -> bool:
        """Check if a position is within the light's range"""
        dx = pos[0] - self.position[0]
        dy = pos[1] - self.position[1]
        distance_squared = dx * dx + dy * dy
        return distance_squared <= (self.range * self.range)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Light2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "texture": self.texture,
            "color": self.color.copy(),
            "energy": self.energy,
            "mode": self.mode,
            "height": self.height,
            "range": self.range,
            "shadow_enabled": self.shadow_enabled,
            "shadow_buffer_size": self.shadow_buffer_size,
            "shadow_smooth": self.shadow_smooth,
            "shadow_color": self.shadow_color.copy()
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Light2D":
        """Deserialize a Light2D from a dictionary."""
        light = cls(data.get("name", "Light2D"))
        cls._apply_node_properties(light, data)

        light.texture = data.get("texture", "")
        light.color = data.get("color", [1.0, 1.0, 1.0, 1.0])
        light.energy = data.get("energy", 1.0)
        light.mode = data.get("mode", "Additive")
        light.height = data.get("height", 0.0)
        light.range = data.get("range", 200.0)
        light.shadow_enabled = data.get("shadow_enabled", False)
        light.shadow_buffer_size = data.get("shadow_buffer_size", 256)
        light.shadow_smooth = data.get("shadow_smooth", 0.0)
        light.shadow_color = data.get("shadow_color", [0.0, 0.0, 0.0, 1.0])

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            light.add_child(child)
        return light
