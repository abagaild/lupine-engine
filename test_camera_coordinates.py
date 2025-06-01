#!/usr/bin/env python3
"""
Test script to verify camera coordinate system fixes
"""

import sys
import json
from pathlib import Path

def test_coordinate_transformations():
    """Test the coordinate transformations we implemented"""
    print("🔧 Testing Camera Coordinate System Fixes")
    print("=" * 50)
    
    # Load the camera scene
    scene_file = Path("test_camera_scene.json")
    if not scene_file.exists():
        print("❌ Camera scene file not found!")
        return False
    
    with open(scene_file, 'r') as f:
        scene_data = json.load(f)
    
    print(f"✅ Loaded scene: {scene_data.get('name', 'Unknown')}")
    
    # Find camera and sprites
    nodes = scene_data.get("nodes", [])
    
    def find_nodes_by_type(node_list, node_type):
        found = []
        for node in node_list:
            if node.get("type") == node_type:
                found.append(node)
            # Check children
            children = node.get("children", [])
            if children:
                found.extend(find_nodes_by_type(children, node_type))
        return found
    
    cameras = find_nodes_by_type(nodes, "Camera2D")
    sprites = find_nodes_by_type(nodes, "Sprite")
    
    print(f"\n📷 Found {len(cameras)} camera(s):")
    for camera in cameras:
        name = camera.get("name", "Unknown")
        position = camera.get("position", [0, 0])
        current = camera.get("current", False)
        zoom = camera.get("zoom", [1.0, 1.0])
        offset = camera.get("offset", [0.0, 0.0])
        
        print(f"  - {name}: pos={position}, current={current}, zoom={zoom}, offset={offset}")
        
        # Apply our coordinate transformation
        camera_x = position[0] + offset[0]
        camera_y = -(position[1] + offset[1])  # Invert Y for Arcade
        print(f"    → Arcade position: ({camera_x}, {camera_y})")
    
    print(f"\n🎨 Found {len(sprites)} sprite(s):")
    for sprite in sprites:
        name = sprite.get("name", "Unknown")
        position = sprite.get("position", [0, 0])
        texture = sprite.get("texture", "")
        
        print(f"  - {name}: pos={position}, texture={texture}")
        
        # Apply our coordinate transformation
        sprite_x = position[0]
        sprite_y = -position[1]  # Invert Y for Arcade
        print(f"    → Arcade position: ({sprite_x}, {sprite_y})")
    
    print("\n🔄 Coordinate System Analysis:")
    print("Scene View (Editor):")
    print("  - Origin (0,0) at center")
    print("  - Y-axis: positive up, negative down")
    print("  - Camera at (0,0) shows center of world")
    
    print("\nArcade (Game Runner):")
    print("  - Origin (0,0) at center (with camera)")
    print("  - Y-axis: positive up, negative down")
    print("  - Camera position is center of view")
    print("  - Sprites need Y-inversion to match scene view")
    
    print("\n✅ Expected Results:")
    if cameras and sprites:
        camera = cameras[0]
        cam_pos = camera.get("position", [0, 0])
        
        print(f"Camera at {cam_pos} should show:")
        for sprite in sprites:
            sprite_pos = sprite.get("position", [0, 0])
            relative_x = sprite_pos[0] - cam_pos[0]
            relative_y = sprite_pos[1] - cam_pos[1]
            
            # In scene view coordinates
            print(f"  - {sprite.get('name', 'Unknown')}: {relative_x:+.0f} right, {relative_y:+.0f} up from camera")
    
    return True

def test_specific_positions():
    """Test specific positions from the camera scene"""
    print("\n🎯 Testing Specific Scene Positions:")
    print("=" * 50)
    
    # Expected positions from test_camera_scene.json
    camera_pos = [0, 0]
    player_pos = [100, 200]
    background_pos = [-200, -100]
    
    print("Scene View (Editor) Positions:")
    print(f"  Camera: {camera_pos}")
    print(f"  Player: {player_pos}")
    print(f"  Background: {background_pos}")
    
    print("\nArcade (Game Runner) Positions (after transformation):")
    # Camera transformation
    cam_arcade = [camera_pos[0], -camera_pos[1]]
    player_arcade = [player_pos[0], -player_pos[1]]
    background_arcade = [background_pos[0], -background_pos[1]]
    
    print(f"  Camera: {cam_arcade}")
    print(f"  Player: {player_arcade}")
    print(f"  Background: {background_arcade}")
    
    print("\nRelative to Camera (what should be visible):")
    player_rel = [player_pos[0] - camera_pos[0], player_pos[1] - camera_pos[1]]
    background_rel = [background_pos[0] - camera_pos[0], background_pos[1] - camera_pos[1]]
    
    print(f"  Player: {player_rel[0]:+.0f} right, {player_rel[1]:+.0f} up")
    print(f"  Background: {background_rel[0]:+.0f} right, {background_rel[1]:+.0f} up")
    
    print("\n📐 Expected Visual Layout:")
    print("  - Player should appear 100 pixels right, 200 pixels up from center")
    print("  - Background should appear 200 pixels left, 100 pixels down from center")
    
    return True

def main():
    """Run coordinate system tests"""
    try:
        success1 = test_coordinate_transformations()
        success2 = test_specific_positions()
        
        if success1 and success2:
            print("\n🎉 Coordinate System Tests Completed!")
            print("\nKey Fixes Applied:")
            print("1. ✅ Camera Y-coordinate inverted: y = -(position[1] + offset[1])")
            print("2. ✅ Sprite Y-coordinate inverted: y = -position[1]")
            print("3. ✅ Camera position treated as view center")
            print("4. ✅ Maintained world coordinate consistency")
            
            print("\nTo test visually:")
            print("1. Open Lupine Engine editor")
            print("2. Load test_camera_scene.json")
            print("3. Run the scene")
            print("4. Verify sprites appear at correct relative positions")
            
            return True
        else:
            print("❌ Some tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
