# 全量设计文档对比审计方法

> 适用场景: 项目完成开发后, 对照设计文档逐模块验证实现完整度

## 触发条件
- 用户要求"从头到尾审查一遍"
- 用户要求"与设计方案对比"
- Sprint交付完成后的终审

## 审计流程

### Phase 1: 设计文档扫描
```
读取 docs/ 下所有设计交接文档
提取每个模块的:
  - API端点清单
  - 功能区块 (### 标题)
  - 交互点
  - 边界情况
```

### Phase 2: 后端实际端点统计
```python
# 找所有包含 router = APIRouter() 的文件
# 统计 @router.xxx("/path") 装饰器数量
# 注意: enhanced.py / version.py / onboarding.py / invite.py 等子模块也要统计
```

### Phase 3: 前端API调用检测
```python
# 检查每个 pages/*.tsx 文件:
# 1. 是否 import 了 api.ts 中的 API 方法
# 2. 是否有 setTimeout / MOCK_ / mockData 等mock模式
# 3. 是否通过 useAuth / AuthContext 间接调用API
```

### Phase 4: 对比矩阵
```
模块 | 设计API | 实际API | 前端页面 | 前端调用 | 状态
-----|---------|---------|----------|----------|-----
M1   |  0      |  2      |  1页     |  1/1     | 🟢
M2   | 29      | 17      |  3页     |  3/3     | 🟡
...
```

### Phase 5: 安全14项检查
1. 密钥管理 (.env in .gitignore)
2. 认证覆盖 (每个router有get_current_user)
3. 输入验证 (Pydantic vs dict)
4. SQL注入 (ORM vs raw SQL)
5. Prompt注入 (sanitize)
6. 密码存储 (bcrypt)
7. CORS (无通配符)
8. .env安全
9. 文件上传 (白名单+大小)
10. 限流 (rate_limit + usage)
11. 错误处理 (无堆栈泄露)
12. JWT黑名单
13. 登录限频
14. AI额度控制

## 输出格式
```
================================================================
  项目名 — 全量终审报告
================================================================
  一、设计文档 vs 实际实现 对比 (表格)
  二、代码质量审查 (评分)
  三、安全审查 (14项)
  四、基础设施审查
  五、综合评分
  六、遗留问题
  CONCLUSION: PASS/FAIL
================================================================
```

## 关键教训
- 设计文档中API数可能与实际router端点数不一致 (设计含增强/扩展功能)
- auth模块的API分散在 router.py + enhanced.py + onboarding.py + invite.py + payment.py 5个文件
- 首页(LandingPage)和定价页(PricingPage)不需要后端API调用 (静态内容+useAuth足够)
- Login/Register通过AuthContext间接调用API, 不算"无API调用"
- Agent Team并行审核时, 模型不可用会导致2/3失败, 需有fallback策略

## Pitfalls
- **设计文档API计数不准**: 设计文档中的API数包含增强/高级功能, 实际router可能只实现核心功能
- **enhanced.py路由重复**: auth/enhanced.py与auth/router.py共享prefix, 重复端点会死代码
- **Alembic async陷阱**: env.py中SQLite用同步引擎(asyncio.run会报async driver错误), PostgreSQL用async
- **Agent Team模型不可用**: delegate_task的子Agent可能因模型token无权限而失败, 需准备手动fallback
