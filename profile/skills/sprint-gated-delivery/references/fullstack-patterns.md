# Full-Stack Development Patterns (FastAPI + React/Vite)

## Project Structure Pattern

```
project/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + router registration
│   │   ├── config.py         # Pydantic Settings
│   │   ├── database.py       # SQLAlchemy async engine
│   │   ├── common/
│   │   │   ├── security.py   # JWT + bcrypt
│   │   │   ├── deps.py       # Auth dependencies
│   │   │   ├── usage.py      # Rate limiting (atomic)
│   │   │   ├── quota.py      # Quota query
│   │   │   └── response.py   # Unified response format
│   │   ├── ai_engine/
│   │   │   └── base.py       # LLM engine (mock fallback + sanitize)
│   │   ├── models/           # SQLAlchemy models (one per file)
│   │   ├── auth/             # router + schemas
│   │   ├── resume/           # router + schemas + optimize + version
│   │   ├── experiment/       # router + schemas + city_salary + trends + report
│   │   ├── interview/        # router + schemas + question_bank + progress
│   │   ├── job/              # router + schemas + enhanced + match
│   │   ├── student/          # router + schemas
│   │   ├── learning/         # router + engine
│   │   ├── community/        # router + qa
│   │   └── admin/            # router + content
│   ├── requirements.txt
│   └── .env
├── web/
│   ├── server.ts             # Express + Vite + proxy
│   ├── src/
│   │   ├── App.tsx           # Main app with tab routing
│   │   ├── components/       # One file per page
│   │   ├── services/api.ts   # Axios API layer
│   │   ├── types/index.ts    # TypeScript types
│   │   └── store/index.ts    # Zustand state
│   └── package.json
└── shared/
    └── constants.py          # Shared between frontend/backend
```

## Key Patterns

### Module Registration (main.py)
Each module must be registered in 3 places:
1. Import the router
2. `app.include_router(router, prefix="/api/v1/xxx", tags=["xxx"])`
3. Add to `/api/v1/modules` response

### UUID Validation Pattern
```python
import uuid as uuid_mod
try:
    uuid_mod.UUID(id_string)
except ValueError:
    raise HTTPException(status_code=400, detail="Invalid ID format")
```
Must be called BEFORE any database query.

### Pydantic UUID Serialization
```python
from pydantic import field_validator

class MyResponse(BaseModel):
    id: str

    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v else ""
```

### AI Mock Fallback Pattern
When no API key is configured, return structured mock data:
```python
if not self.api_key:
    return self._mock_response(messages)
```
Mock responses must match the expected JSON schema exactly.

### Frontend API Service Pattern
```typescript
const api = axios.create({ baseURL: "/api/v1", timeout: 60000 });

// Attach token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/";
    }
    return Promise.reject(err);
  }
);
```

### CRUD Module Template
Each business module follows:
1. `router.py` - API endpoints with `Depends(get_current_user)`
2. `schemas.py` - Pydantic request/response models
3. `__init__.py` - Empty
4. Optional: `engine.py` for AI logic, `enhanced.py` for extra endpoints
