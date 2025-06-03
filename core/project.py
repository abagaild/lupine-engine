"""
Project Management System for Lupine Engine
Handles project creation, loading, and configuration
"""

import json
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path


class LupineProject:
    """Represents a Lupine Engine project"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_file = self.project_path / "project.lupine"
        self.config: Dict[str, Any] = {}
        self.scenes: List[str] = []
        self.main_scene: Optional[str] = None
        
    def create_new_project(self, name: str, description: str = "") -> bool:
        """Create a new project with standard folder structure"""
        try:
            # Create project directory
            self.project_path.mkdir(parents=True, exist_ok=True)
            
            # Create standard folder structure
            folders = [
                "assets",
                "assets/audio",
                "assets/entities",
                "assets/user-interface",
                "assets/environment",
                "assets/misc",
                "data",
                "prefabs",
                "scenes",
                "scripts",
                "nodes",
                "nodes/base",
                "nodes/node2d",
                "nodes/ui",
                "nodes/audio",
                "nodes/prefabs"
            ]

            for folder in folders:
                (self.project_path / folder).mkdir(parents=True, exist_ok=True)

            # Copy node definitions to local project
            self._copy_node_definitions()
            
            # Create project configuration
            self.config = {
                "name": name,
                "description": description,
                "version": "1.0.0",
                "engine_version": "1.0.0",
                "main_scene": "",
                "settings": {
                    "display": {
                        "width": 1024,
                        "height": 768,
                        "fullscreen": False,
                        "resizable": True
                    },
                    "audio": {
                        "master_volume": 1.0,
                        "music_volume": 0.8,
                        "sfx_volume": 1.0
                    },
                    "input": {
                        "deadzone": 0.2
                    }
                },
                "export": {
                    "platforms": ["windows", "linux", "mac"],
                    "icon": "icon.png"
                }
            }
            
            # Save project file
            self.save_project()

            # Copy node definitions to project
            self._copy_node_definitions()

            # Copy prefabs to project
            self._copy_prefabs()

            # Create default main scene
            self.create_default_scene()

            return True
            
        except Exception as e:
            print(f"Error creating project: {e}")
            return False
    
    def create_default_scene(self) -> None:
        """Create a default main scene"""
        scene_content = {
            "name": "Main",
            "nodes": [
                {
                    "name": "Main",
                    "type": "Node2D",
                    "position": [0, 0],
                    "children": []
                }
            ]
        }
        
        scene_path = self.project_path / "scenes" / "Main.scene"
        with open(scene_path, 'w') as f:
            from .json_utils import safe_json_dump
            safe_json_dump(scene_content, f, indent=2)
        
        self.config["main_scene"] = "scenes/Main.scene"
        self.save_project()
    
    def load_project(self) -> bool:
        """Load project from project file"""
        try:
            if not self.project_file.exists():
                return False
                
            with open(self.project_file, 'r') as f:
                self.config = json.load(f)
            
            # Load scene list
            self.load_scenes()
            
            return True
            
        except Exception as e:
            print(f"Error loading project: {e}")
            return False
    
    def save_project(self) -> bool:
        """Save project configuration"""
        try:
            with open(self.project_file, 'w') as f:
                from .json_utils import safe_json_dump
                safe_json_dump(self.config, f, indent=2)
            return True

        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    def load_scenes(self) -> None:
        """Load list of available scenes"""
        scenes_dir = self.project_path / "scenes"
        if scenes_dir.exists():
            self.scenes = [
                str(scene_file.relative_to(self.project_path))
                for scene_file in scenes_dir.glob("*.scene")
            ]
    
    def get_project_name(self) -> str:
        """Get project name"""
        return self.config.get("name", "Untitled Project")
    
    def get_project_description(self) -> str:
        """Get project description"""
        return self.config.get("description", "")

    def _copy_node_definitions(self) -> None:
        """Copy node definitions from engine to local project"""
        try:
            # Get the engine's nodes directory
            engine_root = Path(__file__).parent.parent  # Go up from core/ to engine root
            engine_nodes_dir = engine_root / "nodes"

            if not engine_nodes_dir.exists():
                print(f"Warning: Engine nodes directory not found at {engine_nodes_dir}")
                return

            # Define node categorization based on new directory structure
            node_categories = {
                "base": ["base/Node.py", "base/Node2D.py", "base/Timer.py"],
                "node2d": ["node2d/Sprite.py", "node2d/AnimatedSprite.py", "node2d/Camera2D.py",
                          "node2d/Area2D.py", "node2d/CollisionShape2D.py", "node2d/CollisionPolygon2D.py",
                          "node2d/RigidBody2D.py", "node2d/StaticBody2D.py", "node2d/KinematicBody2D.py"],
                "ui": ["ui/Control.py", "ui/Panel.py", "ui/Label.py", "ui/Button.py", "ui/CanvasLayer.py",
                       "ui/ColorRect.py", "ui/TextureRect.py", "ui/ProgressBar.py",
                       "ui/VBoxContainer.py", "ui/HBoxContainer.py", "ui/CenterContainer.py", "ui/GridContainer.py",
                       "ui/RichTextLabel.py", "ui/PanelContainer.py", "ui/NinePatchRect.py", "ui/ItemList.py",
                       "ui/LineEdit.py", "ui/CheckBox.py", "ui/Slider.py", "ui/ScrollContainer.py",
                       "ui/HSeparator.py", "ui/VSeparator.py"],
                "audio": ["audio/AudioStreamPlayer.py", "audio/AudioStreamPlayer2D.py"],
                "prefabs": []  # Will be populated with any remaining files
            }

            # Copy categorized nodes
            for category, node_files in node_categories.items():
                category_dir = self.project_path / "nodes" / category

                for node_file in node_files:
                    source_file = engine_nodes_dir / node_file
                    if source_file.exists():
                        # Extract just the filename for the destination
                        dest_file = category_dir / Path(node_file).name
                        shutil.copy2(source_file, dest_file)
                        print(f"Copied {Path(node_file).name} to {category}/")
                    else:
                        print(f"Warning: Node file {node_file} not found in engine")

            # Copy any remaining .py files to prefabs
            prefabs_dir = self.project_path / "nodes" / "prefabs"
            for py_file in engine_nodes_dir.glob("*.py"):
                # Check if already copied to another category
                already_copied = False
                for category_files in node_categories.values():
                    if py_file.name in category_files:
                        already_copied = True
                        break

                if not already_copied:
                    dest_file = prefabs_dir / py_file.name
                    shutil.copy2(py_file, dest_file)
                    print(f"Copied {py_file.name} to prefabs/")

        except Exception as e:
            print(f"Error copying node definitions: {e}")

    def _copy_prefabs(self) -> None:
        """Copy prefab definitions from engine to local project"""
        try:
            # Get the engine's prefabs directory
            engine_root = Path(__file__).parent.parent  # Go up from core/ to engine root
            engine_prefabs_dir = engine_root / "prefabs"

            if not engine_prefabs_dir.exists():
                print(f"Warning: Engine prefabs directory not found at {engine_prefabs_dir}")
                return

            # Copy prefab files only to nodes/prefabs (not to main prefabs directory)
            nodes_prefabs_dir = self.project_path / "nodes" / "prefabs"

            for prefab_file in engine_prefabs_dir.glob("*"):
                if prefab_file.is_file():
                    # Copy Python files to nodes/prefabs for node registry
                    if prefab_file.suffix == ".py":
                        nodes_dest_file = nodes_prefabs_dir / prefab_file.name
                        shutil.copy2(prefab_file, nodes_dest_file)
                        print(f"Copied prefab script: {prefab_file.name} to nodes/prefabs/")

                    # Copy other prefab files (JSON, etc.) to nodes/prefabs as well
                    else:
                        nodes_dest_file = nodes_prefabs_dir / prefab_file.name
                        shutil.copy2(prefab_file, nodes_dest_file)
                        print(f"Copied prefab: {prefab_file.name} to nodes/prefabs/")

        except Exception as e:
            print(f"Error copying prefabs: {e}")

    def get_main_scene(self) -> Optional[str]:
        """Get main scene path"""
        return self.config.get("main_scene")
    
    def set_main_scene(self, scene_path: str) -> None:
        """Set main scene"""
        self.config["main_scene"] = scene_path
        self.save_project()
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """Get absolute path from project-relative path"""
        return self.project_path / relative_path
    
    def get_relative_path(self, absolute_path: str) -> str:
        """Get project-relative path from absolute path"""
        abs_path = Path(absolute_path)
        try:
            return str(abs_path.relative_to(self.project_path))
        except ValueError:
            return str(abs_path)


class ProjectManager:
    """Manages multiple projects and recent projects list"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".lupine_engine"
        self.config_file = self.config_dir / "config.json"
        self.recent_projects: List[str] = []
        self.load_config()
    
    def load_config(self) -> None:
        """Load global configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.recent_projects = config.get("recent_projects", [])
        except Exception as e:
            print(f"Error loading config: {e}")
            self.recent_projects = []
    
    def save_config(self) -> None:
        """Save global configuration"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            config = {
                "recent_projects": self.recent_projects
            }
            with open(self.config_file, 'w') as f:
                from .json_utils import safe_json_dump
                safe_json_dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def add_recent_project(self, project_path: str) -> None:
        """Add project to recent projects list"""
        project_path = str(Path(project_path).resolve())
        
        # Remove if already in list
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
        
        # Add to beginning
        self.recent_projects.insert(0, project_path)
        
        # Keep only last 10 projects
        self.recent_projects = self.recent_projects[:10]
        
        self.save_config()
    
    def get_recent_projects(self) -> List[Dict[str, str]]:
        """Get list of recent projects with metadata"""
        projects = []
        for project_path in self.recent_projects:
            path = Path(project_path)
            if path.exists() and (path / "project.lupine").exists():
                project = LupineProject(project_path)
                if project.load_project():
                    projects.append({
                        "name": project.get_project_name(),
                        "path": project_path,
                        "description": project.get_project_description()
                    })
        return projects
    
    def remove_recent_project(self, project_path: str) -> None:
        """Remove project from recent projects list"""
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
            self.save_config()
