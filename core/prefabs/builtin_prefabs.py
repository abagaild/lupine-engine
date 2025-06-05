"""
Builtin Prefabs for Lupine Engine
Provides common game prefabs like NPCs, items, enemies, etc.
"""

from datetime import datetime
from .prefab_system import EnhancedPrefab, PrefabType, EventDefinition, VisualScriptInput


def create_builtin_prefabs():
    """Create all builtin prefabs"""
    prefabs = []
    
    # NPC Prefab
    npc_prefab = create_npc_prefab()
    prefabs.append(npc_prefab)
    
    # Enemy Prefab
    enemy_prefab = create_enemy_prefab()
    prefabs.append(enemy_prefab)
    
    # Item Prefab
    item_prefab = create_item_prefab()
    prefabs.append(item_prefab)
    
    # Chest Prefab
    chest_prefab = create_chest_prefab()
    prefabs.append(chest_prefab)
    
    # Door Prefab
    door_prefab = create_door_prefab()
    prefabs.append(door_prefab)
    
    # Sign Prefab
    sign_prefab = create_sign_prefab()
    prefabs.append(sign_prefab)
    
    # Trigger Zone Prefab
    trigger_prefab = create_trigger_zone_prefab()
    prefabs.append(trigger_prefab)
    
    return prefabs


def create_npc_prefab():
    """Create NPC prefab"""
    prefab = EnhancedPrefab("NPC", PrefabType.ENTITY)
    prefab.description = "Non-player character with dialogue and interaction"
    prefab.category = "Characters"
    prefab.icon = "npc.png"
    prefab.base_node_type = "KinematicBody2D"
    
    # Node structure
    prefab.node_structure = {
        "name": "NPC",
        "type": "KinematicBody2D",
        "position": [0, 0],
        "children": [
            {
                "name": "Sprite",
                "type": "Sprite2D",
                "position": [0, 0],
                "texture": "",
                "children": []
            },
            {
                "name": "CollisionShape2D",
                "type": "CollisionShape2D",
                "position": [0, 0],
                "shape": "rectangle",
                "size": [32, 32],
                "children": []
            },
            {
                "name": "InteractionArea",
                "type": "Area2D",
                "position": [0, 0],
                "children": [
                    {
                        "name": "InteractionCollision",
                        "type": "CollisionShape2D",
                        "position": [0, 0],
                        "shape": "rectangle",
                        "size": [48, 48],
                        "children": []
                    }
                ]
            }
        ]
    }
    
    # Properties
    prefab.add_property("npc_name", "string", "NPC", "Name of the NPC", "Basic")
    prefab.add_property("sprite_texture", "path", "", "Sprite texture path", "Appearance")
    prefab.add_property("dialogue_file", "path", "", "Dialogue script file", "Dialogue")
    prefab.add_property("movement_speed", "number", 50.0, "Movement speed", "Movement", min_value=0, max_value=200)
    prefab.add_property("can_move", "boolean", True, "Whether NPC can move", "Movement")
    prefab.add_property("facing_direction", "string", "down", "Initial facing direction", "Movement", 
                       options=["up", "down", "left", "right"])
    prefab.add_property("interaction_distance", "number", 48.0, "Interaction distance", "Interaction", min_value=16, max_value=128)
    
    # Property groups
    prefab.property_groups = {
        "Basic": "Basic NPC properties",
        "Appearance": "Visual appearance settings",
        "Dialogue": "Dialogue and conversation settings",
        "Movement": "Movement and animation settings",
        "Interaction": "Player interaction settings"
    }
    
    # Events
    prefab.add_event("on_interact", "Called when player interacts with NPC", [
        VisualScriptInput("player", "node", description="The player node")
    ])
    prefab.add_event("on_dialogue_start", "Called when dialogue starts")
    prefab.add_event("on_dialogue_end", "Called when dialogue ends")
    prefab.add_event("on_player_nearby", "Called when player enters interaction area", [
        VisualScriptInput("player", "node", description="The player node")
    ])
    prefab.add_event("on_player_left", "Called when player leaves interaction area")
    
    # Default script
    prefab.default_script = '''# NPC Script
!npc_name = "NPC"
!sprite_texture = ""
!dialogue_file = ""
!movement_speed = 50.0
!can_move = True
!facing_direction = "down"
!interaction_distance = 48.0

def _ready():
    # Set up sprite
    sprite = find_child("Sprite")
    if sprite and sprite_texture:
        sprite.texture = load_texture(sprite_texture)
    
    # Set up interaction area
    interaction_area = find_child("InteractionArea")
    if interaction_area:
        interaction_area.body_entered.connect(on_player_nearby)
        interaction_area.body_exited.connect(on_player_left)

def on_interact(player):
    if dialogue_file:
        start_dialogue(dialogue_file)
    else:
        print(f"{npc_name}: Hello!")

def on_dialogue_start():
    print(f"Started dialogue with {npc_name}")

def on_dialogue_end():
    print(f"Ended dialogue with {npc_name}")

def on_player_nearby(player):
    print(f"Player near {npc_name}")

def on_player_left():
    print(f"Player left {npc_name}")
'''
    
    prefab.tags = ["npc", "character", "dialogue", "interaction"]
    prefab.created_at = datetime.now().isoformat()
    prefab.modified_at = prefab.created_at
    
    return prefab


