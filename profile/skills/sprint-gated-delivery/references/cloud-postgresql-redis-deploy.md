# Cloud PostgreSQL + Redis Deployment Pattern

## Overview
Deploying a FastAPI backend with PostgreSQL + Redis on a lightweight cloud server (3.3GB RAM) alongside existing services.

## PostgreSQL Setup

```bash
# Install
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable postgresql && sudo systemctl start postgresql

# Create user and database
sudo -u postgres psql -c "CREATE USER myapp WITH PASSWORD 'strong_password_here';"
sudo -u postgres psql -c "CREATE DATABASE myapp OWNER myapp;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE myapp TO myapp;"

# Verify
PGPASSWORD=strong_password_here psql -U myapp -d myapp -h localhost -c "SELECT 1;"
```

## Redis Setup

```bash
sudo apt-get install -y redis-server
sudo systemctl enable redis-server && sudo systemctl start redis-server
redis-cli ping  # should return PONG
```

## Redis Three-DB Isolation Pattern

| DB | Purpose | Key Pattern |
|----|---------|-------------|
| 0  | Rate limiting | `rl:{ip}:{type}` |
| 1  | Login guard | `login_lock:{phone}`, `login_attempts:{phone}` |
| 2  | JWT blacklist | `blacklist:{token}` |

## Redis Connection Factory (redis_pool.py)

```python
import redis
from app.config import settings

_pools: dict = {}

def get_redis(db: int = 0) -> redis.Redis:
    if db not in _pools:
        _pools[db] = redis.from_url(
            settings.REDIS_URL, db=db, decode_responses=True,
            socket_timeout=5, socket_connect_timeout=5,
        )
        _pools[db].ping()
    return _pools[db]
```

## Rate Limiting with Lua Script (Atomic)

```lua
-- RATE_LIMIT_LUA
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end
if current > limit then
    return 0
end
return 1
```

Usage: `r.eval(RATE_LIMIT_LUA, 1, key, str(max_req), str(window))`

## Login Guard Pattern

```python
def check_login_allowed(phone: str) -> None:
    r = get_login_redis()
    lock = r.get(f"login_lock:{phone}")
    if lock:
        raise HTTPException(429, f"Too many attempts, try {lock}s later")

def record_login_failure(phone: str) -> None:
    r = get_login_redis()
    attempts = r.incr(f"login_attempts:{phone}")
    r.expire(f"login_attempts:{phone}", 300)
    if attempts >= 5:
        r.setex(f"login_lock:{phone}", 300, "300")
        r.delete(f"login_attempts:{phone}")
```

## JWT Blacklist (fail-closed)

```python
def is_token_blacklisted(token: str) -> bool:
    try:
        r = get_blacklist_redis()
        return r.exists(f"blacklist:{token}") > 0
    except Exception:
        return True  # fail-closed: Redis down = reject
```

## UUID Type Compatibility (SQLite/PostgreSQL)

```python
import uuid
from sqlalchemy import String, TypeDecorator

class UUID(TypeDecorator):
    impl = String(36)
    cache_ok = True
    def process_bind_param(self, value, dialect):
        return str(value) if value else value
    def process_result_value(self, value, dialect):
        try: return uuid.UUID(value)
        except: return value
```

## systemd Service Template

```ini
[Unit]
Description=<app> Backend
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/myapp/backend
ExecStart=/home/ubuntu/myapp/backend/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

## .env Template (Production)

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<random 32+ hex chars>
JWT_SECRET=<random 32+ hex chars>
DEBUG=false
ENVIRONMENT=production
CORS_ORIGINS=["http://your-domain:port"]
```

**CRITICAL:** Generate random keys with `openssl rand -hex 32`. Never use default values.

## Port Planning (Coexistence)

```
Existing service:  3010 (don't touch)
New backend:       8002
New frontend:      3009
PostgreSQL:        5432 (localhost only)
Redis:             6379 (localhost only)
```

## .env Lifecycle Rule

**tar upload overwrites cloud .env!** Always exclude:
```bash
tar czf backend.tar.gz --exclude='backend/.env' backend/
```
Cloud .env must be created/managed separately with production credentials.
