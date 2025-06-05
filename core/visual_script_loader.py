"""
Visual Script Loader for Lupine Engine
Loads and executes visual scripts (.vscript files) at runtime
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from .visual_script_generator import VisualScriptCodeGenerator
from .prefabs.prefab_system import VisualScriptBlock, VisualScriptInput, VisualScriptOutput, VisualScriptBlockType


class VisualScriptInstance:
    """Runtime instance of a visual script"""
    
    def __init__(self, script_data: Dict[str, Any], node):
        self.script_data = script_data
        self.node = node
        self.variables = {}
        self.generator = VisualScriptCodeGenerator()
        
        # Parse blocks and connections
        self.blocks = []
        self.connections = []

        if 'blocks' in script_data:
            for block_data in script_data['blocks']:
                if 'block_definition' in block_data:
                    # Convert JSON data to VisualScriptBlock object
                    block_def = block_data['block_definition']
                    visual_block = self._create_visual_script_block(block_def)
                    if visual_block:
                        self.blocks.append(visual_block)

        if 'connections' in script_data:
            self.connections = script_data['connections']

        # Set up the generator
        self.generator.set_script_data(self.blocks, self.connections)
        
        # Generate and compile the code
        self.generated_code = self.generator.generate_code("VisualScript")
        self.compiled_code = None
        self.script_class = None
        self.script_instance = None
        
        try:
            # Compile the generated code
            self.compiled_code = compile(self.generated_code, '<visual_script>', 'exec')
            
            # Execute to get the class
            namespace = {
                'Node': node.__class__,
                'print': print,
                # Add other necessary imports here
            }
            exec(self.compiled_code, namespace)
            
            # Get the generated class
            if 'VisualScript' in namespace:
                self.script_class = namespace['VisualScript']
                self.script_instance = self.script_class(node)
            
        except Exception as e:
            print(f"Error compiling visual script: {e}")
            print(f"Generated code:\n{self.generated_code}")
    
    def execute(self):
        """Execute the visual script"""
        if self.script_instance and hasattr(self.script_instance, 'execute'):
            try:
                self.script_instance.execute()
            except Exception as e:
                print(f"Error executing visual script: {e}")

    def _create_visual_script_block(self, block_def: Dict[str, Any]) -> Optional[VisualScriptBlock]:
        """Create a VisualScriptBlock from JSON data"""
        try:
            # Create inputs
            inputs = []
            for inp_data in block_def.get('inputs', []):
                input_obj = VisualScriptInput(
                    name=inp_data.get('name', ''),
                    type=inp_data.get('type', 'any'),
                    default_value=inp_data.get('default_value'),
                    description=inp_data.get('description', ''),
                    is_execution_pin=inp_data.get('is_execution_pin', False)
                )
                inputs.append(input_obj)

            # Create outputs
            outputs = []
            for out_data in block_def.get('outputs', []):
                output_obj = VisualScriptOutput(
                    name=out_data.get('name', ''),
                    type=out_data.get('type', 'any'),
                    description=out_data.get('description', ''),
                    is_execution_pin=out_data.get('is_execution_pin', False)
                )
                outputs.append(output_obj)

            # Get block type
            block_type_data = block_def.get('block_type', {})
            if isinstance(block_type_data, dict):
                block_type_value = block_type_data.get('value', 'action')
            else:
                block_type_value = str(block_type_data)

            # Map string to enum
            block_type_map = {
                'event': VisualScriptBlockType.EVENT,
                'action': VisualScriptBlockType.ACTION,
                'flow': VisualScriptBlockType.FLOW,
                'variable': VisualScriptBlockType.VARIABLE,
                'custom': VisualScriptBlockType.CUSTOM
            }
            block_type = block_type_map.get(block_type_value, VisualScriptBlockType.ACTION)

            # Create the block
            visual_block = VisualScriptBlock(
                id=block_def.get('id', ''),
                name=block_def.get('name', ''),
                category=block_def.get('category', ''),
                block_type=block_type,
                description=block_def.get('description', ''),
                inputs=inputs,
                outputs=outputs,
                code_template=block_def.get('code_template', ''),
                color=block_def.get('color', '#808080')
            )

            return visual_block

        except Exception as e:
            print(f"Error creating visual script block: {e}")
            return None

    def has_method(self, method_name: str) -> bool:
        """Check if the script has a specific method"""
        return bool(self.script_instance and
                   hasattr(self.script_instance, method_name))
    
    def call_method(self, method_name: str, *args, **kwargs):
        """Call a method on the script instance"""
        if self.has_method(method_name):
            try:
                method = getattr(self.script_instance, method_name)
                return method(*args, **kwargs)
            except Exception as e:
                print(f"Error calling visual script method {method_name}: {e}")
        return None


class VisualScriptLoader:
    """Loads and manages visual scripts"""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path
        self.loaded_scripts: Dict[str, Dict[str, Any]] = {}
    
    def load_visual_script(self, script_path: str) -> Optional[Dict[str, Any]]:
        """Load a visual script from file"""
        try:
            # Check if already loaded
            if script_path in self.loaded_scripts:
                return self.loaded_scripts[script_path]
            
            # Resolve path
            if self.project_path:
                full_path = Path(self.project_path) / script_path
            else:
                full_path = Path(script_path)
            
            if not full_path.exists():
                print(f"Visual script file not found: {full_path}")
                return None
            
            # Load the script data
            with open(full_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # Cache the loaded script
            self.loaded_scripts[script_path] = script_data
            return script_data
            
        except Exception as e:
            print(f"Error loading visual script {script_path}: {e}")
            return None
    
    def create_script_instance(self, script_path: str, node) -> Optional[VisualScriptInstance]:
        """Create a visual script instance for a node"""
        script_data = self.load_visual_script(script_path)
        if script_data:
            return VisualScriptInstance(script_data, node)
        return None
    
    def attach_visual_script_to_node(self, node, script_path: str) -> bool:
        """Attach a visual script to a node"""
        try:
            script_instance = self.create_script_instance(script_path, node)
            if script_instance:
                node.visual_script_path = script_path
                node.visual_script_instance = script_instance
                return True
        except Exception as e:
            print(f"Error attaching visual script to node: {e}")
        return False
    
    def reload_script(self, script_path: str):
        """Reload a visual script (useful for development)"""
        if script_path in self.loaded_scripts:
            del self.loaded_scripts[script_path]
        return self.load_visual_script(script_path)


# Global visual script loader instance
_visual_script_loader: Optional[VisualScriptLoader] = None


def get_visual_script_loader() -> VisualScriptLoader:
    """Get the global visual script loader instance"""
    global _visual_script_loader
    if _visual_script_loader is None:
        _visual_script_loader = VisualScriptLoader()
    return _visual_script_loader


def set_visual_script_loader(loader: VisualScriptLoader):
    """Set the global visual script loader instance"""
    global _visual_script_loader
    _visual_script_loader = loader


def load_visual_script_for_node(node, script_path: str) -> bool:
    """Convenience function to load a visual script for a node"""
    loader = get_visual_script_loader()
    return loader.attach_visual_script_to_node(node, script_path)


def execute_visual_script(node) -> bool:
    """Execute the visual script attached to a node"""
    if hasattr(node, 'visual_script_instance') and node.visual_script_instance:
        node.visual_script_instance.execute()
        return True
    return False
