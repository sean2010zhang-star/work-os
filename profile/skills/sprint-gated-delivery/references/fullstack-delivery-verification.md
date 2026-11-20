# Full-Stack Delivery Verification Pattern

## Trigger
When building a full-stack application (backend API + frontend UI), the delivery is NOT complete until both sides are connected and working end-to-end.

## Failure Pattern
Built backend APIs (25 endpoints) and frontend pages (14 components) separately, but:
- Frontend used mock/hardcoded data, never called backend APIs
- Resume upload used setTimeout instead of real API
- Experiment results showed MOCK constants instead of API data
- Interview used setTimeout for AI responses
- Result: Agent Team audit found only 45% of design features actually implemented

## Correct Gate Verification Checklist

### Gate 1: Backend API (must ALL pass)
- [ ] Server starts without errors
- [ ] `/health` returns 200
- [ ] Every endpoint returns expected response (curl test)
- [ ] Auth flow works: register → login → token → protected endpoint
- [ ] CRUD operations: create → read → update → delete

### Gate 2: Frontend (must ALL pass)
- [ ] Page renders without console errors
- [ ] Visual style matches reference design (if provided)
- [ ] Port is NOT conflicting with other services
- [ ] All interactive elements have onClick handlers

### Gate 3: Frontend-Backend Integration (must ALL pass)
- [ ] Frontend API service layer calls backend endpoints
- [ ] Registration/login flow works end-to-end
- [ ] File upload works through frontend → backend
- [ ] AI features call backend (not mock data)
- [ ] Error states handled (429 rate limit, 401 auth, 500 server)

### Gate 4: Feature Completeness (must ALL pass)
- [ ] Every feature in design doc has: backend endpoint + frontend component + API call
- [ ] No component uses setTimeout/mock data for core functionality
- [ ] Freemium limits enforced (429 when quota exceeded)
- [ ] AI responses come from backend, not frontend constants

## Proxy Pattern (Vite + FastAPI)
When frontend uses Vite (not Next.js) and backend is separate:

```typescript
// server.ts - Express proxy to FastAPI backend
import http from "http";
app.use("/api/v1", (req, res) => {
  const proxyReq = http.request({
    hostname: "localhost", port: 8001,
    path: `/api/v1${req.url}`, method: req.method, headers: req.headers,
  }, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
    proxyRes.pipe(res);
  });
  proxyReq.on("error", (e) => { res.status(502).json({ error: "Backend unavailable" }); });
  req.pipe(proxyReq);
});
```

This handles multipart/form-data file uploads correctly (unlike fetch-based proxies).

## Port Conflicts
Always check port availability before starting:
```bash
lsof -i :PORT 2>/dev/null | head -3
```
Default ports to avoid: 3000 (common), 3001 (often occupied), 8000 (common).
Safe ports: 3009, 3002, 8001, 8002.

## Reference Frontend Integration
When user provides a reference frontend (zip file):
1. Extract to project directory
2. Install dependencies (npm install)
3. Change port if needed
4. Add proxy middleware to connect to backend
5. Keep all reference components as-is (they define the visual style)
6. Only modify server.ts to add backend proxy
7. Verify visual style matches reference (screenshot comparison)
