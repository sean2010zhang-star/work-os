# FastAPI + Next.js 双服务器架构模式

> 适用于: Python后端(ML/AI/数据处理) + React前端 的全栈项目

## 架构

```
浏览器 → Next.js(:3002) → API Proxy → FastAPI(:8000)
                ↓                        ↓
         React前端(TSX)          Python引擎(7+个)
```

## 关键组件

### 1. FastAPI后端 (backend/main.py)

```python
#!/usr/bin/env /opt/homebrew/bin/python3  # macOS必须显式指定
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="项目名", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
async def health():
    return {"status": "ok", "engines": [...]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Next.js API Proxy (src/app/api/proxy/route.ts)

```typescript
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const target = url.searchParams.get("target") || "/api/health";
  const resp = await fetch(`${BACKEND}${target}`);
  return NextResponse.json(await resp.json());
}

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const target = url.searchParams.get("target") || "/api/upload";
  const contentType = request.headers.get("content-type") || "";
  
  if (contentType.includes("multipart/form-data")) {
    const formData = await request.formData();
    const resp = await fetch(`${BACKEND}${target}`, { method: "POST", body: formData });
    return NextResponse.json(await resp.json(), { status: resp.status });
  }
  // ... JSON fallback
}
```

### 3. 前端调用模式

```typescript
// 通过proxy调用后端API
const resp = await fetch("/api/proxy?target=/api/extract-criteria", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ parse_result: data }),
});
```

## 引擎架构模式 (BaseEngine)

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel

class EngineConfig(BaseModel):
    enabled: bool = True
    timeout: int = 60
    strategy: str = "default"

class EngineResult(BaseModel):
    engine: str
    version: str
    elapsed_ms: int
    success: bool
    errors: list[str] = []
    data: dict | None = None

class BaseEngine(ABC):
    name: str = "base"
    version: str = "1.0.0"
    
    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()
    
    @abstractmethod
    def process(self, input_data) -> EngineResult: ...
    
    def _run_with_timing(self, input_data) -> EngineResult:
        import time
        start = time.time()
        try:
            result = self.process(input_data)
            result.elapsed_ms = int((time.time() - start) * 1000)
            return result
        except Exception as e:
            return EngineResult(engine=self.name, ..., success=False, errors=[str(e)])
```

## 启动脚本

```bash
# 后端 (terminal 1)
cd backend && /opt/homebrew/bin/python3 main.py  # macOS
cd backend && python3 main.py                     # Linux

# 前端 (terminal 2)
npx next dev -p 3002
```

## Pipeline编排模式

当项目有多个引擎需要串联时，创建Pipeline编排器：

```python
class BidEvaluationPipeline:
    def __init__(self):
        self.parser = DocumentParser(EngineConfig())
        self.extractor = CriteriaExtractor(EngineConfig())
        self.scorer = ScoringEngine(EngineConfig())
        # ... 实例化所有引擎

    def run_full_evaluation(self, files, params) -> dict:
        start = time.time()
        steps = []
        
        # Step 1: 解析
        result = self.parser._run_with_timing(file_path)
        steps.append({"step": "解析", "elapsed_ms": ...})
        
        # Step 2: 拆解 (依赖Step1)
        criteria = self.extractor._run_with_timing({"parse_result": result.data})
        
        # Step 3: 并行处理每个投标人
        for bid_file in bid_files:
            score = self.scorer._run_with_timing(score_input)
            # ...
        
        return {"success": True, "steps": steps, "scores": [...], "elapsed_ms": ...}
```

API端点接收Pipeline参数，调用编排器，返回完整结果。

## 8引擎架构示例（通用多模块系统）

```
E1 DocumentParser    → PDF/DOCX解析
E2 CriteriaExtractor → 标准拆解 (rule/llm/hybrid)
E3 ComplianceChecker → 资格审查
E4 ScoringEngine     → 评分 (客观+金额+主观+协同过滤)
E5 DeviationAnalyzer → 偏离分析
E6 CollusionDetector → 围标串标检测
E7 EquityChecker     → 股权穿透
E8 ReportGenerator   → Word/Excel报告

Pipeline: E1→E2→[E3∥E4∥E5]→E6→E7→E8
```

## 注意事项

- macOS上必须用 `/opt/homebrew/bin/python3`，系统python3可能缺少fastapi等包
- CORS必须允许 `*`（开发阶段），生产环境需限制
- Proxy route必须处理 multipart/form-data（文件上传）
- `max_duration` 设为30秒（Next.js API route默认10秒太短）
- 每个引擎独立模块，有自己的输入/输出Schema、配置、日志
- 引擎可替换策略（配置文件切换），Pipeline支持并行/串联/跳过
