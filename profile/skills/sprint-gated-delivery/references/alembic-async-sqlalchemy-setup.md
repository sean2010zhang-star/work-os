# Alembic + SQLAlchemy 异步项目迁移指南 (实测)

## 场景
项目用`Base.metadata.create_all`创建表，需要迁移到alembic做版本化迁移。

## 核心陷阱: 同步vs异步

alembic的autogenerate/upgrade需要**同步**数据库连接。
项目如果用async SQLAlchemy(`create_async_engine`)，必须在env.py中转为同步驱动。

```python
# 正确: env.py用同步引擎
from sqlalchemy import engine_from_config, pool

db_url = settings.DATABASE_URL  # e.g. "postgresql+asyncpg://..." or "sqlite+aiosqlite:///..."
sync_url = db_url.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")

connectable = engine_from_config(
    config.get_section(config.config_ini_section, {}),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
)
```

```python
# 错误: 用async引擎会导致 "psycopg2 is not async" 错误
from sqlalchemy.ext.asyncio import async_engine_from_config
connectable = async_engine_from_config(...)  # ❌ 不要用这个
```

## SQLite特殊处理

SQLite不支持事务性DDL(ALTER TABLE)，必须用batch模式:

```python
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=True,  # SQLite必须
)
```

## 初始化步骤

```bash
cd backend/
pip install alembic

# 1. 初始化
alembic init alembic

# 2. 编辑 alembic.ini: 清空sqlalchemy.url (在env.py中动态设置)
# sqlalchemy.url =

# 3. 编辑 alembic/env.py:
#    - import app.models (注册所有表到metadata)
#    - 从app.config.settings读取DATABASE_URL
#    - 转为同步驱动
#    - render_as_batch=True

# 4. 生成初始migration
alembic revision --autogenerate -m "initial_schema"

# 5. 标记现有数据库为head (因为create_all已创建了表)
alembic stamp head

# 6. 后续schema变更
alembic revision --autogenerate -m "描述变更"
alembic upgrade head
```

## env.py完整模板

```python
"""
Alembic env.py - SQLAlchemy迁移支持
兼容SQLite和PostgreSQL, 同步执行
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.database import Base
import app.models  # noqa: F401 - 注册所有模型
target_metadata = Base.metadata

from app.config import settings
db_url = settings.DATABASE_URL
sync_url = db_url.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## main.py集成

保留`create_all`作为开发环境fallback，生产环境用`alembic upgrade head`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 生产环境应使用 alembic upgrade head
    # 保留 create_all 作为开发环境fallback
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
```

## .gitignore

```gitignore
# Alembic版本文件可选择性忽略
alembic/versions/*.py
!alembic/versions/.gitkeep
```
