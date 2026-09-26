import React, { useEffect, useRef, useState } from 'react';
import { DependencyGraph, GraphNode } from '../types/api';

interface Props {
  graph: DependencyGraph;
}

interface NodeDetail {
  node: GraphNode;
  x: number;
  y: number;
}

export default function BlastRadiusGraph({ graph }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<NodeDetail | null>(null);
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});

  // Only show meaningful nodes (not file-container nodes for clarity)
  const visibleNodes = graph.nodes.filter(n =>
    n.type !== 'file' || n.is_changed || n.is_directly_impacted || n.is_indirectly_impacted
  );
  const nodeIds = new Set(visibleNodes.map(n => n.id));
  const visibleEdges = graph.edges.filter(
    e => nodeIds.has(e.source) && nodeIds.has(e.target) && e.type !== 'references'
  );

  useEffect(() => {
    if (visibleNodes.length === 0) return;
    const newPos: Record<string, { x: number; y: number }> = {};
    const W = 700, H = 400, CX = W / 2, CY = H / 2;

    // Layout: changed nodes center, direct inner ring, indirect outer ring, others edge
    const changed = visibleNodes.filter(n => n.is_changed);
    const direct = visibleNodes.filter(n => n.is_directly_impacted && !n.is_changed);
    const indirect = visibleNodes.filter(n => n.is_indirectly_impacted && !n.is_changed && !n.is_directly_impacted);
    const other = visibleNodes.filter(n => !n.is_changed && !n.is_directly_impacted && !n.is_indirectly_impacted);

    // Center changed nodes
    changed.forEach((n, i) => {
      const angle = (i / Math.max(changed.length, 1)) * 2 * Math.PI;
      newPos[n.id] = { x: CX + Math.cos(angle) * (changed.length > 1 ? 60 : 0), y: CY + Math.sin(angle) * (changed.length > 1 ? 60 : 0) };
    });
    // Inner ring: direct
    direct.forEach((n, i) => {
      const angle = (i / Math.max(direct.length, 1)) * 2 * Math.PI;
      newPos[n.id] = { x: CX + Math.cos(angle) * 130, y: CY + Math.sin(angle) * 130 };
    });
    // Outer ring: indirect
    indirect.forEach((n, i) => {
      const angle = (i / Math.max(indirect.length, 1)) * 2 * Math.PI - 0.3;
      newPos[n.id] = { x: CX + Math.cos(angle) * 230, y: CY + Math.sin(angle) * 190 };
    });
    // Edge: others
    other.forEach((n, i) => {
      const angle = (i / Math.max(other.length, 1)) * 2 * Math.PI + 0.5;
      newPos[n.id] = { x: CX + Math.cos(angle) * 310, y: CY + Math.sin(angle) * 260 };
    });
    setPositions(newPos);
  }, [graph]);

  if (visibleNodes.length === 0) {
    return (
      <div className="graph-empty">
        <p className="text-muted">No dependency graph data available.</p>
      </div>
    );
  }

  const getNodeColor = (n: GraphNode) => {
    if (n.is_changed) return '#ff6e6e';
    if (n.is_directly_impacted) return '#ff9966';
    if (n.is_indirectly_impacted) return '#d29922';
    return '#30363d';
  };

  const getNodeRadius = (n: GraphNode) => {
    if (n.is_changed) return 22;
    if (n.is_directly_impacted) return 17;
    if (n.is_indirectly_impacted) return 14;
    return 11;
  };

  const handleNodeClick = (node: GraphNode, e: React.MouseEvent<SVGCircleElement>) => {
    const pos = positions[node.id];
    if (!pos) return;
    setSelectedNode(selectedNode?.node.id === node.id ? null : { node, x: pos.x, y: pos.y });
  };

  return (
    <div className="graph-container">
      <svg ref={svgRef} viewBox="0 0 700 400" className="graph-svg">
        <defs>
          <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="var(--border)" />
          </marker>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Legend */}
        <g transform="translate(8,8)">
          {[
            { color: '#ff6e6e', label: 'Changed' },
            { color: '#ff9966', label: 'Direct impact' },
            { color: '#d29922', label: 'Indirect impact' },
          ].map((l, i) => (
            <g key={l.label} transform={`translate(0,${i * 18})`}>
              <circle cx="6" cy="6" r="5" fill={l.color} />
              <text x="16" y="10" fontSize="10" fill="var(--text-muted)">{l.label}</text>
            </g>
          ))}
        </g>

        {/* Edges */}
        {visibleEdges.map((edge, i) => {
          const sp = positions[edge.source];
          const tp = positions[edge.target];
          if (!sp || !tp) return null;
          const dx = tp.x - sp.x, dy = tp.y - sp.y;
          const len = Math.sqrt(dx * dx + dy * dy);
          if (len < 1) return null;
          const targetNode = visibleNodes.find(n => n.id === edge.target);
          const r = targetNode ? getNodeRadius(targetNode) + 3 : 14;
          const ex = tp.x - (dx / len) * r;
          const ey = tp.y - (dy / len) * r;
          return (
            <line
              key={i}
              x1={sp.x} y1={sp.y} x2={ex} y2={ey}
              stroke="var(--border)" strokeWidth="1.5"
              markerEnd="url(#arrow)"
              opacity={0.6}
            />
          );
        })}

        {/* Nodes */}
        {visibleNodes.map(node => {
          const pos = positions[node.id];
          if (!pos) return null;
          const r = getNodeRadius(node);
          const color = getNodeColor(node);
          const isSelected = selectedNode?.node.id === node.id;
          return (
            <g key={node.id} transform={`translate(${pos.x},${pos.y})`}>
              <circle
                r={r}
                fill={color}
                fillOpacity={isSelected ? 1 : 0.85}
                stroke={isSelected ? '#fff' : color}
                strokeWidth={isSelected ? 2 : 1}
                filter={node.is_changed ? 'url(#glow)' : undefined}
                style={{ cursor: 'pointer' }}
                onClick={(e) => handleNodeClick(node, e)}
              />
              <text
                textAnchor="middle"
                dy="0.35em"
                fontSize={node.is_changed ? 9 : 8}
                fill="#fff"
                pointerEvents="none"
                style={{ userSelect: 'none' }}
              >
                {node.label.length > 10 ? node.label.slice(0, 9) + '…' : node.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Node detail popover */}
      {selectedNode && (
        <div className="node-detail">
          <div className="node-detail-header">
            <span className={`badge badge-${selectedNode.node.is_changed ? 'critical' : selectedNode.node.is_directly_impacted ? 'high' : 'medium'}`}>
              {selectedNode.node.is_changed ? 'CHANGED' : selectedNode.node.is_directly_impacted ? 'DIRECT IMPACT' : 'INDIRECT IMPACT'}
            </span>
            <button className="close-btn" onClick={() => setSelectedNode(null)}>✕</button>
          </div>
          <div className="node-detail-name">{selectedNode.node.label}</div>
          <div className="node-detail-row">
            <span className="text-muted text-small">Type:</span>
            <span className="text-small">{selectedNode.node.type}</span>
          </div>
          <div className="node-detail-row">
            <span className="text-muted text-small">File:</span>
            <code className="text-small text-mono">{selectedNode.node.file_path}</code>
          </div>
          {selectedNode.node.metadata?.line !== undefined && (
            <div className="node-detail-row">
              <span className="text-muted text-small">Line:</span>
              <span className="text-small">{String(selectedNode.node.metadata.line as number)}</span>
            </div>
          )}
        </div>
      )}

      <style>{styles}</style>
    </div>
  );
}

const styles = `
.graph-container { position: relative; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; }
.graph-svg { width: 100%; height: auto; display: block; }
.graph-empty { padding: 40px; text-align: center; }
.node-detail {
  position: absolute; bottom: 12px; left: 12px;
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px 14px; min-width: 200px; max-width: 280px;
}
.node-detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.node-detail-name { font-weight: 600; margin-bottom: 8px; font-family: var(--mono); font-size: 13px; color: var(--text); }
.node-detail-row { display: flex; gap: 8px; align-items: baseline; margin-bottom: 4px; }
.close-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 14px; padding: 0; }
.close-btn:hover { color: var(--text); }
`;
