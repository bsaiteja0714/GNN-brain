/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useMemo, useState, useRef, useEffect } from "react";
import * as THREE from "three";
// @ts-ignore
import ForceGraph3D from "react-force-graph-3d";
import "./App.css";
import ChatPanel from "./ChatPanel";

// ── Types ────────────────────────────────────────────────────────────────────

type NodeRole =
  | "Student"
  | "CR"
  | "Teacher"
  | "HOD"
  | "Dean"
  | "Admin"
  | "project"
  | "Other";

type BrainNode = {
  id: string;
  label: string;
  cluster: number;
  text: string;
  role: NodeRole;
  section?: "A" | "B" | "C";
  importance: number;
};

type BrainLink = { source: string; target: string };
type BrainGraph = { nodes: BrainNode[]; links: BrainLink[] };

// ── Constants ─────────────────────────────────────────────────────────────────

const BACKEND_URL = "/api";

const NODE_COLORS: Record<number, string> = {
  0: "#22c55e", // Section A  — green
  1: "#f97316", // Section B  — orange
  2: "#6366f1", // Section C  — indigo
  3: "#eab308", // HOD        — yellow
  4: "#ef4444", // Dean       — red
  5: "#0ea5e9", // Admin      — sky blue
  6: "#ec4899", // Project    — pink
  7: "#a855f7", // Other      — purple
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function clusterFor(role: string, section?: string): number {
  if (section === "A") return 0;
  if (section === "B") return 1;
  if (section === "C") return 2;
  if (role === "HOD") return 3;
  if (role === "Dean") return 4;
  if (role === "Admin") return 5;
  if (role === "project") return 6;
  return 7;
}

function mapRole(raw: string): NodeRole {
  const allowed: NodeRole[] = [
    "Student", "CR", "Teacher", "HOD", "Dean", "Admin", "project",
  ];
  return allowed.includes(raw as NodeRole) ? (raw as NodeRole) : "Other";
}

// ── App ───────────────────────────────────────────────────────────────────────

const App: React.FC = () => {
  const [graphData, setGraphData] = useState<BrainGraph>({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState<BrainNode | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [graphLoading, setGraphLoading] = useState(true);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState<Set<string>>(new Set());
  const [highlightedLinkKeys, setHighlightedLinkKeys] = useState<Set<string>>(new Set());

  const fgRef = useRef<any>();

  // Reusable arrow geometry
  const { arrowGeom, arrowMat } = useMemo(() => ({
    arrowGeom: new THREE.ConeGeometry(1, 2, 8),
    arrowMat: new THREE.MeshStandardMaterial({ color: 0xff6600 }),
  }), []);

  // Quick id → node map
  const nodeById = useMemo(() => {
    const m: Record<string, BrainNode> = {};
    graphData.nodes.forEach((n) => (m[n.id] = n));
    return m;
  }, [graphData.nodes]);

  // Neighbours of selected node
  const neighborIds = useMemo(() => {
    if (!selectedNode) return new Set<string>();
    const s = new Set<string>();
    graphData.links.forEach((l) => {
      const src = l.source as string;
      const tgt = l.target as string;
      if (src === selectedNode.id) s.add(tgt);
      if (tgt === selectedNode.id) s.add(src);
    });
    return s;
  }, [selectedNode, graphData.links]);

  // ── Fetch graph from backend ───────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      setGraphLoading(true);
      try {
        const res = await fetch(`${BACKEND_URL}/graph`);
        if (!res.ok) throw new Error("not-ok");
        const data = await res.json();

        const mappedNodes: BrainNode[] = (data.nodes ?? []).map((n: any) => {
          const section = n.section as "A" | "B" | "C" | undefined;
          return {
            id: n.id,
            label: n.label ?? n.id,
            cluster: clusterFor(n.role ?? "Other", section),
            text: n.text ?? "",
            role: mapRole(n.role ?? "Other"),
            section,
            importance: n.importance ?? 1,
          };
        });

        const mappedLinks: BrainLink[] = (data.links ?? []).map((l: any) => ({
          source: l.source,
          target: l.target,
        }));

        setGraphData({ nodes: mappedNodes, links: mappedLinks });
        setBackendConnected(true);
      } catch {
        setBackendConnected(false);
      } finally {
        setGraphLoading(false);
      }
    })();
  }, []);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleNodeClick = (node: any) => {
    const n = node as BrainNode;
    setSelectedNode(n);
    setHighlightedNodeIds(new Set());
    setHighlightedLinkKeys(new Set());

    if (fgRef.current && node.x !== undefined) {
      const distance = 120;
      const distRatio =
        1 + distance / Math.hypot(node.x || 1, node.y || 1, node.z || 1);
      fgRef.current.cameraPosition(
        { x: (node.x || 0) * distRatio, y: (node.y || 0) * distRatio, z: (node.z || 0) * distRatio },
        node,
        1000
      );
    }
  };

  const handleBackgroundClick = () => {
    setSelectedNode(null);
    setHighlightedNodeIds(new Set());
    setHighlightedLinkKeys(new Set());
  };

  // ── Link / node helpers ────────────────────────────────────────────────────

  const isLinkHighlighted = (link: any) => {
    const src = (link.source as any)?.id ?? link.source;
    const tgt = (link.target as any)?.id ?? link.target;
    return highlightedLinkKeys.has(`${src}->${tgt}`);
  };

  const getNodeColor = (n: any) => {
    const node = n as BrainNode;
    const base = NODE_COLORS[node.cluster] ?? "#a855f7";

    if (highlightedNodeIds.size > 0) {
      return highlightedNodeIds.has(node.id) ? "#facc15" : "rgba(255,255,255,0.05)";
    }
    if (!selectedNode) return base;
    if (node.id === selectedNode.id) return "#facc15";
    if (neighborIds.has(node.id)) return "#22c55e";
    return "rgba(255,255,255,0.08)";
  };

  const getLinkColor = (link: any) =>
    isLinkHighlighted(link) ? "rgba(255,215,0,0.95)" : "rgba(255,255,255,0.5)";

  const getLinkOpacity = (link: any) => {
    if (highlightedLinkKeys.size > 0) return isLinkHighlighted(link) ? 1 : 0.06;
    if (!selectedNode) return 0.35;
    const src = (link.source as any)?.id ?? link.source;
    const tgt = (link.target as any)?.id ?? link.target;
    if (src === selectedNode.id || tgt === selectedNode.id || neighborIds.has(src) || neighborIds.has(tgt))
      return 0.8;
    return 0.06;
  };

  const getLinkWidth = (link: any) => {
    if (isLinkHighlighted(link)) return 4;
    if (!selectedNode) return 0.5;
    const src = (link.source as any)?.id ?? link.source;
    const tgt = (link.target as any)?.id ?? link.target;
    if (src === selectedNode.id || tgt === selectedNode.id || neighborIds.has(src) || neighborIds.has(tgt))
      return 2.5;
    return 0.3;
  };

  const getParticleSpeed = (link: any) => {
    const srcId = (link.source as any)?.id ?? link.source;
    const tgtId = (link.target as any)?.id ?? link.target;
    const imp = Math.max(nodeById[srcId]?.importance ?? 1, nodeById[tgtId]?.importance ?? 1);
    return 0.002 + ((imp - 1) / 4) * 0.018;
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="app-root">
      {/* ── 3-D Graph ──────────────────────────────────────────────────── */}
      <div className="graph-panel">
        {/* Status badge */}
        <div style={{ position: "absolute", left: 12, top: 12, zIndex: 10 }}>
          <div
            style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              padding: "6px 12px", background: "rgba(0,0,0,0.6)",
              borderRadius: 8, color: "#fff", fontSize: 13, backdropFilter: "blur(6px)",
            }}
          >
            <div
              style={{
                width: 10, height: 10, borderRadius: 10,
                background: backendConnected ? "#22c55e" : "#ef4444",
                boxShadow: backendConnected ? "0 0 6px rgba(34,197,94,0.6)" : "0 0 6px rgba(239,68,68,0.6)",
              }}
            />
            {graphLoading ? "Loading graph…" : backendConnected ? "Backend: Connected" : "Backend: Offline"}
          </div>
        </div>

        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          backgroundColor="black"
          onNodeClick={handleNodeClick}
          onBackgroundClick={handleBackgroundClick}
          nodeLabel={(n: any) => {
            const node = n as BrainNode;
            return `<b>${node.label}</b><br/>Role: ${node.role}<br/>Section: ${node.section ?? "—"}`;
          }}
          nodeRelSize={4}
          nodeAutoColorBy="cluster"
          nodeColor={getNodeColor}
          linkColor={getLinkColor}
          linkOpacity={getLinkOpacity}
          linkWidth={getLinkWidth}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={getParticleSpeed}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleColor={() => "rgba(255,255,255,0.9)"}
          linkDirectionalArrowLength={10}
          linkDirectionalArrowRelPos={0.85}
          linkDirectionalArrowColor={() => "rgba(255,255,255,0.9)"}
          linkThreeObjectExtend={true}
          linkThreeObject={() => null}
          linkThreeObjectUpdate={(obj: any) => { if (obj) obj.visible = false; }}
        />
      </div>

      {/* ── Side Panel ──────────────────────────────────────────────────── */}
      <div className="side-panel">
        <h2>🧠 GNN Brain Graph</h2>

        {selectedNode ? (
          <>
            <h3>Selected Node</h3>
            <p>
              <strong>Label:</strong> {selectedNode.label}<br />
              <strong>Role:</strong> {selectedNode.role}<br />
              <strong>Section:</strong> {selectedNode.section ?? "—"}<br />
              <strong>Importance:</strong> {selectedNode.importance}
            </p>

            <h4>Description</h4>
            <p style={{ fontSize: 13, color: "#94a3b8" }}>{selectedNode.text}</p>

            <h4>Neighbours</h4>
            <ul style={{ fontSize: 13 }}>
              {graphData.nodes
                .filter((n) => neighborIds.has(n.id))
                .map((n) => (
                  <li key={n.id}>
                    <span
                      style={{
                        display: "inline-block", width: 10, height: 10,
                        borderRadius: "50%", background: NODE_COLORS[n.cluster] ?? "#a855f7",
                        marginRight: 6,
                      }}
                    />
                    {n.label} <span style={{ color: "#64748b" }}>({n.role})</span>
                  </li>
                ))}
            </ul>

            <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
              <button
                className="btn"
                onClick={() => { setHighlightedNodeIds(new Set()); setHighlightedLinkKeys(new Set()); }}
              >
                Clear highlights
              </button>
            </div>
          </>
        ) : (
          <p style={{ color: "#94a3b8", fontSize: 14 }}>
            Click any node in the graph to select it and start a conversation.
          </p>
        )}

        {/* Legend */}
        <div style={{ marginTop: 24 }}>
          <h4>Legend</h4>
          {[
            { color: "#22c55e", label: "Section A Students" },
            { color: "#f97316", label: "Section B Students" },
            { color: "#6366f1", label: "Section C Students" },
            { color: "#eab308", label: "HOD" },
            { color: "#ef4444", label: "Dean" },
            { color: "#0ea5e9", label: "Admin" },
            { color: "#ec4899", label: "Projects" },
            { color: "#a855f7", label: "Other" },
          ].map(({ color, label }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <div style={{ width: 12, height: 12, borderRadius: "50%", background: color, flexShrink: 0 }} />
              <span style={{ fontSize: 13, color: "#cbd5e1" }}>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Chat Panel ──────────────────────────────────────────────────── */}
      <ChatPanel
        nodeId={selectedNode?.id || null}
        nodeLabel={selectedNode?.label || null}
        backendUrl={BACKEND_URL}
        onSourcesReturned={(sources) => {
          setHighlightedNodeIds(new Set(sources));
          setHighlightedLinkKeys(new Set());
        }}
      />
    </div>
  );
};

export default App;
