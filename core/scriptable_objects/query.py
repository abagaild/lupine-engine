"""
Query System for Scriptable Objects
Provides SQL-like querying capabilities for finding instances
"""

from typing import Any, List, Dict, Optional, Callable, Union
from enum import Enum
import re
import operator


class QueryOperator(Enum):
    """Supported query operators"""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class QueryCondition:
    """Represents a single query condition"""
    
    def __init__(self, field: str, op: QueryOperator, value: Any = None):
        self.field = field
        self.operator = op
        self.value = value
    
    def evaluate(self, instance) -> bool:
        """Evaluate this condition against an instance"""
        field_value = instance.get_value(self.field)
        
        if self.operator == QueryOperator.EQUALS:
            return field_value == self.value
        elif self.operator == QueryOperator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == QueryOperator.GREATER_THAN:
            return field_value > self.value
        elif self.operator == QueryOperator.GREATER_EQUAL:
            return field_value >= self.value
        elif self.operator == QueryOperator.LESS_THAN:
            return field_value < self.value
        elif self.operator == QueryOperator.LESS_EQUAL:
            return field_value <= self.value
        elif self.operator == QueryOperator.CONTAINS:
            return isinstance(field_value, str) and str(self.value) in field_value
        elif self.operator == QueryOperator.STARTS_WITH:
            return isinstance(field_value, str) and field_value.startswith(str(self.value))
        elif self.operator == QueryOperator.ENDS_WITH:
            return isinstance(field_value, str) and field_value.endswith(str(self.value))
        elif self.operator == QueryOperator.REGEX:
            return isinstance(field_value, str) and bool(re.search(str(self.value), field_value))
        elif self.operator == QueryOperator.IN:
            return field_value in self.value if isinstance(self.value, (list, tuple, set)) else False
        elif self.operator == QueryOperator.NOT_IN:
            return field_value not in self.value if isinstance(self.value, (list, tuple, set)) else True
        elif self.operator == QueryOperator.IS_NULL:
            return field_value is None
        elif self.operator == QueryOperator.IS_NOT_NULL:
            return field_value is not None
        
        return False


class QueryBuilder:
    """Builder for constructing complex queries"""
    
    def __init__(self):
        self.conditions: List[QueryCondition] = []
        self.logic_operators: List[str] = []  # "AND", "OR"
        self.order_by: List[tuple] = []  # (field, ascending)
        self.limit_count: Optional[int] = None
        self.offset_count: int = 0
    
    def where(self, field: str, op: Union[QueryOperator, str], value: Any = None) -> 'QueryBuilder':
        """Add a WHERE condition"""
        if isinstance(op, str):
            op = QueryOperator(op)
        
        condition = QueryCondition(field, op, value)
        self.conditions.append(condition)
        
        return self
    
    def and_where(self, field: str, op: Union[QueryOperator, str], value: Any = None) -> 'QueryBuilder':
        """Add an AND condition"""
        if self.conditions:
            self.logic_operators.append("AND")
        return self.where(field, op, value)
    
    def or_where(self, field: str, op: Union[QueryOperator, str], value: Any = None) -> 'QueryBuilder':
        """Add an OR condition"""
        if self.conditions:
            self.logic_operators.append("OR")
        return self.where(field, op, value)
    
    def order_by(self, field: str, ascending: bool = True) -> 'QueryBuilder':
        """Add ordering"""
        self.order_by.append((field, ascending))
        return self
    
    def limit(self, count: int) -> 'QueryBuilder':
        """Set result limit"""
        self.limit_count = count
        return self
    
    def offset(self, count: int) -> 'QueryBuilder':
        """Set result offset"""
        self.offset_count = count
        return self
    
    def evaluate_conditions(self, instance) -> bool:
        """Evaluate all conditions against an instance"""
        if not self.conditions:
            return True
        
        # Evaluate first condition
        result = self.conditions[0].evaluate(instance)
        
        # Apply logic operators
        for i, logic_op in enumerate(self.logic_operators):
            if i + 1 < len(self.conditions):
                condition_result = self.conditions[i + 1].evaluate(instance)
                
                if logic_op == "AND":
                    result = result and condition_result
                elif logic_op == "OR":
                    result = result or condition_result
        
        return result
    
    def apply_ordering(self, instances: List) -> List:
        """Apply ordering to results"""
        if not self.order_by:
            return instances
        
        def sort_key(instance):
            key_values = []
            for field, ascending in self.order_by:
                value = instance.get_value(field)
                # Handle None values
                if value is None:
                    value = "" if isinstance(value, str) else 0
                key_values.append(value)
            return key_values
        
        # Sort by multiple fields
        sorted_instances = sorted(instances, key=sort_key)
        
        # Apply descending order for fields marked as such
        for field, ascending in reversed(self.order_by):
            if not ascending:
                sorted_instances.reverse()
                break  # Only reverse once for the primary sort field
        
        return sorted_instances
    
    def apply_limit_offset(self, instances: List) -> List:
        """Apply limit and offset to results"""
        start = self.offset_count
        end = start + self.limit_count if self.limit_count else None
        
        return instances[start:end]


