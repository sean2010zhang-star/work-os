# 全栈集成测试脚本模式 (实测验证)

## 模式
用Python urllib直接调用API，避免curl的f-string转义问题。
脚本用随机手机号避免额度限制冲突。

```python
import json, urllib.request, urllib.error, random

BASE = "http://localhost:8002/api/v1"
PHONE = f"139{random.randint(10000000,99999999)}"

def api(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return {"error": e.code}, e.code
    except Exception as e:
        return {"error": str(e)[:60]}, 0

# Register fresh user
r, _ = api("POST", "/auth/register", {"phone": PHONE, "password": "test12345678"})
T = r.get("access_token", "")

# Test all endpoints with check function
p, f = 0, 0
def chk(name, ok):
    global p, f
    if ok: p += 1
    else: f += 1

# ... test calls ...
print(f"总计: {p}/{p+f} PASS ({p/(p+f)*100:.0f}%)")
```

## 关键注意事项
1. 手机号必须11位: `f"139{random.randint(10000000,99999999)}"`
2. 密码必须8位+: `"test12345678"`
3. 随机手机号避免不同测试间额度冲突
4. 文件上传需要单独处理(multipart/form-data)
5. 云端测试通过SSH执行脚本: `ssh ubuntu@server 'python3 -c "..."'`
