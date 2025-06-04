"""
Node Registry System for Lupine Engine
Manages dynamic node registration and categorization for extensible node system
"""

import json
import re
from typing import Dict, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from .scene.node_registry import NodeRegistry as BaseNodeRegistry
from .scene.base_node import Node


class NodeCategory(Enum):
    """Node categories for organization"""
    BASE = "Base"
    NODE_2D = "2D"
    UI = "UI"
    AUDIO = "Audio"
    PREFABS = "Prefabs"


@dataclass
class NodeDefinition:
    """Definition of a registered node type"""
    name: str
    category: NodeCategory
    class_name: str
    script_path: Optional[str] = None
    icon_path: Optional[str] = None
    description: str = ""
    is_builtin: bool = True
    factory_func: Optional[Callable] = None


class DynamicNodeRegistry(BaseNodeRegistry):
    """Enhanced node registry with dynamic discovery and categorization"""

    def __init__(self):
        super().__init__()
        self._node_definitions: Dict[str, NodeDefinition] = {}
        self._categories: Dict[NodeCategory, List[NodeDefinition]] = {
            category: [] for category in NodeCategory
        }
        self._project_path: Optional[Path] = None
        self._initialized = False

    def set_project_path(self, project_path: Path):
        """Set the project path for dynamic node discovery"""
        self._project_path = project_path
        if not self._initialized:
            self._initialize_builtin_nodes()
            self._initialized = True

    def _initialize_builtin_nodes(self):
        """Initialize built-in nodes by scanning the nodes directory"""
        if not self._project_path:
            return

        nodes_dir = self._project_path / "nodes"
        if not nodes_dir.exists():
            return

        # Scan each category directory
        for category_dir in nodes_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name.upper()
            if category_name == "NODE2D":
                category = NodeCategory.NODE_2D
            elif category_name in [cat.name for cat in NodeCategory]:
                category = NodeCategory[category_name]
            else:
                category = NodeCategory.PREFABS

            # Scan Python files in category directory
            for py_file in category_dir.glob("*.py"):
                self._register_node_from_file(py_file, category, is_builtin=True)

    def _register_node_from_file(self, file_path: Path, category: NodeCategory, is_builtin: bool = False):
        """Register a node from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract class name and description
            class_name = self._extract_class_name(content)
            if not class_name:
                return

            description = self._extract_description(content)

            # Create relative script path
            if self._project_path:
                try:
                    script_path = str(file_path.relative_to(self._project_path))
                except ValueError:
                    script_path = str(file_path)
            else:
                script_path = str(file_path)

            # Create node definition
            node_def = NodeDefinition(
                name=class_name,
                category=category,
                class_name=class_name,
                script_path=script_path,
                description=description,
                is_builtin=is_builtin
            )

            # Register the node
            self._node_definitions[class_name] = node_def
            self._categories[category].append(node_def)

            # Create placeholder class for the base registry
            class DynamicNode(Node):
                def __init__(self, name: str = class_name):
                    super().__init__(name, class_name)
                    self.script_path = script_path

            self.register_node(class_name, DynamicNode)

        except Exception as e:
            print(f"Error registering node from {file_path}: {e}")

    def _extract_class_name(self, content: str) -> Optional[str]:
        """Extract the main class name from Python content"""
        # Look for class definitions
        class_pattern = r'^class\s+(\w+)\s*(?:\([^)]*\))?\s*:'
        matches = re.findall(class_pattern, content, re.MULTILINE)

        if matches:
            # Return the first class found (usually the main node class)
            return matches[0]
        return None

    def _extract_description(self, content: str) -> str:
        """Extract description from Python content"""
        # Look for module docstring
        docstring_pattern = r'"""([^"]+)"""'
        matches = re.findall(docstring_pattern, content)

        if matches:
            # Return first docstring, cleaned up
            desc = matches[0].strip()
            # Take first line if multi-line
            return desc.split('\n')[0]

        return ""

    def get_all_categories(self) -> List[NodeCategory]:
        """Get all available node categories"""
        return list(NodeCategory)

    def get_nodes_by_category(self, category: NodeCategory) -> List[NodeDefinition]:
        """Get all nodes in a specific category"""
        return self._categories.get(category, [])

    def get_node_definition(self, node_name: str) -> Optional[NodeDefinition]:
        """Get node definition by name"""
        return self._node_definitions.get(node_name)

    def scan_for_custom_nodes(self, directory: Path):
        """Scan directory for custom node definitions"""
        if not directory.exists():
            return

        # Scan all Python files in the directory and subdirectories
        for py_file in directory.rglob("*.py"):
            # Determine category based on directory structure
            relative_path = py_file.relative_to(directory)
            category_name = relative_path.parts[0] if relative_path.parts else "prefabs"

            # Map directory name to category
            if category_name.lower() == "base":
                category = NodeCategory.BASE
            elif category_name.lower() in ["node2d", "2d"]:
                category = NodeCategory.NODE_2D
            elif category_name.lower() == "ui":
                category = NodeCategory.UI
            elif category_name.lower() == "audio":
                category = NodeCategory.AUDIO
            else:
                category = NodeCategory.PREFABS

            self._register_node_from_file(py_file, category, is_builtin=False)

    def load_prefabs_from_directory(self, directory: Path):
        """Load prefab definitions from directory"""
        if not directory.exists():
            return

        # Load JSON prefab definitions
        for json_file in directory.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    prefab_data = json.load(f)

                # Create node definition from prefab data
                prefab_name = json_file.stem
                node_def = NodeDefinition(
                    name=prefab_name,
                    category=NodeCategory.PREFABS,
                    class_name=prefab_data.get("type", "Node"),
                    script_path=str(json_file.relative_to(self._project_path)) if self._project_path else str(json_file),
                    description=f"Prefab: {prefab_data.get('description', prefab_name)}",
                    is_builtin=False
                )

                self._node_definitions[prefab_name] = node_def
                self._categories[NodeCategory.PREFABS].append(node_def)

            except Exception as e:
                print(f"Error loading prefab {json_file}: {e}")

        # Also scan for Python prefab scripts
        for py_file in directory.glob("*.py"):
            self._register_node_from_file(py_file, NodeCategory.PREFABS, is_builtin=False)

    def create_node_instance(self, node_type: str, node_name: str) -> Optional[Node]:
        """Create a node instance with proper script path"""
        node_def = self._node_definitions.get(node_type)
        if not node_def:
            # Fallback to base registry
            return self.create_node(node_type, node_name)

        # Try to load the actual Python class
        if node_def.script_path and node_def.script_path.endswith('.py'):
            try:
                # Import the module dynamically
                import importlib.util
                import sys

                spec = importlib.util.spec_from_file_location(node_type, node_def.script_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Get the class from the module
                    if hasattr(module, node_type):
                        node_class = getattr(module, node_type)
                        # Create instance of the actual class
                        return node_class(node_name)

            except Exception as e:
                print(f"Error loading node class {node_type} from {node_def.script_path}: {e}")

        # Fallback: Create base node instance
        from core.scene.base_node import Node
        node = Node(node_name, node_type)
        if node_def.script_path:
            node.script_path = node_def.script_path

        return node

    def refresh_nodes(self):
        """Refresh all node definitions by rescanning directories"""
        if not self._project_path:
            return

        # Clear existing definitions
        self._node_definitions.clear()
        for category_list in self._categories.values():
            category_list.clear()

        # Re-initialize
        self._initialize_builtin_nodes()

        # Rescan custom nodes
        nodes_dir = self._project_path / "nodes"
        if nodes_dir.exists():
            self.scan_for_custom_nodes(nodes_dir)

        # Rescan prefabs
        prefabs_dir = self._project_path / "prefabs"
        if prefabs_dir.exists():
            self.load_prefabs_from_directory(prefabs_dir)


# Global registry instance
_node_registry: Optional[DynamicNodeRegistry] = None
_project_path: Optional[Path] = None


def get_node_registry() -> DynamicNodeRegistry:
    """Get the global node registry instance"""
    global _node_registry
    if _node_registry is None:
        _node_registry = DynamicNodeRegistry()
        if _project_path:
            _node_registry.set_project_path(_project_path)
    return _node_registry


def set_project_path(project_path: Path):
    """Set the project path for the node registry"""
    global _project_path
    _project_path = project_path

    # Update existing registry if it exists
    if _node_registry:
        _node_registry.set_project_path(project_path)
