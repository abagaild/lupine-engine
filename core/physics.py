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
from .scene import Node2D, CollisionShape2D, CollisionPolygon2D, Area2D, RigidBody2D, StaticBody2D, KinematicBody2D


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
                self.pymunk_body.position = pos[0], pos[1]
        
        # Set user data for collision callbacks
        self.pymunk_body.user_data = self
    
    def add_collision_shape(self, shape_node: Node2D):
        """Add a collision shape to this body"""
        if isinstance(shape_node, CollisionShape2D):
            self._add_collision_shape_2d(shape_node)
        elif isinstance(shape_node, CollisionPolygon2D):
            self._add_collision_polygon_2d(shape_node)
    
    def _add_collision_shape_2d(self, shape_node: CollisionShape2D):
        """Add CollisionShape2D to body"""
        shape_type = getattr(shape_node, 'shape', 'rectangle')
        
        if shape_type == 'rectangle':
            size = getattr(shape_node, 'size', [32, 32])
            if isinstance(size, list) and len(size) >= 2:
                width, height = size[0], size[1]
                shape = pymunk.Poly.create_box(self.pymunk_body, (width, height))
        
        elif shape_type == 'circle':
            radius = getattr(shape_node, 'radius', 16.0)
            shape = pymunk.Circle(self.pymunk_body, radius)
        
        elif shape_type == 'capsule':
            radius = getattr(shape_node, 'capsule_radius', 16.0)
            height = getattr(shape_node, 'height', 32.0)
            # Create capsule as circle with segments
            a = (0, -height/2 + radius)
            b = (0, height/2 - radius)
            shape = pymunk.Segment(self.pymunk_body, a, b, radius)
        
        elif shape_type == 'segment':
            point_a = getattr(shape_node, 'point_a', [0, 0])
            point_b = getattr(shape_node, 'point_b', [32, 0])
            if isinstance(point_a, list) and isinstance(point_b, list):
                shape = pymunk.Segment(self.pymunk_body, point_a, point_b, 1.0)
        
        else:
            # Default to box
            shape = pymunk.Poly.create_box(self.pymunk_body, (32, 32))
        
        # Set shape properties
        shape.friction = self.friction
        shape.elasticity = self.elasticity
        shape.collision_type = self.collision_layer
        shape.filter = pymunk.ShapeFilter(categories=self.collision_layer, mask=self.collision_mask)
        shape.user_data = self
        
        self.pymunk_shapes.append(shape)
    
    def _add_collision_polygon_2d(self, polygon_node: CollisionPolygon2D):
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
        if isinstance(self.node, RigidBody2D):
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
        self.areas: Dict[str, 'AreaHandler'] = {}
        
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
                # Get contact information
                contact_point_set = arbiter.contact_point_set
                if contact_point_set.count > 0:
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
        
        # Set default collision handler
        self.space.add_default_collision_handler().begin = collision_handler
    
    def _notify_collision(self, body: PhysicsBody, other_body: PhysicsBody, contact: PhysicsContact):
        """Notify a body of collision"""
        for callback in body.collision_callbacks:
            try:
                callback(other_body, contact)
            except Exception as e:
                print(f"Error in collision callback: {e}")
    
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
    
    def _add_rigid_body(self, node: RigidBody2D) -> PhysicsBody:
        """Add RigidBody2D to physics world"""
        body = PhysicsBody(node, PhysicsBodyType.DYNAMIC)
        
        # Set physics properties
        body.mass = getattr(node, 'mass', 1.0)
        body.collision_layer = getattr(node, 'collision_layer', 1)
        body.collision_mask = getattr(node, 'collision_mask', 1)
        
        # Add collision shapes from children
        for child in node.children:
            if isinstance(child, (CollisionShape2D, CollisionPolygon2D)):
                body.add_collision_shape(child)
        
        # Add to space
        self.space.add(body.pymunk_body)
        for shape in body.pymunk_shapes:
            self.space.add(shape)
        
        self.bodies[node.name] = body
        return body
    
    def _add_static_body(self, node: StaticBody2D) -> PhysicsBody:
        """Add StaticBody2D to physics world"""
        body = PhysicsBody(node, PhysicsBodyType.STATIC)
        
        body.collision_layer = getattr(node, 'collision_layer', 1)
        body.collision_mask = getattr(node, 'collision_mask', 1)
        
        # Add collision shapes from children
        for child in node.children:
            if isinstance(child, (CollisionShape2D, CollisionPolygon2D)):
                body.add_collision_shape(child)
        
        # Add to space
        self.space.add(body.pymunk_body)
        for shape in body.pymunk_shapes:
            self.space.add(shape)
        
        self.bodies[node.name] = body
        return body
    
    def _add_kinematic_body(self, node: KinematicBody2D) -> PhysicsBody:
        """Add KinematicBody2D to physics world"""
        body = PhysicsBody(node, PhysicsBodyType.KINEMATIC)
        
        body.collision_layer = getattr(node, 'collision_layer', 1)
        body.collision_mask = getattr(node, 'collision_mask', 1)
        
        # Add collision shapes from children
        for child in node.children:
            if isinstance(child, (CollisionShape2D, CollisionPolygon2D)):
                body.add_collision_shape(child)
        
        # Add to space
        self.space.add(body.pymunk_body)
        for shape in body.pymunk_shapes:
            self.space.add(shape)
        
        self.bodies[node.name] = body
        return body
    
    def _add_area(self, node: Area2D):
        """Add Area2D to physics world (sensor)"""
        # Areas are handled differently as sensors
        # Implementation would go here
        pass
    
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
        
        # Update nodes from physics
        for body in self.bodies.values():
            body.update_node_from_physics()
    
    def set_gravity(self, gravity: Tuple[float, float]):
        """Set world gravity"""
        self.space.gravity = gravity
    
    def get_body(self, node_name: str) -> Optional[PhysicsBody]:
        """Get physics body by node name"""
        return self.bodies.get(node_name)
    
    def query_point(self, point: Tuple[float, float]) -> List[PhysicsBody]:
        """Query bodies at a point"""
        results = []
        point_query = self.space.point_query_nearest(point, 0, pymunk.ShapeFilter())
        if point_query:
            body = point_query.shape.user_data
            if body:
                results.append(body)
        return results
    
    def raycast(self, start: Tuple[float, float], end: Tuple[float, float]) -> Optional[Dict]:
        """Perform raycast and return hit information"""
        hit = self.space.segment_query_first(start, end, 0, pymunk.ShapeFilter())
        if hit:
            body = hit.shape.user_data if hit.shape.user_data else None
            return {
                'body': body,
                'point': (hit.point.x, hit.point.y),
                'normal': (hit.normal.x, hit.normal.y),
                'distance': hit.alpha
            }
        return None
