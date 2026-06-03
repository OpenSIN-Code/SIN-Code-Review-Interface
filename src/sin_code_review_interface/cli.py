"""CLI for the SIN-Code Review Interface.

Two commands:
  - `serve`: start the FastAPI review server (default 127.0.0.1:8780).
  - `diff`: render an intent-based semantic diff between two files as HTML.

Docs: cli.doc.md
"""
import typer
import uvicorn

app = typer.Typer(help="SIN-Code Review Interface CLI")


# ── serve ──────────────────────────────────────────────────────────────
@app.command()
def serve(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8780),
    reload: bool = typer.Option(False, "--reload"),
):
    """Start the review interface server.

    Args:
        host: Bind host. Default loopback only — set to 0.0.0.0 to expose externally.
        port: Bind port. Default 8780.
        reload: Auto-reload on code changes (dev only).
    """
    # We import the ASGI app by string so the entry point works even
    # when the module is run as a script (avoids re-imports).
    uvicorn.run(
        "sin_code_review_interface.server:app",
        host=host,
        port=port,
        reload=reload,
    )


# ── diff ───────────────────────────────────────────────────────────────
@app.command()
def diff(file_a: str, file_b: str, output: str = typer.Option(None, "--out")):
    """Render an intent-based semantic diff between two files as HTML.

    Args:
        file_a: Path to the "before" file.
        file_b: Path to the "after" file.
        output: If provided, write HTML to this file. Otherwise print to stdout.
    """
    # Imports are deferred so `sin-review serve` works even without
    # the optional `sin-code-ibd` dep installed.
    from sin_code_ibd import ASTDiff, IntentSummarizer, RiskScorer
    from .visualizer import SemanticDiffRenderer

    ad = ASTDiff()
    changes = ad.diff_files(file_a, file_b)
    intents = IntentSummarizer().summarize(changes)
    risk = RiskScorer().score(changes)

    html = SemanticDiffRenderer.render_html(intents, risk)

    if output:
        with open(output, "w") as f:
            f.write(html)
        typer.echo(f"Written to {output}")
    else:
        typer.echo(html)


if __name__ == "__main__":
    app()
