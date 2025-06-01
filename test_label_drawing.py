#!/usr/bin/env python3
"""
Test Label drawing functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import arcade

class LabelTestWindow(arcade.Window):
    """Test window for Label drawing"""
    
    def __init__(self):
        super().__init__(800, 600, "Label Drawing Test")
        
    def setup(self):
        """Set up the test"""
        arcade.set_background_color(arcade.color.DARK_GRAY)
        
    def on_draw(self):
        """Draw the test scene"""
        self.clear()
        
        # Test basic arcade.draw_text function
        try:
            arcade.draw_text("Basic Text Test", 50, 500, arcade.color.WHITE, 16)
            arcade.draw_text("SUCCESS: Basic text drawing works!", 50, 470, arcade.color.GREEN, 14)
        except Exception as e:
            print(f"Basic text drawing failed: {e}")
            
        # Test different colors
        try:
            arcade.draw_text("Red Text", 50, 440, arcade.color.RED, 14)
            arcade.draw_text("Blue Text", 50, 410, arcade.color.BLUE, 14)
            arcade.draw_text("Yellow Text", 50, 380, arcade.color.YELLOW, 14)
        except Exception as e:
            print(f"Colored text drawing failed: {e}")
            
        # Test different sizes
        try:
            arcade.draw_text("Small", 50, 350, arcade.color.WHITE, 10)
            arcade.draw_text("Medium", 50, 320, arcade.color.WHITE, 16)
            arcade.draw_text("Large", 50, 280, arcade.color.WHITE, 24)
        except Exception as e:
            print(f"Sized text drawing failed: {e}")
            
        # Test positioning
        try:
            arcade.draw_text("Top Left", 10, self.height - 30, arcade.color.CYAN, 14)
            arcade.draw_text("Top Right", self.width - 100, self.height - 30, arcade.color.CYAN, 14)
            arcade.draw_text("Bottom Left", 10, 10, arcade.color.CYAN, 14)
            arcade.draw_text("Bottom Right", self.width - 120, 10, arcade.color.CYAN, 14)
        except Exception as e:
            print(f"Positioned text drawing failed: {e}")
            
        # Test percentage-based positioning simulation
        try:
            # Simulate 50% width, 50% height
            center_x = self.width * 0.5
            center_y = self.height * 0.5
            arcade.draw_text("CENTER (50%, 50%)", center_x - 80, center_y, arcade.color.ORANGE, 16)
            
            # Simulate 80% width, 95% height (like TopRightLabel)
            top_right_x = self.width * 0.8
            top_right_y = self.height * 0.95
            arcade.draw_text("80%, 95%", top_right_x, top_right_y, arcade.color.MAGENTA, 14)
            
        except Exception as e:
            print(f"Percentage positioning failed: {e}")
            
        # Test UI positioning simulation
        try:
            # Simulate game area with letterboxing
            target_aspect = 16.0 / 9.0
            current_aspect = self.width / self.height
            
            if current_aspect > target_aspect:
                # Pillarboxing
                game_height = self.height
                game_width = int(self.height * target_aspect)
                offset_x = (self.width - game_width) // 2
                offset_y = 0
            else:
                # Letterboxing
                game_width = self.width
                game_height = int(self.width / target_aspect)
                offset_x = 0
                offset_y = (self.height - game_height) // 2
                
            # Draw game bounds
            arcade.draw_lbwh_rectangle_outline(offset_x, offset_y, game_width, game_height, arcade.color.WHITE, 2)
            
            # Test UI positioning within game bounds
            ui_x = offset_x + 10  # 10 pixels from left edge
            ui_y = offset_y + 10  # 10 pixels from bottom edge
            arcade.draw_text("UI: Bottom Left", ui_x, ui_y, arcade.color.YELLOW, 12)
            
            # Test percentage UI positioning
            ui_x_percent = offset_x + (game_width * 0.8)  # 80% from left
            ui_y_percent = offset_y + (game_height * 0.9)  # 90% from bottom
            arcade.draw_text("UI: 80%, 90%", ui_x_percent, ui_y_percent, arcade.color.LIME, 12)
            
        except Exception as e:
            print(f"UI positioning simulation failed: {e}")
            
        # Test instructions
        arcade.draw_text("This test verifies that text drawing works correctly", 50, 200, arcade.color.WHITE, 12)
        arcade.draw_text("All text should be visible and properly positioned", 50, 180, arcade.color.WHITE, 12)
        arcade.draw_text("The white rectangle shows the game bounds with aspect ratio", 50, 160, arcade.color.WHITE, 12)
        arcade.draw_text("Press ESC to exit", 50, 140, arcade.color.WHITE, 12)
                        
    def on_key_press(self, key, modifiers):
        """Handle key press"""
        if key == arcade.key.ESCAPE:
            self.close()

def main():
    """Run the label drawing test"""
    print("Label Drawing Test")
    print("=" * 50)
    print("Testing arcade.draw_text functionality...")
    
    window = LabelTestWindow()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
