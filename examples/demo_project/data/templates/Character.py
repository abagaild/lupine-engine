"""
Character - NPC or player character data
Generated scriptable object template
"""

from core.scriptable_objects.instance import ScriptableObjectInstance

class Character(ScriptableObjectInstance):
    """
    NPC or player character data
    """

    def __init__(self, **kwargs):
        super().__init__("Character", **kwargs)

        self.character_name = kwargs.get("character_name", 'Unnamed')
        self.level = kwargs.get("level", 1)
        self.health = kwargs.get("health", 100)
        self.mana = kwargs.get("mana", 50)
        self.position = kwargs.get("position", [0.0, 0.0])
        self.portrait = kwargs.get("portrait", '')
        self.is_player = kwargs.get("is_player", False)
        self.dialogue_file = kwargs.get("dialogue_file", '')

    def _ready(self):
        """Called when the object is ready"""
        pass

    # Custom code

    
        def take_damage(self, amount):
            """Apply damage to character"""
            self.current_health = max(0, getattr(self, 'current_health', self.health) - amount)
            return self.current_health <= 0  # Returns True if character died
        
        def heal(self, amount):
            """Heal the character"""
            self.current_health = min(self.health, getattr(self, 'current_health', self.health) + amount)
        
        def level_up(self):
            """Level up the character"""
            self.level += 1
            self.health += 10  # Increase max health
            self.mana += 5     # Increase max mana
        