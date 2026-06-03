"""Visualization components for knowledge graphs and semantic diffs.

Two classes:
  - `GraphVisualizer`: extracts a subgraph around a node and formats it
    for the review UI / D3.js.
  - `SemanticDiffRenderer`: produces a self-contained HTML snippet for
    an intent-based diff (used by the CLI `diff` command).

Docs: visualizer.doc.md
"""
from __future__ import annotations

import json
from typing import Any, Optional

import networkx as nx


# ── GraphVisualizer ────────────────────────────────────────────────────
class GraphVisualizer:
    """Render knowledge-graph subsets for UI display.

    Wraps a `networkx.MultiDiGraph` (the SIN-Code knowledge graph) and
    produces JSON-shaped data the frontend can render directly.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def render_subgraph(self, center_node: str, depth: int = 2) -> dict:
        """Extract and format a subgraph around a center node.

        Walks both successors AND predecessors, so the result includes
        the full neighborhood (callers + callees, importers + importers-of).

        Args:
            center_node: Node id to anchor on.
            depth: BFS depth (default 2 — center + 1 hop + 2 hops).

        Returns:
            Dict with `center`, `nodes`, `edges` keys, or
            `{"error": "Node not found"}` if `center_node` isn't in the graph.
        """
        if not self.graph.has_node(center_node):
            return {"error": "Node not found"}

        # ── BFS up to `depth` levels, including predecessors ──
        # We track `current` and expand it each iteration; `nodes` accumulates.
        nodes = {center_node}
        current = {center_node}
        for _ in range(depth):
            next_level = set()
            for n in current:
                # Both directions — we want the full neighborhood, not just
                # the call graph "downstream" of `center_node`.
                next_level.update(self.graph.successors(n))
                next_level.update(self.graph.predecessors(n))
            nodes.update(next_level)
            current = next_level

        # ── Format for the frontend ──
        # Each node carries id / label (display name) / kind / file.
        # Edges are filtered to those with BOTH endpoints in our node set.
        graph_data = {
            "center": center_node,
            "nodes": [
                {
                    "id": n,
                    "label": self.graph.nodes[n].get("name", n),
                    "kind": self.graph.nodes[n].get("kind", "unknown"),
                    "file": self.graph.nodes[n].get("file"),
                }
                for n in nodes
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "kind": data.get("kind", "unknown"),
                }
                for u, v, data in self.graph.edges(keys=False, data=True)
                if u in nodes and v in nodes
            ],
        }
        return graph_data

    def to_d3_format(self) -> dict:
        """Convert the full graph to D3.js's force-directed shape.

        Output uses D3's `nodes`/`links` convention (note: `links`, not `edges`).
        `value: 1` is a placeholder — tune to edge weight if you add one.
        """
        return {
            "nodes": [
                # `group` becomes the D3 color category; we default to 1
                # (single color) when the node has no `kind` annotation.
                {"id": n, "name": d.get("name", n), "group": d.get("kind", 1)}
                for n, d in self.graph.nodes(data=True)
            ],
            "links": [
                {"source": u, "target": v, "value": 1}
                for u, v in self.graph.edges()
            ],
        }


# ── SemanticDiffRenderer ───────────────────────────────────────────────
class SemanticDiffRenderer:
    """Render intent-based diffs as self-contained HTML for the review UI.

    The output is a single `<div>` with inline styles — no external CSS,
    no JS. Drop it into a Markdown doc or an email and it just works.
    """

    @staticmethod
    def render_html(intents: list, risk: dict) -> str:
        """Render an intent summary + risk score as a styled HTML snippet.

        Args:
            intents: List of `Intent` objects (from `sin-code-ibd`).
                     Each must have `.risk`, `.headline`, `.rationale`.
            risk: Dict with `"risk"` (one of high/medium/low) and `"score"`.

        Returns:
            HTML string. Inline-styled; safe to embed anywhere.
        """
        # Bootstrap-style colors: red/amber/green for high/medium/low.
        # `gray` is the fallback for unexpected risk values.
        color = {"high": "#dc3545", "medium": "#ffc107", "low": "#28a745"}.get(risk["risk"], "#6c757d")

        html = f"""
        <div style="border-left: 4px solid {color}; padding: 1rem; background: #f8f9fa;">
            <h3 style="margin: 0 0 1rem;">Risk: {risk['risk']} ({risk['score']})</h3>
        """

        for intent in intents:
            html += f"""
            <div style="margin-bottom: 1rem;">
                <strong>[{intent.risk.upper()}]</strong> {intent.headline}<br>
                <em style="color: #666;">{intent.rationale}</em>
            </div>
            """

        html += "</div>"
        return html
