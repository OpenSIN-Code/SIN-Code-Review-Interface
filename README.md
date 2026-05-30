# SIN-Code Review Interface

> Human-centered review interface for agent-generated code.

Part of the SIN-Code agent-engineering stack. Brings the stack's signals —
semantic diffs (IBD) and knowledge graphs (SCKG) — into a UI a human can read.

## Why

Agents produce changes faster than humans can review line-by-line. This interface
surfaces **intent** and **risk** instead of raw line diffs, and lets reviewers
explore the blast radius of a change through the knowledge graph.

## Features

- **Web UI**: FastAPI server with a zero-build HTML front end
- **Semantic review API**: `POST /api/review` runs IBD's AST diff + intent + risk
- **Graph view**: `GET /api/graph/{symbol}` returns a knowledge-graph subgraph
- **Renderers**: `GraphVisualizer` (D3-ready JSON) and `SemanticDiffRenderer` (HTML)
- **CLI**: serve the UI or emit a standalone HTML diff

## Quickstart

```bash
pip install -e .

# Start the server
sin-review serve --port 8780
# open http://127.0.0.1:8780

# Generate a standalone HTML diff
sin-review diff old.py new.py --out review.html
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Review UI |
| POST | `/api/review` | Semantic diff + intent + risk for two files |
| GET | `/api/graph/{symbol_fqid}` | Knowledge-graph subgraph around a symbol |
| GET | `/health` | Liveness probe |

The review and diff endpoints depend on `sin-code-ibd`; the graph endpoint
depends on `sin-code-sckg`. Install those alongside this package to enable them.

## VSCode

The optional `vscode` extra (`pip install -e .[vscode]`) pulls in `pyright` and
`python-lsp-server` for editor integration.

## License

MIT — see LICENSE.
