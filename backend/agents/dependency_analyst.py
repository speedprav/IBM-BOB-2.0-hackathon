"""
Dependency Analyst — identifies changed symbols and their blast radius.
Pure deterministic logic; no LLM calls.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set
from analysis.graph import DependencyGraph, compute_impact, GraphNode


@dataclass
class DependencyAnalysisResult:
    changed_files: List[str]
    changed_symbol_names: List[str]
    changed_node_ids: List[str]
    direct_impact_node_ids: List[str]
    indirect_impact_node_ids: List[str]
    affected_files: List[str]
    affected_symbols: List[str]
    blast_radius_summary: str


def analyze_dependencies(
    graph: DependencyGraph,
    changed_files: List[str],
    changed_symbol_names: List[str],
) -> DependencyAnalysisResult:
    """
    Given the dependency graph and the set of changed files/symbols,
    compute the full blast radius.
    """
    # Resolve changed node IDs
    changed_node_ids: List[str] = []

    # Include file nodes for changed files
    for cf in changed_files:
        file_id = f"file::{cf}"
        if file_id in graph.nodes:
            changed_node_ids.append(file_id)

    # Include symbol nodes for changed symbols
    for sym_name in changed_symbol_names:
        sym_id = graph.symbol_index.get(sym_name)
        if sym_id and sym_id not in changed_node_ids:
            changed_node_ids.append(sym_id)

    # Compute blast radius
    direct_set, indirect_set = compute_impact(graph, changed_node_ids)

    # Collect affected files
    affected_files: Set[str] = set()
    affected_symbols: List[str] = []

    for node_id in list(direct_set) + list(indirect_set):
        node = graph.nodes.get(node_id)
        if node:
            affected_files.add(node.file_path)
            if node.node_type in ('function', 'method', 'class'):
                affected_symbols.append(node.label)

    summary = (
        f"{len(changed_files)} file(s) changed, "
        f"{len(changed_symbol_names)} symbol(s) modified. "
        f"Direct impact: {len(direct_set)} node(s) in {len(affected_files)} file(s). "
        f"Indirect impact: {len(indirect_set)} additional node(s)."
    )

    return DependencyAnalysisResult(
        changed_files=changed_files,
        changed_symbol_names=changed_symbol_names,
        changed_node_ids=changed_node_ids,
        direct_impact_node_ids=list(direct_set),
        indirect_impact_node_ids=list(indirect_set),
        affected_files=list(affected_files),
        affected_symbols=affected_symbols,
        blast_radius_summary=summary,
    )
