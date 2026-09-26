"""
Symbol extractor — deterministic AST-based symbol extraction for Python.
"""
from __future__ import annotations
import ast
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Symbol:
    name: str
    kind: str          # 'function' | 'class' | 'method' | 'import'
    file_path: str
    line: int
    parent: Optional[str] = None   # class name for methods
    calls: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


class _SymbolVisitor(ast.NodeVisitor):
    """Walk an AST and collect symbols + call/import relationships."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.symbols: List[Symbol] = []
        self._current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.symbols.append(Symbol(
            name=node.name,
            kind='class',
            file_path=self.file_path,
            line=node.lineno,
        ))
        prev = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = prev

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_func(node)

    def _handle_func(self, node) -> None:
        kind = 'method' if self._current_class else 'function'
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = _extract_call_name(child)
                if name:
                    calls.append(name)
        sym = Symbol(
            name=node.name,
            kind=kind,
            file_path=self.file_path,
            line=node.lineno,
            parent=self._current_class,
            calls=calls,
        )
        self.symbols.append(sym)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.symbols.append(Symbol(
                name=alias.asname or alias.name,
                kind='import',
                file_path=self.file_path,
                line=node.lineno,
                imports=[alias.name],
            ))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ''
        for alias in node.names:
            imported_name = f"{module}.{alias.name}" if module else alias.name
            self.symbols.append(Symbol(
                name=alias.asname or alias.name,
                kind='import',
                file_path=self.file_path,
                line=node.lineno,
                imports=[imported_name],
            ))


def extract_symbols(file_path: str, content: str) -> List[Symbol]:
    """Parse a Python file and extract all symbols."""
    try:
        tree = ast.parse(content, filename=file_path)
    except SyntaxError:
        return []
    visitor = _SymbolVisitor(file_path)
    visitor.visit(tree)
    return visitor.symbols


def _extract_call_name(node: ast.Call) -> Optional[str]:
    """Best-effort extraction of the callable name from a Call node."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None
