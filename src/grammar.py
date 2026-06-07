"""
grammar.py - Grammar definitions, FIRST/FOLLOW set computation, and parse table
construction for the Decaf mini-compiler.

Contains:
  - PRODUCTIONS: list of all grammar productions as (lhs, rhs) tuples
  - Grammar class with FIRST/FOLLOW computation and LL(1)/SLR(1) table building
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Production rules
# Each entry: (lhs: str, rhs: tuple[str, ...])
# Empty tuple () represents epsilon (ε)
# ---------------------------------------------------------------------------

PRODUCTIONS = [
    # 0: Program -> DeclList
    ('Program', ('DeclList',)),

    # 1: DeclList -> Decl DeclList
    ('DeclList', ('Decl', 'DeclList')),
    # 2: DeclList -> ε
    ('DeclList', ()),

    # 3: Decl -> ClassDecl
    ('Decl', ('ClassDecl',)),
    # 4: Decl -> InterfaceDecl
    ('Decl', ('InterfaceDecl',)),
    # 5: Decl -> void id ( Formals ) Block   [void-return function]
    ('Decl', ('void', 'id', '(', 'Formals', ')', 'Block')),
    # 6: Decl -> Type id DeclRest   [handles both VarDecl and typed FuncDecl]
    ('Decl', ('Type', 'id', 'DeclRest')),

    # 6a: DeclRest -> ;              [Variable declaration]
    ('DeclRest', (';',)),
    # 6b: DeclRest -> ( Formals ) Block   [Function declaration]
    ('DeclRest', ('(', 'Formals', ')', 'Block')),

    # 7: VarDecl -> Type id ;
    ('VarDecl', ('Type', 'id', ';')),

    # 8: FuncDecl -> RetType id ( Formals ) Block
    ('FuncDecl', ('RetType', 'id', '(', 'Formals', ')', 'Block')),

    # 9: RetType -> Type
    ('RetType', ('Type',)),
    # 10: RetType -> void
    ('RetType', ('void',)),

    # 11: Type -> int TypeSuffix
    ('Type', ('int', 'TypeSuffix')),
    # 12: Type -> double TypeSuffix
    ('Type', ('double', 'TypeSuffix')),
    # 13: Type -> bool TypeSuffix
    ('Type', ('bool', 'TypeSuffix')),
    # 14: Type -> string TypeSuffix
    ('Type', ('string', 'TypeSuffix')),
    # 15: Type -> id TypeSuffix
    ('Type', ('id', 'TypeSuffix')),

    # 16: TypeSuffix -> [ ] TypeSuffix
    ('TypeSuffix', ('[', ']', 'TypeSuffix')),
    # 17: TypeSuffix -> ε
    ('TypeSuffix', ()),

    # 18: Formals -> ParamList
    ('Formals', ('ParamList',)),
    # 19: Formals -> ε
    ('Formals', ()),

    # 20: ParamList -> Param ParamTail
    ('ParamList', ('Param', 'ParamTail')),

    # 21: ParamTail -> , Param ParamTail
    ('ParamTail', (',', 'Param', 'ParamTail')),
    # 22: ParamTail -> ε
    ('ParamTail', ()),

    # 23: Param -> Type id
    ('Param', ('Type', 'id')),

    # 24: ClassDecl -> class id ClassBase ClassImpl { FieldList }
    ('ClassDecl', ('class', 'id', 'ClassBase', 'ClassImpl', '{', 'FieldList', '}')),

    # 25: ClassBase -> extends id
    ('ClassBase', ('extends', 'id')),
    # 26: ClassBase -> ε
    ('ClassBase', ()),

    # 27: ClassImpl -> implements IdentList
    ('ClassImpl', ('implements', 'IdentList')),
    # 28: ClassImpl -> ε
    ('ClassImpl', ()),

    # 29: IdentList -> id IdentListTail
    ('IdentList', ('id', 'IdentListTail')),

    # 30: IdentListTail -> , id IdentListTail
    ('IdentListTail', (',', 'id', 'IdentListTail')),
    # 31: IdentListTail -> ε
    ('IdentListTail', ()),

    # 32: FieldList -> Field FieldList
    ('FieldList', ('Field', 'FieldList')),
    # 33: FieldList -> ε
    ('FieldList', ()),

    # 34: Field -> void id ( Formals ) Block   [void-return method]
    ('Field', ('void', 'id', '(', 'Formals', ')', 'Block')),
    # 35: Field -> Type id FieldRest   [handles VarDecl and typed FuncDecl in class body]
    ('Field', ('Type', 'id', 'FieldRest')),

    # 35a: FieldRest -> ;              [class variable declaration]
    ('FieldRest', (';',)),
    # 35b: FieldRest -> ( Formals ) Block   [class method declaration]
    ('FieldRest', ('(', 'Formals', ')', 'Block')),

    # 36: InterfaceDecl -> interface id { ProtoList }
    ('InterfaceDecl', ('interface', 'id', '{', 'ProtoList', '}')),

    # 37: ProtoList -> Proto ProtoList
    ('ProtoList', ('Proto', 'ProtoList')),
    # 38: ProtoList -> ε
    ('ProtoList', ()),

    # 39: Proto -> RetType id ( Formals ) ;
    ('Proto', ('RetType', 'id', '(', 'Formals', ')', ';')),

    # 40: Block -> { StmtList }
    ('Block', ('{', 'StmtList', '}')),

    # 41: StmtList -> Stmt StmtList
    ('StmtList', ('Stmt', 'StmtList')),
    # 42: StmtList -> ε
    ('StmtList', ()),

    # 43: Stmt -> VarDecl
    ('Stmt', ('VarDecl',)),
    # 44: Stmt -> ExprStmt
    ('Stmt', ('ExprStmt',)),
    # 45: Stmt -> IfStmt
    ('Stmt', ('IfStmt',)),
    # 46: Stmt -> WhileStmt
    ('Stmt', ('WhileStmt',)),
    # 47: Stmt -> ForStmt
    ('Stmt', ('ForStmt',)),
    # 48: Stmt -> ReturnStmt
    ('Stmt', ('ReturnStmt',)),
    # 49: Stmt -> BreakStmt
    ('Stmt', ('BreakStmt',)),
    # 50: Stmt -> PrintStmt
    ('Stmt', ('PrintStmt',)),
    # 51: Stmt -> Block
    ('Stmt', ('Block',)),

    # 52: ExprStmt -> Expr ;
    ('ExprStmt', ('Expr', ';')),

    # 53: IfStmt -> if ( Expr ) Stmt ElsePart
    ('IfStmt', ('if', '(', 'Expr', ')', 'Stmt', 'ElsePart')),

    # 54: ElsePart -> else Stmt
    ('ElsePart', ('else', 'Stmt')),
    # 55: ElsePart -> ε
    ('ElsePart', ()),

    # 56: WhileStmt -> while ( Expr ) Stmt
    ('WhileStmt', ('while', '(', 'Expr', ')', 'Stmt')),

    # 57: ForStmt -> for ( ForInit ; Expr ; ForUpdate ) Stmt
    ('ForStmt', ('for', '(', 'ForInit', ';', 'Expr', ';', 'ForUpdate', ')', 'Stmt')),

    # 58: ForInit -> Expr
    ('ForInit', ('Expr',)),
    # 59: ForInit -> ε
    ('ForInit', ()),

    # 60: ForUpdate -> Expr
    ('ForUpdate', ('Expr',)),
    # 61: ForUpdate -> ε
    ('ForUpdate', ()),

    # 62: ReturnStmt -> return RetExprOpt ;
    ('ReturnStmt', ('return', 'RetExprOpt', ';')),

    # 63: RetExprOpt -> Expr
    ('RetExprOpt', ('Expr',)),
    # 64: RetExprOpt -> ε
    ('RetExprOpt', ()),

    # 65: BreakStmt -> break ;
    ('BreakStmt', ('break', ';')),

    # 66: PrintStmt -> Print ( ExprList ) ;
    ('PrintStmt', ('Print', '(', 'ExprList', ')', ';')),

    # 67: ExprList -> Expr ExprListTail
    ('ExprList', ('Expr', 'ExprListTail')),

    # 68: ExprListTail -> , Expr ExprListTail
    ('ExprListTail', (',', 'Expr', 'ExprListTail')),
    # 69: ExprListTail -> ε
    ('ExprListTail', ()),

    # 70: Expr -> OrExpr AssignTail
    ('Expr', ('OrExpr', 'AssignTail')),

    # 71: AssignTail -> = Expr
    ('AssignTail', ('=', 'Expr')),
    # 72: AssignTail -> ε
    ('AssignTail', ()),

    # 73: OrExpr -> AndExpr OrTail
    ('OrExpr', ('AndExpr', 'OrTail')),

    # 74: OrTail -> || AndExpr OrTail
    ('OrTail', ('||', 'AndExpr', 'OrTail')),
    # 75: OrTail -> ε
    ('OrTail', ()),

    # 76: AndExpr -> EqExpr AndTail
    ('AndExpr', ('EqExpr', 'AndTail')),

    # 77: AndTail -> && EqExpr AndTail
    ('AndTail', ('&&', 'EqExpr', 'AndTail')),
    # 78: AndTail -> ε
    ('AndTail', ()),

    # 79: EqExpr -> RelExpr EqTail
    ('EqExpr', ('RelExpr', 'EqTail')),

    # 80: EqTail -> == RelExpr
    ('EqTail', ('==', 'RelExpr')),
    # 81: EqTail -> != RelExpr
    ('EqTail', ('!=', 'RelExpr')),
    # 82: EqTail -> ε
    ('EqTail', ()),

    # 83: RelExpr -> AddExpr RelTail
    ('RelExpr', ('AddExpr', 'RelTail')),

    # 84: RelTail -> < AddExpr
    ('RelTail', ('<', 'AddExpr')),
    # 85: RelTail -> <= AddExpr
    ('RelTail', ('<=', 'AddExpr')),
    # 86: RelTail -> > AddExpr
    ('RelTail', ('>', 'AddExpr')),
    # 87: RelTail -> >= AddExpr
    ('RelTail', ('>=', 'AddExpr')),
    # 88: RelTail -> ε
    ('RelTail', ()),

    # 89: AddExpr -> MulExpr AddTail
    ('AddExpr', ('MulExpr', 'AddTail')),

    # 90: AddTail -> + MulExpr AddTail
    ('AddTail', ('+', 'MulExpr', 'AddTail')),
    # 91: AddTail -> - MulExpr AddTail
    ('AddTail', ('-', 'MulExpr', 'AddTail')),
    # 92: AddTail -> ε
    ('AddTail', ()),

    # 93: MulExpr -> UnaryExpr MulTail
    ('MulExpr', ('UnaryExpr', 'MulTail')),

    # 94: MulTail -> * UnaryExpr MulTail
    ('MulTail', ('*', 'UnaryExpr', 'MulTail')),
    # 95: MulTail -> / UnaryExpr MulTail
    ('MulTail', ('/', 'UnaryExpr', 'MulTail')),
    # 96: MulTail -> % UnaryExpr MulTail
    ('MulTail', ('%', 'UnaryExpr', 'MulTail')),
    # 97: MulTail -> ε
    ('MulTail', ()),

    # 98: UnaryExpr -> ! UnaryExpr
    ('UnaryExpr', ('!', 'UnaryExpr')),
    # 99: UnaryExpr -> - UnaryExpr
    ('UnaryExpr', ('-', 'UnaryExpr')),
    # 100: UnaryExpr -> PostExpr
    ('UnaryExpr', ('PostExpr',)),

    # 101: PostExpr -> Primary PostTail
    ('PostExpr', ('Primary', 'PostTail')),

    # 102: PostTail -> [ Expr ] PostTail
    ('PostTail', ('[', 'Expr', ']', 'PostTail')),
    # 103: PostTail -> . id CallTail PostTail
    ('PostTail', ('.', 'id', 'CallTail', 'PostTail')),
    # 104: PostTail -> ε
    ('PostTail', ()),

    # 105: CallTail -> ( ActualList )
    ('CallTail', ('(', 'ActualList', ')')),
    # 106: CallTail -> ε
    ('CallTail', ()),

    # Primary productions
    # 107: Primary -> id CallTail
    ('Primary', ('id', 'CallTail')),
    # 108: Primary -> INT_CONST
    ('Primary', ('INT_CONST',)),
    # 109: Primary -> DOUBLE_CONST
    ('Primary', ('DOUBLE_CONST',)),
    # 110: Primary -> BOOL_CONST
    ('Primary', ('BOOL_CONST',)),
    # 111: Primary -> STRING_CONST
    ('Primary', ('STRING_CONST',)),
    # 112: Primary -> null
    ('Primary', ('null',)),
    # 113: Primary -> this
    ('Primary', ('this',)),
    # 114: Primary -> ( Expr )
    ('Primary', ('(', 'Expr', ')')),
    # 115: Primary -> ReadInteger ( )
    ('Primary', ('ReadInteger', '(', ')')),
    # 116: Primary -> ReadLine ( )
    ('Primary', ('ReadLine', '(', ')')),
    # 117: Primary -> New ( id )
    ('Primary', ('New', '(', 'id', ')')),
    # 118: Primary -> NewArray ( Expr , Type )
    ('Primary', ('NewArray', '(', 'Expr', ',', 'Type', ')')),

    # 119: ActualList -> Expr ExprListTail
    ('ActualList', ('Expr', 'ExprListTail')),
    # 120: ActualList -> ε
    ('ActualList', ()),
]

# ---------------------------------------------------------------------------
# All terminal symbols in the grammar
# ---------------------------------------------------------------------------
TERMINALS = frozenset([
    'int', 'double', 'bool', 'string', 'void',
    'class', 'interface', 'null', 'this',
    'extends', 'implements', 'for', 'while', 'if', 'else',
    'return', 'break', 'New', 'NewArray', 'Print',
    'ReadInteger', 'ReadLine',
    'id', 'INT_CONST', 'DOUBLE_CONST', 'BOOL_CONST', 'STRING_CONST',
    '+', '-', '*', '/', '%',
    '<', '<=', '>', '>=', '=', '==', '!=',
    '&&', '||', '!',
    ';', ',', '.', '(', ')', '[', ']', '{', '}',
    '$',
])

EPSILON = 'ε'


class Grammar:
    """
    Encapsulates the grammar and provides:
      - FIRST / FOLLOW set computation (iterative fixpoint)
      - LL(1) parse table construction
      - LR(0) item set construction
      - SLR(1) action/goto table construction
    """

    def __init__(self, productions):
        self.productions = productions   # list of (lhs, rhs)
        self.terminals = set(TERMINALS)
        self.nonterminals = set()
        self.start_symbol = productions[0][0]  # 'Program'

        for lhs, rhs in productions:
            self.nonterminals.add(lhs)

        self.first_sets = {}    # symbol -> set of terminals + possibly EPSILON
        self.follow_sets = {}   # nonterminal -> set of terminals

    # ------------------------------------------------------------------
    # FIRST set computation
    # ------------------------------------------------------------------

    def compute_first_sets(self):
        """Iteratively compute FIRST(X) for all symbols."""
        # Initialize
        for t in self.terminals:
            self.first_sets[t] = {t}
        self.first_sets[EPSILON] = {EPSILON}
        for nt in self.nonterminals:
            self.first_sets[nt] = set()

        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                before = len(self.first_sets[lhs])
                added = self.first_of_string(rhs)
                self.first_sets[lhs] |= added
                if len(self.first_sets[lhs]) > before:
                    changed = True

    def first_of_string(self, symbols):
        """Compute FIRST of a sequence of grammar symbols."""
        result = set()
        if not symbols:
            result.add(EPSILON)
            return result

        all_nullable = True
        for sym in symbols:
            sym_first = self.first_sets.get(sym, set())
            result |= (sym_first - {EPSILON})
            if EPSILON not in sym_first:
                all_nullable = False
                break

        if all_nullable:
            result.add(EPSILON)

        return result

    # ------------------------------------------------------------------
    # FOLLOW set computation
    # ------------------------------------------------------------------

    def compute_follow_sets(self):
        """Iteratively compute FOLLOW(A) for all non-terminals."""
        for nt in self.nonterminals:
            self.follow_sets[nt] = set()

        # Start symbol contains $
        self.follow_sets[self.start_symbol].add('$')

        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                for i, sym in enumerate(rhs):
                    if sym not in self.nonterminals:
                        continue
                    # sym is a non-terminal B
                    before = len(self.follow_sets[sym])
                    # beta = rhs after position i
                    beta = rhs[i + 1:]
                    first_beta = self.first_of_string(beta)
                    # Add FIRST(beta) - {ε} to FOLLOW(B)
                    self.follow_sets[sym] |= (first_beta - {EPSILON})
                    # If ε ∈ FIRST(beta), add FOLLOW(lhs) to FOLLOW(B)
                    if EPSILON in first_beta:
                        self.follow_sets[sym] |= self.follow_sets[lhs]
                    if len(self.follow_sets[sym]) > before:
                        changed = True

    # ------------------------------------------------------------------
    # LL(1) table construction
    # ------------------------------------------------------------------

    def build_ll1_table(self):
        """
        Build M[A, a] LL(1) parse table.
        Returns dict mapping (nonterminal, terminal) -> production rhs tuple.
        Reports conflicts in returned conflicts list.
        """
        table = {}
        conflicts = []

        for idx, (lhs, rhs) in enumerate(self.productions):
            first_rhs = self.first_of_string(rhs)

            # For each terminal a in FIRST(rhs), add production to M[lhs, a]
            for terminal in first_rhs:
                if terminal == EPSILON:
                    continue
                key = (lhs, terminal)
                if key in table:
                    conflicts.append((key, table[key], rhs, idx))
                    # Keep first entry (prefer first production = shift for dangling else)
                else:
                    table[key] = rhs

            # If ε ∈ FIRST(rhs), for each b in FOLLOW(lhs), add to M[lhs, b]
            if EPSILON in first_rhs:
                for terminal in self.follow_sets.get(lhs, set()):
                    key = (lhs, terminal)
                    if key in table:
                        # Dangling else: prefer shift (non-epsilon production)
                        existing_rhs = table[key]
                        if existing_rhs == ():
                            # Replace epsilon with shift (actual production wins)
                            table[key] = rhs
                        # else keep existing (which is the shift)
                        conflicts.append((key, existing_rhs, rhs, idx))
                    else:
                        table[key] = rhs

        # ------------------------------------------------------------------
        # Post-processing: resolve remaining LL(1) conflicts.
        #
        # The Decaf grammar is mostly LL(1) after introducing DeclRest and
        # FieldRest. Remaining conflicts:
        #  1. Stmt -> VarDecl vs Stmt -> ExprStmt when lookahead is 'id'
        #     (named-type variable declarations like MyClass x; need 2-token
        #      lookahead; we prefer ExprStmt for 'id' and document this limitation)
        # ------------------------------------------------------------------

        # (1) M[Stmt, id] -> prefer ExprStmt over VarDecl.
        #     Handles 'x = 5;', 'x.f();', 'x[i] = ...;' correctly.
        #     Named-type VarDecl ('MyClass x;') needs 2-token lookahead
        #     (handled correctly in the recursive descent parser).
        expr_stmt_rhs = ('ExprStmt',)
        table[('Stmt', 'id')] = expr_stmt_rhs

        # (2) Add epsilon to TypeSuffix for operator/assign tokens that legally
        #     follow a type in formal parameter, function return type, etc.
        type_suffix_epsilon_tokens = {
            'id', ';', ',', ')', '=', '{', '}',
            '&&', '||', '==', '!=', '<', '<=', '>', '>=',
            '+', '-', '*', '/', '%', '.',
        }
        for tok in type_suffix_epsilon_tokens:
            key = ('TypeSuffix', tok)
            if key not in table:
                table[key] = ()   # TypeSuffix -> ε

        # (3) ForInit and ForUpdate: 'id' should try Expr (not VarDecl)
        table[('ForInit', 'id')] = ('Expr',)
        table[('ForUpdate', 'id')] = ('Expr',)

        self.ll1_table = table
        self.ll1_conflicts = conflicts
        return table

    # ------------------------------------------------------------------
    # LR(0) item construction
    # ------------------------------------------------------------------

    def _augmented_productions(self):
        """Return augmented productions with Program' -> Program $ at index 0."""
        aug = [("Program'", ('Program', '$'))] + list(self.productions)
        return aug

    def _closure(self, items, aug_prods):
        """Compute closure of a set of LR(0) items."""
        # items: set of (prod_idx, dot_pos)
        closure = set(items)
        changed = True
        while changed:
            changed = False
            new_items = set()
            for prod_idx, dot in closure:
                lhs, rhs = aug_prods[prod_idx]
                if dot < len(rhs):
                    symbol = rhs[dot]
                    if symbol in self.nonterminals or symbol == "Program":
                        # Add all productions for this symbol
                        for i, (pl, pr) in enumerate(aug_prods):
                            if pl == symbol:
                                item = (i, 0)
                                if item not in closure:
                                    new_items.add(item)
            if new_items:
                closure |= new_items
                changed = True
        return frozenset(closure)

    def _goto(self, items, symbol, aug_prods):
        """Compute goto(items, symbol)."""
        moved = set()
        for prod_idx, dot in items:
            lhs, rhs = aug_prods[prod_idx]
            if dot < len(rhs) and rhs[dot] == symbol:
                moved.add((prod_idx, dot + 1))
        if not moved:
            return None
        return self._closure(moved, aug_prods)

    def build_lr0_items(self):
        """
        Build canonical collection of LR(0) item sets.
        Returns (aug_prods, states, goto_map) where:
          - states: list of frozensets of (prod_idx, dot_pos)
          - goto_map: dict {(state_idx, symbol): state_idx}
        """
        aug_prods = self._augmented_productions()

        # Initial state: closure({Program' -> .Program $})
        initial = self._closure({(0, 0)}, aug_prods)
        states = [initial]
        state_map = {initial: 0}
        goto_map = {}

        # All symbols that can appear after the dot
        all_symbols = self.nonterminals | self.terminals | {"Program", "Program'"}

        worklist = [0]
        while worklist:
            state_idx = worklist.pop(0)
            state = states[state_idx]
            for sym in all_symbols:
                target = self._goto(state, sym, aug_prods)
                if target is None or len(target) == 0:
                    continue
                if target not in state_map:
                    state_map[target] = len(states)
                    states.append(target)
                    worklist.append(state_map[target])
                goto_map[(state_idx, sym)] = state_map[target]

        self._aug_prods = aug_prods
        self._lr0_states = states
        self._lr0_goto = goto_map
        return aug_prods, states, goto_map

    # ------------------------------------------------------------------
    # SLR(1) table construction
    # ------------------------------------------------------------------

    def build_slr1_table(self):
        """
        Build SLR(1) action and goto tables.
        Returns (action, goto, conflicts) where:
          - action: {(state, terminal): ('shift', state) | ('reduce', prod_idx) | ('accept',)}
          - goto: {(state, nonterminal): state}
          - conflicts: list of conflict descriptions
        """
        aug_prods, states, goto_map = self.build_lr0_items()

        action = {}
        goto = {}
        conflicts = []

        for state_idx, items in enumerate(states):
            for prod_idx, dot in items:
                lhs, rhs = aug_prods[prod_idx]

                if dot < len(rhs):
                    sym = rhs[dot]
                    target = goto_map.get((state_idx, sym))
                    if target is None:
                        continue

                    if sym in self.terminals or sym == '$':
                        # Shift
                        key = (state_idx, sym)
                        new_action = ('shift', target)
                        if key in action:
                            existing = action[key]
                            if existing[0] == 'reduce':
                                # Shift-reduce conflict.
                                # Standard SLR(1) resolution: prefer shift for 'else'
                                # (resolves dangling-else ambiguity). For all other
                                # tokens, the reduce was added first and is kept.
                                if sym == 'else':
                                    conflicts.append(
                                        f"Shift-reduce conflict at state {state_idx}, "
                                        f"sym '{sym}': preferring shift (dangling else)"
                                    )
                                    action[key] = new_action  # shift wins for else
                                else:
                                    # Keep the reduce; note the conflict
                                    conflicts.append(
                                        f"Shift-reduce conflict at state {state_idx}, "
                                        f"sym '{sym}': keeping reduce over shift"
                                    )
                            elif existing[0] == 'shift' and existing != new_action:
                                # Shift-shift: report but keep first
                                conflicts.append(
                                    f"Shift-shift conflict at state {state_idx}, sym {sym}")
                            # else: same shift or accept already there
                        else:
                            action[key] = new_action
                    elif sym in self.nonterminals or sym == 'Program':
                        # Goto
                        goto[(state_idx, sym)] = target

                else:
                    # dot at end of production
                    if lhs == "Program'" :
                        # Accept
                        key = (state_idx, '$')
                        action[key] = ('accept',)
                    else:
                        # Find original production index (aug_prods[0] is augmented)
                        orig_idx = prod_idx - 1  # offset by 1 due to augmented production
                        follow_lhs = self.follow_sets.get(lhs, set())
                        for terminal in follow_lhs:
                            key = (state_idx, terminal)
                            new_action = ('reduce', orig_idx)
                            if key in action:
                                existing = action[key]
                                if existing[0] == 'shift':
                                    # Shift-reduce conflict: prefer shift (dangling else)
                                    conflicts.append(
                                        f"Shift-reduce conflict at state {state_idx}, "
                                        f"sym '{terminal}': keeping shift over reduce {orig_idx}"
                                    )
                                elif existing != new_action:
                                    conflicts.append(
                                        f"Reduce-reduce conflict at state {state_idx}, "
                                        f"sym '{terminal}'"
                                    )
                                    # Keep lower-numbered production (first encountered)
                                    if orig_idx < existing[1]:
                                        action[key] = new_action
                            else:
                                action[key] = new_action

        self.slr1_action = action
        self.slr1_goto = goto
        self.slr1_conflicts = conflicts
        return action, goto, conflicts

    # ------------------------------------------------------------------
    # Pretty-print helpers
    # ------------------------------------------------------------------

    def print_first_follow(self):
        print("\n" + "=" * 60)
        print("FIRST SETS")
        print("=" * 60)
        for nt in sorted(self.nonterminals):
            fs = sorted(self.first_sets.get(nt, set()))
            print(f"  FIRST({nt:<20}) = {{ {', '.join(fs)} }}")

        print("\n" + "=" * 60)
        print("FOLLOW SETS")
        print("=" * 60)
        for nt in sorted(self.nonterminals):
            fol = sorted(self.follow_sets.get(nt, set()))
            print(f"  FOLLOW({nt:<20}) = {{ {', '.join(fol)} }}")

    def print_ll1_table(self):
        if not hasattr(self, 'll1_table'):
            self.build_ll1_table()
        print("\n" + "=" * 60)
        print("LL(1) PARSE TABLE")
        print("=" * 60)
        # Group by nonterminal
        from collections import defaultdict
        by_nt = defaultdict(dict)
        for (nt, term), rhs in self.ll1_table.items():
            rhs_str = ' '.join(rhs) if rhs else 'ε'
            by_nt[nt][term] = rhs_str
        for nt in sorted(by_nt):
            print(f"\n  {nt}:")
            for term in sorted(by_nt[nt]):
                print(f"    [{term}] -> {by_nt[nt][term]}")
        if self.ll1_conflicts:
            print(f"\n  CONFLICTS ({len(self.ll1_conflicts)}):")
            for c in self.ll1_conflicts[:20]:
                print(f"    {c}")

    def print_lr_table(self):
        if not hasattr(self, 'slr1_action'):
            self.build_slr1_table()
        print("\n" + "=" * 60)
        print("SLR(1) ACTION/GOTO TABLE")
        print("=" * 60)
        num_states = len(self._lr0_states)
        print(f"  States: {num_states}")
        # Print first 20 states
        for state in range(min(num_states, 20)):
            entries = {k: v for k, v in self.slr1_action.items() if k[0] == state}
            goto_entries = {k: v for k, v in self.slr1_goto.items() if k[0] == state}
            if entries or goto_entries:
                print(f"\n  State {state}:")
                for (s, sym), act in sorted(entries.items(), key=lambda x: x[0][1]):
                    print(f"    action[{sym}] = {act}")
                for (s, sym), st in sorted(goto_entries.items(), key=lambda x: x[0][1]):
                    print(f"    goto[{sym}] = {st}")
        if self.slr1_conflicts:
            print(f"\n  CONFLICTS ({len(self.slr1_conflicts)}):")
            for c in self.slr1_conflicts[:20]:
                print(f"    {c}")


# ---------------------------------------------------------------------------
# Module-level convenience: pre-build grammar and export FIRST/FOLLOW
# ---------------------------------------------------------------------------
_default_grammar = None
FIRST_SETS = {}
FOLLOW_SETS = {}


def get_default_grammar():
    global _default_grammar, FIRST_SETS, FOLLOW_SETS
    if _default_grammar is None:
        _default_grammar = Grammar(PRODUCTIONS)
        _default_grammar.compute_first_sets()
        _default_grammar.compute_follow_sets()
        FIRST_SETS = _default_grammar.first_sets
        FOLLOW_SETS = _default_grammar.follow_sets
    return _default_grammar
