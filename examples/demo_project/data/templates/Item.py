"""
Item - Basic game item with properties
Generated scriptable object template
"""

from core.scriptable_objects.instance import ScriptableObjectInstance

class Item(ScriptableObjectInstance):
    """
    Basic game item with properties
    """

    def __init__(self, **kwargs):
        super().__init__("Item", **kwargs)

        self.display_name = kwargs.get("display_name", 'New Item')
        self.description = kwargs.get("description", '')
        self.icon = kwargs.get("icon", '')
        self.value = kwargs.get("value", 0)
        self.weight = kwargs.get("weight", 1.0)
        self.stackable = kwargs.get("stackable", True)
        self.max_stack = kwargs.get("max_stack", 99)
        self.rarity_color = kwargs.get("rarity_color", [1.0, 1.0, 1.0, 1.0])

    def _ready(self):
        """Called when the object is ready"""
        pass

    # Custom code

    
        def get_display_text(self):
            """Get formatted display text for this item"""
            return f"{self.display_name} (x{self.quantity if hasattr(self, 'quantity') else 1})"
        
        def can_stack_with(self, other_item):
            """Check if this item can stack with another"""
            return (self.stackable and 
                    hasattr(other_item, 'template_name') and 
                    other_item.template_name == self.template_name and
                    other_item.display_name == self.display_name)
        