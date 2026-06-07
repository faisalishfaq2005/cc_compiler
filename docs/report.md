# Decaf Mini-Compiler --- Project Report

**Course:** CS-471L Compiler Construction Lab
**Institution:** University of Engineering and Technology, Lahore
**Semester:** Spring 2026
**Language Compiled:** Decaf (object-oriented, Java-like)
**Implementation Language:** Python 3.10+

---

## 1. Introduction

This project implements a front-end mini-compiler for the **Decaf** programming
language -- a statically typed, object-oriented language designed specifically for
compiler construction courses. Decaf borrows its syntax from Java but strips away
generics, packages, exceptions, and complex I/O, leaving a tractable yet expressive
target language.

The compiler is organised as six cooperating modules:

| Module | File | Role |
|--------|------|------|
| Lexical Analyzer | `src/lexer.py` | Tokenises source text using double-buffering |
| Recursive Descent Parser | `src/rd_parser.py` | Hand-coded LL parser; builds AST; fills symbol table |
| LL(1) Non-Recursive Parser | `src/ll_parser.py` | Table-driven predictive parser with parse trace |
| SLR(1) LR Parser | `src/lr_parser.py` | Bottom-up shift-reduce parser with full action/goto tables |
| Symbol Table Manager | `src/symbol_table.py` | Scoped hash-based symbol store |
| Error Handler | `src/error_handler.py` | Centralised error/warning collection and recovery |

The six modules share a single Grammar object (built in `src/grammar.py`) that
provides production rules, FIRST/FOLLOW sets, and both the LL(1) table and the
SLR(1) action/goto tables.

### Goals

1. Demonstrate lexical analysis with double-buffering.
2. Implement three distinct parsing strategies for the same grammar.
3. Build and query a scoped symbol table.
4. Provide useful error messages and recover from syntax errors.

---

## 2. Language Overview: Decaf

A Decaf program is a sequence of top-level **declarations**. Each declaration is
one of: a variable declaration, a function declaration, a class declaration, or
an interface declaration.

### Type System

| Type keyword | Meaning |
|---|---|
| `int` | 32-bit signed integer |
| `double` | IEEE 754 double-precision float |
| `bool` | Boolean: `true` or `false` |
| `string` | Immutable character string |
| `void` | Return type for procedures |
| `ClassName` | Instance of a user-defined class |
| `T[]` | One-dimensional array of type T |

### Classes and Interfaces

```decaf
class Dog extends Animal implements Runnable {
    string name;
    void bark() { Print("Woof!"); }
}
```

Classes support single inheritance (`extends`) and multiple interface
implementation (`implements`). Interface declarations contain method prototypes
only -- no bodies.

### Built-in Operations

| Operation | Return Type | Description |
|---|---|---|
| `Print(e, ...)` | void | Print expressions to stdout |
| `ReadInteger()` | int | Read one integer from stdin |
| `ReadLine()` | string | Read one line from stdin |
| `New(T)` | T | Allocate a new instance of class T |
| `NewArray(n, T)` | T[] | Allocate an array of n elements |

---

## 3. Module Descriptions

### 3.1 Module 1: Lexical Analyzer (`lexer.py`)

The lexer converts a raw source string into a flat sequence of `Token` objects.
Each `Token` carries: `type` (a `TokenType` enum), `value` (the literal or
converted Python value), `line`, and `col`.

#### Double-Buffering (`DoubleBuffer` class)

Efficient character scanning uses two buffers of `BUFF_SIZE = 512` bytes each.
The key insight is that a token can span a buffer boundary; the double-buffer
scheme ensures this never requires re-reading the source.

- `next_char()`: advances the `forward` pointer and returns the current character.
- `retract()`: moves `forward` back by one position (used when peeking one
  character too far, e.g., deciding `!=` vs `!`).
- `start_lexeme()` / `get_lexeme()`: mark and retrieve the current token text.
- `peek()` / `peek_ahead(n)`: read ahead without advancing `forward`.

