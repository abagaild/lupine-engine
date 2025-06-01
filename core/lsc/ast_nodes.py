"""
AST (Abstract Syntax Tree) Nodes for LSC Language
Represents the structure of parsed LSC code
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict, Union
from dataclasses import dataclass


class ASTNode(ABC):
    """Base class for all AST nodes"""
    
    def __init__(self, line: int = 0, column: int = 0):
        self.line = line
        self.column = column
    
    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor for the visitor pattern"""
        pass


# Expressions
class Expression(ASTNode):
    """Base class for expressions"""
    pass


@dataclass
class Literal(Expression):
    """Literal value (number, string, boolean, null)"""
    value: Any
    
    def accept(self, visitor):
        return visitor.visit_literal(self)


@dataclass
class Identifier(Expression):
    """Variable or function identifier"""
    name: str
    
    def accept(self, visitor):
        return visitor.visit_identifier(self)


@dataclass
class BinaryOp(Expression):
    """Binary operation (a + b, a == b, etc.)"""
    left: Expression
    operator: str
    right: Expression
    
    def accept(self, visitor):
        return visitor.visit_binary_op(self)


@dataclass
class UnaryOp(Expression):
    """Unary operation (-a, not a, etc.)"""
    operator: str
    operand: Expression
    
    def accept(self, visitor):
        return visitor.visit_unary_op(self)


@dataclass
class TernaryOp(Expression):
    """Ternary conditional operator (condition ? true_expr : false_expr)"""
    condition: Expression
    true_expr: Expression
    false_expr: Expression
    
    def accept(self, visitor):
        return visitor.visit_ternary_op(self)


@dataclass
class FunctionCall(Expression):
    """Function call expression"""
    function: Expression
    arguments: List[Expression]
    
    def accept(self, visitor):
        return visitor.visit_function_call(self)


@dataclass
class MemberAccess(Expression):
    """Member access (object.property)"""
    object: Expression
    member: str
    
    def accept(self, visitor):
        return visitor.visit_member_access(self)


@dataclass
class IndexAccess(Expression):
    """Index access (array[index])"""
    object: Expression
    index: Expression
    
    def accept(self, visitor):
        return visitor.visit_index_access(self)


@dataclass
class ArrayLiteral(Expression):
    """Array literal [1, 2, 3]"""
    elements: List[Expression]
    
    def accept(self, visitor):
        return visitor.visit_array_literal(self)


@dataclass
class DictionaryLiteral(Expression):
    """Dictionary literal {key: value}"""
    pairs: List[tuple[Expression, Expression]]
    
    def accept(self, visitor):
        return visitor.visit_dictionary_literal(self)


@dataclass
class NodePath(Expression):
    """Node path expression ($NodeName or $"path/to/node")"""
    path: str
    
    def accept(self, visitor):
        return visitor.visit_node_path(self)


# Statements
class Statement(ASTNode):
    """Base class for statements"""
    pass


@dataclass
class ExpressionStatement(Statement):
    """Expression used as statement"""
    expression: Expression
    
    def accept(self, visitor):
        return visitor.visit_expression_statement(self)


@dataclass
class VarDeclaration(Statement):
    """Variable declaration"""
    name: str
    type_hint: Optional[str]
    initializer: Optional[Expression]
    is_const: bool = False
    
    def accept(self, visitor):
        return visitor.visit_var_declaration(self)


@dataclass
class Assignment(Statement):
    """Assignment statement"""
    target: Expression
    operator: str  # =, +=, -=, etc.
    value: Expression
    
    def accept(self, visitor):
        return visitor.visit_assignment(self)


@dataclass
class IfStatement(Statement):
    """If statement with optional elif and else"""
    condition: Expression
    then_body: List[Statement]
    elif_clauses: List[tuple[Expression, List[Statement]]]
    else_body: Optional[List[Statement]]
    
    def accept(self, visitor):
        return visitor.visit_if_statement(self)


@dataclass
class WhileStatement(Statement):
    """While loop"""
    condition: Expression
    body: List[Statement]
    
    def accept(self, visitor):
        return visitor.visit_while_statement(self)


@dataclass
class DoWhileStatement(Statement):
    """Do-while loop (LSC extension)"""
    body: List[Statement]
    condition: Expression
    
    def accept(self, visitor):
        return visitor.visit_do_while_statement(self)


@dataclass
class ForStatement(Statement):
    """For loop"""
    variable: str
    iterable: Expression
    body: List[Statement]
    
    def accept(self, visitor):
        return visitor.visit_for_statement(self)


@dataclass
class BreakStatement(Statement):
    """Break statement"""
    
    def accept(self, visitor):
        return visitor.visit_break_statement(self)


