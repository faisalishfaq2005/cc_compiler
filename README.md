# Decaf Mini-Compiler

**Course:** CS-471L Compiler Construction Lab
**Institution:** University of Engineering and Technology (UET), Lahore
**Semester:** Spring 2026
**Language Compiled:** Decaf
**Implementation:** Python 3.10+

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Project Structure](#2-project-structure)
3. [Build and Run Instructions](#3-build-and-run-instructions)
4. [Module 1: Lexical Analyzer](#4-module-1-lexical-analyzer)
5. [Module 2: Recursive Descent Parser](#5-module-2-recursive-descent-parser)
6. [Module 3: LL(1) Predictive Parser](#6-module-3-ll1-non-recursive-predictive-parser)
7. [Module 4: SLR(1) LR Parser](#7-module-4-slr1-lr-parser)
8. [Module 5: Symbol Table Manager](#8-module-5-symbol-table-manager)
9. [Module 6: Error Handler](#9-module-6-error-handler)
10. [Integration: How the Modules Connect](#10-integration-how-all-6-modules-connect)
11. [Grammar Discussion](#11-grammar-discussion)
12. [Sample Programs and Outputs](#12-sample-programs-and-outputs)
13. [Limitations and Future Work](#13-limitations-and-future-work)
14. [References](#14-references)

---

## 1. Project Overview

This project is a complete front-end compiler for the **Decaf** programming language.
Decaf is an object-oriented, statically typed language that is syntactically similar
to Java but much smaller in scope, making it an ideal subject for a compiler
construction course.

The compiler demonstrates all major front-end phases:

- **Lexical analysis** -- tokenising source text into a flat stream of tokens
- **Syntax analysis** -- three independent parsers verifying the grammar
- **Semantic analysis (partial)** -- symbol table construction, scope management,
  and undefined-identifier detection
- **Error reporting and recovery** -- diagnostics with line/column positions and
  panic-mode recovery

The project is implemented entirely in **Python 3.10+** with no external
dependencies. All six modules are in the `src/` directory and share a common
grammar object defined in `src/grammar.py`.

### What Decaf Looks Like

```decaf
class Animal {
    string name;
    int age;

    void speak() {
        Print("...");
    }

    string getName() {
        return name;
    }
}

class Dog extends Animal {
    void speak() {
        Print("Woof!");
    }
}

void main() {
    Dog d;
    d = New(Dog);
    d.speak();
    Print(d.getName());
}
```

Decaf supports:
- Primitive types: `int`, `double`, `bool`, `string`, `void`
- Arrays: `int[]`, `bool[]`, `Animal[]`
- Classes with single inheritance and multiple interface implementation
- Control flow: `if`/`else`, `while`, `for`, `return`, `break`
- Built-in I/O: `Print`, `ReadInteger`, `ReadLine`
- Object allocation: `New(ClassName)`, `NewArray(size, Type)`
- All standard arithmetic, comparison, and logical operators

---

## 2. Project Structure

```
FinalProject/
|
|-- src/                        # All source code
|   |-- main.py                 # Entry point, argument parsing, output control
|   |-- lexer.py                # Lexical analyser with double buffering
|   |-- tokens.py               # TokenType enum and Token dataclass
|   |-- grammar.py              # Productions, FIRST/FOLLOW, LL(1)/SLR(1) tables
|   |-- rd_parser.py            # Recursive descent parser (builds AST)
|   |-- ll_parser.py            # LL(1) non-recursive predictive parser
|   |-- lr_parser.py            # SLR(1) bottom-up shift-reduce parser
|   |-- symbol_table.py         # Scoped symbol table with hash storage
|   +-- error_handler.py        # Error/warning collection and recovery
|
|-- test/                       # Decaf source test files
|   |-- test1_valid.decaf       # Basic functions, variables, arithmetic
|   |-- test2_class.decaf       # Class declarations, inheritance, New()
|   |-- test3_complex.decaf     # Loops, interfaces, arrays, nested control flow
|   |-- test4_errors.decaf      # Intentional syntax and semantic errors
|   +-- test5_expressions.decaf # Full expression grammar coverage
|
|-- output/                     # Generated parser traces and token lists
|   |-- test1_valid_lexer.txt
|   |-- test1_valid_rd_parser.txt
|   |-- test1_valid_ll_parser.txt
|   |-- test1_valid_lr_parser.txt
|   |-- grammar_analysis.txt
|   +-- lr_table.txt
|
|-- docs/                       # Documentation (Markdown + LaTeX)
|   |-- grammar.md              # BNF grammar specification
|   |-- grammar.tex             # LaTeX version
|   |-- first_follow.md         # FIRST and FOLLOW sets with algorithms
|   |-- first_follow.tex        # LaTeX version
|   |-- ll1_table.md            # LL(1) parse table description
|   |-- ll1_table.tex           # LaTeX version
|   |-- lr_table.md             # SLR(1) parse table description
|   |-- lr_table.tex            # LaTeX version
|   |-- report.md               # Full project report
|   +-- report.tex              # LaTeX report (compilable with pdflatex)
|
|-- Makefile                    # Build targets (Linux/macOS/Git Bash)
|-- build.bat                   # Build script (Windows CMD)
+-- README.md                   # This file
```

---

## 3. Build and Run Instructions

### Prerequisites

- Python 3.10 or later (check: `python --version`)
- No external packages required

### Option A: Direct Python Command

```bash
# Full run: all 6 modules on a file
python src/main.py test/test1_valid.decaf --all

# Lexer only
python src/main.py test/test1_valid.decaf --lexer

# Recursive descent parser with symbol table
python src/main.py test/test1_valid.decaf --rd --symtab

# LL(1) predictive parser
python src/main.py test/test1_valid.decaf --ll

# SLR(1) bottom-up parser
python src/main.py test/test1_valid.decaf --lr

# Print FIRST and FOLLOW sets
python src/main.py test/test1_valid.decaf --first --follow

# Print LL(1) parse table
python src/main.py test/test1_valid.decaf --ll-table

# Print SLR(1) action/goto table
python src/main.py test/test1_valid.decaf --lr-table

# Increase trace output limit (default: 100 steps)
python src/main.py test/test5_expressions.decaf --ll --trace-limit 500
```

### Option B: Makefile (Linux, macOS, Git Bash on Windows)

```bash
make test                                    # All test files, all parsers
make lexer FILE=test/test1_valid.decaf
make rd    FILE=test/test2_class.decaf
make ll    FILE=test/test3_complex.decaf
make lr    FILE=test/test5_expressions.decaf
make first-follow
make ll-table
make lr-table
make clean
```

### Option C: build.bat (Windows Command Prompt)

```batch
build.bat test
build.bat lexer  test\test1_valid.decaf
build.bat rd     test\test2_class.decaf
build.bat ll     test\test3_complex.decaf
build.bat lr     test\test5_expressions.decaf
build.bat clean
```

### Output Files

All parser traces and token lists are written to the `output/` directory.
File naming convention:
- `output/<basename>_lexer.txt`
- `output/<basename>_rd_parser.txt`
- `output/<basename>_ll_parser.txt`
- `output/<basename>_lr_parser.txt`

---

## 4. Module 1: Lexical Analyzer

**File:** `src/lexer.py`

### What is a Lexer?

A lexer (or scanner) is the first phase of a compiler. It reads the raw source
text character by character and groups characters into **tokens** -- the smallest
meaningful units of the language (keywords, identifiers, operators, literals).

For example, the source text `int x = 5 + y;` becomes the token stream:
```
KW_INT "int"
IDENTIFIER "x"
ASSIGN "="
INT_CONST 5
PLUS "+"
IDENTIFIER "y"
SEMICOLON ";"
```

### Double Buffering

The `DoubleBuffer` class implements the classic two-buffer input technique from
the Dragon Book. Two buffers of `BUFF_SIZE = 512` characters each are maintained.
The `forward` pointer scans characters one at a time. When `forward` reaches the
end of one buffer half, the other half is silently reloaded from the source string.

**Why is this important?**
- Every character is examined at most twice (once when loaded, once when read).
- Tokens that straddle a buffer boundary are handled transparently.
- The `retract()` operation (backing up one character) is O(1).
- On large files, buffered I/O is 10-100x faster than unbuffered reads.

```
Buffer A [0..511]    Buffer B [512..1023]
  ^lexeme_start         ^forward

  When forward reaches 1023:
    -> reload Buffer A from source[1024..1535]
    -> continue scanning into Buffer A
```

Key methods on `DoubleBuffer`:
| Method | Description |
|--------|-------------|
| `next_char()` | Return current char and advance `forward` |
| `retract()` | Move `forward` back by 1 |
| `peek()` | Look at next char without advancing |
| `peek_ahead(n)` | Look n characters ahead |
| `start_lexeme()` | Mark start of current token |
| `get_lexeme()` | Return text from `lexeme_start` to `forward` |
| `at_eof()` | True if at end of source |

### Token Types

All token types are defined as the `TokenType` enum in `src/tokens.py`.

| Category | Token Types | Notes |
|---|---|---|
| Type keywords | `KW_INT`, `KW_DOUBLE`, `KW_BOOL`, `KW_STRING`, `KW_VOID` | |
| Class keywords | `KW_CLASS`, `KW_INTERFACE`, `KW_EXTENDS`, `KW_IMPLEMENTS` | |
| Value keywords | `KW_NULL`, `KW_THIS`, `KW_TRUE`, `KW_FALSE` | true/false => BOOL_CONST |
| Control flow | `KW_IF`, `KW_ELSE`, `KW_WHILE`, `KW_FOR`, `KW_RETURN`, `KW_BREAK` | |
| Built-in ops | `KW_NEW`, `KW_NEWARRAY`, `KW_PRINT`, `KW_READINTEGER`, `KW_READLINE` | |
| Literals | `INT_CONST`, `DOUBLE_CONST`, `BOOL_CONST`, `STRING_CONST` | |
| Identifier | `IDENTIFIER` | max 31 chars |
| Arithmetic | `PLUS`, `MINUS`, `STAR`, `SLASH`, `PERCENT` | |
| Comparison | `LT`, `LE`, `GT`, `GE`, `EQ`, `NEQ` | |
| Logical | `AND`, `OR`, `NOT` | `&&`, `||`, `!` |
| Assignment | `ASSIGN` | `=` |
| Punctuation | `SEMICOLON`, `COMMA`, `DOT`, `LPAREN`, `RPAREN`, `LBRACE`, `RBRACE`, `LBRACKET`, `RBRACKET` | |
| Special | `EOF`, `ERROR` | |

### Example Output

For `test/test1_valid.decaf`:

```
Token(KW_VOID, 'void', line=2, col=1)
Token(IDENTIFIER, 'main', line=2, col=6)
Token(LPAREN, '(', line=2, col=10)
Token(RPAREN, ')', line=2, col=11)
Token(LBRACE, '{', line=2, col=13)
Token(KW_INT, 'int', line=3, col=5)
Token(IDENTIFIER, 'x', line=3, col=9)
Token(SEMICOLON, ';', line=3, col=10)
...
```

---

## 5. Module 2: Recursive Descent Parser

**File:** `src/rd_parser.py`

### What is Top-Down Parsing?

Top-down parsing starts at the root of the parse tree (the start symbol) and
repeatedly expands non-terminals until all leaves are terminal symbols that match
the input tokens. Recursive descent is the most natural implementation: each
non-terminal becomes a function, and the parse tree is built by the call stack.

### One Function Per Non-Terminal

The grammar has approximately 55 non-terminals; the recursive descent parser has
55 corresponding Python methods. For example:

- `parse_program()` handles `Program`
- `parse_decl()` handles `Decl`
- `parse_if_stmt()` handles `IfStmt`
- `parse_expr()` handles `Expr`

Each method:
1. Reads the current lookahead token.
2. Chooses which production to apply based on the token.
3. Calls other parse methods for non-terminal symbols.
4. Calls `advance()` for terminal symbols (matching them against the expected token).
5. Returns an AST dict node.

### Grammar Structure and Parse Functions

The grammar's 121 productions map directly to the parse methods:

| Grammar Rule | Method |
|---|---|
| `Program -> DeclList` | `parse_program` |
| `VarDecl -> Type id ;` | `parse_var_decl` |
| `FuncDecl -> RetType id ( Formals ) Block` | `parse_func_decl` |
| `ClassDecl -> class id ClassBase ...` | `parse_class_decl` |
| `IfStmt -> if ( Expr ) Stmt ElsePart` | `parse_if_stmt` |
| `Expr -> OrExpr AssignTail` | `parse_expr` |
| `AddExpr -> MulExpr AddTail` | `parse_add_expr` |
| `Primary -> id CallTail / INT_CONST / ...` | `parse_primary` |
| (and ~45 more) | ... |

For left-recursive expressions (which use right-recursive tail rules in the LL(1)
grammar), the RD parser uses while loops to achieve natural left-associativity:

```python
def parse_mul_expr(self):
    node = self.parse_unary_expr()
    while self.current.grammar_symbol() in ('*', '/', '%'):
        op = self.current.value
        self.advance()
        rhs = self.parse_unary_expr()
        node = {'type': 'BinaryOp', 'op': op,
                'children': [node, rhs], 'line': node.get('line', 0)}
    return node
```

### Symbol Table Integration

The RD parser is the only parser that populates the symbol table:

**On declaration:**
```python
# In parse_var_decl():
entry = SymbolEntry(name, 'variable', type_str, self.st.scope_level, line)
if not self.st.insert(entry):
    self.eh.report_error('SEMANTIC', f"Duplicate declaration: '{name}'", line, col)
```

**On function/class boundary:**
```python
# In parse_func_decl():
self.st.enter_scope(func_name)
body = self.parse_block()
self.st.exit_scope()
```

**On identifier use:**
```python
# In parse_primary():
if not self.st.lookup(name):
    self.eh.report_error('SEMANTIC', f"Undefined identifier '{name}'", line, col)
```

### AST Structure

The AST uses Python dicts with a standard schema:

```python
{
    'type':     'BinaryOp',      # required: the AST node type
    'value':    '+',             # optional: operator, name, literal value
    'line':     8,               # source line (for error messages)
    'children': [left, right]    # list of child AST nodes
}
```

Common AST node types: `Program`, `FuncDecl`, `ClassDecl`, `VarDecl`, `Block`,
`IfStmt`, `WhileStmt`, `ForStmt`, `ReturnStmt`, `BinaryOp`, `UnaryOp`,
`Assign`, `ArrayAccess`, `FieldAccess`, `FuncCall`, `Id`, `IntLit`,
`DoubleLit`, `BoolLit`, `StringLit`, `NullLit`, `NewExpr`.

### Error Recovery

When the parser encounters an unexpected token:
1. `error_handler.report_error('SYNTAX', message, line, col)` records the error.
2. `error_handler.panic_mode_recover(self, FOLLOW[current_nt])` skips tokens
   until a synchronisation token (from the FOLLOW set) is seen.
3. The parser continues from the synchronisation point.

### Example Parse Trace

For `void main() { int x; x = 5; }`:

```
parse_program()
  parse_decl_list()
    parse_decl()        lookahead='void' => FuncDecl
      parse_func_decl()
        parse_ret_type() => void
        match 'main'
        match '('
        parse_formals()  => epsilon (next is ')')
        match ')'
        parse_block()
          match '{'
          parse_stmt_list()
            parse_stmt()    lookahead='int' => VarDecl
              parse_var_decl() => int x ;
            parse_stmt()    lookahead='x' (next='=') => ExprStmt
              parse_expr_stmt() => x = 5 ;
            parse_stmt_list() => epsilon (next is '}')
          match '}'
```

---

## 6. Module 3: LL(1) Non-Recursive Predictive Parser

**File:** `src/ll_parser.py`

### What is LL(1)?

LL(1) stands for:
- **L**: scan input **L**eft to right
- **L**: construct a **L**eftmost derivation
- **(1)**: use **1** token of lookahead

An LL(1) parser is deterministic: for any non-terminal `A` on the parse stack and
any lookahead token `a`, there is at most one production to apply. This means:

1. No backtracking is needed.
2. The parse runs in O(n) time (n = number of input tokens).
3. The parser can be driven entirely by a 2D lookup table.

### FIRST Sets

`FIRST(X)` is the set of terminals that can begin any string derived from `X`.

**Algorithm:**
```
FIRST(a) = {a}  for each terminal a
FIRST(epsilon) = {epsilon}

For non-terminal A, iterate until stable:
  For each production A -> X1 X2 ... Xk:
    add FIRST(X1) \ {epsilon}  to  FIRST(A)
    if epsilon in FIRST(X1):
      add FIRST(X2) \ {epsilon}  to  FIRST(A)
      ...
      if epsilon in FIRST(X1) through FIRST(Xk):
        add epsilon  to  FIRST(A)
```

**Example:** `FIRST(AddExpr)` = `{!, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST,
New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this}` because
`AddExpr -> MulExpr AddTail`, `MulExpr -> UnaryExpr MulTail`, `UnaryExpr` starts
with `!`, `-`, or the FIRST set of `PostExpr`, and so on down to `Primary`.

### FOLLOW Sets

`FOLLOW(A)` is the set of terminals that can appear immediately to the right of
`A` in some sentential form.

**Algorithm:**
```
FOLLOW(Start) = {$}

Iterate until stable:
  For each production B -> alpha A beta:
    add FIRST(beta) \ {epsilon}  to  FOLLOW(A)
    if epsilon in FIRST(beta):
      add FOLLOW(B)  to  FOLLOW(A)
  For each production B -> alpha A:
    add FOLLOW(B)  to  FOLLOW(A)
```

**Example:** `FOLLOW(Expr)` = `{), ,, ;, ]}` because:
- In `ExprStmt -> Expr ;`: adds `{;}`
- In `ForStmt -> for ( ForInit ; Expr ; ForUpdate )`: adds `{;}`
- In `Primary -> ( Expr )`: adds `{)}`
- In `ExprList -> Expr ExprListTail` and `ExprListTail -> , Expr ExprListTail`:
  FIRST(ExprListTail) = `{,, epsilon}`, so adds `{,}` and FOLLOW(ExprList) = `{)}`
- In `PostTail -> [ Expr ] PostTail`: adds `{]}`

### LL(1) Table Construction

The parse table `M[A, a]` is built using FIRST and FOLLOW:

```
For each production A -> alpha:
  for each t in FIRST(alpha) \ {epsilon}:
    M[A, t] = (A -> alpha)
  if epsilon in FIRST(alpha):
    for each t in FOLLOW(A):
      M[A, t] = (A -> alpha)
```

**Example entries:**

| M[NT, token] | Production |
|---|---|
| M[Stmt, if] | `Stmt -> IfStmt` |
| M[Stmt, while] | `Stmt -> WhileStmt` |
| M[Stmt, int] | `Stmt -> VarDecl` |
| M[AddTail, +] | `AddTail -> + MulExpr AddTail` |
| M[AddTail, -] | `AddTail -> - MulExpr AddTail` |
| M[AddTail, ;] | `AddTail -> epsilon` |
| M[ElsePart, else] | `ElsePart -> else Stmt` (prefer shift) |
| M[ElsePart, }] | `ElsePart -> epsilon` |

### Conflicts

The Decaf grammar has four LL(1)/SLR(1) conflicts. All are resolved
deterministically:

| Conflict | Description | Resolution |
|---|---|---|
| VarDecl vs ExprStmt | Both start with `id` in `Stmt` | 2-token lookahead |
| Dangling else | `else` could bind to any enclosing `if` | Prefer shift (nearest if) |
| TypeSuffix `[` in state 108 | Ambiguous in SLR(1) automaton | Prefer reduce |
| `id` in SLR(1) state 1 | DeclList ambiguity | Prefer reduce |

### The Parsing Algorithm (Three Cases)

```
stack = ['$', 'Program']
token = lexer.next_token()

while stack is not empty:
    X = stack.top()
    a = token.grammar_symbol()

    CASE 1: X is '$' and a is '$'
        --> ACCEPT (successful parse)

    CASE 2: X is a terminal
        if X == a:
            stack.pop()
            token = lexer.next_token()   # consume matched terminal
        else:
            report_error("Expected X, found a")
            panic_mode_recover(FOLLOW[parent_nt])

    CASE 3: X is a non-terminal
        if M[X, a] is defined:
            stack.pop()
            push reversed RHS of M[X, a] (skip epsilon)
        else:
            report_error("No production for M[X, a]")
            panic_mode_recover(FOLLOW[X])
```

### Example Parse Trace (abbreviated)

For `void main() { return 0; }`:

```
Stack (top right)                  Input          Action
---------------------------------  -------------  ---------------------------
$ Program                          void main...   Program -> DeclList
$ DeclList                         void main...   DeclList -> Decl DeclList
$ DeclList Decl                    void main...   Decl -> FuncDecl
$ DeclList FuncDecl                void main...   FuncDecl -> RetType id(...)Block
$ DeclList Block ) Formals ( id RetType  void...  RetType -> void
$ DeclList Block ) Formals ( id void     void...  match void
$ DeclList Block ) Formals ( id          main...  match id
$ DeclList Block ) Formals (             ( )...   match (
$ DeclList Block ) Formals               ) ...    Formals -> epsilon
$ DeclList Block )                       ) ...    match )
$ DeclList Block                         { ret... Block -> { StmtList }
$ DeclList } StmtList {                  { ret... match {
$ DeclList } StmtList                    return.. StmtList -> Stmt StmtList
$ DeclList } StmtList Stmt               return.. Stmt -> ReturnStmt
...
$ DeclList                               $        DeclList -> epsilon
$                                        $        ACCEPT
```

---

## 7. Module 4: SLR(1) LR Parser

**File:** `src/lr_parser.py`

### What is Bottom-Up Parsing?

While LL(1) starts from the start symbol and works downward, LR parsing works
upward: it reads tokens left-to-right, shifting them onto a stack, and whenever
it recognises a complete right-hand side on the top of the stack (called a
**handle**), it **reduces** that sequence to the corresponding left-hand side.

### LR(0) Items: Dot Notation

An **LR(0) item** is a production with a dot marker showing progress:
```
[VarDecl -> Type id . ;]    (dot at position 3 of 4)
```
This means: "we have matched `Type id` so far; we still expect `;` to complete
`VarDecl`". When the dot reaches the end, the RHS is complete and the parser
should reduce.

### Canonical LR(0) Item Collection

The SLR(1) automaton is built by:

1. **Augmenting** the grammar: add `Program' -> Program`.
2. **Computing closure**: if `[A -> alpha . B beta]` is in a state, add all
   productions `[B -> . gamma]` (B can start here).
3. **Computing goto**: `goto(state, X)` = closure of all items with the dot moved
   past `X`.
4. **Iterating**: build all reachable states.

The Decaf grammar produces **229 states**.

### SLR(1) Table Construction

The action table has three types of entries:
- `shift t`: push current token and go to state `t`
- `reduce A -> alpha`: pop `|alpha|` items, push `A`, consult goto table
- `accept`: the parse is complete

The goto table maps `(state, non-terminal)` to the next state after a reduction.

**SLR(1) reduces only when the lookahead is in FOLLOW(A)** (hence "SLR"), which
is more restrictive than LR(0) and eliminates many spurious conflicts.

### State Stack Evolution

The LR parser maintains two stacks: a state stack and a symbol stack. Example:

```
States         Symbols           Input            Action
-----------    ---------------   ----------       -----------
[0]            [$]               void main...     shift void
[0, 15]        [$, void]         main (           shift id
[0, 15, N]     [$, void, id]     (                goto RetType
[0, ..., R]    [$, RetType]      main (           shift id (name)
...
[0, ..., 80]   [$, VarDecl]      x = 5...         reduce: Stmt -> VarDecl
[0, ..., 81]   [$, Stmt]         x = 5...         goto StmtList
```

### Conflict Resolution

Four conflicts arise and are all resolved:

**Conflict 1 -- Dangling Else (State 218, token `else`)**

```
[IfStmt -> if ( Expr ) Stmt . ElsePart]   -- can shift 'else'
[ElsePart -> .]                            -- can reduce on FOLLOW(ElsePart)
```

`else` is in FOLLOW(ElsePart) AND can be shifted. **Resolution: shift**, binding
`else` to the nearest `if`. This matches C, Java, and all other C-family languages.

**Conflict 2 -- TypeSuffix (State 108, token `[`)**

In a type declaration context, after seeing `[]`, the parser can either:
- Shift `[` to start another dimension: `int[][]`
- Reduce `TypeSuffix -> epsilon` and treat `[` as an array subscript

**Resolution: reduce** -- the type declaration context is already complete.

**Conflict 3 -- Reduce/Reduce (State 108, token `)`)**

Two different `TypeSuffix -> epsilon` instances are both applicable.
**Resolution: use the first** (lower production number).

**Conflict 4 -- DeclList Ambiguity (State 1, token `id`)**

**Resolution: reduce** -- complete the pending `DeclList` item.

### SLR(1) Full Algorithm

```
state_stack = [0]
symbol_stack = ['$']

loop:
    s = state_stack.top()
    a = next_token.grammar_symbol()

    if action[s][a] == shift t:
        symbol_stack.push(a)
        state_stack.push(t)
        advance_input()

    elif action[s][a] == reduce (A -> beta):
        for _ in range(len(beta)):
            state_stack.pop()
            symbol_stack.pop()
        t = goto[state_stack.top()][A]
        symbol_stack.push(A)
        state_stack.push(t)

    elif action[s][a] == accept:
        DONE

    else:
        error_handler.report(state=s, token=a)
        panic_mode_recover(FOLLOW[reduce_nt])
```

---

## 8. Module 5: Symbol Table Manager

**File:** `src/symbol_table.py`

### Why a Symbol Table?

A symbol table records everything the compiler knows about each identifier:
its name, kind (variable/function/class), type, scope level, and source location.
This information is needed for:
- Detecting duplicate declarations (two variables with the same name in the same scope)
- Detecting undeclared uses (using a variable before declaring it)
- Type checking (verifying that operands are compatible)
- Code generation (knowing the memory layout of each variable)

### Hash Table with Polynomial Rolling Hash

The hash function used is the standard polynomial rolling hash:

```
h(name) = (ord(c0) * 31^0 + ord(c1) * 31^1 + ... + ord(cn) * 31^n) mod 211
```

This is identical to Java's `String.hashCode()`. The modulus 211 is a prime
number, which distributes hash values more uniformly and reduces clustering
(collisions between nearby hash values).

The hash value is displayed in the symbol table dump as an educational feature,
showing how different identifier names hash to different buckets.

### Stack-Based Scoping

Decaf uses **lexical (static) scoping**: the scope of a variable is determined
by where it is declared in the source text.

The symbol table implements this with a **stack of dictionaries**:

```
scopes = [
    {global_scope},              # index 0 -- always present
    {function_param_scope},      # index 1 -- when inside a function
    {function_body_scope},       # index 2 -- when inside the function's block
    {inner_block_scope},         # index 3 -- when inside an if/while/for block
    ...
]
```

`enter_scope()` pushes a new `{}`. `exit_scope()` pops the top dict (discarding
all variables declared in that scope). `lookup(name)` searches from index -1
(innermost) to index 0 (outermost), returning the first match.

This implements the **inner-shadows-outer** rule: if `x` is declared at global
scope and also inside a function, uses of `x` inside the function refer to the
inner `x`.

### Symbol Entry Attributes

```python
class SymbolEntry:
    name        : str    # "myVariable"
    kind        : str    # "variable" | "function" | "class" | "interface" |
                         # "parameter" | "array"
    type_       : str    # "int" | "bool[]" | "Animal" | etc.
    scope_level : int    # 0 = global, 1 = first nested, etc.
    line        : int    # source line of declaration
    col         : int    # source column of declaration
    attributes  : dict   # for functions: {"return_type": "int",
                         #                 "param_types": ["int", "double"]}
```

### Operations

| Operation | Description | Complexity |
|---|---|---|
| `insert(entry)` | Insert into current scope; return False if duplicate | O(1) avg |
| `lookup(name)` | Search all scopes innermost-first | O(depth) |
| `lookup_current_scope(name)` | Only current scope | O(1) avg |
| `lookup_global(name)` | Only global scope | O(1) avg |
| `delete(name)` | Remove from first scope where found | O(depth) |
| `enter_scope(name)` | Push new empty scope | O(1) |
| `exit_scope()` | Pop innermost scope | O(1) |
| `dump(title)` | Pretty-print all entries with hash values | O(n) |

### Symbol Table Dump Example

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
============================================================
```

---

## 9. Module 6: Error Handler

**File:** `src/error_handler.py`

### Types of Errors

| Kind | Raised By | Examples |
|---|---|---|
| `LEXICAL` | `lexer.py` | Unexpected `@`, unterminated `"string`, invalid `0x` |
| `SYNTAX` | All three parsers | `Expected ';', found '}'`, `No rule for M[Stmt, @]` |
| `SEMANTIC` | `rd_parser.py` | `Undefined identifier 'x'`, `Duplicate declaration 'main'` |

### Error Collection and Limit

The error handler collects up to **50 errors** (`MAX_ERRORS`). This limit prevents
"error cascade": a single typo near the top of the file could produce hundreds of
misleading downstream errors. After 50, additional errors are suppressed with a
message: "Too many errors -- compilation aborted after 50".

### Panic-Mode Recovery

When a parser encounters a syntax error, it needs to recover before continuing.
The simplest strategy is **panic-mode recovery**:

1. Report the error.
2. Discard input tokens one by one until a **synchronisation token** is found.
3. A synchronisation token is one that belongs to `FOLLOW(A)` -- a token that
   can legitimately follow the non-terminal `A` that caused the error.
4. Resume parsing from that token.

For example, if an error occurs inside a statement (`A = Stmt`), the FOLLOW set
includes `}`, `if`, `while`, `return`, etc. The parser skips tokens until it sees
one of these, then continues parsing the next statement.

This strategy usually allows the parser to find and report several independent
errors in a single compilation pass.

### Phrase-Level Suggestions

For common programmer mistakes, the error handler generates a specific hint:

```python
suggestions = {
    (';', ','):  "Did you use ',' instead of ';'?",
    (',', ';'):  "Did you use ';' instead of ','?",
    (')', ']'):  "Mismatched bracket: expected ')' but found ']'",
    (']', ')'):  "Mismatched bracket: expected ']' but found ')'",
    ('==', '='): "Did you mean '==' (equality) instead of '=' (assignment)?",
    ('=', '=='): "Did you mean '=' (assignment) instead of '==' (equality)?",
}
```

### Error Message Format

All errors are printed to `stderr` immediately when detected, and then
summarised at the end:

```
*** [SYNTAX] Line 12, Col 8: Expected ';', found '}'
*** [SEMANTIC] Line 15, Col 12: Undefined identifier 'undeclaredVar'

------------------------------------------------------------
  ERRORS (2):
    [SYNTAX] Line 12, Col 8: Expected ';', found '}'
    [SEMANTIC] Line 15, Col 12: Undefined identifier 'undeclaredVar'
------------------------------------------------------------
```

---

## 10. Integration: How All 6 Modules Connect

```
main.py
  |
  |-- Grammar (grammar.py)         <-- Shared object, built once
  |   |-- PRODUCTIONS              Contains all 121 production rules
  |   |-- compute_first_sets()     FIRST sets for all non-terminals
  |   |-- compute_follow_sets()    FOLLOW sets for all non-terminals
  |   |-- build_ll1_table()        M[A, a] for the LL(1) parser
  |   +-- build_slr1_table()       action[s,a] and goto[s,A] for SLR(1)
  |
  |-- Lexer (lexer.py)             <-- One instance per parser invocation
  |   |-- DoubleBuffer
  |   +-- next_token() / tokenize()
  |
  |-- RecursiveDescentParser (rd_parser.py)
  |   |-- uses Lexer.next_token() for token stream
  |   |-- uses SymbolTable.insert/lookup/enter_scope/exit_scope
  |   +-- uses ErrorHandler.report_error / panic_mode_recover
  |
  |-- LLParser (ll_parser.py)
  |   |-- uses Grammar.ll1_table for M[A, a] lookups
  |   |-- uses Lexer.next_token() for token stream
  |   +-- uses ErrorHandler.report_error
  |
  |-- LRParser (lr_parser.py)
  |   |-- uses Grammar.action / Grammar.goto_tbl
  |   |-- uses Lexer.next_token() for token stream
  |   +-- uses ErrorHandler.report_error
  |
  |-- SymbolTable (symbol_table.py)
  |   +-- Used only by RecursiveDescentParser
  |
  +-- ErrorHandler (error_handler.py)
      +-- One instance per parser; collects all diagnostics
```

All three parsers receive the same source file via their own independent `Lexer`
instance. They share the `Grammar` object (which is read-only after construction)
to avoid rebuilding the FIRST/FOLLOW sets and LR automaton for each run.

Each parser run produces:
1. Console output (trace, errors, symbol table)
2. A text file in `output/<filename>_<parser>.txt`

---

## 11. Grammar Discussion

### Grammar Size

| Metric | Value |
|---|---|
| Non-terminals | 55 |
| Productions | ~121 |
| Terminals | ~40 |
| LL(1) table cells (non-empty) | ~400 |
| SLR(1) states | 229 |
| SLR(1) conflicts (all resolved) | 4 |

### Left-Recursion Removal

The original Decaf grammar has left-recursive rules for types and expressions.
These were eliminated before table construction:

**Type arrays:**
```
Original:  Type -> Type []    (left-recursive)
After:     Type       -> int TypeSuffix | double TypeSuffix | ...
           TypeSuffix -> [] TypeSuffix | epsilon
```

**Binary expressions (example -- all operators follow the same pattern):**
```
Original:  AddExpr -> AddExpr + MulExpr | AddExpr - MulExpr | MulExpr
After:     AddExpr -> MulExpr AddTail
           AddTail -> + MulExpr AddTail | - MulExpr AddTail | epsilon
```

### Operator Precedence

The precedence hierarchy is encoded structurally in the grammar:

| Level | Operators | Grammar Non-Terminal |
|---|---|---|
| Highest (1) | `[]`, `.` | PostTail |
| 2 | `!`, unary `-` | UnaryExpr |
| 3 | `*`, `/`, `%` | MulTail |
| 4 | `+`, `-` | AddTail |
| 5 | `<`, `<=`, `>`, `>=` | RelTail |
| 6 | `==`, `!=` | EqTail |
| 7 | `&&` | AndTail |
| 8 | `||` | OrTail |
| Lowest (9) | `=` | AssignTail |

Higher levels bind more tightly. Assignment `=` is right-associative (via
`AssignTail -> = Expr` which recurses back to `Expr`).

### Why "Essentially LL(1)"?

The Decaf grammar is not perfectly LL(1) (there are 4 conflicts), but it is
"essentially LL(1)" because:
- All conflicts are resolvable without backtracking.
- The dangling-else conflict is resolved by the standard "prefer shift" rule.
- The `Stmt -> VarDecl vs ExprStmt` conflict is resolved by a single extra
  lookahead token.
- The TypeSuffix and DeclList conflicts are resolved by straightforward
  context-based rules.

In practice, all real-world LL parsers handle these patterns, so the grammar
is considered LL(1) for all practical purposes.

---

## 12. Sample Programs and Outputs

### test1_valid.decaf

```decaf
void main() {
    int x;
    x = 5;
    int y;
    y = 10;
    int z;
    z = x + y;
    Print(z);
}

int add(int a, int b) {
    return a + b;
}
```

- Lexer: 43 tokens, 0 errors
- RD Parser: 2 function declarations, 3 local variables in `main`
- LL(1): ~120 parse steps, ACCEPT
- SLR(1): ~200 shift/reduce steps, ACCEPT

### test2_class.decaf

```decaf
class Animal { ... }
class Dog extends Animal { ... }
void main() { Dog d; d = New(Dog); d.speak(); }
```

- Tests class declarations, inheritance, `New()`, member access (`.`)
- Symbol table creates separate scopes for `Animal` and `Dog`

### test3_complex.decaf

Tests: `for` loops with init/update expressions, `while` loops, nested
`if`/`else`, `break`, interface declarations, array types (`int[]`),
`NewArray()`, complex expressions with all 9 precedence levels.

### test4_errors.decaf

Contains intentional errors. Example compiler output:
```
*** [SYNTAX] Line 5, Col 12: Expected ';', found 'id'
*** [SEMANTIC] Line 8, Col 5: Undefined identifier 'missingVar'
*** [SYNTAX] Line 12, Col 1: Expected '}', found '$'
```
The compiler recovers after each error and reports all three before exiting.

### test5_expressions.decaf

Tests the full expression grammar: all arithmetic operators, all comparison
operators, logical `&&` and `||`, negation `!`, unary minus `-`, assignment `=`,
compound expressions with mixed precedence, function calls, array indexing.

The SLR(1) parse trace for this file is particularly instructive -- it shows the
exact order of reductions that implements operator precedence.

---

## 13. Limitations and Future Work

### Current Limitations

1. **No semantic type checking** -- Types are recorded in the symbol table but
   the parsers do not verify that operand types are compatible (e.g., adding a
   string to an integer is not flagged).

2. **No code generation** -- The compiler is a front-end only. It produces an
   AST and a symbol table but generates no intermediate representation or target
   code.

3. **Single-file compilation** -- There is no import or include mechanism.
   All declarations must be in one `.decaf` source file.

4. **Arrays not fully validated** -- The symbol table records array types
   correctly, but subscript bounds are not checked at the type level.

5. **Method overriding not validated** -- When a subclass overrides a method,
   the override signature is not compared to the parent's signature.

6. **No `static` or `final`** -- These are absent from the Decaf specification
   and are not supported.

### Future Work

- **Semantic analysis phase**: full type checking, method override validation,
  `this` resolution, `null` safety.
- **Intermediate code generation**: three-address code or LLVM IR.
- **Optimisation**: constant folding, dead code elimination, loop invariant
  hoisting.
- **Better error recovery**: phrase-level recovery for common patterns (e.g.,
  inserting a missing semicolon).
- **Language Server Protocol (LSP) integration**: real-time syntax highlighting
  and error reporting in VS Code or another IDE.
- **Interactive REPL**: a read-eval-print loop for Decaf expressions.

---

## 14. References

1. **Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D.** (2006).
   *Compilers: Principles, Techniques, and Tools* (2nd ed.).
   Addison-Wesley. ("The Dragon Book")
   -- Primary reference for all lexer/parser algorithms, FIRST/FOLLOW
   computation, and LR table construction.

2. **Lam, M. S. et al.** (2003).
   *CS143 Decaf Language Specification*.
   Stanford University.
   https://web.stanford.edu/class/cs143/
   -- Formal specification of the Decaf language.

3. **Cooper, K. D., & Torczon, L.** (2011).
   *Engineering a Compiler* (2nd ed.).
   Morgan Kaufmann.
   -- Alternative perspective on compiler construction, especially useful for
   the symbol table and error recovery chapters.

4. **Python Software Foundation.**
   *Python 3 Documentation*.
   https://docs.python.org/3/
   -- Reference for the implementation language.

---

*This project was developed for CS-471L Compiler Construction Lab at UET Lahore,
Spring 2026.*
