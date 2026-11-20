# Express + Vite 后端代理模式

## 问题
参考前端使用Express+Vite架构（server.ts），需要代理API请求到独立的FastAPI后端。

## 解决方案(实测)

### server.ts 代理代码
```typescript
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

### 关键点
1. 使用fetch（Node 18+内置），不用http.request
2. Express的`app.use(express.json())`会预解析body，直接用`req.body`
3. 代理路由放在Vite middleware之前
4. 不转发content-type header（Express已解析body，手动设application/json）
5. multipart/form-data上传需要特殊处理（Express body parser不处理）

### 已验证的错误方案
- `http.request` + `req.pipe(proxyReq)` → 超时，与Vite middleware冲突
- `for await (const chunk of req)` → Express body已被consume，chunks为空
- `Buffer.concat(chunks)` → 同上

### 端口选择
- 检查端口占用：`lsof -i :PORT`
- 常用端口：3000(Next.js), 3001(其他系统), 3009(可用), 8001(后端)
- 在package.json的dev script中指定端口：`"dev": "vite --port 3009"`
