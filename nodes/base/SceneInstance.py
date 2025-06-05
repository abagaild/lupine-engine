"""
Scene Instance Node for Lupine Engine
Represents an instance of another scene that can be embedded in the current scene
"""

from core.scene.scene_instance import SceneInstance as BaseSceneInstance
from typing import Dict, Any


class SceneInstance(BaseSceneInstance):
    """
    A node that represents an instance of another scene.
    This allows embedding scenes within other scenes, similar to Godot's scene instancing.
    
    Features:
    - Reference to external scene file
    - Property overrides for customizing instances
    - Automatic reloading when source scene changes
    - Circular dependency detection
    - Instance breaking (convert to regular nodes)
    """
    
    def __init__(self, name: str = "SceneInstance"):
        super().__init__(name)
        
        # Additional export variables for the editor
        self.export_variables.update({
            "scene_path": {
                "type": "path",
                "value": "",
                "description": "Path to the scene file to instance",
                "filter": "*.scene"
            },
            "editable_children": {
                "type": "bool",
                "value": False,
                "description": "Allow editing children of this scene instance"
            },
            "auto_reload": {
                "type": "bool",
                "value": True,
                "description": "Automatically reload when source scene changes"
            }
        })
        
        # Additional properties
        self.auto_reload: bool = True

    def _ready(self):
        """Called when the node enters the scene tree."""
        super()._ready()
        
        # Load the scene if path is set
        if self.scene_path and not self.children:
            self.load_scene()

    def load_scene(self) -> bool:
        """Load the referenced scene and add its nodes as children."""
        if not self.scene_path:
            return False
        
        # Get scene manager from the project
        try:
            from core.project import get_current_project
            project = get_current_project()
            if not project:
                print("Warning: No current project available for scene loading")
                return False
            
            scene_manager = project.scene_manager
            if not scene_manager:
                print("Warning: No scene manager available")
                return False
            
            # Clear existing children
            self.children.clear()
            
            # Load and instantiate the scene
            scene = scene_manager.load_scene(self.scene_path)
            if not scene:
                print(f"Warning: Could not load scene {self.scene_path}")
                return False
            
            self.original_scene = scene
            
            # Clone the scene's root nodes as children
            for root_node in scene.root_nodes:
                cloned_node = scene_manager._clone_node_tree(root_node)
                self.add_child(cloned_node)
            
            # Apply property overrides
            self.apply_property_overrides()
            
            return True
            
        except Exception as e:
            print(f"Error loading scene {self.scene_path}: {e}")
            return False

    def reload_scene(self) -> bool:
        """Reload the scene from file."""
        return self.load_scene()

    def set_scene_file(self, scene_path: str) -> None:
        """Set the scene file path and load it."""
        self.scene_path = scene_path
        self.export_variables["scene_path"]["value"] = scene_path
        # Also update the base class method
        self.set_scene_path(scene_path)

        # Only try to load if we have a current project and scene manager
        if scene_path:
            try:
                from core.project import get_current_project
                project = get_current_project()
                if project and project.scene_manager:
                    self.load_scene()
                else:
                    print(f"Scene path set to '{scene_path}' but no project/scene manager available for loading")
            except Exception as e:
                print(f"Error setting scene file '{scene_path}': {e}")

    def get_scene_file(self) -> str:
        """Get the current scene file path."""
        return self.scene_path

    def can_edit_children(self) -> bool:
        """Check if children of this instance can be edited."""
        return self.editable_children

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation with proper property sync."""
        # Ensure export variables are synced with actual values
        self.export_variables["scene_path"]["value"] = self.scene_path
        self.export_variables["editable_children"]["value"] = self.editable_children
        self.export_variables["auto_reload"]["value"] = self.auto_reload

        # Call parent to_dict
        data = super().to_dict()

        # Add our specific properties
        data.update({
            "auto_reload": self.auto_reload
        })

        return data

    def set_editable_children(self, editable: bool) -> None:
        """Set whether children can be edited."""
        self.editable_children = editable
        self.export_variables["editable_children"]["value"] = editable

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneInstance":
        """Create SceneInstance from dictionary data."""
        # Create instance using this class, not the parent
        instance = cls(data.get("name", "SceneInstance"))

        # Apply base node properties
        cls._apply_node_properties(instance, data)

        # Apply scene instance specific properties from parent class
        instance.scene_path = data.get("scene_path", "")
        instance.instance_id = data.get("instance_id", str(__import__('uuid').uuid4()))
        instance.property_overrides = data.get("property_overrides", {})
        instance.editable_children = data.get("editable_children", False)
        instance.auto_reload = data.get("auto_reload", True)

        # Update export variables
        instance.export_variables["scene_path"]["value"] = instance.scene_path
        instance.export_variables["editable_children"]["value"] = instance.editable_children
        instance.export_variables["auto_reload"]["value"] = instance.auto_reload

        return instance

    def get_display_name(self) -> str:
        """Get display name for the editor."""
        if self.scene_path:
            scene_name = self.scene_path.split("/")[-1].replace(".scene", "")
            return f"{self.name} ({scene_name})"
        return f"{self.name} (No Scene)"

    def get_icon_name(self) -> str:
        """Get icon name for the editor."""
        return "scene_instance"

    def __repr__(self) -> str:
        return f"SceneInstance(name='{self.name}', scene_path='{self.scene_path}')"
