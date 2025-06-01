"""
LSC Export Variable Parser
Parses export variables and export groups from LSC scripts for inspector integration
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class ExportVariable:
    """Represents an export variable from LSC script"""
    
    def __init__(self, name: str, var_type: str, default_value: Any = None, 
                 hint: str = "", group: str = ""):
        self.name = name
        self.type = var_type
        self.default_value = default_value
        self.hint = hint
        self.group = group
    
    def __repr__(self):
        return f"ExportVariable(name='{self.name}', type='{self.type}', default={self.default_value})"


class ExportGroup:
    """Represents an export group from LSC script"""
    
    def __init__(self, name: str, hint: str = ""):
        self.name = name
        self.hint = hint
        self.variables: List[ExportVariable] = []
    
    def add_variable(self, variable: ExportVariable):
        """Add a variable to this group"""
        variable.group = self.name
        self.variables.append(variable)
    
    def __repr__(self):
        return f"ExportGroup(name='{self.name}', variables={len(self.variables)})"


class LSCExportParser:
    """Parser for LSC export variables and groups"""
    
    def __init__(self):
        # Regex patterns for parsing
        self.export_var_pattern = re.compile(
            r'export\s+var\s+(\w+)\s*:\s*(\w+)(?:\s*=\s*([^#\n]+))?(?:\s*#\s*(.+))?',
            re.MULTILINE
        )
        
        self.export_group_pattern = re.compile(
            r'export_group\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']*)["\'])?\s*\)',
            re.MULTILINE
        )
        
        self.export_simple_pattern = re.compile(
            r'export\s+(\w+)\s*:\s*(\w+)(?:\s*=\s*([^#\n]+))?(?:\s*#\s*(.+))?',
            re.MULTILINE
        )
    
    def parse_script(self, script_content: str) -> Tuple[List[ExportGroup], List[ExportVariable]]:
        """Parse export variables and groups from script content"""
        groups = []
        ungrouped_variables = []
        current_group = None
        
        lines = script_content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for export_group
            group_match = self.export_group_pattern.search(line)
            if group_match:
                group_name = group_match.group(1)
                group_hint = group_match.group(2) or ""
                current_group = ExportGroup(group_name, group_hint)
                groups.append(current_group)
                continue
            
            # Check for export var
            var_match = self.export_var_pattern.search(line)
            if var_match:
                var_name = var_match.group(1)
                var_type = var_match.group(2)
                default_str = var_match.group(3)
                hint = var_match.group(4) or ""
                
                # Parse default value
                default_value = self.parse_default_value(default_str, var_type)
                
                variable = ExportVariable(var_name, var_type, default_value, hint)
                
                if current_group:
                    current_group.add_variable(variable)
                else:
                    ungrouped_variables.append(variable)
                continue
            
            # Check for simple export (without var keyword)
            simple_match = self.export_simple_pattern.search(line)
            if simple_match:
                var_name = simple_match.group(1)
                var_type = simple_match.group(2)
                default_str = simple_match.group(3)
                hint = simple_match.group(4) or ""
                
                # Parse default value
                default_value = self.parse_default_value(default_str, var_type)
                
                variable = ExportVariable(var_name, var_type, default_value, hint)
                
                if current_group:
                    current_group.add_variable(variable)
                else:
                    ungrouped_variables.append(variable)
                continue
            
            # If we encounter a non-export line and we're in a group, end the group
            if current_group and line and not line.startswith('#'):
                if not any(keyword in line for keyword in ['export', 'var', 'func', 'class']):
                    current_group = None
        
        return groups, ungrouped_variables
    
    def parse_default_value(self, default_str: str, var_type: str) -> Any:
        """Parse default value string based on variable type"""
        if not default_str:
            return self.get_type_default(var_type)
        
        default_str = default_str.strip()
        
        try:
            if var_type in ['int', 'integer']:
                return int(default_str)
            elif var_type in ['float', 'real']:
                return float(default_str)
            elif var_type in ['bool', 'boolean']:
                return default_str.lower() in ['true', '1', 'yes']
            elif var_type in ['string', 'str']:
                # Remove quotes if present
                if default_str.startswith('"') and default_str.endswith('"'):
                    return default_str[1:-1]
                elif default_str.startswith("'") and default_str.endswith("'"):
                    return default_str[1:-1]
                return default_str
            elif var_type == 'Vector2':
                # Parse Vector2(x, y) format
                if 'Vector2(' in default_str:
                    coords = default_str.split('(')[1].split(')')[0]
                    x, y = map(float, coords.split(','))
                    return [x, y]
                return [0.0, 0.0]
            elif var_type == 'Vector3':
                # Parse Vector3(x, y, z) format
                if 'Vector3(' in default_str:
                    coords = default_str.split('(')[1].split(')')[0]
                    x, y, z = map(float, coords.split(','))
                    return [x, y, z]
                return [0.0, 0.0, 0.0]
            elif var_type == 'Color':
                # Parse Color(r, g, b, a) format
                if 'Color(' in default_str:
                    values = default_str.split('(')[1].split(')')[0]
                    r, g, b, a = map(float, values.split(','))
                    return [r, g, b, a]
                return [1.0, 1.0, 1.0, 1.0]
            else:
                # For unknown types, return as string
                return default_str
        except (ValueError, IndexError):
            # If parsing fails, return type default
            return self.get_type_default(var_type)
    
    def get_type_default(self, var_type: str) -> Any:
        """Get default value for a variable type"""
        defaults = {
            'int': 0,
            'integer': 0,
            'float': 0.0,
            'real': 0.0,
            'bool': False,
            'boolean': False,
            'string': "",
            'str': "",
            'Vector2': [0.0, 0.0],
            'Vector3': [0.0, 0.0, 0.0],
            'Color': [1.0, 1.0, 1.0, 1.0],
            'NodePath': "",
            'Resource': None,
            'Texture': None,
            'AudioStream': None
        }
        return defaults.get(var_type, None)
    
    def parse_script_file(self, script_path: str) -> Tuple[List[ExportGroup], List[ExportVariable]]:
        """Parse export variables from a script file"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_script(content)
        except Exception as e:
            print(f"Error parsing script file {script_path}: {e}")
            return [], []
    
    def get_all_variables(self, groups: List[ExportGroup], 
                         ungrouped: List[ExportVariable]) -> List[ExportVariable]:
        """Get all variables from groups and ungrouped list"""
        all_vars = []
        for group in groups:
            all_vars.extend(group.variables)
        all_vars.extend(ungrouped)
        return all_vars


# Example usage and testing
if __name__ == "__main__":
    # Test script content
    test_script = '''
extends Node2D

export_group("Movement", "Character movement settings")
export var speed: float = 100.0  # Movement speed
export var jump_height: int = 200  # Jump height in pixels

export_group("Health")
export var max_health: int = 100
export var regeneration: bool = true

export var player_name: string = "Player"  # Player display name
export var position_offset: Vector2 = Vector2(10, 20)
'''
    
    parser = LSCExportParser()
    groups, ungrouped = parser.parse_script(test_script)
    
    print("Export Groups:")
    for group in groups:
        print(f"  {group}")
        for var in group.variables:
            print(f"    {var}")
    
    print("\nUngrouped Variables:")
    for var in ungrouped:
        print(f"  {var}")
