"""
Advanced Player Controller for Lupine Engine
Comprehensive player controller with multiple movement modes:
- 4-directional movement (grid-based or smooth)
- 8-directional movement (diagonal support)
- Platformer movement (gravity, jumping, wall jumping)
- Sidescroller movement (horizontal focus with gravity)

Features:
- Multiple movement modes
- Gravity and jumping mechanics
- Wall detection and wall jumping
- Ground detection
- Coyote time and jump buffering
- Variable jump height
- Collision handling with move_and_slide
- Animation state management
- Input buffering and responsiveness
"""

import math

# Export variables - Movement Configuration
!movement_mode = "platformer"  # @type:enum "Movement mode" ["4_directional", "8_directional", "platformer", "sidescroller"]
!speed = 300.0  # @type:float "Base movement speed in pixels per second"
!acceleration = 1500.0  # @type:float "Acceleration rate"
!friction = 1200.0  # @type:float "Friction/deceleration rate"

# Export variables - Platformer/Sidescroller Settings
!gravity = 980.0  # @type:float "Gravity strength (pixels/second²)"
!jump_velocity = -400.0  # @type:float "Initial jump velocity (negative = up)"
!max_fall_speed = 600.0  # @type:float "Maximum falling speed"
!wall_jump_velocity = 300.0  # @type:float "Horizontal velocity for wall jumps"
!wall_slide_speed = 100.0  # @type:float "Speed when sliding down walls"

# Export variables - Advanced Features
!coyote_time = 0.1  # @type:float "Time after leaving ground where jump is still allowed"
!jump_buffer_time = 0.1  # @type:float "Time to buffer jump input before landing"
!variable_jump_height = True  # @type:bool "Allow variable jump height by holding jump"
!wall_jumping_enabled = True  # @type:bool "Enable wall jumping mechanics"
!air_control = 0.8  # @type:float "Air movement control factor (0-1)"

# Export variables - Input Settings
!jump_key = "KEY_SPACE"  # @type:str "Key for jumping"
!left_key = "KEY_A"  # @type:str "Key for moving left"
!right_key = "KEY_D"  # @type:str "Key for moving right"
!up_key = "KEY_W"  # @type:str "Key for moving up"
!down_key = "KEY_S"  # @type:str "Key for moving down"

# Export variables - Debug
!debug_mode = False  # @type:bool "Show debug information"


def _ready():
    """Initialize the player controller"""
    print(f"[AdvancedPlayerController] Ready! Node: {self.name}")
    print(f"[AdvancedPlayerController] Movement mode: {movement_mode}")
    
    # Initialize movement state
    self.velocity = [0.0, 0.0]
    self.facing_direction = 1  # 1 = right, -1 = left
    
    # Platformer state
    self.is_on_ground = False
    self.is_on_wall_left = False
    self.is_on_wall_right = False
    self.was_on_ground = False
    self.coyote_timer = 0.0
    self.jump_buffer_timer = 0.0
    self.is_jumping = False
    self.jump_held = False
    
    # Get child nodes
    self.sprite = self.get_node("Sprite")
    self.interaction_area = self.get_node("InteractionArea")

    # Connect interaction area signals
    if self.interaction_area:
        self.interaction_area.connect("body_entered", self._on_interaction_entered)
        self.interaction_area.connect("body_exited", self._on_interaction_exited)
        self.interaction_area.connect("area_entered", self._on_area_entered)
        self.interaction_area.connect("area_exited", self._on_area_exited)

    # Initialize interaction tracking
    self.nearby_interactables = []
    self.nearby_areas = []


def _physics_process(delta):
    """Handle physics-based movement"""
    # Update collision detection using physics queries
    self.is_on_ground = self._check_ground_collision()
    self.is_on_wall_left = self._check_wall_collision(-1)  # Left direction
    self.is_on_wall_right = self._check_wall_collision(1)  # Right direction

    # Update timers
    self._update_timers(delta)

    # Handle input
    input_vector = self._get_input_vector()

    # Apply movement based on mode
    if movement_mode == "4_directional":
        self._handle_4_directional_movement(input_vector, delta)
    elif movement_mode == "8_directional":
        self._handle_8_directional_movement(input_vector, delta)
    elif movement_mode == "platformer":
        self._handle_platformer_movement(input_vector, delta)
    elif movement_mode == "sidescroller":
        self._handle_sidescroller_movement(input_vector, delta)

    # Apply movement with collision
    self.velocity = self.move_and_slide(self.velocity)

    # Update sprite direction
    self._update_sprite_direction()

    # Debug output
    if debug_mode:
        self._debug_output()


def _get_input_vector():
    """Get normalized input vector from keyboard"""
    input_x = 0.0
    input_y = 0.0

    try:
        # Horizontal input
        if is_key_pressed(globals().get(left_key, KEY_A)):
            input_x -= 1.0
        if is_key_pressed(globals().get(right_key, KEY_D)):
            input_x += 1.0

        # Vertical input (for top-down modes)
        if is_key_pressed(globals().get(up_key, KEY_W)):
            input_y -= 1.0
        if is_key_pressed(globals().get(down_key, KEY_S)):
            input_y += 1.0

        # Jump input
        jump_pressed = is_key_pressed(globals().get(jump_key, KEY_SPACE))
        if jump_pressed and not self.jump_held:
            self.jump_buffer_timer = jump_buffer_time
        self.jump_held = jump_pressed

    except Exception as e:
        print(f"[AdvancedPlayerController] Input error: {e}")

    return [input_x, input_y]


