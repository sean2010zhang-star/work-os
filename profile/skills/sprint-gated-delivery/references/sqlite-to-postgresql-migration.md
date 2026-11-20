# SQLite → PostgreSQL Migration Pattern (validated)

## Database Types Module
```python
# app/common/types.py
import uuid
from sqlalchemy import String, TypeDecorator, JSON

class UUID(TypeDecorator):
    impl = String(36)
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value) if isinstance(value, uuid.UUID) else str(value)
        return value
    def process_result_value(self, value, dialect):
        if value is not None:
            try: return uuid.UUID(value)
            except (ValueError, AttributeError): return value
        return value
```

## Model Pattern
```python
from app.common.types import UUID
import uuid

class MyModel(Base):
    id = Column(UUID(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data = Column(JSON, default=dict)  # JSON not JSONB for SQLite compat
```

## database.py Dual Mode
```python
is_sqlite = "sqlite" in settings.DATABASE_URL
if is_sqlite:
    engine = create_async_engine(url, connect_args={"check_same_thread": False})
else:
    engine = create_async_engine(url, pool_size=20, max_overflow=10, pool_pre_ping=True)
```

## Pydantic Schema UUID Handling
```python
class MyResponse(BaseModel):
    id: str
    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v) if v else ""
    class Config:
        from_attributes = True
```

## Migration Checklist
1. Replace JSONB → JSON in all models
2. Replace `from sqlalchemy.dialects.postgresql import UUID` → `from app.common.types import UUID`
3. Replace `UUID(as_uuid=True)` → `UUID(36)`
4. Replace `default=uuid.uuid4` → `default=lambda: str(uuid.uuid4())`
5. Add `pool_pre_ping=True` for PostgreSQL
6. Install asyncpg: `pip install asyncpg`
7. Verify with `SELECT 1` before starting service
