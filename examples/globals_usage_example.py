"""
Example of how to use the Global Manager systems in Lupine Engine
This shows how to access singletons and global variables from game scripts
"""

# Example 1: Using Singletons
def example_singleton_usage():
    """Example of how to use singletons in your game scripts"""
    
    # Import the singleton manager
    from core.globals.singleton_manager import get_singleton
    
    # Get a singleton instance by name
    game_manager = get_singleton("GameManager")
    
    if game_manager:
        # Use the singleton
        game_manager.set_player_name("Alice")
        game_manager.start_game()
        game_manager.add_score(150)
        
        # Get game state
        state = game_manager.get_game_state()
        print(f"Current game state: {state}")
    else:
        print("GameManager singleton not found!")


# Example 2: Using Global Variables
def example_global_variables_usage():
    """Example of how to use global variables in your game scripts"""
    
    # Import the variables manager functions
    from core.globals.variables_manager import get_global_var, set_global_var
    
    # Get global variable values
    max_health = get_global_var("max_health")
    player_speed = get_global_var("player_speed")
    game_title = get_global_var("game_title")
    debug_mode = get_global_var("debug_mode")
    
    print(f"Max Health: {max_health}")
    print(f"Player Speed: {player_speed}")
    print(f"Game Title: {game_title}")
    print(f"Debug Mode: {debug_mode}")
    
    # Set global variable values
    set_global_var("current_level", 5)
    set_global_var("player_name", "Bob")
    
    # Use in game logic
    if debug_mode:
        print("Debug mode is enabled!")
        set_global_var("player_speed", player_speed * 2)  # Double speed in debug


# Example 3: Using in a Node Script
class PlayerController:
    """Example player controller that uses global systems"""
    
    def __init__(self):
        self.health = 100
        self.position = [0, 0]
        
        # Get references to global systems
        from core.globals.singleton_manager import get_singleton
        from core.globals.variables_manager import get_global_var
        
        self.game_manager = get_singleton("GameManager")
        self.max_health = get_global_var("max_health") or 100
        self.speed = get_global_var("player_speed") or 5.0
    
    def _ready(self):
        """Called when node is ready"""
        print(f"Player ready with max health: {self.max_health}")
        print(f"Player speed: {self.speed}")
        
        if self.game_manager:
            print(f"Connected to game manager: {self.game_manager}")
    
    def take_damage(self, damage):
        """Take damage and update game manager"""
        self.health -= damage
        print(f"Player took {damage} damage. Health: {self.health}")
        
        if self.health <= 0:
            self.die()
    
    def die(self):
        """Handle player death"""
        print("Player died!")
        
        if self.game_manager:
            # Reset game through singleton
            self.game_manager.start_game()
            self.health = self.max_health
    
    def collect_item(self, points):
        """Collect an item and add score"""
        if self.game_manager:
            self.game_manager.add_score(points)
            print(f"Collected item worth {points} points!")


# Example 4: Setting up globals at game start
def initialize_game_globals():
    """Example of how to set up global variables at game start"""
    
    from core.globals.variables_manager import set_global_var
    from core.globals.singleton_manager import get_singleton
    
    # Set up initial global variables
    set_global_var("current_level", 1)
    set_global_var("lives_remaining", 3)
    set_global_var("high_score", 0)
    
    # Initialize singletons
    game_manager = get_singleton("GameManager")
    if game_manager:
        game_manager.start_game()
        print("Game initialized with global systems!")


if __name__ == "__main__":
    # Run examples
    print("=== Singleton Usage Example ===")
    example_singleton_usage()
    
    print("\n=== Global Variables Example ===")
    example_global_variables_usage()
    
    print("\n=== Game Initialization Example ===")
    initialize_game_globals()
