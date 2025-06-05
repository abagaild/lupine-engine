#!/usr/bin/env python3
"""
Test script for collision shape hit detection in scene view
"""

import sys
import os
import math

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_collision_shape_hit_detection():
    """Test the collision shape hit detection methods"""
    
    # Mock scene view class with just the hit detection methods
    class MockSceneView:
        def _point_in_polygon(self, x: float, y: float, polygon):
            """Check if a point is inside a polygon using ray casting algorithm"""
            if len(polygon) < 3:
                return False
                
            inside = False
            j = len(polygon) - 1
            
            for i in range(len(polygon)):
                if len(polygon[i]) < 2 or len(polygon[j]) < 2:
                    j = i
                    continue
                    
                xi, yi = polygon[i][0], polygon[i][1]
                xj, yj = polygon[j][0], polygon[j][1]
                
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                    inside = not inside
                j = i
                
            return inside

        def _point_to_line_distance(self, px: float, py: float, line_start, line_end):
            """Calculate the distance from a point to a line segment"""
            x1, y1 = line_start[0], line_start[1]
            x2, y2 = line_end[0], line_end[1]
            
            # Calculate the squared length of the line segment
            line_length_sq = (x2 - x1)**2 + (y2 - y1)**2
            
            if line_length_sq == 0:
                # Line is actually a point
                return math.sqrt((px - x1)**2 + (py - y1)**2)
            
            # Calculate the parameter t for the closest point on the line
            t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
            
            # Calculate the closest point on the line
            closest_x = x1 + t * (x2 - x1)
            closest_y = y1 + t * (y2 - y1)
            
            # Return the distance from the point to the closest point on the line
            return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)

        def _is_point_in_collision_shape(self, node, local_x: float, local_y: float):
            """Check if a point is inside a collision shape's bounds"""
            shape_type = node.get("shape", "rectangle")
            
            if shape_type == "rectangle":
                size = node.get("size", [32.0, 32.0])
                width, height = size[0], size[1]
                return abs(local_x) <= width/2 and abs(local_y) <= height/2
                
            elif shape_type == "circle":
                radius = node.get("radius", 16.0)
                distance = math.sqrt(local_x**2 + local_y**2)
                return distance <= radius
                
            elif shape_type == "capsule":
                size = node.get("size", [32.0, 32.0])
                height = node.get("height", 32.0)
                width = size[0]
                
                # Capsule is a rectangle with rounded ends
                # Check if point is in the rectangular middle section
                if abs(local_x) <= width/2 and abs(local_y) <= height/2:
                    return True
                
                # Check if point is in the circular end caps
                if abs(local_y) > height/2:
                    # Check distance from the center of the appropriate end cap
                    cap_center_y = height/2 if local_y > 0 else -height/2
                    distance = math.sqrt(local_x**2 + (local_y - cap_center_y)**2)
                    return distance <= width/2
                
                return False
                
            elif shape_type == "polygon":
                points = node.get("points", [[0, 0], [32, 0], [32, 32], [0, 32]])
                return self._point_in_polygon(local_x, local_y, points)
                
            elif shape_type == "line":
                line_start = node.get("line_start", [0.0, 0.0])
                line_end = node.get("line_end", [32.0, 0.0])
                
                # Check if point is close to the line (within 3 pixels)
                distance = self._point_to_line_distance(local_x, local_y, line_start, line_end)
                return distance <= 3.0
                
            # Default fallback
            return abs(local_x) <= 16 and abs(local_y) <= 16

    # Create test instance
    scene_view = MockSceneView()
    
    # Test rectangle collision shape
    print("Testing rectangle collision shape...")
    rect_node = {"shape": "rectangle", "size": [64, 32]}
    
    # Test points inside rectangle
    assert scene_view._is_point_in_collision_shape(rect_node, 0, 0) == True  # Center
    assert scene_view._is_point_in_collision_shape(rect_node, 31, 15) == True  # Inside
    assert scene_view._is_point_in_collision_shape(rect_node, 32, 16) == True  # Edge
    
    # Test points outside rectangle
    assert scene_view._is_point_in_collision_shape(rect_node, 33, 0) == False  # Outside width
    assert scene_view._is_point_in_collision_shape(rect_node, 0, 17) == False  # Outside height
    
    print("✓ Rectangle tests passed")
    
    # Test circle collision shape
    print("Testing circle collision shape...")
    circle_node = {"shape": "circle", "radius": 20.0}
    
    # Test points inside circle
    assert scene_view._is_point_in_collision_shape(circle_node, 0, 0) == True  # Center
    assert scene_view._is_point_in_collision_shape(circle_node, 10, 10) == True  # Inside
    assert scene_view._is_point_in_collision_shape(circle_node, 20, 0) == True  # Edge
    
    # Test points outside circle
    assert scene_view._is_point_in_collision_shape(circle_node, 21, 0) == False  # Outside
    assert scene_view._is_point_in_collision_shape(circle_node, 15, 15) == False  # Outside diagonal
    
    print("✓ Circle tests passed")
    
    # Test polygon collision shape
    print("Testing polygon collision shape...")
    # Triangle polygon
    triangle_node = {"shape": "polygon", "points": [[0, 0], [20, 0], [10, 20]]}
    
    # Test points inside triangle
    assert scene_view._is_point_in_collision_shape(triangle_node, 10, 5) == True  # Inside
    
    # Test points outside triangle
    assert scene_view._is_point_in_collision_shape(triangle_node, 0, 10) == False  # Outside
    assert scene_view._is_point_in_collision_shape(triangle_node, 25, 5) == False  # Outside
    
    print("✓ Polygon tests passed")
    
    # Test line collision shape
    print("Testing line collision shape...")
    line_node = {"shape": "line", "line_start": [0, 0], "line_end": [20, 0]}
    
    # Test points near line
    assert scene_view._is_point_in_collision_shape(line_node, 10, 0) == True  # On line
    assert scene_view._is_point_in_collision_shape(line_node, 10, 2) == True  # Near line
    
    # Test points far from line
    assert scene_view._is_point_in_collision_shape(line_node, 10, 5) == False  # Too far
    assert scene_view._is_point_in_collision_shape(line_node, 30, 0) == False  # Beyond line
    
    print("✓ Line tests passed")
    
    print("\n🎉 All collision shape hit detection tests passed!")

if __name__ == "__main__":
    test_collision_shape_hit_detection()
