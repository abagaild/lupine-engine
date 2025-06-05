"""
Visual Script Code Generator for Lupine Engine
Generates Python code from visual script blocks with proper execution flow
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import uuid
from dataclasses import dataclass

from .prefabs.prefab_system import VisualScriptBlock, VisualScriptBlockType


@dataclass
class ExecutionNode:
    """Represents a node in the execution graph"""
    block_id: str
    block: VisualScriptBlock
    inputs: Dict[str, Any]  # Input values
    next_nodes: List['ExecutionNode']  # Next nodes in execution
    visited: bool = False


class VisualScriptCodeGenerator:
    """Generates Python code from visual script blocks"""
    
    def __init__(self):
        self.blocks: Dict[str, VisualScriptBlock] = {}
        self.connections: List[Dict[str, Any]] = []
        self.execution_graph: Dict[str, ExecutionNode] = {}
        
    def set_script_data(self, blocks: List[VisualScriptBlock], connections: List[Dict[str, Any]]):
        """Set the script data for code generation"""
        self.blocks = {block.id: block for block in blocks}
        self.connections = connections
        self._build_execution_graph()
    
    def _build_execution_graph(self):
        """Build the execution graph from blocks and connections"""
        # Create execution nodes
        self.execution_graph = {}
        for block_id, block in self.blocks.items():
            node = ExecutionNode(
                block_id=block_id,
                block=block,
                inputs={},
                next_nodes=[]
            )
            self.execution_graph[block_id] = node
        
        # Build connections
        for connection in self.connections:
            from_id = connection['from_block_id']
            to_id = connection['to_block_id']
            from_output = connection['from_output']
            to_input = connection['to_input']
            conn_type = connection.get('connection_type', 'data')
            
            if from_id in self.execution_graph and to_id in self.execution_graph:
                from_node = self.execution_graph[from_id]
                to_node = self.execution_graph[to_id]
                
                if conn_type == 'exec':
                    # Execution connection
                    from_node.next_nodes.append(to_node)
                else:
                    # Data connection
                    to_node.inputs[to_input] = {
                        'source_block': from_id,
                        'source_output': from_output,
                        'type': 'connection'
                    }
    
    def generate_code(self, class_name: str = "GeneratedScript") -> str:
        """Generate Python code from the visual script"""
        code_lines = [
            "# Generated Python code from visual script",
            "# Created with Lupine Engine Enhanced Visual Script Editor",
            "",
            "# Imports",
            "from core.game_engine import *",
            "from core.scene.base_node import Node",
            "",
            f"class {class_name}:",
            f'    """Generated script class from visual blocks"""',
            "    ",
            "    def __init__(self, node):",
            "        self.node = node",
            "        self._setup_variables()",
            "    ",
            "    def _setup_variables(self):",
            '        """Setup variables from data blocks"""',
        ]
        
        # Generate variable initialization
        data_blocks = [block for block in self.blocks.values() 
                      if not self._has_execution_pins(block)]
        
        for block in data_blocks:
            var_name = self._get_variable_name(block)
            if block.code_template:
                code_lines.append(f"        self.{var_name} = {self._process_code_template(block)}")
            else:
                code_lines.append(f"        self.{var_name} = None")
        
        code_lines.extend([
            "    ",
            "    def execute(self):",
            '        """Execute the visual script logic"""',
        ])
        
        # Find entry points (start events or blocks with no execution input)
        entry_points = self._find_entry_points()
        
        if entry_points:
            for entry_point in entry_points:
                self._generate_execution_chain(entry_point, code_lines, "        ")
        else:
            code_lines.append("        pass  # No entry points found")
        
        # Generate helper methods
        code_lines.extend([
            "    ",
            "    def _get_input_value(self, block_id: str, input_name: str):",
            '        """Get input value for a block"""',
            "        # This would be implemented to get actual input values",
            "        return None",
        ])
        
        return "\n".join(code_lines)
    
    def _has_execution_pins(self, block: VisualScriptBlock) -> bool:
        """Check if a block has execution pins"""
        has_exec_input = any(inp.is_execution_pin for inp in block.inputs)
        has_exec_output = any(out.is_execution_pin for out in block.outputs)
        return has_exec_input or has_exec_output
    
    def _get_variable_name(self, block: VisualScriptBlock) -> str:
        """Get a valid variable name for a block"""
        name = block.name.lower().replace(" ", "_").replace("-", "_")
        # Remove invalid characters
        name = "".join(c for c in name if c.isalnum() or c == "_")
        if not name or name[0].isdigit():
            name = f"block_{name}"
        return name
    
    def _find_entry_points(self) -> List[ExecutionNode]:
        """Find entry points in the execution graph"""
        entry_points = []
        
        for node in self.execution_graph.values():
            # Check if it's a start event
            if node.block.block_type == VisualScriptBlockType.EVENT and "start" in node.block.name.lower():
                entry_points.append(node)
                continue
            
            # Check if it has no execution input connections
            has_exec_input = False
            for connection in self.connections:
                if (connection['to_block_id'] == node.block_id and 
                    connection.get('connection_type') == 'exec'):
                    has_exec_input = True
                    break
            
            if not has_exec_input and self._has_execution_pins(node.block):
                entry_points.append(node)
        
        return entry_points
    
    def _generate_execution_chain(self, node: ExecutionNode, code_lines: List[str], 
                                 indent: str, visited: Optional[Set[str]] = None):
        """Generate code for an execution chain"""
        if visited is None:
            visited = set()
        
        if node.block_id in visited:
            code_lines.append(f"{indent}# Circular reference detected for {node.block.name}")
            return
        
        visited.add(node.block_id)
        
        # Add comment
        code_lines.append(f"{indent}# {node.block.name}")
        
        # Generate block-specific code
        if node.block.block_type == VisualScriptBlockType.FLOW:
            self._generate_flow_block_code(node, code_lines, indent, visited)
        elif node.block.block_type == VisualScriptBlockType.ACTION:
            self._generate_action_block_code(node, code_lines, indent)
        elif node.block.block_type == VisualScriptBlockType.EVENT:
            self._generate_event_block_code(node, code_lines, indent)
        else:
            # Generic block
            if node.block.code_template:
                processed_code = self._process_code_template(node.block, node.inputs)
                code_lines.append(f"{indent}{processed_code}")
            else:
                code_lines.append(f"{indent}pass  # {node.block.name}")
        
        # Continue with next nodes (if not a flow control block)
        if node.block.block_type != VisualScriptBlockType.FLOW:
            for next_node in node.next_nodes:
                code_lines.append("")
                self._generate_execution_chain(next_node, code_lines, indent, visited.copy())
        
        visited.remove(node.block_id)
    
    def _generate_flow_block_code(self, node: ExecutionNode, code_lines: List[str], 
                                 indent: str, visited: Set[str]):
        """Generate code for flow control blocks"""
        block = node.block
        
        if "if" in block.name.lower():
            # If statement
            condition = self._get_input_value(node, "condition", "True")
            code_lines.append(f"{indent}if {condition}:")
            
            # Find true and false branches
            true_nodes = []
            false_nodes = []
            
            for next_node in node.next_nodes:
                # Find which output this connection came from
                for connection in self.connections:
                    if (connection['from_block_id'] == node.block_id and 
                        connection['to_block_id'] == next_node.block_id and
                        connection.get('connection_type') == 'exec'):
                        
                        if connection['from_output'] in ['true', 'True']:
                            true_nodes.append(next_node)
                        elif connection['from_output'] in ['false', 'False']:
                            false_nodes.append(next_node)
            
            # Generate true branch
            if true_nodes:
                for true_node in true_nodes:
                    self._generate_execution_chain(true_node, code_lines, indent + "    ", visited.copy())
            else:
                code_lines.append(f"{indent}    pass")
            
            # Generate false branch
            if false_nodes:
                code_lines.append(f"{indent}else:")
                for false_node in false_nodes:
                    self._generate_execution_chain(false_node, code_lines, indent + "    ", visited.copy())
        
        elif "while" in block.name.lower():
            # While loop
            condition = self._get_input_value(node, "condition", "True")
            code_lines.append(f"{indent}while {condition}:")
            
            # Find loop body nodes
            for next_node in node.next_nodes:
                self._generate_execution_chain(next_node, code_lines, indent + "    ", visited.copy())
        
        elif "for" in block.name.lower():
            # For loop
            count = self._get_input_value(node, "count", "10")
            code_lines.append(f"{indent}for i in range({count}):")
            
            # Find loop body nodes
            for next_node in node.next_nodes:
                self._generate_execution_chain(next_node, code_lines, indent + "    ", visited.copy())
    
    def _generate_action_block_code(self, node: ExecutionNode, code_lines: List[str], indent: str):
        """Generate code for action blocks"""
        if node.block.code_template:
            processed_code = self._process_code_template(node.block, node.inputs)
            code_lines.append(f"{indent}{processed_code}")
        else:
            code_lines.append(f"{indent}pass  # {node.block.name}")
    
    def _generate_event_block_code(self, node: ExecutionNode, code_lines: List[str], indent: str):
        """Generate code for event blocks"""
        if node.block.code_template:
            processed_code = self._process_code_template(node.block, node.inputs)
            code_lines.append(f"{indent}{processed_code}")
        else:
            code_lines.append(f"{indent}pass  # {node.block.name}")
    
    def _process_code_template(self, block: VisualScriptBlock, inputs: Optional[Dict[str, Any]] = None) -> str:
        """Process a code template with input substitution"""
        if not block.code_template:
            return "pass"
        
        code = block.code_template
        inputs = inputs or {}
        
        # Replace input placeholders
        for input_pin in block.inputs:
            placeholder = f"{{{input_pin.name}}}"
            if placeholder in code:
                value = self._get_input_value_from_dict(inputs, input_pin.name, input_pin.default_value)
                code = code.replace(placeholder, str(value))
        
        return code
    
    def _get_input_value(self, node: ExecutionNode, input_name: str, default: Any = None) -> Any:
        """Get input value for a node"""
        if input_name in node.inputs:
            input_info = node.inputs[input_name]
            if input_info['type'] == 'connection':
                # Connected input - would need to evaluate the source
                return f"self._get_connected_value('{input_info['source_block']}', '{input_info['source_output']}')"
        
        # Use default value from block definition
        for input_pin in node.block.inputs:
            if input_pin.name == input_name:
                return input_pin.default_value if input_pin.default_value is not None else default
        
        return default
    
    def _get_input_value_from_dict(self, inputs: Dict[str, Any], input_name: str, default: Any = None) -> Any:
        """Get input value from inputs dictionary"""
        if input_name in inputs:
            input_info = inputs[input_name]
            if isinstance(input_info, dict) and input_info.get('type') == 'connection':
                return f"self._get_connected_value('{input_info['source_block']}', '{input_info['source_output']}')"
            else:
                return input_info
        return default if default is not None else "None"
