# 全量项目审计方法论 (实测)

## 触发条件
- 用户要求"从头到尾审查"、"全量审计"、"对比设计方案"
- Sprint交付后的终审
- 项目交接前的质量评估

## 4层Gate审计流水线

### Gate 1: Pre-flight (文件存在性)
```python
# 统计后端/前端/设计文档文件数和行数
# 检查所有预期文件是否存在且非空
# 检查main.py的router注册数
```

### Gate 2: 代码质量 (语法+规范)
```python
# py_compile全量检查
# 命名规范(PEP8/snake_case)
# 类型标注覆盖率
# 错误处理模式(HTTPException vs error_response)
# 代码重复(DRY)
```

### Gate 3: 前后端打通验证
```python
# Mock数据检测: grep 'setTimeout|MOCK_|mockData' 前端
# API调用检测: grep 'api\.|API\.|fetch\(|useAuth' 前端
# 页面覆盖: 每个页面是否有真实API调用
# 路径匹配: 前端api.ts路径 vs 后端router路径
```

### Gate 4: 设计文档 vs 实际实现对比
```python
# 读取设计文档索引获取每模块API数
# 统计后端实际router端点数
# 逐模块对比: 设计API vs 实际API vs 前端调用
# 输出完成度矩阵
```

## 设计文档对比方法

### 步骤
1. 读取 `docs/全量设计文档索引.md` 获取每模块设计API数
2. 遍历 `backend/app/` 所有router文件, 用regex提取 `@router.xxx("/path")`
3. 按模块映射: auth→M2, resume→M3, experiment→M4, etc.
4. 遍历 `frontend/src/pages/` 检查每页面是否有API调用
5. 输出对比表: 模块 | 设计API | 实际API | 前端页面 | 状态

### 完成度判定标准
- 🟢 完成: 实际API ≥ 设计API×80% 且 前端调用率≥70%
- 🟡 部分: 实际API ≥ 设计API×50%
- 🔴 不足: 实际API < 设计API×50%
- ⚪ 未定义: 设计文档中无API定义

### 注意事项
- 设计文档中的API数可能过度估算(包含UI交互而非API端点)
- 前端通过AuthContext间接调用authAPI也算有效调用
- enhanced/router.py和router.py可能共享prefix, 需检查重复

## Agent Team模型回退策略

当delegate_task的Agent因模型不可用(403)失败时:
1. 不要反复重试相同配置
2. 主Agent直接用execute_code执行审核逻辑
3. 用regex+文件遍历替代Agent的智能分析
4. 产出等效的审计报告

## 审计→修复→再审 循环

```
全量审计(发现P0+P1)
  → Writer阶段: 批量修复
  → 审查Agent: 3-Agent并行验证修复
  → 验收Gate: 语法+功能+集成全量检查
  → 再审: 对比设计文档确认完成度提升
```

## 安全14项检查清单

1. 密钥管理(.env在.gitignore)
2. 认证覆盖(每个router有get_current_user)
3. 输入验证(Pydantic vs dict)
4. SQL注入(raw SQL vs ORM)
5. Prompt注入(AI功能有sanitize)
6. 密码存储(bcrypt)
7. CORS(无通配符)
8. .env安全(权限+gitignore)
9. 文件上传(白名单+大小限制)
10. 限流(rate_limit.py)
11. 错误处理(不泄露堆栈)
12. JWT黑名单(token_blacklist.py)
13. 登录限频(login_guard.py)
14. AI额度控制(ai_usage.py)
