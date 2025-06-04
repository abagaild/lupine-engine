"""
Timer node implementation for Lupine Engine
Provides timing functionality with signals and callbacks
"""

from nodes.base.Node import Node
from typing import Dict, Any, Optional
import time


class Timer(Node):
    """
    Timer node for handling time-based events and delays.
    
    Features:
    - Configurable wait time
    - One-shot or repeating timers
    - Autostart capability
    - Pause and resume functionality
    - Timeout signal emission
    - Process mode awareness
    """
    
    def __init__(self, name: str = "Timer"):
        super().__init__(name)
        self.type = "Timer"
        
        # Export variables for editor
        self.export_variables = {
            "wait_time": {
                "type": "float",
                "value": 1.0,
                "min": 0.001,
                "description": "Time to wait before timeout (in seconds)"
            },
            "one_shot": {
                "type": "bool",
                "value": False,
                "description": "If true, timer stops after first timeout"
            },
            "autostart": {
                "type": "bool",
                "value": False,
                "description": "If true, timer starts automatically when entering tree"
            },
            "paused": {
                "type": "bool",
                "value": False,
                "description": "If true, timer is paused"
            }
        }
        
        # Timer properties
        self.wait_time: float = 1.0
        self.one_shot: bool = False
        self.autostart: bool = False
        self.paused: bool = False
        
        # Internal state
        self._time_left: float = 0.0
        self._started: bool = False
        self._last_process_time: Optional[float] = None
        
        # Built-in signals
        self.add_signal("timeout")
    
    def _ready(self):
        """Called when the timer enters the scene tree"""
        super()._ready()
        
        if self.autostart:
            self.start()
    
    def _process(self, delta: float):
        """Process the timer countdown"""
        super()._process(delta)
        
        if not self._started or self.paused:
            return
        
        # Update time left
        self._time_left -= delta
        
        # Check for timeout
        if self._time_left <= 0.0:
            self._timeout()
    
    def start(self, time_sec: Optional[float] = None):
        """
        Start the timer with optional custom wait time.
        
        Args:
            time_sec: Custom wait time. If None, uses wait_time property.
        """
        if time_sec is not None:
            self._time_left = max(0.001, time_sec)
        else:
            self._time_left = max(0.001, self.wait_time)
        
        self._started = True
        self.paused = False
        self._last_process_time = time.time()
    
    def stop(self):
        """Stop the timer and reset time left"""
        self._started = False
        self._time_left = 0.0
        self._last_process_time = None
    
    def pause(self):
        """Pause the timer without resetting time left"""
        self.paused = True
    
    def resume(self):
        """Resume a paused timer"""
        if self._started:
            self.paused = False
            self._last_process_time = time.time()
    
    def is_stopped(self) -> bool:
        """Check if the timer is stopped"""
        return not self._started
    
    def is_paused(self) -> bool:
        """Check if the timer is paused"""
        return self.paused
    
    def get_time_left(self) -> float:
        """Get the remaining time before timeout"""
        return max(0.0, self._time_left)
    
    def set_wait_time(self, time_sec: float):
        """Set the wait time for the timer"""
        self.wait_time = max(0.001, time_sec)
        
        # If timer is running and new time is shorter, adjust time left
        if self._started and self._time_left > self.wait_time:
            self._time_left = self.wait_time
    
    def get_wait_time(self) -> float:
        """Get the wait time for the timer"""
        return self.wait_time
    
    def set_one_shot(self, one_shot: bool):
        """Set whether the timer is one-shot"""
        self.one_shot = one_shot
    
    def is_one_shot(self) -> bool:
        """Check if the timer is one-shot"""
        return self.one_shot
    
    def set_autostart(self, autostart: bool):
        """Set whether the timer autostarts"""
        self.autostart = autostart
    
    def is_autostart(self) -> bool:
        """Check if the timer autostarts"""
        return self.autostart
    
    def get_progress(self) -> float:
        """Get the progress of the timer (0.0 to 1.0)"""
        if self.wait_time <= 0:
            return 1.0
        
        elapsed = self.wait_time - self._time_left
        return min(1.0, max(0.0, elapsed / self.wait_time))
    
    def get_elapsed_time(self) -> float:
        """Get the elapsed time since the timer started"""
        if not self._started:
            return 0.0
        
        return self.wait_time - self._time_left
    
    def restart(self):
        """Restart the timer with the current wait_time"""
        self.start()
    
    def _timeout(self):
        """Handle timer timeout"""
        # Emit timeout signal
        self.emit_signal("timeout")
        
        # Call script's timeout method if available
        if self.script_instance and hasattr(self.script_instance, 'call_method'):
            try:
                if self.script_instance.has_method('_on_timeout'):
                    self.script_instance.call_method('_on_timeout')
                elif self.script_instance.has_method('on_timeout'):
                    self.script_instance.call_method('on_timeout')
            except Exception as e:
                print(f"Error calling timeout method in {self.script_path}: {e}")
                import traceback
                traceback.print_exc()
        
        # Handle one-shot vs repeating
        if self.one_shot:
            self.stop()
        else:
            # Restart for repeating timer
            self._time_left = self.wait_time
    
    def connect_timeout(self, target_node: "Node", method_name: str):
        """Convenience method to connect timeout signal"""
        self.connect("timeout", target_node, method_name)
    
    def disconnect_timeout(self, target_node: "Node", method_name: str):
        """Convenience method to disconnect timeout signal"""
        self.disconnect("timeout", target_node, method_name)
    
    def create_tween_timer(self, duration: float, callback=None) -> "Timer":
        """
        Create a one-shot timer for tween-like functionality.
        
        Args:
            duration: Duration in seconds
            callback: Optional callback function to call on timeout
            
        Returns:
            The timer instance for chaining
        """
        self.set_wait_time(duration)
        self.set_one_shot(True)
        
        if callback:
            # Store callback for later execution
            self._tween_callback = callback
        
        self.start()
        return self
    
    def _handle_tween_callback(self):
        """Handle tween callback if set"""
        if hasattr(self, '_tween_callback') and self._tween_callback:
            try:
                self._tween_callback()
            except Exception as e:
                print(f"Error calling tween callback: {e}")
            finally:
                self._tween_callback = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "wait_time": self.wait_time,
            "one_shot": self.one_shot,
            "autostart": self.autostart,
            "paused": self.paused,
            "_time_left": self._time_left,
            "_started": self._started
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Timer":
        """Create from dictionary"""
        timer = cls(data.get("name", "Timer"))
        cls._apply_node_properties(timer, data)
        
        # Apply Timer specific properties
        timer.wait_time = data.get("wait_time", 1.0)
        timer.one_shot = data.get("one_shot", False)
        timer.autostart = data.get("autostart", False)
        timer.paused = data.get("paused", False)
        timer._time_left = data.get("_time_left", 0.0)
        timer._started = data.get("_started", False)
        
        # Create children
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            timer.add_child(child)
        
        return timer
    
    def __str__(self) -> str:
        """String representation of the timer"""
        status = "stopped"
        if self._started:
            status = "paused" if self.paused else "running"
        
        return f"Timer({self.name}, wait_time={self.wait_time}, status={status}, time_left={self._time_left:.2f})"
