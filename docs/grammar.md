# Decaf Grammar Specification

## Language Overview

Decaf is a strongly-typed, object-oriented language designed for compiler construction
courses. It is a subset of Java with a simplified type system and a fixed set of
built-in I/O operations. Decaf supports:

- Primitive types: `int`, `double`, `bool`, `string`
- One-dimensional arrays of any primitive or class type
- Class declarations with optional single inheritance (`extends`) and interface
  implementation (`implements`)
- Interface declarations (prototype lists only)
- Function declarations at the global scope and as class members
- A full expression language with 9 levels of operator precedence
- Control flow: `if/else`, `while`, `for`, `return`, `break`
- Built-in operations: `Print`, `ReadInteger`, `ReadLine`, `New`, `NewArray`

---

## BNF Grammar (LL(1) Form — Left-Recursion Free, Left-Factored)

The grammar below is the final, parser-ready form. All left-recursive rules have
been eliminated and all ambiguous prefixes have been left-factored.

### Program Structure

```bnf
Program    ::= DeclList
DeclList   ::= Decl DeclList
             | ε

Decl       ::= ClassDecl
             | InterfaceDecl
             | void id ( Formals ) Block
             | Type id DeclRest

DeclRest   ::= ;                     (* variable declaration *)
             | ( Formals ) Block     (* function declaration *)
```

> **Note on LL(1) disambiguation:** The original grammar `Decl -> VarDecl | FuncDecl`
> is not LL(1) because both alternatives begin with the same FIRST set (type keywords).
> We introduce `DeclRest` to defer the decision until after `Type id` has been consumed,
> at which point `;` (variable) and `(` (function) are distinct lookaheads.

### Variable and Function Declarations (semantic non-terminals)

These non-terminals remain for use by the recursive descent parser and symbol table, but are
folded into `DeclRest` and `FieldRest` for LL(1) parsing:

```bnf
VarDecl    ::= Type id ;

FuncDecl   ::= RetType id ( Formals ) Block

RetType    ::= Type
             | void

Type       ::= int    TypeSuffix
             | double TypeSuffix
             | bool   TypeSuffix
             | string TypeSuffix
             | id     TypeSuffix

TypeSuffix ::= [ ] TypeSuffix
             | ε

Formals    ::= ParamList
             | ε

ParamList  ::= Param ParamTail

ParamTail  ::= , Param ParamTail
             | ε

Param      ::= Type id
```

### Class and Interface Declarations

```bnf
ClassDecl  ::= class id ClassBase ClassImpl { FieldList }

ClassBase  ::= extends id
             | ε

ClassImpl  ::= implements IdentList
             | ε

IdentList      ::= id IdentListTail

IdentListTail  ::= , id IdentListTail
                 | ε

FieldList  ::= Field FieldList
             | ε

Field      ::= void id ( Formals ) Block
             | Type id FieldRest

FieldRest  ::= ;                     (* class variable *)
             | ( Formals ) Block     (* class method *)

InterfaceDecl  ::= interface id { ProtoList }

ProtoList  ::= Proto ProtoList
             | ε

Proto      ::= RetType id ( Formals ) ;
```

> **Note on Field disambiguation:** Same approach as `DeclRest`. After reading `Type id`,
> a `;` indicates a class variable and `(` indicates a method.

### Blocks and Statements

```bnf
Block      ::= { StmtList }

StmtList   ::= Stmt StmtList
             | ε

Stmt       ::= VarDecl
             | ExprStmt
             | IfStmt
             | WhileStmt
             | ForStmt
             | ReturnStmt
             | BreakStmt
             | PrintStmt
             | Block

ExprStmt   ::= Expr ;

IfStmt     ::= if ( Expr ) Stmt ElsePart
ElsePart   ::= else Stmt
             | ε

WhileStmt  ::= while ( Expr ) Stmt

ForStmt    ::= for ( ForInit ; Expr ; ForUpdate ) Stmt
ForInit    ::= Expr | ε
ForUpdate  ::= Expr | ε

ReturnStmt ::= return RetExprOpt ;
RetExprOpt ::= Expr | ε

BreakStmt  ::= break ;

PrintStmt  ::= Print ( ExprList ) ;

ExprList     ::= Expr ExprListTail
ExprListTail ::= , Expr ExprListTail
               | ε
```

