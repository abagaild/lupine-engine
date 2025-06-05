"""
Dialogue Parser for Ren'py-style Scripting
Parses dialogue scripts into structured data for execution
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """Types of dialogue nodes"""
    DIALOGUE = "dialogue"
    CHOICE = "choice"
    COMMAND = "command"
    END = "end"


@dataclass
class DialogueChoice:
    """Represents a dialogue choice"""
    text: str
    target_node: str
    condition: Optional[str] = None


@dataclass
class DialogueNode:
    """Represents a dialogue node"""
    node_id: str
    node_type: NodeType
    speaker: Optional[str] = None
    dialogue_lines: List[str] = field(default_factory=list)
    choices: List[DialogueChoice] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)
    condition: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Clean up speaker name (convert PascalCase to readable format)
        if self.speaker:
            self.speaker = self._format_speaker_name(self.speaker)
    
    def _format_speaker_name(self, speaker: str) -> str:
        """Convert speaker name from PascalCase to readable format"""
        # Remove emotion suffix if present
        if '_' in speaker:
            speaker = speaker.split('_')[0]
        
        # Convert PascalCase to readable format
        # DamienWayne -> Damien Wayne
        formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', speaker)
        return formatted


@dataclass
class DialogueScript:
    """Represents a complete dialogue script"""
    filename: str
    nodes: Dict[str, DialogueNode] = field(default_factory=dict)
    start_node: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DialogueParser:
    """Parser for Ren'py-style dialogue scripts"""
    
    def __init__(self):
        # Regex patterns
        self.command_pattern = re.compile(r'\[\[(.+?)\]\]')
        self.choice_pattern = re.compile(r'\[(.+?)\|(.+?)\]')
        self.connection_pattern = re.compile(r'\[(.+?)\]')
        self.condition_pattern = re.compile(r'(.+?)\s+if\s+(.+)')
        
    def parse_script(self, script_content: str) -> DialogueScript:
        """Parse a dialogue script from text content"""
        lines = script_content.strip().split('\n')
        script = DialogueScript(filename="")
        
        current_node = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                i += 1
                continue
            
            # Parse filename declaration
            if line.startswith('FN :'):
                script.filename = line[4:].strip()
                i += 1
                continue
            
            # Parse node declaration
            if self._is_node_declaration(line):
                # Save previous node
                if current_node:
                    script.nodes[current_node.node_id] = current_node
                    if not script.start_node:
                        script.start_node = current_node.node_id
                
                # Parse new node
                current_node = self._parse_node_declaration(line)
                i += 1
                continue
            
            # Parse node content
            if current_node:
                i = self._parse_node_content(lines, i, current_node)
            else:
                i += 1
        
        # Save final node
        if current_node:
            script.nodes[current_node.node_id] = current_node
            if not script.start_node:
                script.start_node = current_node.node_id
        
        return script
    
    def _is_node_declaration(self, line: str) -> bool:
        """Check if line is a node declaration"""
        # Node ID can be alphanumeric with underscores, optionally followed by condition
        pattern = r'^[a-zA-Z0-9_]+(\s+if\s+.+)?$'
        return bool(re.match(pattern, line))
    
    def _parse_node_declaration(self, line: str) -> DialogueNode:
        """Parse a node declaration line"""
        # Check for condition
        condition_match = self.condition_pattern.match(line)
        if condition_match:
            node_id = condition_match.group(1).strip()
            condition = condition_match.group(2).strip()
        else:
            node_id = line.strip()
            condition = None
        
        return DialogueNode(
            node_id=node_id,
            node_type=NodeType.DIALOGUE,
            condition=condition
        )
    
    def _parse_node_content(self, lines: List[str], start_index: int, node: DialogueNode) -> int:
        """Parse the content of a node, returns next line index"""
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Empty line or next node declaration - end current node
            if not line or self._is_node_declaration(line):
                break
            
            # Skip comments
            if line.startswith('#'):
                i += 1
                continue
            
            # Parse commands
            if self.command_pattern.search(line):
                commands = self.command_pattern.findall(line)
                node.commands.extend(commands)
                i += 1
                continue
            
            # Parse choices
            if self.choice_pattern.search(line):
                choices = self.choice_pattern.findall(line)
                for choice_text, target in choices:
                    node.choices.append(DialogueChoice(choice_text.strip(), target.strip()))
                node.node_type = NodeType.CHOICE
                i += 1
                continue
            
            # Parse simple connections
            if self.connection_pattern.match(line) and not self.choice_pattern.search(line):
                connections = self.connection_pattern.findall(line)
                node.connections.extend([conn.strip() for conn in connections])
                i += 1
                continue
            
            # Check for 'end' keyword
            if line.lower() == 'end':
                node.node_type = NodeType.END
                i += 1
                continue
            
            # Parse speaker (if no dialogue lines yet and not a command/choice/connection)
            if not node.dialogue_lines and not node.speaker and not any([
                self.command_pattern.search(line),
                self.choice_pattern.search(line),
                self.connection_pattern.match(line)
            ]):
                node.speaker = line
                i += 1
                continue
            
            # Parse dialogue line
            node.dialogue_lines.append(line)
            i += 1
        
        return i
    
    def script_to_text(self, script: DialogueScript) -> str:
        """Convert a dialogue script back to text format"""
        lines = []
        
        # Add filename
        if script.filename:
            lines.append(f"FN : {script.filename}")
            lines.append("")
        
        # Add nodes in order (start with start_node, then others)
        processed_nodes = set()
        
        if script.start_node and script.start_node in script.nodes:
            lines.extend(self._node_to_text(script.nodes[script.start_node]))
            processed_nodes.add(script.start_node)
        
        # Add remaining nodes
        for node_id, node in script.nodes.items():
            if node_id not in processed_nodes:
                lines.extend(self._node_to_text(node))
        
        return '\n'.join(lines)
    
    def _node_to_text(self, node: DialogueNode) -> List[str]:
        """Convert a dialogue node to text lines"""
        lines = []
        
        # Node declaration
        if node.condition:
            lines.append(f"{node.node_id} if {node.condition}")
        else:
            lines.append(node.node_id)
        
        # Speaker
        if node.speaker:
            lines.append(node.speaker)
        
        # Dialogue lines
        lines.extend(node.dialogue_lines)
        
        # Commands
        for command in node.commands:
            lines.append(f"[[{command}]]")
        
        # Choices
        for choice in node.choices:
            lines.append(f"[{choice.text}|{choice.target_node}]")
        
        # Simple connections
        for connection in node.connections:
            lines.append(f"[{connection}]")
        
        # End marker
        if node.node_type == NodeType.END:
            lines.append("end")
        
        lines.append("")  # Empty line after node
        return lines
    
    def validate_script(self, script: DialogueScript) -> List[str]:
        """Validate a dialogue script and return list of errors"""
        errors = []
        
        # Check for start node
        if not script.start_node:
            errors.append("No start node found")
        elif script.start_node not in script.nodes:
            errors.append(f"Start node '{script.start_node}' not found in script")
        
        # Check node references
        for node_id, node in script.nodes.items():
            # Check choice targets
            for choice in node.choices:
                if choice.target_node not in script.nodes and choice.target_node != 'end':
                    errors.append(f"Node '{node_id}': Choice target '{choice.target_node}' not found")
            
            # Check connection targets
            for connection in node.connections:
                if connection not in script.nodes and connection != 'end':
                    errors.append(f"Node '{node_id}': Connection target '{connection}' not found")
        
        return errors
