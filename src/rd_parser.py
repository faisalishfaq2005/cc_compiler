"""
rd_parser.py - Recursive Descent Parser for the Decaf mini-compiler.

One method per non-terminal from the Decaf LL(1) grammar.
Builds a dict-based AST, populates the symbol table, and reports errors
via the error handler. Uses panic-mode recovery with FOLLOW sets.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from tokens import Token, TokenType
from symbol_table import SymbolEntry


# ---------------------------------------------------------------------------
# FOLLOW sets (abbreviated) used for panic-mode recovery in each NT
# ---------------------------------------------------------------------------
FOLLOW = {
    'Program':       {'$'},
    'DeclList':      {'$'},
    'Decl':          {'int', 'double', 'bool', 'string', 'void', 'class', 'interface',
                      'id', '$'},
    'VarDecl':       {'int', 'double', 'bool', 'string', 'void', 'class', 'interface',
                      'id', '}', '$'},
    'FuncDecl':      {'int', 'double', 'bool', 'string', 'void', 'class', 'interface',
                      'id', '}', '$'},
    'RetType':       {'id'},
    'Type':          {'id', ';', ',', '(', ')'},
    'TypeSuffix':    {'id', ';', ',', '(', ')'},
    'Formals':       {')'},
    'ParamList':     {')'},
    'ParamTail':     {')'},
    'Param':         {')', ','},
    'ClassDecl':     {'int', 'double', 'bool', 'string', 'void', 'class', 'interface',
                      'id', '$'},
    'ClassBase':     {'implements', '{'},
    'ClassImpl':     {'{'},
    'IdentList':     {'{'},
    'IdentListTail': {'{'},
    'FieldList':     {'}'},
    'Field':         {'int', 'double', 'bool', 'string', 'void', 'id', '}'},
    'InterfaceDecl': {'int', 'double', 'bool', 'string', 'void', 'class', 'interface',
                      'id', '$'},
    'ProtoList':     {'}'},
    'Proto':         {'int', 'double', 'bool', 'string', 'void', 'id', '}'},
    'Block':         {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', 'id', '$'},
    'StmtList':      {'}'},
    'Stmt':          {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', 'id', ';', 'else', '$'},
    'ExprStmt':      {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', '$'},
    'IfStmt':        {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', 'else', '$'},
    'ElsePart':      {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', 'else', '$'},
    'WhileStmt':     {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', '$'},
    'ForStmt':       {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', '$'},
    'ForInit':       {';'},
    'ForUpdate':     {')'},
    'ReturnStmt':    {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', '$'},
    'RetExprOpt':    {';'},
    'BreakStmt':     {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', '$'},
    'PrintStmt':     {'int', 'double', 'bool', 'string', 'if', 'while', 'for',
                      'return', 'break', 'Print', '{', '}', '$'},
    'ExprList':      {')'},
    'ExprListTail':  {')'},
    'Expr':          {';', ')', ',', ']'},
    'AssignTail':    {';', ')', ',', ']'},
    'OrExpr':        {';', ')', ',', ']', '='},
    'OrTail':        {';', ')', ',', ']', '='},
    'AndExpr':       {';', ')', ',', ']', '=', '||'},
    'AndTail':       {';', ')', ',', ']', '=', '||'},
    'EqExpr':        {';', ')', ',', ']', '=', '||', '&&'},
    'EqTail':        {';', ')', ',', ']', '=', '||', '&&'},
    'RelExpr':       {';', ')', ',', ']', '=', '||', '&&', '==', '!='},
    'RelTail':       {';', ')', ',', ']', '=', '||', '&&', '==', '!='},
    'AddExpr':       {';', ')', ',', ']', '=', '||', '&&', '==', '!=',
                      '<', '<=', '>', '>='},
    'AddTail':       {';', ')', ',', ']', '=', '||', '&&', '==', '!=',
                      '<', '<=', '>', '>='},
    'MulExpr':       {';', ')', ',', ']', '=', '||', '&&', '==', '!=',
                      '<', '<=', '>', '>=', '+', '-'},
    'MulTail':       {';', ')', ',', ']', '=', '||', '&&', '==', '!=',
                      '<', '<=', '>', '>=', '+', '-'},
    'UnaryExpr':     {';', ')', ',', ']', '=', '||', '&&', '==', '!=',
                      '<', '<=', '>', '>=', '+', '-', '*', '/', '%'},
    'PostExpr':      {';', ')', ',', ']', '=', '||', '&&', '==', '!=',
                      '<', '<=', '>', '>=', '+', '-', '*', '/', '%'},
    'PostTail':      {';', ')', ',', ']', '=', '||', '&&', '==', '!=',
                      '<', '<=', '>', '>=', '+', '-', '*', '/', '%'},
    'CallTail':      {'[', '.', ';', ')', ',', ']', '=', '||', '&&', '==', '!=',
                      '<', '<=', '>', '>=', '+', '-', '*', '/', '%'},
    'Primary':       {'[', '.', ';', ')', ',', ']', '=', '||', '&&', '==', '!=',
                      '<', '<=', '>', '>=', '+', '-', '*', '/', '%'},
    'ActualList':    {')'},
}

# FIRST sets for deciding which production to use
# (only the sets we need for dispatch in the parser methods)
FIRST_TYPE = {TokenType.KW_INT, TokenType.KW_DOUBLE, TokenType.KW_BOOL,
              TokenType.KW_STRING, TokenType.IDENTIFIER}
FIRST_RETTYPE = FIRST_TYPE | {TokenType.KW_VOID}
FIRST_STMT_NONDECL = {
    TokenType.KW_IF, TokenType.KW_WHILE, TokenType.KW_FOR,
    TokenType.KW_RETURN, TokenType.KW_BREAK, TokenType.KW_PRINT,
    TokenType.LBRACE,
    # Expression starters
    TokenType.IDENTIFIER, TokenType.INT_CONST, TokenType.DOUBLE_CONST,
    TokenType.BOOL_CONST, TokenType.STRING_CONST,
    TokenType.KW_NULL, TokenType.KW_THIS, TokenType.LPAREN,
    TokenType.KW_READINTEGER, TokenType.KW_READLINE,
    TokenType.KW_NEW, TokenType.KW_NEWARRAY,
    TokenType.MINUS, TokenType.NOT,
}
FIRST_EXPR = {
    TokenType.IDENTIFIER, TokenType.INT_CONST, TokenType.DOUBLE_CONST,
    TokenType.BOOL_CONST, TokenType.STRING_CONST,
    TokenType.KW_NULL, TokenType.KW_THIS, TokenType.LPAREN,
    TokenType.KW_READINTEGER, TokenType.KW_READLINE,
    TokenType.KW_NEW, TokenType.KW_NEWARRAY,
    TokenType.MINUS, TokenType.NOT,
}


def make_node(kind, children=None, value=None, line=None, col=None):
    """Create an AST node dict."""
    node = {'type': kind, 'children': children or [], 'value': value}
    if line is not None:
        node['line'] = line
    if col is not None:
        node['col'] = col
    return node


class RecursiveDescentParser:
    """
    Hand-written recursive descent parser for Decaf.

    Each parse_X() method corresponds to non-terminal X and returns an AST node.
    Errors are reported via self.eh and recovery skips to the FOLLOW set.
    Symbol table is populated on declarations.
    """

    def __init__(self, lexer, symbol_table, error_handler):
        self.lexer = lexer
        self.st = symbol_table
        self.eh = error_handler
        self.current = None
        self.tokens_parsed = 0
        self._current_function_return_type = None
        self._in_loop = 0
        self.advance()  # load first token

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------

    def advance(self):
        self.current = self.lexer.next_token()
        self.tokens_parsed += 1

    def peek(self):
        return self.lexer.peek_token()

    def match(self, expected_type: TokenType) -> Token:
        """Consume and return current token if it matches expected_type."""
        if self.current.type == expected_type:
            tok = self.current
            self.advance()
            return tok
        else:
            suggestion = self.eh.phrase_level_suggest(
                expected_type.name, self.current.type.name)
            self.eh.report_error(
                'SYNTAX',
                f"Expected {expected_type.name}, got {self.current.type.name} "
                f"('{self.current.value}'). {suggestion}",
                self.current.line, self.current.col)
            # Return a fake token for error recovery (don't advance)
            return Token(expected_type, None, self.current.line, self.current.col)

    def match_sym(self, sym_str: str) -> Token:
        """Match by grammar symbol string (e.g., ';', 'id')."""
        gs = self.current.grammar_symbol()
        if gs == sym_str:
            tok = self.current
            self.advance()
            return tok
        else:
            self.eh.report_error(
                'SYNTAX',
                f"Expected '{sym_str}', got '{gs}' ('{self.current.value}')",
                self.current.line, self.current.col)
            return Token(TokenType.ERROR, None, self.current.line, self.current.col)

    def _sync(self, follow_set: set):
        """Panic-mode recovery: skip tokens until one in follow_set."""
        while (self.current.type != TokenType.EOF and
               self.current.grammar_symbol() not in follow_set):
            self.advance()

    def _cur_sym(self) -> str:
        return self.current.grammar_symbol()

    def _cur_is(self, *types) -> bool:
        return self.current.type in types

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def parse(self):
        ast = self.parse_program()
        if self.current.type != TokenType.EOF:
            self.eh.report_error(
                'SYNTAX', 'Unexpected tokens after program end',
                self.current.line, self.current.col)
        return ast

    # ------------------------------------------------------------------
    # Grammar rules
    # ------------------------------------------------------------------

    def parse_program(self):
        """Program -> DeclList"""
        line, col = self.current.line, self.current.col
        children = [self.parse_decl_list()]
        return make_node('Program', children, line=line, col=col)

    def parse_decl_list(self):
        """DeclList -> Decl DeclList | ε"""
        children = []
        # FIRST(Decl) = FIRST_RETTYPE ∪ {class, interface}
        while self.current.type in (FIRST_RETTYPE |
                                    {TokenType.KW_CLASS, TokenType.KW_INTERFACE}):
            children.append(self.parse_decl())
        return make_node('DeclList', children)

    def parse_decl(self):
        """Decl -> VarDecl | FuncDecl | ClassDecl | InterfaceDecl"""
        if self.current.type == TokenType.KW_CLASS:
            return self.parse_class_decl()
        if self.current.type == TokenType.KW_INTERFACE:
            return self.parse_interface_decl()

        # Disambiguate VarDecl vs FuncDecl:
        # RetType id ; -> VarDecl (if type followed by id followed by ;)
        # RetType id ( -> FuncDecl
        # void always -> FuncDecl
        if self.current.type == TokenType.KW_VOID:
            return self.parse_func_decl()

        # Type id ; vs Type id (
        # We need to look ahead 2 tokens: Type id [; or (]
        # After parsing Type and id, the next token decides.
        # We use a save/restore approach via lexer peeking — instead,
        # we parse RetType, then peek at what follows the id.
        # Since Type can consume multiple tokens (e.g., int[][]),
        # we speculatively parse and branch on the token after id.
        return self._parse_var_or_func_decl()

    def _parse_var_or_func_decl(self):
        """Parse VarDecl or FuncDecl by looking ahead after type+id."""
        # Save state is not straightforward; instead peek after type tokens.
        # Heuristic: after type tokens and an identifier, if '(' follows -> FuncDecl.
        # We parse Type, then id, then decide.

        line, col = self.current.line, self.current.col
        type_node = self.parse_type()
        type_str = type_node.get('value', '?')

        if self.current.type != TokenType.IDENTIFIER:
            self.eh.report_error('SYNTAX',
                f"Expected identifier after type, got '{self.current.value}'",
                self.current.line, self.current.col)
            self._sync(FOLLOW['Decl'])
            return make_node('ErrorDecl', line=line, col=col)

        id_tok = self.current
        self.advance()

        if self.current.type == TokenType.SEMICOLON:
            # VarDecl: Type id ;
            self.advance()  # consume ;
            entry = SymbolEntry(id_tok.value, 'variable', type_str,
                                self.st.scope_level, id_tok.line, id_tok.col)
            if not self.st.insert(entry):
                self.eh.report_error('SEMANTIC',
                    f"Duplicate declaration of '{id_tok.value}'",
                    id_tok.line, id_tok.col)
            return make_node('VarDecl',
                             [type_node, make_node('id', value=id_tok.value,
                                                   line=id_tok.line)],
                             value=id_tok.value, line=line, col=col)

        elif self.current.type == TokenType.LPAREN:
            # FuncDecl: RetType id ( Formals ) Block
            return self._finish_func_decl(type_node, id_tok, type_str, line, col)
        else:
            self.eh.report_error('SYNTAX',
                f"Expected ';' or '(' after '{id_tok.value}', "
                f"got '{self.current.value}'",
                self.current.line, self.current.col)
            self._sync(FOLLOW['Decl'])
            return make_node('ErrorDecl', line=line, col=col)

    def _finish_func_decl(self, type_node, id_tok, return_type, line, col):
        """Complete FuncDecl after RetType id already consumed."""
        self.match(TokenType.LPAREN)
        self.st.enter_scope(f'func_{id_tok.value}')
        formals_node = self.parse_formals()
        self.match(TokenType.RPAREN)

        # Register function in outer scope before entering body
        # Build param type list
        param_types = []
        for child in formals_node.get('children', []):
            if child and child.get('type') == 'Param':
                pt = child.get('value', 'unknown')
                param_types.append(pt)

        # Insert into symbol table (parent scope)
        # Exit current scope temporarily to insert at parent level
        current_scope_entries = {}
        # Actually insert in parent scope (level - 1)
        func_entry = SymbolEntry(id_tok.value, 'function', return_type,
                                 self.st.scope_level - 1, id_tok.line, id_tok.col)
        func_entry.attributes['return_type'] = return_type
        func_entry.attributes['param_types'] = param_types
        # Insert in the scope before current (parent scope)
        parent_scope = self.st.scopes[-2] if len(self.st.scopes) >= 2 else self.st.scopes[0]
        if id_tok.value in parent_scope:
            self.eh.report_error('SEMANTIC',
                f"Duplicate function declaration '{id_tok.value}'",
                id_tok.line, id_tok.col)
        else:
            func_entry.scope_level = self.st.scope_level - 1
            parent_scope[id_tok.value] = func_entry

        prev_ret = self._current_function_return_type
        self._current_function_return_type = return_type
        block_node = self.parse_block()
        self._current_function_return_type = prev_ret

        self.st.exit_scope()

        return make_node('FuncDecl',
                         [type_node,
                          make_node('id', value=id_tok.value, line=id_tok.line),
                          formals_node, block_node],
                         value=id_tok.value, line=line, col=col)

    def parse_var_decl(self):
        """VarDecl -> Type id ;"""
        line, col = self.current.line, self.current.col
        type_node = self.parse_type()
        type_str = type_node.get('value', '?')
        id_tok = self.match(TokenType.IDENTIFIER)
        self.match(TokenType.SEMICOLON)

        entry = SymbolEntry(id_tok.value if id_tok.value else '?',
                            'variable', type_str,
                            self.st.scope_level, id_tok.line, id_tok.col)
        if id_tok.value and not self.st.insert(entry):
            self.eh.report_error('SEMANTIC',
                f"Duplicate declaration of '{id_tok.value}'",
                id_tok.line, id_tok.col)

        return make_node('VarDecl',
                         [type_node, make_node('id', value=id_tok.value,
                                               line=id_tok.line)],
                         value=id_tok.value, line=line, col=col)

    def parse_func_decl(self):
        """FuncDecl -> RetType id ( Formals ) Block"""
        line, col = self.current.line, self.current.col
        ret_type_node = self.parse_ret_type()
        ret_type_str = ret_type_node.get('value', 'void')
        id_tok = self.match(TokenType.IDENTIFIER)
        return self._finish_func_decl(ret_type_node, id_tok, ret_type_str, line, col)

    def parse_ret_type(self):
        """RetType -> Type | void"""
        if self.current.type == TokenType.KW_VOID:
            tok = self.current
            self.advance()
            return make_node('RetType', value='void', line=tok.line, col=tok.col)
        return make_node('RetType', [self.parse_type()],
                         value=self._type_str_from_type_node(None))

    def parse_type(self):
        """Type -> (int|double|bool|string|id) TypeSuffix"""
        line, col = self.current.line, self.current.col
        base_types = {
            TokenType.KW_INT: 'int',
            TokenType.KW_DOUBLE: 'double',
            TokenType.KW_BOOL: 'bool',
            TokenType.KW_STRING: 'string',
        }
        if self.current.type in base_types:
            base = base_types[self.current.type]
            self.advance()
        elif self.current.type == TokenType.IDENTIFIER:
            base = self.current.value
            self.advance()
        else:
            self.eh.report_error('SYNTAX',
                f"Expected type, got '{self.current.value}'",
                self.current.line, self.current.col)
            self._sync(FOLLOW['Type'])
            return make_node('Type', value='error', line=line, col=col)

        suffix_node = self.parse_type_suffix()
        suffix = suffix_node.get('value', '')
        full_type = base + suffix

        return make_node('Type',
                         [make_node('BaseType', value=base), suffix_node],
                         value=full_type, line=line, col=col)

    def parse_type_suffix(self):
        """TypeSuffix -> [ ] TypeSuffix | ε"""
        if self.current.type == TokenType.LBRACKET:
            line = self.current.line
            self.advance()  # consume [
            self.match(TokenType.RBRACKET)
            inner = self.parse_type_suffix()
            inner_val = inner.get('value', '')
            return make_node('TypeSuffix', [inner],
                             value='[]' + inner_val, line=line)
        return make_node('TypeSuffix', value='')

    def _type_str_from_type_node(self, node):
        """Helper to extract type string from a Type node."""
        if node and isinstance(node, dict):
            return node.get('value', '?')
        return '?'

    def parse_formals(self):
        """Formals -> ParamList | ε"""
        if self.current.type in FIRST_TYPE:
            return make_node('Formals', [self.parse_param_list()])
        return make_node('Formals')

    def parse_param_list(self):
        """ParamList -> Param ParamTail"""
        param = self.parse_param()
        tail = self.parse_param_tail()
        return make_node('ParamList', [param] + tail.get('children', []))

    def parse_param_tail(self):
        """ParamTail -> , Param ParamTail | ε"""
        if self.current.type == TokenType.COMMA:
            self.advance()
            param = self.parse_param()
            tail = self.parse_param_tail()
            return make_node('ParamTail', [param] + tail.get('children', []))
        return make_node('ParamTail')

    def parse_param(self):
        """Param -> Type id"""
        line, col = self.current.line, self.current.col
        type_node = self.parse_type()
        type_str = type_node.get('value', '?')
        id_tok = self.match(TokenType.IDENTIFIER)

        if id_tok.value:
            entry = SymbolEntry(id_tok.value, 'parameter', type_str,
                                self.st.scope_level, id_tok.line, id_tok.col)
            if not self.st.insert(entry):
                self.eh.report_error('SEMANTIC',
                    f"Duplicate parameter '{id_tok.value}'",
                    id_tok.line, id_tok.col)

        return make_node('Param',
                         [type_node, make_node('id', value=id_tok.value)],
                         value=type_str, line=line, col=col)

    def parse_class_decl(self):
        """ClassDecl -> class id ClassBase ClassImpl { FieldList }"""
        line, col = self.current.line, self.current.col
        self.match(TokenType.KW_CLASS)
        id_tok = self.match(TokenType.IDENTIFIER)
        class_name = id_tok.value if id_tok.value else '?'

        # Insert class into symbol table
        entry = SymbolEntry(class_name, 'class', class_name,
                            self.st.scope_level, id_tok.line, id_tok.col)
        if not self.st.insert(entry):
            self.eh.report_error('SEMANTIC',
                f"Duplicate class declaration '{class_name}'",
                id_tok.line, id_tok.col)

        base_node = self.parse_class_base()
        impl_node = self.parse_class_impl()
        self.match(TokenType.LBRACE)
        self.st.enter_scope(f'class_{class_name}')
        field_node = self.parse_field_list()
        self.st.exit_scope()
        self.match(TokenType.RBRACE)

        return make_node('ClassDecl',
                         [make_node('id', value=class_name, line=id_tok.line),
                          base_node, impl_node, field_node],
                         value=class_name, line=line, col=col)

    def parse_class_base(self):
        """ClassBase -> extends id | ε"""
        if self.current.type == TokenType.KW_EXTENDS:
            self.advance()
            id_tok = self.match(TokenType.IDENTIFIER)
            return make_node('ClassBase',
                             [make_node('id', value=id_tok.value)],
                             value=id_tok.value)
        return make_node('ClassBase')

    def parse_class_impl(self):
        """ClassImpl -> implements IdentList | ε"""
        if self.current.type == TokenType.KW_IMPLEMENTS:
            self.advance()
            ident_list = self.parse_ident_list()
            return make_node('ClassImpl', [ident_list])
        return make_node('ClassImpl')

    def parse_ident_list(self):
        """IdentList -> id IdentListTail"""
        id_tok = self.match(TokenType.IDENTIFIER)
        tail = self.parse_ident_list_tail()
        names = [id_tok.value] + tail.get('value_list', [])
        return make_node('IdentList',
                         [make_node('id', value=id_tok.value)] + tail.get('children', []),
                         value=names)

    def parse_ident_list_tail(self):
        """IdentListTail -> , id IdentListTail | ε"""
        if self.current.type == TokenType.COMMA:
            self.advance()
            id_tok = self.match(TokenType.IDENTIFIER)
            tail = self.parse_ident_list_tail()
            names = [id_tok.value] + tail.get('value_list', [])
            node = make_node('IdentListTail',
                             [make_node('id', value=id_tok.value)] + tail.get('children', []))
            node['value_list'] = names
            return node
        n = make_node('IdentListTail')
        n['value_list'] = []
        return n

    def parse_field_list(self):
        """FieldList -> Field FieldList | ε"""
        children = []
        while self.current.type in (FIRST_RETTYPE | {TokenType.KW_VOID}):
            children.append(self.parse_field())
        return make_node('FieldList', children)

    def parse_field(self):
        """Field -> VarDecl | FuncDecl"""
        return self.parse_decl()

    def parse_interface_decl(self):
        """InterfaceDecl -> interface id { ProtoList }"""
        line, col = self.current.line, self.current.col
        self.match(TokenType.KW_INTERFACE)
        id_tok = self.match(TokenType.IDENTIFIER)
        iname = id_tok.value if id_tok.value else '?'

        entry = SymbolEntry(iname, 'interface', iname,
                            self.st.scope_level, id_tok.line, id_tok.col)
        if not self.st.insert(entry):
            self.eh.report_error('SEMANTIC',
                f"Duplicate interface '{iname}'", id_tok.line, id_tok.col)

        self.match(TokenType.LBRACE)
        self.st.enter_scope(f'interface_{iname}')
        proto_list = self.parse_proto_list()
        self.st.exit_scope()
        self.match(TokenType.RBRACE)

        return make_node('InterfaceDecl',
                         [make_node('id', value=iname), proto_list],
                         value=iname, line=line, col=col)

    def parse_proto_list(self):
        """ProtoList -> Proto ProtoList | ε"""
        children = []
        while self.current.type in FIRST_RETTYPE:
            children.append(self.parse_proto())
        return make_node('ProtoList', children)

    def parse_proto(self):
        """Proto -> RetType id ( Formals ) ;"""
        line, col = self.current.line, self.current.col
        ret_type = self.parse_ret_type()
        id_tok = self.match(TokenType.IDENTIFIER)
        self.match(TokenType.LPAREN)
        formals = self.parse_formals()
        self.match(TokenType.RPAREN)
        self.match(TokenType.SEMICOLON)
        return make_node('Proto',
                         [ret_type, make_node('id', value=id_tok.value), formals],
                         value=id_tok.value, line=line, col=col)

    def parse_block(self):
        """Block -> { StmtList }"""
        line, col = self.current.line, self.current.col
        self.match(TokenType.LBRACE)
        self.st.enter_scope('block')
        stmt_list = self.parse_stmt_list()
        self.st.exit_scope()
        self.match(TokenType.RBRACE)
        return make_node('Block', [stmt_list], line=line, col=col)

    def parse_stmt_list(self):
        """StmtList -> Stmt StmtList | ε"""
        children = []
        while self.current.type != TokenType.RBRACE and \
              self.current.type != TokenType.EOF:
            if self.current.type in FIRST_TYPE:
                # Could be VarDecl inside block
                children.append(self.parse_stmt())
            elif self.current.type in FIRST_STMT_NONDECL:
                children.append(self.parse_stmt())
            else:
                break
        return make_node('StmtList', children)

    def parse_stmt(self):
        """
        Stmt -> VarDecl | ExprStmt | IfStmt | WhileStmt | ForStmt
              | ReturnStmt | BreakStmt | PrintStmt | Block
        """
        t = self.current.type
        line, col = self.current.line, self.current.col

        if t in FIRST_TYPE:
            # Could be VarDecl (Type id ;) or ExprStmt starting with id
            if t == TokenType.IDENTIFIER:
                # Disambiguate: if id followed by id -> VarDecl (class type)
                # Otherwise -> ExprStmt
                # Peek: we know current is IDENTIFIER; peek next
                nxt = self.lexer.peek_token()
                if nxt.type == TokenType.IDENTIFIER:
                    # VarDecl: Type(=id) id ;
                    return self.parse_var_decl()
                else:
                    # ExprStmt starting with identifier
                    return self.parse_expr_stmt()
            else:
                # int/double/bool/string followed by something
                # Check if it could be VarDecl
                # All built-in type keywords start a VarDecl in statement context
                return self.parse_var_decl()

        if t == TokenType.KW_IF:
            return self.parse_if_stmt()
        if t == TokenType.KW_WHILE:
            return self.parse_while_stmt()
        if t == TokenType.KW_FOR:
            return self.parse_for_stmt()
        if t == TokenType.KW_RETURN:
            return self.parse_return_stmt()
        if t == TokenType.KW_BREAK:
            return self.parse_break_stmt()
        if t == TokenType.KW_PRINT:
            return self.parse_print_stmt()
        if t == TokenType.LBRACE:
            return self.parse_block()

        if t in FIRST_EXPR:
            return self.parse_expr_stmt()

        # Unknown statement
        self.eh.report_error('SYNTAX',
            f"Unexpected token '{self.current.value}' in statement",
            self.current.line, self.current.col)
        self._sync(FOLLOW['Stmt'])
        return make_node('ErrorStmt', line=line, col=col)

    def parse_expr_stmt(self):
        """ExprStmt -> Expr ;"""
        line, col = self.current.line, self.current.col
        expr = self.parse_expr()
        if self.current.type == TokenType.SEMICOLON:
            self.advance()
        else:
            self.eh.report_error('SYNTAX',
                f"Expected ';' after expression, got '{self.current.value}'",
                self.current.line, self.current.col)
        return make_node('ExprStmt', [expr], line=line, col=col)

    def parse_if_stmt(self):
        """IfStmt -> if ( Expr ) Stmt ElsePart"""
        line, col = self.current.line, self.current.col
        self.match(TokenType.KW_IF)
        self.match(TokenType.LPAREN)
        cond = self.parse_expr()
        self.match(TokenType.RPAREN)
        then_stmt = self.parse_stmt()
        else_part = self.parse_else_part()
        return make_node('IfStmt', [cond, then_stmt, else_part],
                         line=line, col=col)

    def parse_else_part(self):
        """ElsePart -> else Stmt | ε"""
        if self.current.type == TokenType.KW_ELSE:
            self.advance()
            stmt = self.parse_stmt()
            return make_node('ElsePart', [stmt])
        return make_node('ElsePart')

    def parse_while_stmt(self):
        """WhileStmt -> while ( Expr ) Stmt"""
        line, col = self.current.line, self.current.col
        self.match(TokenType.KW_WHILE)
        self.match(TokenType.LPAREN)
        cond = self.parse_expr()
        self.match(TokenType.RPAREN)
        self._in_loop += 1
        body = self.parse_stmt()
        self._in_loop -= 1
        return make_node('WhileStmt', [cond, body], line=line, col=col)

    def parse_for_stmt(self):
        """ForStmt -> for ( ForInit ; Expr ; ForUpdate ) Stmt"""
        line, col = self.current.line, self.current.col
        self.match(TokenType.KW_FOR)
        self.match(TokenType.LPAREN)
        init = self.parse_for_init()
        self.match(TokenType.SEMICOLON)
        cond = self.parse_expr()
        self.match(TokenType.SEMICOLON)
        update = self.parse_for_update()
        self.match(TokenType.RPAREN)
        self._in_loop += 1
        body = self.parse_stmt()
        self._in_loop -= 1
        return make_node('ForStmt', [init, cond, update, body],
                         line=line, col=col)

    def parse_for_init(self):
        """ForInit -> Expr | ε"""
        if self.current.type in FIRST_EXPR:
            return self.parse_expr()
        return make_node('ForInit')

    def parse_for_update(self):
        """ForUpdate -> Expr | ε"""
        if self.current.type in FIRST_EXPR:
            return self.parse_expr()
        return make_node('ForUpdate')

    def parse_return_stmt(self):
        """ReturnStmt -> return RetExprOpt ;"""
        line, col = self.current.line, self.current.col
        self.match(TokenType.KW_RETURN)
        ret_expr = self.parse_ret_expr_opt()
        self.match(TokenType.SEMICOLON)
        return make_node('ReturnStmt', [ret_expr], line=line, col=col)

    def parse_ret_expr_opt(self):
        """RetExprOpt -> Expr | ε"""
        if self.current.type in FIRST_EXPR:
            return self.parse_expr()
        return make_node('RetExprOpt')

    def parse_break_stmt(self):
        """BreakStmt -> break ;"""
        line, col = self.current.line, self.current.col
        if self._in_loop == 0:
            self.eh.report_error('SEMANTIC',
                "'break' outside of loop", line, col)
        self.match(TokenType.KW_BREAK)
        self.match(TokenType.SEMICOLON)
        return make_node('BreakStmt', line=line, col=col)

    def parse_print_stmt(self):
        """PrintStmt -> Print ( ExprList ) ;"""
        line, col = self.current.line, self.current.col
        self.match(TokenType.KW_PRINT)
        self.match(TokenType.LPAREN)
        expr_list = self.parse_expr_list()
        self.match(TokenType.RPAREN)
        self.match(TokenType.SEMICOLON)
        return make_node('PrintStmt', [expr_list], line=line, col=col)

    def parse_expr_list(self):
        """ExprList -> Expr ExprListTail"""
        expr = self.parse_expr()
        tail = self.parse_expr_list_tail()
        return make_node('ExprList', [expr] + tail.get('children', []))

    def parse_expr_list_tail(self):
        """ExprListTail -> , Expr ExprListTail | ε"""
        if self.current.type == TokenType.COMMA:
            self.advance()
            expr = self.parse_expr()
            tail = self.parse_expr_list_tail()
            return make_node('ExprListTail', [expr] + tail.get('children', []))
        return make_node('ExprListTail')

    # ------------------------------------------------------------------
    # Expression parsing (operator precedence via recursive grammar)
    # ------------------------------------------------------------------

    def parse_expr(self):
        """Expr -> OrExpr AssignTail"""
        line, col = self.current.line, self.current.col
        left = self.parse_or_expr()
        return self.parse_assign_tail(left, line, col)

    def parse_assign_tail(self, left, line, col):
        """AssignTail -> = Expr | ε"""
        if self.current.type == TokenType.ASSIGN:
            self.advance()
            right = self.parse_expr()
            return make_node('Assign', [left, right], value='=',
                             line=line, col=col)
        return left

    def parse_or_expr(self):
        """OrExpr -> AndExpr OrTail"""
        left = self.parse_and_expr()
        return self.parse_or_tail(left)

    def parse_or_tail(self, left):
        """OrTail -> || AndExpr OrTail | ε"""
        if self.current.type == TokenType.OR:
            op = self.current
            self.advance()
            right = self.parse_and_expr()
            node = make_node('BinOp', [left, right], value='||',
                             line=op.line, col=op.col)
            return self.parse_or_tail(node)
        return left

    def parse_and_expr(self):
        """AndExpr -> EqExpr AndTail"""
        left = self.parse_eq_expr()
        return self.parse_and_tail(left)

    def parse_and_tail(self, left):
        """AndTail -> && EqExpr AndTail | ε"""
        if self.current.type == TokenType.AND:
            op = self.current
            self.advance()
            right = self.parse_eq_expr()
            node = make_node('BinOp', [left, right], value='&&',
                             line=op.line, col=op.col)
            return self.parse_and_tail(node)
        return left

    def parse_eq_expr(self):
        """EqExpr -> RelExpr EqTail"""
        left = self.parse_rel_expr()
        return self.parse_eq_tail(left)

    def parse_eq_tail(self, left):
        """EqTail -> == RelExpr | != RelExpr | ε"""
        if self.current.type == TokenType.EQ:
            op = self.current
            self.advance()
            right = self.parse_rel_expr()
            return make_node('BinOp', [left, right], value='==',
                             line=op.line, col=op.col)
        if self.current.type == TokenType.NEQ:
            op = self.current
            self.advance()
            right = self.parse_rel_expr()
            return make_node('BinOp', [left, right], value='!=',
                             line=op.line, col=op.col)
        return left

    def parse_rel_expr(self):
        """RelExpr -> AddExpr RelTail"""
        left = self.parse_add_expr()
        return self.parse_rel_tail(left)

    def parse_rel_tail(self, left):
        """RelTail -> < | <= | > | >= AddExpr | ε"""
        ops = {
            TokenType.LT: '<', TokenType.LE: '<=',
            TokenType.GT: '>', TokenType.GE: '>=',
        }
        if self.current.type in ops:
            op_val = ops[self.current.type]
            op = self.current
            self.advance()
            right = self.parse_add_expr()
            return make_node('BinOp', [left, right], value=op_val,
                             line=op.line, col=op.col)
        return left

    def parse_add_expr(self):
        """AddExpr -> MulExpr AddTail"""
        left = self.parse_mul_expr()
        return self.parse_add_tail(left)

    def parse_add_tail(self, left):
        """AddTail -> + MulExpr AddTail | - MulExpr AddTail | ε"""
        if self.current.type == TokenType.PLUS:
            op = self.current
            self.advance()
            right = self.parse_mul_expr()
            node = make_node('BinOp', [left, right], value='+',
                             line=op.line, col=op.col)
            return self.parse_add_tail(node)
        if self.current.type == TokenType.MINUS:
            op = self.current
            self.advance()
            right = self.parse_mul_expr()
            node = make_node('BinOp', [left, right], value='-',
                             line=op.line, col=op.col)
            return self.parse_add_tail(node)
        return left

    def parse_mul_expr(self):
        """MulExpr -> UnaryExpr MulTail"""
        left = self.parse_unary_expr()
        return self.parse_mul_tail(left)

    def parse_mul_tail(self, left):
        """MulTail -> * | / | % UnaryExpr MulTail | ε"""
        ops = {
            TokenType.STAR: '*', TokenType.SLASH: '/',
            TokenType.PERCENT: '%',
        }
        if self.current.type in ops:
            op_val = ops[self.current.type]
            op = self.current
            self.advance()
            right = self.parse_unary_expr()
            node = make_node('BinOp', [left, right], value=op_val,
                             line=op.line, col=op.col)
            return self.parse_mul_tail(node)
        return left

    def parse_unary_expr(self):
        """UnaryExpr -> ! UnaryExpr | - UnaryExpr | PostExpr"""
        if self.current.type == TokenType.NOT:
            op = self.current
            self.advance()
            operand = self.parse_unary_expr()
            return make_node('UnaryOp', [operand], value='!',
                             line=op.line, col=op.col)
        if self.current.type == TokenType.MINUS:
            op = self.current
            self.advance()
            operand = self.parse_unary_expr()
            return make_node('UnaryOp', [operand], value='-',
                             line=op.line, col=op.col)
        return self.parse_post_expr()

    def parse_post_expr(self):
        """PostExpr -> Primary PostTail"""
        primary = self.parse_primary()
        return self.parse_post_tail(primary)

    def parse_post_tail(self, left):
        """PostTail -> [ Expr ] PostTail | . id CallTail PostTail | ε"""
        if self.current.type == TokenType.LBRACKET:
            op = self.current
            self.advance()
            idx = self.parse_expr()
            self.match(TokenType.RBRACKET)
            node = make_node('IndexOp', [left, idx], value='[]',
                             line=op.line, col=op.col)
            return self.parse_post_tail(node)

        if self.current.type == TokenType.DOT:
            op = self.current
            self.advance()
            id_tok = self.match(TokenType.IDENTIFIER)
            call = self.parse_call_tail(id_tok)
            node = make_node('FieldAccess', [left, call],
                             value=id_tok.value, line=op.line, col=op.col)
            return self.parse_post_tail(node)

        return left

    def parse_call_tail(self, id_tok=None):
        """CallTail -> ( ActualList ) | ε"""
        if self.current.type == TokenType.LPAREN:
            line = self.current.line
            self.advance()
            args = self.parse_actual_list()
            self.match(TokenType.RPAREN)
            name = id_tok.value if id_tok else '?'
            return make_node('Call', [args], value=name, line=line)
        # Return id node without call
        if id_tok:
            return make_node('id', value=id_tok.value,
                             line=id_tok.line, col=id_tok.col)
        return make_node('NoCall')

    def parse_primary(self):
        """
        Primary -> id CallTail | INT_CONST | DOUBLE_CONST | BOOL_CONST
                 | STRING_CONST | null | this | ( Expr )
                 | ReadInteger ( ) | ReadLine ( )
                 | New ( id ) | NewArray ( Expr , Type )
        """
        line, col = self.current.line, self.current.col
        t = self.current.type

        if t == TokenType.IDENTIFIER:
            id_tok = self.current
            self.advance()
            call = self.parse_call_tail(id_tok)
            # If call_tail returned a Call node, wrap; else return id/call
            if call.get('type') == 'Call':
                call['value'] = id_tok.value
                return call
            return make_node('Var', value=id_tok.value,
                             line=line, col=col)

        if t == TokenType.INT_CONST:
            val = self.current.value
            self.advance()
            return make_node('IntLit', value=val, line=line, col=col)

        if t == TokenType.DOUBLE_CONST:
            val = self.current.value
            self.advance()
            return make_node('DoubleLit', value=val, line=line, col=col)

        if t == TokenType.BOOL_CONST:
            val = self.current.value
            self.advance()
            return make_node('BoolLit', value=val, line=line, col=col)

        if t == TokenType.STRING_CONST:
            val = self.current.value
            self.advance()
            return make_node('StringLit', value=val, line=line, col=col)

        if t == TokenType.KW_NULL:
            self.advance()
            return make_node('Null', value='null', line=line, col=col)

        if t == TokenType.KW_THIS:
            self.advance()
            return make_node('This', value='this', line=line, col=col)

        if t == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.match(TokenType.RPAREN)
            return make_node('Paren', [expr], line=line, col=col)

        if t == TokenType.KW_READINTEGER:
            self.advance()
            self.match(TokenType.LPAREN)
            self.match(TokenType.RPAREN)
            return make_node('ReadInteger', line=line, col=col)

        if t == TokenType.KW_READLINE:
            self.advance()
            self.match(TokenType.LPAREN)
            self.match(TokenType.RPAREN)
            return make_node('ReadLine', line=line, col=col)

        if t == TokenType.KW_NEW:
            self.advance()
            self.match(TokenType.LPAREN)
            id_tok = self.match(TokenType.IDENTIFIER)
            self.match(TokenType.RPAREN)
            return make_node('New', value=id_tok.value, line=line, col=col)

        if t == TokenType.KW_NEWARRAY:
            self.advance()
            self.match(TokenType.LPAREN)
            size_expr = self.parse_expr()
            self.match(TokenType.COMMA)
            elem_type = self.parse_type()
            self.match(TokenType.RPAREN)
            return make_node('NewArray', [size_expr, elem_type],
                             value=elem_type.get('value', '?'),
                             line=line, col=col)

        # Error
        self.eh.report_error('SYNTAX',
            f"Unexpected token '{self.current.value}' in expression",
            self.current.line, self.current.col)
        self._sync(FOLLOW['Primary'])
        return make_node('ErrorExpr', line=line, col=col)

    def parse_actual_list(self):
        """ActualList -> Expr ExprListTail | ε"""
        if self.current.type in FIRST_EXPR:
            expr = self.parse_expr()
            tail = self.parse_expr_list_tail()
            return make_node('ActualList', [expr] + tail.get('children', []))
        return make_node('ActualList')
