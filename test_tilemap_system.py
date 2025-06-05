#!/usr/bin/env python3
"""
Test script for the tilemap and tileset system
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.tileset import TileSet, TileDefinition, get_tileset_manager
from nodes.node2d.TileMap import TileMap

def test_tileset_creation():
    """Test creating and manipulating tilesets"""
    print("Testing TileSet creation...")
    
    # Create a new tileset
    tileset = TileSet("Test Tileset")
    tileset.texture_path = "assets/test_tileset.png"
    tileset.tile_size = [32, 32]
    tileset.margin = [1, 1]
    tileset.spacing = [2, 2]
    
    # Add some tiles
    for i in range(10):
        tile_def = TileDefinition(i)
        tile_def.name = f"Test Tile {i}"
        tile_def.texture_rect = [i * 34, 0, 32, 32]  # Account for spacing
        tile_def.tags = ["test", f"tile_{i}"]
        
        # Add collision shape for some tiles
        if i % 3 == 0:
            tile_def.collision_shapes.append({
                "type": "rect",
                "rect": [0, 0, 32, 32]
            })
        
        tileset.add_tile(tile_def)
    
    print(f"Created tileset with {len(tileset.tiles)} tiles")
    
    # Test serialization
    tileset_data = tileset.to_dict()
    print(f"Serialized tileset data keys: {list(tileset_data.keys())}")
    
    # Test deserialization
    tileset2 = TileSet.from_dict(tileset_data)
    print(f"Deserialized tileset has {len(tileset2.tiles)} tiles")
    
    # Test tile queries
    tagged_tiles = tileset.get_tiles_with_tag("test")
    print(f"Found {len(tagged_tiles)} tiles with 'test' tag")
    
    return tileset

def test_tilemap_creation():
    """Test creating and manipulating tilemaps"""
    print("\nTesting TileMap creation...")
    
    # Create a new tilemap
    tilemap = TileMap("Test TileMap")
    
    # Test layer management
    print(f"Initial layers: {len(tilemap.layers)}")
    
    # Add more layers
    layer1 = tilemap.add_layer("Background")
    layer2 = tilemap.add_layer("Foreground")
    print(f"Added layers, now have: {len(tilemap.layers)} layers")
    
    # Test tile placement
    tile_data = {"tile_id": 5, "tileset": 0}
    tilemap.set_tile(0, 0, tile_data, layer=0)
    tilemap.set_tile(1, 0, tile_data, layer=0)
    tilemap.set_tile(0, 1, tile_data, layer=1)
    
    # Test tile retrieval
    retrieved_tile = tilemap.get_tile(0, 0, layer=0)
    print(f"Retrieved tile at (0,0): {retrieved_tile}")
    
    # Test used cells
    used_cells_layer0 = tilemap.get_used_cells(layer=0)
    used_cells_layer1 = tilemap.get_used_cells(layer=1)
    print(f"Used cells layer 0: {used_cells_layer0}")
    print(f"Used cells layer 1: {used_cells_layer1}")
    
    # Test serialization
    tilemap_data = tilemap.to_dict()
    print(f"Serialized tilemap data keys: {list(tilemap_data.keys())}")
    
    # Test deserialization
    tilemap2 = TileMap.from_dict(tilemap_data)
    print(f"Deserialized tilemap has {len(tilemap2.layers)} layers")
    
    return tilemap

def test_tileset_manager():
    """Test the tileset manager"""
    print("\nTesting TileSet Manager...")
    
    manager = get_tileset_manager()
    
    # Create a test tileset file
    test_dir = Path("test_assets")
    test_dir.mkdir(exist_ok=True)
    
    tileset = TileSet("Manager Test")
    tileset.texture_path = "test_texture.png"
    
    # Add a few tiles
    for i in range(5):
        tile_def = TileDefinition(i)
        tile_def.name = f"Manager Tile {i}"
        tileset.add_tile(tile_def)
    
    # Save to file
    test_file = test_dir / "test_tileset.json"
    tileset.save_to_file(str(test_file))
    print(f"Saved test tileset to {test_file}")
    
    # Load through manager
    loaded_tileset = manager.load_tileset(str(test_file))
    if loaded_tileset:
        print(f"Manager loaded tileset with {len(loaded_tileset.tiles)} tiles")
    else:
        print("Manager failed to load tileset")
    
    # Test caching
    loaded_again = manager.load_tileset(str(test_file))
    print(f"Cached load successful: {loaded_again is loaded_tileset}")
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()

def test_coordinate_conversion():
    """Test coordinate conversion functions"""
    print("\nTesting coordinate conversion...")
    
    tilemap = TileMap("Coordinate Test")
    tilemap.position = [100, 50]
    tilemap.cell_size = [32, 32]
    
    # Test world to map conversion
    world_pos = [132, 82]  # Should be tile (1, 1)
    map_pos = tilemap.world_to_map(world_pos)
    print(f"World {world_pos} -> Map {map_pos}")
    
    # Test map to world conversion
    map_pos = [2, 3]
    world_pos = tilemap.map_to_world(map_pos)
    print(f"Map {map_pos} -> World {world_pos}")
    
    # Test cell rect
    cell_rect = tilemap.get_cell_rect(1, 1)
    print(f"Cell (1,1) rect: {cell_rect}")

def main():
    """Run all tests"""
    print("=== Tilemap and Tileset System Tests ===\n")
    
    try:
        # Test tileset functionality
        tileset = test_tileset_creation()
        
        # Test tilemap functionality
        tilemap = test_tilemap_creation()
        
        # Test tileset manager
        test_tileset_manager()
        
        # Test coordinate conversion
        test_coordinate_conversion()
        
        print("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        print(f"\n=== Test failed with error: {e} ===")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
