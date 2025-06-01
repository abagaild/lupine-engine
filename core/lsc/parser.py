"""
LSC Parser - Builds Abstract Syntax Tree from tokens
Implements recursive descent parsing for LSC language
"""

from typing import List, Optional, Union
from .lexer import Token, TokenType, LSCLexer
from .ast_nodes import *


class ParseError(Exception):
    """Parser error exception"""
    
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"{message} at line {token.line}, column {token.column}")


class LSCParser:
    """Recursive descent parser for LSC language"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        
    def parse(self) -> Program:
        """Parse tokens into AST"""
        statements = []
        
        while not self.is_at_end():
            # Skip newlines and comments at top level
            if self.check(TokenType.NEWLINE) or self.check(TokenType.COMMENT):
                self.advance()
                continue
                
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        
        return Program(statements)
    
    def statement(self) -> Optional[Statement]:
        """Parse a statement"""
        try:
            # Tool class
            if self.match(TokenType.TOOL):
                return self.class_declaration(is_tool=True)
            
            # Class declaration
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            
            # Function declaration
            if self.match(TokenType.FUNC):
                return self.function_declaration()
            
            # Export declarations
            if self.match(TokenType.EXPORT):
                return self.export_declaration()
            
            if self.match(TokenType.EXPORT_GROUP):
                return self.export_group()
            
            # Signal declaration
            if self.match(TokenType.SIGNAL):
                return self.signal_declaration()
            
            # Enum declaration
            if self.match(TokenType.ENUM):
                return self.enum_declaration()
            
            # Variable declaration
            if self.match(TokenType.VAR, TokenType.CONST):
                return self.var_declaration()
            
            # Control flow
            if self.match(TokenType.IF):
                return self.if_statement()
            
            if self.match(TokenType.WHILE):
                return self.while_statement()
            
            if self.match(TokenType.DO):
                return self.do_while_statement()
            
            if self.match(TokenType.FOR):
                return self.for_statement()
            
            if self.match(TokenType.BREAK):
                self.consume_newline()
                return BreakStatement()
            
            if self.match(TokenType.CONTINUE):
                self.consume_newline()
                return ContinueStatement()
            
            if self.match(TokenType.RETURN):
                return self.return_statement()
            
            if self.match(TokenType.PASS):
                self.consume_newline()
                return PassStatement()
            
            # Expression statement or assignment
            return self.expression_statement()
            
        except ParseError:
            # Synchronize on error
            self.synchronize()
            return None
    
    def class_declaration(self, is_tool: bool = False) -> ClassDef:
        """Parse class declaration"""
        name = self.consume(TokenType.IDENTIFIER, "Expected class name").value
        
        base_class = None
        if self.match(TokenType.EXTENDS):
            base_class = self.consume(TokenType.IDENTIFIER, "Expected base class name").value
        
        self.consume(TokenType.COLON, "Expected ':' after class declaration")
        self.consume_newline()
        
        body = self.block()
        
        return ClassDef(name, base_class, body, is_tool)
    
    def function_declaration(self) -> FunctionDef:
        """Parse function declaration"""
        name = self.consume(TokenType.IDENTIFIER, "Expected function name").value
        
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        
        parameters = []
        if not self.check(TokenType.RPAREN):
            parameters = self.parameter_list()
        
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")
        
        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.consume(TokenType.IDENTIFIER, "Expected return type").value
        
        self.consume(TokenType.COLON, "Expected ':' after function declaration")
        self.consume_newline()
        
        body = self.block()
        
        return FunctionDef(name, parameters, return_type, body)
    
    def parameter_list(self) -> List[Parameter]:
        """Parse function parameter list"""
        parameters = []
        
        parameters.append(self.parameter())
        
        while self.match(TokenType.COMMA):
            parameters.append(self.parameter())
        
        return parameters
    
    def parameter(self) -> Parameter:
        """Parse single parameter"""
        name = self.consume(TokenType.IDENTIFIER, "Expected parameter name").value
        
        type_hint = None
        if self.match(TokenType.COLON):
            type_hint = self.consume(TokenType.IDENTIFIER, "Expected parameter type").value
        
        default_value = None
        if self.match(TokenType.ASSIGN):
            default_value = self.expression()
        
        return Parameter(name, type_hint, default_value)
    
    def export_declaration(self) -> ExportDeclaration:
        """Parse export declaration"""
        # Check for export type hints
        export_type = None
        export_hint = None
        
        if self.match(TokenType.LPAREN):
            # Export with type hint: export(int, "range", "1,10")
            export_type = self.consume(TokenType.IDENTIFIER, "Expected export type").value
            
            if self.match(TokenType.COMMA):
                export_hint = self.consume(TokenType.STRING, "Expected export hint").value
            
            self.consume(TokenType.RPAREN, "Expected ')' after export hint")
        
        var_decl = self.var_declaration()
        
        return ExportDeclaration(var_decl, export_type, export_hint)
    
    def export_group(self) -> ExportGroup:
        """Parse export group"""
        self.consume(TokenType.LPAREN, "Expected '(' after export_group")
        name = self.consume(TokenType.STRING, "Expected group name").value
        
        prefix = None
        if self.match(TokenType.COMMA):
            prefix = self.consume(TokenType.STRING, "Expected group prefix").value
        
        self.consume(TokenType.RPAREN, "Expected ')' after export group")
        self.consume_newline()
        
        return ExportGroup(name, prefix)
    
    def signal_declaration(self) -> SignalDeclaration:
        """Parse signal declaration"""
        name = self.consume(TokenType.IDENTIFIER, "Expected signal name").value
        
        parameters = []
        if self.match(TokenType.LPAREN):
            if not self.check(TokenType.RPAREN):
                parameters = self.parameter_list()
            self.consume(TokenType.RPAREN, "Expected ')' after signal parameters")
        
        self.consume_newline()
        
        return SignalDeclaration(name, parameters)
    
    def enum_declaration(self) -> EnumDeclaration:
        """Parse enum declaration"""
        name = self.consume(TokenType.IDENTIFIER, "Expected enum name").value
        
        self.consume(TokenType.LBRACE, "Expected '{' after enum name")
        
        values = []
        if not self.check(TokenType.RBRACE):
            values.append(self.consume(TokenType.IDENTIFIER, "Expected enum value").value)
            
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RBRACE):
                    break
                values.append(self.consume(TokenType.IDENTIFIER, "Expected enum value").value)
        
        self.consume(TokenType.RBRACE, "Expected '}' after enum values")
        self.consume_newline()
        
        return EnumDeclaration(name, values)
    
    def var_declaration(self) -> VarDeclaration:
        """Parse variable declaration"""
        is_const = self.previous().type == TokenType.CONST
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name").value
        
        type_hint = None
        if self.match(TokenType.COLON):
            type_hint = self.consume(TokenType.IDENTIFIER, "Expected variable type").value
        
        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.expression()
        
        self.consume_newline()
        
        return VarDeclaration(name, type_hint, initializer, is_const)
    
    def if_statement(self) -> IfStatement:
        """Parse if statement"""
        condition = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after if condition")
        self.consume_newline()
        
        then_body = self.block()
        
        elif_clauses = []
        while self.match(TokenType.ELIF):
            elif_condition = self.expression()
            self.consume(TokenType.COLON, "Expected ':' after elif condition")
            self.consume_newline()
            elif_body = self.block()
            elif_clauses.append((elif_condition, elif_body))
        
        else_body = None
        if self.match(TokenType.ELSE):
            self.consume(TokenType.COLON, "Expected ':' after else")
            self.consume_newline()
            else_body = self.block()
        
        return IfStatement(condition, then_body, elif_clauses, else_body)
    
    def while_statement(self) -> WhileStatement:
        """Parse while statement"""
        condition = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after while condition")
        self.consume_newline()
        
        body = self.block()
        
        return WhileStatement(condition, body)

    def do_while_statement(self) -> DoWhileStatement:
        """Parse do-while statement"""
        self.consume(TokenType.COLON, "Expected ':' after do")
        self.consume_newline()

        body = self.block()

        self.consume(TokenType.WHILE, "Expected 'while' after do block")
        condition = self.expression()
        self.consume_newline()

        return DoWhileStatement(body, condition)

    def for_statement(self) -> ForStatement:
        """Parse for statement"""
        variable = self.consume(TokenType.IDENTIFIER, "Expected variable name").value
        self.consume(TokenType.IN, "Expected 'in' after for variable")
        iterable = self.expression()
        self.consume(TokenType.COLON, "Expected ':' after for clause")
        self.consume_newline()

        body = self.block()

        return ForStatement(variable, iterable, body)

    def return_statement(self) -> ReturnStatement:
        """Parse return statement"""
        value = None
        if not self.check(TokenType.NEWLINE):
            value = self.expression()

        self.consume_newline()

        return ReturnStatement(value)

    def expression_statement(self) -> Statement:
        """Parse expression statement or assignment"""
        expr = self.expression()

        # Check for assignment operators
        if self.match(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                     TokenType.MULTIPLY_ASSIGN, TokenType.DIVIDE_ASSIGN,
                     TokenType.MODULO_ASSIGN, TokenType.POWER_ASSIGN):
            operator = self.previous().value
            value = self.expression()
            self.consume_newline()
            return Assignment(expr, operator, value)

        self.consume_newline()
        return ExpressionStatement(expr)

    def block(self) -> List[Statement]:
        """Parse indented block of statements"""
        statements = []

        self.consume(TokenType.INDENT, "Expected indented block")

        while not self.check(TokenType.DEDENT) and not self.is_at_end():
            if self.check(TokenType.NEWLINE) or self.check(TokenType.COMMENT):
                self.advance()
                continue

            stmt = self.statement()
            if stmt:
                statements.append(stmt)

        self.consume(TokenType.DEDENT, "Expected end of block")

        return statements

    def expression(self) -> Expression:
        """Parse expression"""
        return self.ternary()

    def ternary(self) -> Expression:
        """Parse ternary conditional expression"""
        expr = self.logical_or()

        if self.match(TokenType.QUESTION):
            true_expr = self.expression()
            self.consume(TokenType.COLON, "Expected ':' in ternary expression")
            false_expr = self.expression()
            return TernaryOp(expr, true_expr, false_expr)

        return expr

    def logical_or(self) -> Expression:
        """Parse logical OR expression"""
        expr = self.logical_and()

        while self.match(TokenType.OR, TokenType.OR_OP):
            operator = self.previous().value
            right = self.logical_and()
            expr = BinaryOp(expr, operator, right)

        return expr

    def logical_and(self) -> Expression:
        """Parse logical AND expression"""
        expr = self.equality()

        while self.match(TokenType.AND, TokenType.AND_OP):
            operator = self.previous().value
            right = self.equality()
            expr = BinaryOp(expr, operator, right)

        return expr

    def equality(self) -> Expression:
        """Parse equality expression"""
        expr = self.comparison()

        while self.match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            operator = self.previous().value
            right = self.comparison()
            expr = BinaryOp(expr, operator, right)

        return expr

    def comparison(self) -> Expression:
        """Parse comparison expression"""
        expr = self.bitwise_or()

        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL,
                         TokenType.LESS, TokenType.LESS_EQUAL, TokenType.IN, TokenType.IS):
            operator = self.previous().value
            right = self.bitwise_or()
            expr = BinaryOp(expr, operator, right)

        return expr

    def bitwise_or(self) -> Expression:
        """Parse bitwise OR expression"""
        expr = self.bitwise_xor()

        while self.match(TokenType.BIT_OR):
            operator = self.previous().value
            right = self.bitwise_xor()
            expr = BinaryOp(expr, operator, right)

        return expr

    def bitwise_xor(self) -> Expression:
        """Parse bitwise XOR expression"""
        expr = self.bitwise_and()

        while self.match(TokenType.BIT_XOR):
            operator = self.previous().value
            right = self.bitwise_and()
            expr = BinaryOp(expr, operator, right)

        return expr

    def bitwise_and(self) -> Expression:
        """Parse bitwise AND expression"""
        expr = self.shift()

        while self.match(TokenType.BIT_AND):
            operator = self.previous().value
            right = self.shift()
            expr = BinaryOp(expr, operator, right)

        return expr

    def shift(self) -> Expression:
        """Parse shift expression"""
        expr = self.term()

        while self.match(TokenType.BIT_SHIFT_LEFT, TokenType.BIT_SHIFT_RIGHT):
            operator = self.previous().value
            right = self.term()
            expr = BinaryOp(expr, operator, right)

        return expr

    def term(self) -> Expression:
        """Parse addition/subtraction expression"""
        expr = self.factor()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous().value
            right = self.factor()
            expr = BinaryOp(expr, operator, right)

        return expr

    def factor(self) -> Expression:
        """Parse multiplication/division expression"""
        expr = self.power()

        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            operator = self.previous().value
            right = self.power()
            expr = BinaryOp(expr, operator, right)

        return expr

    def power(self) -> Expression:
        """Parse power expression"""
        expr = self.unary()

        if self.match(TokenType.POWER):
            operator = self.previous().value
            right = self.power()  # Right associative
            expr = BinaryOp(expr, operator, right)

        return expr

    def unary(self) -> Expression:
        """Parse unary expression"""
        if self.match(TokenType.NOT, TokenType.NOT_OP, TokenType.MINUS, TokenType.PLUS, TokenType.BIT_NOT):
            operator = self.previous().value
            expr = self.unary()
            return UnaryOp(operator, expr)

        return self.call()

    def call(self) -> Expression:
        """Parse function call and member access"""
        expr = self.primary()

        while True:
            if self.match(TokenType.LPAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "Expected property name after '.'").value
                expr = MemberAccess(expr, name)
            elif self.match(TokenType.LBRACKET):
                index = self.expression()
                self.consume(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexAccess(expr, index)
            else:
                break

        return expr

    def finish_call(self, callee: Expression) -> FunctionCall:
        """Parse function call arguments"""
        arguments = []

        if not self.check(TokenType.RPAREN):
            arguments.append(self.expression())
            while self.match(TokenType.COMMA):
                arguments.append(self.expression())

        self.consume(TokenType.RPAREN, "Expected ')' after arguments")

        return FunctionCall(callee, arguments)

    def primary(self) -> Expression:
        """Parse primary expression"""
        if self.match(TokenType.BOOLEAN):
            return Literal(self.previous().value == "true")

        if self.match(TokenType.NULL):
            return Literal(None)

        if self.match(TokenType.NUMBER):
            value = self.previous().value
            return Literal(float(value) if '.' in value else int(value))

        if self.match(TokenType.STRING):
            return Literal(self.previous().value)

        if self.match(TokenType.IDENTIFIER):
            return Identifier(self.previous().value)

        if self.match(TokenType.DOLLAR):
            # Node path
            if self.match(TokenType.STRING):
                return NodePath(self.previous().value)
            elif self.match(TokenType.IDENTIFIER):
                return NodePath(self.previous().value)
            else:
                raise ParseError("Expected node path after '$'", self.peek())

        if self.match(TokenType.LBRACKET):
            # Array literal
            elements = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.expression())
                while self.match(TokenType.COMMA):
                    elements.append(self.expression())

            self.consume(TokenType.RBRACKET, "Expected ']' after array elements")
            return ArrayLiteral(elements)

        if self.match(TokenType.LBRACE):
            # Dictionary literal
            pairs = []
            if not self.check(TokenType.RBRACE):
                key = self.expression()
                self.consume(TokenType.COLON, "Expected ':' after dictionary key")
                value = self.expression()
                pairs.append((key, value))

                while self.match(TokenType.COMMA):
                    if self.check(TokenType.RBRACE):
                        break
                    key = self.expression()
                    self.consume(TokenType.COLON, "Expected ':' after dictionary key")
                    value = self.expression()
                    pairs.append((key, value))

            self.consume(TokenType.RBRACE, "Expected '}' after dictionary elements")
            return DictionaryLiteral(pairs)

        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise ParseError("Expected expression", self.peek())

    # Utility methods
    def match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types"""
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type"""
        if self.is_at_end():
            return False
        return self.peek().type == token_type

    def advance(self) -> Token:
        """Consume current token and return it"""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        """Check if we're at end of tokens"""
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        """Return current token without consuming it"""
        return self.tokens[self.current]

    def previous(self) -> Token:
        """Return previous token"""
        return self.tokens[self.current - 1]

    def consume(self, token_type: TokenType, message: str) -> Token:
        """Consume token of expected type or raise error"""
        if self.check(token_type):
            return self.advance()

        current_token = self.peek()
        raise ParseError(message, current_token)

    def consume_newline(self) -> None:
        """Consume newline token if present"""
        if self.check(TokenType.NEWLINE):
            self.advance()

    def synchronize(self) -> None:
        """Synchronize parser after error"""
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.NEWLINE:
                return

            if self.peek().type in [TokenType.CLASS, TokenType.FUNC, TokenType.VAR,
                                   TokenType.FOR, TokenType.IF, TokenType.WHILE,
                                   TokenType.RETURN]:
                return

            self.advance()
