"""
Dependency / reference graph construction — deterministic graph traversal.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from analysis.scanner import ScanResult
from analysis.extractor import Symbol, extract_symbols


@dataclass
class GraphNode:
    id: str
    label: str
    node_type: str       # file | class | function | method
    file_path: str
    symbol: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    edge_type: str       # calls | imports | contains
    label: Optional[str] = None


@dataclass
class DependencyGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    # symbol_name → node_id  (for quick lookup)
    symbol_index: Dict[str, str] = field(default_factory=dict)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        # Deduplicate
        key = (edge.source, edge.target, edge.edge_type)
        if not any((e.source, e.target, e.edge_type) == key for e in self.edges):
            self.edges.append(edge)

    def get_callers(self, node_id: str) -> List[str]:
        """Return IDs of nodes that call/import this node."""
        return [e.source for e in self.edges if e.target == node_id]

    def get_callees(self, node_id: str) -> List[str]:
        """Return IDs of nodes called/imported by this node."""
        return [e.target for e in self.edges if e.source == node_id]

    def reachable_from(self, node_ids: List[str], direction: str = 'callers') -> Set[str]:
        """BFS: collect all nodes reachable from seed via callers or callees."""
        visited: Set[str] = set()
        queue = list(node_ids)
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            if direction == 'callers':
                neighbours = self.get_callers(current)
            else:
                neighbours = self.get_callees(current)
            for n in neighbours:
                if n not in visited:
                    queue.append(n)
        return visited


def build_dependency_graph(scan_result: ScanResult) -> Tuple[DependencyGraph, Dict[str, List[Symbol]]]:
    """
    Build a deterministic dependency graph from a scan result.
    Returns (graph, file_symbols_map).
    """
    graph = DependencyGraph()
    file_symbols: Dict[str, List[Symbol]] = {}

    # Pass 1: create all nodes
    for scanned_file in scan_result.files:
        if scanned_file.language != 'python':
            continue

        # File node
        file_id = f"file::{scanned_file.path}"
        graph.add_node(GraphNode(
            id=file_id,
            label=scanned_file.path.split('/')[-1],
            node_type='file',
            file_path=scanned_file.path,
            metadata={'full_path': scanned_file.path, 'lines': scanned_file.lines},
        ))

        symbols = extract_symbols(scanned_file.path, scanned_file.content)
        file_symbols[scanned_file.path] = symbols

        for sym in symbols:
            if sym.kind == 'import':
                continue
            sym_id = _symbol_id(sym)
            graph.add_node(GraphNode(
                id=sym_id,
                label=sym.name,
                node_type=sym.kind,
                file_path=scanned_file.path,
                symbol=sym.name,
                metadata={'line': sym.line, 'parent': sym.parent},
            ))
            graph.symbol_index[sym.name] = sym_id
            # file contains symbol
            graph.add_edge(GraphEdge(
                source=file_id,
                target=sym_id,
                edge_type='contains',
            ))
            # class contains method
            if sym.kind == 'method' and sym.parent:
                parent_id = f"class::{scanned_file.path}::{sym.parent}"
                if parent_id in graph.nodes:
                    graph.add_edge(GraphEdge(
                        source=parent_id,
                        target=sym_id,
                        edge_type='contains',
                    ))

    # Pass 2: resolve call edges
    for scanned_file in scan_result.files:
        if scanned_file.language != 'python':
            continue
        symbols = file_symbols.get(scanned_file.path, [])
        for sym in symbols:
            if sym.kind not in ('function', 'method'):
                continue
            caller_id = _symbol_id(sym)
            for call_name in sym.calls:
                target_id = graph.symbol_index.get(call_name)
                if target_id and target_id != caller_id:
                    graph.add_edge(GraphEdge(
                        source=caller_id,
                        target=target_id,
                        edge_type='calls',
                        label=f"calls {call_name}",
                    ))

    # Pass 3: resolve import edges (file → file)
    for scanned_file in scan_result.files:
        if scanned_file.language != 'python':
            continue
        symbols = file_symbols.get(scanned_file.path, [])
        file_id = f"file::{scanned_file.path}"
        for sym in symbols:
            if sym.kind != 'import':
                continue
            for imported in sym.imports:
                # Map module name to file
                candidate = _module_to_file(imported, scan_result)
                if candidate:
                    target_file_id = f"file::{candidate}"
                    if target_file_id in graph.nodes:
                        graph.add_edge(GraphEdge(
                            source=file_id,
                            target=target_file_id,
                            edge_type='imports',
                            label=f"imports {imported}",
                        ))

    return graph, file_symbols


def compute_impact(
    graph: DependencyGraph,
    changed_node_ids: List[str],
) -> Tuple[Set[str], Set[str]]:
    """
    Given a set of changed node IDs, compute direct and indirect impact sets.
    Returns (direct_impact, indirect_impact).
    """
    direct: Set[str] = set()
    for node_id in changed_node_ids:
        direct.update(graph.get_callers(node_id))
    direct -= set(changed_node_ids)

    # Indirect = everything reachable from direct, excluding changed and direct
    all_reachable = graph.reachable_from(list(direct), direction='callers')
    indirect = all_reachable - direct - set(changed_node_ids)

    return direct, indirect


def _symbol_id(sym: Symbol) -> str:
    if sym.kind == 'class':
        return f"class::{sym.file_path}::{sym.name}"
    if sym.parent:
        return f"method::{sym.file_path}::{sym.parent}.{sym.name}"
    return f"function::{sym.file_path}::{sym.name}"


def _module_to_file(module_name: str, scan_result: ScanResult) -> Optional[str]:
    """Best-effort mapping: 'services.order_service' → 'services/order_service.py'"""
    candidate = module_name.replace('.', '/') + '.py'
    for f in scan_result.files:
        if f.path == candidate or f.path.endswith('/' + candidate):
            return f.path
    # Also try just the last segment
    short = module_name.split('.')[-1] + '.py'
    for f in scan_result.files:
        if f.path.endswith(short):
            return f.path
    return None