def create_enemy_prefab():
    """Create Enemy prefab"""
    prefab = EnhancedPrefab("Enemy", PrefabType.ENTITY)
    prefab.description = "Basic enemy with AI and combat"
    prefab.category = "Characters"
    prefab.icon = "enemy.png"
    prefab.base_node_type = "KinematicBody2D"
    
    # Node structure
    prefab.node_structure = {
        "name": "Enemy",
        "type": "KinematicBody2D",
        "position": [0, 0],
        "children": [
            {
                "name": "Sprite",
                "type": "Sprite2D",
                "position": [0, 0],
                "texture": "",
                "children": []
            },
            {
                "name": "CollisionShape2D",
                "type": "CollisionShape2D",
                "position": [0, 0],
                "shape": "rectangle",
                "size": [32, 32],
                "children": []
            },
            {
                "name": "DetectionArea",
                "type": "Area2D",
                "position": [0, 0],
                "children": [
                    {
                        "name": "DetectionCollision",
                        "type": "CollisionShape2D",
                        "position": [0, 0],
                        "shape": "circle",
                        "radius": 100,
                        "children": []
                    }
                ]
            }
        ]
    }
    
    # Properties
    prefab.add_property("enemy_name", "string", "Enemy", "Name of the enemy", "Basic")
    prefab.add_property("sprite_texture", "path", "", "Sprite texture path", "Appearance")
    prefab.add_property("max_health", "number", 100.0, "Maximum health", "Combat", min_value=1, max_value=1000)
    prefab.add_property("attack_damage", "number", 10.0, "Attack damage", "Combat", min_value=1, max_value=100)
    prefab.add_property("movement_speed", "number", 75.0, "Movement speed", "Movement", min_value=0, max_value=200)
    prefab.add_property("detection_range", "number", 100.0, "Detection range", "AI", min_value=32, max_value=300)
    prefab.add_property("attack_range", "number", 32.0, "Attack range", "Combat", min_value=16, max_value=100)
    prefab.add_property("ai_type", "string", "aggressive", "AI behavior type", "AI", 
                       options=["passive", "aggressive", "patrol", "guard"])
    
    # Property groups
    prefab.property_groups = {
        "Basic": "Basic enemy properties",
        "Appearance": "Visual appearance settings",
        "Combat": "Combat and damage settings",
        "Movement": "Movement settings",
        "AI": "AI behavior settings"
    }
    
    # Events
    prefab.add_event("on_player_detected", "Called when player is detected", [
        VisualScriptInput("player", "node", description="The player node")
    ])
    prefab.add_event("on_player_lost", "Called when player is lost")
    prefab.add_event("on_attack", "Called when enemy attacks", [
        VisualScriptInput("target", "node", description="The attack target")
    ])
    prefab.add_event("on_take_damage", "Called when enemy takes damage", [
        VisualScriptInput("damage", "number", description="Damage amount"),
        VisualScriptInput("source", "node", description="Damage source")
    ])
    prefab.add_event("on_death", "Called when enemy dies")
    
    prefab.tags = ["enemy", "combat", "ai", "character"]
    prefab.created_at = datetime.now().isoformat()
    prefab.modified_at = prefab.created_at
    
    return prefab


def create_item_prefab():
    """Create Item prefab"""
    prefab = EnhancedPrefab("Item", PrefabType.ITEM)
    prefab.description = "Collectible item"
    prefab.category = "Items"
    prefab.icon = "item.png"
    prefab.base_node_type = "Area2D"
    
    # Node structure
    prefab.node_structure = {
        "name": "Item",
        "type": "Area2D",
        "position": [0, 0],
        "children": [
            {
                "name": "Sprite",
                "type": "Sprite2D",
                "position": [0, 0],
                "texture": "",
                "children": []
            },
            {
                "name": "CollisionShape2D",
                "type": "CollisionShape2D",
                "position": [0, 0],
                "shape": "rectangle",
                "size": [24, 24],
                "children": []
            }
        ]
    }
    
    # Properties
    prefab.add_property("item_name", "string", "Item", "Name of the item", "Basic")
    prefab.add_property("item_id", "string", "", "Unique item ID", "Basic")
    prefab.add_property("sprite_texture", "path", "", "Sprite texture path", "Appearance")
    prefab.add_property("quantity", "number", 1, "Item quantity", "Basic", min_value=1, max_value=999)
    prefab.add_property("auto_collect", "boolean", True, "Automatically collect on touch", "Behavior")
    prefab.add_property("respawn_time", "number", 0.0, "Respawn time (0 = no respawn)", "Behavior", min_value=0, max_value=300)
    
    # Events
    prefab.add_event("on_collect", "Called when item is collected", [
        VisualScriptInput("collector", "node", description="The collecting node")
    ])
    prefab.add_event("on_respawn", "Called when item respawns")
    
    prefab.tags = ["item", "collectible", "pickup"]
    prefab.created_at = datetime.now().isoformat()
    prefab.modified_at = prefab.created_at
    
    return prefab


