"""
Python Script Runtime System for Lupine Engine
Replaces the LSC system with native Python script execution
"""

import ast
import re
import sys
import types
import inspect
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path


class PythonScriptRuntime:
    """Runtime system for executing Python scripts in the game engine"""
    
    def __init__(self, game_runtime=None):
        self.game_runtime = game_runtime
        self.delta_time = 0.0
        self.runtime_time = 0.0
        self.global_scope = {}
        self.current_scope = None
        
        # Setup built-in functions
        self.setup_builtins()
    
    def setup_builtins(self):
        """Setup built-in functions available to all scripts"""
        self.global_scope.update({
            # Core engine functions
            'print': print,
            'len': len,
            'range': range,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'abs': abs,
            'min': min,
            'max': max,
            
            # Game engine specific functions (will be added by game_runtime)
            'get_node': None,
            'find_node': None,
            'change_scene': None,
            'emit_signal': None,
            'get_delta_time': lambda: self.delta_time,
            'get_runtime_time': lambda: self.runtime_time,
        })
    
    def update_time(self, delta_time: float):
        """Update timing information"""
        self.delta_time = delta_time
        self.runtime_time += delta_time
    
    def get_runtime_time(self) -> float:
        """Get total runtime in seconds"""
        return self.runtime_time
    
    def add_builtin(self, name: str, func: Callable):
        """Add a built-in function to the global scope"""
        self.global_scope[name] = func
    
    def execute_script(self, script_content: str, script_instance: 'PythonScriptInstance'):
        """Execute a Python script in the context of a script instance"""
        try:
            # Parse export variables and groups
            parsed_data = self.parse_export_variables(script_content)
            export_vars = parsed_data['variables']
            export_groups = parsed_data['groups']

            script_instance.export_variables = export_vars
            script_instance.export_groups = export_groups

            # Convert script content to valid Python by replacing '!' prefix
            processed_content = self.process_script_content(script_content)

            # Create execution namespace
            namespace = self.global_scope.copy()
            namespace.update({
                'self': script_instance.node,
                'node': script_instance.node,
                '__file__': script_instance.script_path,
                '__name__': '__main__',
            })

            # Add export variables to namespace with their default values
            for var_name, var_info in export_vars.items():
                namespace[var_name] = var_info['value']

            # Execute the processed script
            exec(processed_content, namespace)

            # Update export variables with any changes from script execution
            for var_name in export_vars.keys():
                if var_name in namespace:
                    export_vars[var_name]['value'] = namespace[var_name]

            # Store the namespace for later method calls
            script_instance.namespace = namespace

            return True

        except Exception as e:
            print(f"Error executing script {script_instance.script_path}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def process_script_content(self, script_content: str) -> str:
        """Process script content to convert '!' prefix variables to regular Python variables"""
        lines = script_content.split('\n')
        processed_lines = []

        for line in lines:
            # Replace lines that start with '!' with regular variable assignments
            stripped = line.strip()
            if stripped.startswith('!') and '=' in stripped:
                # Extract the variable name and value
                var_part = stripped[1:]  # Remove the '!' prefix
                processed_lines.append(line.replace('!' + var_part.split('=')[0], var_part.split('=')[0]))
            else:
                processed_lines.append(line)

        return '\n'.join(processed_lines)

    def parse_export_variables(self, script_content: str) -> Dict[str, Any]:
        """Parse export variables and groups from script content"""
        export_vars = {}
        export_groups = {}
        current_group = None

        # Use regex to find export variables and groups
        import re
        lines = script_content.split('\n')

        for line in lines:
            stripped = line.strip()

            # Check for export group declaration
            if stripped.startswith('# @export_group'):
                # Parse group declaration: # @export_group("Group Name", "Optional description")
                group_match = re.match(r'#\s*@export_group\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']*)["\'])?\s*\)', stripped)
                if group_match:
                    group_name = group_match.group(1)
                    group_description = group_match.group(2) or ""
                    current_group = group_name
                    if group_name not in export_groups:
                        export_groups[group_name] = {
                            'name': group_name,
                            'description': group_description,
                            'variables': []
                        }
                continue

            # Check for export variable
            if stripped.startswith('!') and '=' in stripped:
                try:
                    # Extract variable name and value
                    parts = stripped.split('=', 1)
                    var_name = parts[0][1:].strip()  # Remove '!' and whitespace
                    value_str = parts[1].strip()

                    # Check for type hint in comment
                    type_hint = None
                    hint_description = ""
                    if '#' in value_str:
                        value_part, comment_part = value_str.split('#', 1)
                        value_str = value_part.strip()
                        comment = comment_part.strip()

                        # Parse type hint: # @type:path or # @type:color "Description"
                        type_match = re.match(r'@type:\s*(\w+)(?:\s+["\']([^"\']*)["\'])?', comment)
                        if type_match:
                            type_hint = type_match.group(1)
                            hint_description = type_match.group(2) or ""

                    # Try to evaluate the value
                    try:
                        default_value = ast.literal_eval(value_str)
                    except:
                        # If literal_eval fails, treat as string
                        if value_str.startswith('"') and value_str.endswith('"'):
                            default_value = value_str[1:-1]
                        elif value_str.startswith("'") and value_str.endswith("'"):
                            default_value = value_str[1:-1]
                        else:
                            default_value = value_str

                    # Determine base type
                    base_type = type(default_value).__name__

                    # Use type hint if provided, otherwise use base type
                    var_type = type_hint if type_hint else base_type

                    var_info = {
                        'value': default_value,
                        'type': var_type,
                        'base_type': base_type,
                        'hint': hint_description,
                        'group': current_group
                    }

                    export_vars[var_name] = var_info

                    # Add to current group if one is active
                    if current_group and current_group in export_groups:
                        export_groups[current_group]['variables'].append(var_name)

                except Exception as e:
                    print(f"Error parsing export variable from line '{stripped}': {e}")

        return {'variables': export_vars, 'groups': export_groups}


class PythonScriptInstance:
    """Represents an instance of a Python script attached to a node"""

    def __init__(self, node, script_path: str, runtime: PythonScriptRuntime, base_class=None):
        self.node = node
        self.script_path = script_path
        self.runtime = runtime
        self.base_class = base_class
        self.namespace = {}
        self.export_variables = {}
        self.export_groups = {}
        self.ready_called = False
        
        # Bind the script instance to the node
        node.script_instance = self
    
    def get_script_methods(self) -> Dict[str, Callable]:
        """Get methods that should be available in the script namespace"""
        return {
            'emit_signal': self.emit_signal,
            'connect': self.connect,
            'get_node': self.get_node,
            'find_node': self.find_node,
            'change_scene': self.change_scene,
        }
    
    def _create_lifecycle_method(self, method_name: str):
        """Create a wrapper for lifecycle methods"""
        def wrapper(*args, **kwargs):
            if method_name in self.namespace:
                return self.namespace[method_name](*args, **kwargs)
        return wrapper
    
    def call_method(self, method_name: str, *args, **kwargs):
        """Call a method defined in the script"""
        if method_name in self.namespace and callable(self.namespace[method_name]):
            try:
                return self.namespace[method_name](*args, **kwargs)
            except Exception as e:
                print(f"Error calling {method_name} in {self.script_path}: {e}")
                import traceback
                traceback.print_exc()
        return None
    
    def has_method(self, method_name: str) -> bool:
        """Check if the script has a specific method"""
        return method_name in self.namespace and callable(self.namespace[method_name])
    
    def emit_signal(self, signal_name: str, *args):
        """Emit a signal (placeholder implementation)"""
        print(f"Signal emitted: {signal_name} with args: {args}")
        # TODO: Implement proper signal system
    
    def connect(self, signal_name: str, target_method: Callable):
        """Connect a signal to a method (placeholder implementation)"""
        print(f"Connected signal {signal_name} to {target_method}")
        # TODO: Implement proper signal system
    
    def get_node(self, path: str):
        """Get a node by path"""
        if self.runtime.game_runtime:
            return self.runtime.game_runtime.get_node(path)
        return None
    
    def find_node(self, name: str):
        """Find a node by name"""
        if self.runtime.game_runtime:
            return self.runtime.game_runtime.find_node_by_name(name)
        return None

    def change_scene(self, scene_path: str):
        """Change to a different scene"""
        if self.runtime.game_runtime:
            return self.runtime.game_runtime.change_scene(scene_path)
        print(f"Changing scene to: {scene_path}")

    def get_export_variable(self, name: str):
        """Get the value of an export variable"""
        if name in self.export_variables:
            return self.export_variables[name]['value']
        return None

    def set_export_variable(self, name: str, value: Any):
        """Set the value of an export variable"""
        if name in self.export_variables:
            self.export_variables[name]['value'] = value
            # Also update in the script namespace if it exists
            if name in self.namespace:
                self.namespace[name] = value


def change_scene(scene_path: str):
    """Built-in function to change scenes"""
    # This will be replaced by the actual game runtime implementation
    print(f"Changing scene to: {scene_path}")


def emit_signal(signal_name: str, *args):
    """Built-in function to emit signals"""
    print(f"Signal emitted: {signal_name} with args: {args}")
