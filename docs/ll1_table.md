# LL(1) Parse Table

## Overview

The LL(1) (Left-to-right, Leftmost derivation, 1 token lookahead) parse table
`M[A, a]` specifies, for each non-terminal `A` on top of the parse stack and
each possible next input token `a`, which production to apply.

### Construction Rule

For each production `A -> alpha`:

1. For each terminal `t` in `FIRST(alpha) \ {ε}`:  
   set `M[A, t] = A -> alpha`

2. If `ε ∈ FIRST(alpha)`:  
   for each terminal `t` in `FOLLOW(A)`:  
   set `M[A, t] = A -> alpha`

An entry of `error` (blank) means no production applies — a syntax error.
A cell with two productions indicates an LL(1) conflict.

### The Parsing Algorithm

```
Push $ onto stack
Push Start symbol onto stack
token = next_token()

loop:
  X = top of stack
  if X == $ and token == $:
    accept
  elif X is a terminal:
    if X == token.grammar_symbol:
      pop X from stack
      token = next_token()
    else:
      error("unexpected token")
  else:  # X is a non-terminal
    if M[X, token.grammar_symbol] exists:
      pop X from stack
      push M[X, token.grammar_symbol] (right-hand side) in reverse order
    else:
      error("no rule for M[" + X + ", " + token + "]")
      (panic-mode: skip until token in FOLLOW(X))
```

---

## LL(1) Table: Declarations and Types

The columns below show the production to apply (by production number from grammar.md).

### Program / DeclList / Decl

| NT       | `bool` | `class` | `double` | `id` | `int` | `interface` | `string` | `void` | `$` |
|----------|--------|---------|----------|------|-------|-------------|----------|--------|-----|
| Program  | P0     | P0      | P0       | P0   | P0    | P0          | P0       | P0     | P0  |
| DeclList | P1     | P1      | P1       | P1   | P1    | P1          | P1       | P1     | P2  |
| Decl     | P3/P4  | P5      | P3/P4    | P3/P4| P3/P4 | P6          | P3/P4    | P4     |     |

*P0 = `Program -> DeclList`; P1 = `DeclList -> Decl DeclList`; P2 = `DeclList -> ε`*
*P3 = `Decl -> VarDecl`; P4 = `Decl -> FuncDecl`; P5 = `Decl -> ClassDecl`; P6 = `Decl -> InterfaceDecl`*

Note: On lookahead `id` in Decl context, a 2-token lookahead distinguishes VarDecl
(`id id ;`) from FuncDecl (`id id ( ...)`).

### Type / TypeSuffix / RetType

| NT         | `bool` | `double` | `id` | `int` | `string` | `void` | `[`  | `)`  | other |
|------------|--------|----------|------|-------|----------|--------|------|------|-------|
| Type       | P13    | P12      | P15  | P11   | P14      |        |      |      |       |
| TypeSuffix |        |          |      |       |          |        | P16  | P17  | P17   |
| RetType    | P9     | P9       | P9   | P9    | P9       | P10    |      |      |       |

*P11=`Type->int TypeSuffix`; P12=`Type->double TypeSuffix`; P13=`Type->bool TypeSuffix`*
*P14=`Type->string TypeSuffix`; P15=`Type->id TypeSuffix`*
*P16=`TypeSuffix->[] TypeSuffix`; P17=`TypeSuffix->ε`*

### Formals / ParamList / ParamTail / Param

| NT        | `bool` | `double` | `id` | `int` | `string` | `)` | `,` |
|-----------|--------|----------|------|-------|----------|-----|-----|
| Formals   | P18    | P18      | P18  | P18   | P18      | P19 |     |
| ParamList | P20    | P20      | P20  | P20   | P20      |     |     |
| ParamTail |        |          |      |       |          | P22 | P21 |
| Param     | P23    | P23      | P23  | P23   | P23      |     |     |

---

## LL(1) Table: Statements

### Stmt / StmtList

