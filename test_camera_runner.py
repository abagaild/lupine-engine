#!/usr/bin/env python3
"""
Test script to run the camera alignment test scene directly
"""

import sys
import os
import tempfile
import subprocess

def create_test_runner():
    """Create a test runner script for the camera alignment scene"""
    
    # Get the Lupine Engine path
    lupine_engine_path = os.path.dirname(os.path.abspath(__file__))
    scene_file_path = os.path.join(lupine_engine_path, "test_camera_alignment.scene")
    
    # Create the runner script content
    runner_content = f'''
import sys
import os
sys.path.insert(0, r"{lupine_engine_path}")

import arcade
import json
from pathlib import Path

# Import LSC runtime for script execution
try:
    from core.lsc import LSCRuntime, LSCInterpreter
    from core.lsc.interpreter import execute_lsc_script
    from core.scene import Scene, Node, Node2D, Sprite, Camera2D
    LSC_AVAILABLE = True
except ImportError as e:
    print(f"LSC not available: {{e}}")
    LSC_AVAILABLE = False

class CameraTestWindow(arcade.Window):
    """Test window for camera alignment"""
    
    def __init__(self):
        super().__init__(1280, 720, "Camera Alignment Test")
        self.scene_data = None
        self.scene = None
        self.camera = None
        self.sprite_lists = {{}}
        self.lsc_runtime = None
        
        # Load the test scene
        self.load_scene(r"{scene_file_path}")
        
    def load_scene(self, scene_file):
        """Load the test scene"""
        try:
            with open(scene_file, 'r') as f:
                self.scene_data = json.load(f)
            print(f"Loaded test scene: {{self.scene_data.get('name', 'Unknown')}}")
            
            # Load scene using proper Scene class if available
            if LSC_AVAILABLE:
                self.scene = Scene.load_from_file(scene_file)
                print("Using LSC Scene system")
            else:
                print("Using fallback JSON parsing")
                
        except Exception as e:
            print(f"Error loading scene: {{e}}")
            
    def setup(self):
        """Set up the test"""
        arcade.set_background_color(arcade.color.DARK_GRAY)
        
        # Initialize sprite lists
        self.sprite_lists = {{
            "sprites": arcade.SpriteList(),
            "ui": arcade.SpriteList()
        }}
        
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
            print(f"Camera initialized: position={{self.camera.position}}, viewport={{self.camera.viewport}}")
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
            print(f"Found camera: {{node.name}} at {{position}} -> arcade {{(camera_x, camera_y)}}")
            
        elif isinstance(node, dict) and node.get("type") == "Camera2D" and node.get("current", False):
            self.camera = arcade.Camera2D()
            position = node.get("position", [0.0, 0.0])
            zoom = node.get("zoom", [1.0, 1.0])
            offset = node.get("offset", [0.0, 0.0])
            
            camera_x = position[0] + offset[0]
            camera_y = position[1] + offset[1]
            
            self.camera.position = (camera_x, camera_y)
            self.camera.zoom = zoom[0] if isinstance(zoom, list) else zoom
            print(f"Found camera: {{node.get('name', 'Camera2D')}} at {{position}} -> arcade {{(camera_x, camera_y)}}")
            
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
                    full_path = os.path.join(r"{lupine_engine_path}", texture_path)
                    texture = arcade.load_texture(full_path)
                    arcade_sprite.texture = texture
                    print(f"Loaded texture for {{node.name}}: {{texture_path}}")
                except Exception as e:
                    print(f"Failed to load texture {{texture_path}}: {{e}}")
                    
            self.sprite_lists["sprites"].append(arcade_sprite)
            print(f"Created sprite: {{node.name}} at {{node.position}}")
            
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
                    full_path = os.path.join(r"{lupine_engine_path}", texture_path)
                    texture = arcade.load_texture(full_path)
                    arcade_sprite.texture = texture
                    print(f"Loaded texture: {{texture_path}}")
                except Exception as e:
                    print(f"Failed to load texture {{texture_path}}: {{e}}")
                    
            self.sprite_lists["sprites"].append(arcade_sprite)
            print(f"Created sprite: {{node_data.get('name', 'Sprite')}} at {{position}}")
            
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
        
        # Draw UI elements with default camera
        self.ctx.default_camera.use()
        
        # Draw test info
        arcade.draw_text(f"Camera Position: {{self.camera.position if self.camera else 'None'}}", 
                        10, self.height - 30, arcade.color.WHITE, 16)
        arcade.draw_text(f"Sprites: {{len(self.sprite_lists['sprites'])}}", 
                        10, self.height - 50, arcade.color.WHITE, 16)
        arcade.draw_text("Expected: Center sprite should be in center of view", 
                        10, self.height - 70, arcade.color.YELLOW, 16)
        arcade.draw_text("Expected: Offset sprite should be 100px right, 100px up from center", 
                        10, self.height - 90, arcade.color.YELLOW, 16)
                        
    def on_key_press(self, key, modifiers):
        """Handle key press"""
        if key == arcade.key.ESCAPE:
            self.close()

def main():
    """Run the camera test"""
    print("🎯 Camera Alignment Test")
    print("=" * 50)
    
    window = CameraTestWindow()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
'''
    
    return runner_content

def main():
    """Run the camera alignment test"""
    print("🔧 Creating Camera Alignment Test")
    print("=" * 50)
    
    # Create temporary runner script
    runner_content = create_test_runner()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(runner_content)
        temp_script = f.name
    
    try:
        print(f"Running test script: {temp_script}")
        result = subprocess.run([sys.executable, temp_script], 
                              capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        print(f"Return code: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        print("Test completed (timeout reached)")
    except Exception as e:
        print(f"Error running test: {e}")
    finally:
        # Clean up
        try:
            os.unlink(temp_script)
        except:
            pass

if __name__ == "__main__":
    main()
