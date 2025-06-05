"""
Example Game Script Using Global Scope Scriptable Objects
Shows how to use scriptable objects in actual game scenarios
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Initialize scriptable objects and inject into global scope
from core.scriptable_objects.loader import initialize_loader, inject_scriptable_objects

# Initialize with demo data
demo_dir = Path(__file__).parent / "demo_project"
initialize_loader(str(demo_dir), enable_global_scope=True)

# Inject into global namespace
inject_scriptable_objects(globals(), "SO")


class Player:
    """Example player class that uses scriptable objects"""
    
    def __init__(self, name: str):
        self.name = name
        self.level = 1
        self.health = 100
        self.max_health = 100
        self.inventory = {}
        self.equipped_weapon = None
        self.gold = 100
        
        # Load player data from scriptable objects if it exists
        try:
            # This would load a player character template
            player_template = SO.Character.Player_Template
            self.max_health = player_template.health
            self.health = self.max_health
        except AttributeError:
            pass  # Use defaults if no template exists
    
    def add_item(self, item_name: str, quantity: int = 1):
        """Add an item to inventory using scriptable object data"""
        try:
            # Get item data from scriptable objects
            item_data = getattr(SO.Item, item_name.replace(' ', '_'))
            
            # Check if item can stack
            if item_data.stackable:
                current_qty = self.inventory.get(item_name, 0)
                max_stack = item_data.max_stack
                
                if current_qty + quantity <= max_stack:
                    self.inventory[item_name] = current_qty + quantity
                    print(f"Added {quantity}x {item_data.display_name}")
                    return True
                else:
                    print(f"Cannot add {quantity}x {item_name} - would exceed stack limit")
                    return False
            else:
                if item_name not in self.inventory:
                    self.inventory[item_name] = 1
                    print(f"Added {item_data.display_name}")
                    return True
                else:
                    print(f"Cannot add {item_name} - non-stackable item already in inventory")
                    return False
        except AttributeError:
            print(f"Item '{item_name}' not found in scriptable objects")
            return False
    
    def use_item(self, item_name: str):
        """Use an item from inventory"""
        if item_name not in self.inventory:
            print(f"You don't have {item_name}")
            return False
        
        try:
            # Get item data
            item_data = getattr(SO.Item, item_name.replace(' ', '_'))
            
            # Remove from inventory
            self.inventory[item_name] -= 1
            if self.inventory[item_name] <= 0:
                del self.inventory[item_name]
            
            print(f"Used {item_data.display_name}")
            
            # Apply item effects based on type
            if "health" in item_name.lower() or "potion" in item_name.lower():
                heal_amount = 50  # Could be stored in scriptable object
                self.heal(heal_amount)
                print(f"Restored {heal_amount} health!")
            
            return True
        except AttributeError:
            print(f"Item data for '{item_name}' not found")
            return False
    
    def equip_weapon(self, weapon_name: str):
        """Equip a weapon using scriptable object data"""
        try:
            weapon_data = getattr(SO.Weapon, weapon_name.replace(' ', '_'))
            self.equipped_weapon = weapon_data
            print(f"Equipped {weapon_data.weapon_name}")
            print(f"  Damage: {weapon_data.damage}")
            print(f"  Attack Speed: {weapon_data.attack_speed}")
            print(f"  Critical Chance: {weapon_data.critical_chance * 100:.1f}%")
            return True
        except AttributeError:
            print(f"Weapon '{weapon_name}' not found")
            return False
    
    def attack(self, target):
        """Attack a target using equipped weapon"""
        if not self.equipped_weapon:
            damage = 5  # Base unarmed damage
            print(f"{self.name} attacks with bare hands for {damage} damage")
            return damage
        
        # Use weapon's calculate_damage method if available
        if hasattr(self.equipped_weapon, 'calculate_damage'):
            damage, is_crit = self.equipped_weapon.calculate_damage()
            crit_text = " CRITICAL HIT!" if is_crit else ""
            print(f"{self.name} attacks with {self.equipped_weapon.weapon_name} for {damage} damage{crit_text}")
            return damage
        else:
            damage = self.equipped_weapon.damage
            print(f"{self.name} attacks with {self.equipped_weapon.weapon_name} for {damage} damage")
            return damage
    
    def heal(self, amount: int):
        """Heal the player"""
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        actual_heal = self.health - old_health
        print(f"Healed {actual_heal} HP ({self.health}/{self.max_health})")
    
    def take_damage(self, amount: int):
        """Take damage"""
        self.health = max(0, self.health - amount)
        print(f"Took {amount} damage! ({self.health}/{self.max_health})")
        return self.health <= 0
    
    def show_inventory(self):
        """Show inventory with item details from scriptable objects"""
        if not self.inventory:
            print("Inventory is empty")
            return
        
        print("Inventory:")
        total_value = 0
        
        for item_name, quantity in self.inventory.items():
            try:
                item_data = getattr(SO.Item, item_name.replace(' ', '_'))
                value = item_data.value * quantity
                total_value += value
                print(f"  {item_data.display_name} x{quantity} (worth {value} gold)")
            except AttributeError:
                print(f"  {item_name} x{quantity} (unknown item)")
        
        print(f"Total value: {total_value} gold")


class NPC:
    """Example NPC class using scriptable objects"""
    
    def __init__(self, character_name: str):
        try:
            self.data = getattr(SO.Character, character_name.replace(' ', '_'))
            self.name = self.data.character_name
            self.level = self.data.level
            self.health = self.data.health
            self.current_health = self.health
            print(f"Loaded NPC: {self.name} (Level {self.level})")
        except AttributeError:
            print(f"NPC '{character_name}' not found in scriptable objects")
            self.data = None
            self.name = character_name
            self.level = 1
            self.health = 50
            self.current_health = self.health
    
    def speak(self):
        """NPC speaks using dialogue from scriptable objects"""
        if self.data and hasattr(self.data, 'dialogue_file'):
            dialogue_file = self.data.dialogue_file
            if dialogue_file:
                print(f"{self.name}: [Would load dialogue from {dialogue_file}]")
            else:
                print(f"{self.name}: Hello, traveler!")
        else:
            print(f"{self.name}: Greetings!")
    
    def take_damage(self, amount: int):
        """Take damage using scriptable object methods if available"""
        if self.data and hasattr(self.data, 'take_damage'):
            died = self.data.take_damage(amount)
            self.current_health = getattr(self.data, 'current_health', self.current_health)
            return died
        else:
            self.current_health = max(0, self.current_health - amount)
            print(f"{self.name} takes {amount} damage!")
            return self.current_health <= 0


def demo_gameplay():
    """Demonstrate gameplay using scriptable objects"""
    print("Game Script Demo with Global Scope Scriptable Objects")
    print("=" * 60)
    
    # Create player
    player = Player("Hero")
    
    print("\n1. Inventory Management")
    print("-" * 25)
    
    # Add items to inventory
    player.add_item("Health Potion", 3)
    player.show_inventory()
    
    # Use an item
    print("\nUsing health potion...")
    player.take_damage(30)  # Take some damage first
    player.use_item("Health Potion")
    
    print("\n2. Weapon System")
    print("-" * 20)
    
    # Equip weapon
    player.equip_weapon("Magic Sword")
    
    # Create an NPC to fight
    print("\nEncountering Village Elder...")
    elder = NPC("Village Elder")
    elder.speak()
    
    # Combat
    print("\nCombat begins!")
    damage = player.attack(elder)
    died = elder.take_damage(damage)
    
    if died:
        print(f"{elder.name} has been defeated!")
    else:
        print(f"{elder.name} has {elder.current_health} health remaining")
    
    print("\n3. Dynamic Item Access")
    print("-" * 25)
    
    # Show how to access any item dynamically
    print("Available items in the database:")
    try:
        items = SO.Item
        for item_name in dir(items):
            if not item_name.startswith('_'):
                item_data = getattr(items, item_name)
                print(f"  {item_data.display_name} - {item_data.description}")
    except AttributeError:
        print("No items found")
    
    print("\n4. Quest System Integration")
    print("-" * 30)
    
    # Show how quests could work
    try:
        quest = SO.Quest.Tutorial_Quest
        print(f"Available Quest: {quest.quest_name}")
        print(f"Description: {quest.description}")
        print(f"Objective: {quest.objective}")
        print(f"Rewards: {quest.reward_gold} gold, {quest.reward_exp} XP")
        print(f"Required Level: {quest.required_level}")
        
        if player.level >= quest.required_level:
            print("Player can accept this quest!")
        else:
            print("Player level too low for this quest")
    except AttributeError:
        print("No quests found")
    
    print("\n5. Performance Benefits")
    print("-" * 25)
    
    print("Benefits of global scope access:")
    print("✓ Natural syntax: SO.Item.Health_Potion.value")
    print("✓ Lazy loading: Only loads data when accessed")
    print("✓ Automatic caching: Frequently used objects stay in memory")
    print("✓ Memory efficient: Unused objects are automatically unloaded")
    print("✓ Type safety: Access fields and methods directly")
    print("✓ IDE support: Auto-completion works with loaded objects")


def demo_advanced_usage():
    """Demonstrate advanced usage patterns"""
    print("\n\n6. Advanced Usage Patterns")
    print("-" * 30)
    
    print("Dynamic template access:")
    print("```python")
    print("# Get all items of a certain type")
    print("weapons = []")
    print("for item_name in dir(SO.Item):")
    print("    if not item_name.startswith('_'):")
    print("        item = getattr(SO.Item, item_name)")
    print("        if hasattr(item, 'weapon_type'):")
    print("            weapons.append(item)")
    print("```")
    
    print("\nConditional method calls:")
    print("```python")
    print("# Safe method calling")
    print("if hasattr(SO.Character.Village_Elder, 'special_ability'):")
    print("    SO.Character.Village_Elder.special_ability()")
    print("```")
    
    print("\nData validation:")
    print("```python")
    print("# Validate item before use")
    print("item = SO.Item.Health_Potion")
    print("if item.value > 0 and item.stackable:")
    print("    player.add_item('Health Potion')")
    print("```")


if __name__ == "__main__":
    try:
        demo_gameplay()
        demo_advanced_usage()
        
        print("\n\nDemo completed successfully!")
        print("The global scope system enables natural, efficient access to scriptable objects.")
        
    except Exception as e:
        print(f"Error running demo: {e}")
        print("Make sure to run scriptable_objects_demo.py first to create example data")
