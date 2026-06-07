"""
ll_parser.py - Non-Recursive Predictive (LL(1)) Parser for the Decaf mini-compiler.

Uses the LL(1) parse table built by grammar.Grammar.build_ll1_table().
Maintains an explicit stack and produces a derivation trace.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from tokens import Token, TokenType


class LLParser:
    """
    Table-driven LL(1) parser for Decaf.

    Algorithm:
      1. Push '$' and 'Program' onto the stack (top = 'Program').
      2. Repeat:
         a. If top == input symbol (terminal match), pop and advance.
         b. If top is a non-terminal, look up M[top, input] and expand.
         c. On error, do panic-mode recovery via FOLLOW sets.
      3. Accept when both stack and input are '$'.

    Trace format: list of (stack_str, lookahead_str, action_str)
    """

    def __init__(self, grammar, lexer, symbol_table, error_handler):
        self.grammar = grammar
        self.lexer = lexer
        self.st = symbol_table
        self.eh = error_handler
        # Build table if not already built
        if not hasattr(grammar, 'll1_table') or not grammar.ll1_table:
            self.table = grammar.build_ll1_table()
        else:
            self.table = grammar.ll1_table
        self.trace = []  # list of (stack_str, lookahead_val, action_str)

    def _stack_str(self, stack):
        """Pretty-print the stack (top on right)."""
        return ' '.join(stack)

    def parse(self):
        """
        Run the LL(1) parse. Returns the trace list.
        Each trace entry: (stack_snapshot, input_symbol, action_description)
        """
        stack = ['$', 'Program']   # top is last element
        current = self.lexer.next_token()
        step = 0
        max_steps = 100000  # safety limit

        while stack and stack[-1] != '$' and step < max_steps:
            step += 1
            top = stack[-1]
            sym = current.grammar_symbol()

            # --------------------------------------------------------
            # Terminal on top of stack
            # --------------------------------------------------------
            if top in self.grammar.terminals or top == '$':
                if top == sym:
                    # Match
                    action = f'match  {top!r}'
                    self.trace.append((
                        self._stack_str(stack),
                        f'{sym}({current.value!r})',
                        action
                    ))
                    stack.pop()
                    current = self.lexer.next_token()
                else:
                    # Terminal mismatch
                    suggestion = self.eh.phrase_level_suggest(top, sym)
                    self.eh.report_error(
                        'SYNTAX',
                        f"Expected '{top}', got '{sym}' ('{current.value}'). {suggestion}",
                        current.line, current.col
                    )
                    self.trace.append((
                        self._stack_str(stack),
                        f'{sym}({current.value!r})',
                        f'ERROR: expected {top!r}'
                    ))
                    # Error recovery: skip input token
                    current = self.lexer.next_token()
                    sym = current.grammar_symbol()
                continue

            # --------------------------------------------------------
            # Non-terminal on top of stack
            # --------------------------------------------------------
            if top in self.grammar.nonterminals:
                key = (top, sym)
                if key in self.table:
                    production = self.table[key]
                    rhs_str = ' '.join(production) if production else 'ε'
                    action = f'{top} -> {rhs_str}'
                    self.trace.append((
                        self._stack_str(stack),
                        f'{sym}({current.value!r})',
                        action
                    ))
                    stack.pop()
                    # Push production right-hand side in reverse order
                    for symbol in reversed(production):
                        stack.append(symbol)
                else:
                    # No entry in table: syntax error
                    self.eh.report_error(
                        'SYNTAX',
                        f"No production for ({top}, '{sym}') — unexpected token "
                        f"'{current.value}' at line {current.line}, col {current.col}",
                        current.line, current.col
                    )
                    self.trace.append((
                        self._stack_str(stack),
                        f'{sym}({current.value!r})',
                        f'ERROR: no production M[{top},{sym}]'
                    ))

                    # Panic-mode recovery
                    follow = self.grammar.follow_sets.get(top, set())
                    # Skip input tokens until we find one in FOLLOW(top) or FIRST of something useful
                    recovered = False
                    while current.type != TokenType.EOF:
                        sym = current.grammar_symbol()
                        if sym in follow:
                            # Pop the non-terminal (epsilon action)
                            stack.pop()
                            recovered = True
                            break
                        # Also check if sym is in the table for any non-terminal on stack
                        for s in reversed(stack):
                            if s in self.grammar.nonterminals:
                                if (s, sym) in self.table:
                                    # Pop everything above s
                                    while stack and stack[-1] != s:
                                        stack.pop()
                                    recovered = True
                                    break
                        if recovered:
                            break
                        current = self.lexer.next_token()

                    if not recovered:
                        # Give up on this non-terminal
                        if stack and stack[-1] == top:
                            stack.pop()
                continue

            # --------------------------------------------------------
            # Unknown symbol (shouldn't happen with correct grammar)
            # --------------------------------------------------------
            self.eh.report_error('SYNTAX',
                f"Parser internal error: unknown stack symbol '{top}'",
                current.line, current.col)
            stack.pop()

        # Final accept check
        sym = current.grammar_symbol()
        if (not stack or stack[-1] == '$') and sym == '$':
            self.trace.append(('$', '$', 'ACCEPT'))
        elif step >= max_steps:
            self.eh.report_error('SYNTAX',
                'LL(1) parser exceeded step limit (possible grammar cycle)',
                0, 0)

        return self.trace

    def print_trace(self, max_rows=200):
        """Pretty-print the parse trace."""
        print(f"\n{'='*80}")
        print("LL(1) PARSER TRACE")
        print('='*80)
        print(f"  {'Stack':<45} {'Input':<20} {'Action'}")
        print(f"  {'-'*45} {'-'*20} {'-'*30}")
        for i, (stk, inp, act) in enumerate(self.trace[:max_rows]):
            print(f"  {stk:<45} {inp:<20} {act}")
        if len(self.trace) > max_rows:
            print(f"  ... ({len(self.trace) - max_rows} more steps)")
        print('='*80)
