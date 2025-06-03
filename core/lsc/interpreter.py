"""
LSC Interpreter - Executes LSC AST nodes
Implements the visitor pattern to traverse and execute the abstract syntax tree
"""

from typing import Any, List, Dict, Optional
from .ast_nodes import *
from .runtime import LSCRuntime, LSCScope
from .inheritance import LSCInheritanceManager


class LSCRuntimeError(Exception):
    """Runtime error in LSC execution"""
    pass


class ReturnValue(Exception):
    """Exception used for return statement control flow"""
    def __init__(self, value: Any):
        self.value = value


class BreakException(Exception):
    """Exception used for break statement control flow"""
    pass


class ContinueException(Exception):
    """Exception used for continue statement control flow"""
    pass


class LSCInterpreter(ASTVisitor):
    """Interpreter for LSC language"""
    
    def __init__(self, runtime: LSCRuntime):
        self.runtime = runtime
    
    def interpret(self, program: Program) -> None:
        """Interpret a program"""
        try:
            self.visit_program(program)
        except LSCRuntimeError as e:
            print(f"Runtime Error: {e}")
            raise
    
    def visit_program(self, node: Program) -> None:
        """Visit program node with two-pass execution"""
        # First pass: Define all functions, classes, and signals
        for statement in node.statements:
            if self._is_definition_statement(statement):
                self.execute_statement(statement)

        # Second pass: Execute all other statements
        for statement in node.statements:
            if not self._is_definition_statement(statement):
                self.execute_statement(statement)

    def _is_definition_statement(self, statement) -> bool:
        """Check if statement is a definition (function, class, signal, enum)"""
        from .ast_nodes import FunctionDef, ClassDef, SignalDeclaration, EnumDeclaration
        return isinstance(statement, (FunctionDef, ClassDef, SignalDeclaration, EnumDeclaration))
    
    def execute_statement(self, statement: Statement) -> None:
        """Execute a statement"""
        statement.accept(self)
    
    def evaluate_expression(self, expression: Expression) -> Any:
        """Evaluate an expression"""
        return expression.accept(self)
    
    # Expression visitors
    def visit_literal(self, node: Literal) -> Any:
        """Visit literal node"""
        return node.value
    
    def visit_identifier(self, node: Identifier) -> Any:
        """Visit identifier node"""
        try:
            return self.runtime.get_variable(node.name)
        except NameError:
            # Try to provide a reasonable default for common undefined variables
            default_value = self._get_default_for_undefined_variable(node.name)
            if default_value is not None:
                print(f"Warning: Using default value for undefined variable '{node.name}'")
                # Define the variable with the default value for future use
                self.runtime.define_variable(node.name, default_value)
                return default_value
            else:
                print(f"Runtime Error: Undefined variable '{node.name}'")
                # Return None instead of crashing to allow script to continue
                return None
    
    def visit_binary_op(self, node: BinaryOp) -> Any:
        """Visit binary operation node"""
        left = self.evaluate_expression(node.left)
        
        # Short-circuit evaluation for logical operators
        if node.operator == "and" or node.operator == "&&":
            if not self._is_truthy(left):
                return left
            return self.evaluate_expression(node.right)
        
        if node.operator == "or" or node.operator == "||":
            if self._is_truthy(left):
                return left
            return self.evaluate_expression(node.right)
        
        right = self.evaluate_expression(node.right)
        
        # Arithmetic operators
        if node.operator == "+":
            return left + right
        elif node.operator == "-":
            return left - right
        elif node.operator == "*":
            return left * right
        elif node.operator == "/":
            if right == 0:
                raise LSCRuntimeError("Division by zero")
            return left / right
        elif node.operator == "%":
            return left % right
        elif node.operator == "**":
            return left ** right
        
        # Comparison operators
        elif node.operator == "==":
            return left == right
        elif node.operator == "!=":
            return left != right
        elif node.operator == "<":
            return left < right
        elif node.operator == "<=":
            return left <= right
        elif node.operator == ">":
            return left > right
        elif node.operator == ">=":
            return left >= right
        
        # Bitwise operators
        elif node.operator == "&":
            return left & right
        elif node.operator == "|":
            return left | right
        elif node.operator == "^":
            return left ^ right
        elif node.operator == "<<":
            return left << right
        elif node.operator == ">>":
            return left >> right
        
        # Membership operators
        elif node.operator == "in":
            return left in right
        elif node.operator == "is":
            return left is right
        
        else:
            raise LSCRuntimeError(f"Unknown binary operator '{node.operator}'")
    
    def visit_unary_op(self, node: UnaryOp) -> Any:
        """Visit unary operation node"""
        operand = self.evaluate_expression(node.operand)
        
        if node.operator == "-":
            return -operand
        elif node.operator == "+":
            return +operand
        elif node.operator == "not" or node.operator == "!":
            return not self._is_truthy(operand)
        elif node.operator == "~":
            return ~operand
        else:
            raise LSCRuntimeError(f"Unknown unary operator '{node.operator}'")
    
    def visit_ternary_op(self, node: TernaryOp) -> Any:
        """Visit ternary operation node"""
        condition = self.evaluate_expression(node.condition)
        
        if self._is_truthy(condition):
            return self.evaluate_expression(node.true_expr)
        else:
            return self.evaluate_expression(node.false_expr)
    
    def visit_function_call(self, node: FunctionCall) -> Any:
        """Visit function call node"""
        function = self.evaluate_expression(node.function)

        if function is None:
            # If function is None (undefined), return None instead of crashing
            print(f"Warning: Attempting to call undefined function")
            return None

        if not callable(function):
            print(f"Warning: '{function}' is not callable, returning None")
            return None

        # Evaluate arguments
        args = [self.evaluate_expression(arg) for arg in node.arguments]

        try:
            return function(*args)
        except Exception as e:
            print(f"Warning: Error calling function: {e}")
            return None
    
    def visit_member_access(self, node: MemberAccess) -> Any:
        """Visit member access node"""
        obj = self.evaluate_expression(node.object)
        
        if hasattr(obj, node.member):
            return getattr(obj, node.member)
        else:
            raise LSCRuntimeError(f"'{type(obj).__name__}' object has no attribute '{node.member}'")
    
    def visit_index_access(self, node: IndexAccess) -> Any:
        """Visit index access node"""
        obj = self.evaluate_expression(node.object)
        index = self.evaluate_expression(node.index)
        
        try:
            return obj[index]
        except (KeyError, IndexError, TypeError) as e:
            raise LSCRuntimeError(f"Index access error: {e}")
    
    def visit_array_literal(self, node: ArrayLiteral) -> List[Any]:
        """Visit array literal node"""
        return [self.evaluate_expression(element) for element in node.elements]
    
    def visit_dictionary_literal(self, node: DictionaryLiteral) -> Dict[Any, Any]:
        """Visit dictionary literal node"""
        result = {}
        for key_expr, value_expr in node.pairs:
            key = self.evaluate_expression(key_expr)
            value = self.evaluate_expression(value_expr)
            result[key] = value
        return result
    
    def visit_node_path(self, node: NodePath) -> Any:
        """Visit node path node"""
        # Use runtime to get node by path
        return self.runtime.get_node(node.path)
    
    # Statement visitors
    def visit_expression_statement(self, node: ExpressionStatement) -> None:
        """Visit expression statement node"""
        self.evaluate_expression(node.expression)
    
    def visit_var_declaration(self, node: VarDeclaration) -> None:
        """Visit variable declaration node"""
        value = None
        if node.initializer:
            value = self.evaluate_expression(node.initializer)
        
        self.runtime.define_variable(node.name, value)
    
    def visit_assignment(self, node: Assignment) -> None:
        """Visit assignment node"""
        value = self.evaluate_expression(node.value)
        
        if isinstance(node.target, Identifier):
            # Simple variable assignment
            if node.operator == "=":
                self.runtime.set_variable(node.target.name, value)
            else:
                # Compound assignment
                current = self.runtime.get_variable(node.target.name)
                if node.operator == "+=":
                    self.runtime.set_variable(node.target.name, current + value)
                elif node.operator == "-=":
                    self.runtime.set_variable(node.target.name, current - value)
                elif node.operator == "*=":
                    self.runtime.set_variable(node.target.name, current * value)
                elif node.operator == "/=":
                    if value == 0:
                        raise LSCRuntimeError("Division by zero")
                    self.runtime.set_variable(node.target.name, current / value)
                elif node.operator == "%=":
                    self.runtime.set_variable(node.target.name, current % value)
                elif node.operator == "**=":
                    self.runtime.set_variable(node.target.name, current ** value)
        
        elif isinstance(node.target, MemberAccess):
            # Member assignment
            obj = self.evaluate_expression(node.target.object)
            if hasattr(obj, node.target.member):
                if node.operator == "=":
                    setattr(obj, node.target.member, value)
                else:
                    # Compound assignment for member
                    current = getattr(obj, node.target.member)
                    if node.operator == "+=":
                        setattr(obj, node.target.member, current + value)
                    elif node.operator == "-=":
                        setattr(obj, node.target.member, current - value)
                    elif node.operator == "*=":
                        setattr(obj, node.target.member, current * value)
                    elif node.operator == "/=":
                        if value == 0:
                            raise LSCRuntimeError("Division by zero")
                        setattr(obj, node.target.member, current / value)
                    elif node.operator == "%=":
                        setattr(obj, node.target.member, current % value)
                    elif node.operator == "**=":
                        setattr(obj, node.target.member, current ** value)
                    else:
                        raise LSCRuntimeError(f"Unknown compound assignment operator '{node.operator}'")
            else:
                raise LSCRuntimeError(f"'{type(obj).__name__}' object has no attribute '{node.target.member}'")
        
        elif isinstance(node.target, IndexAccess):
            # Index assignment
            obj = self.evaluate_expression(node.target.object)
            index = self.evaluate_expression(node.target.index)
            
            try:
                if node.operator == "=":
                    obj[index] = value
                else:
                    # Compound assignment for index
                    current = obj[index]
                    if node.operator == "+=":
                        obj[index] = current + value
                    # ... other compound operators
            except (KeyError, IndexError, TypeError) as e:
                raise LSCRuntimeError(f"Index assignment error: {e}")
    
    def visit_if_statement(self, node: IfStatement) -> None:
        """Visit if statement node"""
        condition = self.evaluate_expression(node.condition)
        
        if self._is_truthy(condition):
            self._execute_block(node.then_body)
        else:
            # Check elif clauses
            for elif_condition, elif_body in node.elif_clauses:
                elif_cond_value = self.evaluate_expression(elif_condition)
                if self._is_truthy(elif_cond_value):
                    self._execute_block(elif_body)
                    return
            
            # Execute else block if present
            if node.else_body:
                self._execute_block(node.else_body)
    
    def visit_while_statement(self, node: WhileStatement) -> None:
        """Visit while statement node"""
        try:
            while True:
                condition = self.evaluate_expression(node.condition)
                if not self._is_truthy(condition):
                    break
                
                try:
                    self._execute_block(node.body)
                except ContinueException:
                    continue
                except BreakException:
                    break
        except BreakException:
            pass
    
    def visit_do_while_statement(self, node: DoWhileStatement) -> None:
        """Visit do-while statement node"""
        try:
            while True:
                try:
                    self._execute_block(node.body)
                except ContinueException:
                    pass
                except BreakException:
                    break
                
                condition = self.evaluate_expression(node.condition)
                if not self._is_truthy(condition):
                    break
        except BreakException:
            pass

    def visit_for_statement(self, node: ForStatement) -> None:
        """Visit for statement node"""
        iterable = self.evaluate_expression(node.iterable)

        try:
            for item in iterable:
                self.runtime.define_variable(node.variable, item)

                try:
                    self._execute_block(node.body)
                except ContinueException:
                    continue
                except BreakException:
                    break
        except BreakException:
            pass
        except TypeError:
            raise LSCRuntimeError(f"'{type(iterable).__name__}' object is not iterable")

    def visit_break_statement(self, node: BreakStatement) -> None:
        """Visit break statement node"""
        raise BreakException()

    def visit_continue_statement(self, node: ContinueStatement) -> None:
        """Visit continue statement node"""
        raise ContinueException()

    def visit_return_statement(self, node: ReturnStatement) -> None:
        """Visit return statement node"""
        value = None
        if node.value:
            value = self.evaluate_expression(node.value)
        raise ReturnValue(value)

    def visit_pass_statement(self, node: PassStatement) -> None:
        """Visit pass statement node"""
        pass  # No-op

    def visit_function_def(self, node: FunctionDef) -> None:
        """Visit function definition node"""
        def lsc_function(*args):
            # Create new scope for function
            func_scope = self.runtime.push_scope()

            try:
                # Bind parameters
                for i, param in enumerate(node.parameters):
                    if i < len(args):
                        self.runtime.define_variable(param.name, args[i])
                    elif param.default_value:
                        default = self.evaluate_expression(param.default_value)
                        self.runtime.define_variable(param.name, default)
                    else:
                        raise LSCRuntimeError(f"Missing argument for parameter '{param.name}'")

                # Execute function body
                try:
                    self._execute_block(node.body)
                    return None  # No explicit return
                except ReturnValue as ret:
                    return ret.value

            finally:
                # Restore scope
                self.runtime.pop_scope()

        # Define function in current scope
        self.runtime.define_variable(node.name, lsc_function)

    def visit_class_def(self, node: ClassDef) -> None:
        """Visit class definition node"""
        # For now, just execute the class body in a new scope
        # A full implementation would create a proper class object
        class_scope = self.runtime.push_scope()

        try:
            self._execute_block(node.body)
        finally:
            self.runtime.pop_scope()

    def visit_export_declaration(self, node: ExportDeclaration) -> None:
        """Visit export declaration node"""
        # Execute the variable declaration
        self.visit_var_declaration(node.var_declaration)

        # Add to export system
        var_name = node.var_declaration.name
        var_value = self.runtime.get_variable(var_name)
        var_type = node.var_declaration.type_hint or "auto"

        self.runtime.export_system.add_export_variable(
            var_name, var_type, var_value,
            node.export_type, node.export_hint
        )

    def visit_export_group(self, node: ExportGroup) -> None:
        """Visit export group node"""
        self.runtime.export_system.add_export_group(node.name, node.prefix)

    def visit_extends_statement(self, node: ExtendsStatement) -> None:
        """Visit extends statement node"""
        # Store the base class information for inheritance
        # This will be used when creating script instances
        self.runtime.current_extends = node.base_class

    def visit_signal_declaration(self, node: SignalDeclaration) -> None:
        """Visit signal declaration node"""
        # For now, just define an empty signal function
        # A full implementation would create a proper signal object
        def signal_func(*args):
            pass

        self.runtime.define_variable(node.name, signal_func)

    def visit_enum_declaration(self, node: EnumDeclaration) -> None:
        """Visit enum declaration node"""
        # Create enum as a dictionary
        enum_dict = {}
        for i, value in enumerate(node.values):
            enum_dict[value] = i

        self.runtime.define_variable(node.name, enum_dict)

    # Utility methods
    def _execute_block(self, statements: List[Statement]) -> None:
        """Execute a block of statements"""
        for statement in statements:
            self.execute_statement(statement)

    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy"""
        if value is None or value is False:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, (str, list, dict)) and len(value) == 0:
            return False
        return True

    def _get_default_for_undefined_variable(self, name: str) -> Any:
        """Get a reasonable default value for common undefined variables"""
        from .builtins import Vector2, Rect2, Color, Texture

        # Common defaults for frequently used undefined variables
        defaults = {
            'current': False,
            'collision_mask': 1,
            'collision_layer': 1,
            'enable_animations': True,
            'texture': None,
            'null': None,
            'position': Vector2(0, 0),
            'global_position': Vector2(0, 0),
            'velocity': Vector2(0, 0),
            'scale': Vector2(1, 1),
            'rotation': 0.0,
            'visible': True,
            'modulate': Color(1, 1, 1, 1),
            'z_index': 0,
            'safe_margin': 0.08,
            'enabled': True,
            'max_stamina': 100.0,
            'hframes': 1,
            'vframes': 1,
            'frame': 0,
            'frame_x': 0,
            'frame_y': 0,
            'centered': True,
            'offset': Vector2(0, 0),
            'flip_h': False,
            'flip_v': False,
            'region_enabled': False,
            'region_rect': Rect2(0, 0, 0, 0),
            # Note: Function defaults removed - functions should be defined in first pass
        }

        return defaults.get(name)


def execute_lsc_script(source_code: str, runtime: LSCRuntime) -> None:
    """Execute LSC source code"""
    from .lexer import LSCLexer
    from .parser import LSCParser

    # Tokenize
    lexer = LSCLexer(source_code)
    tokens = lexer.tokenize()

    # Parse
    parser = LSCParser(tokens)
    ast = parser.parse()

    # Interpret
    interpreter = LSCInterpreter(runtime)
    interpreter.interpret(ast)
