"""
error_handler.py - Error Handler for the Decaf mini-compiler.

Provides:
  - CompilerError dataclass
  - ErrorHandler with error/warning reporting, panic-mode recovery,
    and phrase-level suggestions
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


class CompilerError:
    """
    Represents a single compiler error or warning.

    Attributes:
        kind    : 'LEXICAL', 'SYNTAX', 'SEMANTIC'
        message : human-readable error description
        line    : source line number
        col     : source column number
    """

    def __init__(self, kind: str, message: str, line: int, col: int):
        self.kind = kind
        self.message = message
        self.line = line
        self.col = col

    def __repr__(self):
        return f"[{self.kind}] Line {self.line}, Col {self.col}: {self.message}"

    def __lt__(self, other):
        return (self.line, self.col) < (other.line, other.col)


class CompilerWarning:
    """Represents a compiler warning."""

    def __init__(self, message: str, line: int, col: int):
        self.message = message
        self.line = line
        self.col = col

    def __repr__(self):
        return f"[WARNING] Line {self.line}, Col {self.col}: {self.message}"

    def __lt__(self, other):
        return (self.line, self.col) < (other.line, other.col)


class ErrorHandler:
    """
    Central error/warning manager for the compiler.

    Collects errors during compilation and provides:
      - report_error()  : record a compiler error
      - report_warning(): record a warning
      - has_errors()    : check if any errors were recorded
      - print_summary() : display all errors and warnings sorted by line
      - panic_mode_recover(): skip tokens until sync token found
      - phrase_level_suggest(): generate helpful "expected X, found Y" messages
    """

    MAX_ERRORS = 50  # Stop after this many errors to prevent cascade

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.error_count = 0

    def report_error(self, kind: str, message: str, line: int, col: int):
        """Record a compiler error."""
        if self.error_count >= self.MAX_ERRORS:
            return
        err = CompilerError(kind, message, line, col)
        self.errors.append(err)
        self.error_count += 1
        # Print immediately so users see progress
        print(f"  *** {err}", file=sys.stderr)

    def report_warning(self, message: str, line: int, col: int):
        """Record a warning (does not increment error_count)."""
        warn = CompilerWarning(message, line, col)
        self.warnings.append(warn)
        print(f"  *** {warn}", file=sys.stderr)

    def has_errors(self) -> bool:
        return self.error_count > 0

    def print_summary(self):
        """Print all errors and warnings sorted by source position."""
        print(f"\n{'-'*60}")
        if not self.errors and not self.warnings:
            print("  Compilation successful (no errors or warnings).")
        else:
            if self.errors:
                print(f"  ERRORS ({len(self.errors)}):")
                for err in sorted(self.errors):
                    print(f"    {err}")
            if self.warnings:
                print(f"  WARNINGS ({len(self.warnings)}):")
                for warn in sorted(self.warnings):
                    print(f"    {warn}")
            if self.error_count >= self.MAX_ERRORS:
                print(f"  (Too many errors - compilation aborted after {self.MAX_ERRORS})")
        print('-'*60)

    def clear(self):
        """Reset error/warning state."""
        self.errors.clear()
        self.warnings.clear()
        self.error_count = 0

    # ------------------------------------------------------------------
    # Recovery helpers
    # ------------------------------------------------------------------

    def panic_mode_recover(self, parser, sync_tokens: set):
        """
        Panic-mode error recovery: advance the parser's current token
        until we find a token in sync_tokens or EOF.

        parser must have:
          - parser.current : current Token
          - parser.advance(): consume next token
          - parser.lexer   : Lexer instance
        """
        from tokens import TokenType
        while parser.current.type != TokenType.EOF:
            sym = parser.current.grammar_symbol()
            if sym in sync_tokens:
                return
            parser.advance()

    def phrase_level_suggest(self, expected: str, found: str) -> str:
        """
        Generate a user-friendly suggestion message.

        Examples:
          - missing semicolon
          - wrong operator
        """
        suggestions = {
            (';', ','): "Did you use ',' instead of ';'?",
            (',', ';'): "Did you use ';' instead of ','?",
            (')', ']'): "Mismatched bracket: expected ')' but found ']'",
            (']', ')'): "Mismatched bracket: expected ']' but found ')'",
            ('}', ')'): "Mismatched brace: expected '}' but found ')'",
            ('==', '='): "Did you mean '==' (equality) instead of '=' (assignment)?",
            ('=', '=='): "Did you mean '=' (assignment) instead of '==' (equality)?",
        }
        hint = suggestions.get((expected, found), '')
        msg = f"Expected '{expected}', found '{found}'."
        if hint:
            msg += f" {hint}"
        return msg

    def error_summary_string(self) -> str:
        """Return error summary as a string."""
        lines = []
        lines.append('-'*60)
        if not self.errors and not self.warnings:
            lines.append("  Compilation successful (no errors or warnings).")
        else:
            if self.errors:
                lines.append(f"  ERRORS ({len(self.errors)}):")
                for err in sorted(self.errors):
                    lines.append(f"    {err}")
            if self.warnings:
                lines.append(f"  WARNINGS ({len(self.warnings)}):")
                for warn in sorted(self.warnings):
                    lines.append(f"    {warn}")
        lines.append('-'*60)
        return '\n'.join(lines)
