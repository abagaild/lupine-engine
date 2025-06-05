"""
TileMap node implementation for Lupine Engine
Grid of tiles with tileset, collision layers, and batch rendering
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional, Union


class TileMap(Node2D):
    """
    TileMap for painting tiles on a grid.
    
    Features:
    - Tileset reference
    - Cell size and origin
    - Per-cell tile index storage
    - Collision layer/mask
    - Modulate and opacity
    """

    def __init__(self, name: str = "TileMap"):
        super().__init__(name)
        self.type = "TileMap"

        # Export variables for editor
        self.export_variables = {
            "tileset": {
                "type": "path",
                "value": "",
                "filter": "*.tres,*.json",
                "description": "Path to TileSet resource"
            },
            "cell_size": {
                "type": "vector2",
                "value": [32.0, 32.0],
                "description": "Width/height of a single tile"
            },
            "cell_origin": {
                "type": "enum",
                "value": "TopLeft",
                "options": ["TopLeft", "Center"],
                "description": "Origin point of the grid"
            },
            "mode": {
                "type": "enum",
                "value": "Square",
                "options": ["Square", "Hexagonal", "Isometric"],
                "description": "Tilemap drawing mode"
            },
            "modulate": {
                "type": "color",
                "value": [1.0, 1.0, 1.0, 1.0],
                "description": "Color modulation for the entire TileMap"
            },
            "opacity": {
                "type": "float",
                "value": 1.0,
                "min": 0.0,
                "max": 1.0,
                "description": "Opacity for the entire TileMap"
            },
            "collision_layer": {
                "type": "int",
                "value": 1,
                "description": "Physics layer this TileMap occupies"
            },
            "collision_mask": {
                "type": "int",
                "value": 1,
                "description": "Which layers this TileMap collides with"
            },
            "one_way_collision_enabled": {
                "type": "bool",
                "value": False,
                "description": "Enable one-way collisions (like platforms)"
            },
            "one_way_collision_margin": {
                "type": "float",
                "value": 0.0,
                "description": "Margin for one-way collision"
            }
        }

        # Core properties
        self.tileset: str = ""
        self.cell_size: List[float] = [32.0, 32.0]
        self.cell_origin: str = "TopLeft"
        self.mode: str = "Square"
        self.modulate: List[float] = [1.0, 1.0, 1.0, 1.0]
        self.opacity: float = 1.0
        self.collision_layer: int = 1
        self.collision_mask: int = 1
        self.one_way_collision_enabled: bool = False
        self.one_way_collision_margin: float = 0.0

        # Layer system - support up to 20 layers
        self.layers: List[Dict[str, Any]] = []
        self.current_layer: int = 0
        self.max_layers: int = 20

        # Multiple tileset support
        self.tilesets: List[str] = []  # List of tileset paths

        # Map size configuration
        self.map_size_mode: str = "infinite"  # "infinite" or "fixed"
        self.fixed_map_size: List[int] = [100, 100]  # width, height in tiles

        # Internal tile data: mapping (layer, x, y) → tile data
        self._tiles: Dict[str, Dict[str, Any]] = {}  # e.g. {"0": {"0,0": {"tileset": 0, "tile_id": 5}}}

        # Initialize with one default layer (after _tiles is created)
        self.add_layer("Layer 0")

        # Built-in signals
        self.add_signal("tiles_changed")
        self.add_signal("layer_changed")

    # Layer management
    def add_layer(self, name: Optional[str] = None) -> int:
        """Add a new layer and return its index"""
        if len(self.layers) >= self.max_layers:
            return -1

        layer_index = len(self.layers)
        if name is None:
            name = f"Layer {layer_index}"

        layer_data = {
            "name": name,
            "visible": True,
            "opacity": 1.0,
            "z_index": layer_index
        }

        self.layers.append(layer_data)
        self._tiles[str(layer_index)] = {}

        self.emit_signal("layer_changed", layer_index, "added")
        return layer_index

    def remove_layer(self, layer_index: int) -> bool:
        """Remove a layer"""
        if not (0 <= layer_index < len(self.layers)):
            return False

        # Don't allow removing the last layer
        if len(self.layers) <= 1:
            return False

        # Remove layer data
        del self.layers[layer_index]
        if str(layer_index) in self._tiles:
            del self._tiles[str(layer_index)]

        # Adjust current layer if needed
        if self.current_layer >= len(self.layers):
            self.current_layer = len(self.layers) - 1

        # Reindex remaining layers
        new_tiles = {}
        for i, layer in enumerate(self.layers):
            old_key = str(i + 1 if i >= layer_index else i)
            if old_key in self._tiles:
                new_tiles[str(i)] = self._tiles[old_key]
        self._tiles = new_tiles

        self.emit_signal("layer_changed", layer_index, "removed")
        return True

    def set_layer_property(self, layer_index: int, property_name: str, value: Any):
        """Set a layer property"""
        if 0 <= layer_index < len(self.layers):
            self.layers[layer_index][property_name] = value
            self.emit_signal("layer_changed", layer_index, "modified")

    # Tileset management
    def add_tileset(self, tileset_path: str) -> int:
        """Add a tileset and return its index"""
        if tileset_path not in self.tilesets:
            self.tilesets.append(tileset_path)
        return self.tilesets.index(tileset_path)

    def remove_tileset(self, tileset_index: int) -> bool:
        """Remove a tileset"""
        if 0 <= tileset_index < len(self.tilesets):
            del self.tilesets[tileset_index]
            # TODO: Update tiles that reference this tileset
            return True
        return False

    # Tile editing API (updated for layers)
    def set_tile(self, x: int, y: int, tile_data: Optional[Dict[str, Any]], layer: Optional[int] = None):
        """Assign tile data at grid cell (x, y) on specified layer."""
        if layer is None:
            layer = self.current_layer

        layer_key = str(layer)
        if layer_key not in self._tiles:
            return

        pos_key = f"{x},{y}"
        old_data = self._tiles[layer_key].get(pos_key, None)

        if tile_data is None or tile_data.get("tile_id", -1) < 0:
            # Remove tile
            if pos_key in self._tiles[layer_key]:
                del self._tiles[layer_key][pos_key]
        else:
            self._tiles[layer_key][pos_key] = tile_data

        self.emit_signal("tiles_changed", x, y, layer, old_data, tile_data)

    def get_tile(self, x: int, y: int, layer: Optional[int] = None) -> Dict[str, Any]:
        """Retrieve tile data at (x, y) on specified layer."""
        if layer is None:
            layer = self.current_layer

        layer_key = str(layer)
        if layer_key not in self._tiles:
            return {}

        return self._tiles[layer_key].get(f"{x},{y}", {})

    def clear_tile(self, x: int, y: int, layer: Optional[int] = None):
        """Remove any tile at (x, y) on specified layer."""
        self.set_tile(x, y, None, layer)

    def clear_layer(self, layer: Optional[int] = None):
        """Remove all tiles from specified layer."""
        if layer is None:
            layer = self.current_layer

        layer_key = str(layer)
        if layer_key in self._tiles:
            self._tiles[layer_key].clear()
            self.emit_signal("tiles_changed", None, None, layer, None, None)

    def clear_all(self):
        """Remove all tiles from all layers."""
        for layer_key in self._tiles:
            self._tiles[layer_key].clear()
        self.emit_signal("tiles_changed", None, None, None, None, None)

    # Utility methods for tile manipulation
    def get_used_cells(self, layer: Optional[int] = None) -> List[List[int]]:
        """Get a list of all cells that have tiles on specified layer"""
        if layer is None:
            layer = self.current_layer

        layer_key = str(layer)
        if layer_key not in self._tiles:
            return []

        cells = []
        for key in self._tiles[layer_key].keys():
            x, y = map(int, key.split(','))
            cells.append([x, y])
        return cells

    def get_used_rect(self, layer: Optional[int] = None) -> List[int]:
        """Get the rectangle that encompasses all used tiles on specified layer"""
        cells = self.get_used_cells(layer)
        if not cells:
            return [0, 0, 0, 0]

        min_x = min(cell[0] for cell in cells)
        max_x = max(cell[0] for cell in cells)
        min_y = min(cell[1] for cell in cells)
        max_y = max(cell[1] for cell in cells)

        return [min_x, min_y, max_x - min_x + 1, max_y - min_y + 1]

    def get_all_used_cells(self) -> Dict[int, List[List[int]]]:
        """Get used cells for all layers"""
        result = {}
        for layer_index in range(len(self.layers)):
            result[layer_index] = self.get_used_cells(layer_index)
        return result

    def world_to_map(self, world_pos: List[float]) -> List[int]:
        """Convert world position to map coordinates"""
        # Adjust for node position
        local_x = world_pos[0] - self.position[0]
        local_y = world_pos[1] - self.position[1]

        # Convert to tile coordinates
        tile_x = int(local_x // self.cell_size[0])
        tile_y = int(local_y // self.cell_size[1])

        return [tile_x, tile_y]

    def map_to_world(self, map_pos: List[int]) -> List[float]:
        """Convert map coordinates to world position"""
        # Calculate world position based on cell origin
        if self.cell_origin == "Center":
            world_x = map_pos[0] * self.cell_size[0] + self.cell_size[0] / 2
            world_y = map_pos[1] * self.cell_size[1] + self.cell_size[1] / 2
        else:  # TopLeft
            world_x = map_pos[0] * self.cell_size[0]
            world_y = map_pos[1] * self.cell_size[1]

        # Adjust for node position
        world_x += self.position[0]
        world_y += self.position[1]

        return [world_x, world_y]

    def get_cell_rect(self, x: int, y: int) -> List[float]:
        """Get the world rectangle for a specific cell"""
        world_pos = self.map_to_world([x, y])

        if self.cell_origin == "Center":
            rect_x = world_pos[0] - self.cell_size[0] / 2
            rect_y = world_pos[1] - self.cell_size[1] / 2
        else:  # TopLeft
            rect_x = world_pos[0]
            rect_y = world_pos[1]

        return [rect_x, rect_y, self.cell_size[0], self.cell_size[1]]

    def set_tileset(self, tileset_path: str):
        """Set the tileset resource path"""
        self.tileset = tileset_path

    def get_tileset(self) -> str:
        """Get the tileset resource path"""
        return self.tileset

    def to_dict(self) -> Dict[str, Any]:
        """Serialize TileMap to a dictionary."""
        data = super().to_dict()
        data.update({
            "tileset": self.tileset,
            "cell_size": self.cell_size.copy(),
            "cell_origin": self.cell_origin,
            "mode": self.mode,
            "modulate": self.modulate.copy(),
            "opacity": self.opacity,
            "collision_layer": self.collision_layer,
            "collision_mask": self.collision_mask,
            "one_way_collision_enabled": self.one_way_collision_enabled,
            "one_way_collision_margin": self.one_way_collision_margin,
            "layers": [layer.copy() for layer in self.layers],
            "current_layer": self.current_layer,
            "tilesets": self.tilesets.copy(),
            "map_size_mode": self.map_size_mode,
            "fixed_map_size": self.fixed_map_size.copy(),
            "tiles": {layer_key: layer_tiles.copy() for layer_key, layer_tiles in self._tiles.items()}
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TileMap":
        """Deserialize a TileMap from a dictionary."""
        tilemap = cls(data.get("name", "TileMap"))
        cls._apply_node_properties(tilemap, data)

        tilemap.tileset = data.get("tileset", "")
        tilemap.cell_size = data.get("cell_size", [32.0, 32.0])
        tilemap.cell_origin = data.get("cell_origin", "TopLeft")
        tilemap.mode = data.get("mode", "Square")
        tilemap.modulate = data.get("modulate", [1.0, 1.0, 1.0, 1.0])
        tilemap.opacity = data.get("opacity", 1.0)
        tilemap.collision_layer = data.get("collision_layer", 1)
        tilemap.collision_mask = data.get("collision_mask", 1)
        tilemap.one_way_collision_enabled = data.get("one_way_collision_enabled", False)
        tilemap.one_way_collision_margin = data.get("one_way_collision_margin", 0.0)

        # Load layer system data
        tilemap.layers = data.get("layers", [{"name": "Layer 0", "visible": True, "opacity": 1.0, "z_index": 0}])
        tilemap.current_layer = data.get("current_layer", 0)
        tilemap.tilesets = data.get("tilesets", [])
        tilemap.map_size_mode = data.get("map_size_mode", "infinite")
        tilemap.fixed_map_size = data.get("fixed_map_size", [100, 100])

        # Initialize _tiles for all layers
        tilemap._tiles = {}
        for i in range(len(tilemap.layers)):
            tilemap._tiles[str(i)] = {}

        # Load tiles data
        tiles_data = data.get("tiles", {})
        if isinstance(tiles_data, dict) and tiles_data:
            # Check if this is old format (direct tile mapping) or new format (layered)
            first_key = next(iter(tiles_data.keys()))
            if first_key.isdigit():
                # New layered format
                for layer_key, layer_tiles in tiles_data.items():
                    if layer_key in tilemap._tiles:
                        tilemap._tiles[layer_key] = layer_tiles.copy()
            else:
                # Old format - migrate to layer 0
                tilemap._tiles["0"] = tiles_data.copy()

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            tilemap.add_child(child)
        return tilemap
