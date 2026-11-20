# Express-to-FastAPI Proxy + your cloud provider Deployment (Validated)

## Context
When deploying a Vite+Express frontend alongside a FastAPI backend on a lightweight cloud server, the Express server can proxy API requests to FastAPI. This avoids CORS issues and allows a single port for the frontend.

## Express Proxy Pattern (server.ts)
```typescript
const BACKEND_URL = "http://localhost:8002";

// Proxy /api/v1/* to FastAPI backend using native fetch
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

**Why not `http.request` pipe**: The Node.js `http.request` pipe approach fails with some request body sizes. `fetch` with `JSON.stringify(req.body)` is more reliable when Express has already parsed the JSON body via `app.use(express.json())`.

**Why not `for await (const chunk of req)`**: Reading request body chunks from Express req stream can hang or produce empty buffers. Using the pre-parsed `req.body` is safer.

## your cloud provider Deployment Pattern

### Server: <your-server> (<spec>)
### Key constraint: No PostgreSQL, no Redis, must not affect existing services

### Port allocation (independent partition)
| Port | Service | Process |
|------|---------|---------|
| 3009 | Example Frontend | node (Express+Vite) |
| 3010 | Existing legacy service | uvicorn |
| 8002 | Example Backend | python3 (FastAPI) |

### systemd service files
```ini
# /etc/systemd/system/myapp-backend.service
[Unit]
Description=<app> Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/myapp/backend
ExecStart=/home/ubuntu/myapp/backend/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/myapp-web.service
[Unit]
Description=<app> Frontend
After=network.target myapp-backend.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/myapp/web
ExecStart=/usr/bin/npm run dev
Restart=always
RestartSec=5
Environment=NODE_ENV=development
Environment=PORT=3009

[Install]
WantedBy=multi-user.target
```

### Deployment steps
1. `scp` tar.gz to server
2. Extract to `~/myapp/`
3. Create `.env` with random keys: `openssl rand -hex 32`
4. `chmod 600 .env`
5. `python3 -m venv .venv && pip install -r requirements.txt`
6. `sudo systemctl daemon-reload && sudo systemctl enable myapp-backend && sudo systemctl start myapp-backend`
7. `npm install && sudo systemctl enable myapp-web && sudo systemctl start myapp-web`
8. Verify: `curl http://localhost:8002/health`

### CRITICAL: .env must be re-applied after scp
The tar.gz includes the local `.env` which has local PostgreSQL URL. After extracting on the server, **always** copy the cloud-specific `.env` over it:
```bash
cp /tmp/myapp-cloud.env ~/myapp/backend/.env
chmod 600 ~/myapp/backend/.env
```

## Pitfalls
1. **NODE_ENV=production without build**: Express serves static from `dist/` in production mode. If you haven't run `npm run build`, the frontend returns 404. Use `NODE_ENV=development` for Vite dev server.
2. **Port conflict**: Always check `ss -tlnp` before deploying. Never use ports already in use by existing services.
3. **Python 3.10 vs 3.11**: Server may have Python 3.10 while local has 3.11. Test import on the server before starting the service.
4. **.env gets overwritten by scp**: The local `.env` (with PostgreSQL URL) is included in the tar.gz. Must re-apply cloud `.env` after extraction.
5. **SQLite path**: `sqlite+aiosqlite:///./myapp.db` uses relative path. systemd WorkingDirectory determines where the .db file is created.
6. **CORS must include server IP**: Not just `localhost`. Set `CORS_ORIGINS=["http://SERVER_IP:3009"]` in cloud `.env`.
