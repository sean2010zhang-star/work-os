# Vite + Express + FastAPI Proxy Pattern

## Problem
Reference frontend uses Vite+Express (e.g. Google AI Studio export), but backend is FastAPI on different port.

## Solution: Express Proxy Middleware

### server.ts
```typescript
const PORT = 3009;
const BACKEND_URL = "http://localhost:8001";

// Proxy /api/v1/* to FastAPI backend
app.use("/api/v1", async (req, res) => {
  try {
    const targetUrl = `${BACKEND_URL}/api/v1${req.url}`;
    const headers: Record<string, string> = {};
    if (req.headers.authorization) headers["Authorization"] = req.headers.authorization as string;

    const fetchOpts: RequestInit = { method: req.method, headers };
    if (req.method !== "GET" && req.method !== "HEAD" && req.body) {
      headers["Content-Type"] = "application/json";
      fetchOpts.body = JSON.stringify(req.body);
    }

    const response = await fetch(targetUrl, fetchOpts);
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (e: any) {
    console.error("Backend proxy error:", e.message);
    res.status(502).json({ error: "Backend unavailable" });
  }
});
```

### Key Points
1. Express `app.use("/api/v1")` 必须在 Vite middleware 之前注册
2. 用 `req.body`（Express已解析的JSON body），不要用 `for await (const chunk of req)` 流式读取
3. 用 `fetch` 而不是 `http.request`（后者在tsx环境下有兼容问题）
4. 前端直接调用 `/api/v1/*`，不需要跨域配置

### Pitfalls
- `http.request` pipe模式在tsx+Vite环境下超时（原因不明），用fetch替代
- multipart/form-data（文件上传）需要特殊处理：Express的body parser不解析multipart
- 前端的auth token通过 `localStorage.getItem("token")` 获取，在axios interceptor中注入
