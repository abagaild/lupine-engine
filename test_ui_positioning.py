#!/usr/bin/env python3
"""
Test the new UI positioning system with percentage-based positioning
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import arcade
import json

# Import LSC runtime for script execution
try:
    from core.lsc import LSCRuntime, LSCInterpreter
    from core.lsc.interpreter import execute_lsc_script
    from core.scene import Scene, Node, Node2D, Sprite, Camera2D
    LSC_AVAILABLE = True
    print("LSC available")
except ImportError as e:
    print(f"LSC not available: {e}")
    LSC_AVAILABLE = False

class UIPositioningTestWindow(arcade.Window):
    """Test window for UI positioning system"""
    
    def __init__(self):
        super().__init__(1280, 720, "UI Positioning Test - Resize to test scaling!")
        self.scene_data = None
        self.scene = None
        self.camera = None
        self.sprite_lists = {}
        
        # Load the test scene
        scene_file = "test_ui_positioning.scene"
        self.load_scene(scene_file)
        
    def load_scene(self, scene_file):
        """Load the test scene"""
        try:
            with open(scene_file, 'r') as f:
                self.scene_data = json.load(f)
            print(f"Loaded test scene: {self.scene_data.get('name', 'Unknown')}")
            
            # Load scene using proper Scene class if available
            if LSC_AVAILABLE:
                self.scene = Scene.load_from_file(scene_file)
                print("Using LSC Scene system")
                # Debug: Print what was loaded
                if self.scene:
                    print(f"Scene has {len(self.scene.root_nodes)} root nodes")
                    for i, node in enumerate(self.scene.root_nodes):
                        print(f"  Node {i}: {node.name} ({node.type}) at {getattr(node, 'position', 'no position')}")
            else:
                print("Using fallback JSON parsing")
                
        except Exception as e:
            print(f"Error loading scene: {e}")
            
    def setup(self):
        """Set up the test"""
        arcade.set_background_color(arcade.color.DARK_GRAY)
        
        # Initialize sprite lists
        self.sprite_lists = {
            "sprites": arcade.SpriteList(),
            "ui": arcade.SpriteList()
        }
        
        # Find and setup camera
        if self.scene:
            for root_node in self.scene.root_nodes:
                self.find_cameras(root_node)
                self.setup_node(root_node)
        elif self.scene_data:
            nodes = self.scene_data.get("nodes", [])
            for node in nodes:
                self.find_cameras(node)
                self.setup_node_fallback(node)
                
        # Initialize camera viewport
        if self.camera:
            self.camera.match_window(viewport=True, projection=True, scissor=True, position=False)
            print(f"Camera initialized: position={self.camera.position}, viewport={self.camera.viewport}")
        else:
            print("No camera found!")
            
    def find_cameras(self, node):
        """Find camera nodes"""
        if hasattr(node, 'type') and node.type == "Camera2D" and getattr(node, 'current', False):
            self.camera = arcade.Camera2D()
            position = getattr(node, 'position', [0.0, 0.0])
            zoom = getattr(node, 'zoom', [1.0, 1.0])
            offset = getattr(node, 'offset', [0.0, 0.0])
            
            camera_x = position[0] + offset[0]
            camera_y = position[1] + offset[1]
            
            self.camera.position = (camera_x, camera_y)
            self.camera.zoom = zoom[0] if isinstance(zoom, list) else zoom
            print(f"Found camera: {node.name} at {position} -> arcade {(camera_x, camera_y)}")
            
        elif isinstance(node, dict) and node.get("type") == "Camera2D" and node.get("current", False):
            self.camera = arcade.Camera2D()
            position = node.get("position", [0.0, 0.0])
            zoom = node.get("zoom", [1.0, 1.0])
            offset = node.get("offset", [0.0, 0.0])
            
            camera_x = position[0] + offset[0]
            camera_y = position[1] + offset[1]
            
            self.camera.position = (camera_x, camera_y)
            self.camera.zoom = zoom[0] if isinstance(zoom, list) else zoom
            print(f"Found camera: {node.get('name', 'Camera2D')} at {position} -> arcade {(camera_x, camera_y)}")
            
        # Check children
        if hasattr(node, 'children'):
            for child in node.children:
                self.find_cameras(child)
        elif isinstance(node, dict) and 'children' in node:
            for child in node['children']:
                self.find_cameras(child)
                
    def setup_node(self, node):
        """Setup node from Scene object"""
        if hasattr(node, 'type') and node.type == "Sprite":
            # Create arcade sprite
            arcade_sprite = arcade.Sprite()
            arcade_sprite.center_x = node.position[0]
            arcade_sprite.center_y = node.position[1]
            
            # Try to load texture
            texture_path = getattr(node, 'texture', '')
            if texture_path:
                try:
                    texture = arcade.load_texture(texture_path)
                    arcade_sprite.texture = texture
                    print(f"Loaded texture for {node.name}: {texture_path}")
                except Exception as e:
                    print(f"Failed to load texture {texture_path}: {e}")
                    
            self.sprite_lists["sprites"].append(arcade_sprite)
            print(f"Created sprite: {node.name} at {node.position}")
            
        # Process children
        if hasattr(node, 'children'):
            for child in node.children:
                self.setup_node(child)
                
    def setup_node_fallback(self, node_data):
        """Setup node from JSON data"""
        if node_data.get("type") == "Sprite":
            arcade_sprite = arcade.Sprite()
            position = node_data.get("position", [0.0, 0.0])
            arcade_sprite.center_x = position[0]
            arcade_sprite.center_y = position[1]
            
            # Try to load texture
            texture_path = node_data.get('texture', '')
            if texture_path:
                try:
                    texture = arcade.load_texture(texture_path)
                    arcade_sprite.texture = texture
                    print(f"Loaded texture: {texture_path}")
                except Exception as e:
                    print(f"Failed to load texture {texture_path}: {e}")
                    
            self.sprite_lists["sprites"].append(arcade_sprite)
            print(f"Created sprite: {node_data.get('name', 'Sprite')} at {position}")
            
        # Process children
        for child in node_data.get('children', []):
            self.setup_node_fallback(child)
            
    def on_draw(self):
        """Draw the test scene"""
        self.clear()
        
        # Use camera if available
        if self.camera:
            self.camera.use()
            
        # Draw sprites
        self.sprite_lists["sprites"].draw()
        
        # Test the UI camera fix
        if self.camera:
            # Reset to default camera for UI
            if hasattr(self.ctx, 'default_camera'):
                self.ctx.default_camera.use()
            elif hasattr(self.ctx, '_default_camera'):
                self.ctx._default_camera.use()
            else:
                # Fallback - create a new camera for UI
                ui_camera = arcade.Camera2D()
                ui_camera.match_window()
                ui_camera.use()
        
        # Draw UI elements using the new positioning system
        if self.scene:
            for root_node in self.scene.root_nodes:
                self.draw_ui_node(root_node)
        elif self.scene_data:
            nodes = self.scene_data.get("nodes", [])
            for node in nodes:
                self.draw_ui_node_fallback(node)
        
        # Draw test info
        arcade.draw_text(f"Window Size: {self.width}x{self.height}", 
                        10, self.height - 30, arcade.color.WHITE, 16)
        arcade.draw_text("Resize window to test UI scaling!", 
                        10, self.height - 50, arcade.color.GREEN, 16)
        arcade.draw_text("UI elements should maintain relative positions", 
                        10, self.height - 70, arcade.color.YELLOW, 16)
                        
    def draw_ui_node(self, node):
        """Draw UI nodes from Scene objects"""
        if hasattr(node, 'type'):
            if node.type in ["Label", "Panel", "Control"]:
                # Convert node to dict format for drawing
                node_data = {
                    "type": node.type,
                    "position": getattr(node, 'position', [0.0, 0.0]),
                    "rect_size": getattr(node, 'rect_size', [100.0, 50.0]),
                    "text": getattr(node, 'text', 'Label'),
                    "font_color": getattr(node, 'font_color', [1.0, 1.0, 1.0, 1.0]),
                    "font_size": getattr(node, 'font_size', 14),
                    "h_align": getattr(node, 'h_align', 'Left'),
                    "v_align": getattr(node, 'v_align', 'Top'),
                    "panel_color": getattr(node, 'panel_color', [0.2, 0.2, 0.2, 1.0]),
                    "border_width": getattr(node, 'border_width', 0.0),
                    "border_color": getattr(node, 'border_color', [0.0, 0.0, 0.0, 1.0]),
                    "children": []
                }
                self.draw_ui_node_fallback(node_data)
                
        # Process children
        if hasattr(node, 'children'):
            for child in node.children:
                self.draw_ui_node(child)
                
    def draw_ui_node_fallback(self, node_data):
        """Draw UI nodes from JSON data"""
        node_type = node_data.get("type", "Node")
        
        if node_type == "Label":
            self.draw_label_fallback(node_data)
        elif node_type == "Panel":
            self.draw_panel_fallback(node_data)
        elif node_type == "Control":
            self.draw_control_fallback(node_data)
            
        # Process children
        for child in node_data.get('children', []):
            self.draw_ui_node_fallback(child)
    
    # Include the UI drawing methods from game_runner.py
    def calculate_ui_position(self, position, rect_size=None):
        """Calculate UI position relative to game viewport with support for percentage positioning"""
        # Maintain 16:9 aspect ratio with letterboxing/pillarboxing
        target_aspect = 16.0 / 9.0
        current_aspect = self.width / self.height
        
        if current_aspect > target_aspect:
            # Window is too wide - add pillarboxing (black bars on sides)
            game_height = self.height
            game_width = int(self.height * target_aspect)
            offset_x = (self.width - game_width) // 2
            offset_y = 0
        else:
            # Window is too tall - add letterboxing (black bars on top/bottom)
            game_width = self.width
            game_height = int(self.width / target_aspect)
            offset_x = 0
            offset_y = (self.height - game_height) // 2
        
        game_area = {
            "width": game_width,
            "height": game_height,
            "offset_x": offset_x,
            "offset_y": offset_y
        }
        
        # Support for percentage-based positioning (0.0-1.0 range)
        x_pos = position[0]
        y_pos = position[1]
        
        # Convert percentage to absolute position
        if 0.0 <= x_pos <= 1.0:
            x_pos = x_pos * game_area['width']
        if 0.0 <= y_pos <= 1.0:
            y_pos = y_pos * game_area['height']
            
        # Calculate final screen position
        ui_x = game_area['offset_x'] + x_pos
        ui_y = game_area['offset_y'] + y_pos
        
        return ui_x, ui_y
    
    def calculate_ui_size(self, rect_size, base_size=None):
        """Calculate UI size with support for percentage-based sizing"""
        # Maintain 16:9 aspect ratio with letterboxing/pillarboxing
        target_aspect = 16.0 / 9.0
        current_aspect = self.width / self.height
        
        if current_aspect > target_aspect:
            game_height = self.height
            game_width = int(self.height * target_aspect)
        else:
            game_width = self.width
            game_height = int(self.width / target_aspect)
        
        game_area = {
            "width": game_width,
            "height": game_height
        }
        
        width = rect_size[0]
        height = rect_size[1]
        
        # Support percentage-based sizing (0.0-1.0 range)
        if 0.0 <= width <= 1.0:
            width = width * game_area['width']
        if 0.0 <= height <= 1.0:
            height = height * game_area['height']
            
        return width, height
    
    def draw_label_fallback(self, node_data):
        """Draw Label node with new positioning system"""
        position = node_data.get("position", [0.0, 0.0])
        rect_size = node_data.get("rect_size", [100.0, 50.0])
        text = node_data.get("text", "Label")
        font_color = node_data.get("font_color", [1.0, 1.0, 1.0, 1.0])
        h_align = node_data.get("h_align", "Left")
        v_align = node_data.get("v_align", "Top")
        
        # Calculate UI position and size with percentage support
        ui_x, ui_y = self.calculate_ui_position(position, rect_size)
        ui_width, ui_height = self.calculate_ui_size(rect_size)
        
        # Convert font color to arcade format
        font_arcade_color = (
            int(font_color[0] * 255),
            int(font_color[1] * 255),
            int(font_color[2] * 255)
        )
        
        # Calculate text position based on alignment
        text_x = ui_x - ui_width/2 + 5  # Default left alignment with padding
        if h_align == "Center":
            text_x = ui_x
        elif h_align == "Right":
            text_x = ui_x + ui_width/2 - 5
        
        text_y = ui_y + ui_height/2 - 15  # Default top alignment
        if v_align == "Center":
            text_y = ui_y
        elif v_align == "Bottom":
            text_y = ui_y - ui_height/2 + 15
        
        # Handle font size
        actual_font_size = node_data.get("font_size", 14)
        if 0.0 <= actual_font_size <= 1.0:
            # Percentage-based font sizing
            target_aspect = 16.0 / 9.0
            current_aspect = self.width / self.height
            if current_aspect > target_aspect:
                game_height = self.height
            else:
                game_height = int(self.width / target_aspect)
            actual_font_size = actual_font_size * game_height
        
        # Draw the text
        arcade.draw_text(text, text_x, text_y, font_arcade_color, actual_font_size)
    
    def draw_panel_fallback(self, node_data):
        """Draw Panel node with new positioning system"""
        position = node_data.get("position", [0.0, 0.0])
        rect_size = node_data.get("rect_size", [100.0, 100.0])
        panel_color = node_data.get("panel_color", [0.2, 0.2, 0.2, 1.0])
        border_width = node_data.get("border_width", 0.0)
        border_color = node_data.get("border_color", [0.0, 0.0, 0.0, 1.0])
        
        # Calculate UI position and size with percentage support
        ui_x, ui_y = self.calculate_ui_position(position, rect_size)
        ui_width, ui_height = self.calculate_ui_size(rect_size)
        
        # Convert colors to arcade format
        panel_arcade_color = (
            int(panel_color[0] * 255),
            int(panel_color[1] * 255),
            int(panel_color[2] * 255),
            int(panel_color[3] * 255)
        )
        
        # Draw panel background
        arcade.draw_lbwh_rectangle_filled(
            ui_x - ui_width/2, ui_y - ui_height/2, ui_width, ui_height,
            panel_arcade_color
        )
        
        # Draw border if enabled
        if border_width > 0:
            border_arcade_color = (
                int(border_color[0] * 255),
                int(border_color[1] * 255),
                int(border_color[2] * 255)
            )
            arcade.draw_lbwh_rectangle_outline(
                ui_x - ui_width/2, ui_y - ui_height/2, ui_width, ui_height,
                border_arcade_color, int(border_width)
            )
    
    def draw_control_fallback(self, node_data):
        """Draw Control node (invisible container)"""
        # Control nodes are invisible - no rendering needed
        pass
                        
    def on_key_press(self, key, modifiers):
        """Handle key press"""
        if key == arcade.key.ESCAPE:
            self.close()

def main():
    """Run the UI positioning test"""
    print("UI Positioning Test")
    print("=" * 50)
    print("This test demonstrates:")
    print("- Fixed positioning relative to game viewport")
    print("- Percentage-based positioning and sizing")
    print("- Proper scaling on window resize")
    print("- Camera-independent UI positioning")
    print()
    
    window = UIPositioningTestWindow()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
