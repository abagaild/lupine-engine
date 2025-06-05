"""
Asset Resolver for Dialogue System
Handles resolution of asset paths for backgrounds, music, sound effects, and portraits
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from core.project import LupineProject


class DialogueAssetResolver:
    """Resolves asset paths for dialogue system with fallback support"""
    
    def __init__(self, project: LupineProject):
        self.project = project
        self.project_path = Path(project.project_path)
        
        # Default asset directories
        self.asset_dirs = {
            'backgrounds': self.project_path / 'assets' / 'backgrounds',
            'music': self.project_path / 'assets' / 'music',
            'sound_effects': self.project_path / 'assets' / 'soundEffects',
            'portraits': self.project_path / 'assets' / 'portraits'
        }
        
        # Supported file extensions
        self.extensions = {
            'backgrounds': ['.png', '.jpg', '.jpeg', '.bmp', '.tga'],
            'music': ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac'],
            'sound_effects': ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac'],
            'portraits': ['.png', '.jpg', '.jpeg', '.bmp', '.tga']
        }
        
        # Cache for resolved paths
        self._path_cache: Dict[str, Optional[str]] = {}
    
    def resolve_background(self, background_name: str) -> Optional[str]:
        """Resolve background asset path"""
        return self._resolve_asset('backgrounds', background_name)
    
    def resolve_music(self, music_name: str) -> Optional[str]:
        """Resolve music asset path"""
        return self._resolve_asset('music', music_name)
    
    def resolve_sound_effect(self, sound_name: str) -> Optional[str]:
        """Resolve sound effect asset path"""
        return self._resolve_asset('sound_effects', sound_name)
    
    def resolve_portrait(self, character_name: str, emotion: str = None) -> Optional[str]:
        """
        Resolve portrait asset path with emotion support and fallback to neutral
        
        Args:
            character_name: Name of the character
            emotion: Emotion state (optional)
            
        Returns:
            Resolved path or None if not found
        """
        # Try with emotion first if provided
        if emotion and emotion.lower() != 'neutral':
            portrait_name = f"{character_name}_{emotion}"
            path = self._resolve_asset('portraits', portrait_name, character_name)
            if path:
                return path
        
        # Fallback to neutral or base character name
        neutral_name = f"{character_name}_neutral"
        path = self._resolve_asset('portraits', neutral_name, character_name)
        if path:
            return path
            
        # Final fallback to just character name
        return self._resolve_asset('portraits', character_name, character_name)
    
    def _resolve_asset(self, asset_type: str, asset_name: str, cache_key: str = None) -> Optional[str]:
        """
        Resolve asset path with caching
        
        Args:
            asset_type: Type of asset (backgrounds, music, etc.)
            asset_name: Name of the asset
            cache_key: Key for caching (defaults to asset_name)
            
        Returns:
            Resolved relative path or None if not found
        """
        cache_key = cache_key or asset_name
        cache_full_key = f"{asset_type}:{cache_key}"
        
        # Check cache first
        if cache_full_key in self._path_cache:
            return self._path_cache[cache_full_key]
        
        # Check if it's already a path (contains / or \)
        if '/' in asset_name or '\\' in asset_name:
            # Treat as direct path
            full_path = self.project_path / asset_name
            if full_path.exists():
                relative_path = str(Path(asset_name))
                self._path_cache[cache_full_key] = relative_path
                return relative_path
        
        # Search in default directory
        asset_dir = self.asset_dirs.get(asset_type)
        if not asset_dir or not asset_dir.exists():
            self._path_cache[cache_full_key] = None
            return None
        
        # Try different extensions
        extensions = self.extensions.get(asset_type, [])
        
        for ext in extensions:
            # Try exact name with extension
            file_path = asset_dir / f"{asset_name}{ext}"
            if file_path.exists():
                relative_path = str(file_path.relative_to(self.project_path))
                self._path_cache[cache_full_key] = relative_path
                return relative_path
        
        # Try case-insensitive search
        if asset_dir.exists():
            for file_path in asset_dir.iterdir():
                if file_path.is_file():
                    name_without_ext = file_path.stem.lower()
                    if name_without_ext == asset_name.lower():
                        relative_path = str(file_path.relative_to(self.project_path))
                        self._path_cache[cache_full_key] = relative_path
                        return relative_path
        
        # Search in character subdirectories for portraits
        if asset_type == 'portraits':
            for subdir in asset_dir.iterdir():
                if subdir.is_dir():
                    for ext in extensions:
                        file_path = subdir / f"{asset_name}{ext}"
                        if file_path.exists():
                            relative_path = str(file_path.relative_to(self.project_path))
                            self._path_cache[cache_full_key] = relative_path
                            return relative_path
        
        # Not found
        self._path_cache[cache_full_key] = None
        return None
    
    def get_available_backgrounds(self) -> List[str]:
        """Get list of available background assets"""
        return self._get_available_assets('backgrounds')
    
    def get_available_music(self) -> List[str]:
        """Get list of available music assets"""
        return self._get_available_assets('music')
    
    def get_available_sound_effects(self) -> List[str]:
        """Get list of available sound effect assets"""
        return self._get_available_assets('sound_effects')
    
    def get_available_portraits(self) -> Dict[str, List[str]]:
        """Get list of available portraits organized by character"""
        portraits_dir = self.asset_dirs['portraits']
        if not portraits_dir.exists():
            return {}
        
        portraits = {}
        extensions = self.extensions['portraits']
        
        # Scan for portrait files
        for file_path in portraits_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                name = file_path.stem
                
                # Parse character name and emotion
                if '_' in name:
                    character, emotion = name.split('_', 1)
                else:
                    character = name
                    emotion = 'neutral'
                
                if character not in portraits:
                    portraits[character] = []
                
                if emotion not in portraits[character]:
                    portraits[character].append(emotion)
        
        return portraits
    
    def _get_available_assets(self, asset_type: str) -> List[str]:
        """Get list of available assets for a given type"""
        asset_dir = self.asset_dirs.get(asset_type)
        if not asset_dir or not asset_dir.exists():
            return []
        
        assets = []
        extensions = self.extensions.get(asset_type, [])
        
        for file_path in asset_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                # Use stem (filename without extension) as asset name
                assets.append(file_path.stem)
        
        return sorted(list(set(assets)))
    
    def clear_cache(self):
        """Clear the asset path cache"""
        self._path_cache.clear()
    
    def validate_asset_directories(self) -> Dict[str, bool]:
        """Validate that asset directories exist"""
        return {
            asset_type: asset_dir.exists()
            for asset_type, asset_dir in self.asset_dirs.items()
        }
    
    def create_asset_directories(self):
        """Create missing asset directories"""
        for asset_dir in self.asset_dirs.values():
            asset_dir.mkdir(parents=True, exist_ok=True)
