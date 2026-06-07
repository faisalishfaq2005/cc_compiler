# SLR(1) Parse Table

## Algorithm Choice: SLR(1)

We chose SLR(1) (Simple LR with 1-token lookahead) because:

1. It is more powerful than LR(0): it uses FOLLOW sets to restrict reduce
   actions, eliminating many spurious reduce/reduce conflicts.
2. It is simpler to construct than LALR(1) or canonical LR(1): no lookahead
   sets need to be propagated through the item sets.
3. The Decaf grammar, with four explicit conflict resolutions (see below), is
   SLR(1)-parseable.
4. FOLLOW sets were already computed for the LL(1) parser, so no additional
   analysis is required.

The compiled Decaf SLR(1) automaton has **229 states** and **4 resolved
conflicts**.

---

## Bottom-Up Parsing Concepts

### Shift-Reduce Parsing

LR parsing is bottom-up: it reads input left-to-right and builds the parse tree
from leaves to root. At each step the parser either:

- **Shifts**: pushes the next input token onto the stack, advances input pointer.
- **Reduces**: replaces the top `k` symbols of the stack with the left-hand side
  of the production `A -> X1 X2 ... Xk`, effectively recognising a handle.
- **Accepts**: when the stack contains only `$` and `Start'` and input is `$`.
- **Errors**: no valid action exists.

### LR(0) Items

An **LR(0) item** is a production with a dot marker showing how far parsing has
progressed:

```
[A -> alpha . beta]   means: we have matched alpha; beta is still expected
```

The dot advances on shift (terminal ahead) or on goto (non-terminal just
reduced):

```
[A -> alpha . X beta]  --shift/goto X-->  [A -> alpha X . beta]
```

### Closure Operation

```
closure(I):
  result = I
  for each [A -> alpha . B beta] in result:
    for each production B -> gamma:
      add [B -> . gamma] to result (if not already present)
  return result
```

### Goto Operation

```
goto(I, X):
  result = {[A -> alpha X . beta] : [A -> alpha . X beta] in I}
  return closure(result)
```

---

## LR(0) Item Sets: Key States

### State 0 (Initial State)

The augmented grammar adds production `Program' -> . Program $`.

```
[Program' -> . Program]          (kernel)
[Program  -> . DeclList]         (closure)
[DeclList -> . Decl DeclList]    (closure)
[DeclList -> .]                  (closure -- reduce on $)
[Decl     -> . VarDecl]          (closure)
[Decl     -> . FuncDecl]         (closure)
[Decl     -> . ClassDecl]        (closure)
[Decl     -> . InterfaceDecl]    (closure)
[VarDecl  -> . Type id ;]        (closure)
[FuncDecl -> . RetType id ( Formals ) Block]  (closure)
[Type     -> . int TypeSuffix]   (closure)
[Type     -> . double TypeSuffix] (closure)
[Type     -> . bool TypeSuffix]  (closure)
[Type     -> . string TypeSuffix] (closure)
[Type     -> . id TypeSuffix]    (closure)
[RetType  -> . Type]             (closure)
[RetType  -> . void]             (closure)
[ClassDecl -> . class id ClassBase ClassImpl { FieldList }]  (closure)
[InterfaceDecl -> . interface id { ProtoList }]  (closure)
```

**Transitions from State 0:**

| Symbol        | Goto State |
|---------------|------------|
| `Program`     | State 1    |
| `DeclList`    | State 2    |
| `Decl`        | State 3    |
| `VarDecl`     | State 4    |
| `FuncDecl`    | State 5    |
| `ClassDecl`   | State 6    |
| `InterfaceDecl` | State 7  |
| `Type`        | State 8    |
| `RetType`     | State 9    |
| `int`         | State 10   |
| `double`      | State 11   |
| `bool`        | State 12   |
| `string`      | State 13   |
| `id`          | State 14   |
| `void`        | State 15   |
| `class`       | State 16   |
| `interface`   | State 17   |

### State 1 (Program seen)

```
[Program' -> Program .]    (kernel — accept on $)
```

**Action:** `accept` on `$`.  
**Conflict (Resolved):** Shift/reduce conflict on `id` — resolved by reducing.

### State 2 (DeclList seen from State 0)

```
[Program -> DeclList .]    (kernel)
[DeclList -> . Decl DeclList]
[DeclList -> .]
```

**Action:** reduce by `Program -> DeclList` on `$`.

### State 10 (After seeing `int`)

```
[Type -> int . TypeSuffix]
[TypeSuffix -> . [ ] TypeSuffix]
[TypeSuffix -> .]
```

**Transitions:**
- `[` -> State for `TypeSuffix -> [ . ] TypeSuffix`
- otherwise reduce by `TypeSuffix -> ε`, then reduce by `Type -> int TypeSuffix`

### State 108 (TypeSuffix conflict state)

This state arises in the context where the parser has just seen the first `[`
of a possible type suffix and must decide whether another `[` starts a new
TypeSuffix or ends the current context.

```
[TypeSuffix -> [ ] . TypeSuffix]   (can shift [ for nested suffix)
[TypeSuffix -> .]                   (can reduce TypeSuffix -> ε)
```

**Conflict on `[`:** shift (start nested `TypeSuffix`) vs reduce (`TypeSuffix -> ε`).  
**Resolution:** **Reduce** — the type declaration context is already fully parsed
at this point; a `[` after this state belongs to an expression context.

**Conflict on `)`:** reduce/reduce between two `TypeSuffix -> ε` instances.  
**Resolution:** **Reduce** by the first applicable production.

### State 218 (Dangling else conflict state)

This state contains items representing the post-`Stmt` position in an `IfStmt`:

```
[IfStmt -> if ( Expr ) Stmt . ElsePart]
[ElsePart -> .]                          (reduce on FOLLOW(ElsePart))
[ElsePart -> . else Stmt]               (shift on else)
```

**Conflict on `else`:** shift (P54: bind to nearest if) vs reduce (P55: ε, leave
else for outer if).  
**Resolution:** **Shift** — standard dangling-else resolution.

---

## Action Table: Selected Entries

Format: `s`N = shift to state N; `r`P = reduce by production P; `acc` = accept.

| State | `int` | `void` | `class` | `id` | `{` | `}` | `if` | `return` | `;` | `$` |
|-------|-------|--------|---------|------|-----|-----|------|----------|-----|-----|
| 0     | s10   | s15    | s16     | s14  |     |     |      |          |     |     |
| 1     |       |        |         | r(resolve) | | | |       |     | acc |
| 2     |       |        |         |      |     |     |      |          |     | r0  |
| 10    | —     | —      | —       | r17  | r17 | r17 | r17  | r17      | r17 | r17 |
| 218   |       |        |         |      |     | r55 | r55  | r55      |     | r55 |
| 218   | s219 (else->shift) | | | | | | | | | |

*State 218 on `else`: shift to 219 (dangling-else resolution)*
*State 218 on FOLLOW(Stmt) \ {else}: reduce by ElsePart -> ε*

---

## Goto Table: Selected Entries

| State | `Program` | `DeclList` | `Decl` | `Type` | `Block` | `Stmt` | `Expr` |
|-------|-----------|------------|--------|--------|---------|--------|--------|
| 0     | 1         | 2          | 3      | 8      |         |        |        |
| 2     |           | —          | 3      | 8      |         |        |        |
| ...   |           |            |        |        | ...     |        |        |

---

## Conflict Resolution Summary

| # | State | Token | Conflict Type   | Resolution         | Justification                              |
|---|-------|-------|-----------------|--------------------|--------------------------------------------|
| 1 | 218   | `else`| Shift/Reduce    | Shift (P54)        | Dangling-else: bind else to nearest if     |
| 2 | 108   | `[`   | Shift/Reduce    | Reduce (TypeSuffix->ε) | Type context complete; `[` is expr context |
| 3 | 108   | `)`   | Reduce/Reduce   | Reduce (first)     | Both reduce TypeSuffix->ε; first wins      |
| 4 | 1     | `id`  | Shift/Reduce    | Reduce             | Complete DeclList before shifting new Decl |

---

## Parse Trace: test1_valid.decaf (first 20 steps)

Source: `void main() { int x; x = 5; Print(z); }`

| Step | State Stack        | Symbol Stack            | Input                  | Action                    |
|------|--------------------|-------------------------|------------------------|---------------------------|
| 1    | [0]                | [$]                     | void main ( ) { ...    | s15 (shift void)          |
| 2    | [0,15]             | [$, void]               | main ( ) { ...         | s(id)=shift main          |
| 3    | [0,15,N]           | [$, void, id]           | ( ) { ...              | goto[RetType]             |
| 4    | [0,15,N,R]         | [$, RetType]            | main ( ...             | s(id) shift main          |
| 5    | [...]              | [$, RetType, id]        | ( ) { ...              | shift (                   |
| 6    | [...]              | [$, RetType, id, (]     | ) { ...                | r19 Formals->ε            |
| 7    | [...]              | [$, RetType, id, (, Formals] | ) { ...           | shift )                   |
| 8    | [...]              | [$, RetType, id, (, Formals, )] | { ...           | goto Block                |
| 9    | [...]              | [...]                   | { int x ; ...          | shift {                   |
| 10   | [...]              | [..., {]                | int x ; ...            | s10 (shift int)           |
| 11   | [...]              | [..., {, int]           | x ; ...                | r17 TypeSuffix->ε         |
| 12   | [...]              | [..., {, int, TypeSuffix] | x ; ...             | r11 Type->int TypeSuffix  |
| 13   | [...]              | [..., {, Type]          | x ; ...                | s(id) shift x             |
| 14   | [...]              | [..., {, Type, id]      | ; ...                  | s(;) shift ;              |
| 15   | [...]              | [..., {, Type, id, ;]   | x = 5 ...              | r7 VarDecl->Type id ;     |
| 16   | [...]              | [..., {, VarDecl]       | x = 5 ...              | r43 Stmt->VarDecl         |
| 17   | [...]              | [..., {, Stmt]          | x = 5 ...              | goto StmtList...          |
| 18   | [...]              | [..., StmtList]         | x = 5 ...              | shift x (ExprStmt path)   |
| 19   | [...]              | [...]                   | = 5 ...                | ... (expression reductions)|
| 20   | [...]              | [...]                   | Print ( z ) ; ...      | ... (continue)            |

The full trace (hundreds of steps) is written to `output/test1_valid_lr_parser.txt`
when you run: `python src/main.py test/test1_valid.decaf --lr`

---

## SLR(1) Algorithm Summary

```
Input: token stream
Stack: [0]                      (start with initial state)
symbol_stack: [$]

loop:
  s = top of state_stack
  a = next input token
  
  if action[s, a] == shift t:
    push a onto symbol_stack
    push t onto state_stack
    advance input
    
  elif action[s, a] == reduce A -> beta:
    pop |beta| states from state_stack
    pop |beta| symbols from symbol_stack
    t = goto[top_of_state_stack, A]
    push A onto symbol_stack
    push t onto state_stack
    
  elif action[s, a] == accept:
    DONE -- successful parse
    
  else:
    error("no action for state " + s + ", token " + a)
    panic_mode_recover()
```

The complete action and goto tables are written to `output/lr_table.txt` when
you run: `python src/main.py test/test1_valid.decaf --lr-table`
