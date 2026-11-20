# 前后端打通验证模式（防骨架交付）

来源: 典型反例 — Sprint 级 Gate 全 PASS，但端到端打通率不足一半。

## 问题根因

Gate 1只检查文件存在，Gate 2只检查语法通过，没有验证"前端是否真正调用了后端"。
结果：前端用setTimeout/MOCK_常量模拟API返回，用户看到的是假功能。

## 检测命令

```bash
# 后端真实DB操作（有输出=有真实逻辑 ✅）
grep -rn 'db.execute\|db.add\|db.query\|session.query' app/

# 前端真实API调用（有输出=有真实调用 ✅）
grep -rn 'api\.\|API\.\|fetch(' src/components/

# mock数据残留（有输出=骨架交付 ❌）
grep -rn 'setTimeout\|MOCK_\|// Mock' src/components/

# 端到端链路
curl -X POST http://localhost:PORT/api/xxx -d '{...}'
```

## 判定矩阵

| 后端API | 前端页面 | 前端调真实API | 判定 |
|---------|---------|--------------|------|
| ✅ | ✅ | ✅ | 打通 ✅ |
| ✅ | ✅ | ❌ (mock) | 骨架交付 ❌ |
| ✅ | ❌ | — | 未打通 ❌ |
| ❌ | ❌ | — | 未实现 ❌ |

## 集成到Gate验证

Gate 2增强检查清单：
```
[ ] grep -r "setTimeout.*Mock" frontend/ → 不应存在
[ ] grep -r "MOCK_" frontend/ → 不应存在
[ ] 每个router的CRUD有db.execute → 真实DB
[ ] 前端每个页面有import { API } → 真实API调用
[ ] python3 test_full.py → 全部PASS
```

## 间接API调用模式（AuthContext/Provider模式）

**集成审计典型案例**: LoginPage/RegisterPage显示"无API调用"，但实际通过AuthContext间接调用了authAPI。直接grep `api.` 会误报。

正确检测逻辑：
```
1. 页面直接import api → 直接调用 ✅
2. 页面import useAuth/AuthContext → 间接调用 ✅ (通过context)
3. 页面无api import也无context → 真正缺失 ❌
```

检测命令（含间接调用）：
```bash
# 直接API调用
grep -rn 'api\.\|API\.\|fetch(' src/pages/*.tsx

# 间接API调用（通过AuthContext/useAuth）
grep -rn 'useAuth\|AuthContext' src/pages/*.tsx

# 真正无API调用的页面（两者都没有）
for f in src/pages/*.tsx; do
  if ! grep -q 'api\.\|API\.\|fetch(\|useAuth\|AuthContext' "$f"; then
    echo "NO_API: $f"
  fi
done
```

## 骨架交付的典型模式

- ❌ 前端组件用setTimeout模拟AI响应
- ❌ api.ts定义了但组件不用
- ❌ 后端有API但前端无对应页面
- ❌ 新建模块全项目零import零调用（死代码）
- ❌ 只创建router.py但不注册到main.py（端点不可达）
- ❌ 前后端API路径不匹配（如前端/decision-helper vs 后端/decision）