**Why double buffering?** Without buffering, each character read is an OS system
call. With double buffering, a block of 512 characters is loaded at once, and
subsequent reads are in-memory operations. Even if a very long token straddles
the 512-character boundary, both halves are simultaneously available in memory.

#### Token Types Table

| Category | Examples |
|---|---|
| Keywords | `void`, `int`, `class`, `if`, `while`, `return`, `true`, `New` |
| Literals | `42`, `0xFF`, `3.14`, `"hello"`, `true` |
| Identifiers | `myVar`, `Animal`, `_count` (max 31 chars) |
| Operators | `+`, `-`, `*`, `/`, `%`, `!`, `=`, `==`, `!=`, `<`, `<=`, `&&`, `||` |
| Punctuation | `;`, `,`, `.`, `(`, `)`, `{`, `}`, `[`, `]` |

#### Example Lexer Output (test1_valid.decaf excerpt)

```
Token(KW_VOID, 'void', line=2, col=1)
Token(IDENTIFIER, 'main', line=2, col=6)
Token(LPAREN, '(', line=2, col=10)
Token(RPAREN, ')', line=2, col=11)
Token(LBRACE, '{', line=2, col=13)
Token(KW_INT, 'int', line=3, col=5)
Token(IDENTIFIER, 'x', line=3, col=9)
Token(SEMICOLON, ';', line=3, col=10)
```

### 3.2 Module 2: Recursive Descent Parser (`rd_parser.py`)

The recursive descent parser (RDP) is a hand-written top-down parser with one
Python method per non-terminal. It is the most direct translation of the grammar
into executable code.

#### One Function Per Non-Terminal

The grammar has approximately 55 non-terminals; the RD parser has 55 corresponding
parse methods. For example, `parse_if_stmt()` handles `IfStmt`, `parse_expr()`
handles `Expr`, and so on.

For binary operators (which use right-recursive tail rules in the LL(1) grammar),
the RD parser restores natural left-associative evaluation using while loops:

```python
def parse_add_expr(self):
    node = self.parse_mul_expr()
    while self.current.grammar_symbol() in ('+', '-'):
        op = self.current.value
        self.advance()
        rhs = self.parse_mul_expr()
        node = {'type': 'BinaryOp', 'op': op,
                'children': [node, rhs], 'line': node['line']}
    return node
```

#### Symbol Table Integration

- **VarDecl**: inserts `SymbolEntry(name, 'variable', type_str, scope_level, line)`.
- **FuncDecl**: inserts a `'function'` entry; opens a new scope for the body.
- **ClassDecl**: inserts a `'class'` entry; opens a new scope for members.
- **At identifier use**: calls `lookup(name)` across all scopes; reports SEMANTIC
  error if not found.

#### Error Recovery

When a syntax error is detected:
1. Report the error (line, column, expected, found).
2. Call `panic_mode_recover(parser, FOLLOW[nt])` to skip tokens until a
   synchronisation token is found.
3. Continue parsing from that point.

This allows reporting multiple independent errors in one pass.

#### AST Representation

Every parse method returns a `dict` node:

```python
{
  'type':     'FuncDecl',
  'value':    'main',
  'line':     2,
  'children': [ret_type_node, params_node, body_node]
}
```

### 3.3 Module 3: LL(1) Non-Recursive Predictive Parser (`ll_parser.py`)

The LL(1) parser is a stack-based, table-driven parser. It does not recurse;
instead it maintains an explicit parse stack and consults the precomputed parse
table `M[A, a]` at each step.

#### What "LL(1)" Means

- **L**: reads input **L**eft-to-right
- **L**: constructs a **L**eftmost derivation
- **(1)**: uses **1** lookahead token

An LL(1) parser is deterministic: given the non-terminal on top of the stack and
the current lookahead, there is at most one correct production. This makes it
linear time (O(n) input tokens) with O(1) table lookup.

#### The Parse Table `M[A, a]`

