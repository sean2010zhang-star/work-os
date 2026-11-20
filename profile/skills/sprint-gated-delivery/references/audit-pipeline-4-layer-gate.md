# 4-Layer Gate Audit Pipeline for Existing Projects

Use when: user asks to "审查" / "audit" / "review" an existing codebase using Sprint+Gate methodology.

## Pipeline Flow
```
Gate 1 (Pre-flight) → Gate 2 (Syntax) → Gate 3 (Integration) → Gate 4 (Feature Comparison)
                                                              ↓
                                                    Agent Team 3-Agent Review
                                                              ↓
                                                         Audit Report
```

## Gate 1: Pre-flight (文件存在性)
- Count backend files (.py) + frontend files (.tsx/.ts) + design docs (.md)
- Check each file is non-empty (size > 50B)
- Output: file count, total lines, PASS/FAIL

## Gate 2: Syntax Check
```python
# Backend: py_compile all .py files
subprocess.run(["python3", "-m", "py_compile", fp])

# Frontend: check for TypeScript errors (if tsc available)
# Or just verify files parse (no syntax errors in grep)
```

## Gate 3: Frontend-Backend Integration (关键!)
```python
# 1. Mock data detection
mock_patterns = [r'setTimeout.*[Mm]ock', r'MOCK_', r'// [Mm]ock']
# grep all .tsx files for mock patterns

# 2. API call detection
api_patterns = [r'api\.|API\.|fetch\(', r'useAuth|onboardingAPI|inviteAPI']
# grep all page components for real API calls

# 3. API coverage per page
for page in pages:
    has_api = bool(re.search(r'api\.|API\.|fetch\(|useAuth', content))
    has_mock = bool(re.search(r'setTimeout|MOCK_|mock[Dd]ata', content))
    # has_api=True and has_mock=False = PASS
```

## Gate 4: Design Doc Feature Comparison
```python
# 1. Read design docs, extract API endpoints
# 2. Read backend routers, count actual endpoints
# 3. Read frontend api.ts, count defined methods
# 4. Compare: design vs backend vs frontend
# 5. Output completion matrix per module
```

## Agent Team Parallel Review (3 Agents)
```python
delegate_task(tasks=[
    {"goal": "代码质量审核: 命名/错误处理/类型标注/DRY", "toolsets": ["terminal", "file"]},
    {"goal": "架构评估: 模块划分/接口设计/前后端API对齐/路由注册", "toolsets": ["terminal", "file"]},
    {"goal": "安全审核: 认证覆盖/密码存储/输入验证/注入防护", "toolsets": ["terminal", "file"]},
])
```

## Audit Report Format
```
Gate 1: PASS/FAIL — file counts
Gate 2: PASS/FAIL — syntax check results
Gate 3: PASS/FAIL — integration check (mock detection + API coverage)
Gate 4: PASS/FAIL — feature comparison matrix

Agent 1 (代码): X/10, P0 list, P1 list
Agent 2 (架构): X/10, P0 list, module completion matrix
Agent 3 (安全): X/10, P0 list

综合评分: X.X/10
P0 清单: N个
P1 清单: N个
CONCLUSION: PASS/FAIL
```

## P0/P1 Fix Pipeline (after audit)
```
Writer (fix issues) → 审查Agent (3-Agent verify) → 验收Gate (syntax + integration)
```
Fix in order: P0 first (blocks runtime), then P1 (quality).

## Pitfalls
- **LoginPage/RegisterPage may use AuthContext** — don't mark as FAIL if they call API via context hook
- **DashboardPage may use useAuth** — indirect API call via context is valid
- **Design doc API count vs regex extraction** — text descriptions may not match HTTP method+path patterns; use the doc's own API table if available
- **Agent Team model availability** — if subagent model unavailable, fall back to self-audit with execute_code
