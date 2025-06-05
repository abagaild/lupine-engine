#!/usr/bin/env python3
"""
Test script to create a scene with a TileMap node and test the tilemap system
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_test_scene():
    """Create a test scene with a TileMap node"""
    
    # Create a simple scene with a TileMap
    scene_data = {
        "name": "TilemapTestScene",
        "type": "Node2D",
        "position": [0, 0],
        "rotation": 0,
        "scale": [1, 1],
        "children": [
            {
                "name": "TestTileMap",
                "type": "TileMap",
                "position": [0, 0],
                "rotation": 0,
                "scale": [1, 1],
                "cell_size": [32, 32],
                "cell_origin": "TopLeft",
                "mode": "Square",
                "modulate": [1.0, 1.0, 1.0, 1.0],
                "opacity": 1.0,
                "collision_layer": 1,
                "collision_mask": 1,
                "one_way_collision_enabled": False,
                "one_way_collision_margin": 0.0,
                "layers": [
                    {
                        "name": "Background",
                        "visible": True,
                        "opacity": 1.0,
                        "z_index": 0
                    },
                    {
                        "name": "Foreground", 
                        "visible": True,
                        "opacity": 0.8,
                        "z_index": 1
                    }
                ],
                "current_layer": 0,
                "tilesets": ["assets/sample_tileset.tres"],
                "map_size_mode": "infinite",
                "fixed_map_size": [100, 100],
                "tiles": {
                    "0": {
                        "0,0": {"tile_id": 0, "tileset": 0},
                        "1,0": {"tile_id": 1, "tileset": 0},
                        "2,0": {"tile_id": 2, "tileset": 0},
                        "0,1": {"tile_id": 3, "tileset": 0},
                        "1,1": {"tile_id": 4, "tileset": 0},
                        "2,1": {"tile_id": 5, "tileset": 0},
                        "3,0": {"tile_id": 0, "tileset": 0},
                        "3,1": {"tile_id": 1, "tileset": 0},
                        "4,0": {"tile_id": 2, "tileset": 0},
                        "4,1": {"tile_id": 3, "tileset": 0}
                    },
                    "1": {
                        "1,1": {"tile_id": 2, "tileset": 0},
                        "2,2": {"tile_id": 3, "tileset": 0}
                    }
                },
                "children": []
            },
            {
                "name": "Camera2D",
                "type": "Camera2D",
                "position": [0, 0],
                "rotation": 0,
                "scale": [1, 1],
                "current": True,
                "enabled": True,
                "zoom": [1.0, 1.0],
                "offset": [0.0, 0.0],
                "follow_target": None,
                "smoothing_enabled": False,
                "smoothing_speed": 5.0,
                "limit_left": -10000000,
                "limit_top": -10000000,
                "limit_right": 10000000,
                "limit_bottom": 10000000,
                "limit_smoothed": False,
                "drag_margin_left": 0.2,
                "drag_margin_top": 0.2,
                "drag_margin_right": 0.2,
                "drag_margin_bottom": 0.2,
                "editor_draw_limits": False,
                "editor_draw_drag_margin": False,
                "children": []
            }
        ]
    }
    
    return scene_data

def save_test_scene():
    """Save the test scene to a file"""
    scene_data = create_test_scene()
    
    # Create scenes directory if it doesn't exist
    scenes_dir = Path("scenes")
    scenes_dir.mkdir(exist_ok=True)
    
    # Save the scene
    scene_file = scenes_dir / "tilemap_test.scene"
    with open(scene_file, 'w') as f:
        json.dump(scene_data, f, indent=2)
    
    print(f"Test scene saved to: {scene_file}")
    return scene_file

def test_tilemap_loading():
    """Test loading the TileMap from the scene"""
    from nodes.node2d.TileMap import TileMap
    from core.tileset import get_tileset_manager
    
    print("Testing TileMap loading...")
    
    # Create a TileMap from the test data
    scene_data = create_test_scene()
    tilemap_data = scene_data["children"][0]  # First child is the TileMap
    
    # Create TileMap node from data
    tilemap = TileMap.from_dict(tilemap_data)
    
    print(f"TileMap created: {tilemap.name}")
    print(f"Layers: {len(tilemap.layers)}")
    print(f"Tilesets: {tilemap.tilesets}")
    print(f"Cell size: {tilemap.cell_size}")
    print(f"Map size mode: {tilemap.map_size_mode}")
    
    # Test layer functionality
    for i, layer in enumerate(tilemap.layers):
        used_cells = tilemap.get_used_cells(i)
        print(f"Layer {i} ({layer['name']}): {len(used_cells)} tiles")
    
    # Test tile access
    tile_data = tilemap.get_tile(0, 0, layer=0)
    print(f"Tile at (0,0) layer 0: {tile_data}")
    
    tile_data = tilemap.get_tile(1, 1, layer=1)
    print(f"Tile at (1,1) layer 1: {tile_data}")
    
    # Test tileset loading
    tileset_manager = get_tileset_manager()
    if tilemap.tilesets:
        tileset_path = tilemap.tilesets[0]
        print(f"Loading tileset: {tileset_path}")
        
        # Try to load the sample tileset
        tileset = tileset_manager.load_tileset(tileset_path)
        if tileset:
            print(f"Tileset loaded: {tileset.name}")
            print(f"Tiles in tileset: {len(tileset.tiles)}")
            
            # Show some tile info
            for tile_id, tile_def in list(tileset.tiles.items())[:3]:
                print(f"  Tile {tile_id}: {tile_def.name} - tags: {tile_def.tags}")
        else:
            print("Failed to load tileset")
    
    return tilemap

def main():
    """Run the tilemap test"""
    print("=== Tilemap Scene Test ===\n")
    
    try:
        # Save test scene
        scene_file = save_test_scene()
        
        # Test tilemap loading
        tilemap = test_tilemap_loading()
        
        print(f"\n=== Test completed successfully! ===")
        print(f"Scene file: {scene_file}")
        print("You can now:")
        print("1. Open the editor and load the test scene")
        print("2. Select the TileMap node and click 'Open Tilemap Editor'")
        print("3. Use the Tileset Editor from the Tools menu")
        
        return 0
        
    except Exception as e:
        print(f"\n=== Test failed with error: {e} ===")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
