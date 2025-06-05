"""
Dialogue Runtime System
Manages execution of dialogue scripts and state management
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .dialogue_parser import DialogueScript, DialogueNode, NodeType, DialogueParser
from .dialogue_commands import DialogueCommandExecutor
from .asset_resolver import DialogueAssetResolver


class DialogueState(Enum):
    """States of dialogue execution"""
    STOPPED = "stopped"
    PLAYING = "playing"
    WAITING_FOR_INPUT = "waiting_for_input"
    WAITING_FOR_CHOICE = "waiting_for_choice"
    PAUSED = "paused"
    FINISHED = "finished"


@dataclass
class DialogueContext:
    """Context information for dialogue execution"""
    script: DialogueScript
    current_node_id: Optional[str] = None
    current_line_index: int = 0
    state: DialogueState = DialogueState.STOPPED
    choice_options: List[Any] = None
    
    def reset(self):
        """Reset context to initial state"""
        self.current_node_id = self.script.start_node
        self.current_line_index = 0
        self.state = DialogueState.STOPPED
        self.choice_options = None


class DialogueRuntime:
    """Runtime system for executing dialogue scripts"""
    
    def __init__(self, project, asset_resolver: DialogueAssetResolver = None):
        self.project = project
        self.asset_resolver = asset_resolver or DialogueAssetResolver(project)
        self.command_executor = DialogueCommandExecutor(self.asset_resolver)
        self.parser = DialogueParser()
        
        # Current execution context
        self.context: Optional[DialogueContext] = None
        
        # Event callbacks
        self.on_dialogue_line: Optional[Callable] = None
        self.on_speaker_change: Optional[Callable] = None
        self.on_choices_available: Optional[Callable] = None
        self.on_dialogue_finished: Optional[Callable] = None
        self.on_state_change: Optional[Callable] = None
        
        # Auto-advance settings
        self.auto_advance = False
        self.auto_advance_delay = 2.0  # seconds
        
        # History
        self.dialogue_history: List[Dict[str, Any]] = []
        self.max_history = 100
    
    def load_script_from_file(self, script_path: str) -> bool:
        """Load a dialogue script from file"""
        try:
            file_path = Path(self.project.project_path) / script_path
            if not file_path.exists():
                print(f"Dialogue script not found: {script_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            script = self.parser.parse_script(content)
            script.filename = script_path
            
            # Validate script
            errors = self.parser.validate_script(script)
            if errors:
                print(f"Script validation errors: {errors}")
                return False
            
            self.context = DialogueContext(script)
            self.context.reset()
            return True
            
        except Exception as e:
            print(f"Error loading dialogue script: {e}")
            return False
    
    def load_script_from_text(self, script_text: str, filename: str = "untitled") -> bool:
        """Load a dialogue script from text"""
        try:
            script = self.parser.parse_script(script_text)
            script.filename = filename
            
            # Validate script
            errors = self.parser.validate_script(script)
            if errors:
                print(f"Script validation errors: {errors}")
                return False
            
            self.context = DialogueContext(script)
            self.context.reset()
            return True
            
        except Exception as e:
            print(f"Error loading dialogue script: {e}")
            return False
    
    def start_dialogue(self) -> bool:
        """Start dialogue execution"""
        if not self.context or not self.context.script.start_node:
            return False
        
        self.context.reset()
        self.context.state = DialogueState.PLAYING
        self._notify_state_change()
        
        # Execute initial commands and advance to first dialogue
        return self._advance_dialogue()
    
    def advance_dialogue(self) -> bool:
        """Advance to next dialogue line or node"""
        if not self.context or self.context.state not in [DialogueState.WAITING_FOR_INPUT, DialogueState.PLAYING]:
            return False
        
        return self._advance_dialogue()
    
    def make_choice(self, choice_index: int) -> bool:
        """Make a dialogue choice"""
        if not self.context or self.context.state != DialogueState.WAITING_FOR_CHOICE:
            return False
        
        if not self.context.choice_options or choice_index >= len(self.context.choice_options):
            return False
        
        choice = self.context.choice_options[choice_index]
        target_node = choice.target_node
        
        # Add choice to history
        self._add_to_history("choice", choice.text, target_node)
        
        # Navigate to target node
        if target_node == "end":
            return self._finish_dialogue()
        
        return self._goto_node(target_node)
    
    def _advance_dialogue(self) -> bool:
        """Internal method to advance dialogue"""
        if not self.context:
            return False
        
        current_node = self._get_current_node()
        if not current_node:
            return self._finish_dialogue()
        
        # Execute commands first
        for command in current_node.commands:
            self.command_executor.execute_command(command)
        
        # Handle different node types
        if current_node.node_type == NodeType.END:
            return self._finish_dialogue()
        
        elif current_node.node_type == NodeType.CHOICE:
            return self._handle_choice_node(current_node)
        
        elif current_node.node_type == NodeType.DIALOGUE:
            return self._handle_dialogue_node(current_node)
        
        return False
    
    def _handle_dialogue_node(self, node: DialogueNode) -> bool:
        """Handle a dialogue node"""
        # Check if we have dialogue lines to show
        if self.context.current_line_index < len(node.dialogue_lines):
            # Show current dialogue line
            line = node.dialogue_lines[self.context.current_line_index]
            speaker = node.speaker
            
            # Add to history
            self._add_to_history("dialogue", line, speaker)
            
            # Notify callbacks
            if self.on_dialogue_line:
                self.on_dialogue_line(line, speaker)
            
            if self.on_speaker_change and speaker:
                self.on_speaker_change(speaker)
            
            # Advance line index
            self.context.current_line_index += 1
            
            # Wait for input unless auto-advancing
            if not self.auto_advance:
                self.context.state = DialogueState.WAITING_FOR_INPUT
                self._notify_state_change()
            
            return True
        
        else:
            # No more dialogue lines, check for connections
            if node.connections:
                target = node.connections[0]  # Take first connection
                if target == "end":
                    return self._finish_dialogue()
                else:
                    return self._goto_node(target)
            else:
                # No connections, finish dialogue
                return self._finish_dialogue()
    
    def _handle_choice_node(self, node: DialogueNode) -> bool:
        """Handle a choice node"""
        if not node.choices:
            return self._finish_dialogue()
        
        # Filter choices based on conditions
        available_choices = []
        for choice in node.choices:
            if not choice.condition or self.command_executor.evaluate_condition(choice.condition):
                available_choices.append(choice)
        
        if not available_choices:
            return self._finish_dialogue()
        
        # Set up choice state
        self.context.choice_options = available_choices
        self.context.state = DialogueState.WAITING_FOR_CHOICE
        self._notify_state_change()
        
        # Notify callback
        if self.on_choices_available:
            choice_texts = [choice.text for choice in available_choices]
            self.on_choices_available(choice_texts)
        
        return True
    
    def _goto_node(self, node_id: str) -> bool:
        """Navigate to a specific node"""
        if not self.context or node_id not in self.context.script.nodes:
            return False
        
        # Find the correct node variant based on conditions
        target_node = self._find_matching_node(node_id)
        if not target_node:
            return False
        
        self.context.current_node_id = target_node.node_id
        self.context.current_line_index = 0
        self.context.state = DialogueState.PLAYING
        self._notify_state_change()
        
        return self._advance_dialogue()
    
    def _find_matching_node(self, base_node_id: str) -> Optional[DialogueNode]:
        """Find the first matching node variant based on conditions"""
        # Look for nodes with the same base ID but different conditions
        matching_nodes = []
        
        for node_id, node in self.context.script.nodes.items():
            if node_id == base_node_id or node_id.startswith(f"{base_node_id} if"):
                matching_nodes.append(node)
        
        # Sort by specificity (nodes with conditions first)
        matching_nodes.sort(key=lambda n: 0 if n.condition else 1)
        
        # Return first matching node
        for node in matching_nodes:
            if not node.condition or self.command_executor.evaluate_condition(node.condition):
                return node
        
        return None
    
    def _get_current_node(self) -> Optional[DialogueNode]:
        """Get the current dialogue node"""
        if not self.context or not self.context.current_node_id:
            return None
        
        return self._find_matching_node(self.context.current_node_id)
    
    def _finish_dialogue(self) -> bool:
        """Finish dialogue execution"""
        if not self.context:
            return False
        
        self.context.state = DialogueState.FINISHED
        self._notify_state_change()
        
        if self.on_dialogue_finished:
            self.on_dialogue_finished()
        
        return True
    
    def _add_to_history(self, entry_type: str, content: str, extra: str = None):
        """Add entry to dialogue history"""
        entry = {
            'type': entry_type,
            'content': content,
            'extra': extra,
            'timestamp': None  # Could add timestamp if needed
        }
        
        self.dialogue_history.append(entry)
        
        # Limit history size
        if len(self.dialogue_history) > self.max_history:
            self.dialogue_history.pop(0)
    
    def _notify_state_change(self):
        """Notify state change callback"""
        if self.on_state_change:
            self.on_state_change(self.context.state if self.context else DialogueState.STOPPED)
    
    def pause_dialogue(self):
        """Pause dialogue execution"""
        if self.context:
            self.context.state = DialogueState.PAUSED
            self._notify_state_change()
    
    def resume_dialogue(self):
        """Resume dialogue execution"""
        if self.context and self.context.state == DialogueState.PAUSED:
            self.context.state = DialogueState.PLAYING
            self._notify_state_change()
    
    def stop_dialogue(self):
        """Stop dialogue execution"""
        if self.context:
            self.context.state = DialogueState.STOPPED
            self._notify_state_change()
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current dialogue runtime state"""
        if not self.context:
            return {'state': DialogueState.STOPPED}
        
        return {
            'state': self.context.state,
            'script_name': self.context.script.filename,
            'current_node': self.context.current_node_id,
            'line_index': self.context.current_line_index,
            'has_choices': bool(self.context.choice_options),
            'visual_state': self.command_executor.get_current_state()
        }
    
    def set_callbacks(self, **callbacks):
        """Set event callbacks"""
        for name, callback in callbacks.items():
            if hasattr(self, name):
                setattr(self, name, callback)
    
    def get_dialogue_history(self) -> List[Dict[str, Any]]:
        """Get dialogue history"""
        return self.dialogue_history.copy()
    
    def clear_history(self):
        """Clear dialogue history"""
        self.dialogue_history.clear()
