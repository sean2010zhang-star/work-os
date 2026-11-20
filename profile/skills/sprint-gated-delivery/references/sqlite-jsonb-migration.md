# SQLite JSONB Migration Pattern

## Problem
SQLAlchemy models using `JSONB` from `sqlalchemy.dialects.postgresql` fail on SQLite:
```
sqlalchemy.exc.CompileError: (in table 'users', column 'skills'): 
Compiler SQLiteTypeCompiler can't render element of type JSONB
```

## Solution
Replace all `JSONB` imports with `JSON` from `sqlalchemy`:

### Before (PostgreSQL-only)
```python
from sqlalchemy.dialects.postgresql import UUID, JSONB
```

### After (SQLite + PostgreSQL compatible)
```python
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON as JSONB  # SQLite: JSON, PostgreSQL: JSONB
```

## Batch Fix
```bash
sed -i '' 's/from sqlalchemy.dialects.postgresql import UUID, JSONB/from sqlalchemy.dialects.postgresql import UUID\nfrom sqlalchemy import JSON as JSONB/g' app/models/*.py
```

## Verified: production deployment deployment
- 6 model files updated (user/resume/experiment/interview/job/subscription)
- SQLite auto-creates tables with JSON type
- PostgreSQL still uses JSONB when deployed there
- No functional difference for CRUD operations

## Requirements
- `aiosqlite==0.20.0` in requirements.txt for async SQLite
- `sqlite+aiosqlite:///./myapp.db` as DATABASE_URL
