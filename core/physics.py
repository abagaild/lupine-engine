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
        print(f"[PHYSICS] Adding collision shape to {self.node.name}: {shape_type}")
        if shape_type == "CollisionShape2D":
            self._add_collision_shape_2d(shape_node)
        elif shape_type == "CollisionPolygon2D":
            self._add_collision_polygon_2d(shape_node)
    
    def _add_collision_shape_2d(self, shape_node: Node2D):
        """Add CollisionShape2D to body"""
        shape_type = getattr(shape_node, 'shape', 'rectangle')
        print(f"[PHYSICS] Creating {shape_type} collision shape for {self.node.name}")

        # Get shape position relative to body (collision shape offset)
        shape_position = getattr(shape_node, 'position', [0.0, 0.0])
        if not isinstance(shape_position, list) or len(shape_position) < 2:
            shape_position = [0.0, 0.0]

        shape_offset = (float(shape_position[0]), float(shape_position[1]))
        print(f"[PHYSICS] Shape offset: {shape_offset}")
        print(f"[PHYSICS] Parent body position: {getattr(self.node, 'position', [0.0, 0.0])}")

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

                print(f"[PHYSICS] Rectangle shape size: {width}x{height}")

                # Create box vertices manually to apply offset
                half_width = width / 2.0
                half_height = height / 2.0
                vertices = [
                    (shape_offset[0] - half_width, shape_offset[1] - half_height),  # bottom-left
                    (shape_offset[0] + half_width, shape_offset[1] - half_height),  # bottom-right
                    (shape_offset[0] + half_width, shape_offset[1] + half_height),  # top-right
                    (shape_offset[0] - half_width, shape_offset[1] + half_height)   # top-left
                ]
                print(f"[PHYSICS] Rectangle vertices: {vertices}")
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

        # Store old position for change detection
        old_position = getattr(self.node, 'position', [0, 0]).copy() if hasattr(self.node, 'position') else [0, 0]

        # Update position
        if hasattr(self.node, 'position'):
            pos = self.pymunk_body.position
            self.node.position = [pos.x, pos.y]

        # Update rotation
        if hasattr(self.node, 'rotation'):
            self.node.rotation = self.pymunk_body.angle

        # Check if position changed significantly and mark transform dirty
        new_position = getattr(self.node, 'position', [0, 0])
        if (abs(new_position[0] - old_position[0]) > 0.1 or
            abs(new_position[1] - old_position[1]) > 0.1):
            # Position changed - mark transform as dirty for redrawing
            if hasattr(self.node, '_mark_transform_dirty'):
                self.node._mark_transform_dirty()

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
        self.space.gravity = (0, 981)  # Default gravity (pixels/s²) - positive Y is downward in screen coordinates
        
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

        # Check for inheritance from physics body types (for script-based physics nodes)
        try:
            # Import physics body classes to check inheritance
            from nodes.node2d.KinematicBody2D import KinematicBody2D
            from nodes.node2d.StaticBody2D import StaticBody2D
            from nodes.node2d.Rigidbody2D import RigidBody2D
            from nodes.node2d.Area2D import Area2D

            # Check if the node inherits from any physics body type
            if isinstance(node, KinematicBody2D):
                return self._add_kinematic_body(node)
            elif isinstance(node, StaticBody2D):
                return self._add_static_body(node)
            elif isinstance(node, RigidBody2D):
                return self._add_rigid_body(node)
            elif isinstance(node, Area2D):
                return self._add_area(node)
        except Exception as e:
            print(f"[WARNING] Error checking physics inheritance for {node.name}: {e}")

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
        print(f"[PHYSICS] Adding static body: {node.name}")
        body = PhysicsBody(node, PhysicsBodyType.STATIC)

        body.collision_layer = getattr(node, 'collision_layer', 1)
        body.collision_mask = getattr(node, 'collision_mask', 1)
        print(f"[PHYSICS] Static body collision layer: {body.collision_layer}, mask: {body.collision_mask}")

        # Add collision shapes from children
        collision_shapes_found = 0
        print(f"[PHYSICS] Static body has {len(node.children)} children:")
        for child in node.children:
            child_type = getattr(child, 'type', 'NO_TYPE')
            print(f"[PHYSICS]   Child: {child.name} (type: {child_type})")
            if hasattr(child, 'type') and child.type in ["CollisionShape2D", "CollisionPolygon2D"]:
                print(f"[PHYSICS] Found collision shape child: {child.name} ({child.type})")
                body.add_collision_shape(child)
                collision_shapes_found += 1

        print(f"[PHYSICS] Total collision shapes added: {collision_shapes_found}")

        # Add to space
        self.space.add(body.pymunk_body)
        for shape in body.pymunk_shapes:
            self.space.add(shape)
            print(f"[PHYSICS] Added shape to physics space")

        # Use unique key to avoid name collisions
        unique_key = f"{node.name}_{id(node)}"
        self.bodies[unique_key] = body
        print(f"[PHYSICS] Static body registered with key: {unique_key}")
        return body
    
    def _add_kinematic_body(self, node: Node2D) -> PhysicsBody:
        """Add KinematicBody2D to physics world"""
        print(f"[PHYSICS] Adding kinematic body: {node.name}")
        body = PhysicsBody(node, PhysicsBodyType.KINEMATIC)

        body.collision_layer = getattr(node, 'collision_layer', 1)
        body.collision_mask = getattr(node, 'collision_mask', 1)
        print(f"[PHYSICS] Kinematic body collision layer: {body.collision_layer}, mask: {body.collision_mask}")

        # Add collision shapes from children
        collision_shapes_found = 0
        print(f"[PHYSICS] Kinematic body has {len(node.children)} children:")
        for child in node.children:
            child_type = getattr(child, 'type', 'NO_TYPE')
            print(f"[PHYSICS]   Child: {child.name} (type: {child_type})")
            if hasattr(child, 'type') and child.type in ["CollisionShape2D", "CollisionPolygon2D"]:
                print(f"[PHYSICS] Found collision shape child: {child.name} ({child.type})")
                body.add_collision_shape(child)
                collision_shapes_found += 1

        print(f"[PHYSICS] Total collision shapes added: {collision_shapes_found}")

        # Add to space
        self.space.add(body.pymunk_body)
        for shape in body.pymunk_shapes:
            self.space.add(shape)
            print(f"[PHYSICS] Added shape to physics space")

        # Use unique key to avoid name collisions
        unique_key = f"{node.name}_{id(node)}"
        self.bodies[unique_key] = body
        print(f"[PHYSICS] Kinematic body registered with key: {unique_key}")
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
        # Debug: Print body count every 300 frames (5 seconds at 60fps) - less verbose
        if hasattr(self, '_debug_frame_count'):
            self._debug_frame_count += 1
        else:
            self._debug_frame_count = 0

        if self._debug_frame_count % 300 == 0:
            print(f"[PHYSICS] Step: {len(self.bodies)} bodies, {len(self.space.shapes)} shapes in space")

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

    def get_body_by_pymunk_shape(self, pymunk_shape) -> Optional[PhysicsBody]:
        """Get physics body associated with a pymunk shape"""
        for body in self.bodies.values():
            if pymunk_shape in body.pymunk_shapes:
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
                   collision_mask: int = 0xFFFFFFFF, exclude_body: Optional[PhysicsBody] = None) -> Optional[Dict]:
        """
        Cast a shape along a path and return first hit with proper swept collision detection.

        Args:
            shape_type: "circle" or "rectangle"
            size: (radius,) for circle or (width, height) for rectangle
            start: Starting position (x, y)
            end: Ending position (x, y)
            collision_mask: Collision mask for filtering
            exclude_body: Physics body to exclude from collision (e.g., the casting body itself)

        Returns:
            Dict with collision info or None if no collision:
            {
                'body': PhysicsBody that was hit,
                'point': (x, y) collision point,
                'normal': (x, y) collision normal,
                'distance': 0.0-1.0 distance along path where collision occurred
            }
        """
        import math

        # Calculate movement vector
        move_vector = (end[0] - start[0], end[1] - start[1])
        move_distance = math.sqrt(move_vector[0]**2 + move_vector[1]**2)

        # Handle zero movement
        if move_distance < 0.001:
            return self._check_shape_overlap(shape_type, size, start, collision_mask, exclude_body)

        # Normalize movement vector
        move_dir = (move_vector[0] / move_distance, move_vector[1] / move_distance)

        # Create temporary body and shape for casting
        temp_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        temp_body.position = start

        if shape_type == "circle":
            # For circles, use the first element as radius (size should be (diameter, diameter))
            radius = size[0] / 2.0
            temp_shape = pymunk.Circle(temp_body, radius)
        else:  # rectangle
            temp_shape = pymunk.Poly.create_box(temp_body, size)

        temp_shape.filter = pymunk.ShapeFilter(mask=collision_mask)
        temp_shape.sensor = True  # Make it a sensor so it doesn't affect physics

        # Add to space temporarily for collision detection
        self.space.add(temp_body, temp_shape)

        try:
            # Perform swept collision detection
            result = self._perform_swept_collision(
                temp_body, temp_shape, start, end, move_dir, move_distance,
                collision_mask, exclude_body
            )
            return result
        finally:
            # Always remove temporary shape from space
            self.space.remove(temp_body, temp_shape)

    def _check_shape_overlap(self, shape_type: str, size: Tuple[float, float],
                           position: Tuple[float, float], collision_mask: int,
                           exclude_body: Optional[PhysicsBody] = None) -> Optional[Dict]:
        """Check if shape overlaps with any existing shapes at given position"""
        # Create temporary body and shape
        temp_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        temp_body.position = position

        if shape_type == "circle":
            radius = size[0] / 2.0
            temp_shape = pymunk.Circle(temp_body, radius)
        else:  # rectangle
            temp_shape = pymunk.Poly.create_box(temp_body, size)

        temp_shape.filter = pymunk.ShapeFilter(mask=collision_mask)
        temp_shape.sensor = True

        # Add to space temporarily
        self.space.add(temp_body, temp_shape)

        try:
            # Query for overlapping shapes using more precise collision detection
            for shape in self.space.shapes:
                if shape == temp_shape:
                    continue

                # Skip if this is the excluded body
                if exclude_body and hasattr(shape, 'user_data') and shape.user_data == exclude_body:
                    continue

                # Skip sensors
                if hasattr(shape, 'sensor') and shape.sensor:
                    continue

                # Check for overlap using pymunk's collision detection
                if self._shapes_colliding(temp_shape, shape):
                    body = shape.user_data if hasattr(shape, 'user_data') and shape.user_data else None
                    if body:
                        # Calculate a better collision normal for overlap
                        normal = self._calculate_overlap_normal(temp_shape, shape, position)

                        return {
                            'body': body,
                            'point': position,
                            'normal': normal,
                            'distance': 0.0
                        }

            return None

        finally:
            self.space.remove(temp_body, temp_shape)

    def _calculate_overlap_normal(self, shape1, shape2, position: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate the best normal direction to resolve an overlap"""
        import math

        try:
            # Try to get contact points from collision
            contact_set = shape1.shapes_collide(shape2)
            if contact_set.points:
                # Use the normal from the first contact point
                normal = contact_set.normal
                # Ensure the normal points away from shape2 towards shape1
                return (normal.x, normal.y)
        except Exception as e:
            print(f"[PHYSICS] Error getting contact normal: {e}")

        # Fallback: calculate normal based on shape centers and edges
        try:
            center1 = shape1.body.position
            center2 = shape2.body.position

            # Calculate direction from shape2 to shape1 (direction to push shape1)
            dx = center1.x - center2.x
            dy = center1.y - center2.y

            # If centers are too close, try to find the best separation direction
            # by looking at the shape edges
            length = math.sqrt(dx*dx + dy*dy)
            if length < 0.001:
                # Centers are at same position, try to find edge-based normal
                normal = self._calculate_edge_based_normal(shape1, shape2)
                if normal:
                    return normal
                # If that fails, use a default direction
                return (1.0, 0.0)  # Push to the right
            else:
                return (dx/length, dy/length)
        except Exception as e:
            print(f"[PHYSICS] Error calculating center-based normal: {e}")

        # Final fallback: use upward normal
        return (0.0, -1.0)

    def _calculate_edge_based_normal(self, shape1, shape2) -> Optional[Tuple[float, float]]:
        """Calculate normal based on shape edges when centers overlap"""
        import math

        try:
            # Get bounding boxes
            bb1 = shape1.bb
            bb2 = shape2.bb

            # Calculate overlap amounts in each direction
            overlap_left = bb1.right - bb2.left
            overlap_right = bb2.right - bb1.left
            overlap_top = bb1.bottom - bb2.top
            overlap_bottom = bb2.bottom - bb1.bottom

            # Find the direction with minimum overlap (easiest escape route)
            min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

            if min_overlap == overlap_left:
                return (-1.0, 0.0)  # Push left
            elif min_overlap == overlap_right:
                return (1.0, 0.0)   # Push right
            elif min_overlap == overlap_top:
                return (0.0, 1.0)   # Push up
            else:
                return (0.0, -1.0)  # Push down

        except Exception as e:
            print(f"[PHYSICS] Error calculating edge-based normal: {e}")
            return None

    def _perform_swept_collision(self, temp_body, temp_shape, start: Tuple[float, float],
                               end: Tuple[float, float], move_dir: Tuple[float, float],
                               move_distance: float, collision_mask: int,
                               exclude_body: Optional[PhysicsBody] = None) -> Optional[Dict]:
        """
        Perform swept collision detection by stepping along the movement path.
        This handles large movement deltas and provides accurate collision detection.
        """
        import math

        # Calculate step size - smaller steps for more accuracy, but balance performance
        # Use shape size to determine appropriate step size
        if hasattr(temp_shape, 'radius'):
            # Circle shape
            shape_size = temp_shape.radius * 2
        else:
            # Rectangle shape - use smaller dimension
            bb = temp_shape.bb
            shape_size = min(bb.right - bb.left, bb.top - bb.bottom)

        # Step size should be a fraction of the shape size, but not too small
        step_size = max(shape_size * 0.25, 2.0)  # At least 2 pixels
        num_steps = max(int(move_distance / step_size), 1)
        actual_step_size = move_distance / num_steps

        # Step along the path
        for step in range(num_steps + 1):
            # Calculate current position
            t = step / num_steps if num_steps > 0 else 1.0
            current_pos = (
                start[0] + move_dir[0] * move_distance * t,
                start[1] + move_dir[1] * move_distance * t
            )

            # Move temp body to current position
            temp_body.position = current_pos

            # Check for collisions at this position
            collision_info = self._check_collision_at_position(
                temp_shape, current_pos, collision_mask, exclude_body
            )

            if collision_info:
                # Found collision, calculate accurate collision info
                collision_info['distance'] = t  # Distance along path (0.0 to 1.0)
                return collision_info

        return None

    def _check_collision_at_position(self, temp_shape, position: Tuple[float, float],
                                   collision_mask: int, exclude_body: Optional[PhysicsBody] = None) -> Optional[Dict]:
        """Check for collision at a specific position and return detailed collision info"""
        # Query for shapes at this position
        point_queries = self.space.point_query(position, 0, pymunk.ShapeFilter(mask=collision_mask))

        for query in point_queries:
            shape = query.shape

            # Skip if this is the temp shape itself
            if shape == temp_shape:
                continue

            # Skip if this is the excluded body
            if exclude_body and hasattr(shape, 'user_data') and shape.user_data == exclude_body:
                continue

            # Skip sensors unless we want to detect them
            if hasattr(shape, 'sensor') and shape.sensor:
                continue

            body = shape.user_data if hasattr(shape, 'user_data') and shape.user_data else None
            if body:
                # Calculate collision normal
                normal = self._calculate_collision_normal(temp_shape, shape, position)

                return {
                    'body': body,
                    'point': position,
                    'normal': normal,
                    'distance': 0.0  # Will be set by caller
                }

        # Also check for shape-to-shape collision using more precise method
        for shape in self.space.shapes:
            if shape == temp_shape:
                continue

            # Skip if this is the excluded body
            if exclude_body and hasattr(shape, 'user_data') and shape.user_data == exclude_body:
                continue

            # Skip sensors
            if hasattr(shape, 'sensor') and shape.sensor:
                continue

            # Check if shapes are colliding using pymunk's collision detection
            if self._shapes_colliding(temp_shape, shape):
                body = shape.user_data if hasattr(shape, 'user_data') and shape.user_data else None
                if body:
                    normal = self._calculate_collision_normal(temp_shape, shape, position)

                    return {
                        'body': body,
                        'point': position,
                        'normal': normal,
                        'distance': 0.0  # Will be set by caller
                    }

        return None

    def _shapes_colliding(self, shape1, shape2) -> bool:
        """Check if two shapes are colliding using pymunk collision detection"""
        try:
            # Use pymunk's collision detection
            contact_set = shape1.shapes_collide(shape2)
            return len(contact_set.points) > 0
        except:
            # Fallback to bounding box check
            bb1 = shape1.bb
            bb2 = shape2.bb
            return not (bb1.right < bb2.left or bb1.left > bb2.right or
                       bb1.top < bb2.bottom or bb1.bottom > bb2.top)

    def _calculate_collision_normal(self, temp_shape, colliding_shape, position: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate the collision normal between two shapes using pre-calculated edge normals"""
        import math

        try:
            # First try to use the collision shape's pre-calculated edge normals
            # Get the collision shape node from the colliding body
            colliding_body = self.get_body_by_pymunk_shape(colliding_shape)
            if colliding_body and hasattr(colliding_body, 'node'):
                colliding_node = colliding_body.node

                # Find the CollisionShape2D child
                collision_shape_node = None
                for child in colliding_node.children:
                    if hasattr(child, 'type') and child.type == "CollisionShape2D":
                        collision_shape_node = child
                        break

                if collision_shape_node and hasattr(collision_shape_node, 'get_best_collision_normal'):
                    # Use the collision shape's improved normal calculation
                    temp_center = [temp_shape.body.position.x, temp_shape.body.position.y]
                    collision_point = [position[0], position[1]]

                    normal = collision_shape_node.get_best_collision_normal(collision_point, temp_center)
                    print(f"[PHYSICS] Using collision shape edge normal: {normal}")
                    return (normal[0], normal[1])
        except Exception as e:
            print(f"[PHYSICS] Error using collision shape normals: {e}")

        try:
            # Try to get contact points and normal from pymunk
            contact_set = temp_shape.shapes_collide(colliding_shape)
            if contact_set.points:
                # Use the normal from the first contact point
                normal = contact_set.normal
                # The normal from pymunk should point from colliding_shape towards temp_shape
                # which is the direction to push temp_shape to resolve the collision
                print(f"[PHYSICS] Using pymunk contact normal: {(normal.x, normal.y)}")
                return (normal.x, normal.y)
        except Exception as e:
            print(f"[PHYSICS] Error getting collision normal: {e}")

        # Fallback: Use edge-based calculation first for better accuracy
        try:
            edge_normal = self._calculate_edge_based_normal(temp_shape, colliding_shape)
            if edge_normal:
                print(f"[PHYSICS] Using edge-based normal: {edge_normal}")
                return edge_normal
        except Exception as e:
            print(f"[PHYSICS] Error calculating edge-based normal: {e}")

        # Final fallback: calculate normal based on shape centers
        try:
            temp_center = temp_shape.body.position
            colliding_center = colliding_shape.body.position

            # Vector from colliding shape to temp shape
            dx = temp_center.x - colliding_center.x
            dy = temp_center.y - colliding_center.y

            # Normalize
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0.001:
                normal = (dx / length, dy / length)
                print(f"[PHYSICS] Using center-based normal: {normal}")
                return normal
            else:
                # If centers are at same position, default to pushing upward
                print(f"[PHYSICS] Using default upward normal: (0.0, 1.0)")
                return (0.0, 1.0)
        except Exception as e:
            print(f"[PHYSICS] Error calculating fallback normal: {e}")
            return (0.0, 1.0)

    def shape_cast_all(self, shape_type: str, size: Tuple[float, float],
                      start: Tuple[float, float], end: Tuple[float, float],
                      collision_mask: int = 0xFFFFFFFF, exclude_body: Optional[PhysicsBody] = None) -> List[Dict]:
        """
        Cast a shape and return all hits along the path, sorted by distance.

        Returns:
            List of collision dicts sorted by distance along path
        """
        import math

        # Calculate movement vector
        move_vector = (end[0] - start[0], end[1] - start[1])
        move_distance = math.sqrt(move_vector[0]**2 + move_vector[1]**2)

        # Handle zero movement
        if move_distance < 0.001:
            overlap = self._check_shape_overlap(shape_type, size, start, collision_mask, exclude_body)
            return [overlap] if overlap else []

        # Normalize movement vector
        move_dir = (move_vector[0] / move_distance, move_vector[1] / move_distance)

        # Create temporary body and shape for casting
        temp_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        temp_body.position = start

        if shape_type == "circle":
            radius = size[0] / 2.0
            temp_shape = pymunk.Circle(temp_body, radius)
        else:  # rectangle
            temp_shape = pymunk.Poly.create_box(temp_body, size)

        temp_shape.filter = pymunk.ShapeFilter(mask=collision_mask)
        temp_shape.sensor = True

        # Add to space temporarily
        self.space.add(temp_body, temp_shape)

        try:
            # Collect all collisions along the path
            collisions = self._collect_all_collisions_along_path(
                temp_body, temp_shape, start, end, move_dir, move_distance,
                collision_mask, exclude_body
            )

            # Sort by distance
            collisions.sort(key=lambda x: x['distance'])
            return collisions

        finally:
            self.space.remove(temp_body, temp_shape)

    def _collect_all_collisions_along_path(self, temp_body, temp_shape, start: Tuple[float, float],
                                         end: Tuple[float, float], move_dir: Tuple[float, float],
                                         move_distance: float, collision_mask: int,
                                         exclude_body: Optional[PhysicsBody] = None) -> List[Dict]:
        """Collect all collisions along the movement path"""
        collisions = []
        bodies_hit = set()  # Track bodies we've already hit to avoid duplicates

        # Calculate step size
        if hasattr(temp_shape, 'radius'):
            shape_size = temp_shape.radius * 2
        else:
            bb = temp_shape.bb
            shape_size = min(bb.right - bb.left, bb.top - bb.bottom)

        step_size = max(shape_size * 0.25, 2.0)
        num_steps = max(int(move_distance / step_size), 1)

        # Step along the path
        for step in range(num_steps + 1):
            t = step / num_steps if num_steps > 0 else 1.0
            current_pos = (
                start[0] + move_dir[0] * move_distance * t,
                start[1] + move_dir[1] * move_distance * t
            )

            temp_body.position = current_pos

            # Check for collisions at this position
            collision_info = self._check_collision_at_position(
                temp_shape, current_pos, collision_mask, exclude_body
            )

            if collision_info and collision_info['body'] not in bodies_hit:
                collision_info['distance'] = t
                collisions.append(collision_info)
                bodies_hit.add(collision_info['body'])

        return collisions

    def test_move(self, body: PhysicsBody, move_delta: Tuple[float, float]) -> Optional[Dict]:
        """
        Test if a body can move by the given delta without collision.
        Returns collision info if collision would occur, None if movement is safe.
        """
        if not body or not body.pymunk_body:
            return None

        # Get current position
        current_pos = body.pymunk_body.position
        target_pos = (current_pos[0] + move_delta[0], current_pos[1] + move_delta[1])

        # Determine shape type and size
        shape_type = "rectangle"
        shape_size = (32.0, 32.0)

        if body.pymunk_shapes:
            shape = body.pymunk_shapes[0]
            if hasattr(shape, 'radius'):
                shape_type = "circle"
                shape_size = (shape.radius * 2, shape.radius * 2)  # Diameter for both dimensions
            elif hasattr(shape, 'get_vertices'):
                vertices = shape.get_vertices()
                if vertices:
                    min_x = min(v.x for v in vertices)
                    max_x = max(v.x for v in vertices)
                    min_y = min(v.y for v in vertices)
                    max_y = max(v.y for v in vertices)
                    shape_size = (max_x - min_x, max_y - min_y)

        # Use shape cast to test movement
        return self.shape_cast(
            shape_type,
            shape_size,
            (current_pos[0], current_pos[1]),
            target_pos,
            collision_mask=body.collision_mask,
            exclude_body=body
        )

    def get_overlapping_bodies(self, body: PhysicsBody) -> List[PhysicsBody]:
        """Get all bodies currently overlapping with the given body"""
        if not body or not body.pymunk_body:
            return []

        overlapping = []
        current_pos = body.pymunk_body.position

        # Determine shape type and size
        shape_type = "rectangle"
        shape_size = (32.0, 32.0)

        if body.pymunk_shapes:
            shape = body.pymunk_shapes[0]
            if hasattr(shape, 'radius'):
                shape_type = "circle"
                shape_size = (shape.radius * 2, shape.radius * 2)  # Diameter for both dimensions
            elif hasattr(shape, 'get_vertices'):
                vertices = shape.get_vertices()
                if vertices:
                    min_x = min(v.x for v in vertices)
                    max_x = max(v.x for v in vertices)
                    min_y = min(v.y for v in vertices)
                    max_y = max(v.y for v in vertices)
                    shape_size = (max_x - min_x, max_y - min_y)

        # Check for overlaps at current position
        overlap_info = self._check_shape_overlap(
            shape_type, shape_size, (current_pos[0], current_pos[1]),
            body.collision_mask, exclude_body=body
        )

        if overlap_info and overlap_info['body']:
            overlapping.append(overlap_info['body'])

        return overlapping