class QueryEngine:
    """Main query engine for scriptable objects"""
    
    def __init__(self, manager):
        self.manager = manager
    
    def query(self, template_name: str) -> QueryBuilder:
        """Start a new query for a template"""
        return QueryBuilder()
    
    def execute(self, template_name: str, query: QueryBuilder) -> List:
        """Execute a query and return results"""
        # Get all instances of the template
        instances = self.manager.get_instances_of_template(template_name)
        
        # Filter by conditions
        filtered_instances = [
            instance for instance in instances
            if query.evaluate_conditions(instance)
        ]
        
        # Apply ordering
        ordered_instances = query.apply_ordering(filtered_instances)
        
        # Apply limit and offset
        final_instances = query.apply_limit_offset(ordered_instances)
        
        return final_instances
    
    def find_by_field(self, template_name: str, field: str, value: Any) -> List:
        """Simple find by single field value"""
        query = self.query(template_name).where(field, QueryOperator.EQUALS, value)
        return self.execute(template_name, query)
    
    def find_by_criteria(self, template_name: str, criteria: Dict[str, Any]) -> List:
        """Find by multiple field criteria (AND logic)"""
        query = self.query(template_name)
        
        for field, value in criteria.items():
            query = query.and_where(field, QueryOperator.EQUALS, value)
        
        return self.execute(template_name, query)
    
    def search_text(self, template_name: str, text: str, fields: Optional[List[str]] = None) -> List:
        """Search for text across specified fields"""
        instances = self.manager.get_instances_of_template(template_name)
        
        if not fields:
            # Search all string fields
            template = self.manager.get_template(template_name)
            if template:
                fields = [f.name for f in template.fields if f.field_type.value in ["string"]]
            else:
                fields = []

        matching_instances = []
        text_lower = text.lower()

        for instance in instances:
            for field in fields or []:
                field_value = instance.get_value(field, "")
                if isinstance(field_value, str) and text_lower in field_value.lower():
                    matching_instances.append(instance)
                    break  # Don't add the same instance multiple times
        
        return matching_instances
    
    def aggregate(self, template_name: str, field: str, operation: str) -> Any:
        """Perform aggregation operations"""
        instances = self.manager.get_instances_of_template(template_name)
        values = [instance.get_value(field) for instance in instances]
        
        # Filter out None values
        numeric_values = [v for v in values if isinstance(v, (int, float))]
        
        if operation == "count":
            return len(instances)
        elif operation == "sum":
            return sum(numeric_values)
        elif operation == "avg":
            return sum(numeric_values) / len(numeric_values) if numeric_values else 0
        elif operation == "min":
            return min(numeric_values) if numeric_values else None
        elif operation == "max":
            return max(numeric_values) if numeric_values else None
        elif operation == "distinct":
            return list(set(values))
        
        return None
    
    def group_by(self, template_name: str, field: str) -> Dict[Any, List]:
        """Group instances by field value"""
        instances = self.manager.get_instances_of_template(template_name)
        groups = {}
        
        for instance in instances:
            field_value = instance.get_value(field)
            if field_value not in groups:
                groups[field_value] = []
            groups[field_value].append(instance)
        
        return groups


# Convenience functions for common queries

def equals(field: str, value: Any) -> QueryCondition:
    """Create an equals condition"""
    return QueryCondition(field, QueryOperator.EQUALS, value)

def not_equals(field: str, value: Any) -> QueryCondition:
    """Create a not equals condition"""
    return QueryCondition(field, QueryOperator.NOT_EQUALS, value)

def greater_than(field: str, value: Any) -> QueryCondition:
    """Create a greater than condition"""
    return QueryCondition(field, QueryOperator.GREATER_THAN, value)

def less_than(field: str, value: Any) -> QueryCondition:
    """Create a less than condition"""
    return QueryCondition(field, QueryOperator.LESS_THAN, value)

def contains(field: str, value: str) -> QueryCondition:
    """Create a contains condition"""
    return QueryCondition(field, QueryOperator.CONTAINS, value)

def in_list(field: str, values: List[Any]) -> QueryCondition:
    """Create an 'in list' condition"""
    return QueryCondition(field, QueryOperator.IN, values)

def regex_match(field: str, pattern: str) -> QueryCondition:
    """Create a regex match condition"""
    return QueryCondition(field, QueryOperator.REGEX, pattern)
