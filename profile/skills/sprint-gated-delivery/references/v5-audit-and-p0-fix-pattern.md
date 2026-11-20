# V5 Audit → P0 Fix → P1 Refactor → Test Pattern

## Pattern: Post-Audit Iterative Fix

After Agent Team audit identifies issues, fix in priority order:

### Phase 1: P0 Fixes (blocking)
1. **Auth restoration** — Replace `user=None` with `Depends(get_current_user)`
2. **Real LLM connection** — Create async adapter, connect to existing llm_client
3. **DB persistence** — Replace in-memory `_experiments = {}` with SQLAlchemy model
4. **Frontend logic** — Replace `Math.random()` with score-based threshold
5. **Real data modules** — Connect report helpers to actual service modules

### Phase 2: P1 Refactoring (quality)
1. **DRY violations** — Extract shared functions to common/utils.py
2. **Dead code** — Remove unused imports and functions
3. **UI fixes** — SVG label truncation, click-outside handlers

### Phase 3: Tests + Docs
1. **Unit tests** — Engine modules with mock LLM
2. **API tests** — Endpoint tests with pytest-asyncio
3. **Documentation** — API docs with request/response examples

## Key Pitfalls

### Async LLM in FastAPI
```python
# WRONG: sync wrapper creates new event loop → deadlock
def create_llm_fn():
    def llm_fn(prompt):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(call_llm_json(prompt))
    return llm_fn

# RIGHT: async function called with await
def create_async_llm_fn():
    async def async_llm_fn(prompt):
        return await call_llm_json(prompt)
    return async_llm_fn
```

### Database Session Naming
```python
# WRONG: check actual name in database.py
from app.core.database import AsyncSessionLocal  # may not exist

# RIGHT: check actual export
from app.core.database import async_session  # actual name
```

### Mock LLM Keyword Matching
When mock LLM checks prompt keywords, Chinese prompts may not match English keywords. Add Chinese equivalents:
```python
if "假设" in combined or "分析师" in combined:  # Chinese
    return {"hypotheses": MOCK_HYPOTHESES}
```

### Frontend Type Imports
```typescript
// WRONG: type-only imports as values
import { UserType, Tier } from "./types/v5";

// RIGHT: use import type
import type { UserType, Tier } from "./types/v5";
```

### Mock Data Field Names
Mock data must match the actual interface. If interface expects `name`, don't use `title`:
```typescript
// WRONG
{ title: "路径名", match_score: 85 }
// RIGHT  
{ name: "路径名", total_score: 85 }
```

## Testing Pattern

### conftest.py for Auth Tests
```python
@pytest_asyncio.fixture
async def test_user(db_session):
    """Create test user in DB, return user dict."""
    user = User(email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return {"id": user.id, "email": user.email}

@pytest_asyncio.fixture
async def auth_token(test_user):
    """Token must use user ID, not email."""
    return create_access_token(data={"sub": str(test_user["id"])})
```

### MOCK_LLM for Tests
```bash
MOCK_LLM=true pytest tests/ -v
```

## Session Stats
- 25 files changed, +824/-265 lines
- 53 tests (40 engine + 13 API), all passing
- Quality: 6/10 → 8.5/10 after fixes
