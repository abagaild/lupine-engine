#!/usr/bin/env python3
"""
Test script for the resizable game runner with improved text performance
"""

import sys
import os
sys.path.insert(0, '.')

import arcade
import json

class TestResizableGameWindow(arcade.Window):
    def __init__(self):
        super().__init__(1280, 720, "Lupine Engine - Resizable Game Runner Test", resizable=True)
        self.scene_data = None
        self.textures = {}
        self.text_objects = {}  # Cache for text objects to improve performance
        self.load_scene()

    def get_text_object(self, text, font_size=12, color=arcade.color.WHITE):
        """Get or create a cached text object for better performance"""
        key = f"{text}_{font_size}_{color}"
        if key not in self.text_objects:
            self.text_objects[key] = arcade.Text(
                text=text,
                x=0,
                y=0,
                color=color,
                font_size=font_size
            )
        return self.text_objects[key]

    def draw_cached_text(self, text, x, y, color=arcade.color.WHITE, font_size=12):
        """Draw text using cached text objects for better performance"""
        text_obj = self.get_text_object(text, font_size, color)
        text_obj.x = x
        text_obj.y = y
        text_obj.draw()

    def load_scene(self):
        # Create a simple test scene
        self.scene_data = {
            "name": "ResizableTest",
            "nodes": [{
                "name": "Main",
                "type": "Node2D",
                "position": [0, 0],
                "children": [
                    {
                        "name": "TestSprite",
                        "type": "Sprite",
                        "position": [0, 0],
                        "size": [64, 64],
                        "children": []
                    },
                    {
                        "name": "TestCamera",
                        "type": "Camera2D",
                        "position": [100, 100],
                        "current": True,
                        "children": []
                    }
                ]
            }]
        }

    def setup(self):
        arcade.set_background_color(arcade.color.DARK_GRAY)
        
        # Set proper OpenGL blend mode to avoid white film
        self.ctx.enable(self.ctx.BLEND)
        self.ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA
        
        print("Resizable game setup complete")
        print("ESC to exit, try resizing the window!")

    def on_draw(self):
        self.clear()

        # Set proper blend mode for rendering
        self.ctx.enable(self.ctx.BLEND)
        self.ctx.blend_func = self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA

        # Draw scene nodes
        if self.scene_data:
            nodes = self.scene_data.get("nodes", [])
            for node in nodes:
                self.draw_node_fallback(node)

        # Draw UI overlay
        self.draw_ui()

    def draw_node_fallback(self, node_data):
        """Fallback node rendering"""
        position = node_data.get("position", [0, 0])
        node_type = node_data.get("type", "Node")

        # Center position on screen
        x = position[0] + self.width // 2
        y = position[1] + self.height // 2

        if node_type == "Node2D":
            arcade.draw_circle_filled(x, y, 8, arcade.color.WHITE)
            self.draw_cached_text(node_data.get("name", "Node"), x + 15, y,
                                arcade.color.WHITE, 12)
        elif node_type == "Sprite":
            size = node_data.get("size", [64, 64])
            arcade.draw_lbwh_rectangle_filled(x - size[0]//2, y - size[1]//2, size[0], size[1], arcade.color.GREEN)
            self.draw_cached_text(node_data.get("name", "Sprite"), x + size[0]//2 + 10, y,
                                arcade.color.WHITE, 12)
        elif node_type == "Camera2D":
            arcade.draw_lbwh_rectangle_outline(x - 30, y - 20, 60, 40, arcade.color.YELLOW, 3)
            self.draw_cached_text(node_data.get("name", "Camera"), x + 35, y,
                                arcade.color.YELLOW, 12)

        # Draw children
        for child in node_data.get("children", []):
            self.draw_node_fallback(child)

    def draw_ui(self):
        """Draw UI overlay with window size info"""
        self.draw_cached_text("Lupine Engine - Resizable Game Runner Test", 10, self.height - 30,
                            arcade.color.WHITE, 16)
        self.draw_cached_text(f"Window Size: {self.width} x {self.height}", 10, self.height - 60,
                            arcade.color.LIGHT_GRAY, 14)
        self.draw_cached_text("ESC: Exit | Try resizing the window!", 10, 10, arcade.color.WHITE, 12)
        self.draw_cached_text("Using cached text objects for better performance", 10, 30, 
                            arcade.color.GREEN, 12)

    def on_resize(self, width, height):
        """Handle window resize events"""
        super().on_resize(width, height)
        
        # Clear text cache when window is resized to avoid positioning issues
        self.text_objects.clear()
        print(f"Window resized to: {width} x {height}")

    def on_update(self, delta_time):
        pass

    def on_key_press(self, key, modifiers):
        """Handle key press events"""
        if key == arcade.key.ESCAPE:
            self.close()

def main():
    try:
        print("Starting resizable game runner test...")
        print("Features to test:")
        print("1. Smaller window size (1280x720 instead of 1920x1080)")
        print("2. Resizable window")
        print("3. Cached text objects for better performance")
        print("4. No white film overlay")
        print()
        
        game = TestResizableGameWindow()
        game.setup()
        arcade.run()
    except Exception as e:
        print(f"Game error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
