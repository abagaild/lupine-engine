"""
Audio System for Lupine Engine
OpenAL-based audio management for the game engine
"""

import os
import wave
from typing import Dict, Optional, Tuple
from pathlib import Path

try:
    import openal
    OPENAL_AVAILABLE = True
except ImportError:
    OPENAL_AVAILABLE = False
    print("Warning: OpenAL not available. Audio features will be disabled.")


class AudioManager:
    """Manages audio playback using OpenAL"""
    
    def __init__(self):
        self.device = None
        self.context = None
        self.sources = {}  # source_id -> source
        self.buffers = {}  # file_path -> buffer
        self.master_volume = 1.0
        self.music_volume = 0.8
        self.sfx_volume = 1.0
        
        if OPENAL_AVAILABLE:
            self.initialize()
    
    def initialize(self) -> bool:
        """Initialize OpenAL"""
        if not OPENAL_AVAILABLE:
            return False
        
        try:
            # Open default device (pass empty string for default device instead of None)
            self.device = openal.oalOpen("")
            if not self.device:
                print("Failed to open OpenAL device")
                return False
            
            # Create context
            self.context = openal.oalCreateContext(self.device, None)
            if not self.context:
                print("Failed to create OpenAL context")
                return False
            
            # Make context current
            openal.oalMakeContextCurrent(self.context)
            
            print("OpenAL initialized successfully")
            return True
            
        except Exception as e:
            print(f"Failed to initialize OpenAL: {e}")
            return False
    
    def shutdown(self):
        """Shutdown OpenAL"""
        if not OPENAL_AVAILABLE:
            return
        
        try:
            # Stop all sources
            for source in self.sources.values():
                openal.oalSourceStop(source)
                openal.oalDeleteSources([source])
            
            # Delete all buffers
            for buffer in self.buffers.values():
                openal.oalDeleteBuffers([buffer])
            
            # Cleanup context and device
            if self.context:
                openal.oalMakeContextCurrent(None)
                openal.oalDestroyContext(self.context)
            
            if self.device:
                openal.oalClose(self.device)
            
            print("OpenAL shutdown complete")
            
        except Exception as e:
            print(f"Error during OpenAL shutdown: {e}")
    
    def load_audio_file(self, file_path: str) -> Optional[int]:
        """Load an audio file and return buffer ID"""
        if not OPENAL_AVAILABLE:
            return None
        
        file_path = str(Path(file_path))
        
        # Check if already loaded
        if file_path in self.buffers:
            return self.buffers[file_path]
        
        try:
            # Load WAV file (basic implementation)
            if file_path.lower().endswith('.wav'):
                buffer = self.load_wav_file(file_path)
                if buffer:
                    self.buffers[file_path] = buffer
                    return buffer
            else:
                print(f"Unsupported audio format: {file_path}")
                return None
                
        except Exception as e:
            print(f"Failed to load audio file {file_path}: {e}")
            return None
    
    def load_wav_file(self, file_path: str) -> Optional[int]:
        """Load a WAV file"""
        try:
            with wave.open(file_path, 'rb') as wav_file:
                # Get audio properties
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                sample_rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                
                # Read audio data
                audio_data = wav_file.readframes(frames)
                
                # Determine OpenAL format
                if channels == 1:
                    if sample_width == 1:
                        format = openal.AL_FORMAT_MONO8
                    elif sample_width == 2:
                        format = openal.AL_FORMAT_MONO16
                    else:
                        print(f"Unsupported sample width: {sample_width}")
                        return None
                elif channels == 2:
                    if sample_width == 1:
                        format = openal.AL_FORMAT_STEREO8
                    elif sample_width == 2:
                        format = openal.AL_FORMAT_STEREO16
                    else:
                        print(f"Unsupported sample width: {sample_width}")
                        return None
                else:
                    print(f"Unsupported channel count: {channels}")
                    return None
                
                # Create OpenAL buffer
                buffer = openal.oalGenBuffers(1)[0]
                openal.oalBufferData(buffer, format, audio_data, len(audio_data), sample_rate)
                
                return buffer
                
        except Exception as e:
            print(f"Error loading WAV file {file_path}: {e}")
            return None
    
    def create_source(self, source_id: str) -> Optional[int]:
        """Create an audio source"""
        if not OPENAL_AVAILABLE:
            return None
        
        try:
            source = openal.oalGenSources(1)[0]
            self.sources[source_id] = source
            
            # Set default properties
            openal.oalSourcef(source, openal.AL_PITCH, 1.0)
            openal.oalSourcef(source, openal.AL_GAIN, 1.0)
            openal.oalSource3f(source, openal.AL_POSITION, 0.0, 0.0, 0.0)
            openal.oalSource3f(source, openal.AL_VELOCITY, 0.0, 0.0, 0.0)
            openal.oalSourcei(source, openal.AL_LOOPING, openal.AL_FALSE)
            
            return source
            
        except Exception as e:
            print(f"Failed to create audio source {source_id}: {e}")
            return None
    
    def play_sound(self, source_id: str, file_path: str, loop: bool = False, volume: float = 1.0):
        """Play a sound"""
        if not OPENAL_AVAILABLE:
            return
        
        # Load audio file
        buffer = self.load_audio_file(file_path)
        if not buffer:
            return
        
        # Get or create source
        if source_id not in self.sources:
            self.create_source(source_id)
        
        source = self.sources.get(source_id)
        if not source:
            return
        
        try:
            # Stop current playback
            openal.oalSourceStop(source)
            
            # Set buffer
            openal.oalSourcei(source, openal.AL_BUFFER, buffer)
            
            # Set properties
            openal.oalSourcei(source, openal.AL_LOOPING, openal.AL_TRUE if loop else openal.AL_FALSE)
            openal.oalSourcef(source, openal.AL_GAIN, volume * self.sfx_volume * self.master_volume)
            
            # Play
            openal.oalSourcePlay(source)
            
        except Exception as e:
            print(f"Failed to play sound {file_path}: {e}")
    
    def play_music(self, file_path: str, loop: bool = True, volume: float = 1.0):
        """Play background music"""
        self.play_sound("music", file_path, loop, volume * self.music_volume)
    
    def stop_sound(self, source_id: str):
        """Stop a sound"""
        if not OPENAL_AVAILABLE:
            return
        
        source = self.sources.get(source_id)
        if source:
            try:
                openal.oalSourceStop(source)
            except Exception as e:
                print(f"Failed to stop sound {source_id}: {e}")
    
    def stop_music(self):
        """Stop background music"""
        self.stop_sound("music")
    
    def pause_sound(self, source_id: str):
        """Pause a sound"""
        if not OPENAL_AVAILABLE:
            return
        
        source = self.sources.get(source_id)
        if source:
            try:
                openal.oalSourcePause(source)
            except Exception as e:
                print(f"Failed to pause sound {source_id}: {e}")
    
    def resume_sound(self, source_id: str):
        """Resume a paused sound"""
        if not OPENAL_AVAILABLE:
            return
        
        source = self.sources.get(source_id)
        if source:
            try:
                openal.oalSourcePlay(source)
            except Exception as e:
                print(f"Failed to resume sound {source_id}: {e}")
    
    def set_master_volume(self, volume: float):
        """Set master volume (0.0 to 1.0)"""
        self.master_volume = max(0.0, min(1.0, volume))
        
        # Update all playing sources
        for source in self.sources.values():
            try:
                current_gain = openal.oalGetSourcef(source, openal.AL_GAIN)
                # This is a simplified approach - in practice you'd want to track original volumes
                openal.oalSourcef(source, openal.AL_GAIN, current_gain)
            except:
                pass
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
    
    def set_sfx_volume(self, volume: float):
        """Set sound effects volume (0.0 to 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))
    
    def is_playing(self, source_id: str) -> bool:
        """Check if a source is currently playing"""
        if not OPENAL_AVAILABLE:
            return False
        
        source = self.sources.get(source_id)
        if source:
            try:
                state = openal.oalGetSourcei(source, openal.AL_SOURCE_STATE)
                return state == openal.AL_PLAYING
            except:
                return False
        return False
    
    def set_listener_position(self, x: float, y: float, z: float = 0.0):
        """Set 3D listener position"""
        if not OPENAL_AVAILABLE:
            return
        
        try:
            openal.oalListener3f(openal.AL_POSITION, x, y, z)
        except Exception as e:
            print(f"Failed to set listener position: {e}")
    
    def set_source_position(self, source_id: str, x: float, y: float, z: float = 0.0):
        """Set 3D source position"""
        if not OPENAL_AVAILABLE:
            return
        
        source = self.sources.get(source_id)
        if source:
            try:
                openal.oalSource3f(source, openal.AL_POSITION, x, y, z)
            except Exception as e:
                print(f"Failed to set source position: {e}")


# Global audio manager instance
audio_manager = AudioManager()