`M[A, a]` answers: "When non-terminal `A` is on top of the stack and the next
input is `a`, which production should I apply?"

Construction rule for production `A -> alpha`:
- For each `t` in `FIRST(alpha) \ {epsilon}`: set `M[A, t] = (A -> alpha)`.
- If `epsilon` in `FIRST(alpha)`: for each `t` in `FOLLOW(A)`: set
  `M[A, t] = (A -> alpha)`.

#### The Three-Case Parsing Loop

At each step, examine stack-top `X` and lookahead `a`:

1. `X` is a terminal equal to `a`: **match** -- pop `X`, advance input.
2. `X` is a non-terminal and `M[X, a]` is defined: **expand** -- pop `X`, push
   the production's RHS in reverse order.
3. Otherwise: **error** -- report, attempt panic-mode recovery.

#### Parse Trace Example

```
Stack                            Input              Action
--------------------------       -------            ------
$ Program                        void main...       Program->DeclList
$ DeclList                       void main...       DeclList->Decl DeclList
$ DeclList Decl                  void main...       Decl->FuncDecl
$ DeclList FuncDecl              void main...       FuncDecl->RetType id(...)
...
$                                $                  ACCEPT
```

### 3.4 Module 4: SLR(1) LR Parser (`lr_parser.py`)

The SLR(1) parser is a bottom-up, shift-reduce parser. It is more powerful than
LL(1): it can handle a strictly larger class of grammars and naturally handles
left-associative binary operators without needing left-recursion removal.

#### LR(0) Items and the Automaton

An LR(0) item is a production with a dot marker `[A -> alpha . beta]` showing
progress. The SLR(1) automaton has 229 states for the Decaf grammar, each being
a set of LR(0) items.

**Closure**: if `[A -> alpha . B beta]` is in a state, all productions `B -> gamma`
contribute items `[B -> . gamma]` to the same state.

**Goto(state, X)**: moves the dot past `X` in all items where `X` immediately
follows the dot.

#### SLR(1) Table Construction

- `action[s, a] = shift t`: if `[A -> alpha . a beta]` in state `s` and
  `goto(s, a) = t`.
- `action[s, a] = reduce A->alpha`: if `[A -> alpha .]` in state `s` and
  `a` in `FOLLOW(A)`.
- `action[s, $] = accept`: if `[S' -> S .]` in state `s`.
- `goto[s, A] = t`: if `goto(state_s, A) = state_t`.

#### Conflict Resolution

Four conflicts arise and are all resolved deterministically:

| Conflict | State | Token | Resolution |
|---|---|---|---|
| Dangling else | 218 | `else` | Prefer shift (nearest if) |
| TypeSuffix ambiguity | 108 | `[` | Prefer reduce |
| Reduce/reduce | 108 | `)` | Use first production |
| DeclList ambiguity | 1 | `id` | Prefer reduce |

#### Parse Trace Example

```
States        Symbols           Input        Action
-----------   ---------------   ----------   -----------
[0]           [$]               void main    shift void
[0,15]        [$,void]          main(        shift id
[0,15,N]      [$,void,id]       (            goto RetType
...
```

### 3.5 Module 5: Symbol Table Manager (`symbol_table.py`)

The symbol table is the compiler's central store for semantic information.

#### Scoped Symbol Table

Decaf uses block scoping (like C and Java). The implementation uses a stack of
Python dicts:

- `scopes[0]`: global scope (function/class/interface names)
- `scopes[1]`: function parameter scope
- `scopes[2]`: function body scope
- `scopes[3+]`: nested block scopes

`enter_scope()` pushes a new empty dict. `exit_scope()` pops it. `lookup(name)`
searches from innermost to outermost, implementing the standard "inner shadows
outer" rule.

#### Polynomial Rolling Hash

```python
def _hash(self, name: str) -> int:
    h = 0
    for c in name:
        h = (h * 31 + ord(c)) % self.HASH_SIZE   # HASH_SIZE = 211
    return h
```