### Expressions (Operator Precedence Encoded in Grammar)

```bnf
Expr       ::= OrExpr AssignTail
AssignTail ::= = Expr
             | ε

OrExpr     ::= AndExpr OrTail
OrTail     ::= || AndExpr OrTail
             | ε

AndExpr    ::= EqExpr AndTail
AndTail    ::= && EqExpr AndTail
             | ε

EqExpr     ::= RelExpr EqTail
EqTail     ::= == RelExpr
             | != RelExpr
             | ε

RelExpr    ::= AddExpr RelTail
RelTail    ::= <  AddExpr
             | <= AddExpr
             | >  AddExpr
             | >= AddExpr
             | ε

AddExpr    ::= MulExpr AddTail
AddTail    ::= + MulExpr AddTail
             | - MulExpr AddTail
             | ε

MulExpr    ::= UnaryExpr MulTail
MulTail    ::= * UnaryExpr MulTail
             | / UnaryExpr MulTail
             | % UnaryExpr MulTail
             | ε

UnaryExpr  ::= ! UnaryExpr
             | - UnaryExpr
             | PostExpr

PostExpr   ::= Primary PostTail
PostTail   ::= [ Expr ] PostTail
             | . id CallTail PostTail
             | ε

CallTail   ::= ( ActualList )
             | ε

Primary    ::= id CallTail
             | INT_CONST
             | DOUBLE_CONST
             | BOOL_CONST
             | STRING_CONST
             | null
             | this
             | ( Expr )
             | ReadInteger ( )
             | ReadLine ( )
             | New ( id )
             | NewArray ( Expr , Type )

ActualList ::= Expr ExprListTail
             | ε
```

---

## Left-Recursion Removal

The original Decaf specification uses a natural but left-recursive form for types
and expressions. Before constructing either an LL(1) or a recursive-descent parser,
all left recursion must be eliminated.

### Array Type Suffix

The original specification writes:

```
Type  ::= int | double | bool | string | id        (primitive)
       | Type []                                    (LEFT RECURSIVE)
```

This was transformed by introducing a new non-terminal `TypeSuffix`:

```bnf
Type       ::= int TypeSuffix | double TypeSuffix | bool TypeSuffix
             | string TypeSuffix | id TypeSuffix
TypeSuffix ::= [ ] TypeSuffix | ε
```

`TypeSuffix` captures zero or more `[]` suffixes in a right-recursive manner,
which can be handled by both recursive descent and stack-based LL(1) parsing.

### Expression Left Recursion

The standard left-recursive arithmetic grammar:

```
AddExpr ::= AddExpr + MulExpr | AddExpr - MulExpr | MulExpr
```

was transformed using the standard technique (introducing a right-recursive tail):

```bnf
AddExpr ::= MulExpr AddTail
AddTail ::= + MulExpr AddTail | - MulExpr AddTail | ε
```

The same pattern applies to `OrExpr`/`OrTail`, `AndExpr`/`AndTail`,
`EqExpr`/`EqTail`, `RelExpr`/`RelTail`, and `MulExpr`/`MulTail`.

---

## Operator Precedence

The precedence levels are encoded structurally in the grammar hierarchy.
A lower position in the hierarchy means higher binding strength.

| Level | Operator(s)           | Associativity | Grammar Rule         |
|-------|-----------------------|---------------|----------------------|
| 1     | `[]`  `.`             | Left          | PostTail             |
| 2     | `!`   unary `-`       | Right         | UnaryExpr            |
| 3     | `*`   `/`   `%`       | Left          | MulTail              |
| 4     | `+`   `-`             | Left          | AddTail              |
| 5     | `<`   `<=`  `>`  `>=` | Left          | RelTail              |
| 6     | `==`  `!=`            | Left          | EqTail               |
| 7     | `&&`                  | Left          | AndTail              |
| 8     | `\|\|`                | Left          | OrTail               |
| 9     | `=`                   | Right         | AssignTail           |

Assignment (`=`) has the lowest precedence and is right-associative by the
rule `AssignTail ::= = Expr` (Expr recurses back to the top).

---

## LL(1) Conflict Analysis

### Conflict 1 — Stmt: VarDecl vs ExprStmt on `id`

When the next token is an identifier (`id`), the parser cannot immediately
distinguish:

```
Stmt -> VarDecl  (starts with Type -> id TypeSuffix)
Stmt -> ExprStmt (starts with Expr -> ... -> Primary -> id ...)
```

**Resolution:** A two-token lookahead is used. If the token after `id` is
another `id`, the statement is a `VarDecl` (the first `id` is a class-type name,
the second is the declared variable name). Otherwise it is an `ExprStmt`.
This is implemented in the recursive-descent parser as a speculative peek.

### Conflict 2 — Dangling Else

The rule:
```
IfStmt  ::= if ( Expr ) Stmt ElsePart
ElsePart ::= else Stmt | ε
```
is ambiguous when `else` follows an `if` inside another `if`. The shift/reduce
conflict in the SLR(1) automaton (state 218, token `else`) is resolved by
preferring the **shift** action, which binds `else` to the nearest enclosing
`if`. This is the standard resolution and matches the behavior of C, Java, etc.

### Conflict 3 — TypeSuffix on `[`

State 108 in the SLR(1) automaton sees both a potential shift (`[` begins a new
`TypeSuffix`) and a reduce (the `TypeSuffix` rule is complete). This arises from
the dual role of `[` as both a type-suffix opener and an array-subscript operator
in the expression grammar. It is resolved by reducing (the type declaration
context has already been concluded by that state).

### Conflict 4 — Shift/Reduce on `id` in State 1

State 1 sees a shift/reduce conflict on `id`. It is resolved by reducing, which
correctly prioritizes completing a pending `DeclList` item before shifting a new
declaration.

### Summary

Despite these four conflicts, the grammar is considered **"essentially LL(1)"**:
all conflicts have deterministic, context-free resolutions, and no backtracking
is required. The recursive-descent parser resolves conflicts inline; the SLR(1)
parser resolves them through explicit conflict-resolution rules applied during
table construction.

---

## Production Index Reference