def create_chest_prefab():
    """Create Chest prefab"""
    prefab = EnhancedPrefab("Chest", PrefabType.INTERACTIVE)
    prefab.description = "Interactive chest with items"
    prefab.category = "Interactive"
    prefab.icon = "chest.png"
    prefab.base_node_type = "StaticBody2D"
    
    # Properties
    prefab.add_property("chest_name", "string", "Chest", "Name of the chest", "Basic")
    prefab.add_property("sprite_texture", "path", "", "Sprite texture path", "Appearance")
    prefab.add_property("is_locked", "boolean", False, "Whether chest is locked", "Behavior")
    prefab.add_property("key_item", "string", "", "Required key item ID", "Behavior")
    prefab.add_property("contents", "string", "", "Chest contents (JSON)", "Contents")
    prefab.add_property("one_time_use", "boolean", True, "Can only be opened once", "Behavior")
    
    # Events
    prefab.add_event("on_open", "Called when chest is opened", [
        VisualScriptInput("opener", "node", description="The node opening the chest")
    ])
    prefab.add_event("on_locked_attempt", "Called when locked chest is accessed")
    
    prefab.tags = ["chest", "container", "interactive", "loot"]
    prefab.created_at = datetime.now().isoformat()
    prefab.modified_at = prefab.created_at
    
    return prefab


def create_door_prefab():
    """Create Door prefab"""
    prefab = EnhancedPrefab("Door", PrefabType.INTERACTIVE)
    prefab.description = "Interactive door or portal"
    prefab.category = "Interactive"
    prefab.icon = "door.png"
    prefab.base_node_type = "StaticBody2D"
    
    # Properties
    prefab.add_property("door_name", "string", "Door", "Name of the door", "Basic")
    prefab.add_property("sprite_texture", "path", "", "Sprite texture path", "Appearance")
    prefab.add_property("target_scene", "path", "", "Target scene to load", "Teleport")
    prefab.add_property("target_position", "vector2", [0, 0], "Target position in scene", "Teleport")
    prefab.add_property("is_locked", "boolean", False, "Whether door is locked", "Behavior")
    prefab.add_property("key_item", "string", "", "Required key item ID", "Behavior")
    prefab.add_property("auto_open", "boolean", False, "Automatically open on approach", "Behavior")
    
    # Events
    prefab.add_event("on_use", "Called when door is used", [
        VisualScriptInput("user", "node", description="The node using the door")
    ])
    prefab.add_event("on_locked_attempt", "Called when locked door is accessed")
    
    prefab.tags = ["door", "portal", "teleport", "interactive"]
    prefab.created_at = datetime.now().isoformat()
    prefab.modified_at = prefab.created_at
    
    return prefab


def create_sign_prefab():
    """Create Sign prefab"""
    prefab = EnhancedPrefab("Sign", PrefabType.INTERACTIVE)
    prefab.description = "Readable sign with text"
    prefab.category = "Interactive"
    prefab.icon = "sign.png"
    prefab.base_node_type = "StaticBody2D"
    
    # Properties
    prefab.add_property("sign_text", "string", "Sign text here", "Text to display", "Content")
    prefab.add_property("sprite_texture", "path", "", "Sprite texture path", "Appearance")
    prefab.add_property("auto_read", "boolean", False, "Automatically show text on approach", "Behavior")
    
    # Events
    prefab.add_event("on_read", "Called when sign is read", [
        VisualScriptInput("reader", "node", description="The node reading the sign")
    ])
    
    prefab.tags = ["sign", "text", "readable", "interactive"]
    prefab.created_at = datetime.now().isoformat()
    prefab.modified_at = prefab.created_at
    
    return prefab


def create_trigger_zone_prefab():
    """Create Trigger Zone prefab"""
    prefab = EnhancedPrefab("TriggerZone", PrefabType.EVENT)
    prefab.description = "Invisible trigger zone for events"
    prefab.category = "Events"
    prefab.icon = "trigger.png"
    prefab.base_node_type = "Area2D"
    
    # Properties
    prefab.add_property("trigger_name", "string", "Trigger", "Name of the trigger", "Basic")
    prefab.add_property("trigger_size", "vector2", [64, 64], "Size of trigger area", "Area")
    prefab.add_property("one_shot", "boolean", False, "Trigger only once", "Behavior")
    prefab.add_property("player_only", "boolean", True, "Only trigger for player", "Behavior")
    
    # Events
    prefab.add_event("on_trigger_enter", "Called when something enters trigger", [
        VisualScriptInput("body", "node", description="The entering body")
    ])
    prefab.add_event("on_trigger_exit", "Called when something exits trigger", [
        VisualScriptInput("body", "node", description="The exiting body")
    ])
    
    prefab.tags = ["trigger", "event", "zone", "invisible"]
    prefab.created_at = datetime.now().isoformat()
    prefab.modified_at = prefab.created_at
    
    return prefab
