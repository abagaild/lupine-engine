"""
Physics System for Lupine Engine
Integrates Pymunk physics engine with Lupine Engine nodes
"""

import pymunk
import pymunk.pygame_util
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Import scene nodes
from .scene import Node2D


class PhysicsBodyType(Enum):
    """Physics body types"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    KINEMATIC = "kinematic"


@dataclass
class PhysicsContact:
    """Physics contact information"""
    body_a: 'PhysicsBody'
    body_b: 'PhysicsBody'
    point: Tuple[float, float]
    normal: Tuple[float, float]
    impulse: float


class PhysicsBody:
    """Wrapper for Pymunk body with Lupine Engine integration"""
    
    def __init__(self, node: Node2D, body_type: PhysicsBodyType = PhysicsBodyType.DYNAMIC):
        self.node = node
        self.body_type = body_type
        self.pymunk_body: Optional[pymunk.Body] = None
        self.pymunk_shapes: List[pymunk.Shape] = []
        self.collision_callbacks: List[callable] = []
        
        # Physics properties
        self.mass = 1.0
        self.moment = pymunk.moment_for_box(1.0, (32, 32))
        self.friction = 0.7
        self.elasticity = 0.0
        
        # Collision filtering
        self.collision_layer = 1
        self.collision_mask = 1
        
        # Create Pymunk body
        self._create_pymunk_body()
    
    def _create_pymunk_body(self):
        """Create the Pymunk body based on type"""
        if self.body_type == PhysicsBodyType.STATIC:
            self.pymunk_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        elif self.body_type == PhysicsBodyType.KINEMATIC:
            self.pymunk_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        else:  # DYNAMIC
            self.pymunk_body = pymunk.Body(self.mass, self.moment)
        
        # Set initial position from node
        if hasattr(self.node, 'position'):
            pos = self.node.position
            if isinstance(pos, list) and len(pos) >= 2:
                self.pymunk_body.position = float(pos[0]), float(pos[1])
            elif isinstance(pos, tuple) and len(pos) >= 2:
                self.pymunk_body.position = float(pos[0]), float(pos[1])
        elif hasattr(self.node, 'get_position'):
            pos = self.node.get_position()
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                self.pymunk_body.position = float(pos[0]), float(pos[1])
        elif hasattr(self.node, 'get_global_position'):
            pos = self.node.get_global_position()
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                self.pymunk_body.position = float(pos[0]), float(pos[1])
        else:
            # Default position if no position property found
            self.pymunk_body.position = 0.0, 0.0
        
        # Set user data for collision callbacks
        self.pymunk_body.user_data = self
    
    def add_collision_shape(self, shape_node):
        """Add a collision shape to this body"""
        # Use duck typing instead of isinstance
        shape_type = getattr(shape_node, 'type', None)
        if shape_type == "CollisionShape2D":
            self._add_collision_shape_2d(shape_node)
        elif shape_type == "CollisionPolygon2D":
            self._add_collision_polygon_2d(shape_node)
    
    def _add_collision_shape_2d(self, shape_node: Node2D):
        """Add CollisionShape2D to body"""
        shape_type = getattr(shape_node, 'shape', 'rectangle')

        # Get shape position relative to body (collision shape offset)
        shape_position = getattr(shape_node, 'position', [0.0, 0.0])
        if not isinstance(shape_position, list) or len(shape_position) < 2:
            shape_position = [0.0, 0.0]

        shape_offset = (float(shape_position[0]), float(shape_position[1]))

        if shape_type == 'rectangle':
            size = getattr(shape_node, 'size', [32, 32])
            # Handle nested lists/tuples
            if isinstance(size, (list, tuple)) and len(size) >= 2:
                # Extract width and height, handling nested structures
                width_val = size[0]
                height_val = size[1]

                # If width/height are themselves lists/tuples, take the first element
                while isinstance(width_val, (list, tuple)) and len(width_val) > 0:
                    width_val = width_val[0]
                while isinstance(height_val, (list, tuple)) and len(height_val) > 0:
                    height_val = height_val[0]

                # Ensure we have numeric values
                try:
                    width, height = float(width_val), float(height_val)
                except (ValueError, TypeError):
                    width, height = 32.0, 32.0

                # Create box vertices manually to apply offset
                half_width = width / 2.0
                half_height = height / 2.0
                vertices = [
                    (shape_offset[0] - half_width, shape_offset[1] - half_height),  # bottom-left
                    (shape_offset[0] + half_width, shape_offset[1] - half_height),  # bottom-right
                    (shape_offset[0] + half_width, shape_offset[1] + half_height),  # top-right
                    (shape_offset[0] - half_width, shape_offset[1] + half_height)   # top-left
                ]
                shape = pymunk.Poly(self.pymunk_body, vertices)
            else:
                # Default box with offset
                half_width = 16.0
                half_height = 16.0
                vertices = [
                    (shape_offset[0] - half_width, shape_offset[1] - half_height),
                    (shape_offset[0] + half_width, shape_offset[1] - half_height),
                    (shape_offset[0] + half_width, shape_offset[1] + half_height),
                    (shape_offset[0] - half_width, shape_offset[1] + half_height)
                ]
                shape = pymunk.Poly(self.pymunk_body, vertices)

        elif shape_type == 'circle':
            radius = float(getattr(shape_node, 'radius', 16.0))
            shape = pymunk.Circle(self.pymunk_body, radius, shape_offset)

        elif shape_type == 'capsule':
            size = getattr(shape_node, 'size', [32, 32])
            if isinstance(size, list) and len(size) >= 2:
                width, height = size[0], size[1]
                # Create capsule as a segment with radius
                radius = min(width, height) / 4
                segment_length = max(width, height) - 2 * radius
                if width > height:
                    # Horizontal capsule
                    a = (shape_offset[0] - segment_length/2, shape_offset[1])
                    b = (shape_offset[0] + segment_length/2, shape_offset[1])
                else:
                    # Vertical capsule
                    a = (shape_offset[0], shape_offset[1] - segment_length/2)
                    b = (shape_offset[0], shape_offset[1] + segment_length/2)
                shape = pymunk.Segment(self.pymunk_body, a, b, radius)
            else:
                shape = pymunk.Poly.create_box(self.pymunk_body, (32, 32), radius=0.0)

        elif shape_type == 'polygon':
            points = getattr(shape_node, 'points', [[0, 0], [32, 0], [32, 32], [0, 32]])
            # Convert to tuples for pymunk and apply offset
            vertices = []
            for point in points:
                if isinstance(point, list) and len(point) >= 2:
                    vertices.append((point[0] + shape_offset[0], point[1] + shape_offset[1]))

            if len(vertices) >= 3:
                try:
                    shape = pymunk.Poly(self.pymunk_body, vertices)
                except ValueError:
                    # Invalid polygon, fall back to box
                    print(f"Warning: Invalid polygon shape, using box instead")
                    shape = pymunk.Poly.create_box(self.pymunk_body, (32, 32), radius=0.0)
            else:
                shape = pymunk.Poly.create_box(self.pymunk_body, (32, 32), radius=0.0)

        elif shape_type == 'line':
            line_start = getattr(shape_node, 'line_start', [0.0, 0.0])
            line_end = getattr(shape_node, 'line_end', [32.0, 0.0])
            if isinstance(line_start, list) and isinstance(line_end, list) and len(line_start) >= 2 and len(line_end) >= 2:
                # Apply offset to line points
                start = (line_start[0] + shape_offset[0], line_start[1] + shape_offset[1])
                end = (line_end[0] + shape_offset[0], line_end[1] + shape_offset[1])
                shape = pymunk.Segment(self.pymunk_body, start, end, 1.0)  # thickness
            else:
                shape = pymunk.Poly.create_box(self.pymunk_body, (32, 32), radius=0.0)

        elif shape_type == 'segment':
            point_a = getattr(shape_node, 'point_a', [0, 0])
            point_b = getattr(shape_node, 'point_b', [32, 0])
            if isinstance(point_a, list) and isinstance(point_b, list):
                # Apply offset to segment points
                a = (point_a[0] + shape_offset[0], point_a[1] + shape_offset[1])
                b = (point_b[0] + shape_offset[0], point_b[1] + shape_offset[1])
                shape = pymunk.Segment(self.pymunk_body, a, b, 1.0)
            else:
                shape = pymunk.Poly.create_box(self.pymunk_body, (32, 32), radius=0.0)

        else:
            # Default to box
            shape = pymunk.Poly.create_box(self.pymunk_body, (32, 32), radius=0.0)
        
        # Set shape properties
        shape.friction = self.friction
        shape.elasticity = self.elasticity
        shape.collision_type = self.collision_layer
        shape.filter = pymunk.ShapeFilter(categories=self.collision_layer, mask=self.collision_mask)
        shape.user_data = self
        
        self.pymunk_shapes.append(shape)
    
    def _add_collision_polygon_2d(self, polygon_node: Node2D):
        """Add CollisionPolygon2D to body"""
        polygon = getattr(polygon_node, 'polygon', [[0, 0], [32, 0], [32, 32], [0, 32]])
        
        # Convert polygon format
        vertices = []
        for vertex in polygon:
            if isinstance(vertex, list) and len(vertex) >= 2:
                vertices.append((vertex[0], vertex[1]))
        
        if len(vertices) >= 3:
            try:
                shape = pymunk.Poly(self.pymunk_body, vertices)
                shape.friction = self.friction
                shape.elasticity = self.elasticity
                shape.collision_type = self.collision_layer
                shape.filter = pymunk.ShapeFilter(categories=self.collision_layer, mask=self.collision_mask)
                shape.user_data = self
                
                self.pymunk_shapes.append(shape)
            except Exception as e:
                print(f"Error creating polygon shape: {e}")
                # Fallback to box
                shape = pymunk.Poly.create_box(self.pymunk_body, (32, 32))
                shape.friction = self.friction
                shape.elasticity = self.elasticity
                shape.collision_type = self.collision_layer
                shape.filter = pymunk.ShapeFilter(categories=self.collision_layer, mask=self.collision_mask)
                shape.user_data = self
                
                self.pymunk_shapes.append(shape)
    
    def update_from_node(self):
        """Update physics body from node properties"""
        if not self.pymunk_body:
            return
        
        # Update position
        if hasattr(self.node, 'position'):
            pos = self.node.position
            if isinstance(pos, list) and len(pos) >= 2:
                self.pymunk_body.position = pos[0], pos[1]
        
        # Update rotation
        if hasattr(self.node, 'rotation'):
            self.pymunk_body.angle = self.node.rotation
        
        # Update physics properties for dynamic bodies
        if hasattr(self.node, 'type') and self.node.type == "RigidBody2D":
            self.mass = getattr(self.node, 'mass', 1.0)
            self.collision_layer = getattr(self.node, 'collision_layer', 1)
            self.collision_mask = getattr(self.node, 'collision_mask', 1)
            
            if self.body_type == PhysicsBodyType.DYNAMIC:
                self.pymunk_body.mass = self.mass
    
    def update_node_from_physics(self):
        """Update node from physics body"""
        if not self.pymunk_body:
            return

        # Update position
        if hasattr(self.node, 'position'):
            pos = self.pymunk_body.position
            self.node.position = [pos.x, pos.y]

        # Update rotation
        if hasattr(self.node, 'rotation'):
            self.node.rotation = self.pymunk_body.angle

    def update_physics_from_node(self):
        """Update physics body from node"""
        if not self.pymunk_body:
            return

        # Update position
        if hasattr(self.node, 'position'):
            pos = self.node.position
            if isinstance(pos, list) and len(pos) >= 2:
                self.pymunk_body.position = pos[0], pos[1]

        # Update rotation
        if hasattr(self.node, 'rotation'):
            self.pymunk_body.angle = self.node.rotation
    
    def apply_force(self, force: Tuple[float, float], point: Optional[Tuple[float, float]] = None):
        """Apply force to the body"""
        if self.pymunk_body and self.body_type == PhysicsBodyType.DYNAMIC:
            if point:
                self.pymunk_body.apply_force_at_world_point(force, point)
            else:
                self.pymunk_body.apply_force_at_local_point(force, (0, 0))
    
    def apply_impulse(self, impulse: Tuple[float, float], point: Optional[Tuple[float, float]] = None):
        """Apply impulse to the body"""
        if self.pymunk_body and self.body_type == PhysicsBodyType.DYNAMIC:
            if point:
                self.pymunk_body.apply_impulse_at_world_point(impulse, point)
            else:
                self.pymunk_body.apply_impulse_at_local_point(impulse, (0, 0))
    
    def set_velocity(self, velocity: Tuple[float, float]):
        """Set body velocity"""
        if self.pymunk_body:
            self.pymunk_body.velocity = velocity
    
    def get_velocity(self) -> Tuple[float, float]:
        """Get body velocity"""
        if self.pymunk_body:
            vel = self.pymunk_body.velocity
            return (vel.x, vel.y)
        return (0, 0)


class PhysicsWorld:
    """Physics world manager using Pymunk"""
    
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, -981)  # Default gravity (pixels/s²)
        
        # Physics bodies
        self.bodies: Dict[str, PhysicsBody] = {}
        self.areas: Dict[str, Dict] = {}
        
        # Collision handlers
        self.collision_handlers: Dict[int, callable] = {}
        
        # Physics settings
        self.time_step = 1.0 / 60.0  # 60 FPS
        self.velocity_iterations = 10
        self.position_iterations = 10
        
        # Setup default collision handler
        self._setup_collision_handlers()
    
    def _setup_collision_handlers(self):
        """Setup collision detection handlers"""
        def collision_handler(arbiter, space, data):
            """Handle collisions between bodies"""
            shape_a, shape_b = arbiter.shapes
            body_a = shape_a.user_data if shape_a.user_data else None
            body_b = shape_b.user_data if shape_b.user_data else None

            if body_a and body_b:
                print(f"[COLLISION] {body_a.node.name} collided with {body_b.node.name}")

                # Check if either shape is a sensor (Area2D)
                if shape_a.sensor or shape_b.sensor:
                    self._handle_sensor_collision(body_a, body_b, shape_a.sensor, shape_b.sensor, True)
                else:
                    # Regular collision
                    # Get contact information
                    contact_point_set = arbiter.contact_point_set
                    if len(contact_point_set.points) > 0:
                        point = contact_point_set.points[0].point_a
                        normal = contact_point_set.normal
                        impulse = contact_point_set.points[0].distance

                        # Create contact info
                        contact = PhysicsContact(
                            body_a=body_a,
                            body_b=body_b,
                            point=(point.x, point.y),
                            normal=(normal.x, normal.y),
                            impulse=impulse
                        )

                        # Notify bodies of collision
                        self._notify_collision(body_a, body_b, contact)
                        self._notify_collision(body_b, body_a, contact)

            return True

        def sensor_separate_handler(arbiter, space, data):
            """Handle sensor separation"""
            shape_a, shape_b = arbiter.shapes
            body_a = shape_a.user_data if shape_a.user_data else None
            body_b = shape_b.user_data if shape_b.user_data else None

            if body_a and body_b:
                if shape_a.sensor or shape_b.sensor:
                    self._handle_sensor_collision(body_a, body_b, shape_a.sensor, shape_b.sensor, False)

            return True

        # Set default collision handler
        default_handler = self.space.add_default_collision_handler()
        default_handler.begin = collision_handler
        default_handler.separate = sensor_separate_handler
    
    def _handle_sensor_collision(self, body_a: PhysicsBody, body_b: PhysicsBody,
                                a_is_sensor: bool, b_is_sensor: bool, entering: bool):
        """Handle sensor (Area2D) collision events"""
        # Determine which is the sensor and which is the body
        sensor_body = body_a if a_is_sensor else body_b
        other_body = body_b if a_is_sensor else body_a

        # Get the area node
        area_name = sensor_body.node.name
        if area_name in self.areas:
            area_info = self.areas[area_name]
            area_node = area_info['node']

            if entering:
                # Body entered area
                if hasattr(other_body.node, 'type'):
                    if other_body.node.type == "Area2D":
                        # Area entered area
                        if other_body.node not in area_info['overlapping_areas']:
                            area_info['overlapping_areas'].add(other_body.node)
                            if hasattr(area_node, 'emit_signal'):
                                area_node.emit_signal("area_entered", other_body.node)
                    else:
                        # Body entered area
                        if other_body.node not in area_info['overlapping_bodies']:
                            area_info['overlapping_bodies'].add(other_body.node)
                            if hasattr(area_node, 'emit_signal'):
                                area_node.emit_signal("body_entered", other_body.node)
            else:
                # Body exited area
                if hasattr(other_body.node, 'type'):
                    if other_body.node.type == "Area2D":
                        # Area exited area
                        if other_body.node in area_info['overlapping_areas']:
                            area_info['overlapping_areas'].remove(other_body.node)
                            if hasattr(area_node, 'emit_signal'):
                                area_node.emit_signal("area_exited", other_body.node)
                    else:
                        # Body exited area
                        if other_body.node in area_info['overlapping_bodies']:
                            area_info['overlapping_bodies'].remove(other_body.node)
                            if hasattr(area_node, 'emit_signal'):
                                area_node.emit_signal("body_exited", other_body.node)

    def _notify_collision(self, body: PhysicsBody, other_body: PhysicsBody, contact: PhysicsContact):
        """Notify a body of collision"""
        for callback in body.collision_callbacks:
            try:
                callback(other_body, contact)
            except Exception as e:
                print(f"Error in collision callback: {e}")
                import traceback
                traceback.print_exc()
    
    def add_node(self, node: Node2D) -> Optional[PhysicsBody]:
        """Add a physics node to the world - dynamically detect physics node types"""
        # Use node type string for dynamic detection instead of isinstance
        node_type = getattr(node, 'type', None)

        if node_type == "RigidBody2D":
            return self._add_rigid_body(node)
        elif node_type == "StaticBody2D":
            return self._add_static_body(node)
        elif node_type == "KinematicBody2D":
            return self._add_kinematic_body(node)
        elif node_type == "Area2D":
            return self._add_area(node)

        # Also check for physics-related properties to detect custom physics nodes
        if hasattr(node, 'physics_body_type'):
            body_type = getattr(node, 'physics_body_type', None)
            if body_type == "rigid":
                return self._add_rigid_body(node)
            elif body_type == "static":
                return self._add_static_body(node)
            elif body_type == "kinematic":
                return self._add_kinematic_body(node)
            elif body_type == "area":
                return self._add_area(node)

        return None
    
    def _add_rigid_body(self, node: Node2D) -> PhysicsBody:
        """Add RigidBody2D to physics world"""
        body = PhysicsBody(node, PhysicsBodyType.DYNAMIC)
        
        # Set physics properties
        body.mass = getattr(node, 'mass', 1.0)
        body.collision_layer = getattr(node, 'collision_layer', 1)
        body.collision_mask = getattr(node, 'collision_mask', 1)
        
        # Add collision shapes from children
        for child in node.children:
            if hasattr(child, 'type') and child.type in ["CollisionShape2D", "CollisionPolygon2D"]:
                body.add_collision_shape(child)
        
        # Add to space
        self.space.add(body.pymunk_body)
        for shape in body.pymunk_shapes:
            self.space.add(shape)
        
        # Use unique key to avoid name collisions
        unique_key = f"{node.name}_{id(node)}"
        self.bodies[unique_key] = body
        return body
    
    def _add_static_body(self, node: Node2D) -> PhysicsBody:
        """Add StaticBody2D to physics world"""
        body = PhysicsBody(node, PhysicsBodyType.STATIC)
        
        body.collision_layer = getattr(node, 'collision_layer', 1)
        body.collision_mask = getattr(node, 'collision_mask', 1)
        
        # Add collision shapes from children
        for child in node.children:
            if hasattr(child, 'type') and child.type in ["CollisionShape2D", "CollisionPolygon2D"]:
                body.add_collision_shape(child)
        
        # Add to space
        self.space.add(body.pymunk_body)
        for shape in body.pymunk_shapes:
            self.space.add(shape)
        
        # Use unique key to avoid name collisions
        unique_key = f"{node.name}_{id(node)}"
        self.bodies[unique_key] = body
        return body
    
    def _add_kinematic_body(self, node: Node2D) -> PhysicsBody:
        """Add KinematicBody2D to physics world"""
        body = PhysicsBody(node, PhysicsBodyType.KINEMATIC)
        
        body.collision_layer = getattr(node, 'collision_layer', 1)
        body.collision_mask = getattr(node, 'collision_mask', 1)
        
        # Add collision shapes from children
        for child in node.children:
            if hasattr(child, 'type') and child.type in ["CollisionShape2D", "CollisionPolygon2D"]:
                body.add_collision_shape(child)
        
        # Add to space
        self.space.add(body.pymunk_body)
        for shape in body.pymunk_shapes:
            self.space.add(shape)
        
        # Use unique key to avoid name collisions
        unique_key = f"{node.name}_{id(node)}"
        self.bodies[unique_key] = body
        return body
    
    def _add_area(self, node: Node2D):
        """Add Area2D to physics world (sensor)"""
        # Create a kinematic body for the area (sensors don't need physics)
        body = PhysicsBody(node, PhysicsBodyType.KINEMATIC)

        body.collision_layer = getattr(node, 'collision_layer', 1)
        body.collision_mask = getattr(node, 'collision_mask', 1)

        # Add collision shapes from children
        for child in node.children:
            if hasattr(child, 'type') and child.type in ["CollisionShape2D", "CollisionPolygon2D"]:
                body.add_collision_shape(child)

        # Add to space
        self.space.add(body.pymunk_body)
        for shape in body.pymunk_shapes:
            # Make shapes sensors (no collision response)
            shape.sensor = True
            self.space.add(shape)

        # Store area for sensor collision handling
        # Use unique key to avoid name collisions
        unique_key = f"{node.name}_{id(node)}"
        self.areas[unique_key] = {
            'node': node,
            'body': body,
            'overlapping_bodies': set(),
            'overlapping_areas': set()
        }

        self.bodies[unique_key] = body
        return body
    
    def remove_node(self, node_name: str):
        """Remove a node from physics world"""
        if node_name in self.bodies:
            body = self.bodies[node_name]
            
            # Remove from space
            for shape in body.pymunk_shapes:
                self.space.remove(shape)
            self.space.remove(body.pymunk_body)
            
            del self.bodies[node_name]
    
    def step(self, dt: float):
        """Step the physics simulation"""
        self.space.step(dt)

        # Update nodes from physics (but not kinematic bodies - they control themselves)
        for body in self.bodies.values():
            # Only update dynamic and static bodies from physics
            # Kinematic bodies are controlled by their nodes
            if body.body_type != PhysicsBodyType.KINEMATIC:
                body.update_node_from_physics()


    
    def set_gravity(self, gravity: Tuple[float, float]):
        """Set world gravity"""
        self.space.gravity = gravity
    
    def get_body(self, node_name: str) -> Optional[PhysicsBody]:
        """Get physics body by node name"""
        return self.bodies.get(node_name)

    def get_body_by_node(self, node) -> Optional[PhysicsBody]:
        """Get physics body by node reference"""
        for body in self.bodies.values():
            if body.node == node:
                return body
        return None
    
    def query_point(self, point: Tuple[float, float]) -> List[PhysicsBody]:
        """Query bodies at a point"""
        results = []
        point_query = self.space.point_query_nearest(point, 0, pymunk.ShapeFilter())
        if point_query:
            body = point_query.shape.user_data
            if body:
                results.append(body)
        return results
    
    def raycast(self, start: Tuple[float, float], end: Tuple[float, float],
                collision_mask: int = 0xFFFFFFFF, exclude_sensors: bool = True) -> Optional[Dict]:
        """Perform raycast and return hit information"""
        # Create shape filter
        shape_filter = pymunk.ShapeFilter(mask=collision_mask)

        hit = self.space.segment_query_first(start, end, 0, shape_filter)
        if hit:
            # Skip sensors if requested
            if exclude_sensors and hasattr(hit.shape, 'sensor') and hit.shape.sensor:
                return None

            body = hit.shape.user_data if hit.shape.user_data else None
            return {
                'body': body,
                'point': (hit.point.x, hit.point.y),
                'normal': (hit.normal.x, hit.normal.y),
                'distance': hit.alpha
            }
        return None

    def raycast_all(self, start: Tuple[float, float], end: Tuple[float, float],
                    collision_mask: int = 0xFFFFFFFF, exclude_sensors: bool = True) -> List[Dict]:
        """Perform raycast and return all hit information"""
        shape_filter = pymunk.ShapeFilter(mask=collision_mask)
        hits = self.space.segment_query(start, end, 0, shape_filter)

        results = []
        for hit in hits:
            # Skip sensors if requested
            if exclude_sensors and hasattr(hit.shape, 'sensor') and hit.shape.sensor:
                continue

            body = hit.shape.user_data if hit.shape.user_data else None
            results.append({
                'body': body,
                'point': (hit.point.x, hit.point.y),
                'normal': (hit.normal.x, hit.normal.y),
                'distance': hit.alpha
            })

        return results

    def shape_cast(self, shape_type: str, size: Tuple[float, float],
                   start: Tuple[float, float], end: Tuple[float, float],
                   collision_mask: int = 0xFFFFFFFF) -> Optional[Dict]:
        """Cast a shape and return first hit"""
        # Create a temporary body and shape for casting
        temp_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        temp_body.position = start

        if shape_type == "circle":
            temp_shape = pymunk.Circle(temp_body, size[0])
        else:  # rectangle
            temp_shape = pymunk.Poly.create_box(temp_body, size)

        temp_shape.filter = pymunk.ShapeFilter(mask=collision_mask)

        # Perform shape cast (this is a simplified version)
        # In a full implementation, you'd move the shape along the path
        # and check for intersections at each step

        # For now, just do a point query at the end position
        temp_body.position = end
        point_query = self.space.point_query_nearest(end, 0, pymunk.ShapeFilter(mask=collision_mask))

        if point_query:
            body = point_query.shape.user_data if point_query.shape.user_data else None
            return {
                'body': body,
                'point': (point_query.point.x, point_query.point.y),
                'normal': (0, 1),  # Simplified normal
                'distance': point_query.distance
            }

        return None
