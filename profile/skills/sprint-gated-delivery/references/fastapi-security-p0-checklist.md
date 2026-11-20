# FastAPI Security P0 Checklist — 实测验证

## 14项P0安全/稳定性问题（按修复优先级排序）

### 1. 批量赋值漏洞
**症状**: `setattr(user, field, value)` 遍历用户输入的所有字段，攻击者可提交 `{"role":"ADMIN","tier":"PREMIUM"}` 提权。
**修复**: 白名单字段赋值 `ALLOWED_FIELDS = {"nickname", "avatar_url", ...}` + `if field in ALLOWED_FIELDS: setattr(...)`
**文件**: auth/router.py update_profile

### 2. AI Prompt注入未全覆盖
**症状**: _sanitize()只在部分入口调用，其他入口的用户输入直接拼入prompt。
**修复**: 列出所有llm_engine调用点，逐一确认输入经过_sanitize。
**检查**: `grep -rn "llm_engine" app/ | grep -v "_sanitize"` 找到所有未保护的调用。

### 3. 文件上传先读后检
**症状**: `await file.read()` 全量读入内存后才判断大小，大文件可OOM。
**修复**: 流式分块读取 + 实时大小检查。
```python
content = b""
while True:
    chunk = await file.read(1024 * 1024)  # 1MB
    if not chunk: break
    content += chunk
    if len(content) > MAX_SIZE:
        raise HTTPException(413, "File too large")
```

### 4. TOCTOU竞态（额度检查非原子）
**症状**: 先检查usage < limit，再usage += 1，并发请求可绕过。
**修复**: 使用`check_and_increment_usage()`统一函数。注意：ORM层setattr+flush不是真正的数据库原子操作，生产环境需要SQL级`UPDATE SET usage = usage + 1 WHERE usage < limit`。

### 5. 不安全默认配置
**症状**: SECRET_KEY="change-me-in-production"，DEBUG=True。
**修复**: 生产环境启动校验 + 开发环境使用强随机默认值。
```python
if os.environ.get("ENVIRONMENT") == "production":
    if settings.SECRET_KEY.startswith("pl-dev-"):
        raise RuntimeError("FATAL: SECRET_KEY must be set in production")
```

### 6. JWT异常处理过于宽泛
**症状**: `except Exception` 捕获所有异常，掩盖编程错误。
**修复**: 分层捕获 `jwt.ExpiredSignatureError` / `jwt.InvalidTokenError` / `Exception`。

### 7. LLM JSON解析不健壮
**症状**: LLM返回```json...```包裹的JSON时json.loads失败。
**修复**: 三级解析：直接json.loads → 正则提取代码块 → 正则提取首个JSON对象。
```python
@staticmethod
def _extract_json(text: str) -> dict:
    try: return json.loads(text)
    except: pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try: return json.loads(match.group(1))
        except: pass
    return {"error": "parse_failed", "detail": "Please try again"}  # 不返回raw给客户端
```

### 8. 登录暴力破解无防护
**修复**: 内存计数器(5次/5分钟)，生产用Redis滑动窗口。

### 9. 密码策略过弱
**修复**: 注册min_length=8 + 手机号正则`^1[3-9]\d{9}$`。LoginRequest的约束必须与RegisterRequest一致。

### 10. CORS过于宽松
**症状**: `allow_methods=["*"]` + `allow_headers=["*"]`
**修复**: 显式列出 `allow_methods=["GET","POST","PUT","DELETE"]` + `allow_headers=["Authorization","Content-Type"]`

### 11. LLM原始响应泄露
**症状**: `_extract_json`失败时返回`{"raw": text[:500]}`给客户端，可能含prompt残余。
**修复**: 返回`{"error": "AI response parsing failed", "detail": "Please try again"}`，raw只记录日志。

### 12. 编码检测级联
**症状**: `content.decode("utf-8", errors="ignore")` 静默丢弃非UTF-8字符。
**修复**: UTF-8 → GBK → UTF-8(errors="replace") 三级降级。

### 13. UUID校验顺序
**症状**: UUID校验在DB查询之后，无效UUID会触发DB层错误。
**修复**: `_validate_uuid(id_str)` 在DB查询之前调用。

### 14. datetime时区不一致
**症状**: `datetime.now(timezone.utc)` (aware) 与 `datetime.utcnow()` (naive) 混用导致 `TypeError: can't subtract offset-naive and offset-aware datetimes`。
**修复**: 统一使用naive datetime（与SQLAlchemy模型default一致）。

## 反模式清单

| 反模式 | 症状 | 预防 |
|--------|------|------|
| 修复未集成 | 创建utility模块但未import | grep确认新模块被外部import |
| 旧代码残留 | NameError引用已移除变量 | patch后read_file确认目标区域 |
| null字节 | SyntaxError: source code string cannot contain null bytes | write_file后py_compile验证 |
| mock关键词冲突 | prompt中"score"触发错误的mock分支 | 具体关键词优先，组合条件替代单一词 |
| 审计分不升反降 | 声称修复但审计Agent未检测到改善 | 每轮修复后重跑审计验证 |
