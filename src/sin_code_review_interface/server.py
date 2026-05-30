"""FastAPI-Server für das Review-Interface."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from .visualizer import GraphVisualizer, SemanticDiffRenderer


app = FastAPI(title="SIN-Code Review Interface")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    file_a: str
    file_b: str
    repo_root: Optional[str] = "."


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main review UI."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SIN-Code Review Interface</title>
        <style>
            body { font-family: system-ui; margin: 2rem; }
            .diff { background: #f8f9fa; padding: 1rem; border-radius: 4px; }
            .risk-high { border-left: 4px solid #dc3545; }
            .risk-medium { border-left: 4px solid #ffc107; }
            .risk-low { border-left: 4px solid #28a745; }
        </style>
    </head>
    <body>
        <h1>SIN-Code Semantic Review</h1>
        <form id="reviewForm">
            <input type="text" id="fileA" placeholder="File A path" required>
            <input type="text" id="fileB" placeholder="File B path" required>
            <button type="submit">Analyze</button>
        </form>
        <div id="results"></div>
        <script>
            document.getElementById('reviewForm').onsubmit = async (e) => {
                e.preventDefault();
                const res = await fetch('/api/review', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        file_a: document.getElementById('fileA').value,
                        file_b: document.getElementById('fileB').value
                    })
                });
                const data = await res.json();
                document.getElementById('results').innerHTML =
                    `<div class="diff risk-${data.risk.risk}">
                        <h3>Risk: ${data.risk.risk} (${data.risk.score})</h3>
                        ${data.intents.map(i =>
                            `<p><strong>[${i.risk.toUpperCase()}]</strong> ${i.headline}</p>
                             <p><em>${i.rationale}</em></p>`
                        ).join('')}
                    </div>`;
            };
        </script>
    </body>
    </html>
    """


@app.post("/api/review")
async def api_review(req: ReviewRequest):
    """Semantic review endpoint."""
    try:
        from sin_code_ibd import ASTDiff, IntentSummarizer, RiskScorer

        ad = ASTDiff()
        changes = ad.diff_files(req.file_a, req.file_b)
        intents = IntentSummarizer().summarize(changes)
        risk = RiskScorer().score(changes)

        return JSONResponse({
            "intents": [i.__dict__ for i in intents],
            "risk": risk,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/{symbol_fqid}")
async def graph_view(symbol_fqid: str, repo_root: str = Query(".")):
    """Return knowledge graph view for a symbol."""
    try:
        from sin_code_sckg.graph import KnowledgeGraph
        kg = KnowledgeGraph(storage_path=f"{repo_root}/.sin/knowledge.graph")

        if not kg.graph.has_node(symbol_fqid):
            raise HTTPException(status_code=404, detail="Symbol not found")

        visualizer = GraphVisualizer(kg.graph)
        return JSONResponse(visualizer.render_subgraph(symbol_fqid, depth=2))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
