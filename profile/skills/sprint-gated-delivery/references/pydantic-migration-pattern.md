# Dict → Pydantic Schema Migration Pattern (validated)

## The Problem
Routes with `data: dict` allow arbitrary input, no validation, no OpenAPI docs.
When changed to `data: PydanticModel`, `data.get("key")` crashes with AttributeError.

## Migration Steps
1. Create Pydantic schema with Field constraints
2. Change function signature from `data: dict` to `data: MySchema`
3. Replace ALL `data.get("key")` with `data.key` in function body
4. Replace ALL `data["key"]` with `data.key`
5. Replace ALL `req.get("key")` with `data.key` (unify param name to `data`)
6. Verify: `grep -n '\.get(' router.py` should return 0 hits for request params

## Example Schema
```python
from pydantic import BaseModel, Field

class CityRecommendRequest(BaseModel):
    industry: str = Field(..., min_length=1, max_length=100)
    job: str = Field(default="", max_length=100)
    preferences: dict = Field(default_factory=dict)
```

## Error Handler Decorator
```python
# app/common/error_handler.py
import functools, logging
from fastapi import HTTPException
logger = logging.getLogger(__name__)

def handle_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"{func.__name__} failed: {type(e).__name__}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper
```

## Common Pitfalls
- Parameter name inconsistency: some functions use `data`, others `req` → unify to `data`
- Inline `import logging` in error handlers → move to module top
- `except Exception as e: return {"error": str(e)}` → use @handle_errors + HTTPException
