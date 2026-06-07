#!/usr/bin/env python3
"""
main.py - Main entry point for the Decaf Mini Compiler.

Usage:
  python main.py <source.decaf> [options]

Options:
  --lexer    Run lexer only
  --rd       Run recursive descent parser
  --ll       Run LL(1) non-recursive predictive parser
  --lr       Run SLR(1) bottom-up parser
  --symtab   Print symbol table after parsing
  --first    Print FIRST sets
  --follow   Print FOLLOW sets
  --ll-table Print LL(1) parse table
  --lr-table Print LR action/goto table
  --all      Run all modules (default if no specific module selected)
  --output   Output directory (default: 'output')
  --trace-limit  Max trace rows to print (default: 100)
"""

import sys
import os
import argparse

# Set stdout/stderr to UTF-8 on Windows to avoid encoding errors
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure src/ is on the path whether we run from root or src/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _THIS_DIR)


# ---------------------------------------------------------------------------
# AST pretty-printer
# ---------------------------------------------------------------------------

def print_ast(node, indent=0, file=None):
    """Recursively pretty-print an AST node."""
    out = file or sys.stdout
    if node is None:
        return
    if isinstance(node, dict):
        typ = node.get('type', '?')
        val = node.get('value', '')
        line = node.get('line', '')
        line_str = f'  [L{line}]' if line else ''
        val_str = f' = {val!r}' if val not in (None, '', [], {}) else ''
        print(' ' * (indent * 2) + f'[{typ}]{val_str}{line_str}', file=out)
        for child in node.get('children', []):
            print_ast(child, indent + 1, file=out)
    elif isinstance(node, list):
        for item in node:
            print_ast(item, indent, file=out)


