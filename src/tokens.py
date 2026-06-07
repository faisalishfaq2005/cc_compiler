"""
tokens.py - Token types and Token class for the Decaf mini-compiler.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    # Keywords
    KW_INT = auto()
    KW_DOUBLE = auto()
    KW_BOOL = auto()
    KW_STRING = auto()
    KW_CLASS = auto()
    KW_INTERFACE = auto()
    KW_NULL = auto()
    KW_THIS = auto()
    KW_EXTENDS = auto()
    KW_IMPLEMENTS = auto()
    KW_FOR = auto()
    KW_WHILE = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_RETURN = auto()
    KW_BREAK = auto()
    KW_NEW = auto()
    KW_NEWARRAY = auto()
    KW_PRINT = auto()
    KW_READINTEGER = auto()
    KW_READLINE = auto()
    KW_VOID = auto()
    KW_TRUE = auto()
    KW_FALSE = auto()
    # Literals
    INT_CONST = auto()
    DOUBLE_CONST = auto()
    BOOL_CONST = auto()
    STRING_CONST = auto()
    # Identifier
    IDENTIFIER = auto()
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    EQ = auto()
    NEQ = auto()
    ASSIGN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    # Punctuation
    SEMICOLON = auto()
    COMMA = auto()
    DOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    # Special
    EOF = auto()
    ERROR = auto()


KEYWORDS = {
    'void': TokenType.KW_VOID,
    'int': TokenType.KW_INT,
    'double': TokenType.KW_DOUBLE,
    'bool': TokenType.KW_BOOL,
    'string': TokenType.KW_STRING,
    'class': TokenType.KW_CLASS,
    'interface': TokenType.KW_INTERFACE,
    'null': TokenType.KW_NULL,
    'this': TokenType.KW_THIS,
    'extends': TokenType.KW_EXTENDS,
    'implements': TokenType.KW_IMPLEMENTS,
    'for': TokenType.KW_FOR,
    'while': TokenType.KW_WHILE,
    'if': TokenType.KW_IF,
    'else': TokenType.KW_ELSE,
    'return': TokenType.KW_RETURN,
    'break': TokenType.KW_BREAK,
    'New': TokenType.KW_NEW,
    'NewArray': TokenType.KW_NEWARRAY,
    'Print': TokenType.KW_PRINT,
    'ReadInteger': TokenType.KW_READINTEGER,
    'ReadLine': TokenType.KW_READLINE,
    'true': TokenType.KW_TRUE,
    'false': TokenType.KW_FALSE,
}


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    col: int

    def __repr__(self):
        return f'Token({self.type.name}, {self.value!r}, line={self.line}, col={self.col})'

    def grammar_symbol(self):
        """Return the grammar symbol string this token represents."""
        MAP = {
            TokenType.KW_INT: 'int',
            TokenType.KW_DOUBLE: 'double',
            TokenType.KW_BOOL: 'bool',
            TokenType.KW_STRING: 'string',
            TokenType.KW_CLASS: 'class',
            TokenType.KW_INTERFACE: 'interface',
            TokenType.KW_NULL: 'null',
            TokenType.KW_THIS: 'this',
            TokenType.KW_EXTENDS: 'extends',
            TokenType.KW_IMPLEMENTS: 'implements',
            TokenType.KW_FOR: 'for',
            TokenType.KW_WHILE: 'while',
            TokenType.KW_IF: 'if',
            TokenType.KW_ELSE: 'else',
            TokenType.KW_RETURN: 'return',
            TokenType.KW_BREAK: 'break',
            TokenType.KW_NEW: 'New',
            TokenType.KW_NEWARRAY: 'NewArray',
            TokenType.KW_PRINT: 'Print',
            TokenType.KW_READINTEGER: 'ReadInteger',
            TokenType.KW_READLINE: 'ReadLine',
            TokenType.KW_VOID: 'void',
            TokenType.KW_TRUE: 'BOOL_CONST',
            TokenType.KW_FALSE: 'BOOL_CONST',
            TokenType.INT_CONST: 'INT_CONST',
            TokenType.DOUBLE_CONST: 'DOUBLE_CONST',
            TokenType.BOOL_CONST: 'BOOL_CONST',
            TokenType.STRING_CONST: 'STRING_CONST',
            TokenType.IDENTIFIER: 'id',
            TokenType.PLUS: '+',
            TokenType.MINUS: '-',
            TokenType.STAR: '*',
            TokenType.SLASH: '/',
            TokenType.PERCENT: '%',
            TokenType.LT: '<',
            TokenType.LE: '<=',
            TokenType.GT: '>',
            TokenType.GE: '>=',
            TokenType.EQ: '==',
            TokenType.NEQ: '!=',
            TokenType.ASSIGN: '=',
            TokenType.AND: '&&',
            TokenType.OR: '||',
            TokenType.NOT: '!',
            TokenType.SEMICOLON: ';',
            TokenType.COMMA: ',',
            TokenType.DOT: '.',
            TokenType.LPAREN: '(',
            TokenType.RPAREN: ')',
            TokenType.LBRACE: '{',
            TokenType.RBRACE: '}',
            TokenType.LBRACKET: '[',
            TokenType.RBRACKET: ']',
            TokenType.EOF: '$',
        }
        return MAP.get(self.type, 'ERROR')
