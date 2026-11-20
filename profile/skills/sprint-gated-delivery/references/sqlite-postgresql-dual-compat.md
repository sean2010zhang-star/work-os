# SQLite/PostgreSQL双兼容模式 (实测验证)

## UUID类型兼容
PostgreSQL UUID方言在SQLite上报错。自定义TypeDecorator：

```python
import uuid
from sqlalchemy import String, TypeDecorator

class UUID(TypeDecorator):
    impl = String(36)
    cache_ok = True
    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value) if isinstance(value, uuid.UUID) else str(value)
        return value
    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value) if dialect.name != "sqlite" else value
        return value
```

使用: `from app.common.types import UUID` 替代 `from sqlalchemy.dialects.postgresql import UUID`
模型: `id = Column(UUID(36), primary_key=True, default=lambda: str(uuid.uuid4()))`

## JSONB→JSON兼容
`JSONB`类型在SQLite上不支持。统一用`from sqlalchemy import JSON`。

## config.py双数据库支持
```python
DATABASE_URL: str = "sqlite+aiosqlite:///./myapp.db"  # 默认SQLite
# 生产: postgresql+asyncpg://user:pass@host:5432/dbname
```

database.py根据URL选择引擎：
```python
if "sqlite" in settings.DATABASE_URL:
    engine = create_async_engine(url, connect_args={"check_same_thread": False})
else:
    engine = create_async_engine(url, pool_size=20, max_overflow=10)
```

## 部署注意事项
- SQLite: 零配置，适合MVP/单机
- PostgreSQL: 需安装+创建用户+数据库
- 切换只需改DATABASE_URL环境变量
- JSONB→JSON是单向的，PG原生支持JSONB更好