| #  | Production                                           |
|----|------------------------------------------------------|
| 0  | Program -> DeclList                                  |
| 1  | DeclList -> Decl DeclList                            |
| 2  | DeclList -> ε                                        |
| 3  | Decl -> VarDecl                                      |
| 4  | Decl -> FuncDecl                                     |
| 5  | Decl -> ClassDecl                                    |
| 6  | Decl -> InterfaceDecl                                |
| 7  | VarDecl -> Type id ;                                 |
| 8  | FuncDecl -> RetType id ( Formals ) Block             |
| 9  | RetType -> Type                                      |
| 10 | RetType -> void                                      |
| 11 | Type -> int TypeSuffix                               |
| 12 | Type -> double TypeSuffix                            |
| 13 | Type -> bool TypeSuffix                              |
| 14 | Type -> string TypeSuffix                            |
| 15 | Type -> id TypeSuffix                                |
| 16 | TypeSuffix -> [ ] TypeSuffix                         |
| 17 | TypeSuffix -> ε                                      |
| 18 | Formals -> ParamList                                 |
| 19 | Formals -> ε                                         |
| 20 | ParamList -> Param ParamTail                         |
| 21 | ParamTail -> , Param ParamTail                       |
| 22 | ParamTail -> ε                                       |
| 23 | Param -> Type id                                     |
| 24 | ClassDecl -> class id ClassBase ClassImpl { FieldList } |
| 25 | ClassBase -> extends id                              |
| 26 | ClassBase -> ε                                       |
| 27 | ClassImpl -> implements IdentList                    |
| 28 | ClassImpl -> ε                                       |
| 29 | IdentList -> id IdentListTail                        |
| 30 | IdentListTail -> , id IdentListTail                  |
| 31 | IdentListTail -> ε                                   |
| 32 | FieldList -> Field FieldList                         |
| 33 | FieldList -> ε                                       |
| 34 | Field -> VarDecl                                     |
| 35 | Field -> FuncDecl                                    |
| 36 | InterfaceDecl -> interface id { ProtoList }          |
| 37 | ProtoList -> Proto ProtoList                         |
| 38 | ProtoList -> ε                                       |
| 39 | Proto -> RetType id ( Formals ) ;                    |
| 40 | Block -> { StmtList }                                |
| 41 | StmtList -> Stmt StmtList                            |
| 42 | StmtList -> ε                                        |
| 43 | Stmt -> VarDecl                                      |
| 44 | Stmt -> ExprStmt                                     |
| 45 | Stmt -> IfStmt                                       |
| 46 | Stmt -> WhileStmt                                    |
| 47 | Stmt -> ForStmt                                      |
| 48 | Stmt -> ReturnStmt                                   |
| 49 | Stmt -> BreakStmt                                    |
| 50 | Stmt -> PrintStmt                                    |
| 51 | Stmt -> Block                                        |
| 52 | ExprStmt -> Expr ;                                   |
| 53 | IfStmt -> if ( Expr ) Stmt ElsePart                  |
| 54 | ElsePart -> else Stmt                                |
| 55 | ElsePart -> ε                                        |
| 56 | WhileStmt -> while ( Expr ) Stmt                     |
| 57 | ForStmt -> for ( ForInit ; Expr ; ForUpdate ) Stmt   |
| 58 | ForInit -> Expr                                      |
| 59 | ForInit -> ε                                         |
| 60 | ForUpdate -> Expr                                    |
| 61 | ForUpdate -> ε                                       |
| 62 | ReturnStmt -> return RetExprOpt ;                    |
| 63 | RetExprOpt -> Expr                                   |
| 64 | RetExprOpt -> ε                                      |
| 65 | BreakStmt -> break ;                                 |
| 66 | PrintStmt -> Print ( ExprList ) ;                    |
| 67 | ExprList -> Expr ExprListTail                        |
| 68 | ExprListTail -> , Expr ExprListTail                  |
| 69 | ExprListTail -> ε                                    |
| 70 | Expr -> OrExpr AssignTail                            |
| 71 | AssignTail -> = Expr                                 |
| 72 | AssignTail -> ε                                      |
| 73 | OrExpr -> AndExpr OrTail                             |
| 74 | OrTail -> \|\| AndExpr OrTail                        |
| 75 | OrTail -> ε                                          |
| 76 | AndExpr -> EqExpr AndTail                            |
| 77 | AndTail -> && EqExpr AndTail                         |
| 78 | AndTail -> ε                                         |
| 79 | EqExpr -> RelExpr EqTail                             |
| 80 | EqTail -> == RelExpr                                 |
| 81 | EqTail -> != RelExpr                                 |
| 82 | EqTail -> ε                                          |
| 83 | RelExpr -> AddExpr RelTail                           |
| 84 | RelTail -> < AddExpr                                 |
| 85 | RelTail -> <= AddExpr                                |
| 86 | RelTail -> > AddExpr                                 |
| 87 | RelTail -> >= AddExpr                                |
| 88 | RelTail -> ε                                         |
| 89 | AddExpr -> MulExpr AddTail                           |
| 90 | AddTail -> + MulExpr AddTail                         |
| 91 | AddTail -> - MulExpr AddTail                         |
| 92 | AddTail -> ε                                         |
| 93 | MulExpr -> UnaryExpr MulTail                         |
| 94 | MulTail -> * UnaryExpr MulTail                       |
| 95 | MulTail -> / UnaryExpr MulTail                       |
| 96 | MulTail -> % UnaryExpr MulTail                       |
| 97 | MulTail -> ε                                         |
| 98 | UnaryExpr -> ! UnaryExpr                             |
| 99 | UnaryExpr -> - UnaryExpr                             |
| 100| UnaryExpr -> PostExpr                                |
| 101| PostExpr -> Primary PostTail                         |
| 102| PostTail -> [ Expr ] PostTail                        |
| 103| PostTail -> . id CallTail PostTail                   |
| 104| PostTail -> ε                                        |
| 105| CallTail -> ( ActualList )                           |
| 106| CallTail -> ε                                        |
| 107| Primary -> id CallTail                               |
| 108| Primary -> INT_CONST                                 |
| 109| Primary -> DOUBLE_CONST                              |
| 110| Primary -> BOOL_CONST                                |
| 111| Primary -> STRING_CONST                              |
| 112| Primary -> null                                      |
| 113| Primary -> this                                      |
| 114| Primary -> ( Expr )                                  |
| 115| Primary -> ReadInteger ( )                           |
| 116| Primary -> ReadLine ( )                              |
| 117| Primary -> New ( id )                                |
| 118| Primary -> NewArray ( Expr , Type )                  |
| 119| ActualList -> Expr ExprListTail                      |
| 120| ActualList -> ε                                      |
