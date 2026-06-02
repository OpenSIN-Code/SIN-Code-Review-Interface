# Installation — `sin-code-review-interface`

## Requirements

- Python **3.9+**
- `pip` (or `uv`/`pipx`)
- Git (for repository-aware features)

## Install from source (recommended during preview)

```bash
git clone https://github.com/OpenSIN-Code/SIN-Code-Review-Interface.git
cd SIN-Code-Review-Interface
pip install -e .
```

This installs the `sin-review` CLI and the importable package `sin_code_review_interface`.

## Install into an isolated environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
```

## Optional: MCP server support

The MCP server requires the optional `mcp` dependency:

```bash
pip install -e ".[mcp]"
```

## Verify the installation

```bash
sin-review --help
pytest -q
```

## Uninstall

```bash
pip uninstall sin-code-review-interface
```