This is the same hash function used in Java's `String.hashCode()`. HASH_SIZE 211
is prime, minimising clustering. The hash value is printed in the symbol table
dump for educational illustration.

#### Symbol Entry Attributes

| Attribute | Description |
|---|---|
| `name` | Identifier string |
| `kind` | `'variable'`, `'function'`, `'class'`, `'interface'`, `'parameter'`, `'array'` |
| `type_` | Type string: `'int'`, `'bool[]'`, `'Animal'`, etc. |
| `scope_level` | Nesting depth (0 = global) |
| `line`, `col` | Source position of declaration |
| `attributes` | Extra dict: `return_type`, `param_types` for functions |

#### Symbol Table Dump Example

```
============================================================
  Symbol Table
  (Scopes: 2, Hash size: 211)
============================================================

  Scope 0 [global]:
  Name                 Kind         Type                 Line   Hash
  -------------------- ------------ -------------------- ------ ------
  add                  function     int                  12     193
  main                 function     void                 2      145

  Scope 1 [main]:
  x                    variable     int                  3      120
  y                    variable     int                  5      121
  z                    variable     int                  7      122

  Total entries: 5
```

### 3.6 Module 6: Error Handler (`error_handler.py`)

The error handler is the single collection point for all compiler diagnostics.

#### Error Classification

- **LEXICAL**: unrecognised characters, unterminated strings/comments, invalid numbers
- **SYNTAX**: unexpected tokens, missing tokens, production mismatches
- **SEMANTIC**: undefined identifiers, duplicate declarations

#### Key Methods

| Method | Description |
|---|---|
| `report_error(kind, message, line, col)` | Record a compiler error |
| `report_warning(message, line, col)` | Record a warning |
| `has_errors()` | True if any errors recorded |
| `panic_mode_recover(parser, sync_tokens)` | Skip tokens until sync |
| `phrase_level_suggest(expected, found)` | Generate helpful hint |
| `print_summary()` | Print all diagnostics sorted by line |

#### Phrase-Level Hints

| Mismatch | Hint |
|---|---|
| Expected `;`, found `,` | "Did you use ',' instead of ';'?" |
| Expected `)`, found `]` | "Mismatched bracket" |
| Expected `==`, found `=` | "Did you mean '==' (equality)?" |

---

## 4. Grammar Specification and Transformations

### 4.1 Left-Recursion Removal

Original (left-recursive):
```
Type -> int | double | bool | string | id | Type []
```

After transformation:
```
Type       -> int TypeSuffix | double TypeSuffix | ... | id TypeSuffix
TypeSuffix -> [] TypeSuffix | epsilon
```

Similarly for all binary expression operators. For example, AddExpr:
```
AddExpr -> MulExpr AddTail
AddTail -> + MulExpr AddTail | - MulExpr AddTail | epsilon
```

### 4.2 Left-Factoring

The `Stmt` non-terminal has alternatives for `VarDecl` and `ExprStmt` that both
start with type keywords or `id`. A 2-token lookahead disambiguates: if the token
after `id` is another `id`, it is a `VarDecl` (class-type-name + variable-name);
otherwise it is an `ExprStmt`.

### 4.3 Grammar Statistics

- Non-terminals: 55
- Productions: ~121
- Terminals: ~40
- LL(1) table non-empty cells: ~400
- SLR(1) states: 229
- SLR(1) conflicts: 4 (all resolved)

---

## 5. Integration Architecture

All six modules communicate through well-defined interfaces:

```
main.py
  |-- Grammar (grammar.py)   -- shared, read-only after construction
  |-- Lexer (lexer.py)       -- one per parser invocation
  |-- RecursiveDescentParser -- uses Lexer, SymbolTable, ErrorHandler
  |-- LLParser               -- uses Grammar.ll1_table, Lexer, ErrorHandler
  |-- LRParser               -- uses Grammar.action/goto, Lexer, ErrorHandler
  |-- SymbolTable            -- used by RD parser for scope management
  +-- ErrorHandler           -- one per parser invocation
```

