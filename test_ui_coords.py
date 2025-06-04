#!/usr/bin/env python3
"""
Test script to verify UI coordinate conversion logic
"""

class MockSceneView:
    def __init__(self):
        # Game bounds (UI coordinate space)
        self.game_width = 1920
        self.game_height = 1080
        
        # View bounds (world coordinate space)
        self.view_width = 2000
        self.view_height = 1200
    
    def _ui_to_world_coords(self, ui_position: list) -> list:
        """Convert UI coordinates (game bounds space) to editor world coordinates"""
        # UI coordinates are in game bounds space (0,0 at top-left, Y increases downward)
        # Editor world coordinates are centered at (0,0), Y increases upward
        
        # Scale UI coordinates to world coordinates based on current view
        # UI coordinates are in game bounds (0 to game_width, 0 to game_height)
        # World coordinates are in view bounds (-view_width/2 to +view_width/2, etc.)
        
        # Convert UI position to normalized coordinates (0 to 1)
        norm_x = ui_position[0] / self.game_width
        norm_y = ui_position[1] / self.game_height
        
        # Convert to world coordinates
        world_x = (norm_x - 0.5) * self.view_width
        world_y = (0.5 - norm_y) * self.view_height  # Flip Y axis
        
        return [world_x, world_y]

    def _world_to_ui_coords(self, world_position):
        """Convert editor world coordinates to UI coordinates (game bounds space)"""
        # World coordinates are in view bounds (-view_width/2 to +view_width/2, etc.)
        # UI coordinates are in game bounds space (0,0 at top-left), Y increases downward
        
        # Convert world coordinates to normalized coordinates (0 to 1)
        norm_x = (world_position[0] / self.view_width) + 0.5
        norm_y = 0.5 - (world_position[1] / self.view_height)  # Flip Y axis
        
        # Convert to UI coordinates
        ui_x = norm_x * self.game_width
        ui_y = norm_y * self.game_height
        
        return [ui_x, ui_y]

def test_coordinate_conversion():
    """Test coordinate conversion functions"""
    scene_view = MockSceneView()
    
    print("Testing UI to World coordinate conversion:")
    print("=" * 50)
    
    # Test cases: UI coordinates -> expected world coordinates
    test_cases = [
        # UI position -> expected world position
        ([0, 0], "Top-left corner"),           # Should map to (-1000, 600)
        ([960, 540], "Center"),                # Should map to (0, 0)
        ([1920, 1080], "Bottom-right corner"), # Should map to (1000, -600)
        ([100, 50], "Button at 100,50"),      # Test case from ButtonTest.scene
        ([100, 100], "Button at 100,100"),    # Test case from ButtonTest.scene
    ]
    
    for ui_pos, description in test_cases:
        world_pos = scene_view._ui_to_world_coords(ui_pos)
        back_to_ui = scene_view._world_to_ui_coords(world_pos)
        
        print(f"{description}:")
        print(f"  UI: {ui_pos} -> World: {world_pos} -> Back to UI: {back_to_ui}")
        
        # Check if conversion is reversible
        ui_diff = [abs(ui_pos[0] - back_to_ui[0]), abs(ui_pos[1] - back_to_ui[1])]
        if ui_diff[0] < 0.01 and ui_diff[1] < 0.01:
            print(f"  ✓ Conversion is reversible")
        else:
            print(f"  ✗ Conversion error: {ui_diff}")
        print()

if __name__ == "__main__":
    test_coordinate_conversion()
