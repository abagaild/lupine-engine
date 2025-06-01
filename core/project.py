"""
Project Management System for Lupine Engine
Handles project creation, loading, and configuration
"""

import os
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
                "scripts"
            ]
            
            for folder in folders:
                (self.project_path / folder).mkdir(parents=True, exist_ok=True)
            
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
            json.dump(scene_content, f, indent=2)
        
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
                json.dump(self.config, f, indent=2)
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
                json.dump(config, f, indent=2)
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
