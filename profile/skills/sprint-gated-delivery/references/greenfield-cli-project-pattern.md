# Greenfield CLI Project — Sprint Pattern (Validated)

## Context

Sprint-gated-delivery is typically used for upgrading existing products. This reference documents that it works identically for **building from scratch** — a greenfield CLI + API + Dashboard project executed 7 consecutive sprints with no user intervention between gates.

## Project: Experiment Hub

A management system for 38 experiment/research skills. Built in one session, 7 sprints, all gates PASS.

## Architecture Pattern: CLI + API + Dashboard + SQLite

```
project/
├── pyproject.toml          # click + rich + pyyaml + fastapi + uvicorn
├── src/<pkg>/
│   ├── cli.py              # Click CLI entry (all commands)
│   ├── core/               # Business logic modules
│   │   ├── registry.py     # Scanner/classifier
│   │   ├── runner.py       # Execution engine
│   │   ├── recommender.py  # Recommendation engine
│   │   ├── crystallizer.py # Output generator
│   │   └── pipeline.py     # Workflow orchestrator
│   ├── adapters/           # Framework adapters (strategy pattern)
│   │   ├── base.py         # AbstractAdapter + ExperimentResult dataclass
│   │   └── <framework>.py  # One per framework
│   ├── storage/
│   │   └── database.py     # SQLite ORM (init + CRUD + stats)
│   └── api/
│       └── server.py       # FastAPI (REST endpoints + HTML serve)
├── dashboard/
│   └── index.html          # Single-file dark-theme dashboard (vanilla JS + fetch)
└── templates/              # YAML config templates
```

**Key decisions**:
- SQLite for zero-dependency persistence (no PostgreSQL needed for local tools)
- Single HTML for dashboard (no Node/npm/React build step)
- Click for CLI (simpler than argparse, richer than typer)
- Rich for terminal output (tables, panels, colors)
- FastAPI as optional layer (install only if `exp dashboard` is used)
- Adapters as strategy pattern (one per framework, shared base class)

## Sprint Sequence (Greenfield)

| Sprint | Focus | Deliverables | Gate |
|--------|-------|-------------|------|
| 1 | Skeleton | pyproject.toml, package structure, DB schema, scanner, CLI (list/info/stats/sync) | `exp list` shows N skills |
| 2 | Core Engine | Adapters (base + 4 frameworks), Runner, `exp run`, `exp results` | `exp run <skill> --task` completes |
| 3 | Intelligence | Recommender, Template manager, `exp recommend`, `exp compare`, `exp template` | All 3 commands work |
| 4 | Dashboard | FastAPI server, HTML dashboard (4 tabs), `exp dashboard` | API returns JSON, HTML loads |
| 5 | Crystallizer | Auto-generate SKILL.md from experiments, `exp crystallize` | Draft file generated |
| 6 | Skip/merge | (Adapters already done in Sprint 2) | — |
| 7 | Pipeline | YAML pipeline engine, conditional execution, context passing, `exp pipeline` | Pipeline loads and executes |

**Pattern**: Sprint 1 = skeleton that runs. Sprints 2-N = each adds one coherent module with its CLI commands. Each sprint is independently valuable.

## Gate Verification Pattern

For CLI tools, Gate 2 (Revision) uses subprocess to test commands:

```python
r = subprocess.run(
    [".venv/bin/exp", "run", "skill-name", "--task", "test"],
    capture_output=True, text=True, cwd=base, timeout=15
)
gate2.append(("exp run", "PASS" if r.returncode == 0 and "expected" in r.stdout else "FAIL"))
```

This is more reliable than import-testing because it validates the full CLI → logic → DB chain.

## Pitfalls from This Session

1. **pyproject.toml build-backend**: `setuptools.backends._legacy:_Backend` doesn't exist in newer setuptools. Use `setuptools.build_meta`.

2. **__init__.py must be non-empty**: Gate 1 checks file size > 0. Empty `__init__.py` files fail the check. Add a docstring: `"""Module description."""`

3. **Dashboard HTML path resolution**: When FastAPI server is at `src/pkg/api/server.py`, the dashboard at `project/dashboard/` requires `Path(__file__).parent.parent.parent.parent / "dashboard"` (4 levels up, not 3).

4. **YAML colons in values**: `description: 完整研究流程: 调研` fails YAML parsing. Quote values containing colons: `description: "完整研究流程"`.

5. **uv pip install hangs**: Use `uv sync` after editing pyproject.toml dependencies, not `uv pip install`.

6. **CLI commands as subgroups**: Click subgroups (`@main.group("template")`) need their own `__init__.py`-style registration. The parent group's `--help` automatically includes subcommands.

## Stats

- 22 Python files, 2,308 lines
- 12 CLI commands
- 6 framework adapters
- 5 database tables
- 4 dashboard tabs
- 5 design documents (~63K words)
- 7 git tags (v0.1.0 ~ v0.7.0)
- Total session time: ~45 minutes for full build
