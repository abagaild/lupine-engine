"""
OpenAL Audio System for Pygame-based Game Runner
Replaces Arcade's audio system with OpenAL for better performance and control
"""

import os
from pathlib import Path
from typing import Dict, Optional
import wave
import numpy as np

try:
    import openal
    from openal import al, alc
    OPENAL_AVAILABLE = True
except ImportError:
    print("OpenAL not available - audio will be disabled")
    OPENAL_AVAILABLE = False


class AudioBuffer:
    """OpenAL audio buffer wrapper"""
    
    def __init__(self, buffer_id: int, duration: float):
        self.id = buffer_id
        self.duration = duration


class AudioSource:
    """OpenAL audio source wrapper"""
    
    def __init__(self, source_id: int):
        self.id = source_id
        self.is_playing = False
        self.is_looping = False
        self.volume = 1.0
        self.pitch = 1.0
        self.position = [0.0, 0.0, 0.0]
    
    def play(self):
        """Play the audio source"""
        if OPENAL_AVAILABLE:
            al.alSourcePlay(self.id)
            self.is_playing = True
    
    def stop(self):
        """Stop the audio source"""
        if OPENAL_AVAILABLE:
            al.alSourceStop(self.id)
            self.is_playing = False
    
    def pause(self):
        """Pause the audio source"""
        if OPENAL_AVAILABLE:
            al.alSourcePause(self.id)
            self.is_playing = False
    
    def set_volume(self, volume: float):
        """Set source volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if OPENAL_AVAILABLE:
            al.alSourcef(self.id, al.AL_GAIN, self.volume)
    
    def set_pitch(self, pitch: float):
        """Set source pitch (0.5 to 2.0 typically)"""
        self.pitch = max(0.1, min(4.0, pitch))
        if OPENAL_AVAILABLE:
            al.alSourcef(self.id, al.AL_PITCH, self.pitch)
    
    def set_looping(self, loop: bool):
        """Set whether the source should loop"""
        self.is_looping = loop
        if OPENAL_AVAILABLE:
            al.alSourcei(self.id, al.AL_LOOPING, al.AL_TRUE if loop else al.AL_FALSE)
    
    def set_position(self, x: float, y: float, z: float = 0.0):
        """Set 3D position of the source"""
        self.position = [x, y, z]
        if OPENAL_AVAILABLE:
            al.alSource3f(self.id, al.AL_POSITION, x, y, z)
    
    def update_state(self):
        """Update playing state from OpenAL"""
        if OPENAL_AVAILABLE:
            state = al.alGetSourcei(self.id, al.AL_SOURCE_STATE)
            self.is_playing = (state == al.AL_PLAYING)


class OpenALAudioSystem:
    """OpenAL-based audio system"""
    
    def __init__(self):
        self.device = None
        self.context = None
        self.buffers: Dict[str, AudioBuffer] = {}
        self.sources: Dict[str, AudioSource] = {}
        self.available_sources = []
        self.master_volume = 1.0
        
        if OPENAL_AVAILABLE:
            self.initialize()
    
    def initialize(self):
        """Initialize OpenAL"""
        try:
            # Open default audio device
            self.device = alc.alcOpenDevice(None)
            if not self.device:
                print("Failed to open OpenAL device")
                return False
            
            # Create audio context
            self.context = alc.alcCreateContext(self.device, None)
            if not self.context:
                print("Failed to create OpenAL context")
                return False
            
            # Make context current
            alc.alcMakeContextCurrent(self.context)
            
            # Set listener properties
            al.alListener3f(al.AL_POSITION, 0.0, 0.0, 0.0)
            al.alListener3f(al.AL_VELOCITY, 0.0, 0.0, 0.0)
            # Fix OpenAL orientation parameter - needs to be a ctypes array
            import ctypes
            orientation = (ctypes.c_float * 6)(0.0, 0.0, -1.0, 0.0, 1.0, 0.0)
            al.alListenerfv(al.AL_ORIENTATION, orientation)
            
            # Pre-create some audio sources for efficiency
            for i in range(32):  # 32 simultaneous sounds should be enough
                source_id = al.alGenSources(1)
                if source_id:
                    self.available_sources.append(source_id)
            
            print(f"OpenAL initialized with {len(self.available_sources)} sources")
            return True
            
        except Exception as e:
            print(f"Failed to initialize OpenAL: {e}")
            return False
    
    def load_sound(self, path: str) -> Optional[AudioBuffer]:
        """Load a sound file into an OpenAL buffer"""
        if not OPENAL_AVAILABLE or path in self.buffers:
            return self.buffers.get(path)
        
        try:
            # For now, only support WAV files
            if not path.lower().endswith('.wav'):
                print(f"Unsupported audio format: {path}")
                return None
            
            # Load WAV file
            with wave.open(path, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                duration = wav_file.getnframes() / sample_rate
            
            # Determine OpenAL format
            if channels == 1:
                if sample_width == 1:
                    al_format = al.AL_FORMAT_MONO8
                elif sample_width == 2:
                    al_format = al.AL_FORMAT_MONO16
                else:
                    print(f"Unsupported sample width: {sample_width}")
                    return None
            elif channels == 2:
                if sample_width == 1:
                    al_format = al.AL_FORMAT_STEREO8
                elif sample_width == 2:
                    al_format = al.AL_FORMAT_STEREO16
                else:
                    print(f"Unsupported sample width: {sample_width}")
                    return None
            else:
                print(f"Unsupported channel count: {channels}")
                return None
            
            # Create OpenAL buffer
            buffer_id = al.alGenBuffers(1)
            al.alBufferData(buffer_id, al_format, frames, len(frames), sample_rate)
            
            audio_buffer = AudioBuffer(buffer_id, duration)
            self.buffers[path] = audio_buffer
            return audio_buffer
            
        except Exception as e:
            print(f"Failed to load sound {path}: {e}")
            return None
    
    def play_sound(self, path: str, volume: float = 1.0, pitch: float = 1.0, 
                   loop: bool = False, x: float = 0.0, y: float = 0.0) -> Optional[AudioSource]:
        """Play a sound effect"""
        if not OPENAL_AVAILABLE:
            return None
        
        # Load sound if not already loaded
        audio_buffer = self.load_sound(path)
        if not audio_buffer:
            return None
        
        # Get an available source
        if not self.available_sources:
            print("No available audio sources")
            return None
        
        source_id = self.available_sources.pop(0)
        
        # Configure source
        al.alSourcei(source_id, al.AL_BUFFER, audio_buffer.id)
        al.alSourcef(source_id, al.AL_GAIN, volume * self.master_volume)
        al.alSourcef(source_id, al.AL_PITCH, pitch)
        al.alSourcei(source_id, al.AL_LOOPING, al.AL_TRUE if loop else al.AL_FALSE)
        al.alSource3f(source_id, al.AL_POSITION, x, y, 0.0)
        
        # Create source wrapper
        source = AudioSource(source_id)
        source.set_volume(volume)
        source.set_pitch(pitch)
        source.set_looping(loop)
        source.set_position(x, y, 0.0)
        
        # Play the source
        source.play()
        
        # Store source with a unique key
        source_key = f"{path}_{id(source)}"
        self.sources[source_key] = source
        
        return source
    
    def update(self):
        """Update audio system - call this every frame"""
        if not OPENAL_AVAILABLE:
            return
        
        # Update source states and clean up finished sources
        finished_sources = []
        
        for key, source in self.sources.items():
            source.update_state()
            
            if not source.is_playing and not source.is_looping:
                finished_sources.append(key)
        
        # Clean up finished sources
        for key in finished_sources:
            source = self.sources.pop(key)
            # Return source to available pool
            al.alSourcei(source.id, al.AL_BUFFER, 0)  # Detach buffer
            self.available_sources.append(source.id)
    
    def set_master_volume(self, volume: float):
        """Set master volume for all audio"""
        self.master_volume = max(0.0, min(1.0, volume))
        al.alListenerf(al.AL_GAIN, self.master_volume)
    
    def set_listener_position(self, x: float, y: float, z: float = 0.0):
        """Set 3D position of the audio listener (usually the camera/player)"""
        if OPENAL_AVAILABLE:
            al.alListener3f(al.AL_POSITION, x, y, z)
    
    def cleanup(self):
        """Clean up OpenAL resources"""
        if not OPENAL_AVAILABLE:
            return
        
        # Stop all sources
        for source in self.sources.values():
            source.stop()
        
        # Delete sources
        all_sources = list(self.sources.values()) + [AudioSource(sid) for sid in self.available_sources]
        source_ids = [s.id for s in all_sources]
        if source_ids:
            al.alDeleteSources(len(source_ids), source_ids)
        
        # Delete buffers
        buffer_ids = [b.id for b in self.buffers.values()]
        if buffer_ids:
            al.alDeleteBuffers(len(buffer_ids), buffer_ids)
        
        # Clean up context and device
        if self.context:
            alc.alcMakeContextCurrent(None)
            alc.alcDestroyContext(self.context)
        
        if self.device:
            alc.alcCloseDevice(self.device)
        
        print("OpenAL audio system cleaned up")
