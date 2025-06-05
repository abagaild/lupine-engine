"""
Prefab Manager for Lupine Engine
Manages loading, saving, and organizing prefabs
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

from .prefab_system import EnhancedPrefab, PrefabType, VisualScriptBlock, VisualScriptBlockType
from .builtin_prefabs import create_builtin_prefabs
from .builtin_script_blocks import create_builtin_script_blocks


class PrefabManager:
    """Manages all prefabs in a project"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.prefabs_dir = self.project_path / "prefabs"
        self.script_blocks_dir = self.project_path / "data" / "script_blocks"
        
        # Ensure directories exist
        self.prefabs_dir.mkdir(parents=True, exist_ok=True)
        self.script_blocks_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage
        self.prefabs: Dict[str, EnhancedPrefab] = {}  # id -> prefab
        self.prefabs_by_name: Dict[str, EnhancedPrefab] = {}  # name -> prefab
        self.prefabs_by_category: Dict[str, List[EnhancedPrefab]] = {}
        self.script_blocks: Dict[str, VisualScriptBlock] = {}  # id -> block
        self.script_blocks_by_category: Dict[str, List[VisualScriptBlock]] = {}
        
        # Load existing prefabs and script blocks
        self.load_all_prefabs()
        self.load_all_script_blocks()
        
        # Create builtin prefabs and script blocks if they don't exist
        self.ensure_builtin_content()
    
    def ensure_builtin_content(self):
        """Ensure builtin prefabs and script blocks exist"""
        # Create builtin prefabs
        builtin_prefabs = create_builtin_prefabs()
        for prefab in builtin_prefabs:
            if prefab.name not in self.prefabs_by_name:
                self.add_prefab(prefab)
                self.save_prefab(prefab)
        
        # Create builtin script blocks
        builtin_blocks = create_builtin_script_blocks()
        for block in builtin_blocks:
            if block.id not in self.script_blocks:
                self.add_script_block(block)
                self.save_script_block(block)
    
    def load_all_prefabs(self):
        """Load all prefabs from the prefabs directory"""
        if not self.prefabs_dir.exists():
            return
        
        for prefab_file in self.prefabs_dir.glob("*.prefab"):
            try:
                prefab = EnhancedPrefab.load_from_file(str(prefab_file))
                self.add_prefab(prefab)
            except Exception as e:
                print(f"Error loading prefab {prefab_file}: {e}")
    
    def load_all_script_blocks(self):
        """Load all script blocks from the script blocks directory"""
        if not self.script_blocks_dir.exists():
            return
        
        for block_file in self.script_blocks_dir.glob("*.block"):
            try:
                with open(block_file, 'r', encoding='utf-8') as f:
                    block_data = json.load(f)
                
                block = VisualScriptBlock(
                    id=block_data["id"],
                    name=block_data["name"],
                    category=block_data["category"],
                    block_type=VisualScriptBlockType(block_data["block_type"]),
                    description=block_data.get("description", ""),
                    inputs=[],  # Will be loaded below
                    outputs=[],  # Will be loaded below
                    code_template=block_data.get("code_template", ""),
                    icon=block_data.get("icon", ""),
                    color=block_data.get("color", "#4A90E2")
                )
                
                # Load inputs and outputs (simplified for now)
                # In a full implementation, these would be properly deserialized
                
                self.add_script_block(block)
            except Exception as e:
                print(f"Error loading script block {block_file}: {e}")
    
    def add_prefab(self, prefab: EnhancedPrefab):
        """Add a prefab to the manager"""
        self.prefabs[prefab.id] = prefab
        self.prefabs_by_name[prefab.name] = prefab
        
        # Add to category
        if prefab.category not in self.prefabs_by_category:
            self.prefabs_by_category[prefab.category] = []
        self.prefabs_by_category[prefab.category].append(prefab)
    
    def add_script_block(self, block: VisualScriptBlock):
        """Add a script block to the manager"""
        self.script_blocks[block.id] = block
        
        # Add to category
        if block.category not in self.script_blocks_by_category:
            self.script_blocks_by_category[block.category] = []
        self.script_blocks_by_category[block.category].append(block)
    
    def remove_prefab(self, prefab_id: str) -> bool:
        """Remove a prefab"""
        if prefab_id not in self.prefabs:
            return False
        
        prefab = self.prefabs[prefab_id]
        
        # Remove from all collections
        del self.prefabs[prefab_id]
        if prefab.name in self.prefabs_by_name:
            del self.prefabs_by_name[prefab.name]
        
        if prefab.category in self.prefabs_by_category:
            self.prefabs_by_category[prefab.category] = [
                p for p in self.prefabs_by_category[prefab.category] 
                if p.id != prefab_id
            ]
        
        # Remove file
        prefab_file = self.prefabs_dir / f"{prefab.name}.prefab"
        if prefab_file.exists():
            prefab_file.unlink()
        
        return True
    
    def remove_script_block(self, block_id: str) -> bool:
        """Remove a script block"""
        if block_id not in self.script_blocks:
            return False
        
        block = self.script_blocks[block_id]
        
        # Remove from all collections
        del self.script_blocks[block_id]
        
        if block.category in self.script_blocks_by_category:
            self.script_blocks_by_category[block.category] = [
                b for b in self.script_blocks_by_category[block.category] 
                if b.id != block_id
            ]
        
        # Remove file
        block_file = self.script_blocks_dir / f"{block.name}.block"
        if block_file.exists():
            block_file.unlink()
        
        return True
    
    def save_prefab(self, prefab: EnhancedPrefab):
        """Save a prefab to file"""
        prefab.modified_at = datetime.now().isoformat()
        prefab_file = self.prefabs_dir / f"{prefab.name}.prefab"
        prefab.save_to_file(str(prefab_file))
    
    def save_script_block(self, block: VisualScriptBlock):
        """Save a script block to file"""
        block_file = self.script_blocks_dir / f"{block.name}.block"
        
        block_data = {
            "id": block.id,
            "name": block.name,
            "category": block.category,
            "block_type": block.block_type.value,
            "description": block.description,
            "inputs": [
                {
                    "name": inp.name,
                    "type": inp.type,
                    "default_value": inp.default_value,
                    "description": inp.description,
                    "required": inp.required,
                    "options": inp.options
                }
                for inp in block.inputs
            ],
            "outputs": [
                {
                    "name": out.name,
                    "type": out.type,
                    "description": out.description
                }
                for out in block.outputs
            ],
            "code_template": block.code_template,
            "icon": block.icon,
            "color": block.color
        }
        
        with open(block_file, 'w', encoding='utf-8') as f:
            json.dump(block_data, f, indent=2)
    
    def get_prefab_by_id(self, prefab_id: str) -> Optional[EnhancedPrefab]:
        """Get prefab by ID"""
        return self.prefabs.get(prefab_id)
    
    def get_prefab_by_name(self, name: str) -> Optional[EnhancedPrefab]:
        """Get prefab by name"""
        return self.prefabs_by_name.get(name)
    
    def get_prefabs_by_category(self, category: str) -> List[EnhancedPrefab]:
        """Get all prefabs in a category"""
        return self.prefabs_by_category.get(category, [])
    
    def get_prefabs_by_type(self, prefab_type: PrefabType) -> List[EnhancedPrefab]:
        """Get all prefabs of a specific type"""
        return [prefab for prefab in self.prefabs.values() if prefab.prefab_type == prefab_type]
    
    def get_script_block_by_id(self, block_id: str) -> Optional[VisualScriptBlock]:
        """Get script block by ID"""
        return self.script_blocks.get(block_id)
    
    def get_script_blocks_by_category(self, category: str) -> List[VisualScriptBlock]:
        """Get all script blocks in a category"""
        return self.script_blocks_by_category.get(category, [])
    
    def get_script_blocks_by_type(self, block_type: VisualScriptBlockType) -> List[VisualScriptBlock]:
        """Get all script blocks of a specific type"""
        return [block for block in self.script_blocks.values() if block.block_type == block_type]
    
    def search_prefabs(self, query: str) -> List[EnhancedPrefab]:
        """Search prefabs by name, description, or tags"""
        query = query.lower()
        results = []
        
        for prefab in self.prefabs.values():
            if (query in prefab.name.lower() or 
                query in prefab.description.lower() or
                any(query in tag.lower() for tag in prefab.tags)):
                results.append(prefab)
        
        return results
    
    def search_script_blocks(self, query: str) -> List[VisualScriptBlock]:
        """Search script blocks by name or description"""
        query = query.lower()
        results = []
        
        for block in self.script_blocks.values():
            if (query in block.name.lower() or 
                query in block.description.lower()):
                results.append(block)
        
        return results
    
    def get_all_categories(self) -> Set[str]:
        """Get all prefab categories"""
        return set(self.prefabs_by_category.keys())
    
    def get_all_script_block_categories(self) -> Set[str]:
        """Get all script block categories"""
        return set(self.script_blocks_by_category.keys())
    
    def create_prefab_instance(self, prefab_id: str, instance_name: Optional[str] = None,
                             property_overrides: Optional[Dict[str, any]] = None) -> Optional[Dict[str, any]]:
        """Create an instance of a prefab"""
        prefab = self.get_prefab_by_id(prefab_id)
        if not prefab:
            return None
        
        return prefab.create_instance(instance_name, property_overrides)
    
    def duplicate_prefab(self, prefab_id: str, new_name: str) -> Optional[EnhancedPrefab]:
        """Duplicate an existing prefab"""
        original = self.get_prefab_by_id(prefab_id)
        if not original:
            return None
        
        # Create a copy
        prefab_data = original.to_dict()
        prefab_data["name"] = new_name
        prefab_data["id"] = None  # Will generate new ID
        
        new_prefab = EnhancedPrefab.from_dict(prefab_data)
        new_prefab.created_at = datetime.now().isoformat()
        new_prefab.modified_at = new_prefab.created_at
        
        self.add_prefab(new_prefab)
        self.save_prefab(new_prefab)
        
        return new_prefab
    
    def export_prefab(self, prefab_id: str, export_path: str) -> bool:
        """Export a prefab to a file"""
        prefab = self.get_prefab_by_id(prefab_id)
        if not prefab:
            return False
        
        try:
            prefab.save_to_file(export_path)
            return True
        except Exception as e:
            print(f"Error exporting prefab: {e}")
            return False
    
    def import_prefab(self, import_path: str) -> Optional[EnhancedPrefab]:
        """Import a prefab from a file"""
        try:
            prefab = EnhancedPrefab.load_from_file(import_path)
            
            # Check for name conflicts
            if prefab.name in self.prefabs_by_name:
                # Generate unique name
                base_name = prefab.name
                counter = 1
                while f"{base_name}_{counter}" in self.prefabs_by_name:
                    counter += 1
                prefab.name = f"{base_name}_{counter}"
            
            self.add_prefab(prefab)
            self.save_prefab(prefab)
            
            return prefab
        except Exception as e:
            print(f"Error importing prefab: {e}")
            return None
