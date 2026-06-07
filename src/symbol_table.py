"""
symbol_table.py - Symbol Table Manager for the Decaf mini-compiler.

Implements a scoped symbol table with polynomial rolling hash for efficient
symbol lookup. Supports nested scopes for class bodies, function bodies, etc.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


class SymbolEntry:
    """
    A single entry in the symbol table.

    Attributes:
        name       : identifier name
        kind       : 'variable', 'constant', 'function', 'array',
                     'class', 'interface', 'parameter'
        type_      : type string, e.g., 'int', 'double', 'bool[]', 'MyClass'
        scope_level: nesting depth (0 = global)
        line       : source line number where declared
        col        : source column number where declared
        attributes : dict for extra info (return_type, param_types, etc.)
    """

    def __init__(self, name, kind, type_, scope_level, line, col=0):
        self.name = name
        self.kind = kind
        self.type_ = type_
        self.scope_level = scope_level
        self.line = line
        self.col = col
        self.attributes = {}

    def __repr__(self):
        return (f"SymbolEntry(name={self.name!r}, kind={self.kind!r}, "
                f"type={self.type_!r}, scope={self.scope_level}, "
                f"line={self.line}, col={self.col})")


class SymbolTable:
    """
    Scoped symbol table using a stack of hash-table scopes.

    Uses a prime-sized hash table conceptually, but backed by Python dicts
    for ease. The polynomial rolling hash is exposed via _hash() for
    educational demonstration.
    """

    HASH_SIZE = 211  # prime number for hash table buckets

    def __init__(self):
        self.scopes = []        # stack of dicts (innermost last)
        self.scope_level = 0
        self.global_scope = {}
        self.scopes.append(self.global_scope)
        # Track scope names for pretty printing
        self._scope_names = ['global']

    def _hash(self, name: str) -> int:
        """Polynomial rolling hash: h = sum(c * 31^i) mod HASH_SIZE."""
        h = 0
        for c in name:
            h = (h * 31 + ord(c)) % self.HASH_SIZE
        return h

    def enter_scope(self, name: str = None):
        """Open a new nested scope."""
        self.scope_level += 1
        self.scopes.append({})
        label = name if name else f'scope_{self.scope_level}'
        self._scope_names.append(label)

    def exit_scope(self):
        """Close the current innermost scope."""
        if self.scope_level > 0:
            self.scopes.pop()
            self._scope_names.pop()
            self.scope_level -= 1

    def insert(self, entry: SymbolEntry) -> bool:
        """
        Insert entry into the current (innermost) scope.
        Returns False if name already exists in current scope (duplicate).
        """
        current = self.scopes[-1]
        if entry.name in current:
            return False  # duplicate in current scope
        entry.scope_level = self.scope_level
        current[entry.name] = entry
        return True

    def lookup(self, name: str):
        """
        Search for name from innermost to outermost scope.
        Returns SymbolEntry or None.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_current_scope(self, name: str):
        """Look up name only in the current (innermost) scope."""
        return self.scopes[-1].get(name)

    def lookup_global(self, name: str):
        """Look up name only in global scope."""
        return self.global_scope.get(name)

    def delete(self, name: str) -> bool:
        """Delete name from the first scope it appears in (innermost first)."""
        for scope in reversed(self.scopes):
            if name in scope:
                del scope[name]
                return True
        return False

    def current_scope_level(self) -> int:
        return self.scope_level

    def dump(self, title: str = "Symbol Table"):
        """Pretty-print all entries across all scopes."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"  (Scopes: {self.scope_level + 1}, Hash size: {self.HASH_SIZE})")
        print('='*60)

        for level, (scope, sname) in enumerate(zip(self.scopes, self._scope_names)):
            if not scope:
                continue
            print(f"\n  Scope {level} [{sname}]:")
            print(f"  {'Name':<20} {'Kind':<12} {'Type':<20} {'Line':<6} {'Hash':<6}")
            print(f"  {'-'*20} {'-'*12} {'-'*20} {'-'*6} {'-'*6}")
            for name, entry in sorted(scope.items()):
                h = self._hash(name)
                print(f"  {name:<20} {entry.kind:<12} {entry.type_:<20} "
                      f"{entry.line:<6} {h:<6}")
                if entry.attributes:
                    for k, v in entry.attributes.items():
                        print(f"    .{k} = {v}")

        total = sum(len(s) for s in self.scopes)
        print(f"\n  Total entries: {total}")
        print('='*60)

    def dump_to_string(self, title: str = "Symbol Table") -> str:
        """Return symbol table dump as a string."""
        lines = []
        lines.append('='*60)
        lines.append(f'  {title}')
        lines.append(f'  (Scopes: {self.scope_level + 1}, Hash size: {self.HASH_SIZE})')
        lines.append('='*60)

        for level, (scope, sname) in enumerate(zip(self.scopes, self._scope_names)):
            if not scope:
                continue
            lines.append(f'\n  Scope {level} [{sname}]:')
            lines.append(f"  {'Name':<20} {'Kind':<12} {'Type':<20} {'Line':<6}")
            lines.append(f"  {'-'*20} {'-'*12} {'-'*20} {'-'*6}")
            for name, entry in sorted(scope.items()):
                lines.append(f"  {name:<20} {entry.kind:<12} {entry.type_:<20} {entry.line:<6}")

        total = sum(len(s) for s in self.scopes)
        lines.append(f'\n  Total entries: {total}')
        lines.append('='*60)
        return '\n'.join(lines)
