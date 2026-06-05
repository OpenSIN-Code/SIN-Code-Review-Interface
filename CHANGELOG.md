# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial SIN-Code-Bundle integration (ceo-audit workflow v3)
- OpenCode MCP server registration under `OpenSIN-Code/SIN-Code-Review-Interface`
- Repository-level `SIN_GITHUB_FALLBACK_TOKEN` secret for the App commenter fallback
- Human-centered review interface for agent-generated code
- Programmatic API: CLI + library + web UI
- MCP-consumable for both humans and agents
- Python 3.9+ support under the MIT license
- Installed via the [SIN-Code Bundle](https://github.com/OpenSIN-Code/SIN-Code-Bundle): `pip install sin-code-review-interface`

### Security
- All commits verified via `git-immortal-commit` (annotated tags)
- Server-side diff rendering, no agent-controlled HTML injection
