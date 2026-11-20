# Express → FastAPI Proxy Pattern

## Problem
Vite+Express frontend (port 3009) needs to proxy `/api/v1/*` requests to a FastAPI backend (port 8002).

## Solution (server.ts)

```typescript
const BACKEND_URL = "http://localhost:8002";

app.use("/api/v1", async (req, res) => {
  try {
    const targetUrl = `${BACKEND_URL}/api/v1${req.url}`;
    const headers: Record<string, string> = {};
    if (req.headers.authorization) headers["Authorization"] = req.headers.authorization;
    
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

## Key Points

1. Use Express's already-parsed `req.body` (JSON middleware handles it)
2. Forward `Authorization` header for JWT auth
3. Set `Content-Type: application/json` for POST/PUT
4. Return `502` on backend unavailability
5. **Do NOT use `http.request` pipe pattern** — multipart uploads fail with it
6. **Do NOT read request chunks manually** — Express body parser already did it

## Pitfalls

- `BACKEND_URL` defaults to `localhost:8001` in reference code, must change for cloud deployment
- Multipart file uploads go through this proxy — ensure Express body parser handles them
- The proxy adds latency (~5ms) — acceptable for dev, consider nginx for production
