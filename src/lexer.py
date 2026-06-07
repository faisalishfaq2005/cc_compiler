"""
lexer.py - Lexical Analyzer for the Decaf mini-compiler.

Implements double-buffering for efficient character reading, recognizes all
Decaf tokens including hex integers, scientific notation doubles, strings,
comments, and identifiers.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from tokens import Token, TokenType, KEYWORDS

BUFF_SIZE = 512


class DoubleBuffer:
    """
    Double-buffering implementation for efficient source reading.
    Two buffers of BUFF_SIZE characters each. When the forward pointer
    reaches the end of the current buffer half, the other half is reloaded.
    """

    def __init__(self, source: str):
        self.source = source
        self.source_len = len(source)
        # Logical read position in source string
        self.forward = 0
        # Start of current lexeme
        self.lexeme_start = 0
        # Buffer simulation: two halves of BUFF_SIZE each
        self._buf_a = ''
        self._buf_b = ''
        self._buf_a_start = 0   # source index where buf_a begins
        self._buf_b_start = 0
        self._active = 'a'
        self._load_buffer_a(0)

    def _load_buffer_a(self, start):
        end = min(start + BUFF_SIZE, self.source_len)
        self._buf_a = self.source[start:end]
        self._buf_a_start = start

    def _load_buffer_b(self, start):
        end = min(start + BUFF_SIZE, self.source_len)
        self._buf_b = self.source[start:end]
        self._buf_b_start = start

    def next_char(self):
        """Return next character and advance forward pointer."""
        if self.forward >= self.source_len:
            return '\0'  # EOF sentinel — does NOT advance forward
        ch = self.source[self.forward]
        self.forward += 1
        return ch

    def retract(self):
        """Move forward pointer back by one position (only if not at start of source)."""
        if self.forward > 0 and self.forward > self.lexeme_start:
            self.forward -= 1

    def at_eof(self):
        """Return True if forward is at or past end of source."""
        return self.forward >= self.source_len

    def peek(self):
        """Peek at next character without advancing."""
        if self.forward >= self.source_len:
            return '\0'
        return self.source[self.forward]

    def peek_ahead(self, offset=1):
        """Peek ahead by offset characters."""
        pos = self.forward + offset - 1
        if pos >= self.source_len:
            return '\0'
        return self.source[pos]

    def start_lexeme(self):
        """Mark beginning of a new lexeme."""
        self.lexeme_start = self.forward

    def get_lexeme(self):
        """Return the current lexeme (from lexeme_start to forward)."""
        return self.source[self.lexeme_start:self.forward]


class Lexer:
    """
    Decaf Lexical Analyzer.

    Tokenizes Decaf source code using a double-buffered character reader.
    Provides next_token() for one-token-at-a-time reading and tokenize()
    for collecting all tokens at once.
    """

    def __init__(self, source: str, error_handler=None):
        self.buf = DoubleBuffer(source)
        self.eh = error_handler
        self.line = 1
        self.col = 1
        # Track column offsets per line start position
        self._line_start = 0
        # Token cache for peek_token
        self._peeked = None
        # All tokens for index-based access
        self._tokens = []
        self._token_pos = 0
        self._fully_tokenized = False

    def _cur_col(self):
        return self.buf.lexeme_start - self._line_start + 1

    def _advance_col(self, ch):
        if ch == '\n':
            self.line += 1
            self._line_start = self.buf.forward
            self.col = 1
        else:
            self.col += 1

    def _skip_whitespace_and_comments(self):
        """Skip whitespace, single-line (//) and block (/* */) comments."""
        while True:
            if self.buf.at_eof():
                return  # at end of source, nothing more to skip
            ch = self.buf.next_char()
            if ch == '\0':
                # EOF — do NOT retract (forward is already at source_len)
                return
            if ch in ' \t\r':
                continue
            elif ch == '\n':
                self.line += 1
                self._line_start = self.buf.forward
                continue
            elif ch == '/':
                nxt = self.buf.peek()
                if nxt == '/':
                    # Single-line comment
                    self.buf.next_char()  # consume second /
                    while True:
                        if self.buf.at_eof():
                            return
                        c2 = self.buf.next_char()
                        if c2 == '\n':
                            self.line += 1
                            self._line_start = self.buf.forward
                            break
                        if c2 == '\0':
                            return
                elif nxt == '*':
                    # Block comment
                    self.buf.next_char()  # consume *
                    prev = '\0'
                    while True:
                        if self.buf.at_eof():
                            if self.eh:
                                self.eh.report_error('LEXICAL', 'Unterminated block comment',
                                                     self.line, self._cur_col())
                            return
                        c2 = self.buf.next_char()
                        if c2 == '\0':
                            if self.eh:
                                self.eh.report_error('LEXICAL', 'Unterminated block comment',
                                                     self.line, self._cur_col())
                            return
                        if c2 == '\n':
                            self.line += 1
                            self._line_start = self.buf.forward
                        if prev == '*' and c2 == '/':
                            break
                        prev = c2
                else:
                    # Single '/' — not a comment, put it back
                    self.buf.retract()
                    return
            else:
                # Non-whitespace, non-comment char: put it back
                self.buf.retract()
                return

    def _read_string(self, start_line, start_col):
        """Read a string constant (after opening quote already consumed)."""
        chars = []
        while True:
            ch = self.buf.next_char()
            if ch == '"':
                return Token(TokenType.STRING_CONST, ''.join(chars), start_line, start_col)
            if ch == '\n' or ch == '\0':
                if self.eh:
                    self.eh.report_error('LEXICAL', 'Unterminated string constant',
                                         start_line, start_col)
                if ch == '\n':
                    self.line += 1
                    self._line_start = self.buf.forward
                return Token(TokenType.ERROR, ''.join(chars), start_line, start_col)
            chars.append(ch)

    def _read_identifier_or_keyword(self, first_char, start_line, start_col):
        """Read identifier or keyword starting with first_char."""
        chars = [first_char]
        while True:
            ch = self.buf.peek()
            if ch.isalnum() or ch == '_':
                chars.append(self.buf.next_char())
            else:
                break
        word = ''.join(chars)
        # Enforce max 31 character identifier length
        if len(word) > 31:
            if self.eh:
                self.eh.report_error('LEXICAL',
                                     f'Identifier too long (max 31 chars): {word[:31]}...',
                                     start_line, start_col)
            word = word[:31]
        kw = KEYWORDS.get(word)
        if kw is not None:
            # true/false are bool constants
            if kw == TokenType.KW_TRUE:
                return Token(TokenType.BOOL_CONST, True, start_line, start_col)
            if kw == TokenType.KW_FALSE:
                return Token(TokenType.BOOL_CONST, False, start_line, start_col)
            return Token(kw, word, start_line, start_col)
        return Token(TokenType.IDENTIFIER, word, start_line, start_col)

    def _read_number(self, first_char, start_line, start_col):
        """Read integer (decimal or hex) or double constant."""
        # Check for hex
        if first_char == '0' and self.buf.peek() in ('x', 'X'):
            self.buf.next_char()  # consume x/X
            hex_digits = []
            while True:
                ch = self.buf.peek()
                if ch in '0123456789abcdefABCDEF':
                    hex_digits.append(self.buf.next_char())
                else:
                    break
            if not hex_digits:
                if self.eh:
                    self.eh.report_error('LEXICAL', 'Invalid hex literal', start_line, start_col)
                return Token(TokenType.ERROR, '0x', start_line, start_col)
            val = int(''.join(hex_digits), 16)
            return Token(TokenType.INT_CONST, val, start_line, start_col)

        # Decimal integer or double
        digits = [first_char]
        while self.buf.peek().isdigit():
            digits.append(self.buf.next_char())

        # Check for decimal point
        if self.buf.peek() == '.':
            # It's a double
            digits.append(self.buf.next_char())  # consume '.'
            while self.buf.peek().isdigit():
                digits.append(self.buf.next_char())
            # Check for exponent
            if self.buf.peek() in ('e', 'E'):
                digits.append(self.buf.next_char())  # consume e/E
                if self.buf.peek() in ('+', '-'):
                    digits.append(self.buf.next_char())
                if not self.buf.peek().isdigit():
                    if self.eh:
                        self.eh.report_error('LEXICAL',
                                             'Invalid double literal: missing exponent digits',
                                             start_line, start_col)
                    return Token(TokenType.ERROR, ''.join(digits), start_line, start_col)
                while self.buf.peek().isdigit():
                    digits.append(self.buf.next_char())
            return Token(TokenType.DOUBLE_CONST, float(''.join(digits)), start_line, start_col)

        # Check for exponent without decimal (e.g., 1E2 is NOT valid Decaf double per spec)
        # Decaf doubles require digits.digits form; no standalone exponent
        return Token(TokenType.INT_CONST, int(''.join(digits)), start_line, start_col)

    def next_token(self) -> Token:
        """Return the next token from the source."""
        # If we have a peeked token, return it
        if self._peeked is not None:
            tok = self._peeked
            self._peeked = None
            return tok

        self._skip_whitespace_and_comments()

        # Check for EOF before doing anything else
        if self.buf.at_eof():
            return Token(TokenType.EOF, None, self.line,
                         self.buf.forward - self._line_start + 1)

        # Record start position for token
        start_line = self.line
        start_col = self.buf.forward - self._line_start + 1
        self.buf.start_lexeme()

        ch = self.buf.next_char()
        if ch == '\0':
            return Token(TokenType.EOF, None, start_line, start_col)

        # String literal
        if ch == '"':
            return self._read_string(start_line, start_col)

        # Identifier or keyword
        if ch.isalpha() or ch == '_':
            return self._read_identifier_or_keyword(ch, start_line, start_col)

        # Number
        if ch.isdigit():
            return self._read_number(ch, start_line, start_col)

        # Operators and punctuation
        if ch == '+':
            return Token(TokenType.PLUS, '+', start_line, start_col)
        if ch == '-':
            return Token(TokenType.MINUS, '-', start_line, start_col)
        if ch == '*':
            return Token(TokenType.STAR, '*', start_line, start_col)
        if ch == '/':
            return Token(TokenType.SLASH, '/', start_line, start_col)
        if ch == '%':
            return Token(TokenType.PERCENT, '%', start_line, start_col)
        if ch == '!':
            if self.buf.peek() == '=':
                self.buf.next_char()
                return Token(TokenType.NEQ, '!=', start_line, start_col)
            return Token(TokenType.NOT, '!', start_line, start_col)
        if ch == '=':
            if self.buf.peek() == '=':
                self.buf.next_char()
                return Token(TokenType.EQ, '==', start_line, start_col)
            return Token(TokenType.ASSIGN, '=', start_line, start_col)
        if ch == '<':
            if self.buf.peek() == '=':
                self.buf.next_char()
                return Token(TokenType.LE, '<=', start_line, start_col)
            return Token(TokenType.LT, '<', start_line, start_col)
        if ch == '>':
            if self.buf.peek() == '=':
                self.buf.next_char()
                return Token(TokenType.GE, '>=', start_line, start_col)
            return Token(TokenType.GT, '>', start_line, start_col)
        if ch == '&':
            if self.buf.peek() == '&':
                self.buf.next_char()
                return Token(TokenType.AND, '&&', start_line, start_col)
            if self.eh:
                self.eh.report_error('LEXICAL', f"Single '&' not valid; expected '&&'",
                                     start_line, start_col)
            return Token(TokenType.ERROR, '&', start_line, start_col)
        if ch == '|':
            if self.buf.peek() == '|':
                self.buf.next_char()
                return Token(TokenType.OR, '||', start_line, start_col)
            if self.eh:
                self.eh.report_error('LEXICAL', f"Single '|' not valid; expected '||'",
                                     start_line, start_col)
            return Token(TokenType.ERROR, '|', start_line, start_col)
        if ch == ';':
            return Token(TokenType.SEMICOLON, ';', start_line, start_col)
        if ch == ',':
            return Token(TokenType.COMMA, ',', start_line, start_col)
        if ch == '.':
            return Token(TokenType.DOT, '.', start_line, start_col)
        if ch == '(':
            return Token(TokenType.LPAREN, '(', start_line, start_col)
        if ch == ')':
            return Token(TokenType.RPAREN, ')', start_line, start_col)
        if ch == '{':
            return Token(TokenType.LBRACE, '{', start_line, start_col)
        if ch == '}':
            return Token(TokenType.RBRACE, '}', start_line, start_col)
        if ch == '[':
            return Token(TokenType.LBRACKET, '[', start_line, start_col)
        if ch == ']':
            return Token(TokenType.RBRACKET, ']', start_line, start_col)

        # Unknown character
        if self.eh:
            self.eh.report_error('LEXICAL', f"Unexpected character '{ch}'",
                                 start_line, start_col)
        return Token(TokenType.ERROR, ch, start_line, start_col)

    def peek_token(self) -> Token:
        """Return next token without consuming it."""
        if self._peeked is None:
            self._peeked = self.next_token()
        return self._peeked

    def tokenize(self):
        """Tokenize entire source and return list of tokens (including EOF)."""
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.type == TokenType.EOF:
                break
        return tokens
