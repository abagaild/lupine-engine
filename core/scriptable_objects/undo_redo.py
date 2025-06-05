"""
Undo/Redo System for Scriptable Objects
Implements command pattern for reversible operations
"""

from typing import Any, List, Optional, Dict
from abc import ABC, abstractmethod
import copy


class Command(ABC):
    """Abstract base class for commands"""
    
    @abstractmethod
    def execute(self) -> Any:
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self) -> Any:
        """Undo the command"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get a description of the command"""
        pass


class UndoRedoManager:
    """Manages undo/redo operations"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: List[Command] = []
        self.current_index = -1
    
    def execute_command(self, command: Command) -> Any:
        """Execute a command and add it to history"""
        result = command.execute()
        
        # Remove any commands after current index (when undoing then doing new action)
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new command
        self.history.append(command)
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
        
        return result
    
    def undo(self) -> bool:
        """Undo the last command"""
        if self.can_undo():
            command = self.history[self.current_index]
            command.undo()
            self.current_index -= 1
            return True
        return False
    
    def redo(self) -> bool:
        """Redo the next command"""
        if self.can_redo():
            self.current_index += 1
            command = self.history[self.current_index]
            command.execute()
            return True
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.current_index < len(self.history) - 1
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of command that would be undone"""
        if self.can_undo():
            return self.history[self.current_index].get_description()
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of command that would be redone"""
        if self.can_redo():
            return self.history[self.current_index + 1].get_description()
        return None
    
    def clear_history(self):
        """Clear all history"""
        self.history.clear()
        self.current_index = -1


# Template Commands

class AddFieldCommand(Command):
    """Command to add a field to a template"""
    
    def __init__(self, template, field):
        self.template = template
        self.field = field
        self.executed = False
    
    def execute(self):
        if not self.executed:
            self.template.add_field(self.field)
            self.executed = True
        return self.field
    
    def undo(self):
        if self.executed:
            self.template.remove_field(self.field.name)
            self.executed = False
    
    def get_description(self) -> str:
        return f"Add field '{self.field.name}'"


class RemoveFieldCommand(Command):
    """Command to remove a field from a template"""
    
    def __init__(self, template, field_name: str):
        self.template = template
        self.field_name = field_name
        self.removed_field = None
        self.field_index = -1
    
    def execute(self):
        # Find and store the field before removing
        for i, field in enumerate(self.template.fields):
            if field.name == self.field_name:
                self.removed_field = copy.deepcopy(field)
                self.field_index = i
                break
        
        if self.removed_field:
            self.template.remove_field(self.field_name)
        return self.removed_field
    
    def undo(self):
        if self.removed_field:
            # Insert at original position
            if self.field_index < len(self.template.fields):
                self.template.fields.insert(self.field_index, self.removed_field)
            else:
                self.template.fields.append(self.removed_field)
    
    def get_description(self) -> str:
        return f"Remove field '{self.field_name}'"


class ModifyFieldCommand(Command):
    """Command to modify a field in a template"""
    
    def __init__(self, template, field_name: str, property_name: str, old_value: Any, new_value: Any):
        self.template = template
        self.field_name = field_name
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        field = self.template.get_field(self.field_name)
        if field:
            setattr(field, self.property_name, self.new_value)
        return self.new_value
    
    def undo(self):
        field = self.template.get_field(self.field_name)
        if field:
            setattr(field, self.property_name, self.old_value)
    
    def get_description(self) -> str:
        return f"Modify field '{self.field_name}.{self.property_name}'"


class ReorderFieldsCommand(Command):
    """Command to reorder fields in a template"""
    
    def __init__(self, template, old_order: List[str], new_order: List[str]):
        self.template = template
        self.old_order = old_order
        self.new_order = new_order
    
    def execute(self):
        self.template.reorder_fields(self.new_order)
        return self.new_order
    
    def undo(self):
        self.template.reorder_fields(self.old_order)
    
    def get_description(self) -> str:
        return "Reorder fields"


class ModifyTemplateCommand(Command):
    """Command to modify template properties"""
    
    def __init__(self, template, property_name: str, old_value: Any, new_value: Any):
        self.template = template
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        setattr(self.template, self.property_name, self.new_value)
        return self.new_value
    
    def undo(self):
        setattr(self.template, self.property_name, self.old_value)
    
    def get_description(self) -> str:
        return f"Modify template '{self.property_name}'"


# Instance Commands

class ModifyInstanceCommand(Command):
    """Command to modify instance data"""
    
    def __init__(self, instance, field_name: str, old_value: Any, new_value: Any):
        self.instance = instance
        self.field_name = field_name
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        self.instance.set_value(self.field_name, self.new_value)
        return self.new_value
    
    def undo(self):
        self.instance.set_value(self.field_name, self.old_value)
    
    def get_description(self) -> str:
        return f"Modify instance '{self.field_name}'"


class CreateInstanceCommand(Command):
    """Command to create a new instance"""
    
    def __init__(self, manager, template_name: str, instance_name: str):
        self.manager = manager
        self.template_name = template_name
        self.instance_name = instance_name
        self.created_instance = None
    
    def execute(self):
        self.created_instance = self.manager.create_instance(self.template_name, self.instance_name)
        if self.created_instance:
            self.manager.save_instance(self.created_instance)
        return self.created_instance
    
    def undo(self):
        if self.created_instance:
            self.manager.delete_instance(self.template_name, self.created_instance.instance_id)
    
    def get_description(self) -> str:
        return f"Create instance '{self.instance_name}'"


class DeleteInstanceCommand(Command):
    """Command to delete an instance"""
    
    def __init__(self, manager, template_name: str, instance_id: str):
        self.manager = manager
        self.template_name = template_name
        self.instance_id = instance_id
        self.deleted_instance = None
    
    def execute(self):
        # Store the instance before deleting
        self.deleted_instance = self.manager.get_instance(self.template_name, self.instance_id)
        if self.deleted_instance:
            self.deleted_instance = copy.deepcopy(self.deleted_instance)
            self.manager.delete_instance(self.template_name, self.instance_id)
        return self.deleted_instance
    
    def undo(self):
        if self.deleted_instance:
            self.manager.save_instance(self.deleted_instance)
    
    def get_description(self) -> str:
        return f"Delete instance '{self.instance_id}'"


# Composite Commands

class CompositeCommand(Command):
    """Command that contains multiple sub-commands"""
    
    def __init__(self, description: str, commands: List[Command] = None):
        self.description = description
        self.commands = commands or []
    
    def add_command(self, command: Command):
        """Add a sub-command"""
        self.commands.append(command)
    
    def execute(self):
        results = []
        for command in self.commands:
            results.append(command.execute())
        return results
    
    def undo(self):
        # Undo in reverse order
        for command in reversed(self.commands):
            command.undo()
    
    def get_description(self) -> str:
        return self.description
