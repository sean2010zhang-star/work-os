# Python CLI + FastAPI + SQLite 项目脚手架 — Sprint结构参考

## 来源
Experiment Hub项目(v0.1.0→v0.7.0, 7个Sprint, )

## 推荐Sprint结构(新Python CLI+API项目)

| Sprint | 内容 | 产出 | Gate条件 |
|--------|------|------|----------|
| 1 | 项目骨架+数据层 | pyproject.toml, SQLite建表, 基本CLI | `exp list`可用 |
| 2 | 核心引擎 | Runner/Processor, CLI主命令 | `exp run`可用 |
| 3 | 辅助功能 | 推荐/对比/模板 | 3个CLI命令可用 |
| 4 | Web Dashboard | FastAPI后端+单HTML前端 | API返回200, HTML加载 |
| 5 | 高级功能 | 结晶/导出/报告 | 核心功能端到端可用 |
| 6 | 扩展 | 额外适配器/插件 | 新模块导入成功 |
| 7 | 编排 | Pipeline/Workflow引擎 | YAML解析+执行 |

## pyproject.toml 模板(uv + src layout)

```toml
[project]
name = "project-name"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
    "pyyaml>=6.0",
    "fastapi>=0.100",
    "uvicorn>=0.23",
]

[project.scripts]
cmd = "package.cli:main"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

## 包结构(src layout)

```
project/
├── pyproject.toml
├── src/package/
│   ├── __init__.py          # 必须非空(Gate检查)
│   ├── cli.py               # Click入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── engine.py        # 核心引擎
│   │   └── utils.py         # 工具函数
│   ├── storage/
│   │   ├── __init__.py
│   │   └── database.py      # SQLite层
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── base.py          # 适配器基类
│   ├── api/
│   │   ├── __init__.py
│   │   └── server.py        # FastAPI
│   └── models/
│       └── __init__.py
├── dashboard/
│   └── index.html           # 单HTML前端
└── .gitignore
```

## 关键pitfalls

1. **build-backend必须是`setuptools.build_meta`** — 不能用`setuptools.backends._legacy:_Backend`(不存在)
2. **__init__.py不能空文件** — Gate 1 Pre-flight会检查文件非空，至少加一行docstring
3. **FastAPI dashboard路径** — `Path(__file__).parent.parent.parent.parent / "dashboard"` (从api/server.py往上4层)
4. **uv venv必须先创建** — `uv venv` → `uv pip install -e .` 或 `uv sync`
5. **.gitignore必须在第一次commit前创建** — 否则__pycache__/.venv会被跟踪

## Gate验证脚本模式

```python
# Gate 1: Pre-flight — 文件存在性
expected_files = ["pyproject.toml", "src/pkg/cli.py", ...]
for f in expected_files:
    assert os.path.exists(f) and os.path.getsize(f) > 0

# Gate 2: Revision — 功能验证
# Test: CLI --help
r = subprocess.run([".venv/bin/cmd", "--help"], ...)
assert r.returncode == 0 and "expected" in r.stdout

# Test: import core modules
r = subprocess.run([".venv/bin/python", "-c", "from pkg.core.engine import Engine; print('OK')"], ...)

# Test: API routes exist
r = subprocess.run([".venv/bin/python", "-c", """
from pkg.api.server import app
routes = [r.path for r in app.routes]
assert '/api/endpoint' in routes
"""], ...)
```
