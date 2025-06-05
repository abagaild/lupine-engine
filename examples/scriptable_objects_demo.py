"""
Demo script for Scriptable Objects System
Creates example templates and instances to demonstrate the system
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.scriptable_objects.manager import ScriptableObjectManager
from core.scriptable_objects.template import ScriptableObjectTemplate
from core.scriptable_objects.field import ScriptableObjectField, FieldType


def create_example_templates(manager: ScriptableObjectManager):
    """Create example templates to demonstrate the system"""
    
    # 1. Item Template
    item_template = ScriptableObjectTemplate("Item", "Basic game item with properties")
    item_template.category = "Game Objects"
    
    # Add fields
    item_template.add_field(ScriptableObjectField("display_name", FieldType.STRING, "New Item", "Display name shown to player"))
    item_template.add_field(ScriptableObjectField("description", FieldType.STRING, "", "Item description"))
    item_template.add_field(ScriptableObjectField("icon", FieldType.IMAGE, "", "Item icon image", "Display"))
    item_template.add_field(ScriptableObjectField("value", FieldType.INT, 0, "Item value in gold", "Economy"))
    item_template.add_field(ScriptableObjectField("weight", FieldType.FLOAT, 1.0, "Item weight", "Economy"))
    item_template.add_field(ScriptableObjectField("stackable", FieldType.BOOL, True, "Can this item stack?", "Properties"))
    item_template.add_field(ScriptableObjectField("max_stack", FieldType.INT, 99, "Maximum stack size", "Properties"))
    item_template.add_field(ScriptableObjectField("rarity_color", FieldType.COLOR, [1.0, 1.0, 1.0, 1.0], "Color indicating rarity", "Display"))
    
    # Add some custom code
    item_template.base_code = '''
    def get_display_text(self):
        """Get formatted display text for this item"""
        return f"{self.display_name} (x{self.quantity if hasattr(self, 'quantity') else 1})"
    
    def can_stack_with(self, other_item):
        """Check if this item can stack with another"""
        return (self.stackable and 
                hasattr(other_item, 'template_name') and 
                other_item.template_name == self.template_name and
                other_item.display_name == self.display_name)
    '''
    
    manager.save_template(item_template)
    
    # 2. Character Template
    character_template = ScriptableObjectTemplate("Character", "NPC or player character data")
    character_template.category = "Characters"
    
    character_template.add_field(ScriptableObjectField("character_name", FieldType.STRING, "Unnamed", "Character's name", "Basic Info"))
    character_template.add_field(ScriptableObjectField("level", FieldType.INT, 1, "Character level", "Stats"))
    character_template.add_field(ScriptableObjectField("health", FieldType.INT, 100, "Maximum health", "Stats"))
    character_template.add_field(ScriptableObjectField("mana", FieldType.INT, 50, "Maximum mana", "Stats"))
    character_template.add_field(ScriptableObjectField("position", FieldType.VECTOR2, [0.0, 0.0], "World position", "Transform"))
    character_template.add_field(ScriptableObjectField("portrait", FieldType.IMAGE, "", "Character portrait", "Display"))
    character_template.add_field(ScriptableObjectField("is_player", FieldType.BOOL, False, "Is this a player character?", "Basic Info"))
    character_template.add_field(ScriptableObjectField("dialogue_file", FieldType.PATH, "", "Path to dialogue file", "Behavior"))
    
    character_template.base_code = '''
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
    '''
    
    manager.save_template(character_template)
    
    # 3. Quest Template
    quest_template = ScriptableObjectTemplate("Quest", "Game quest or mission")
    quest_template.category = "Quests"
    
    quest_template.add_field(ScriptableObjectField("quest_name", FieldType.STRING, "New Quest", "Quest title", "Basic Info"))
    quest_template.add_field(ScriptableObjectField("description", FieldType.STRING, "", "Quest description", "Basic Info"))
    quest_template.add_field(ScriptableObjectField("objective", FieldType.STRING, "", "Current objective text", "Progress"))
    quest_template.add_field(ScriptableObjectField("reward_gold", FieldType.INT, 0, "Gold reward", "Rewards"))
    quest_template.add_field(ScriptableObjectField("reward_exp", FieldType.INT, 0, "Experience reward", "Rewards"))
    quest_template.add_field(ScriptableObjectField("required_level", FieldType.INT, 1, "Minimum level to start", "Requirements"))
    quest_template.add_field(ScriptableObjectField("is_main_quest", FieldType.BOOL, False, "Is this a main story quest?", "Basic Info"))
    quest_template.add_field(ScriptableObjectField("prerequisites", FieldType.ARRAY, [], "Required completed quests", "Requirements"))
    
    manager.save_template(quest_template)
    
    # 4. Weapon Template
    weapon_template = ScriptableObjectTemplate("Weapon", "Weapon item with combat stats")
    weapon_template.category = "Equipment"
    
    weapon_template.add_field(ScriptableObjectField("weapon_name", FieldType.STRING, "Basic Sword", "Weapon name", "Basic Info"))
    weapon_template.add_field(ScriptableObjectField("damage", FieldType.INT, 10, "Base damage", "Combat Stats"))
    weapon_template.add_field(ScriptableObjectField("attack_speed", FieldType.FLOAT, 1.0, "Attacks per second", "Combat Stats"))
    weapon_template.add_field(ScriptableObjectField("critical_chance", FieldType.FLOAT, 0.05, "Critical hit chance (0-1)", "Combat Stats"))
    weapon_template.add_field(ScriptableObjectField("durability", FieldType.INT, 100, "Maximum durability", "Properties"))
    weapon_template.add_field(ScriptableObjectField("weapon_type", FieldType.STRING, "sword", "Type of weapon", "Basic Info"))
    weapon_template.add_field(ScriptableObjectField("two_handed", FieldType.BOOL, False, "Requires both hands?", "Properties"))
    weapon_template.add_field(ScriptableObjectField("enchantment_slots", FieldType.INT, 0, "Number of enchantment slots", "Properties"))
    
    weapon_template.base_code = '''
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
    '''
    
    manager.save_template(weapon_template)
    
    print("Created example templates:")
    print("- Item (basic game items)")
    print("- Character (NPCs and players)")
    print("- Quest (missions and objectives)")
    print("- Weapon (combat equipment)")


def create_example_instances(manager: ScriptableObjectManager):
    """Create example instances of the templates"""
    
    # Create some items
    health_potion = manager.create_instance("Item", "Health Potion")
    if health_potion:
        health_potion.set_value("display_name", "Health Potion")
        health_potion.set_value("description", "Restores 50 HP when consumed")
        health_potion.set_value("value", 25)
        health_potion.set_value("weight", 0.1)
        health_potion.set_value("rarity_color", [0.0, 1.0, 0.0, 1.0])  # Green
        manager.save_instance(health_potion)
    
    magic_sword = manager.create_instance("Weapon", "Magic Sword")
    if magic_sword:
        magic_sword.set_value("weapon_name", "Enchanted Blade")
        magic_sword.set_value("damage", 25)
        magic_sword.set_value("attack_speed", 1.2)
        magic_sword.set_value("critical_chance", 0.15)
        magic_sword.set_value("enchantment_slots", 2)
        manager.save_instance(magic_sword)
    
    # Create a character
    village_elder = manager.create_instance("Character", "Village Elder")
    if village_elder:
        village_elder.set_value("character_name", "Elder Thorne")
        village_elder.set_value("level", 50)
        village_elder.set_value("health", 200)
        village_elder.set_value("mana", 150)
        village_elder.set_value("position", [100.0, 200.0])
        village_elder.set_value("is_player", False)
        manager.save_instance(village_elder)
    
    # Create a quest
    first_quest = manager.create_instance("Quest", "Tutorial Quest")
    if first_quest:
        first_quest.set_value("quest_name", "Welcome to Adventure")
        first_quest.set_value("description", "Learn the basics of the game")
        first_quest.set_value("objective", "Talk to the Village Elder")
        first_quest.set_value("reward_gold", 50)
        first_quest.set_value("reward_exp", 100)
        first_quest.set_value("required_level", 1)
        first_quest.set_value("is_main_quest", True)
        manager.save_instance(first_quest)
    
    print("\nCreated example instances:")
    print("- Health Potion (Item)")
    print("- Enchanted Blade (Weapon)")
    print("- Elder Thorne (Character)")
    print("- Welcome to Adventure (Quest)")


def main():
    """Main demo function"""
    # Create a temporary project directory for testing
    demo_dir = Path(__file__).parent / "demo_project"
    demo_dir.mkdir(exist_ok=True)
    
    # Initialize the manager
    manager = ScriptableObjectManager(str(demo_dir))
    
    print("Scriptable Objects System Demo")
    print("=" * 40)
    
    # Create templates
    create_example_templates(manager)
    
    # Create instances
    create_example_instances(manager)
    
    print(f"\nDemo data created in: {demo_dir}")
    print("You can now open this in the Lupine Engine editor to see the scriptable objects system in action!")
    
    # Show summary
    templates = manager.get_all_templates()
    all_instances = manager.get_all_instances()
    
    print(f"\nSummary:")
    print(f"Templates: {len(templates)}")
    total_instances = sum(len(instances) for instances in all_instances.values())
    print(f"Instances: {total_instances}")
    
    print("\nTemplate details:")
    for template in templates:
        instances = all_instances.get(template.name, [])
        print(f"  {template.name}: {len(template.fields)} fields, {len(instances)} instances")


if __name__ == "__main__":
    main()
