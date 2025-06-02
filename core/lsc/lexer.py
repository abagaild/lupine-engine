"""
LSC Lexer - Tokenizes LSC source code
Handles all LSC language tokens including keywords, operators, literals, etc.
"""

import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Iterator


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()
    
    # Identifiers
    IDENTIFIER = auto()
    
    # Keywords
    CLASS = auto()
    EXTENDS = auto()
    FUNC = auto()
    VAR = auto()
    CONST = auto()
    EXPORT = auto()
    EXPORT_GROUP = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    DO = auto()
    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()
    PASS = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    IS = auto()
    AS = auto()
    MATCH = auto()
    WHEN = auto()
    SIGNAL = auto()
    ENUM = auto()
    STATIC = auto()
    TOOL = auto()
    
    # Built-in lifecycle methods
    READY = auto()
    PROCESS = auto()
    INPUT = auto()
    PHYSICS_PROCESS = auto()
    DRAW = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    POWER = auto()
    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    MULTIPLY_ASSIGN = auto()
    DIVIDE_ASSIGN = auto()
    MODULO_ASSIGN = auto()
    POWER_ASSIGN = auto()
    
    # Comparison
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    
    # Logical
    AND_OP = auto()
    OR_OP = auto()
    NOT_OP = auto()
    
    # Bitwise
    BIT_AND = auto()
    BIT_OR = auto()
    BIT_XOR = auto()
    BIT_NOT = auto()
    BIT_SHIFT_LEFT = auto()
    BIT_SHIFT_RIGHT = auto()
    
    # Punctuation
    DOT = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    ARROW = auto()
    QUESTION = auto()  # For ternary operator
    
    # Brackets
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    
    # Special
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()
    COMMENT = auto()
    
    # Node path operator
    DOLLAR = auto()  # For $NodePath
    
    # Type hints
    TYPE_HINT = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class LSCLexer:
    """Lexer for LSC (Lupine Script) language"""
    
    # Keywords mapping
    KEYWORDS = {
        'class': TokenType.CLASS,
        'extends': TokenType.EXTENDS,
        'func': TokenType.FUNC,
        'var': TokenType.VAR,
        'const': TokenType.CONST,
        'export': TokenType.EXPORT,
        'export_group': TokenType.EXPORT_GROUP,
        'if': TokenType.IF,
        'elif': TokenType.ELIF,
        'else': TokenType.ELSE,
        'for': TokenType.FOR,
        'while': TokenType.WHILE,
        'do': TokenType.DO,
        'break': TokenType.BREAK,
        'continue': TokenType.CONTINUE,
        'return': TokenType.RETURN,
        'pass': TokenType.PASS,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
        'in': TokenType.IN,
        'is': TokenType.IS,
        'as': TokenType.AS,
        'match': TokenType.MATCH,
        'when': TokenType.WHEN,
        'signal': TokenType.SIGNAL,
        'enum': TokenType.ENUM,
        'static': TokenType.STATIC,
        'tool': TokenType.TOOL,
        'true': TokenType.BOOLEAN,
        'false': TokenType.BOOLEAN,
        'null': TokenType.NULL,
        '_ready': TokenType.READY,
        '_process': TokenType.PROCESS,
        '_input': TokenType.INPUT,
        '_physics_process': TokenType.PHYSICS_PROCESS,
        '_draw': TokenType.DRAW,
    }
    
    # Operator patterns
    OPERATORS = [
        ('**=', TokenType.POWER_ASSIGN),
        ('+=', TokenType.PLUS_ASSIGN),
        ('-=', TokenType.MINUS_ASSIGN),
        ('*=', TokenType.MULTIPLY_ASSIGN),
        ('/=', TokenType.DIVIDE_ASSIGN),
        ('%=', TokenType.MODULO_ASSIGN),
        ('==', TokenType.EQUAL),
        ('!=', TokenType.NOT_EQUAL),
        ('<=', TokenType.LESS_EQUAL),
        ('>=', TokenType.GREATER_EQUAL),
        ('<<', TokenType.BIT_SHIFT_LEFT),
        ('>>', TokenType.BIT_SHIFT_RIGHT),
        ('->', TokenType.ARROW),
        ('&&', TokenType.AND_OP),
        ('||', TokenType.OR_OP),
        ('**', TokenType.POWER),
        ('+', TokenType.PLUS),
        ('-', TokenType.MINUS),
        ('*', TokenType.MULTIPLY),
        ('/', TokenType.DIVIDE),
        ('%', TokenType.MODULO),
        ('=', TokenType.ASSIGN),
        ('<', TokenType.LESS),
        ('>', TokenType.GREATER),
        ('&', TokenType.BIT_AND),
        ('|', TokenType.BIT_OR),
        ('^', TokenType.BIT_XOR),
        ('~', TokenType.BIT_NOT),
        ('!', TokenType.NOT_OP),
        ('?', TokenType.QUESTION),
    ]
    
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]  # Track indentation levels
        
    def current_char(self) -> Optional[str]:
        """Get current character"""
        if self.position >= len(self.source):
            return None
        return self.source[self.position]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Peek at character ahead"""
        pos = self.position + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> None:
        """Move to next character"""
        if self.position < len(self.source) and self.source[self.position] == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1
    
    def skip_whitespace(self) -> None:
        """Skip whitespace except newlines"""
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()
    
    def read_string(self, quote_char: str) -> str:
        """Read string literal"""
        value = ''
        self.advance()  # Skip opening quote
        
        while self.current_char() and self.current_char() != quote_char:
            if self.current_char() == '\\':
                self.advance()
                escape_char = self.current_char()
                if escape_char == 'n':
                    value += '\n'
                elif escape_char == 't':
                    value += '\t'
                elif escape_char == 'r':
                    value += '\r'
                elif escape_char == '\\':
                    value += '\\'
                elif escape_char == quote_char:
                    value += quote_char
                else:
                    value += escape_char or ''
                self.advance()
            else:
                value += self.current_char()
                self.advance()
        
        if self.current_char() == quote_char:
            self.advance()  # Skip closing quote
        
        return value
    
    def read_number(self) -> str:
        """Read numeric literal"""
        value = ''
        has_dot = False
        
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if has_dot:
                    break
                has_dot = True
            value += self.current_char()
            self.advance()
        
        return value
    
    def read_identifier(self) -> str:
        """Read identifier or keyword"""
        value = ''
        
        while (self.current_char() and 
               (self.current_char().isalnum() or self.current_char() in '_')):
            value += self.current_char()
            self.advance()
        
        return value

    def read_comment(self) -> str:
        """Read comment"""
        value = ''

        while self.current_char() and self.current_char() != '\n':
            char = self.current_char()
            if char:
                value += char
            self.advance()

        return value

    def handle_indentation(self) -> List[Token]:
        """Handle indentation at start of line"""
        tokens = []
        indent_level = 0

        # Count indentation
        char = self.current_char()
        while char and char in ' \t':
            if char == '\t':
                indent_level += 4  # Tab = 4 spaces
            else:
                indent_level += 1
            self.advance()
            char = self.current_char()

        # Skip empty lines
        if char == '\n' or char == '#':
            return tokens

        current_indent = self.indent_stack[-1]

        if indent_level > current_indent:
            # Increased indentation
            self.indent_stack.append(indent_level)
            tokens.append(Token(TokenType.INDENT, '', self.line, self.column))
        elif indent_level < current_indent:
            # Decreased indentation
            while self.indent_stack and self.indent_stack[-1] > indent_level:
                self.indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, '', self.line, self.column))

        return tokens

    def tokenize(self) -> List[Token]:
        """Tokenize the source code"""
        self.tokens = []
        at_line_start = True

        while self.position < len(self.source):
            char = self.current_char()

            if char is None:
                break

            # Handle indentation at start of line
            if at_line_start:
                if char in ' \t':
                    indent_tokens = self.handle_indentation()
                    self.tokens.extend(indent_tokens)
                    at_line_start = False
                    continue
                elif char not in '\n#':
                    # Non-whitespace at start of line - check for dedents
                    indent_tokens = self.handle_indentation()
                    self.tokens.extend(indent_tokens)
                    at_line_start = False
                    # Don't continue - process the character normally

            # Newline
            if char == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, char, self.line, self.column))
                self.advance()
                at_line_start = True
                continue

            at_line_start = False

            # Skip whitespace
            if char in ' \t\r':
                self.skip_whitespace()
                continue

            # Comments
            if char == '#':
                comment = self.read_comment()
                self.tokens.append(Token(TokenType.COMMENT, comment, self.line, self.column))
                continue

            # String literals
            if char in '"\'':
                string_value = self.read_string(char)
                self.tokens.append(Token(TokenType.STRING, string_value, self.line, self.column))
                continue

            # Numbers
            if char.isdigit():
                number_value = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, number_value, self.line, self.column))
                continue

            # Identifiers and keywords
            if char.isalpha() or char == '_':
                identifier = self.read_identifier()
                token_type = self.KEYWORDS.get(identifier, TokenType.IDENTIFIER)
                self.tokens.append(Token(token_type, identifier, self.line, self.column))
                continue

            # Node path operator
            if char == '$':
                self.tokens.append(Token(TokenType.DOLLAR, char, self.line, self.column))
                self.advance()
                continue

            # Operators (check longest first)
            operator_found = False
            for op_str, op_type in self.OPERATORS:
                if self.source[self.position:].startswith(op_str):
                    self.tokens.append(Token(op_type, op_str, self.line, self.column))
                    for _ in range(len(op_str)):
                        self.advance()
                    operator_found = True
                    break

            if operator_found:
                continue

            # Punctuation
            punctuation_map = {
                '.': TokenType.DOT,
                ',': TokenType.COMMA,
                ':': TokenType.COLON,
                ';': TokenType.SEMICOLON,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
            }

            if char in punctuation_map:
                self.tokens.append(Token(punctuation_map[char], char, self.line, self.column))
                self.advance()
                continue

            # Unknown character
            raise SyntaxError(f"Unexpected character '{char}' at line {self.line}, column {self.column}")

        # Add final dedents
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, '', self.line, self.column))

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))

        return self.tokens

    def __iter__(self) -> Iterator[Token]:
        """Make lexer iterable"""
        if not self.tokens:
            self.tokenize()
        return iter(self.tokens)
