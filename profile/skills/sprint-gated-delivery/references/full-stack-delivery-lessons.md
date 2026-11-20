# Full-Stack Product Delivery Lessons

## Core Delivery Rules

### Skeleton/Mock is NOT Delivery
Delivering stubs with setTimeout/mock data is a DELIVERY FAILURE. Every feature needs:
- Backend API with real logic
- Frontend calling real API (not mock)
- End-to-end pass
The user audits against design doc feature-by-feature. If the audit shows 47% completion, the delivery has failed.

### Frontend Must Match Reference
When user provides reference frontend code (zip file), must fully align:
- Color scheme, layout, component style
- Brand name / subtitle / footer
- Page order follows story flow (not random)
- Tabs connected with arrows to imply flow

### Feature Completion = Design Doc Comparison
Count features by comparing against the site map in the design doc, NOT by counting API endpoints.
Mark each: fully implemented / partially / not implemented / explicitly deferred.

### main.py Bloat Anti-Pattern
When inline routes exceed 10, migrate to module router.py files.
main.py should only have: init + router registration + health check (<100 lines).
(refactor example: 390→79 lines)

### Express Proxy to FastAPI
When frontend uses Vite + Express server.ts:
- Use fetch proxy for /api/v1/* to FastAPI backend
- Correctly forward headers (Authorization, Content-Type)
- For JSON: stringify req.body; For FormData: pipe through
- Port conflict: change from 3001 to unused port (3009)

### Every Sprint Must Pass Integration Test
After each sprint, run comprehensive endpoint test covering all new + existing endpoints.
Track pass/fail count. 100% pass rate before proceeding.

## Architecture Patterns

### Module Structure (per business domain)
```
module/
├── router.py      # FastAPI router with all endpoints
├── schemas.py     # Pydantic request/response models
├── enhanced.py    # Additional features (optional)
└── engine.py      # Business logic / AI calls (optional)
```

### Common Infrastructure
```
common/
├── security.py    # JWT + bcrypt
├── deps.py        # Auth dependencies
├── usage.py       # Atomic quota check (SQL UPDATE WHERE)
├── quota.py       # Usage query
├── response.py    # Unified response format
└── schemas.py     # BaseResponse, UUIDStr
```

### AI Engine Pattern
- Single LLMEngine class with mock fallback
- sanitize_input() for prompt injection defense (regex, 11+ patterns)
- _extract_json() for robust JSON parsing (3-level: direct → markdown block → regex)
- All AI calls through engine, never direct httpx in routers

## Security Checklist
- [ ] All user inputs validated (Pydantic schemas, not raw dict)
- [ ] JWT + bcrypt auth on all sensitive endpoints
- [ ] File upload: extension whitelist + streaming size check + encoding detection
- [ ] Prompt injection defense on all AI entry points
- [ ] SQL atomic operations for quota (no TOCTOU)
- [ ] Production env validation (SECRET_KEY/JWT_SECRET/DEBUG)
- [ ] Login rate limiting (5 attempts/5 min)
- [ ] CORS: explicit methods + headers (not wildcard)
