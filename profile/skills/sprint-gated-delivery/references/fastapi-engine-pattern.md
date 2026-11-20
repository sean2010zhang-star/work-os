# FastAPI 多引擎架构模式

> 适用于：多引擎系统、文档处理系统等需要多个独立处理引擎的项目

## 目录结构

```
backend/
├── main.py                    # FastAPI应用入口
├── pipeline.py                # Pipeline编排器
├── engines/
│   ├── __init__.py
│   ├── base.py               # BaseEngine抽象基类
│   ├── engine_a.py           # 具体引擎A
│   └── engine_b.py           # 具体引擎B
├── schemas/
│   ├── __init__.py
│   └── document.py           # Pydantic数据模型
├── parsers/
│   ├── __init__.py
│   └── document_parser.py    # 文档解析
├── uploads/                   # 上传文件存储
├── reports/                   # 生成的报告
└── requirements.txt
```

## BaseEngine 抽象基类

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, Optional
import time

class EngineConfig(BaseModel):
    enabled: bool = True
    timeout: int = 60
    retry: int = 2
    strategy: str = "default"

class EngineResult(BaseModel):
    engine: str
    version: str
    strategy: str
    elapsed_ms: int
    success: bool
    errors: list[str] = []
    data: Optional[dict] = None

class BaseEngine(ABC):
    name: str = "base"
    version: str = "1.0.0"

    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()

    @abstractmethod
    def process(self, input_data: Any) -> EngineResult:
        ...

    def validate_input(self, input_data: Any) -> bool:
        return True

    def get_info(self) -> dict:
        return {"name": self.name, "version": self.version,
                "strategy": self.config.strategy, "enabled": self.config.enabled}

    def _run_with_timing(self, input_data: Any) -> EngineResult:
        start = time.time()
        try:
            if not self.validate_input(input_data):
                return EngineResult(engine=self.name, version=self.version,
                    strategy=self.config.strategy, elapsed_ms=0,
                    success=False, errors=["Input validation failed"])
            result = self.process(input_data)
            result.elapsed_ms = int((time.time() - start) * 1000)
            return result
        except Exception as e:
            return EngineResult(engine=self.name, version=self.version,
                strategy=self.config.strategy,
                elapsed_ms=int((time.time() - start) * 1000),
                success=False, errors=[str(e)])
```

## Pipeline 编排器模式

```python
class BidEvaluationPipeline:
    def __init__(self):
        self.parser = DocumentParser(EngineConfig(strategy="pymupdf"))
        self.extractor = CriteriaExtractor(EngineConfig(strategy="hybrid"))
        self.compliance = ComplianceChecker(EngineConfig(strategy="default"))
        self.scorer = ScoringEngine(EngineConfig(strategy="default"))

    def run_full_evaluation(self, tender_file, bid_files, ...) -> dict:
        # Step 1: Parse
        # Step 2: Extract criteria
        # Step 3: For each bidder: compliance + score + deviation
        # Step 4: Generate reports
        return {"success": True, "steps": [...], "scores": [...], "reports": {...}}
```

## FastAPI 路由模式

```python
# 每个引擎一个独立端点
@app.post("/api/extract-criteria")
async def extract_criteria(body: dict):
    result = criteria_extractor._run_with_timing({"parse_result": body.get("parse_result")})
    if not result.success:
        raise HTTPException(500, f"失败: {result.errors}")
    return {"success": True, "data": result.data, "elapsed_ms": result.elapsed_ms}

# Pipeline端点串联所有引擎
@app.post("/api/pipeline")
async def run_pipeline(body: dict):
    result = pipeline.run_full_evaluation(...)
    return {"success": True, "data": result}
```

## Next.js API Proxy 模式

前端不直接调FastAPI(8000)，通过Next.js API route代理：

```typescript
// src/app/api/proxy/route.ts
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const target = url.searchParams.get("target") || "/api/upload";
  const formData = await request.formData();
  const resp = await fetch(`${BACKEND}${target}`, { method: "POST", body: formData });
  return NextResponse.json(await resp.json(), { status: resp.status });
}
```

前端调用: `fetch("/api/proxy?target=/api/upload", { ... })`

## macOS Python 版本陷阱

homebrew Python 3.11 有 fastapi/pymupdf，系统 Python 可能没有。

解决方案：shebang 指定 homebrew Python
```python
#!/usr/bin/env /opt/homebrew/bin/python3
```

验证命令: `pip3 show fastapi | grep Location` 确认安装位置。
