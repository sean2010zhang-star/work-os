# SQLite UUID Compatibility Pattern

## Problem
SQLAlchemy models using `UUID(as_uuid=True)` from `sqlalchemy.dialects.postgresql` fail on SQLite:
```
'str' object has no attribute 'hex'
```

## Solution: Custom UUID TypeDecorator

Create `common/types.py`:
```python
import uuid
from sqlalchemy import String, TypeDecorator

class UUID(TypeDecorator):
    impl = String(36)
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value) if dialect.name != "sqlite" else value
        return value
```

In all models: `from app.common.types import UUID` (replace `from sqlalchemy.dialects.postgresql import UUID`)

Also fix defaults: `default=lambda: str(uuid.uuid4())` (not `default=uuid.uuid4`)

## Combined with JSONB fix
Models need BOTH fixes for SQLite:
1. `UUID` from `app.common.types` (not postgresql dialect)
2. `JSON` from `sqlalchemy` (not `JSONB` from postgresql dialect)

## Verified: production deployment(Ubuntu, Python 3.10)
