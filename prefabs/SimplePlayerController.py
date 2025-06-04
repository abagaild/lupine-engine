"""
Simple Player Controller for Lupine Engine
A basic kinematic body that moves with WASD keys

This prefab demonstrates:
- _ready method execution
- _process method execution  
- _physics_process method execution
- Input handling using key constants
- Basic movement with KinematicBody2D
"""

# Export variables - these will appear in the inspector
# Note: In the actual implementation, these would be parsed by the Python runtime
# For now, we'll define them as regular variables and add them to export_variables in _ready
speed = 200.0  # Movement speed in pixels per second
use_physics_process = True  # Whether to use _physics_process for movement

def _ready():
    """Called when the node enters the scene tree"""
    print(f"[SimplePlayerController] Ready! Node: {self.name}")
    print(f"[SimplePlayerController] Speed: {speed}")
    print(f"[SimplePlayerController] Use physics process: {use_physics_process}")
    
    # Initialize velocity for physics movement
    self.velocity = [0.0, 0.0]

def _process(delta):
    """Called every frame - used for non-physics updates"""
    if not use_physics_process:
        # Handle movement in _process if not using physics process
        _handle_movement(delta)

def _physics_process(delta):
    """Called for physics updates - preferred for movement"""
    if use_physics_process:
        # Handle movement in _physics_process for better physics integration
        _handle_movement(delta)

def _handle_movement(delta):
    """Handle player movement based on input"""
    # Reset velocity
    velocity_x = 0.0
    velocity_y = 0.0
    
    # Check WASD input using the exposed key constants and global is_key_pressed function
    try:
        if is_key_pressed(KEY_A):
            velocity_x -= speed
        if is_key_pressed(KEY_D):
            velocity_x += speed
        if is_key_pressed(KEY_W):
            velocity_y -= speed
        if is_key_pressed(KEY_S):
            velocity_y += speed
    except Exception as e:
        print(f"[SimplePlayerController] Input error: {e}")
        return
    
    # Apply movement if there's any input
    if velocity_x != 0.0 or velocity_y != 0.0:
        # Store velocity for potential use by physics system
        self.velocity = [velocity_x, velocity_y]
        
        # Calculate movement for this frame
        movement_x = velocity_x * delta
        movement_y = velocity_y * delta
        
        # Get current position
        current_pos = self.position.copy()
        
        # Apply movement
        new_x = current_pos[0] + movement_x
        new_y = current_pos[1] + movement_y
        
        # Update position
        self.set_position(new_x, new_y)

        # Note: Children (sprites, collision shapes) will automatically move with the parent
        # due to the improved sprite synchronization system in the engine
        
        # Debug output (can be removed for production)
        if abs(velocity_x) > 0 or abs(velocity_y) > 0:
            print(f"[SimplePlayerController] Moving to ({new_x:.1f}, {new_y:.1f}) - Velocity: ({velocity_x:.1f}, {velocity_y:.1f})")

# Note: The _move_children_relative function has been removed because
# the engine now automatically handles child positioning through the
# improved sprite synchronization system

def get_velocity():
    """Get the current velocity vector"""
    return getattr(self, 'velocity', [0.0, 0.0])

def set_velocity(new_velocity):
    """Set the velocity vector"""
    self.velocity = new_velocity.copy() if isinstance(new_velocity, list) else [new_velocity[0], new_velocity[1]]
