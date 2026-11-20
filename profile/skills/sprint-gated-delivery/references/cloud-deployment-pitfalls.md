# Cloud Deployment Pitfalls

## .env Lifecycle
- `tar` upload OVERWRITES cloud .env with local .env
- Local uses PostgreSQL, cloud uses SQLite → asyncpg ModuleNotFoundError
- Fix: `tar --exclude='backend/.env'`, cloud .env created separately
- Cloud .env must be `chmod 600`

## PostgreSQL Setup
- `sudo -u postgres psql -c "CREATE USER myapp WITH PASSWORD 'xxx'"` creates user
- Password must match .env DATABASE_URL exactly
- Verify: `PGPASSWORD=xxx psql -U myapp -d myapp -h localhost -c 'SELECT 1'`
- asyncpg must be installed: `pip install asyncpg`

## Redis Sync vs Async
- FastAPI routes are async but Redis operations should be sync in route handlers
- `import redis` (sync) not `import redis.asyncio as aioredis`
- Each module: `_get_redis()` factory returning sync Redis connection
- Lua scripts for atomic rate limiting: `r.eval(LUA_SCRIPT, 1, key, ...)`

## bcrypt Version Pin
- bcrypt 5.x removed `__about__` module → passlib breaks
- `pip install 'bcrypt==4.0.1'` in requirements.txt

## SQLite/PostgreSQL Dual Compatibility
- JSONB → JSON (SQLAlchemy)
- UUID → custom TypeDecorator with String(36)
- `default=lambda: str(uuid.uuid4())` for SQLite
- PostgreSQL needs `pool_pre_ping=True` for connection health

## systemd Services
- Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8002`
- Frontend: `npm run dev` (Vite+Express)
- Both: `Restart=always`, `RestartSec=5`
- Check: `systemctl status myapp-backend myapp-web`

## Port Planning (coexisting with existing services)
- Existing: 3010 (a legacy service) — DO NOT TOUCH
- New backend: 8002 (FastAPI)
- New frontend: 3009 (Vite+Express)
- PostgreSQL: 5432 (localhost only)
- Redis: 6379 (localhost only)
