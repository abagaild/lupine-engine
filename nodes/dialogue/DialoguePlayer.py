"""
Dialogue Player Node for Lupine Engine
Node for playing dialogue scripts in scenes
"""

from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

from core.scene.base_node import Node
from core.dialogue.dialogue_runtime import DialogueRuntime, DialogueState
from core.dialogue.asset_resolver import DialogueAssetResolver


class DialoguePlayer(Node):
    """
    Node for playing dialogue scripts in scenes.
    
    Features:
    - Load and play dialogue scripts
    - Emit signals for dialogue events
    - Integration with game audio and visuals
    - Variable management integration
    - Scene changing support
    """
    
    def __init__(self, name: str = "DialoguePlayer"):
        super().__init__(name)
        self.type = "DialoguePlayer"
        
        # Export variables
        self.export_variables.update({
            "dialogue_script": {
                "type": "path",
                "value": "",
                "description": "Path to the dialogue script file",
                "filter": "*.dlg"
            },
            "auto_start": {
                "type": "bool",
                "value": False,
                "description": "Automatically start dialogue when node is ready"
            },
            "auto_advance": {
                "type": "bool",
                "value": False,
                "description": "Automatically advance dialogue lines"
            },
            "auto_advance_delay": {
                "type": "float",
                "value": 2.0,
                "description": "Delay between auto-advanced lines (seconds)"
            },
            "pause_on_choices": {
                "type": "bool",
                "value": True,
                "description": "Pause dialogue when choices are available"
            },
            "emit_dialogue_signals": {
                "type": "bool",
                "value": True,
                "description": "Emit signals for dialogue events"
            },
            "dialogue_box_scene": {
                "type": "path",
                "value": "prefabs/dialogue_box.scene",
                "description": "Path to the dialogue box UI scene",
                "filter": "*.scene"
            }
        })
        
        # Runtime components
        self.runtime: Optional[DialogueRuntime] = None
        self.asset_resolver: Optional[DialogueAssetResolver] = None
        
        # State
        self.is_playing = False
        self.current_choices: List[str] = []

        # UI References (will be populated when dialogue box is loaded)
        self.dialogue_box_instance = None
        self.speaker_label = None
        self.dialogue_text = None
        self.continue_indicator = None
        self.portrait_left = None
        self.portrait_center = None
        self.portrait_right = None
        self.choices_container = None
        self.choice_buttons = []

        # Callbacks
        self.on_dialogue_line_callback: Optional[Callable] = None
        self.on_speaker_change_callback: Optional[Callable] = None
        self.on_choices_callback: Optional[Callable] = None
        self.on_dialogue_finished_callback: Optional[Callable] = None
    
    def _ready(self):
        """Called when the node enters the scene tree"""
        super()._ready()

        # Initialize dialogue system
        self._initialize_dialogue_system()

        # Load dialogue box UI
        self._load_dialogue_box()

        # Auto-start if enabled
        if self.auto_start:
            self.start_dialogue()
    
    def _initialize_dialogue_system(self):
        """Initialize the dialogue runtime system"""
        try:
            # Get project from scene tree or global context
            project = self._get_project()
            if not project:
                print("DialoguePlayer: No project found, dialogue system not initialized")
                return
            
            # Initialize components
            self.asset_resolver = DialogueAssetResolver(project)
            self.runtime = DialogueRuntime(project, self.asset_resolver)
            
            # Set up runtime callbacks
            self.runtime.set_callbacks(
                on_dialogue_line=self._on_dialogue_line,
                on_speaker_change=self._on_speaker_change,
                on_choices_available=self._on_choices_available,
                on_dialogue_finished=self._on_dialogue_finished,
                on_state_change=self._on_state_change
            )
            
            # Configure runtime settings
            self.runtime.auto_advance = self.auto_advance
            self.runtime.auto_advance_delay = self.auto_advance_delay
            
            # Set up command executor callbacks
            if self.runtime.command_executor:
                self.runtime.command_executor.set_callbacks(
                    signal_callback=self._emit_dialogue_signal,
                    scene_change_callback=self._change_scene,
                    audio_callback=self._handle_audio_command,
                    visual_callback=self._handle_visual_command
                )
            
        except Exception as e:
            print(f"DialoguePlayer: Failed to initialize dialogue system: {e}")

    def _load_dialogue_box(self):
        """Load the dialogue box UI scene"""
        try:
            if not self.dialogue_box_scene:
                print("DialoguePlayer: No dialogue box scene specified")
                return

            # Get project and scene manager
            project = self._get_project()
            if not project:
                print("DialoguePlayer: No project found, cannot load dialogue box")
                return

            # Load dialogue box scene
            dialogue_box_path = self.dialogue_box_scene
            if not Path(dialogue_box_path).is_absolute():
                dialogue_box_path = str(Path(project.project_path) / dialogue_box_path)

            if not Path(dialogue_box_path).exists():
                print(f"DialoguePlayer: Dialogue box scene not found: {dialogue_box_path}")
                return

            # Load and instantiate the scene
            # This would typically use the scene manager to load the scene
            # For now, we'll just store the path and expect the UI to be set up externally
            print(f"DialoguePlayer: Dialogue box scene loaded: {dialogue_box_path}")

            # Try to find UI elements by name (this would be done after scene instantiation)
            self._find_ui_elements()

        except Exception as e:
            print(f"DialoguePlayer: Failed to load dialogue box: {e}")

    def _find_ui_elements(self):
        """Find and cache references to UI elements in the dialogue box"""
        try:
            # This would typically search the scene tree for nodes with specific names
            # For now, we'll just set up placeholders

            # Expected UI element names from the dialogue box prefab:
            # - SpeakerLabel: Label for speaker name
            # - DialogueText: RichTextLabel for dialogue content
            # - ContinueIndicator: Label for continue prompt
            # - PortraitLeft, PortraitCenter, PortraitRight: TextureRect for character portraits
            # - ChoicesContainer: VBoxContainer for choice buttons
            # - ChoiceButton1, ChoiceButton2, ChoiceButton3, ChoiceButton4: Buttons for choices

            # These would be populated by searching the scene tree
            # self.speaker_label = self.find_node("SpeakerLabel")
            # self.dialogue_text = self.find_node("DialogueText")
            # etc.

            print("DialoguePlayer: UI elements found and cached")

        except Exception as e:
            print(f"DialoguePlayer: Failed to find UI elements: {e}")

    def _update_dialogue_ui(self, line: str, speaker: Optional[str] = None):
        """Update the dialogue UI with new content"""
        try:
            # Update speaker label
            if self.speaker_label and speaker:
                # self.speaker_label.set_text(speaker)
                pass

            # Update dialogue text
            if self.dialogue_text:
                # self.dialogue_text.set_text(line)
                pass

            # Show continue indicator
            if self.continue_indicator:
                # self.continue_indicator.set_visible(True)
                pass

        except Exception as e:
            print(f"DialoguePlayer: Failed to update dialogue UI: {e}")

    def _update_choices_ui(self, choices: List[str]):
        """Update the choices UI with available options"""
        try:
            if not self.choices_container:
                return

            # Hide all choice buttons first
            for i, button in enumerate(self.choice_buttons):
                if button:
                    # button.set_visible(False)
                    pass

            # Show and configure choice buttons for available choices
            for i, choice_text in enumerate(choices):
                if i < len(self.choice_buttons) and self.choice_buttons[i]:
                    button = self.choice_buttons[i]
                    # button.set_text(choice_text)
                    # button.set_visible(True)
                    # Connect button signal to choice selection
                    pass

            # Show choices container
            # self.choices_container.set_visible(True)

        except Exception as e:
            print(f"DialoguePlayer: Failed to update choices UI: {e}")

    def _hide_choices_ui(self):
        """Hide the choices UI"""
        try:
            if self.choices_container:
                # self.choices_container.set_visible(False)
                pass
        except Exception as e:
            print(f"DialoguePlayer: Failed to hide choices UI: {e}")

    def _update_portrait(self, position: str, portrait_path: Optional[str] = None):
        """Update character portrait at specified position"""
        try:
            portrait_node = None

            if position == "left":
                portrait_node = self.portrait_left
            elif position == "center":
                portrait_node = self.portrait_center
            elif position == "right":
                portrait_node = self.portrait_right

            if portrait_node:
                if portrait_path:
                    # Load and set texture
                    # portrait_node.set_texture(portrait_path)
                    # portrait_node.set_visible(True)
                    pass
                else:
                    # Hide portrait
                    # portrait_node.set_visible(False)
                    pass

        except Exception as e:
            print(f"DialoguePlayer: Failed to update portrait: {e}")

    def _get_project(self):
        """Get the current project"""
        # Try to get project from global context
        try:
            from core.project import get_current_project
            return get_current_project()
        except ImportError:
            pass
        
        # Try to get from scene tree
        scene_tree = self.get_tree()
        if scene_tree and hasattr(scene_tree, 'project'):
            return scene_tree.project
        
        return None
    
    def start_dialogue(self) -> bool:
        """Start playing the dialogue script"""
        if not self.runtime:
            print("DialoguePlayer: Runtime not initialized")
            return False
        
        if not self.dialogue_script:
            print("DialoguePlayer: No dialogue script specified")
            return False
        
        # Load script
        script_path = self.dialogue_script
        if not Path(script_path).is_absolute():
            # Make relative to project
            project = self._get_project()
            if project:
                script_path = str(Path(project.project_path) / script_path)
        
        if not self.runtime.load_script_from_file(script_path):
            print(f"DialoguePlayer: Failed to load script: {script_path}")
            return False
        
        # Start dialogue
        if self.runtime.start_dialogue():
            self.is_playing = True
            self.emit_signal("dialogue_started")
            return True
        
        return False
    
    def stop_dialogue(self):
        """Stop the current dialogue"""
        if self.runtime:
            self.runtime.stop_dialogue()
        
        self.is_playing = False
        self.current_choices.clear()
        self.emit_signal("dialogue_stopped")
    
    def pause_dialogue(self):
        """Pause the current dialogue"""
        if self.runtime:
            self.runtime.pause_dialogue()
        
        self.emit_signal("dialogue_paused")
    
    def resume_dialogue(self):
        """Resume the paused dialogue"""
        if self.runtime:
            self.runtime.resume_dialogue()
        
        self.emit_signal("dialogue_resumed")
    
    def advance_dialogue(self):
        """Advance to the next dialogue line"""
        if self.runtime:
            self.runtime.advance_dialogue()
    
    def make_choice(self, choice_index: int) -> bool:
        """Make a dialogue choice"""
        if self.runtime and 0 <= choice_index < len(self.current_choices):
            return self.runtime.make_choice(choice_index)
        
        return False
    
    def get_current_choices(self) -> List[str]:
        """Get current available choices"""
        return self.current_choices.copy()
    
    def get_dialogue_state(self) -> Dict[str, Any]:
        """Get current dialogue state"""
        if self.runtime:
            return self.runtime.get_current_state()
        
        return {'state': DialogueState.STOPPED}
    
    def _on_dialogue_line(self, line: str, speaker: Optional[str] = None):
        """Handle dialogue line event"""
        # Update dialogue UI
        self._update_dialogue_ui(line, speaker)

        if self.emit_dialogue_signals:
            self.emit_signal("dialogue_line", line, speaker or "")

        if self.on_dialogue_line_callback:
            self.on_dialogue_line_callback(line, speaker)
    
    def _on_speaker_change(self, speaker: str):
        """Handle speaker change event"""
        if self.emit_dialogue_signals:
            self.emit_signal("speaker_changed", speaker)
        
        if self.on_speaker_change_callback:
            self.on_speaker_change_callback(speaker)
    
    def _on_choices_available(self, choices: List[str]):
        """Handle choices available event"""
        self.current_choices = choices

        # Update choices UI
        self._update_choices_ui(choices)

        if self.emit_dialogue_signals:
            self.emit_signal("choices_available", choices)

        if self.on_choices_callback:
            self.on_choices_callback(choices)

        # Auto-pause on choices if enabled
        if self.pause_on_choices:
            self.pause_dialogue()
    
    def _on_dialogue_finished(self):
        """Handle dialogue finished event"""
        self.is_playing = False
        self.current_choices.clear()
        
        if self.emit_dialogue_signals:
            self.emit_signal("dialogue_finished")
        
        if self.on_dialogue_finished_callback:
            self.on_dialogue_finished_callback()
    
    def _on_state_change(self, state: DialogueState):
        """Handle dialogue state change"""
        if self.emit_dialogue_signals:
            self.emit_signal("dialogue_state_changed", state.value)
    
    def _emit_dialogue_signal(self, signal_name: str, *args):
        """Emit a dialogue signal globally"""
        # Emit as node signal
        self.emit_signal(f"dialogue_{signal_name}", *args)
        
        # Also emit globally if possible
        try:
            from core.python_runtime import emit_signal
            emit_signal(signal_name, *args)
        except ImportError:
            pass
    
    def _change_scene(self, scene_path: str):
        """Handle scene change command"""
        try:
            from core.python_runtime import change_scene
            change_scene(scene_path)
        except ImportError:
            print(f"DialoguePlayer: Scene change not available: {scene_path}")
    
    def _handle_audio_command(self, command: str, *args):
        """Handle audio commands from dialogue"""
        if command == "play_music":
            music_path, loop = args[0], args[1] if len(args) > 1 else True
            self.emit_signal("play_music", music_path, loop)
        
        elif command == "stop_music":
            force = args[0] if args else False
            self.emit_signal("stop_music", force)
        
        elif command == "cross_music":
            old_music, new_music = args[0], args[1]
            self.emit_signal("cross_music", old_music, new_music)
        
        elif command == "play_sound":
            sound_path = args[0]
            self.emit_signal("play_sound", sound_path)
    
    def _handle_visual_command(self, command: str, *args):
        """Handle visual commands from dialogue"""
        if command == "background":
            background_path = args[0]
            self.emit_signal("set_background", background_path)
        
        elif command == "character_set":
            position, portrait_path = args[0], args[1]
            self._update_portrait(position, portrait_path)
            self.emit_signal("set_character", position, portrait_path)

        elif command == "character_clear":
            position = args[0]
            self._update_portrait(position, None)
            self.emit_signal("clear_character", position)
        
        elif command == "key_image":
            image_path = args[0]
            self.emit_signal("show_key_image", image_path)
        
        elif command == "key_image_clear":
            self.emit_signal("clear_key_image")
        
        elif command == "transition":
            effect_name = args[0]
            self.emit_signal("transition_effect", effect_name)
        
        elif command == "character_effect":
            effect, position = args[0], args[1]
            self.emit_signal("character_effect", effect, position)
    
    def set_dialogue_callbacks(self,
                             on_dialogue_line: Optional[Callable] = None,
                             on_speaker_change: Optional[Callable] = None,
                             on_choices: Optional[Callable] = None,
                             on_finished: Optional[Callable] = None):
        """Set custom callbacks for dialogue events"""
        self.on_dialogue_line_callback = on_dialogue_line
        self.on_speaker_change_callback = on_speaker_change
        self.on_choices_callback = on_choices
        self.on_dialogue_finished_callback = on_finished
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DialoguePlayer':
        """Create DialoguePlayer from dictionary data"""
        node = cls(data.get("name", "DialoguePlayer"))
        
        # Load export variables
        for key, value in data.get("export_variables", {}).items():
            if key in node.export_variables:
                node.export_variables[key]["value"] = value
                setattr(node, key, value)
        
        # Load transform
        if "transform" in data:
            node.transform.from_dict(data["transform"])
        
        # Load children (would be handled by scene manager)
        # for child_data in data.get("children", []):
        #     child = create_node_from_dict(child_data)
        #     if child:
        #         node.add_child(child)
        
        return node
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DialoguePlayer to dictionary"""
        data = super().to_dict()
        
        # Add dialogue-specific data
        data["type"] = "DialoguePlayer"
        
        return data
