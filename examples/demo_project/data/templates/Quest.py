"""
Quest - Game quest or mission
Generated scriptable object template
"""

from core.scriptable_objects.instance import ScriptableObjectInstance

class Quest(ScriptableObjectInstance):
    """
    Game quest or mission
    """

    def __init__(self, **kwargs):
        super().__init__("Quest", **kwargs)

        self.quest_name = kwargs.get("quest_name", 'New Quest')
        self.description = kwargs.get("description", '')
        self.objective = kwargs.get("objective", '')
        self.reward_gold = kwargs.get("reward_gold", 0)
        self.reward_exp = kwargs.get("reward_exp", 0)
        self.required_level = kwargs.get("required_level", 1)
        self.is_main_quest = kwargs.get("is_main_quest", False)
        self.prerequisites = kwargs.get("prerequisites", [])

    def _ready(self):
        """Called when the object is ready"""
        pass
