# Full-Stack Delivery Pitfalls (实测)

## bcrypt 5.x + passlib incompatibility

**Symptom:** `AttributeError: module 'bcrypt' has no attribute '__about__'` on register/login.
**Cause:** bcrypt 5.0 removed `__about__` module that passlib 1.7.x relies on.
**Fix:** `pip install 'bcrypt==4.0.1'`
**Pin in requirements.txt:** `bcrypt==4.0.1`

## Pydantic v2 UUID/Enum serialization from SQLAlchemy

**Symptom:** API returns `null` for fields that have data (User.id, User.tier, etc.)
**Cause:** Pydantic v2's `from_attributes=True` doesn't auto-convert UUID→str or Enum→str.
**Fix:** Add `@field_validator("id", mode="before")` for UUID fields and `@field_validator("tier", mode="before")` for Enum fields:
```python
@field_validator("id", mode="before")
@classmethod
def uuid_to_str(cls, v):
    return str(v) if v else ""

@field_validator("tier", mode="before")
@classmethod
def enum_to_str(cls, v):
    return v.value if hasattr(v, "value") else str(v)
```
**Pattern:** Every schema that reads from a SQLAlchemy model with UUID/Enum fields needs these validators.

## Frontend "connected to API" vs "mock data" detection

**Wrong approach:** Each component has its own mock data with setTimeout.
**Right approach:** All components call api.ts service layer → backend returns real data.
**Detection command:** `grep -rn 'setTimeout\|MOCK_\|// Mock' web/src/components/`
If output is non-empty, frontend is NOT connected to backend.

## LLM mock fallback pattern

**Problem:** No API key → all AI endpoints crash with connection errors.
**Solution:** In LLMEngine.chat(), check `if not self.api_key: return self._mock_response(messages)`.
Mock responses should return valid JSON matching the expected schema, not placeholder text.
This allows the full system to be demoed/tested without LLM API key.

## models/__init__.py must explicitly import all models

**Symptom:** `create_all()` doesn't create tables for some models.
**Cause:** SQLAlchemy only knows about models that are imported before `create_all()`.
**Fix:** In `models/__init__.py`, explicitly import every model class:
```python
from app.models.user import User
from app.models.resume import Resume, ResumeDiagnosis
# ... etc
```

## f-string with JSON curly braces

**Symptom:** `SyntaxError: f-string: single '}' is not allowed`
**Cause:** JSON `{"key": "value"}` inside f-string conflicts with Python's `{expression}` syntax.
**Fix:** Build JSON string outside f-string, then inject via variable. Or use `{{` and `}}` for literal braces.
**Better fix:** Don't use f-strings for JSON-heavy prompts. Use `.format()` or string concatenation.

## bare except catches KeyboardInterrupt/SystemExit

**Wrong:** `except:` 
**Right:** `except (json.JSONDecodeError, Exception):`
bare except in 3 places was flagged as P0 by Agent Team audit.
