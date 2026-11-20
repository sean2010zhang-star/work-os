# Redis-Backed Security Infrastructure Pattern

**来源**: 云端部署场景 (实测)
**场景**: 腾讯云3.3GB RAM服务器，需要持久化限流/登录保护/Token管理

## Redis DB隔离

```
db0: 限流 (rate_limit.py)      - INCR+EXPIRE 滑动窗口
db1: 登录锁定 (login_guard.py) - 5次失败→5分钟锁
db2: Token黑名单 (token_blacklist.py) - logout后token失效
```

## 限流模式 (rate_limit.py)

```python
# Redis滑动窗口
key = f"rl:{client_ip}:{'ai' if is_ai else 'general'}"
current = r.incr(key)
if current == 1:
    r.expire(key, RATE_LIMIT_WINDOW)
if current > max_req:
    raise HTTPException(status_code=429)

# 降级到内存
except Exception:
    _memory_store[key] = [t for t in _memory_store[key] if now - t < window]
```

配置: 通用100/min, AI端点20/min

## 登录锁定模式 (login_guard.py)

```python
# Redis: 5次失败→锁5分钟
key = f"login_attempts:{phone}"
attempts = r.incr(key)
r.expire(key, LOCKOUT_SECONDS)
if attempts >= MAX_ATTEMPTS:
    r.setex(f"login_lock:{phone}", LOCKOUT_SECONDS, "1")
    r.delete(key)

# 检查锁定
lock = r.get(f"login_lock:{phone}")
if lock: raise HTTPException(429)
```

## JWT黑名单模式 (token_blacklist.py)

```python
# 加入黑名单
r.setex(f"blacklist:{token}", expires_in, "1")

# 检查黑名单 (在deps.py的get_current_user中)
if is_token_blacklisted(token):
    raise HTTPException(401, "Token已失效")
```

## Pitfalls

- **Redis不可用时安全缺口**: token_blacklist在Redis异常时返回False(放行)，已注销token仍可用。保守策略应返回True(拒绝)但会导致所有token失效。
- **INCR+EXPIRE非原子**: 极端情况下key无TTL导致内存泄漏。生产应用Lua脚本或pipeline。
- **每个模块各自创建Redis连接**: rate_limit/login_guard/token_blacklist各维护全局连接，应抽取为common/redis.py统一管理。
- **内存fallback无清理**: _memory_store只增不减，长时间运行内存膨胀。应用LRU cache或定期清理。

## 审计评分影响

Redis部署后安全分从6.5提升到7.5 (+1.0)，主要因为:
- 登录限流从内存→Redis (持久化)
- Token黑名单 (logout生效)
- 限流区分AI/普通端点