| NT       | `bool` | `double`| `id` | `int` | `string` | `if` | `while`| `for` | `return`| `break`| `Print`| `{` | `}` |
|----------|--------|---------|------|-------|----------|------|--------|-------|---------|--------|--------|-----|-----|
| StmtList | P41    | P41     | P41  | P41   | P41      | P41  | P41    | P41   | P41     | P41    | P41    | P41 | P42 |
| Stmt     | P43    | P43     | *    | P43   | P43      | P45  | P46    | P47   | P48     | P49    | P50    | P51 |     |

`*` = 2-token lookahead: if next-next token is `id` => P43 (VarDecl), else P44 (ExprStmt)

*P41=`StmtList->Stmt StmtList`; P42=`StmtList->ε`*
*P43=`Stmt->VarDecl`; P44=`Stmt->ExprStmt`; P45=`Stmt->IfStmt`*
*P46=`Stmt->WhileStmt`; P47=`Stmt->ForStmt`; P48=`Stmt->ReturnStmt`*
*P49=`Stmt->BreakStmt`; P50=`Stmt->PrintStmt`; P51=`Stmt->Block`*

### IfStmt / ElsePart / WhileStmt / ReturnStmt

| NT         | `if`| `while`| `return`| `else`| `)`  | other FOLLOW(Stmt) |
|------------|-----|--------|---------|-------|------|--------------------|
| IfStmt     | P53 |        |         |       |      |                    |
| ElsePart   |     |        |         | P54   |      | P55 (ε)            |
| WhileStmt  |     | P56    |         |       |      |                    |
| ReturnStmt |     |        | P62     |       |      |                    |
| RetExprOpt | expr-first tokens => P63 | | | | P64 (ε) | P64 (ε) |

*P53=`IfStmt->if(Expr)Stmt ElsePart`; P54=`ElsePart->else Stmt`; P55=`ElsePart->ε`*

---

## LL(1) Table: Expressions

All expression non-terminals share the same large FIRST set. The table shows
which production to use based on the specific lookahead symbol.

### Expr / AssignTail

| NT         | expr-first tokens      | `=`  | `)` `,` `;` `]` |
|------------|------------------------|------|-----------------|
| Expr       | P70 (`Expr->OrExpr AssignTail`) | | |
| AssignTail | —                      | P71  | P72 (ε)         |

*P70=`Expr->OrExpr AssignTail`; P71=`AssignTail-> = Expr`; P72=`AssignTail->ε`*

### OrExpr / OrTail

| NT     | expr-first | `\|\|` | `)` `,` `;` `=` `]` |
|--------|------------|--------|---------------------|
| OrExpr | P73        |        |                     |
| OrTail |            | P74    | P75 (ε)             |

### AndExpr / AndTail

| NT      | expr-first | `&&` | `)` `,` `;` `=` `]` `\|\|` |
|---------|------------|------|-----------------------------|
| AndExpr | P76        |      |                             |
| AndTail |            | P77  | P78 (ε)                     |

### EqExpr / EqTail

| NT     | expr-first | `==` | `!=` | `&&` `)` `,` `;` `=` `]` `\|\|` |
|--------|------------|------|------|----------------------------------|
| EqExpr | P79        |      |      |                                  |
| EqTail |            | P80  | P81  | P82 (ε)                          |

### RelExpr / RelTail

| NT      | expr-first | `<`  | `<=` | `>`  | `>=` | FOLLOW(RelExpr) |
|---------|------------|------|------|------|------|-----------------|
| RelExpr | P83        |      |      |      |      |                 |
| RelTail |            | P84  | P85  | P86  | P87  | P88 (ε)         |

### AddExpr / AddTail

| NT      | expr-first | `+`  | `-`  | FOLLOW(AddExpr) |
|---------|------------|------|------|-----------------|
| AddExpr | P89        |      |      |                 |
| AddTail |            | P90  | P91  | P92 (ε)         |

### MulExpr / MulTail

| NT      | expr-first | `*`  | `/`  | `%`  | FOLLOW(MulExpr) |
|---------|------------|------|------|------|-----------------|
| MulExpr | P93        |      |      |      |                 |
| MulTail |            | P94  | P95  | P96  | P97 (ε)         |

### UnaryExpr / PostExpr / PostTail / CallTail

