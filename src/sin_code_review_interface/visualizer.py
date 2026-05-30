"""Visualisierungskomponenten für semantische Graphen und Diffs."""
from __future__ import annotations

import json
from typing import Any, Optional

import networkx as nx


class GraphVisualizer:
    """Rendert Knowledge-Graph-Subsets für UI-Darstellung."""

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def render_subgraph(self, center_node: str, depth: int = 2) -> dict:
        """Extrahiert und formatiert einen Subgraphen um einen Knoten."""
        if not self.graph.has_node(center_node):
            return {"error": "Node not found"}

        # Collect nodes within depth
        nodes = {center_node}
        current = {center_node}
        for _ in range(depth):
            next_level = set()
            for n in current:
                next_level.update(self.graph.successors(n))
                next_level.update(self.graph.predecessors(n))
            nodes.update(next_level)
            current = next_level

        # Format for frontend
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
        """Konvertiert für D3.js Visualisierung."""
        return {
            "nodes": [
                {"id": n, "name": d.get("name", n), "group": d.get("kind", 1)}
                for n, d in self.graph.nodes(data=True)
            ],
            "links": [
                {"source": u, "target": v, "value": 1}
                for u, v in self.graph.edges()
            ],
        }


class SemanticDiffRenderer:
    """Rendert Intent-Based Diffs für UI."""

    @staticmethod
    def render_html(intents: list, risk: dict) -> str:
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
