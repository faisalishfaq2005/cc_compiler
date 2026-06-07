# FIRST and FOLLOW Sets — Decaf Grammar

## Overview

FIRST and FOLLOW sets are the mathematical foundation of LL(1) parsing.
They are computed once from the grammar and used to:

1. Build the LL(1) predictive parse table `M[A, a]`.
2. Drive panic-mode error recovery (skip until a FOLLOW-set token appears).
3. Construct the SLR(1) action table (reduce on tokens in FOLLOW(A)).

---

## Algorithm: Computing FIRST Sets

For every grammar symbol X, `FIRST(X)` is the set of terminals that can
appear as the first symbol of any string derived from X.

```
FIRST(a)        = {a}              for every terminal a
FIRST(ε)        = {ε}
FIRST(A)        starts empty, then iterate until no change:

  for each production A -> X1 X2 ... Xk:
    add FIRST(X1) \ {ε}  to  FIRST(A)
    if ε ∈ FIRST(X1):
      add FIRST(X2) \ {ε}  to  FIRST(A)
      ...
      if ε ∈ FIRST(X1) ∩ ... ∩ FIRST(Xk):
        add ε  to  FIRST(A)
```

**Worked example — FIRST(AddExpr):**

```
AddExpr -> MulExpr AddTail
FIRST(AddExpr) = FIRST(MulExpr) \ {ε}  (MulExpr cannot derive ε)

MulExpr -> UnaryExpr MulTail
FIRST(MulExpr) = FIRST(UnaryExpr) \ {ε}

UnaryExpr -> ! UnaryExpr   =>  adds {!}
UnaryExpr -> - UnaryExpr   =>  adds {-}
UnaryExpr -> PostExpr       =>  adds FIRST(PostExpr) \ {ε}
PostExpr  -> Primary PostTail
FIRST(PostExpr) = FIRST(Primary) = {(, BOOL_CONST, DOUBLE_CONST, INT_CONST,
                   New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this}

Therefore:
FIRST(UnaryExpr) = FIRST(MulExpr) = FIRST(AddExpr)
  = {!, -, (, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray,
     ReadInteger, ReadLine, STRING_CONST, id, null, this}
```

---

## Algorithm: Computing FOLLOW Sets

`FOLLOW(A)` is the set of terminals (and `$` for end-of-input) that can
appear immediately to the right of A in any sentential form.

```
FOLLOW(Start) = {$}
Then iterate until no change:

  for each production B -> α A β:
    add FIRST(β) \ {ε}  to  FOLLOW(A)
    if ε ∈ FIRST(β):        (β can vanish)
      add FOLLOW(B)  to  FOLLOW(A)

  for each production B -> α A:   (A at end)
    add FOLLOW(B)  to  FOLLOW(A)
```

**Worked example — FOLLOW(AssignTail):**

```
Expr -> OrExpr AssignTail
  => FOLLOW(AssignTail) includes FOLLOW(Expr) = {), ,, ;, ]}

AssignTail -> = Expr        (Expr embedded, its FOLLOW already noted)
AssignTail -> ε

So FOLLOW(AssignTail) = {), ,, ;, ]}
```

---

## Complete FIRST Sets