---

## 6. Sample Programs and Outputs

### 6.1 test1_valid.decaf -- Basic Functions

Tests: void and int functions, local variable declarations, arithmetic expressions,
Print statements, function call with parameters.

**Lexer**: 43 tokens
**RD Parser**: 2 functions (main, add), 3 local vars in main, 2 parameters in add
**LL(1) Parser**: ~120 parse steps
**SLR(1) Parser**: ~200 shift/reduce steps

### 6.2 test2_class.decaf -- Inheritance

Tests: class declarations, extends, method declarations inside classes, New(),
member access via dot notation.

**Symbol table scope structure:**
- Scope 0 [global]: Animal, Dog, main
- Scope 1 [Animal]: name (string), age (int), speak (function), getName (function)
- Scope 2 [Dog]: speak (function override)
- Scope 3 [main]: d (Dog variable)

### 6.3 test3_complex.decaf -- Control Flow

Tests: for loops, while loops, nested if-else, break statements, array types,
interface declaration, complex expressions.

### 6.4 test4_errors.decaf -- Error Recovery

Intentional errors test the compiler's ability to continue after a failure.
The panic-mode recovery allows parsing to resume at the next statement boundary,
enabling multiple errors to be reported from a single compilation pass.

### 6.5 test5_expressions.decaf -- Expression Precedence

Tests all 9 precedence levels from assignment (lowest) through array indexing
and member access (highest). The LR trace shows the exact order of reductions,
confirming correct precedence and associativity.

---

## 7. Running the Compiler

### Direct Python

```bash
# All modules, all output
python src/main.py test/test1_valid.decaf --all

# Specific modules
python src/main.py test/test1_valid.decaf --lexer
python src/main.py test/test1_valid.decaf --rd --symtab
python src/main.py test/test1_valid.decaf --ll
python src/main.py test/test1_valid.decaf --lr

# Analysis only
python src/main.py test/test1_valid.decaf --first --follow
python src/main.py test/test1_valid.decaf --ll-table
python src/main.py test/test1_valid.decaf --lr-table
```

### Make (Linux/macOS)

```bash
make test           # Run all test files
make lexer FILE=test/test1_valid.decaf
make rd    FILE=test/test2_class.decaf
make ll    FILE=test/test3_complex.decaf
make lr    FILE=test/test5_expressions.decaf
make clean
```

### build.bat (Windows)

```batch
build.bat test
build.bat lexer test\test1_valid.decaf
build.bat rd    test\test2_class.decaf
```

---

## 8. Limitations and Future Work

### Current Limitations

1. **No semantic type checking**: types are recorded but not verified for
   compatibility in expressions (e.g., `"hello" + 5` is not flagged).
2. **No code generation**: front-end only; no IR or target code is produced.
3. **Single-file compilation**: no import/include mechanism.
4. **Arrays not fully checked**: the symbol table records array types but
   subscript bounds are not checked.
5. **No static/final**: absent from Decaf by design.

### Future Work

- Semantic analysis: type checking, overriding validation, `this` resolution.
- Intermediate code generation: three-address code or LLVM IR.
- Optimisation: constant folding, dead code elimination.
- Better error recovery: phrase-level insertion for missing semicolons.
- IDE integration: LSP server for syntax highlighting and error squiggles.

---

## 9. References

1. Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006).
   *Compilers: Principles, Techniques, and Tools* (2nd ed.).
   Addison-Wesley. ("The Dragon Book")

2. Lam, M. S. et al. (2003). *CS143 Decaf Language Specification*.
   Stanford University. https://web.stanford.edu/class/cs143/

3. Cooper, K. D., & Torczon, L. (2011).
   *Engineering a Compiler* (2nd ed.). Morgan Kaufmann.

4. Python Software Foundation. *Python 3 Documentation*.
   https://docs.python.org/3/
