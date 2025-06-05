"""
Example of integrating Scriptable Objects with game scripts
Shows how to use scriptable objects in actual game scenarios
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.scriptable_objects.loader import (
    initialize_loader, load_item, load_character, load_quest,
    find_items_by_type, find_available_quests
)


class GameInventory:
    """Example inventory system using scriptable objects"""
    
    def __init__(self):
        self.items = {}  # item_name -> quantity
    
    def add_item(self, item_name: str, quantity: int = 1):
        """Add an item to inventory"""
        item_data = load_item(item_name)
        if not item_data:
            print(f"Item '{item_name}' not found!")
            return False
        
        # Check if item can stack
        if item_data.get_value("stackable", True):
            current_qty = self.items.get(item_name, 0)
            max_stack = item_data.get_value("max_stack", 99)
            
            if current_qty + quantity <= max_stack:
                self.items[item_name] = current_qty + quantity
                print(f"Added {quantity}x {item_data.get_value('display_name')} to inventory")
                return True
            else:
                print(f"Cannot add {quantity}x {item_name} - would exceed stack limit of {max_stack}")
                return False
        else:
            # Non-stackable items
            if item_name not in self.items:
                self.items[item_name] = 1
                print(f"Added {item_data.get_value('display_name')} to inventory")
                return True
            else:
                print(f"Cannot add {item_name} - non-stackable item already in inventory")
                return False
    
    def use_item(self, item_name: str):
        """Use an item from inventory"""
        if item_name not in self.items:
            print(f"Item '{item_name}' not in inventory!")
            return False
        
        item_data = load_item(item_name)
        if not item_data:
            print(f"Item data for '{item_name}' not found!")
            return False
        
        # Remove one from inventory
        self.items[item_name] -= 1
        if self.items[item_name] <= 0:
            del self.items[item_name]
        
        print(f"Used {item_data.get_value('display_name')}")
        
        # Example: Health potion restores health
        if "health" in item_name.lower():
            print("  +50 Health restored!")
        
        return True
    
    def get_total_value(self):
        """Calculate total value of inventory"""
        total_value = 0
        for item_name, quantity in self.items.items():
            item_data = load_item(item_name)
            if item_data:
                item_value = item_data.get_value("value", 0)
                total_value += item_value * quantity
        return total_value
    
    def list_items(self):
        """List all items in inventory"""
        if not self.items:
            print("Inventory is empty")
            return
        
        print("Inventory:")
        for item_name, quantity in self.items.items():
            item_data = load_item(item_name)
            if item_data:
                display_name = item_data.get_value("display_name", item_name)
                value = item_data.get_value("value", 0)
                print(f"  {display_name} x{quantity} (worth {value * quantity} gold)")


class GameCharacter:
    """Example character system using scriptable objects"""
    
    def __init__(self, character_name: str):
        self.character_data = load_character(character_name)
        if not self.character_data:
            raise ValueError(f"Character '{character_name}' not found!")
        
        # Initialize runtime stats from template
        self.current_health = self.character_data.get_value("health", 100)
        self.current_mana = self.character_data.get_value("mana", 50)
        self.position = self.character_data.get_value("position", [0.0, 0.0])
        
        print(f"Loaded character: {self.character_data.get_value('character_name')}")
        print(f"  Level: {self.character_data.get_value('level')}")
        print(f"  Health: {self.current_health}/{self.character_data.get_value('health')}")
        print(f"  Mana: {self.current_mana}/{self.character_data.get_value('mana')}")
    
    def take_damage(self, amount: int):
        """Apply damage using template method"""
        if hasattr(self.character_data, 'take_damage'):
            # Use template's custom method if available
            died = self.character_data.take_damage(amount)
            self.current_health = getattr(self.character_data, 'current_health', self.current_health)
            return died
        else:
            # Fallback implementation
            self.current_health = max(0, self.current_health - amount)
            print(f"{self.character_data.get_value('character_name')} takes {amount} damage!")
            return self.current_health <= 0
    
    def heal(self, amount: int):
        """Heal the character"""
        max_health = self.character_data.get_value("health", 100)
        self.current_health = min(max_health, self.current_health + amount)
        print(f"{self.character_data.get_value('character_name')} healed for {amount} HP")
    
    def level_up(self):
        """Level up using template method"""
        if hasattr(self.character_data, 'level_up'):
            self.character_data.level_up()
            print(f"{self.character_data.get_value('character_name')} leveled up!")
            print(f"  New level: {self.character_data.get_value('level')}")
            print(f"  New max health: {self.character_data.get_value('health')}")
            print(f"  New max mana: {self.character_data.get_value('mana')}")


class QuestManager:
    """Example quest system using scriptable objects"""
    
    def __init__(self):
        self.active_quests = []
        self.completed_quests = []
    
    def get_available_quests(self, player_level: int):
        """Get quests available to player"""
        available = find_available_quests(player_level)
        
        # Filter out already completed quests
        completed_names = [q.get_value("quest_name") for q in self.completed_quests]
        available = [q for q in available if q.get_value("quest_name") not in completed_names]
        
        # Filter out already active quests
        active_names = [q.get_value("quest_name") for q in self.active_quests]
        available = [q for q in available if q.get_value("quest_name") not in active_names]
        
        return available
    
    def start_quest(self, quest_identifier: str):
        """Start a quest by instance name or quest name"""
        # Try loading by instance name first
        quest_data = load_quest(quest_identifier)
        if not quest_data:
            print(f"Quest '{quest_identifier}' not found!")
            return False
        
        # Check if already active or completed
        if quest_data in self.active_quests:
            print(f"Quest '{quest_identifier}' is already active!")
            return False

        if quest_data in self.completed_quests:
            print(f"Quest '{quest_identifier}' is already completed!")
            return False
        
        self.active_quests.append(quest_data)
        print(f"Started quest: {quest_data.get_value('quest_name')}")
        print(f"  {quest_data.get_value('description')}")
        print(f"  Objective: {quest_data.get_value('objective')}")
        return True
    
    def complete_quest(self, quest_name: str):
        """Complete a quest and give rewards"""
        quest_data = None
        for quest in self.active_quests:
            if quest.get_value("quest_name") == quest_name:
                quest_data = quest
                break
        
        if not quest_data:
            print(f"Quest '{quest_name}' is not active!")
            return False
        
        # Remove from active and add to completed
        self.active_quests.remove(quest_data)
        self.completed_quests.append(quest_data)
        
        # Give rewards
        gold_reward = quest_data.get_value("reward_gold", 0)
        exp_reward = quest_data.get_value("reward_exp", 0)
        
        print(f"Completed quest: {quest_name}")
        if gold_reward > 0:
            print(f"  Received {gold_reward} gold!")
        if exp_reward > 0:
            print(f"  Received {exp_reward} experience!")
        
        return True
    
    def list_active_quests(self):
        """List all active quests"""
        if not self.active_quests:
            print("No active quests")
            return
        
        print("Active Quests:")
        for quest in self.active_quests:
            name = quest.get_value("quest_name")
            objective = quest.get_value("objective")
            is_main = quest.get_value("is_main_quest", False)
            quest_type = "Main" if is_main else "Side"
            print(f"  [{quest_type}] {name}: {objective}")


def demo_game_systems():
    """Demonstrate the game systems using scriptable objects"""
    print("Game Integration Demo")
    print("=" * 40)
    
    # Initialize the loader with demo data
    demo_dir = Path(__file__).parent / "demo_project"
    initialize_loader(str(demo_dir))
    
    print("\n1. Inventory System Demo")
    print("-" * 25)
    inventory = GameInventory()
    inventory.add_item("Health Potion", 3)
    inventory.add_item("Health Potion", 2)  # Should stack
    inventory.list_items()
    print(f"Total inventory value: {inventory.get_total_value()} gold")
    
    inventory.use_item("Health Potion")
    inventory.list_items()
    
    print("\n2. Character System Demo")
    print("-" * 25)
    try:
        character = GameCharacter("Village Elder")
        character.take_damage(50)
        character.heal(25)
        character.level_up()
    except ValueError as e:
        print(f"Error: {e}")
        print("Run the scriptable_objects_demo.py first to create example data")
    
    print("\n3. Quest System Demo")
    print("-" * 20)
    quest_manager = QuestManager()
    
    # Get available quests for level 1 player
    available = quest_manager.get_available_quests(1)
    print(f"Available quests for level 1 player: {len(available)}")
    for quest in available:
        print(f"  - {quest.get_value('quest_name')}")
    
    # Start and complete a quest
    if available:
        first_quest_name = available[0].get_value("quest_name")
        # Use the instance name, not the quest_name field
        first_quest_instance_name = available[0].name
        print(f"Starting quest instance: {first_quest_instance_name}")
        quest_manager.start_quest(first_quest_instance_name)
        quest_manager.list_active_quests()
        quest_manager.complete_quest(first_quest_name)
        quest_manager.list_active_quests()


if __name__ == "__main__":
    demo_game_systems()
