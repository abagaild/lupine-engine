"""
scene/timer.py

Defines Timer node for scheduling time‐based callbacks.
"""

from typing import Dict, Any
from .base_node import Node


class Timer(Node):
    """Timer node for delays, cooldowns, and scheduled events."""

    def __init__(self, name: str = "Timer"):
        super().__init__(name, "Timer")
        # Timer properties
        self.wait_time: float = 1.0
        self.one_shot: bool = True
        self.autostart: bool = False
        self.paused: bool = False

        # Internal state
        self._time_left: float = 0.0
        self._is_running: bool = False

        self.script_path = "nodes/Timer.lsc"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "wait_time": self.wait_time,
            "one_shot": self.one_shot,
            "autostart": self.autostart,
            "paused": self.paused,
            "_time_left": self._time_left,
            "_is_running": self._is_running
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Timer":
        node = cls(data.get("name", "Timer"))
        node.wait_time = data.get("wait_time", 1.0)
        node.one_shot = data.get("one_shot", True)
        node.autostart = data.get("autostart", False)
        node.paused = data.get("paused", False)
        node._time_left = data.get("_time_left", 0.0)
        node._is_running = data.get("_is_running", False)
        Node._apply_node_properties(node, data)
        for child_data in data.get("children", []):
            child = Node.from_dict(child_data)
            node.add_child(child)
        return node