| Non-Terminal     | FIRST Set                                                                                                                       |
|------------------|---------------------------------------------------------------------------------------------------------------------------------|
| Program          | bool, class, double, id, int, interface, string, void, **ε**                                                                    |
| DeclList         | bool, class, double, id, int, interface, string, void, **ε**                                                                    |
| Decl             | bool, class, double, id, int, interface, string, void                                                                           |
| VarDecl          | bool, double, id, int, string                                                                                                   |
| FuncDecl         | bool, double, id, int, string, void                                                                                             |
| RetType          | bool, double, id, int, string, void                                                                                             |
| Type             | bool, double, id, int, string                                                                                                   |
| TypeSuffix       | **[**, **ε**                                                                                                                    |
| Formals          | bool, double, id, int, string, **ε**                                                                                            |
| ParamList        | bool, double, id, int, string                                                                                                   |
| ParamTail        | **,**, **ε**                                                                                                                    |
| Param            | bool, double, id, int, string                                                                                                   |
| ClassDecl        | class                                                                                                                           |
| ClassBase        | extends, **ε**                                                                                                                  |
| ClassImpl        | implements, **ε**                                                                                                               |
| IdentList        | id                                                                                                                              |
| IdentListTail    | **,**, **ε**                                                                                                                    |
| FieldList        | bool, double, id, int, string, void, **ε**                                                                                      |
| Field            | bool, double, id, int, string, void                                                                                             |
| InterfaceDecl    | interface                                                                                                                       |
| ProtoList        | bool, double, id, int, string, void, **ε**                                                                                      |
| Proto            | bool, double, id, int, string, void                                                                                             |
| Block            | **{**                                                                                                                           |
| StmtList         | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, Print, ReadInteger, ReadLine, STRING_CONST, bool, break, double, for, id, if, int, null, return, string, this, while, **{**, **ε** |
| Stmt             | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, Print, ReadInteger, ReadLine, STRING_CONST, bool, break, double, for, id, if, int, null, return, string, this, while, **{** |
| ExprStmt         | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this                |
| IfStmt           | if                                                                                                                              |
| ElsePart         | else, **ε**                                                                                                                     |
| WhileStmt        | while                                                                                                                           |
| ForStmt          | for                                                                                                                             |
| ForInit          | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this, **ε**        |
| ForUpdate        | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this, **ε**        |
| ReturnStmt       | return                                                                                                                          |
| RetExprOpt       | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this, **ε**        |
| BreakStmt        | break                                                                                                                           |
| PrintStmt        | Print                                                                                                                           |
| ExprList         | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this               |
| ExprListTail     | **,**, **ε**                                                                                                                    |
| Expr             | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this               |
| AssignTail       | **=**, **ε**                                                                                                                    |
| OrExpr           | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this               |
| OrTail           | **\|\|**, **ε**                                                                                                                 |
| AndExpr          | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this               |
| AndTail          | **&&**, **ε**                                                                                                                   |
| EqExpr           | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this               |
| EqTail           | **!=**, **==**, **ε**                                                                                                           |
| RelExpr          | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this               |
| RelTail          | **<**, **<=**, **>**, **>=**, **ε**                                                                                             |
| AddExpr          | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this               |
| AddTail          | **+**, **-**, **ε**                                                                                                             |
| MulExpr          | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this               |
| MulTail          | **%**, **\***, **/**, **ε**                                                                                                     |
| UnaryExpr        | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this               |
| PostExpr         | (, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this                     |
| PostTail         | **.**, **[**, **ε**                                                                                                             |
| CallTail         | **(**, **ε**                                                                                                                    |
| Primary          | (, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this                     |
| ActualList       | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, ReadInteger, ReadLine, STRING_CONST, id, null, this, **ε**        |

---

## Complete FOLLOW Sets

| Non-Terminal     | FOLLOW Set                                                                                                                      |
|------------------|---------------------------------------------------------------------------------------------------------------------------------|
| Program          | **$**                                                                                                                           |
| DeclList         | **$**                                                                                                                           |
| Decl             | $, bool, class, double, id, int, interface, string, void                                                                        |
| VarDecl          | !, $, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, Print, ReadInteger, ReadLine, STRING_CONST, bool, break, class, double, else, for, id, if, int, interface, null, return, string, this, void, while, {, } |
| FuncDecl         | $, bool, class, double, id, int, interface, string, void, **}**                                                                 |
| RetType          | id                                                                                                                              |
| Type             | **)**,  id                                                                                                                      |
| TypeSuffix       | **)**,  id                                                                                                                      |
| Formals          | **)**                                                                                                                           |
| ParamList        | **)**                                                                                                                           |
| ParamTail        | **)**                                                                                                                           |
| Param            | **)**,  **,**                                                                                                                   |
| ClassDecl        | $, bool, class, double, id, int, interface, string, void                                                                        |
| ClassBase        | implements, **{**                                                                                                               |
| ClassImpl        | **{**                                                                                                                           |
| IdentList        | **{**                                                                                                                           |
| IdentListTail    | **{**                                                                                                                           |
| FieldList        | **}**                                                                                                                           |
| Field            | bool, double, id, int, string, void, **}**                                                                                      |
| InterfaceDecl    | $, bool, class, double, id, int, interface, string, void                                                                        |
| ProtoList        | **}**                                                                                                                           |
| Proto            | bool, double, id, int, string, void, **}**                                                                                      |
| Block            | !, $, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, Print, ReadInteger, ReadLine, STRING_CONST, bool, break, class, double, else, for, id, if, int, interface, null, return, string, this, void, while, {, } |
| StmtList         | **}**                                                                                                                           |
| Stmt             | !, (, -, BOOL_CONST, DOUBLE_CONST, INT_CONST, New, NewArray, Print, ReadInteger, ReadLine, STRING_CONST, bool, break, double, else, for, id, if, int, null, return, string, this, while, {, } |
| ExprStmt         | same as FOLLOW(Stmt)                                                                                                            |
| IfStmt           | same as FOLLOW(Stmt)                                                                                                            |
| ElsePart         | same as FOLLOW(Stmt)                                                                                                            |
| WhileStmt        | same as FOLLOW(Stmt)                                                                                                            |
| ForStmt          | same as FOLLOW(Stmt)                                                                                                            |
| ReturnStmt       | same as FOLLOW(Stmt)                                                                                                            |
| RetExprOpt       | **;**                                                                                                                           |
| BreakStmt        | same as FOLLOW(Stmt)                                                                                                            |
| PrintStmt        | same as FOLLOW(Stmt)                                                                                                            |
| ExprList         | **)**                                                                                                                           |
| ExprListTail     | **)**                                                                                                                           |
| Expr             | **)**,  **,**,  **;**,  **]**                                                                                                   |
| AssignTail       | **)**,  **,**,  **;**,  **]**                                                                                                   |
| OrExpr           | **)**,  **,**,  **;**,  **=**,  **]**                                                                                           |
| OrTail           | **)**,  **,**,  **;**,  **=**,  **]**                                                                                           |
| AndExpr          | **)**,  **,**,  **;**,  **=**,  **]**,  **\|\|**                                                                               |
| AndTail          | **)**,  **,**,  **;**,  **=**,  **]**,  **\|\|**                                                                               |
| EqExpr           | **&&**,  **)**,  **,**,  **;**,  **=**,  **]**,  **\|\|**                                                                      |
| EqTail           | **&&**,  **)**,  **,**,  **;**,  **=**,  **]**,  **\|\|**                                                                      |
| RelExpr          | **!=**,  **&&**,  **)**,  **,**,  **;**,  **=**,  **==**,  **]**,  **\|\|**                                                    |
| RelTail          | **!=**,  **&&**,  **)**,  **,**,  **;**,  **=**,  **==**,  **]**,  **\|\|**                                                    |
| AddExpr          | **!=**,  **&&**,  **)**,  **,**,  **;**,  **<**,  **<=**,  **=**,  **==**,  **>**,  **>=**,  **]**,  **\|\|**                  |
| AddTail          | **!=**,  **&&**,  **)**,  **,**,  **;**,  **<**,  **<=**,  **=**,  **==**,  **>**,  **>=**,  **]**,  **\|\|**                  |
| MulExpr          | **!=**,  **&&**,  **)**,  **+**,  **,**,  **-**,  **;**,  **<**,  **<=**,  **=**,  **==**,  **>**,  **>=**,  **]**,  **\|\|** |
| MulTail          | **!=**,  **&&**,  **)**,  **+**,  **,**,  **-**,  **;**,  **<**,  **<=**,  **=**,  **==**,  **>**,  **>=**,  **]**,  **\|\|** |
| UnaryExpr        | **!=**,  **%**,  **&&**,  **)**,  **\***,  **+**,  **,**,  **-**,  **/**, **;**,  **<**,  **<=**,  **=**,  **==**,  **>**,  **>=**,  **]**,  **\|\|** |
| PostExpr         | same as FOLLOW(UnaryExpr)                                                                                                       |
| PostTail         | same as FOLLOW(UnaryExpr)                                                                                                       |
| CallTail         | **!=**,  **%**,  **&&**,  **)**,  **\***,  **+**,  **,**,  **-**,  **.**,  **/**,  **;**,  **<**,  **<=**,  **=**,  **==**,  **>**,  **>=**,  **[**,  **]**,  **\|\|** |
| Primary          | same as FOLLOW(CallTail)                                                                                                        |
| ActualList       | **)**                                                                                                                           |

---

## Key Observations

1. **All expression non-terminals share the same FIRST set.** This is expected
   because every expression can start with a unary operator, a literal, or an
   identifier. The left-to-right hierarchy encodes precedence, not disjoint
   first sets.

2. **FOLLOW(Stmt) is large.** It contains all tokens that can legitimately follow
   any statement, including tokens that begin the next statement. This large set
   is important for panic-mode recovery: after a syntax error inside a statement,
   the parser discards tokens until it sees something in FOLLOW(Stmt).

3. **ε in FIRST sets.** Non-terminals that can derive the empty string have ε in
   their FIRST set. These are exactly the non-terminals that require FOLLOW-set
   consultation in the LL(1) table: DeclList, TypeSuffix, Formals, ParamTail,
   ClassBase, ClassImpl, IdentListTail, FieldList, ProtoList, StmtList, ElsePart,
   ForInit, ForUpdate, RetExprOpt, ExprListTail, AssignTail, OrTail, AndTail,
   EqTail, RelTail, AddTail, MulTail, PostTail, CallTail, ActualList.
