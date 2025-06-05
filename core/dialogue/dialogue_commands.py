"""
Dialogue Commands System
Handles execution of dialogue commands like background changes, music, variables, etc.
"""

import re
from typing import Dict, Any, Optional, Callable, List
from core.globals.variables_manager import get_variables_manager, set_global_var, get_global_var
from core.dialogue.asset_resolver import DialogueAssetResolver


class DialogueCommandExecutor:
    """Executes dialogue commands and manages dialogue state"""
    
    def __init__(self, asset_resolver: DialogueAssetResolver):
        self.asset_resolver = asset_resolver
        self.variables_manager = get_variables_manager()
        
        # Current dialogue state
        self.current_background = None
        self.current_music = None
        self.character_positions = {
            'left': None,
            'center': None,
            'right': None
        }
        self.key_image = None
        
        # Command handlers
        self.command_handlers = {
            'background': self._handle_background,
            'setLeft': self._handle_set_left,
            'setCenter': self._handle_set_center,
            'setRight': self._handle_set_right,
            'showKeyImage': self._handle_show_key_image,
            'clearKeyImage': self._handle_clear_key_image,
            'transitionEffect': self._handle_transition_effect,
            'characterEffect': self._handle_character_effect,
            'playMusic': self._handle_play_music,
            'stopMusic': self._handle_stop_music,
            'crossMusic': self._handle_cross_music,
            'playSound': self._handle_play_sound,
            'signal': self._handle_signal,
            'var': self._handle_variable
        }
        
        # External handlers (can be set by dialogue runtime)
        self.external_handlers = {}
        
        # Signal emission callback
        self.signal_callback: Optional[Callable] = None
        self.scene_change_callback: Optional[Callable] = None
        self.audio_callback: Optional[Callable] = None
        self.visual_callback: Optional[Callable] = None
    
    def execute_command(self, command: str) -> bool:
        """
        Execute a dialogue command
        
        Args:
            command: Command string to execute
            
        Returns:
            True if command was executed successfully
        """
        try:
            # Parse command
            parts = command.strip().split(' ', 1)
            if not parts:
                return False
            
            command_name = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            
            # Check for external handlers first
            if command_name in self.external_handlers:
                return self.external_handlers[command_name](args)
            
            # Check built-in handlers
            if command_name in self.command_handlers:
                return self.command_handlers[command_name](args)
            
            print(f"Unknown dialogue command: {command_name}")
            return False
            
        except Exception as e:
            print(f"Error executing dialogue command '{command}': {e}")
            return False
    
    def _handle_background(self, args: str) -> bool:
        """Handle background command"""
        background_path = self.asset_resolver.resolve_background(args.strip())
        if background_path:
            self.current_background = background_path
            if self.visual_callback:
                self.visual_callback('background', background_path)
            return True
        else:
            print(f"Background not found: {args}")
            return False
    
    def _handle_set_left(self, args: str) -> bool:
        """Handle setLeft command"""
        return self._set_character_position('left', args.strip())
    
    def _handle_set_center(self, args: str) -> bool:
        """Handle setCenter command"""
        return self._set_character_position('center', args.strip())
    
    def _handle_set_right(self, args: str) -> bool:
        """Handle setRight command"""
        return self._set_character_position('right', args.strip())
    
    def _set_character_position(self, position: str, character: str) -> bool:
        """Set character at specific position"""
        if not character or character.lower() == 'clear':
            self.character_positions[position] = None
            if self.visual_callback:
                self.visual_callback('character_clear', position)
            return True
        
        # Parse character name and emotion
        if '_' in character:
            char_name, emotion = character.split('_', 1)
        else:
            char_name = character
            emotion = 'neutral'
        
        # Resolve portrait
        portrait_path = self.asset_resolver.resolve_portrait(char_name, emotion)
        if portrait_path:
            self.character_positions[position] = {
                'character': char_name,
                'emotion': emotion,
                'portrait': portrait_path
            }
            if self.visual_callback:
                self.visual_callback('character_set', position, portrait_path)
            return True
        else:
            print(f"Portrait not found: {character}")
            return False
    
    def _handle_show_key_image(self, args: str) -> bool:
        """Handle showKeyImage command"""
        # Try to resolve as background first, then as direct path
        image_path = self.asset_resolver.resolve_background(args.strip())
        if not image_path:
            # Try direct path resolution
            image_path = args.strip()
        
        if image_path:
            self.key_image = image_path
            if self.visual_callback:
                self.visual_callback('key_image', image_path)
            return True
        else:
            print(f"Key image not found: {args}")
            return False
    
    def _handle_clear_key_image(self, args: str) -> bool:
        """Handle clearKeyImage command"""
        self.key_image = None
        if self.visual_callback:
            self.visual_callback('key_image_clear')
        return True
    
    def _handle_transition_effect(self, args: str) -> bool:
        """Handle transitionEffect command"""
        effect_name = args.strip()
        if self.visual_callback:
            self.visual_callback('transition', effect_name)
        return True
    
    def _handle_character_effect(self, args: str) -> bool:
        """Handle characterEffect command"""
        # Parse effect,position format
        parts = args.split(',')
        effect = parts[0].strip()
        position = parts[1].strip() if len(parts) > 1 else 'all'
        
        if self.visual_callback:
            self.visual_callback('character_effect', effect, position)
        return True
    
    def _handle_play_music(self, args: str) -> bool:
        """Handle playMusic command"""
        music_path = self.asset_resolver.resolve_music(args.strip())
        if music_path:
            self.current_music = music_path
            if self.audio_callback:
                self.audio_callback('play_music', music_path, True)  # Loop by default
            return True
        else:
            print(f"Music not found: {args}")
            return False
    
    def _handle_stop_music(self, args: str) -> bool:
        """Handle stopMusic command"""
        force = args.strip().lower() == 'force'
        self.current_music = None
        if self.audio_callback:
            self.audio_callback('stop_music', force)
        return True
    
    def _handle_cross_music(self, args: str) -> bool:
        """Handle crossMusic command"""
        music_path = self.asset_resolver.resolve_music(args.strip())
        if music_path:
            old_music = self.current_music
            self.current_music = music_path
            if self.audio_callback:
                self.audio_callback('cross_music', old_music, music_path)
            return True
        else:
            print(f"Music not found: {args}")
            return False
    
    def _handle_play_sound(self, args: str) -> bool:
        """Handle playSound command"""
        sound_path = self.asset_resolver.resolve_sound_effect(args.strip())
        if sound_path:
            if self.audio_callback:
                self.audio_callback('play_sound', sound_path)
            return True
        else:
            print(f"Sound effect not found: {args}")
            return False
    
    def _handle_signal(self, args: str) -> bool:
        """Handle signal command"""
        # Parse signal name and arguments
        parts = args.split(' ', 1)
        signal_name = parts[0].strip()
        signal_args = parts[1].strip() if len(parts) > 1 else ""
        
        # Parse arguments (simple space-separated for now)
        parsed_args = signal_args.split() if signal_args else []
        
        if self.signal_callback:
            self.signal_callback(signal_name, *parsed_args)
        else:
            # Fallback: emit globally
            print(f"Signal emitted: {signal_name} with args: {parsed_args}")
        
        return True
    
    def _handle_variable(self, args: str) -> bool:
        """Handle var command"""
        # Parse variable assignment: var_name = value
        if '=' not in args:
            print(f"Invalid variable assignment: {args}")
            return False
        
        var_name, value_str = args.split('=', 1)
        var_name = var_name.strip()
        value_str = value_str.strip()
        
        # Try to parse value as different types
        value = self._parse_value(value_str)
        
        # Set global variable
        if self.variables_manager:
            # Try to update existing variable
            existing_var = self.variables_manager.get_variable(var_name)
            if existing_var:
                return self.variables_manager.set_value(var_name, value)
            else:
                # Create new variable (default to string type)
                from core.globals.variables_manager import VariableType
                var_type = self._infer_variable_type(value)
                return self.variables_manager.add_variable(var_name, var_type, value)
        else:
            # Fallback to simple global variable setting
            return set_global_var(var_name, value)
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse a string value to appropriate Python type"""
        value_str = value_str.strip()
        
        # Remove quotes if present
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        
        # Try boolean
        if value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true'
        
        # Try integer
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Default to string
        return value_str
    
    def _infer_variable_type(self, value: Any):
        """Infer variable type from value"""
        from core.globals.variables_manager import VariableType
        
        if isinstance(value, bool):
            return VariableType.BOOL
        elif isinstance(value, int):
            return VariableType.INT
        elif isinstance(value, float):
            return VariableType.FLOAT
        else:
            return VariableType.STRING
    
    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate a conditional expression"""
        if not condition:
            return True
        
        try:
            # Simple condition evaluation
            # Support: var = value, var != value, var > value, var < value, var >= value, var <= value
            # Support: and, or operators
            
            # Replace variable names with their values
            condition = self._replace_variables_in_condition(condition)
            
            # Evaluate the condition
            return eval(condition)
            
        except Exception as e:
            print(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _replace_variables_in_condition(self, condition: str) -> str:
        """Replace variable names in condition with their values"""
        # Find all variable names (alphanumeric + underscore)
        var_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')
        
        def replace_var(match):
            var_name = match.group(1)
            # Skip Python keywords and operators
            if var_name in ['and', 'or', 'not', 'True', 'False', 'None']:
                return var_name
            
            # Get variable value
            value = get_global_var(var_name)
            if value is None:
                return '""'  # Default to empty string
            
            # Quote strings
            if isinstance(value, str):
                return f'"{value}"'
            else:
                return str(value)
        
        return var_pattern.sub(replace_var, condition)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current dialogue state"""
        return {
            'background': self.current_background,
            'music': self.current_music,
            'characters': self.character_positions.copy(),
            'key_image': self.key_image
        }
    
    def set_callbacks(self, signal_callback: Callable = None, 
                     scene_change_callback: Callable = None,
                     audio_callback: Callable = None,
                     visual_callback: Callable = None):
        """Set callback functions for different command types"""
        if signal_callback:
            self.signal_callback = signal_callback
        if scene_change_callback:
            self.scene_change_callback = scene_change_callback
        if audio_callback:
            self.audio_callback = audio_callback
        if visual_callback:
            self.visual_callback = visual_callback
    
    def register_external_command(self, command_name: str, handler: Callable):
        """Register an external command handler"""
        self.external_handlers[command_name] = handler
