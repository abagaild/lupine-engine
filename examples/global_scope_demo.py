"""
Global Scope Demo for Scriptable Objects
Demonstrates accessing scriptable objects through global namespace
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.scriptable_objects.loader import (
    initialize_loader, get_scriptable_objects, inject_scriptable_objects,
    get_scriptable_objects_stats, clear_scriptable_objects_cache
)


def demo_global_scope_access():
    """Demonstrate global scope access to scriptable objects"""
    print("Global Scope Demo for Scriptable Objects")
    print("=" * 50)
    
    # Initialize the loader with demo data
    demo_dir = Path(__file__).parent / "demo_project"
    initialize_loader(str(demo_dir), enable_global_scope=True, cache_size=50, cache_timeout=120.0)
    
    # Get the global namespace
    SO = get_scriptable_objects()
    
    if SO is None:
        print("Error: Global scope not initialized")
        return
    
    print("\n1. Accessing Templates")
    print("-" * 25)
    
    # List available templates
    print("Available templates:")
    for template_name in dir(SO):
        if not template_name.startswith('_'):
            print(f"  - {template_name}")
    
    print("\n2. Accessing Instances")
    print("-" * 25)
    
    try:
        # Access Item template
        items = SO.Item
        print(f"Item template: {items}")
        
        # List available instances
        print("Available item instances:")
        for instance_name in dir(items):
            if not instance_name.startswith('_'):
                print(f"  - {instance_name}")
        
        # Access specific instance
        health_potion = SO.Item.Health_Potion
        print(f"\nHealth Potion instance: {health_potion}")
        
        # Access fields
        print(f"Display name: {health_potion.display_name}")
        print(f"Description: {health_potion.description}")
        print(f"Value: {health_potion.value}")
        print(f"Weight: {health_potion.weight}")
        print(f"Rarity color: {health_potion.rarity_color}")
        
        # Call custom methods
        if hasattr(health_potion, 'get_display_text'):
            print(f"Display text: {health_potion.get_display_text()}")
        
    except AttributeError as e:
        print(f"Error accessing items: {e}")
        print("Make sure to run scriptable_objects_demo.py first to create example data")
    
    print("\n3. Accessing Characters")
    print("-" * 25)
    
    try:
        # Access Character template
        characters = SO.Character
        print(f"Character template: {characters}")
        
        # Access Village Elder
        elder = SO.Character.Village_Elder
        print(f"Village Elder: {elder}")
        print(f"Character name: {elder.character_name}")
        print(f"Level: {elder.level}")
        print(f"Health: {elder.health}")
        print(f"Position: {elder.position}")
        
        # Call custom methods
        if hasattr(elder, 'take_damage'):
            print(f"Taking 25 damage...")
            died = elder.take_damage(25)
            print(f"Character died: {died}")
            print(f"Current health: {getattr(elder, 'current_health', 'Unknown')}")
        
    except AttributeError as e:
        print(f"Error accessing characters: {e}")
    
    print("\n4. Accessing Weapons")
    print("-" * 25)
    
    try:
        # Access Weapon template
        weapons = SO.Weapon
        print(f"Weapon template: {weapons}")
        
        # Access Magic Sword
        sword = SO.Weapon.Magic_Sword
        print(f"Magic Sword: {sword}")
        print(f"Weapon name: {sword.weapon_name}")
        print(f"Damage: {sword.damage}")
        print(f"Attack speed: {sword.attack_speed}")
        print(f"Critical chance: {sword.critical_chance}")
        
        # Call custom methods
        if hasattr(sword, 'calculate_damage'):
            damage, is_crit = sword.calculate_damage()
            crit_text = " (CRITICAL!)" if is_crit else ""
            print(f"Calculated damage: {damage}{crit_text}")
        
    except AttributeError as e:
        print(f"Error accessing weapons: {e}")
    
    print("\n5. Modifying Instance Data")
    print("-" * 30)
    
    try:
        # Modify health potion value
        original_value = SO.Item.Health_Potion.value
        print(f"Original health potion value: {original_value}")
        
        SO.Item.Health_Potion.value = 30
        print(f"Modified health potion value: {SO.Item.Health_Potion.value}")
        
        # Restore original value
        SO.Item.Health_Potion.value = original_value
        print(f"Restored health potion value: {SO.Item.Health_Potion.value}")
        
    except AttributeError as e:
        print(f"Error modifying data: {e}")
    
    print("\n6. Cache Statistics")
    print("-" * 20)
    
    stats = get_scriptable_objects_stats()
    print(f"Template proxies: {stats.get('template_proxies', 0)}")
    print(f"Cached instances: {stats.get('cached_instances', 0)}")
    print(f"Cache size limit: {stats.get('cache_size_limit', 0)}")
    print(f"Cache timeout: {stats.get('cache_timeout', 0)} seconds")


def demo_injection_into_globals():
    """Demonstrate injecting scriptable objects into global namespace"""
    print("\n\n7. Global Namespace Injection")
    print("-" * 35)
    
    # Inject into current globals
    inject_scriptable_objects(globals(), "ScriptableObjects")
    
    try:
        # Now we can access directly
        print("Accessing through injected namespace:")
        print(f"Health Potion value: {ScriptableObjects.Item.Health_Potion.value}")
        print(f"Elder's name: {ScriptableObjects.Character.Village_Elder.character_name}")
        
        # This would work in any script that has the injection
        print("\nExample script usage:")
        print("# In your game script:")
        print("from core.scriptable_objects.loader import inject_scriptable_objects")
        print("inject_scriptable_objects(globals(), 'SO')")
        print("")
        print("# Now you can use:")
        print("player_weapon = SO.Weapon.Magic_Sword")
        print("damage = player_weapon.damage")
        print("if hasattr(player_weapon, 'calculate_damage'):")
        print("    total_damage, is_crit = player_weapon.calculate_damage()")
        
    except NameError as e:
        print(f"Error with injection: {e}")


def demo_performance_features():
    """Demonstrate performance features"""
    print("\n\n8. Performance Features")
    print("-" * 25)
    
    print("Lazy Loading:")
    print("- Templates are loaded on first access")
    print("- Instances are loaded on first field access")
    print("- Unused instances are automatically unloaded after timeout")
    
    print("\nCaching:")
    print("- Recently accessed instances stay in memory")
    print("- Cache size limit prevents memory bloat")
    print("- LRU eviction removes oldest unused instances")
    
    print("\nMemory Management:")
    print("- Background thread cleans up expired cache entries")
    print("- Weak references prevent memory leaks")
    print("- Manual cache clearing available")
    
    # Clear cache to demonstrate
    print("\nClearing cache...")
    clear_scriptable_objects_cache()
    
    stats_after = get_scriptable_objects_stats()
    print(f"Cached instances after clear: {stats_after.get('cached_instances', 0)}")


def demo_name_conversion():
    """Demonstrate name conversion for Python identifiers"""
    print("\n\n9. Name Conversion")
    print("-" * 20)
    
    print("Scriptable object names with spaces and special characters")
    print("are automatically converted to valid Python identifiers:")
    print("")
    print("Examples:")
    print("'Health Potion' -> 'Health_Potion'")
    print("'Magic Sword +1' -> 'Magic_Sword__1'")
    print("'Village Elder (NPC)' -> 'Village_Elder__NPC_'")
    print("'123 Gold Coins' -> '_123_Gold_Coins'")
    print("")
    print("This allows natural access like:")
    print("SO.Item.Health_Potion.value")
    print("SO.Character.Village_Elder.character_name")


def main():
    """Main demo function"""
    demo_global_scope_access()
    demo_injection_into_globals()
    demo_performance_features()
    demo_name_conversion()
    
    print("\n\nDemo completed!")
    print("The global scope system provides:")
    print("✓ Natural dot-notation access to scriptable objects")
    print("✓ Lazy loading for memory efficiency")
    print("✓ Automatic caching with LRU eviction")
    print("✓ Background cleanup of unused instances")
    print("✓ Safe name conversion for Python identifiers")
    print("✓ Easy integration into game scripts")


if __name__ == "__main__":
    main()
