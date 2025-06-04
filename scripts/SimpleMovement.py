"""
Simple Movement Script for Lupine Engine
Attach this to any sprite to make it move with WASD keys

Usage:
1. Attach this script to a Sprite node
2. Set the movement speed in the inspector
3. Run the game and use WASD to move
"""

# Export variables - these will appear in the inspector
!speed = 200.0  # Movement speed in pixels per second

def _on_ready():
    """Called when the node enters the scene tree"""
    print(f"SimpleMovement script ready on {self.name}")

def _process(delta):
    """Called every frame"""
    # Get current position
    current_pos = self.position.copy()

    # Calculate movement based on input
    movement_x = 0
    movement_y = 0

    # Check WASD input using pygame key constants
    try:
        # Fallback: try to access global input state
        # This will work if the game engine exposes input globally
        import pygame
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            movement_x -= speed * delta
        if keys[pygame.K_d]:
            movement_x += speed * delta
        if keys[pygame.K_w]:
            movement_y -= speed * delta
        if keys[pygame.K_s]:
            movement_y += speed * delta

    except Exception as e:
        # If input system fails, print error but don't crash
        print(f"Input error in SimpleMovement: {e}")

    # Apply movement
    if movement_x != 0 or movement_y != 0:
        new_x = current_pos[0] + movement_x
        new_y = current_pos[1] + movement_y

        # Update position
        self.set_position(new_x, new_y)

        # Move children with the parent
        self._move_children(movement_x, movement_y)

def _move_children(self, delta_x, delta_y):
    """Move all children along with the parent"""
    for child in self.children:
        if hasattr(child, 'position'):
            child_pos = child.position.copy()
            child.set_position(child_pos[0] + delta_x, child_pos[1] + delta_y)