def _handle_4_directional_movement(input_vector, delta):
    """Handle 4-directional movement (no diagonals)"""
    # Prioritize horizontal movement, then vertical
    if abs(input_vector[0]) > 0:
        input_vector[1] = 0  # Cancel vertical if horizontal input
    
    # Apply movement
    target_velocity = [input_vector[0] * speed, input_vector[1] * speed]
    
    # Smooth acceleration/deceleration
    self.velocity[0] = self._move_toward(self.velocity[0], target_velocity[0], acceleration * delta)
    self.velocity[1] = self._move_toward(self.velocity[1], target_velocity[1], acceleration * delta)


def _handle_8_directional_movement(input_vector, delta):
    """Handle 8-directional movement with diagonal support"""
    # Normalize diagonal movement to prevent faster diagonal speed
    if input_vector[0] != 0 and input_vector[1] != 0:
        length = math.sqrt(input_vector[0]**2 + input_vector[1]**2)
        input_vector[0] /= length
        input_vector[1] /= length
    
    # Apply movement
    target_velocity = [input_vector[0] * speed, input_vector[1] * speed]
    
    # Smooth acceleration/deceleration
    self.velocity[0] = self._move_toward(self.velocity[0], target_velocity[0], acceleration * delta)
    self.velocity[1] = self._move_toward(self.velocity[1], target_velocity[1], acceleration * delta)


def _handle_platformer_movement(input_vector, delta):
    """Handle platformer movement with gravity and jumping"""
    # Horizontal movement
    if input_vector[0] != 0:
        # Apply air control factor when not on ground
        control_factor = 1.0 if self.is_on_ground else air_control
        target_velocity_x = input_vector[0] * speed * control_factor
        self.velocity[0] = self._move_toward(self.velocity[0], target_velocity_x, acceleration * delta)
        self.facing_direction = 1 if input_vector[0] > 0 else -1
    else:
        # Apply friction
        friction_force = friction if self.is_on_ground else friction * 0.5
        self.velocity[0] = self._move_toward(self.velocity[0], 0, friction_force * delta)
    
    # Vertical movement (gravity and jumping)
    self._handle_gravity_and_jumping(delta)


def _handle_sidescroller_movement(input_vector, delta):
    """Handle sidescroller movement (horizontal focus with gravity)"""
    # Similar to platformer but with different physics tuning
    # Horizontal movement with more responsive controls
    if input_vector[0] != 0:
        target_velocity_x = input_vector[0] * speed
        accel_rate = acceleration * 1.5  # Faster acceleration for sidescroller
        self.velocity[0] = self._move_toward(self.velocity[0], target_velocity_x, accel_rate * delta)
        self.facing_direction = 1 if input_vector[0] > 0 else -1
    else:
        # Higher friction for snappier movement
        self.velocity[0] = self._move_toward(self.velocity[0], 0, friction * 1.5 * delta)
    
    # Vertical movement
    self._handle_gravity_and_jumping(delta)


def _handle_gravity_and_jumping(delta):
    """Handle gravity, jumping, and wall interactions"""
    # Apply gravity
    if not self.is_on_ground:
        self.velocity[1] += gravity * delta
        
        # Limit fall speed
        if self.velocity[1] > max_fall_speed:
            self.velocity[1] = max_fall_speed
        
        # Wall sliding
        if wall_jumping_enabled and (self.is_on_wall_left or self.is_on_wall_right):
            if self.velocity[1] > wall_slide_speed:
                self.velocity[1] = wall_slide_speed
    
    # Handle jumping
    can_jump = (self.is_on_ground or self.coyote_timer > 0 or 
                (wall_jumping_enabled and (self.is_on_wall_left or self.is_on_wall_right)))
    
    if self.jump_buffer_timer > 0 and can_jump:
        self._perform_jump()
    
    # Variable jump height
    if variable_jump_height and self.is_jumping and not self.jump_held and self.velocity[1] < 0:
        self.velocity[1] *= 0.5  # Cut jump short if button released


def _perform_jump():
    """Perform jump action"""
    if wall_jumping_enabled and not self.is_on_ground and (self.is_on_wall_left or self.is_on_wall_right):
        # Wall jump
        self.velocity[1] = jump_velocity
        if self.is_on_wall_left:
            self.velocity[0] = wall_jump_velocity  # Jump away from left wall
        elif self.is_on_wall_right:
            self.velocity[0] = -wall_jump_velocity  # Jump away from right wall
    else:
        # Normal jump
        self.velocity[1] = jump_velocity
    
    self.is_jumping = True
    self.jump_buffer_timer = 0
    self.coyote_timer = 0
    
    # Emit jump signal if needed
    # self.emit_signal("jumped")


