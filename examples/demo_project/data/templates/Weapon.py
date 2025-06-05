"""
Weapon - Weapon item with combat stats
Generated scriptable object template
"""

from core.scriptable_objects.instance import ScriptableObjectInstance

class Weapon(ScriptableObjectInstance):
    """
    Weapon item with combat stats
    """

    def __init__(self, **kwargs):
        super().__init__("Weapon", **kwargs)

        self.weapon_name = kwargs.get("weapon_name", 'Basic Sword')
        self.damage = kwargs.get("damage", 10)
        self.attack_speed = kwargs.get("attack_speed", 1.0)
        self.critical_chance = kwargs.get("critical_chance", 0.05)
        self.durability = kwargs.get("durability", 100)
        self.weapon_type = kwargs.get("weapon_type", 'sword')
        self.two_handed = kwargs.get("two_handed", False)
        self.enchantment_slots = kwargs.get("enchantment_slots", 0)

    def _ready(self):
        """Called when the object is ready"""
        pass

    # Custom code

    
        def calculate_damage(self, base_damage_bonus=0):
            """Calculate total damage including bonuses"""
            total_damage = self.damage + base_damage_bonus
            
            # Apply critical hit
            import random
            if random.random() < self.critical_chance:
                total_damage *= 2
                return total_damage, True  # Return damage and crit flag
            
            return total_damage, False
        
        def repair(self, amount):
            """Repair the weapon"""
            self.current_durability = min(self.durability, 
                                        getattr(self, 'current_durability', self.durability) + amount)
        