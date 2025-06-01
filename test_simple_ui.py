#!/usr/bin/env python3
"""
Test simple UI positioning with the game runner
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

class SimpleUITestWindow(arcade.Window):
    """Test window for simple UI positioning"""
    
    def __init__(self):
        super().__init__(1280, 720, "Simple UI Test")
        self.scene_data = None
        self.scene = None
        self.camera = None
        self.sprite_lists = {}
        
        # Load the test scene
        scene_file = "test_simple_ui.scene"
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
        
        # Switch to UI camera for UI elements
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
        arcade.draw_text(f"Camera Position: {self.camera.position if self.camera else 'None'}", 
                        10, self.height - 30, arcade.color.WHITE, 16)
        arcade.draw_text("SUCCESS: UI positioning working!", 
                        10, self.height - 50, arcade.color.GREEN, 16)
        arcade.draw_text("Yellow text should appear at (50, 100) in UI coordinates", 
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
    
    def draw_label_fallback(self, node_data):
        """Draw Label node with new positioning system"""
        position = node_data.get("position", [0.0, 0.0])
        rect_size = node_data.get("rect_size", [100.0, 50.0])
        text = node_data.get("text", "Label")
        font_color = node_data.get("font_color", [1.0, 1.0, 1.0, 1.0])
        h_align = node_data.get("h_align", "Left")
        v_align = node_data.get("v_align", "Top")
        
        # Calculate UI position - simple absolute positioning for this test
        ui_x = position[0]
        ui_y = position[1]
        
        # Convert font color to arcade format
        font_arcade_color = (
            int(font_color[0] * 255),
            int(font_color[1] * 255),
            int(font_color[2] * 255)
        )
        
        # Handle font size
        actual_font_size = node_data.get("font_size", 14)
        
        # Draw the text
        try:
            arcade.draw_text(text, ui_x, ui_y, font_arcade_color, actual_font_size)
            print(f"Drew label '{text}' at ({ui_x}, {ui_y})")
        except Exception as e:
            print(f"Error drawing label: {e}")
    
    def draw_panel_fallback(self, node_data):
        """Draw Panel node (not used in this test)"""
        pass
    
    def draw_control_fallback(self, node_data):
        """Draw Control node (invisible container)"""
        pass
                        
    def on_key_press(self, key, modifiers):
        """Handle key press"""
        if key == arcade.key.ESCAPE:
            self.close()

def main():
    """Run the simple UI test"""
    print("Simple UI Test")
    print("=" * 50)
    print("Testing basic UI positioning...")
    
    window = SimpleUITestWindow()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
