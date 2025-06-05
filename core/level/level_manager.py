"""
Level Manager for Lupine Engine
Manages loading, saving, and organizing levels
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .level_system import Level, LevelEvent, LevelLayer, EventTrigger, EventCondition


class LevelManager:
    """Manages all levels in a project"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.levels_dir = self.project_path / "levels"
        
        # Ensure directory exists
        self.levels_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage
        self.levels: Dict[str, Level] = {}  # id -> level
        self.levels_by_name: Dict[str, Level] = {}  # name -> level
        
        # Load existing levels
        self.load_all_levels()
    
    def load_all_levels(self):
        """Load all levels from the levels directory"""
        if not self.levels_dir.exists():
            return
        
        for level_file in self.levels_dir.glob("*.level"):
            try:
                level = Level.load_from_file(str(level_file))
                self.add_level(level)
            except Exception as e:
                print(f"Error loading level {level_file}: {e}")
    
    def add_level(self, level: Level):
        """Add a level to the manager"""
        self.levels[level.id] = level
        self.levels_by_name[level.name] = level
    
    def remove_level(self, level_id: str) -> bool:
        """Remove a level"""
        if level_id not in self.levels:
            return False
        
        level = self.levels[level_id]
        
        # Remove from collections
        del self.levels[level_id]
        if level.name in self.levels_by_name:
            del self.levels_by_name[level.name]
        
        # Remove file
        level_file = self.levels_dir / f"{level.name}.level"
        if level_file.exists():
            level_file.unlink()
        
        return True
    
    def save_level(self, level: Level):
        """Save a level to file"""
        level.modified_at = datetime.now().isoformat()
        level_file = self.levels_dir / f"{level.name}.level"
        level.save_to_file(str(level_file))
    
    def get_level_by_id(self, level_id: str) -> Optional[Level]:
        """Get level by ID"""
        return self.levels.get(level_id)
    
    def get_level_by_name(self, name: str) -> Optional[Level]:
        """Get level by name"""
        return self.levels_by_name.get(name)
    
    def create_level(self, name: str, width: int = 20, height: int = 15) -> Level:
        """Create a new level"""
        if name in self.levels_by_name:
            raise ValueError(f"Level '{name}' already exists")
        
        level = Level(name, width, height)
        level.created_at = datetime.now().isoformat()
        level.modified_at = level.created_at
        
        self.add_level(level)
        self.save_level(level)
        
        return level
    
    def duplicate_level(self, level_id: str, new_name: str) -> Optional[Level]:
        """Duplicate an existing level"""
        original = self.get_level_by_id(level_id)
        if not original:
            return None
        
        if new_name in self.levels_by_name:
            raise ValueError(f"Level '{new_name}' already exists")
        
        # Create a copy
        level_data = original.to_dict()
        level_data["name"] = new_name
        level_data["id"] = None  # Will generate new ID
        
        new_level = Level.from_dict(level_data)
        new_level.created_at = datetime.now().isoformat()
        new_level.modified_at = new_level.created_at
        
        self.add_level(new_level)
        self.save_level(new_level)
        
        return new_level
    
    def search_levels(self, query: str) -> List[Level]:
        """Search levels by name, description, or tags"""
        query = query.lower()
        results = []
        
        for level in self.levels.values():
            if (query in level.name.lower() or 
                query in level.description.lower() or
                any(query in tag.lower() for tag in level.tags)):
                results.append(level)
        
        return results
    
    def get_all_levels(self) -> List[Level]:
        """Get all levels"""
        return list(self.levels.values())
    
    def export_level(self, level_id: str, export_path: str) -> bool:
        """Export a level to a file"""
        level = self.get_level_by_id(level_id)
        if not level:
            return False
        
        try:
            level.save_to_file(export_path)
            return True
        except Exception as e:
            print(f"Error exporting level: {e}")
            return False
    
    def import_level(self, import_path: str) -> Optional[Level]:
        """Import a level from a file"""
        try:
            level = Level.load_from_file(import_path)
            
            # Check for name conflicts
            if level.name in self.levels_by_name:
                # Generate unique name
                base_name = level.name
                counter = 1
                while f"{base_name}_{counter}" in self.levels_by_name:
                    counter += 1
                level.name = f"{base_name}_{counter}"
            
            self.add_level(level)
            self.save_level(level)
            
            return level
        except Exception as e:
            print(f"Error importing level: {e}")
            return None
    
    def create_event_template(self, name: str, trigger: EventTrigger = EventTrigger.PLAYER_INTERACT) -> LevelEvent:
        """Create a template event"""
        import uuid
        
        event = LevelEvent(
            id=str(uuid.uuid4()),
            name=name,
            position=(0, 0),
            trigger=trigger
        )
        
        # Set default script based on trigger type
        if trigger == EventTrigger.PLAYER_INTERACT:
            event.raw_script = '''# Player interaction event
def on_interact(player):
    print("Hello, player!")
'''
        elif trigger == EventTrigger.PLAYER_TOUCH:
            event.raw_script = '''# Player touch event
def on_touch(player):
    print("Player touched this event!")
'''
        elif trigger == EventTrigger.AUTO_RUN:
            event.raw_script = '''# Auto-run event
def on_auto_run():
    print("Auto-run event triggered!")
'''
        elif trigger == EventTrigger.PARALLEL:
            event.raw_script = '''# Parallel event
def on_parallel():
    # This runs continuously
    pass
'''
        
        return event
    
    def validate_level(self, level: Level) -> List[str]:
        """Validate a level and return list of issues"""
        issues = []
        
        # Check basic properties
        if not level.name:
            issues.append("Level name is empty")
        
        if level.width <= 0 or level.height <= 0:
            issues.append("Level dimensions must be positive")
        
        if not level.layers:
            issues.append("Level has no layers")
        
        # Check events
        for layer in level.layers:
            for event in layer.events:
                # Check event position
                ex, ey = event.position
                if ex < 0 or ey < 0 or ex >= level.width or ey >= level.height:
                    issues.append(f"Event '{event.name}' is outside level bounds")
                
                # Check event size
                ew, eh = event.size
                if ew <= 0 or eh <= 0:
                    issues.append(f"Event '{event.name}' has invalid size")
                
                # Check for overlapping non-through events
                if not event.through:
                    overlapping = level.get_events_at_position(ex, ey)
                    non_through_overlapping = [e for e in overlapping if not e.through and e.id != event.id]
                    if non_through_overlapping:
                        issues.append(f"Event '{event.name}' overlaps with other non-through events")
        
        return issues
    
    def get_level_statistics(self, level: Level) -> Dict[str, Any]:
        """Get statistics about a level"""
        stats = {
            "name": level.name,
            "dimensions": f"{level.width}x{level.height}",
            "cell_size": level.cell_size,
            "total_cells": level.width * level.height,
            "layer_count": len(level.layers),
            "total_events": sum(len(layer.events) for layer in level.layers),
            "events_by_trigger": {},
            "events_by_layer": {}
        }
        
        # Count events by trigger type
        for layer in level.layers:
            stats["events_by_layer"][layer.name] = len(layer.events)
            
            for event in layer.events:
                trigger_name = event.trigger.value
                if trigger_name not in stats["events_by_trigger"]:
                    stats["events_by_trigger"][trigger_name] = 0
                stats["events_by_trigger"][trigger_name] += 1
        
        return stats
    
    def optimize_level(self, level: Level):
        """Optimize a level by removing unused data and compacting"""
        # Remove empty layers
        level.layers = [layer for layer in level.layers if layer.events or layer.tilemap_data]
        
        # Ensure we have at least one layer
        if not level.layers:
            level.create_default_layer()
        
        # Update active layer if it was removed
        if level.active_layer_id and not level.get_layer_by_id(level.active_layer_id):
            level.active_layer_id = level.layers[0].id if level.layers else None
        
        # Remove duplicate events (same position, same properties)
        for layer in level.layers:
            unique_events = []
            seen_positions = set()
            
            for event in layer.events:
                pos_key = (event.position, event.name, event.trigger.value)
                if pos_key not in seen_positions:
                    unique_events.append(event)
                    seen_positions.add(pos_key)
            
            layer.events = unique_events
    
    def backup_level(self, level_id: str) -> bool:
        """Create a backup of a level"""
        level = self.get_level_by_id(level_id)
        if not level:
            return False
        
        backup_dir = self.levels_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{level.name}_{timestamp}.level"
        
        try:
            level.save_to_file(str(backup_file))
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