def ast_to_string(node, indent=0):
    """Return AST as a string."""
    import io
    buf = io.StringIO()
    print_ast(node, indent, file=buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Section header helper
# ---------------------------------------------------------------------------

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Decaf Mini Compiler -Compiler Construction Lab',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('source', help='Source file (.decaf)')
    parser.add_argument('--lexer', action='store_true', help='Run lexer only')
    parser.add_argument('--rd', action='store_true', help='Run recursive descent parser')
    parser.add_argument('--ll', action='store_true', help='Run LL(1) parser')
    parser.add_argument('--lr', action='store_true', help='Run LR/SLR(1) parser')
    parser.add_argument('--symtab', action='store_true', help='Print symbol table')
    parser.add_argument('--first', action='store_true', help='Print FIRST sets')
    parser.add_argument('--follow', action='store_true', help='Print FOLLOW sets')
    parser.add_argument('--ll-table', action='store_true', help='Print LL(1) table')
    parser.add_argument('--lr-table', action='store_true', help='Print LR table')
    parser.add_argument('--all', action='store_true', help='Run all modules')
    parser.add_argument('--output', default='output', help='Output directory')
    parser.add_argument('--trace-limit', type=int, default=100,
                        help='Max trace rows to print (default: 100)')
    args = parser.parse_args()

    # Determine which modules to run
    run_all = args.all or not any([args.lexer, args.rd, args.ll, args.lr])

    # Read source file
    if not os.path.exists(args.source):
        print(f"Error: File not found: {args.source}", file=sys.stderr)
        sys.exit(1)
    with open(args.source, 'r', encoding='utf-8') as f:
        source = f.read()

    base_name = os.path.splitext(os.path.basename(args.source))[0]
    os.makedirs(args.output, exist_ok=True)

    print(f"\nDecaf Mini Compiler")
    print(f"  Source : {args.source}")
    print(f"  Output : {args.output}/")

    # ----------------------------------------------------------------
    # Build Grammar (shared across all parsers)
    # ----------------------------------------------------------------
    from grammar import Grammar, PRODUCTIONS
    from error_handler import ErrorHandler

    print("\nBuilding grammar (FIRST/FOLLOW sets)...", end=' ', flush=True)
    grammar = Grammar(PRODUCTIONS)
    grammar.compute_first_sets()
    grammar.compute_follow_sets()
    print("done.")

    # Print FIRST/FOLLOW if requested
    if args.first or args.follow or run_all:
        if args.first or run_all:
            section("FIRST SETS")
            for nt in sorted(grammar.nonterminals):
                fs = sorted(grammar.first_sets.get(nt, set()))
                print(f"  FIRST({nt:<20}) = {{ {', '.join(fs)} }}")
        if args.follow or run_all:
            section("FOLLOW SETS")
            for nt in sorted(grammar.nonterminals):
                fol = sorted(grammar.follow_sets.get(nt, set()))
                print(f"  FOLLOW({nt:<20}) = {{ {', '.join(fol)} }}")

    # Print LL(1) table if requested
    if args.ll_table or run_all:
        grammar.build_ll1_table()
        grammar.print_ll1_table()

    # ----------------------------------------------------------------
    # LEXER
    # ----------------------------------------------------------------
    if run_all or args.lexer:
        from lexer import Lexer
        section("LEXER OUTPUT")

        eh = ErrorHandler()
        lex = Lexer(source, eh)
        tokens = lex.tokenize()

        for tok in tokens:
            print(f"  {tok}")

        out_path = os.path.join(args.output, f'{base_name}_lexer.txt')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"LEXER OUTPUT -{args.source}\n")
            f.write('='*60 + '\n')
            for tok in tokens:
                f.write(str(tok) + '\n')
            f.write('\n' + eh.error_summary_string())
        print(f"\n  [Lexer] {len(tokens)} tokens. Output -> {out_path}")
        eh.print_summary()

    # ----------------------------------------------------------------
    # RECURSIVE DESCENT PARSER
    # ----------------------------------------------------------------
    if run_all or args.rd:
        from lexer import Lexer
        from rd_parser import RecursiveDescentParser
        from symbol_table import SymbolTable
        section("RECURSIVE DESCENT PARSER")

        eh = ErrorHandler()
        st = SymbolTable()
        lex = Lexer(source, eh)
        rdp = RecursiveDescentParser(lex, st, eh)
        ast = rdp.parse()

        print(f"\n  AST ({rdp.tokens_parsed} tokens processed):")
        print_ast(ast, indent=1)

        if args.symtab or run_all:
            st.dump("Symbol Table after RD Parse")

        eh.print_summary()

        out_path = os.path.join(args.output, f'{base_name}_rd_parser.txt')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"RD PARSER OUTPUT -{args.source}\n")
            f.write('='*60 + '\n\n')
            f.write("AST:\n")
            f.write(ast_to_string(ast, indent=1))
            f.write('\n')
            f.write(st.dump_to_string("Symbol Table"))
            f.write('\n')
            f.write(eh.error_summary_string())
        print(f"\n  [RD Parser] Output -> {out_path}")

    # ----------------------------------------------------------------
    # LL(1) PARSER
    # ----------------------------------------------------------------
    if run_all or args.ll:
        from lexer import Lexer
        from ll_parser import LLParser
        from symbol_table import SymbolTable
        section("LL(1) PARSER (Non-Recursive Predictive)")

        eh = ErrorHandler()
        st = SymbolTable()
        lex = Lexer(source, eh)
        llp = LLParser(grammar, lex, st, eh)
        trace = llp.parse()

        limit = args.trace_limit
        print(f"\n  Parse trace ({len(trace)} steps, showing first {min(limit, len(trace))}):")
        print(f"  {'Stack':<48} {'Input':<22} {'Action'}")
        print(f"  {'-'*48} {'-'*22} {'-'*30}")
        for stk, inp, act in trace[:limit]:
            print(f"  {stk:<48} {inp:<22} {act}")
        if len(trace) > limit:
            print(f"  ... ({len(trace) - limit} more steps -use --trace-limit N to show more)")

        eh.print_summary()

        out_path = os.path.join(args.output, f'{base_name}_ll_parser.txt')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"LL(1) PARSER OUTPUT -{args.source}\n")
            f.write('='*80 + '\n\n')
            f.write(f"{'Stack':<48} {'Input':<22} {'Action'}\n")
            f.write(f"{'-'*48} {'-'*22} {'-'*30}\n")
            for stk, inp, act in trace:
                f.write(f"{stk:<48} {inp:<22} {act}\n")
            f.write('\n' + eh.error_summary_string())
        print(f"\n  [LL Parser] {len(trace)} steps. Output -> {out_path}")

    # ----------------------------------------------------------------
    # SLR(1) / LR PARSER
    # ----------------------------------------------------------------
    if run_all or args.lr:
        from lexer import Lexer
        from lr_parser import LRParser
        from symbol_table import SymbolTable
        section("SLR(1) PARSER (Bottom-Up)")

        # Build SLR table
        print("  Building SLR(1) tables...", end=' ', flush=True)
        action, goto_tbl, conflicts = grammar.build_slr1_table()
        print(f"done. ({len(grammar._lr0_states)} states, {len(conflicts)} conflicts)")

        if args.lr_table or run_all:
            grammar.print_lr_table()

        if conflicts:
            print(f"\n  Conflicts ({len(conflicts)}):")
            for c in conflicts[:10]:
                print(f"    {c}")

        eh = ErrorHandler()
        st = SymbolTable()
        lex = Lexer(source, eh)
        lrp = LRParser(grammar, lex, st, eh)
        trace = lrp.parse()

        limit = args.trace_limit
        print(f"\n  Parse trace ({len(trace)} steps, showing first {min(limit, len(trace))}):")
        print(f"  {'States':<28} {'Symbols':<28} {'Input':<18} {'Action'}")
        print(f"  {'-'*28} {'-'*28} {'-'*18} {'-'*20}")
        for states, syms, inp, act in trace[:limit]:
            print(f"  {str(states):<28} {str(syms):<28} {inp:<18} {act}")
        if len(trace) > limit:
            print(f"  ... ({len(trace) - limit} more steps)")

        eh.print_summary()

        out_path = os.path.join(args.output, f'{base_name}_lr_parser.txt')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"SLR(1) PARSER OUTPUT -{args.source}\n")
            f.write('='*90 + '\n\n')
            f.write(f"States: {len(grammar._lr0_states)}, "
                    f"Conflicts: {len(conflicts)}\n\n")
            f.write(f"{'States':<28} {'Symbols':<28} {'Input':<18} {'Action'}\n")
            f.write(f"{'-'*28} {'-'*28} {'-'*18} {'-'*20}\n")
            for states, syms, inp, act in trace:
                f.write(f"{str(states):<28} {str(syms):<28} {inp:<18} {act}\n")
            f.write('\n' + eh.error_summary_string())
        print(f"\n  [LR Parser] {len(trace)} steps. Output -> {out_path}")

    print(f"\n{'='*70}")
    print("  Compilation finished.")
    print('='*70)


if __name__ == '__main__':
    main()
