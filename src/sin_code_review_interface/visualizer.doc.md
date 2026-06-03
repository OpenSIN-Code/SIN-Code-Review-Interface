# `visualizer.py` — Visualization Components

What this file does: two classes for rendering structured data as UI-ready output. `GraphVisualizer` extracts a subgraph from a NetworkX graph and formats it for the frontend / D3.js. `SemanticDiffRenderer` produces a self-contained HTML snippet for an intent-based diff (used by the CLI `diff` command).

## Dependency map

- Imports: `networkx` (external dep).
- Imported by: `cli.py` (lazy import for the `diff` command).

## Public API

| Symbol                                       | Purpose                                                            |
|----------------------------------------------|--------------------------------------------------------------------|
| `GraphVisualizer(graph)`                     | Wrap a `networkx.MultiDiGraph` (the SIN knowledge graph).          |
| `.render_subgraph(center_node, depth=2)`     | Extract and format a subgraph; returns `{center, nodes, edges}` or `{"error": "Node not found"}`. |
| `.to_d3_format()`                            | Convert the full graph to D3's `nodes`/`links` shape.             |
| `SemanticDiffRenderer.render_html(intents, risk)` | Render an intent summary + risk score as inline-styled HTML. |

## Important config / limits

- **Default BFS depth: 2** (center + 1 hop + 2 hops). Larger depths are exponentially more nodes.
- **Subgraph includes BOTH successors and predecessors** — the full neighborhood, not just downstream.
- **`render_html` produces self-contained HTML** with inline styles. No external CSS or JS — drop it into a Markdown doc and it just renders.
- **Risk color map is hard-coded**: `high` → red, `medium` → amber, `low` → green, anything else → gray.
- **D3 output uses `value: 1`** for all edges. Replace with a real weight if you add one to your graph.

## Design decisions

- **Why NetworkX?** It's the standard Python graph library and the rest of the SIN-Code stack already depends on it. Using it here means we don't introduce a second graph library.
- **Why both `render_subgraph` and `to_d3_format`?** They serve different consumers: the review UI uses `render_subgraph` (focused, keyed by center), the analytics dashboard uses `to_d3_format` (full graph, force-directed).
- **Why inline styles in `render_html`?** The output is meant to be embedded in places that don't have the SIN-Code CSS (emails, Slack previews, etc.). External stylesheets would break those.
- **Why `predecessors` and `successors` together?** A node's full context matters. Limiting to successors would miss importers; limiting to predecessors would miss callees.

## Usage examples

```python
import networkx as nx
from sin_code_review_interface.visualizer import GraphVisualizer, SemanticDiffRenderer

g = nx.MultiDiGraph()
g.add_node("foo", name="foo", kind="function", file="x.py")
g.add_node("bar", name="bar", kind="function", file="x.py")
g.add_edge("foo", "bar", kind="calls")

gv = GraphVisualizer(g)
print(gv.render_subgraph("foo", depth=1))
# {"center": "foo", "nodes": [...], "edges": [...]}

# HTML for an intent-based diff
html = SemanticDiffRenderer.render_html(intents=[...], risk={"risk": "high", "score": 0.8})
```

## Caveats / footguns

- **`render_subgraph` is a BFS but doesn't deduplicate paths.** A diamond-shaped dependency (A → B → D, A → C → D) will visit D twice. The set-accumulating loop ensures D is added once, but the per-edge metadata in the output may not match the path taken.
- **`to_d3_format` loads the WHOLE graph into memory.** Fine for thousands of nodes, problematic for millions. Add pagination if you need to scale.
- **The HTML in `render_html` uses `<em>` and `<strong>` but no `<p>`** — spacing is done with `<br>` and CSS margin. If you wrap it in a `<p>`, the spacing will collapse.
- **Edge case: an empty `intents` list** still produces a valid (but minimal) HTML output with just the risk header.
