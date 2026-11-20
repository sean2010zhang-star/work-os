# Alembic + Async SQLAlchemy 配置模式

> 验证: PostgreSQL+asyncpg

## 初始化步骤
```bash
cd backend/
pip install alembic
python3 -m alembic init alembic
```

## env.py 关键配置 (同步执行)
```python
from sqlalchemy import engine_from_config, pool
from app.config import settings

# 转为同步驱动
sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
config.set_main_option("sqlalchemy.url", sync_url)

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
```

## 关键陷阱
1. **SQLite不能用async引擎**: `async_engine_from_config` + `psycopg2` 会报 "async driver required"
2. **render_as_batch=True**: SQLite不支持ALTER TABLE, 必须用batch模式(创建新表→复制→删除旧表)
3. **数据库URL覆盖**: alembic.ini中的URL会被env.py中的`config.set_main_option`覆盖
4. **stamp head**: 已有数据库用`create_all`创建的表, 需要`alembic stamp head`标记为已迁移
5. **模型导入**: env.py必须`import app.models`确保所有模型注册到metadata

## main.py中的共存
```python
# 保留create_all作为开发环境fallback
# 生产环境应使用 alembic upgrade head
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

## 迁移命令
```bash
alembic revision --autogenerate -m "描述"  # 生成迁移
alembic upgrade head                         # 执行迁移
alembic stamp head                           # 标记当前状态
alembic history                              # 查看历史
```
