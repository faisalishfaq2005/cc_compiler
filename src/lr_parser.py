"""
lr_parser.py - SLR(1) Bottom-Up Parser for the Decaf mini-compiler.

Uses the SLR(1) action/goto tables built by grammar.Grammar.build_slr1_table().
Implements shift/reduce/accept actions with panic-mode error recovery.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from tokens import Token, TokenType


class LRParser:
    """
    SLR(1) parser for Decaf.

    Tables:
      action[state, terminal] = ('shift', new_state)
                               | ('reduce', prod_idx)
                               | ('accept',)
      goto[state, nonterminal] = new_state

    Parse algorithm:
      1. state_stack = [0], symbol_stack = ['$']
      2. Repeat:
         a. Look up action[state_stack[-1], lookahead]
         b. shift: push symbol and new state
         c. reduce A->α: pop |α| symbols/states, push A, goto[state, A]
         d. accept: done
         e. error: panic recovery
    """

    def __init__(self, grammar, lexer, symbol_table, error_handler):
        self.grammar = grammar
        self.lexer = lexer
        self.st = symbol_table
        self.eh = error_handler

        # Build tables (triggers LR(0) item construction if needed)
        if not hasattr(grammar, 'slr1_action'):
            action, goto, conflicts = grammar.build_slr1_table()
        else:
            action = grammar.slr1_action
            goto = grammar.slr1_goto
            conflicts = grammar.slr1_conflicts

        self.action = action
        self.goto = goto
        self.conflicts = conflicts
        self.trace = []

    def parse(self):
        """
        Run the SLR(1) parse. Returns the trace list.
        Each trace entry: (state_stack, symbol_stack, lookahead, action_str)
        """
        state_stack = [0]
        symbol_stack = ['$']
        current = self.lexer.next_token()
        step = 0
        max_steps = 200000  # safety limit

        while step < max_steps:
            step += 1
            state = state_stack[-1]
            sym = current.grammar_symbol()

            act = self.action.get((state, sym))

            # --------------------------------------------------------
            # Error
            # --------------------------------------------------------
            if act is None:
                self.eh.report_error(
                    'SYNTAX',
                    f"LR parse error: unexpected '{sym}' ('{current.value}') "
                    f"in state {state} at line {current.line}, col {current.col}",
                    current.line, current.col
                )
                self.trace.append((
                    list(state_stack[-5:]),
                    list(symbol_stack[-5:]),
                    sym,
                    f'ERROR in state {state}'
                ))

                # Panic-mode recovery:
                # 1. Try skipping the current input token
                # 2. If that doesn't help, pop states until we find a valid action
                recovered = False

                # First: try advancing input
                if current.type != TokenType.EOF:
                    next_tok = self.lexer.next_token()
                    next_sym = next_tok.grammar_symbol()
                    if (state, next_sym) in self.action:
                        current = next_tok
                        recovered = True

                if not recovered:
                    # Pop states until we find one with some valid action
                    while len(state_stack) > 1:
                        state_stack.pop()
                        if symbol_stack:
                            symbol_stack.pop()
                        top = state_stack[-1]
                        # Check if any terminal leads to a valid action from this state
                        has_action = any(
                            (top, t) in self.action
                            for t in self.grammar.terminals
                        )
                        if has_action:
                            recovered = True
                            break

                    if recovered:
                        # Skip input until we find a token valid in this state
                        top = state_stack[-1]
                        while current.type != TokenType.EOF:
                            sym = current.grammar_symbol()
                            if (top, sym) in self.action:
                                break
                            current = self.lexer.next_token()

                if not recovered or current.type == TokenType.EOF:
                    break
                continue

            # --------------------------------------------------------
            # Record trace step
            # --------------------------------------------------------
            self.trace.append((
                list(state_stack[-6:]),
                list(symbol_stack[-6:]),
                f'{sym}({current.value!r})',
                str(act)
            ))

            kind = act[0]

            # --------------------------------------------------------
            # Shift
            # --------------------------------------------------------
            if kind == 'shift':
                new_state = act[1]
                state_stack.append(new_state)
                symbol_stack.append(sym)
                current = self.lexer.next_token()

            # --------------------------------------------------------
            # Reduce
            # --------------------------------------------------------
            elif kind == 'reduce':
                prod_idx = act[1]
                if prod_idx < 0 or prod_idx >= len(self.grammar.productions):
                    self.eh.report_error('SYNTAX',
                        f'LR parser: invalid production index {prod_idx}',
                        current.line, current.col)
                    break
                lhs, rhs = self.grammar.productions[prod_idx]
                # Pop |rhs| symbols from both stacks
                pop_count = len(rhs)
                for _ in range(pop_count):
                    if state_stack:
                        state_stack.pop()
                    if symbol_stack:
                        symbol_stack.pop()
                # Push lhs
                symbol_stack.append(lhs)
                # Goto
                top_state = state_stack[-1]
                next_state = self.goto.get((top_state, lhs))
                if next_state is None:
                    self.eh.report_error('SYNTAX',
                        f'LR parser: no goto entry for (state={top_state}, NT={lhs})',
                        current.line, current.col)
                    break
                state_stack.append(next_state)

            # --------------------------------------------------------
            # Accept
            # --------------------------------------------------------
            elif kind == 'accept':
                self.trace.append((
                    list(state_stack),
                    list(symbol_stack),
                    '$',
                    'ACCEPT'
                ))
                break

        if step >= max_steps:
            self.eh.report_error('SYNTAX',
                'LR parser exceeded step limit', 0, 0)

        return self.trace

    def print_trace(self, max_rows=200):
        """Pretty-print the LR parse trace."""
        print(f"\n{'='*90}")
        print("SLR(1) PARSER TRACE")
        print('='*90)
        print(f"  {'States':<25} {'Symbols':<25} {'Input':<20} {'Action'}")
        print(f"  {'-'*25} {'-'*25} {'-'*20} {'-'*20}")
        for i, (states, syms, inp, act) in enumerate(self.trace[:max_rows]):
            st_str = str(states)
            sy_str = str(syms)
            print(f"  {st_str:<25} {sy_str:<25} {inp:<20} {act}")
        if len(self.trace) > max_rows:
            print(f"  ... ({len(self.trace) - max_rows} more steps)")
        print('='*90)
