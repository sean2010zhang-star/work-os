# Redis Architecture Pattern (validated)

## Three-DB Isolation
- db0: Rate limiting (general 100/min, AI 20/min)
- db1: Login lock (5 attempts/5 min)
- db2: JWT token blacklist

## Sync Redis Factory Pattern
```python
# Each module gets its own factory function
def _get_redis():
    try:
        import redis
        return redis.Redis(host="localhost", port=6379, db=N, decode_responses=True)
    except Exception:
        return None
```

## Atomic Rate Limiting (Lua Script)
```lua
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
Usage: `r.eval(LUA, 1, key, str(limit), str(window))`

## Login Guard Pattern
- `login_attempts:{phone}` — counter, expires in 300s
- `login_lock:{phone}` — lock flag, expires in 300s
- On failure: incr attempts → if >= 5: set lock, delete attempts
- On success: delete attempts + lock
- On check: if lock exists → 429

## JWT Blacklist Pattern
- `blacklist:{token}` — exists = blacklisted, TTL = token remaining lifetime
- On logout: `setex(key, ttl, "1")`
- On verify: `exists(key) > 0`
- Fallback: if Redis down → allow (conservative for availability)

## Anti-Pattern: Async Redis in Sync Routes
- `import redis.asyncio as aioredis` in sync FastAPI route → returns coroutine
- `r.get(key)` returns `<coroutine ...>` not the value
- Fix: Always use `import redis` (sync) in route handlers
