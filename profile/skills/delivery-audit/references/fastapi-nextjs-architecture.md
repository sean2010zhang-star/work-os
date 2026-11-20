# FastAPI + Next.js 双服务器架构

## 适用场景
Python后端(AI/ML/数据处理) + TypeScript前端(React/Next.js)的项目。

## 架构
```
浏览器 → Next.js(:3002) → API Proxy → FastAPI(:8000)
                ↓
         前端组件(shadcn/ui)
                ↓
         /api/proxy?target=/api/xxx
                ↓
         FastAPI后端(7+引擎)
```

## 后端 (FastAPI)

### 目录结构
```
backend/
├── main.py              # FastAPI入口 + 路由
├── requirements.txt     # Python依赖
├── engines/             # 业务引擎
│   ├── __init__.py
│   ├── base.py          # BaseEngine抽象基类
│   └── xxx_engine.py    # 具体引擎
├── schemas/             # Pydantic Schema
│   ├── __init__.py
│   └── xxx.py
├── parsers/             # 文档解析
│   ├── __init__.py
│   └── document_parser.py
└── uploads/             # 上传文件(.gitignore)
```

### BaseEngine模式
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
    strategy: str
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
    def process(self, input_data) -> EngineResult:
        ...

    def _run_with_timing(self, input_data) -> EngineResult:
        import time
        start = time.time()
        try:
            result = self.process(input_data)
            result.elapsed_ms = int((time.time() - start) * 1000)
            return result
        except Exception as e:
            return EngineResult(
                engine=self.name, version=self.version,
                strategy=self.config.strategy,
                elapsed_ms=int((time.time() - start) * 1000),
                success=False, errors=[str(e)]
            )
```

### CORS配置
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 前端 (Next.js)

### API Proxy路由
```typescript
// src/app/api/proxy/route.ts
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const target = url.searchParams.get("target") || "/api/upload";
  const contentType = request.headers.get("content-type") || "";

  if (contentType.includes("multipart/form-data")) {
    const formData = await request.formData();
    const resp = await fetch(`${BACKEND}${target}`, { method: "POST", body: formData });
    return NextResponse.json(await resp.json(), { status: resp.status });
  } else {
    const body = await request.json();
    const resp = await fetch(`${BACKEND}${target}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return NextResponse.json(await resp.json(), { status: resp.status });
  }
}
```

### 前端调用模式
```typescript
const resp = await fetch("/api/proxy?target=/api/endpoint", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});
const result = await resp.json();
```

## 启动命令
```bash
# 后端
cd backend && /opt/homebrew/bin/python3 main.py  # 端口8000

# 前端
npx next dev -p 3002  # 端口3002
```

## .gitignore
```
node_modules/
.next/
backend/uploads/
backend/__pycache__/
backend/*/__pycache__/
```

## Pitfalls
- Python版本: 确保pip3 show的Location与运行的python3一致
- CORS: FastAPI必须配置CORS middleware，否则前端proxy请求被拒
- multipart/form-data: proxy需要特殊处理FormData（不能JSON.stringify）
- Health check: 通过proxy验证后端可用性: `/api/proxy?target=/api/health`
