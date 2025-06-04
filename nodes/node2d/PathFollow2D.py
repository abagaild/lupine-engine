"""
PathFollow2D node implementation for Lupine Engine
Follows a Path2D with offset, looping, and rotation options
"""

from nodes.base.Node2D import Node2D
from typing import Dict, Any, List, Optional


class PathFollow2D(Node2D):
    """
    PathFollow2D: Attaches to a Path2D and moves along it.
    """

    def __init__(self, name: str = "PathFollow2D"):
        super().__init__(name)
        self.type = "PathFollow2D"

        # Export variables for editor
        self.export_variables = {
            "offset": {
                "type": "float",
                "value": 0.0,
                "description": "Distance along the path (in pixels)"
            },
            "unit_offset": {
                "type": "float",
                "value": 0.0,
                "description": "Normalized position on path (0.0–1.0)"
            },
            "allow_rotate": {
                "type": "bool",
                "value": False,
                "description": "Allow rotation to match path tangent"
            },
            "loop": {
                "type": "bool",
                "value": True,
                "description": "Loop around at end of path"
            },
            "h_offset": {
                "type": "float",
                "value": 0.0,
                "description": "Perpendicular offset from path"
            },
            "v_offset": {
                "type": "float",
                "value": 0.0,
                "description": "Vertical offset from path"
            }
        }

        # Core properties
        self.offset: float = 0.0
        self.unit_offset: float = 0.0
        self.allow_rotate: bool = False
        self.loop: bool = True
        self.h_offset: float = 0.0
        self.v_offset: float = 0.0

        # Internal reference to Path2D node
        self._path_node: Optional[Node2D] = None

    def set_path_to_follow(self, path_node: Node2D):
        """
        Assign a Path2D node to follow.
        The engine should set this automatically when instancing.
        """
        self._path_node = path_node

    def get_path_to_follow(self) -> Optional[Node2D]:
        """Return the assigned Path2D node, if any."""
        return self._path_node

    def _process(self, delta: float):
        """Update the follower’s transform along the path each frame."""
        super()._process(delta)
        if not self._path_node or not hasattr(self._path_node, "curve"):
            return

        curve = getattr(self._path_node, "curve", [])
        if not curve:
            return

        # Simplified interpolation: unit_offset → index
        length = len(curve)
        if length < 2:
            return

        t = self.unit_offset % 1.0 if self.loop else max(0.0, min(self.unit_offset, 1.0))
        idx_f = t * (length - 1)
        i0 = int(idx_f)
        i1 = min(i0 + 1, length - 1)
        frac = idx_f - i0

        pt0 = curve[i0]
        pt1 = curve[i1]
        x = pt0[0] + (pt1[0] - pt0[0]) * frac
        y = pt0[1] + (pt1[1] - pt0[1]) * frac

        # Apply offsets
        self.set_position(x + self.h_offset, y + self.v_offset)

        # Handle rotation if requested (stub: align to segment direction)
        if self.allow_rotate:
            dx = pt1[0] - pt0[0]
            dy = pt1[1] - pt0[1]
            import math
            angle = math.atan2(dy, dx)
            self.set_rotation(angle)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize PathFollow2D to a dictionary."""
        data = super().to_dict()
        data.update({
            "offset": self.offset,
            "unit_offset": self.unit_offset,
            "allow_rotate": self.allow_rotate,
            "loop": self.loop,
            "h_offset": self.h_offset,
            "v_offset": self.v_offset,
            # We store the node path (string) rather than a reference
            "path_node": self._path_node.name if self._path_node else ""
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PathFollow2D":
        """Deserialize a PathFollow2D from a dictionary."""
        follow = cls(data.get("name", "PathFollow2D"))
        cls._apply_node_properties(follow, data)

        follow.offset = data.get("offset", 0.0)
        follow.unit_offset = data.get("unit_offset", 0.0)
        follow.allow_rotate = data.get("allow_rotate", False)
        follow.loop = data.get("loop", True)
        follow.h_offset = data.get("h_offset", 0.0)
        follow.v_offset = data.get("v_offset", 0.0)
        # Actual node-linking happens during scene loading: look up by name/path
        # follow._path_node = <resolve Node2D by data.get("path_node")>

        # Re-create children
        for child_data in data.get("children", []):
            from nodes.base.Node import Node
            child = Node.from_dict(child_data)
            follow.add_child(child)
        return follow
