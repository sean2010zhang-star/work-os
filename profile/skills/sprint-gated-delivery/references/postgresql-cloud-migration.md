# PostgreSQL云迁移+Redis部署实战 (实测)

## PostgreSQL密码一致性

本地.env的DATABASE_URL含`myapp:myapp`，云端PostgreSQL用`myapp:myapp2026`。
tar打包时.env被覆盖→asyncpg找不到→启动失败。

**修复:** 本地和云端统一密码，或tar时`--exclude='backend/.env'`。

## SQLite→PostgreSQL迁移清单

| 问题 | 修复 |
|------|------|
| JSONB不支持 | → JSON (SQLite兼容) |
| UUID类型 | 自定义TypeDecorator: String(36)兼容双库 |
| datetime.utcnow() | → datetime.now(timezone.utc).replace(tzinfo=None) |
| bcrypt 5.x不兼容passlib | pin `bcrypt==4.0.1` |
| asyncpg缺失 | `pip install asyncpg` |

## Redis同步/异步混用

FastAPI是async框架，但rate_limit/login_guard用同步redis.Redis。
同步短操作可接受(keys/get/setex)，但不要在async函数中调用阻塞操作(keys/scan)。
AI引擎用httpx.AsyncClient(异步)。

## 云端.env生命周期

- tar打包时排除.env: `--exclude='backend/.env'`
- 云端单独创建.env，用`openssl rand -hex 32`生成密钥
- `chmod 600 .env`
- 部署后验证: `curl http://localhost:8002/health`
- 验证DB: `sudo -u postgres psql -d myapp -c '\\dt'`
