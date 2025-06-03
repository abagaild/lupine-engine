"""
LSC Inheritance System
Manages class inheritance, method resolution, and super() calls
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from .runtime import LSCScope


class LSCClass:
    """Represents a class in the LSC inheritance system"""
    
    def __init__(self, name: str, base_class: Optional['LSCClass'] = None):
        self.name = name
        self.base_class = base_class
        self.methods: Dict[str, Any] = {}
        self.properties: Dict[str, Any] = {}
        self.script_path: Optional[str] = None
        self.scope: Optional[LSCScope] = None
        
    def add_method(self, name: str, method: Any) -> None:
        """Add a method to this class"""
        self.methods[name] = method
        
    def add_property(self, name: str, value: Any) -> None:
        """Add a property to this class"""
        self.properties[name] = value
        
    def get_method(self, name: str) -> Optional[Any]:
        """Get a method, checking inheritance chain"""
        if name in self.methods:
            return self.methods[name]
        elif self.base_class:
            return self.base_class.get_method(name)
        return None
        
    def get_property(self, name: str) -> Optional[Any]:
        """Get a property, checking inheritance chain"""
        if name in self.properties:
            return self.properties[name]
        elif self.base_class:
            return self.base_class.get_property(name)
        return None
        
    def has_method(self, name: str) -> bool:
        """Check if method exists in inheritance chain"""
        return self.get_method(name) is not None
        
    def has_property(self, name: str) -> bool:
        """Check if property exists in inheritance chain"""
        return self.get_property(name) is not None
        
    def get_all_methods(self) -> Dict[str, Any]:
        """Get all methods from inheritance chain"""
        all_methods = {}
        if self.base_class:
            all_methods.update(self.base_class.get_all_methods())
        all_methods.update(self.methods)
        return all_methods
        
    def get_all_properties(self) -> Dict[str, Any]:
        """Get all properties from inheritance chain"""
        all_properties = {}
        if self.base_class:
            all_properties.update(self.base_class.get_all_properties())
        all_properties.update(self.properties)
        return all_properties


class LSCInheritanceManager:
    """Manages class inheritance and script loading"""
    
    def __init__(self, runtime):
        self.runtime = runtime
        self.classes: Dict[str, LSCClass] = {}
        self.script_cache: Dict[str, str] = {}  # Cache for loaded scripts
        self.project_path: Optional[Path] = None
        
        # Initialize built-in classes
        self._initialize_builtin_classes()
        
    def set_project_path(self, path: Path) -> None:
        """Set the project path for script resolution"""
        self.project_path = path
        
    def _initialize_builtin_classes(self) -> None:
        """Initialize built-in node classes"""
        # Create base Node class
        node_class = LSCClass("Node")
        self.classes["Node"] = node_class
        
        # Create Node2D class extending Node
        node2d_class = LSCClass("Node2D", node_class)
        self.classes["Node2D"] = node2d_class
        
        # Create Control class extending Node
        control_class = LSCClass("Control", node_class)
        self.classes["Control"] = control_class
        
        # Create physics body classes extending Node2D
        for body_type in ["KinematicBody2D", "RigidBody2D", "StaticBody2D", "Area2D"]:
            body_class = LSCClass(body_type, node2d_class)
            self.classes[body_type] = body_class
            
        # Create other common classes
        sprite_class = LSCClass("Sprite", node2d_class)
        self.classes["Sprite"] = sprite_class
        
        animated_sprite_class = LSCClass("AnimatedSprite", node2d_class)
        self.classes["AnimatedSprite"] = animated_sprite_class
        
        camera_class = LSCClass("Camera2D", node2d_class)
        self.classes["Camera2D"] = camera_class
        
    def find_script_path(self, class_name: str) -> Optional[str]:
        """Find the script file for a given class name"""
        if not self.project_path:
            return None
            
        # Check in various node directories
        search_dirs = ["nodes/base", "nodes/node2d", "nodes/ui", "nodes/audio", "nodes/prefabs"]
        
        for search_dir in search_dirs:
            script_path = self.project_path / search_dir / f"{class_name}.lsc"
            if script_path.exists():
                return str(script_path)
                
        return None
        
    def load_script_content(self, script_path: str) -> Optional[str]:
        """Load script content with caching"""
        if script_path in self.script_cache:
            return self.script_cache[script_path]
            
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.script_cache[script_path] = content
                return content
        except Exception as e:
            print(f"Error loading script {script_path}: {e}")
            return None
            
    def parse_extends_from_script(self, script_content: str) -> Optional[str]:
        """Parse extends clause from script content"""
        import re
        extends_match = re.search(r'extends\s+(\w+)', script_content)
        if extends_match:
            return extends_match.group(1)
        return None
        
    def resolve_class(self, class_name: str, visited: Optional[Set[str]] = None) -> Optional[LSCClass]:
        """Resolve a class and its inheritance chain"""
        if visited is None:
            visited = set()
            
        # Prevent circular inheritance
        if class_name in visited:
            print(f"Warning: Circular inheritance detected for class {class_name}")
            return None
            
        visited.add(class_name)
        
        # Return if already resolved
        if class_name in self.classes:
            return self.classes[class_name]
            
        # Find script for this class
        script_path = self.find_script_path(class_name)
        if not script_path:
            print(f"Warning: Could not find script for class {class_name}")
            return None
            
        # Load script content
        script_content = self.load_script_content(script_path)
        if not script_content:
            return None
            
        # Parse extends clause
        base_class_name = self.parse_extends_from_script(script_content)
        base_class = None
        
        if base_class_name:
            # Recursively resolve base class
            base_class = self.resolve_class(base_class_name, visited.copy())
            
        # Create class
        lsc_class = LSCClass(class_name, base_class)
        lsc_class.script_path = script_path
        self.classes[class_name] = lsc_class
        
        return lsc_class
        
    def create_instance_scope(self, class_name: str) -> Optional[LSCScope]:
        """Create a scope for a class instance with inheritance"""
        lsc_class = self.resolve_class(class_name)
        if not lsc_class:
            return None

        # Create scope with inheritance chain
        scope = LSCScope(self.runtime.global_scope)

        # Load and execute parent class scripts in order (base to derived)
        class_chain = self._get_class_chain(lsc_class)

        for cls in class_chain:
            if cls.script_path:
                self._load_class_script_into_scope(cls, scope)

        return scope

    def _get_class_chain(self, lsc_class: LSCClass) -> List[LSCClass]:
        """Get the inheritance chain from base to derived"""
        chain = []
        current = lsc_class

        # Build chain from derived to base
        while current:
            chain.append(current)
            current = current.base_class

        # Reverse to get base to derived order
        chain.reverse()
        return chain

    def _load_class_script_into_scope(self, lsc_class: LSCClass, scope: LSCScope) -> None:
        """Load a class script and execute it in the given scope"""
        if not lsc_class.script_path:
            return

        script_content = self.load_script_content(lsc_class.script_path)
        if not script_content:
            return

        # Set up runtime scope
        old_scope = self.runtime.current_scope
        self.runtime.current_scope = scope

        try:
            # Execute the script to populate the scope with methods and variables
            from .interpreter import execute_lsc_script
            execute_lsc_script(script_content, self.runtime)

            # Store methods and properties in the class for future reference
            for name, value in scope.variables.items():
                if callable(value):
                    lsc_class.add_method(name, value)
                else:
                    lsc_class.add_property(name, value)

        except Exception as e:
            print(f"Error loading class script {lsc_class.script_path}: {e}")
        finally:
            # Restore scope
            self.runtime.current_scope = old_scope
        
    def create_super_object(self, instance_class: LSCClass, instance_scope: LSCScope):
        """Create a super object for method calls"""
        class SuperObject:
            def __init__(self, lsc_class: LSCClass, scope: LSCScope):
                self.lsc_class = lsc_class
                self.scope = scope

            def _ready(self):
                """Call parent _ready method"""
                if self.lsc_class.base_class:
                    method = self.lsc_class.base_class.get_method('_ready')
                    if method and callable(method):
                        return method()

            def on_ready(self):
                """Call parent on_ready method"""
                if self.lsc_class.base_class:
                    method = self.lsc_class.base_class.get_method('on_ready')
                    if method and callable(method):
                        return method()

            def _process(self, delta: float):
                """Call parent _process method"""
                if self.lsc_class.base_class:
                    method = self.lsc_class.base_class.get_method('_process')
                    if method and callable(method):
                        return method(delta)

            def _physics_process(self, delta: float):
                """Call parent _physics_process method"""
                if self.lsc_class.base_class:
                    method = self.lsc_class.base_class.get_method('_physics_process')
                    if method and callable(method):
                        return method(delta)

            def __getattr__(self, name: str):
                """Handle any other super method calls"""
                if self.lsc_class.base_class:
                    method = self.lsc_class.base_class.get_method(name)
                    if method and callable(method):
                        return method

                # Return a no-op function if method not found
                def no_op(*args, **kwargs):
                    pass
                return no_op

        return SuperObject(instance_class, instance_scope)
        
    def get_class(self, class_name: str) -> Optional[LSCClass]:
        """Get a class by name"""
        return self.resolve_class(class_name)
