# Express + Vite + FastAPI Proxy Pattern

## Problem
When using Vite dev server with Express middleware mode and a FastAPI backend, proxying API requests from the frontend to the backend requires specific patterns.

## Solution: Express middleware proxy using fetch

```typescript
// server.ts
const BACKEND_URL = "http://localhost:8001";

// Must be registered BEFORE vite.middlewares
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

// AFTER the proxy route
if (process.env.NODE_ENV !== "production") {
  const vite = await createViteServer({ server: { middlewareMode: true }, appType: "spa" });
  app.use(vite.middlewares);
}
```

## Pitfalls

1. **http.request pipe approach fails** - Using Node's `http.request` with `req.pipe(proxyReq)` causes timeouts in Vite middleware mode. Use `fetch` instead.

2. **Multipart form data** - The `JSON.stringify(req.body)` approach only works for JSON. For file uploads, the frontend must call the backend directly OR use a streaming proxy (not covered here).

3. **Proxy must be before Vite middleware** - If Vite middleware runs first, it will try to handle `/api/v1/*` as a frontend route.

4. **bcrypt 5.x breaks passlib** - Pin `bcrypt==4.0.1` in requirements.txt. bcrypt 5.x removed `__about__` module that passlib relies on.

## Port allocation
- Backend: 8001 (FastAPI default)
- Frontend: 3009 (avoid 3000/3001 which are commonly used)
