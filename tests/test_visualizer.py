import networkx as nx
from sin_code_review_interface.visualizer import GraphVisualizer, SemanticDiffRenderer


def _graph():
    g = nx.MultiDiGraph()
    g.add_node("a", name="a", kind="function", file="a.py")
    g.add_node("b", name="b", kind="function", file="b.py")
    g.add_edge("a", "b", kind="calls")
    return g


def test_render_subgraph():
    viz = GraphVisualizer(_graph())
    data = viz.render_subgraph("a", depth=1)
    ids = {n["id"] for n in data["nodes"]}
    assert "a" in ids and "b" in ids
    assert data["edges"][0]["kind"] == "calls"


def test_render_subgraph_missing_node():
    viz = GraphVisualizer(_graph())
    assert viz.render_subgraph("zzz") == {"error": "Node not found"}


def test_to_d3_format():
    viz = GraphVisualizer(_graph())
    d3 = viz.to_d3_format()
    assert len(d3["nodes"]) == 2
    assert len(d3["links"]) == 1


def test_diff_renderer():
    class Intent:
        risk = "high"
        headline = "Signature changed"
        rationale = "param removed"
    html = SemanticDiffRenderer.render_html([Intent()], {"risk": "high", "score": 0.8})
    assert "Signature changed" in html
    assert "dc3545" in html