@dataclass
class ContinueStatement(Statement):
    """Continue statement"""
    
    def accept(self, visitor):
        return visitor.visit_continue_statement(self)


@dataclass
class ReturnStatement(Statement):
    """Return statement"""
    value: Optional[Expression]
    
    def accept(self, visitor):
        return visitor.visit_return_statement(self)


@dataclass
class PassStatement(Statement):
    """Pass statement (no-op)"""
    
    def accept(self, visitor):
        return visitor.visit_pass_statement(self)


# Function and class definitions
@dataclass
class Parameter:
    """Function parameter"""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[Expression] = None


@dataclass
class FunctionDef(Statement):
    """Function definition"""
    name: str
    parameters: List[Parameter]
    return_type: Optional[str]
    body: List[Statement]
    is_static: bool = False
    
    def accept(self, visitor):
        return visitor.visit_function_def(self)


@dataclass
class ClassDef(Statement):
    """Class definition"""
    name: str
    base_class: Optional[str]
    body: List[Statement]
    is_tool: bool = False
    
    def accept(self, visitor):
        return visitor.visit_class_def(self)


# Export system
@dataclass
class ExportDeclaration(Statement):
    """Export variable declaration for inspector"""
    var_declaration: VarDeclaration
    export_type: Optional[str] = None  # For specific export types
    export_hint: Optional[str] = None  # For dropdowns, file paths, etc.
    
    def accept(self, visitor):
        return visitor.visit_export_declaration(self)


@dataclass
class ExportGroup(Statement):
    """Export group for organizing inspector variables"""
    name: str
    prefix: Optional[str] = None
    
    def accept(self, visitor):
        return visitor.visit_export_group(self)


@dataclass
class SignalDeclaration(Statement):
    """Signal declaration"""
    name: str
    parameters: List[Parameter]
    
    def accept(self, visitor):
        return visitor.visit_signal_declaration(self)


@dataclass
class EnumDeclaration(Statement):
    """Enum declaration"""
    name: str
    values: List[str]
    
    def accept(self, visitor):
        return visitor.visit_enum_declaration(self)


# Program root
@dataclass
class Program(ASTNode):
    """Root node representing entire program"""
    statements: List[Statement]
    
    def accept(self, visitor):
        return visitor.visit_program(self)


# Visitor interface
class ASTVisitor(ABC):
    """Visitor interface for traversing AST"""
    
    @abstractmethod
    def visit_literal(self, node: Literal): pass
    
    @abstractmethod
    def visit_identifier(self, node: Identifier): pass
    
    @abstractmethod
    def visit_binary_op(self, node: BinaryOp): pass
    
    @abstractmethod
    def visit_unary_op(self, node: UnaryOp): pass
    
    @abstractmethod
    def visit_ternary_op(self, node: TernaryOp): pass
    
    @abstractmethod
    def visit_function_call(self, node: FunctionCall): pass
    
    @abstractmethod
    def visit_member_access(self, node: MemberAccess): pass
    
    @abstractmethod
    def visit_index_access(self, node: IndexAccess): pass
    
    @abstractmethod
    def visit_array_literal(self, node: ArrayLiteral): pass
    
    @abstractmethod
    def visit_dictionary_literal(self, node: DictionaryLiteral): pass
    
    @abstractmethod
    def visit_node_path(self, node: NodePath): pass

    @abstractmethod
    def visit_expression_statement(self, node: ExpressionStatement): pass

    @abstractmethod
    def visit_var_declaration(self, node: VarDeclaration): pass

    @abstractmethod
    def visit_assignment(self, node: Assignment): pass

    @abstractmethod
    def visit_if_statement(self, node: IfStatement): pass

    @abstractmethod
    def visit_while_statement(self, node: WhileStatement): pass

    @abstractmethod
    def visit_do_while_statement(self, node: DoWhileStatement): pass

    @abstractmethod
    def visit_for_statement(self, node: ForStatement): pass

    @abstractmethod
    def visit_break_statement(self, node: BreakStatement): pass

    @abstractmethod
    def visit_continue_statement(self, node: ContinueStatement): pass

    @abstractmethod
    def visit_return_statement(self, node: ReturnStatement): pass

    @abstractmethod
    def visit_pass_statement(self, node: PassStatement): pass

    @abstractmethod
    def visit_function_def(self, node: FunctionDef): pass

    @abstractmethod
    def visit_class_def(self, node: ClassDef): pass

    @abstractmethod
    def visit_export_declaration(self, node: ExportDeclaration): pass

    @abstractmethod
    def visit_export_group(self, node: ExportGroup): pass

    @abstractmethod
    def visit_signal_declaration(self, node: SignalDeclaration): pass

    @abstractmethod
    def visit_enum_declaration(self, node: EnumDeclaration): pass

    @abstractmethod
    def visit_program(self, node: Program): pass