| NT        | `!`  | `-`  | PostExpr-first    | `.`  | `[`  | `(`  | FOLLOW |
|-----------|------|------|-------------------|------|------|------|--------|
| UnaryExpr | P98  | P99  | P100              |      |      |      |        |
| PostExpr  |      |      | P101              |      |      |      |        |
| PostTail  |      |      |                   | P103 | P102 |      | P104(ε)|
| CallTail  |      |      |                   |      |      | P105 | P106(ε)|

### Primary

| NT      | `id`  | INT   | DBL   | BOOL  | STR   | `null`| `this`| `(`  | ReadInteger | ReadLine | `New` | NewArray |
|---------|-------|-------|-------|-------|-------|-------|-------|------|-------------|----------|-------|----------|
| Primary | P107  | P108  | P109  | P110  | P111  | P112  | P113  | P114 | P115        | P116     | P117  | P118     |

### ActualList / ExprList / ExprListTail

| NT           | expr-first | `)` | `,` |
|--------------|------------|-----|-----|
| ActualList   | P119       | P120(ε) |  |
| ExprList     | P67        |     |     |
| ExprListTail |            | P69(ε) | P68 |

---

## Conflict Summary

| Conflict | Location | Resolution |
|----------|----------|------------|
| VarDecl vs ExprStmt | `M[Stmt, id]` | 2-token lookahead in RD parser; shift in SLR(1) |
| Dangling else | `M[ElsePart, else]` | Prefer shift (= P54 over P55) |
| TypeSuffix `[` in state 108 | SLR(1) table | Prefer reduce |
| `id` in state 1 | SLR(1) table | Prefer reduce |

---

## Sample Parse Trace: `void main() { return 0; }`

| Step | Stack (top right)              | Input Remaining    | Action                         |
|------|--------------------------------|--------------------|--------------------------------|
| 1    | `$` `Program`                  | `void main () ...` | M[Program, void] = P0          |
| 2    | `$` `DeclList`                 | `void main () ...` | M[DeclList, void] = P1         |
| 3    | `$` `DeclList` `Decl`          | `void main () ...` | M[Decl, void] = P4 (FuncDecl)  |
| 4    | `$` `DeclList` `FuncDecl`      | `void main () ...` | expand FuncDecl                |
| 5    | `$` `DeclList` `Block` `)` `Formals` `(` `id` `RetType` | `void ...` | M[RetType, void] = P10 |
| 6    | `$` `DeclList` `Block` `)` `Formals` `(` `id` `void` | `void ...` | match `void` |
| 7    | `$` `DeclList` `Block` `)` `Formals` `(` `id` | `main () ...` | match `id` = `main` |
| 8    | `$` `DeclList` `Block` `)` `Formals` `(` | `( ) ...` | match `(` |
| 9    | `$` `DeclList` `Block` `)` `Formals` | `) ...` | M[Formals, )] = P19 (ε) |
| 10   | `$` `DeclList` `Block` `)`     | `) ...`            | match `)`                      |
| 11   | `$` `DeclList` `Block`         | `{ return 0; }`    | M[Block, {] = P40              |
| 12   | `$` `DeclList` `}` `StmtList` `{` | `{ return 0; }` | match `{`                   |
| 13   | `$` `DeclList` `}` `StmtList`  | `return 0; }`      | M[StmtList, return] = P41      |
| 14   | `$` `DeclList` `}` `StmtList` `Stmt` | `return 0; }` | M[Stmt, return] = P48        |
| 15   | `$` `DeclList` `}` `StmtList` `ReturnStmt` | `return 0; }` | expand         |
| 16   | ... match `return`, expand `RetExprOpt`, match `0`, match `;` ... | | |
| 17   | `$` `DeclList` `}` `StmtList`  | `}`                | M[StmtList, }] = P42 (ε)      |
| 18   | `$` `DeclList` `}`             | `}`                | match `}`                      |
| 19   | `$` `DeclList`                 | `$`                | M[DeclList, $] = P2 (ε)       |
| 20   | `$`                            | `$`                | **ACCEPT**                     |
