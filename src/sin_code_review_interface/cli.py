"""CLI für das Review-Interface."""
import typer
import uvicorn

app = typer.Typer(help="SIN-Code Review Interface CLI")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8780),
    reload: bool = typer.Option(False, "--reload"),
):
    """Start the review interface server."""
    uvicorn.run(
        "sin_code_review_interface.server:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def diff(file_a: str, file_b: str, output: str = typer.Option(None, "--out")):
    """Generate semantic diff and optionally save as HTML."""
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
