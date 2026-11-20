# Full-Stack Development: The Skeleton Trap

## Problem Pattern (validated)

Agent develops "all files" but each file is a skeleton/mock/stub. The delivery looks complete on paper (49 files, 3000 lines) but:
- Frontend pages use MOCK_DATA, setTimeout simulations, hardcoded arrays
- Backend endpoints exist but no frontend component actually calls them
- api.ts defines all API functions but zero components import them
- User judges delivery as failed

## Root Cause

Agent optimizes for file count and code line count rather than end-to-end functionality.

## Prevention Checklist

### Before claiming any feature is "complete":

1. Backend verification: curl the actual endpoint with real data, verify DB write
2. Frontend wiring: grep -rn 'api\.\|API\.' src/components/ — every page must have at least one real API call
3. Mock detection: grep -rn 'setTimeout\|MOCK_\|// Mock' src/components/ — zero mocks allowed
4. End-to-end test: Write a test script that calls API through frontend proxy

### Gate addition — Integration Gate:
- Each "completed" page has real API calls
- No setTimeout/MOCK_ residuals
- Frontend proxy to backend connectivity
- End-to-end test script passes

## Requirements-Feature Audit Pattern

Before claiming "done", dispatch independent Agent to:
1. Read design document site map (part3_features.md)
2. For each feature: check backend router + frontend component + API wiring
3. Output feature comparison table with completion status
4. Calculate actual completion percentage

## Reference Frontend Integration

When user provides reference code (zip/repo):
1. Use the reference code directly — extract and deploy, don't rewrite
2. Keep the same tech stack — if reference uses Vite+Express, don't switch to Next.js
3. Add API proxy — modify server to proxy API calls to backend
4. Minimal changes — only add backend API integration, don't redesign UI

### Express to FastAPI proxy pattern:
import http from "http";
app.use("/api/v1", (req, res) => {
  const proxyReq = http.request({
    hostname: "localhost", port: 8001,
    path: `/api/v1${req.url}`,
    method: req.method, headers: req.headers,
  }, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
    proxyRes.pipe(res);
  });
  req.pipe(proxyReq);
});

## Port Management

- Always check port availability: lsof -i :PORT
- Default: backend 8001, frontend 3009 (avoid 3000/3001/3002)
