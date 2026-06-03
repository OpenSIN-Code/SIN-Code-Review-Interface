# `cli.py` — Command-line Interface

What this file does: Typer CLI with two commands: `serve` (start the FastAPI review server) and `diff` (render an intent-based semantic diff between two files as HTML).

## Dependency map

- Imports: `typer`, `uvicorn`. Optional runtime dep for `diff`: `sin-code-ibd` (lazy-imported inside the command so `serve` works without it).
- Imports: `.visualizer.SemanticDiffRenderer` (lazy-imported for the same reason).
- Console-script entry point: `sin-review` (declared in `pyproject.toml`).

## Subcommands

| Command | Purpose                                                                                |
|---------|----------------------------------------------------------------------------------------|
| `serve` | Start the FastAPI server. Default `127.0.0.1:8780`. Use `--reload` in dev.            |
| `diff`  | Render an intent-based semantic diff between two files. Optional `--out PATH` to write HTML. |

## Important config / limits

- **Default port: 8780** (configurable via `--port`).
- **Default host: `127.0.0.1`** (loopback only). Pass `--host 0.0.0.0` to expose externally.
- **`diff` requires `sin-code-ibd`** to be installed. `serve` does not.
- **`diff` writes raw HTML to stdout** if `--out` is not given — pipe into a browser or pager.

## Design decisions

- **Why Typer?** Same as the rest of the SIN-Code stack: auto `--help`, type validation, shell completion.
- **Why lazy-import `sin-code-ibd`?** It's an optional dep. `sin-review serve` should work in environments where you only want the review UI and don't need intent-based diffing.
- **Why port 8780?** Convention; this is a dev-time tool, not a long-running service.

## Usage examples

```bash
# Start the server (dev mode with auto-reload)
sin-review serve --reload

# Start on a different port, exposed to the network
sin-review serve --host 0.0.0.0 --port 9000

# Render a diff and save to disk
sin-review diff before.py after.py --out diff.html
```