def _update_timers(delta):
    """Update various timers"""
    # Coyote time - grace period after leaving ground
    if self.is_on_ground:
        self.coyote_timer = coyote_time
    else:
        self.coyote_timer = max(0, self.coyote_timer - delta)

    # Jump buffer - remember jump input briefly
    if self.jump_buffer_timer > 0:
        self.jump_buffer_timer = max(0, self.jump_buffer_timer - delta)

    # Reset jumping flag when landing
    if self.is_on_ground and self.velocity[1] >= 0:
        self.is_jumping = False


def _move_toward(current, target, max_delta):
    """Move current value toward target by max_delta"""
    if abs(target - current) <= max_delta:
        return target
    return current + max_delta if target > current else current - max_delta


def _update_sprite_direction():
    """Update sprite direction based on movement"""
    if self.sprite and self.facing_direction != 0:
        # Flip sprite based on facing direction
        if hasattr(self.sprite, 'flip_h'):
            self.sprite.flip_h = self.facing_direction < 0


def _debug_output():
    """Output debug information"""
    print(f"Velocity: [{self.velocity[0]:.1f}, {self.velocity[1]:.1f}]")
    print(f"Ground: {self.is_on_ground}, Wall L: {self.is_on_wall_left}, Wall R: {self.is_on_wall_right}")
    print(f"Coyote: {self.coyote_timer:.2f}, Jump Buffer: {self.jump_buffer_timer:.2f}")


# Interaction Detection Callbacks
def _on_interaction_entered(body):
    """Called when interaction area detects a body"""
    if body != self and hasattr(body, 'type'):
        if hasattr(body, 'interactable') and body.interactable:
            self.nearby_interactables.append(body)
            print(f"[AdvancedPlayerController] Interactable entered: {body.name}")


def _on_interaction_exited(body):
    """Called when interaction area loses a body"""
    if body in self.nearby_interactables:
        self.nearby_interactables.remove(body)
        print(f"[AdvancedPlayerController] Interactable exited: {body.name}")


def _on_area_entered(area):
    """Called when interaction area detects another area"""
    if area != self.interaction_area:
        self.nearby_areas.append(area)
        print(f"[AdvancedPlayerController] Area entered: {area.name}")


def _on_area_exited(area):
    """Called when interaction area loses another area"""
    if area in self.nearby_areas:
        self.nearby_areas.remove(area)
        print(f"[AdvancedPlayerController] Area exited: {area.name}")


# Ground and Wall Detection using Physics Queries
def _check_ground_collision():
    """Check if player is on ground using physics raycast"""
    # Cast a ray downward from the bottom of the player
    start_pos = [self.position[0], self.position[1] + 24]  # Bottom of player
    end_pos = [self.position[0], self.position[1] + 28]    # Slightly below

    # Get physics world from scene
    physics_world = self._get_physics_world()
    if physics_world:
        hit = physics_world.raycast(start_pos, end_pos, exclude_sensors=True)
        return hit is not None
    return False


def _check_wall_collision(direction):
    """Check if player is against a wall using physics raycast"""
    # Cast a ray horizontally from the side of the player
    offset_x = 18 * direction  # Half width of player + small margin
    start_pos = [self.position[0] + offset_x, self.position[1]]
    end_pos = [self.position[0] + offset_x + (4 * direction), self.position[1]]

    # Get physics world from scene
    physics_world = self._get_physics_world()
    if physics_world:
        hit = physics_world.raycast(start_pos, end_pos, exclude_sensors=True)
        return hit is not None
    return False


def _get_physics_world():
    """Get the physics world from the scene"""
    try:
        scene = self.get_scene()
        if scene and hasattr(scene, 'physics_world'):
            return scene.physics_world
    except:
        pass
    return None


# Public API Methods
def get_movement_mode():
    """Get current movement mode"""
    return movement_mode


def set_movement_mode(new_mode):
    """Set movement mode"""
    global movement_mode
    if new_mode in ["4_directional", "8_directional", "platformer", "sidescroller"]:
        movement_mode = new_mode
        print(f"[AdvancedPlayerController] Movement mode changed to: {movement_mode}")
    else:
        print(f"[AdvancedPlayerController] Invalid movement mode: {new_mode}")


def get_velocity():
    """Get current velocity vector"""
    return self.velocity.copy()


def set_velocity(new_velocity):
    """Set velocity vector"""
    self.velocity = new_velocity.copy() if isinstance(new_velocity, list) else [new_velocity[0], new_velocity[1]]


def is_grounded():
    """Check if player is on ground"""
    return self.is_on_ground


def is_against_wall():
    """Check if player is against any wall"""
    return self.is_on_wall_left or self.is_on_wall_right


def jump():
    """Force a jump (useful for external triggers)"""
    if self.is_on_ground or self.coyote_timer > 0:
        _perform_jump()


def stop():
    """Stop all movement"""
    self.velocity = [0.0, 0.0]


def teleport(new_position):
    """Teleport to new position"""
    self.set_position(new_position[0], new_position[1])
    self.velocity = [0.0, 0.0]
