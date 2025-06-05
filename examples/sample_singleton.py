"""
Sample Singleton Script for Lupine Engine
This demonstrates how to create a singleton that can be accessed globally
"""

class GameManager:
    """Example singleton class for managing game state"""
    
    def __init__(self):
        self.score = 0
        self.level = 1
        self.player_name = "Player"
        self.game_started = False
        print("GameManager singleton initialized!")
    
    def _singleton_init(self):
        """Called when singleton is initialized by the engine"""
        print("GameManager singleton ready!")
        self.load_game_settings()
    
    def _singleton_cleanup(self):
        """Called when singleton is being destroyed"""
        print("GameManager singleton cleanup")
        self.save_game_settings()
    
    def start_game(self):
        """Start a new game"""
        self.game_started = True
        self.score = 0
        self.level = 1
        print(f"Game started for {self.player_name}")
    
    def add_score(self, points):
        """Add points to the score"""
        self.score += points
        print(f"Score: {self.score}")
        
        # Level up every 1000 points
        new_level = (self.score // 1000) + 1
        if new_level > self.level:
            self.level = new_level
            print(f"Level up! Now level {self.level}")
    
    def set_player_name(self, name):
        """Set the player name"""
        self.player_name = name
        print(f"Player name set to: {name}")
    
    def get_game_state(self):
        """Get current game state"""
        return {
            "score": self.score,
            "level": self.level,
            "player_name": self.player_name,
            "game_started": self.game_started
        }
    
    def load_game_settings(self):
        """Load game settings (placeholder)"""
        # In a real game, this would load from a file
        print("Loading game settings...")
    
    def save_game_settings(self):
        """Save game settings (placeholder)"""
        # In a real game, this would save to a file
        print("Saving game settings...")


# Alternative: You can also use the module itself as a singleton
# by defining functions and variables at module level

# Global variables that can be accessed directly
module_score = 0
module_level = 1

def module_add_score(points):
    """Module-level function example"""
    global module_score, module_level
    module_score += points
    new_level = (module_score // 1000) + 1
    if new_level > module_level:
        module_level = new_level
        print(f"Module level up! Now level {module_level}")

def module_get_score():
    """Get module-level score"""
    return module_score
