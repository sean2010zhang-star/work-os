---
name: sprint-gated-delivery
version: 1.0.0
description: Sprint+Gate连续交付 — 每个Sprint完成后自动Gate验证+交付4件套，通过后自动执行下一个Sprint
tags: [sprint, delivery, gate, continuous, pipeline]
related_skills: [delivery-audit, plan-confirm-execute, project-git-version]
---

# Sprint+Gate 连续交付

## 适用场景
- 用户要求"持续开发"、"自动执行下一个sprint"、"连续交付"
- 多模块/多引擎系统需要分阶段交付
- 每个阶段有明确的可验证交付物
- **Greenfield projects**: building from scratch works identically — Sprint 1 = skeleton, Sprints 2-N = one module each (see `references/greenfield-cli-project-pattern.md`)

## 核心流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐
│ Sprint N │───▶│ Gate验证 │───▶│ 4件套   │───▶│ Sprint N+1│
│ 开发     │    │ Pass/Fail│    │ 归档    │    │ 自动开始  │
└─────────┘    └─────────┘    └─────────┘    └──────────┘
```

## Sprint 规划模板

在第一个Sprint开始前，输出完整Sprint规划给用户确认：

```
┌─────────────────────────────────────────┐
│ Sprint 1: [名称]                         │
│ ├─ [任务1]                               │
│ ├─ [任务2]                               │
│ └─ 交付Gate: [具体可验证条件]             │
├─────────────────────────────────────────┤
│ Sprint 2: [名称]                         │
│ ├─ [任务1]                               │
│ └─ 交付Gate: [具体可验证条件]             │
└─────────────────────────────────────────┘
```

## Gate 验证体系（每个Sprint必执行）

### Gate 1: Pre-flight（文件存在性）
- 检查所有预期文件是否存在且非空
- 使用 `read_file` 验证每个文件有内容
- 11/11 文件通过 = PASS

### Gate 退出码忠实性（先于一切 Gate 内容）
**`cmd 2>&1 | tail -3; echo $?` 取到的是 tail 的退出码，不是被测命令的——FAIL 的 gate 会被读成 PASS**（实测：golden 链验证脚本 stdout 里明明有 `✗ ruleId 缺失`，管道后的 $? 仍是 0，假通过险些入库）。规则：Gate 命令的成败判定必须用 `cmd >/dev/null 2>&1; echo $?` 单独取码，或 execute_code 里断言 `subprocess.run(...).returncode == 0`；读 stdout 汇总行只能算半证据。「全链绿」的结论逐条附带退出码出处。

### Gate 2: Revision（功能验证）
- API端点可用性测试（curl）
- 核心功能端到端测试
- 构建通过（TypeScript/Python）
- 每项: PASS/FAIL + 具体数据

### Gate 3: Integration（前后端打通验证）
**每个前端页面必须验证实际调用了后端API，不是mock数据。**
- 检查前端组件中是否有 `api.ts` 中定义的 API 调用（grep `API` 或 `api.` 在 .tsx 中）
- 检查是否有 `setTimeout` 模拟（grep `setTimeout` 在组件中）—— 存在即 FAIL
- 检查是否有硬编码 mock 数据（grep `MOCK_` 或 `mock` 在组件中）—— 存在即 FAIL
- 每个页面必须: 后端有端点 + 前端有页面 + 前端调用了后端 = 三项全 PASS

**间接API调用检测:**
LoginPage/RegisterPage等认证页面通过AuthContext(useAuth hook)间接调用authAPI，直接grep `api.` 会误报FAIL。
- 正确检测: `grep -E 'api\.|API\.|fetch\(|useAuth|useQuery|useMutation' --include='*.tsx'`
- useAuth = 间接调用AuthContext.login/register = 有效API调用
- 静态页面豁免: LandingPage/PricingPage等纯展示页面不要求API调用

**页面分类标准:**
| 类型 | 要求 | 示例 |
|------|------|------|
| 交互页面 | 必须有真实API调用 | Dashboard/Settings/Experiment |
| 认证页面 | useAuth = 有效(间接API) | Login/Register |
| 静态展示页 | 不要求API调用 | Landing/Pricing |
| 功能页面 | 必须有模块API调用 | Resume/Interview/Jobs |
- **localStorage持久化陷阱:** 前端页面用localStorage持久化数据+hardcoded默认值，看起来像有数据但从未调用后端API。
```tsx
// ❌ 陷阱: localStorage + hardcoded mock
const defaultNotifications = [{ id: '1', title: '欢迎...', ... }]; // mock
const [notifications, setNotifications] = useState( => loadSaved('key', defaultNotifications));
// 组件mount时从未调用notificationAPI.list

// ✅ 修复: API优先 + localStorage作为离线fallback
const [notifications, setNotifications] = useState([]);
useEffect( => {
  notificationAPI.list.then(({data}) => {
    setNotifications(adaptAPI(data));
    localStorage.setItem('cache', JSON.stringify(adaptAPI(data)));
  }).catch( => {
    setNotifications(loadSaved('cache', [])); // 离线fallback
  });
}, []);
```
**检测**: `grep -rn 'localStorage.*getItem\|loadSaved' --include='*.tsx'` + 检查对应组件是否有useEffect调用API

**前端页面API调用模式:**
| 页面类型 | 要求 | 示例 |
|----------|------|------|
| 交互页面 | 必须有真实API调用 | Dashboard/Settings/Experiment |
| 认证页面 | useAuth = 有效(间接API) | Login/Register |
| 静态展示页 | 不要求API调用 | Landing/Pricing |
| 功能页面 | 必须有模块API调用 | Resume/Interview/Jobs |

**间接API调用检测:** Login/Register等页面通过AuthContext(useAuth hook)间接调用authAPI，直接grep `api.` 会误报FAIL。
正确检测: `grep -E 'api\.|API\.|fetch\(|useAuth|useQuery|useMutation' --include='*.tsx'`

**惨痛教训:** 曾有项目 8 个 Sprint 全部 Gate 1/2 PASS，但终审需求审查发现大量前端未真实调用后端——大量前端页面用mock数据而非真实API调用。Gate只验证了"文件存在"和"Python语法通过"，没有验证"前端是否真正调用了后端"。结果用户说"你这个项目的交付是失败的"。

### Gate 4: 需求-功能对比审查（终审必执行）
**在声称"完成"之前，必须将设计文档与实际代码逐项对比。**
- 读取设计文档中的功能清单（站点地图/模块列表）
- 对每个功能点，检查: 后端有API? 前端有页面? 前端调用了API?
- 标记每个功能: ✅完全实现 / ⚠️部分实现 / ❌未实现 / 📅推迟
- 输出完成度百分比
- **完成度<80%时禁止声称"完成"，必须继续补齐**

### 输出格式
```
============================================================
  SPRINT N DELIVERY AUDIT REPORT
============================================================
[Gate 1: Pre-flight]
  [PASS] 文件A: N lines
  [FAIL] 文件B: NOT FOUND
[Gate 2: Revision]
  [PASS] API健康检查: status=ok
  [PASS] 核心功能: result=X
============================================================
  Gate 1: PASS | Gate 2: PASS
  CONCLUSION: PASS ✅
============================================================
```

## 交付4件套（Gate通过后必执行）

1. **Git commit + tag** — `git tag -a v2.0-sprint-N -m "Sprint N: 摘要"`
2. **文件备份(tar.gz)** — `~/hermes-backup/项目名_YYYYMMDD_HHMM.tar.gz`
3. **记忆库更新** — `~/Desktop/记忆库/wiki/hermes/{项目}.md`
4. **会话记录会话记录** — `~/Desktop/会话记录/session_YYYYMMDD_项目-sprintN.md`

### 四级全量备份协议（用户说"全量备份"时必执行）

| 层 | 做什么 | 验证 |
|----|--------|------|
| Git | `git add -A && git commit && git tag -a vX.Y.Z` | `git tag -l` 确认 |
| 文件 | `tar czf ~/hermes-backup/{name}_{timestamp}.tar.gz -C ~/projects {name}` | `ls -lh` 确认大小 |
| 记忆库 | 写入 `~/Desktop/记忆库/wiki/hermes/{项目}.md` | 文件存在 |
| 会话记录 | 写入 `~/Desktop/会话记录/session_{timestamp}_{项目}.md` | 文件存在 |


### 验证过的最优执行模式

用户明确要求: "使用之前对比过后的GStack/蜂群/三省六部/Agent Team组合的方式"

**正确模式:**
```
GStack pipeline:    execute_code直接写文件(不用delegate_task)
三省六部:           中书省(方案) → 门下省(审核) → 六部(execute_code) → 审查院(Agent Team)
Agent Team审核:     3个独立Agent并行(代码质量/架构/安全) → 汇总P0修复
Sprint+Gate:        交付框架(4件套+Gate验证)
```

**Agent Team审核模式(替代单agent审核):**
```python
delegate_task(tasks=[
    {"goal": "代码质量审核...", "toolsets": ["terminal", "file"]},
    {"goal": "架构评估...", "toolsets": ["terminal", "file"]},
    {"goal": "安全+边界审核...", "toolsets": ["terminal", "file"]},
])
```
每个Agent只读不写，产出独立报告。主Agent汇总后修复P0再交付。

---

## 全量备份铁律

用户说"全量备份"时，必须备份**回答的全文**，不是摘要或要点。

**错误做法**: 备份"Round X: 回答要点 - bullet1/bullet2/bullet3"
**正确做法**: 备份Round X的完整回答原文(包括所有分析、代码、表格、示例)

用户原话: "不是备份你给我的总结内容，我要全量的信息。我的问题，你的主要思考过程，你给我的全量的详细的回答。"

每轮备份必须包含3部分:
1. **用户问题** — 原文
2. **思考过程** — 加载了什么技能、读了什么文件、得出了什么结论
3. **回答全文** — 完整的回答文本，不是摘要

参考: `references/full-backup-example.md`

**全量对话备份铁律**
用户明确要求: 备份必须包含每轮对话的**完整回答全文**，不是摘要。
- 用户问题: 原文
- 思考过程: 完整推理链路
- 回答全文: 不是bullet point总结，是用户看到的完整回答
- 错误模式: "Round 1: 商业化评估 → 6大差距+Lean Canvas" (摘要，不合格)
- 正确模式: 包含回答中的完整表格、代码块、分析文字


## 全量备份协议（用户说"全量备份"时必执行）

用户说"全量备份"= 四层备份全部执行，不是只做本地压缩包：

| 层 | 做什么 | 验证 |
|----|--------|------|
| Git | `git add -A && git commit && git tag -a vX.Y.Z` + push(如有remote) | `git tag -l` 确认 |
| 记忆库 | 写入 `~/Desktop/记忆库/wiki/hermes/{项目}.md` | 文件存在 |
| 外部存储 | 复制tar.gz到 `<mount>/*/hermes-backup/` | `ls -lh` 确认 |

**执行顺序**: Git → 外部存储(压缩包) → 记忆库
**外部存储用tar.gz** — 不要解压后cp，直接复制压缩包

## Agent Team综合审核模式

当用户要求"综合审核"、"Agent Team审核"时，用delegate_task派发多个独立Agent从不同维度并行审核。

### 与单Agent审核的区别

| 模式 | 审核维度 | 发现率 | 适用场景 |
|------|---------|--------|---------|
| 单Agent | 一次看全部 | 中 | 小改动 |
| Agent Team | 每个Agent专注一个维度 | 高 | Sprint交付/大版本 |

### Agent Team配置(3 Agent)

```python
delegate_task(tasks=[
    {"goal": "代码质量审核: 命名/错误处理/类型标注/docstring/代码重复",
     "toolsets": ["terminal", "file"]},
    {"goal": "架构评估: 模块划分/接口设计/依赖关系/pipeline实现",
     "toolsets": ["terminal", "file"]},
    {"goal": "安全+边界: 输入验证/异常处理/边界值/注入风险",
     "toolsets": ["terminal", "file"]},
])
```

**Pitfall: Agent Team模型不可用** — delegate_task的子Agent可能因模型不可用而失败(如GLM-5.1返回403)。3个Agent中2个失败,只有1个成功。应对策略:
1. 主Agent必须有fallback能力——当Agent失败时自己用execute_code补充执行对应维度的审核
2. 关键审核维度(架构)应优先分配,确保至少1个Agent成功
3. Agent失败时不要中断流程,继续执行其他Gate,最后补充失败的审核维度
4. 用execute_code做代码级检查(py_compile/grep/正则)作为最低保障

### 审核报告格式(每个Agent)

```
评分: X/10
P0问题: [必须修复]
P1问题: [建议修复]
总评: X/10
```

### P0修复流程

1. 收集3个Agent的P0问题
2. 去重合并
3. 修复(用execute_code直接改)
4. 重新跑Gate验证
5. 通过后交付

## 内层执行：Pipeline v3 写-审-验收流水线

每个Sprint内部，单功能的代码开发可用Pipeline v3作为内层执行模式：

```
Sprint+Gate (外层: 管Sprint编排/4层Gate/4件套备份)
  └── Pipeline v3 (内层: Writer→审查→验收, 自动循环, 前后端打通验证)
```

Pipeline v3的6个agent定义模板在 `agent-team-execution` skill的 `templates/pipeline-v3-agents/` 目录下。
核心改进：Agent Team审查(3-Agent并行) + 前后端打通grep检测 + 自动推进。

### 审计→修复→再审 循环
```
全量审计(发现P0+P1) → Writer批量修复 → 审查Agent验证 → 验收Gate → 再审确认
```

### Agent Team模型回退
当delegate_task因模型403失败时，主Agent直接用execute_code+regex执行等效审核。

### 关键陷阱: 同步vs异步
alembic的autogenerate需要同步连接，但项目可能用async SQLAlchemy。

```python
# env.py 正确做法: 用同步引擎
from sqlalchemy import engine_from_config, pool
sync_url = db_url.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
connectable = engine_from_config(config, prefix="sqlalchemy.", poolclass=pool.NullPool)
```

**错误做法**: 用`async_engine_from_config` + `asyncio.run` → SQLite报错
**正确做法**: 全部用同步`engine_from_config`，alembic迁移不需要async

### render_as_batch=True
SQLite不支持ALTER TABLE事务模式，必须用`render_as_batch=True`。

### stamp head
现有数据库已由`create_all`创建，需要`alembic stamp head`标记当前状态。

### 失败模式
- 后端有API端点但前端用setTimeout/mock数据 → 用户看到的是假功能
- 前端有页面但不调用后端API → 前后端未打通
- 新建模块全项目零import零调用 → 死代码
- 只创建router.py但不注册到main.py → 端点不可达

### 正确做法
每个Sprint的交付标准（缺一不可）：
1. **后端端点可curl调用** — 不是"代码写了"，是"curl返回200"
2. **前端页面调用真实API** — 不是"组件存在"，是"浏览器里操作能拿到数据"
3. **集成测试通过** — 用test脚本验证前后端链路
4. **Gate验证包含"前后端打通"检查** — 不只是文件存在性

### 验证命令
```bash
# 后端端点验证
curl -s -X POST http://localhost:8001/api/v1/auth/register -H "Content-Type: application/json" -d '{"phone":"...","password":"..."}'

# 前端代理验证
curl -s -X POST http://localhost:3009/api/v1/auth/register -H "Content-Type: application/json" -d '{"phone":"...","password":"..."}'

# 集成测试脚本
python3 test_full.py  # 覆盖所有端点
```

### 步骤
1. 替换所有品牌名引用（grep确认零残留）
2. 页面Tab按用户故事流排列（不是功能分类）
3. 参考组件映射到产品功能模块
4. 缺失功能创建新页面（不是留空壳）
5. JSX中的品牌名需要手动替换（sed可能漏掉split标签）

### 故事流模板
```
控制台(概览) → 诊断 → 优化 → 实验 → 面试 → 求职 → 专项 → 学习 → 社区 → 设置
```

### 方法
1. 读取设计文档的站点地图（信息架构）
2. 提取每个叶子节点为独立功能点
3. 逐项检查：后端API + 前端页面 + 前后端打通
4. 输出完成度矩阵：模块 | 设计数 | 完成数 | 百分比
5. 低于80%的模块必须补齐

### 分类标准
- ✅ 完全实现（后端API+前端页面+前后端打通）
- ⚠️ 部分实现（有代码但mock/不完整）
- ❌ 未实现（设计中有但代码中没有）
- 📅 明确推迟（V2.0/V3.0计划中）

### 反模式清单
- ❌ 前端页面用setTimeout模拟API调用
- ❌ 后端路由返回硬编码mock数据
- ❌ 用"骨架"、"框架"、"后续迭代"来合理化不完整交付
- ❌ 前端组件不调用后端API（前后端未打通）
- ❌ 只写API端点但前端不使用

### 正确做法
1. 每个功能必须：后端API + 前端页面 + 前后端打通 = 三者齐备
2. 交付前自测：实际调用API验证数据流通
3. 功能审计：对照设计文档逐项检查完成状态
4. 宁可少做Sprint但每个完整，不要多做Sprint但都是骨架

## 反骨架铁律 

用户明确纠正: "我需要的是所有设计功能均已完成，而不是每次都只给我完成一个骨架。"

**骨架 = 罪恶** — 以下任何一项都说明功能未完成:
- 前端页面用 `setTimeout` / `MOCK_` 常量 / 硬编码假数据
- 后端端点存在但前端组件从未调用 `api.ts` 中的对应方法
- 模块有 router 文件但返回 stub (`{"message": "V2.0上线"}`)
- AI 功能未接真实 LLM API（至少要有 fallback 路径）
- 数据库模型存在但无实际 CRUD 操作

**完整性验证清单 (每个 Sprint 必过):**
```
[ ] 后端: 每个 API 端点有真实 DB 操作（grep 'await db.execute' / 'db.add'）
[ ] 后端: AI 端点有真实 LLM 调用或 mock fallback（grep 'llm_engine'）
[ ] 前端: 每个页面组件调用了 api.ts 中的方法（grep -n 'API\.' / 'api\.'）
[ ] 前端: 无 setTimeout 模拟异步（grep -rn 'setTimeout' --include='*.tsx'）
[ ] 前端: 无 MOCK_ / mock 常量驱动的假数据（grep -rn 'MOCK_' --include='*.tsx'）
[ ] 集成: curl 端到端测试通过（注册→登录→使用功能→获取结果）
[ ] 服务: 后端能启动且 health 端点返回 200
[ ] 服务: 前端能启动且页面能渲染
```

**执行铁律:**
1. 写完后端路由后立即写前端页面并接入 API — 不要分两个 Sprint
2. 写完前端组件后立即验证它调用了真实 API — 不是 mock
3. AI 功能必须有 mock fallback（无 API Key 时）+ 真实调用路径（有 Key 时）
4. 每个 Sprint 结束前运行端到端集成测试

### 双参数Body Bug
```python
# ❌ P0: FastAPI无法解析两个同类型body参数 → 422必现
async def create_plan(data: LearningPlanRequest, req: LearningPlanRequest, ...):
    return create_learning_plan(req.skills, ...)  # req永远是默认值

# ✅ 修复: 只保留一个body参数
async def create_plan(data: LearningPlanRequest, ...):
    return create_learning_plan(data.skills, ...)
```
**检测**: `grep -rn 'async def.*data:.*Req.*req:.*Req' backend/app/`
**特征**: 函数体内引用`req.xxx`而非`data.xxx`，说明从main.py迁移时参数未清理

### Router Prefix冲突
```python
# ❌ P0: 两个router注册到同一prefix，重复路由永远不可达
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(auth_enhanced_router, prefix="/api/v1/auth")  # /skills重复！

# ✅ 修复: 删除重复router，合并到主router
```
**检测**: `grep -rn 'include_router' main.py` + 检查prefix是否重复
**特征**: 子模块(enhanced.py)与主router(router.py)定义了相同路径

### 前后端API路径不匹配
```python
# ❌ P0: 前端路径与后端不一致 → 上线404
# frontend api.ts: api.post('/student/decision-helper', data)
# backend router:  @router.post("/decision")
```
**检测**: 提取前端api.ts的所有路径 + 提取后端router的所有路径 → 逐项对比
**修复**: 统一修改前端api.ts匹配后端（后端是source of truth）

## 交付 Gate 的 HTML/JS 语法与运行时形态安全两项必查

**HTML 内联脚本语法闸门** — 单行 JS 语法错 = 整个 `<script type="module">` 块静默死亡 = 页面空白零报错，肉眼与 fetch 检查全放行。`node --check file.html` 测不到内联体（HTML 本身不可 --check）。交付 Gate 必须跑提取式检查：正则抽出 web/app/原型全部 HTML 的内联 `<script>`（跳过 importmap/带 src 的）逐个落临时 .mjs 做 `node --check`，任一非零退出即 FAIL。高发触发点：patch/write_file 替换 JS 块后残留旧块头尾拼接（`const X = [` 悬空）——替换含数组/对象字面量边界的块后，除重读 diff 外必须过此闸门。

**交付运行形态安全审计（代码合规 ≠ 部署合规）** — 「私钥不出机/凭证不外泄」类铁律只核 git 面（.gitignore/ls-files）会漏掉运行态：仓库根静态服务默认绑 `0.0.0.0` 且无路径限制时，`curl http://<host>:<port>/.secrets/<私钥>` 直接 200——私钥经局域网可取走，整个签名体系作废。审计任务书必须含**运行形态实测矩阵**：①对每个敏感资源（私钥/密钥 pub/原始件/运营日志/.git）从当前跑着的服务路径 curl 核 403；②`lsof -nP -iTCP:8001 -sTCP:LISTEN` 核监听面（开发服务默认 127.0.0.1，放开须显式环境变量开关）；③grep 鉴权布尔硬编码（如 `enforce:false`）=付费/权限旁路面，生产开关必须接构建旗标而非注释承诺。python `send_error(code, '中文reason')` 按 latin-1 编码状态行，非 ASCII reason=UnicodeEncodeError 掐断连接、curl 报 000——**000 是服务端炸了，不是 403 生效**，拦截消息用 ASCII 状态行+日志记详情。

**签名入口的文法封闭纪律** — 订单/意图串解析器的每个分支都要白名单：一分支有 `includes` 校验、另一分支直接 `template.replace('%s', 用户串)` 即开「低价签任意字符串」的口子（对象入串→`[object Object]`、`../../evil`、超长串全过）。凡进入签名 payload 的字段，类型+正则文法+长度三闸缺一不可，且回归锁按分支逐形态断言拒单，不只测 happy path。

**双端同用模块禁 Node 专属 API** — 浏览器会 import 的 JS（编解码/目录/校验）禁 Buffer/fs 痕迹，b64 用 btoa/atob+TextEncoder/Decoder；同输入须实测 Node 与浏览器两侧产出**字节相同**（订单串/凭证编码漂移=价格与授权双端分叉）。审计发现注入违规后，清偿者对新增闸门做「先红后绿」自检（临时注入→确认 FAIL→复原→PASS），写入清偿报告。

## 自动推进规则

- Gate全部PASS → 自动执行下一个Sprint（不等用户确认）
- Gate有FAIL → 修复后重新验证，最多3次
- 3次FAIL → Escalation（向用户展示问题，等待决策）
- 用户说"开始执行" = 授权连续推进，不需要每步确认
- **会话被外力截断（工具迭代上限/上下文压缩）时的版本铁律补账序**：截断前若当前批次改动已全绿，立即 commit+tag 再写总结，把"未入库裸奔"压到零；若未跑全量测试则不 commit，但总结第一行必须声明 dirty 状态与范围（哪些文件动了、下轮第一件事是入库还是回滚），恢复会话按该声明先补账再继续——不允许新会话把上一会话的未声明改动直接当成"已交付"。

## Sprint后独立审计→清偿循环

每个Sprint commit+tag后，派独立审计Agent（只读、亲自重跑全部验收项、不信开发端自报），产出结构化 verdict（score/verdict/p0/p1/p2，见 `references/agent-team-material-review-gate.md` 的 schema，同一 schema 复用于事后审计）：

**审计与后续 Sprint 的安全并行**：Sprint 级 gate 审计（非发布终审）以 background delegate 派出的同时，可以继续开发后续 Sprint——但任务书必须把被审对象钉在 **tag**（"仓库 X（tag vN，HEAD=sha）"），禁止钉 HEAD：后续 Sprint 的 commit 会移动 HEAD，钉 HEAD 的审计等于在被抽换的证据上出报告；钉 tag 后审计者按 tag 复现（`git show <tag> --stat`、worktree checkout），与飞行中改动解耦。任务书同时给**显式只读清单**（列到文件级）+「禁止全库扫描/禁读大文档目录」预算条款（子 Agent 陷"再读"循环是 600s 超时主因）。多维终审（同一 tag 多 Agent）仍按下方冻结规则，不适用本并行。

```
Sprint开发 → commit+tag → 独立审计Agent重跑 → PASS(带P1/P2)
  → 开发端"清偿"：修掉P1+可顺手清的P2 → 单独commit+tag（audit清偿版）
  → 自动进入下一Sprint（P1/P2清偿不需复审；只有出现P0才修复后再审）
  ⚠ 例外——发布门终审（正式版/收费前）不适用"清偿免复审"：多维终审后必须派闭环复审官（见下）
```

清偿纪律：
- 清偿 commit 正文按审计发现 ID 逐条列映射（P1-1→修法 / P2-3→修法），让下一轮审计能核对每条是否真清。
- **清偿改动行为时，同笔 commit 必须翻转断言旧行为的既有测试**——旧测试若断言的正是审计标出的缺陷（如"未加载词表时全放行"），只加新断言不改旧断言 = 套件继续绿着锁死错误行为。清偿后跑全量回归（分包测试+链验证+浏览器复验），不只跑受影响项。
- 审计脚本的注释/自报声称断言深度必须与实际执行一致；被审出"深度虚标"时修法是把注释改成真实范围，而不是当场硬补做不到的比对（缺输入数据就明确标注属后续 Sprint 范畴）。

### 终审门闭环复审（发布前专用，区别于普通 Sprint gate）
Sprint 级清偿可免复审，但**发布终审（tag 为 rc）清偿后必须派一个轻量独立复审官**，任务书三件事：①重放上轮红队探针——对修复后代码逐条重跑上一轮审计的绕过攻击集，"上轮漏检须全部转 HIT 或声明为范围外"，任何自报已修实测仍漏=P1 起判（虚报比原漏洞更重）；②清偿逐项抽验——按审计发现 ID 映射表逐条核对代码证据；③回归复跑全部验收命令。复审官须用 git worktree 双版本对比（旧 rc vs 新 rc）区分"修复引入的回归"与"上轮探针自身的标注错误"——上轮探针的期望值标注也会错（实测：复审官发现旧探针把 MISS 误标为基线 HIT）。清偿改动的 commit 与 rc tag 链要保持每 Gate 一对（rc→rc2→rc3→发布版），复审官核对 tag→commit 指向。
- **终审期间冻结代码**：多维并行审计（3 Agent）审的是同一个 tag；若必须中途推进 HEAD（如前两个维度已返回触发清偿），给仍在跑的审计 Agent 发 steer/drift 通知不可靠（Agent 可能已结束），正确姿势是等全部返回再统一清偿、或以新 tag 重派增量复审——不要在审计飞行中静默改动被审文件。
- **已定级接受的设计债要预写入后续审计任务书**：用户/审计确认"记录接受"的风险（附升级触发条件，记入决策记录），下一轮审计的 context 必须原文带入并注明"勿重复定 P1，只核发布前置判定"——否则每个独立审计者都会重新发现并重新争论同一个已知决策，浪费一轮 P1 清偿。

审计口径纪律：
- **批量文本内容生产（写手管线）**：生成含事实/数值/口诀的大量文本（讲义/手册/词条），或用户报「某板块没内容」时，走 `references/subagent-content-authoring.md` 的完整管线——彻查断链层（数据文件自述 vs 宿主实际加载 vs 浏览器实测上屏字数）→ 主会话先实算「锚数据表」入写作规范（唯一合法数值源，锚外禁编造）→ N 写手分片并行 → 主会话六类程序化校验门（红灯先分诊真缺陷 vs 校验器过严）→ 扩写段与写手稿同权送检 → 独立内容审（手算链要独立复算不只对锚表）。
- **展示/分享层的三条验证铁律（独立审计实测击穿面）**：①测试夹具必须用引擎**真实输出形状**（先实跑 dump 一份再写断言）——手造字段形状会掩盖渲染退化（夹具读 f.year、引擎实形 f.date.year → 线上渲空行而套件全绿）；②展示页 catch 分支必须区分 fetch 失败与代码异常并 console.error 留痕——代码级 TypeError 被 catch 吞掉会伪装成「离线/取数失败」，服务端全 200 时页面仍恒显错误态；③截断≠脱敏——用户可把敏感内容（出生日期时刻/性别）写进自由文本（问句/备注），导出/分享层须做内容级模式遮花（日期/时刻/性别/属相正则→占位符）+硬长度闸，键名扫描防不住内容；「宁可遮花不可漏出」，回归锁直接断言原值不上屏。
- **外部库/查表类知识源的断言三锁**：①名单、枚举、结构常量必须多盘探针提取全集后再写入断言、按库实际申报——凭记忆默写口诀/十二神/区间锚每次都出错；库实际与纸面底本冲突时按库断言并在代码注释申报口径。②红测守护力=断言盘面是否含被篡改的目标值——查表函数每个表值至少一盘使其 hit=true 且 basis 串含该值字面，否则改表值不红（"底本纠偏锁定"名不副实的逃逸形态）。③查表函数签名扩展后 grep 调用面全量迁移，新参数缺省时的正确语义=该星/该字段缺席不猜，且要有"旧签名调用"的回归锁。
- **回归锁必须断被修的表象本体，不是元数据**：行为类修复若只断言回显字段（喂库参数/时间戳/clock 串），篡改退回旧行为时这些值不变、套件照绿而 bug 完整复活。锁的验收=同轮篡改注入自检：在探针树把修复退回旧实现→新锁必须红→恢复→绿，之后才可在 commit 申报"锁成立"；断言对象选实际输出面（盘面/渲染结果），元数据断言只能当辅锁。
- **python str.replace 锚点失配=静默空转，"已写入文档"申报前必须 grep 验证**：`s.replace(old,new)` 在 old 不存在时不报错，文档补写变虚报——连续多笔 commit 申报"docs 记"实际从未落盘，且后一笔的插入锚引用了前一笔从未存在的标题=错误沿锚点链式传播（独立审计 grep 全档 0 命中实锤）。规则：写前 assert 旧串命中；写后 `grep -c` 新串并核对计数，验证通过才申报；给无既有锚点小节的文档追加内容一律用文件尾 append，不做 replace；任何"我上轮写过 X"的引用先实测 X 在场。**同类静默空转的第二形态**：`python3 - <<EOF` 的 stdin 源码含非 ASCII 时可报 Non-UTF-8 SyntaxError 整段未执行，而链上后续命令照跑——含中文的批量文件改写一律走 execute_code 或先 write_file 落 .py 再执行，跑完 grep 验证不可省。
- **两页/两引擎输出不一致的诊断序**：先程序化扫 N 随机输入盘逐分量 diff 计数（禁肉眼与挑盘），再把差异分量分解为两类：参数面缺失（一链有校正/另一链没传=真 bug，修=两侧走同一校正函数单一真相源）与口径/流派差（边界定义不同=非 bug，处置=双口径并陈+中性口径注，不强行归一也不藏一侧）。为第二口径写独立自算时再对参考库全量对拍——这是揪存量转换函数归属类真 bug（如岁首边界错归）的最佳时机。对拍结论申报必须附参数口径（N 盘×哪些变量维度），单城/单参探针的影响面低估会被多维复跑的审计打回。
- **审计Agent会发现自报数据的口径问题**（如"800/800全绿"实为双源400+mock单源400）——开发端报告对覆盖率必须按"双源N + 单源/mock N"分列，禁止合并一个数字；审计措辞同样要区分口径。
- 审计Agent越权清理（删untracked垃圾文件）必须在报告中主动披露"略超只读边界"——派审计任务时在goal里写明只读边界，并要求披露任何写操作。
- 验证shell脚本的 `echo` 必须加引号——错误重定向会在仓库根产生未跟踪垃圾文件，审计判脚本卫生问题，且脏工作区违反版本管理铁律。commit前 `git status --porcelain` 必须为空或全部已暂存。
- 版本字符串单一真相源：入口导出 `VERSION` 常量，UI文案与 .d.ts 注释动态引用；grep 旧版本串（含注释和文案，不只代码）应为 0——审计按这个严格口径查。
- **文档数字是被审计面，随代码同 commit 更新** — README/设计文档里断言的测试条数、包数、规则条数、golden 组数、页面数，独立审计会抽样 N 处与实际跑数/程序化计数比对（≥3 处不符定 P1）。改测试数的 commit 必须同一笔同步文档数字；数据文件内的自述计数（如 golden-set 的 counts 字段）也要由 groups 重算生成，不留手填旧值。**commit message 的分项计数同样是被取证面**：审计会数 test 声明条数比对「新增 N 条」自报——写「套件 5 条」实为 4 个 test+1 条内嵌 assert 即定计数虚增；纪律=分项宁少勿虚，拿不准只写总数（`# tests` 行读数），修复既有文件时写「修订条」而非「新增条」；改造既有测试项不新增 test 时总数不变，别按改动量估加数。commit 后自审发现计数申报失实，用 `git tag -d` + `commit --amend` + 重打 tag 就地订正（tag 必须指向申报与事实一致的 commit），不留靠追加 commit 解释的失实链。UI 展示面同理：页面/商店卡片/账本里的证据徽章、锚点计数、版本类文案数字一律程序化实读自单一真相源（数测试名、读 JSON 字段、跑脚本抽输出），禁字面量禁凭记忆编写——写错一个「N 组」或臆造一个不存在的证据（如从未存在的 golden 分组），独立审计逐条实查即定 P0，且此类陷阱会在修复上一处假数字时再自犯，修复时新写的数字本身也要实查。

## 浏览器回归的表单纪律

对表单驱动的页面做浏览器端到端验收时，不要假设页面读取 URL query 参数（多数静态页只读表单）。判定"URL参数无效=FAIL"前先用 getElementById 填字段 + click 提交再取结果；结果区 selector 与页面实际渲染 class 不一致时，先 `document.body.innerText` 找锚点文案定位。

**localStorage 探针要先落在同源页**：浏览器工具当前页不是被测 origin 时（上一次导航失败/停在 about:blank），直接 `js("localStorage.setItem…")` 抛 SecurityError 整个脚本中断。固定套路：先 `goto_url(被测应用任意页)` → 等加载 → 再操作 localStorage/跳转；写测试种子数据尤其如此。

**多闸门页面 E2E 先全量注入状态** — 年龄声明/档位凭证/明示同意等多个独立 localStorage 闸会逐层拦截，结果区空白≠功能坏了。顺序：读 result 区 innerText 找拦截文案定位是哪一层闸 → 注入对应键（凭证类必须用真签发工具签出，禁伪造）→ 重跑。清态后每轮回归把全套预注入当固定前置；凭证会随测试/清缓存丢失，"两轮假信号"的根因几乎都是闸而非代码。

**测数据脏了会炸整页渲染——先排雷再改码**：E2E 里手动 setItem 塞的简化 JSON（缺必填字段）会让页面脚本 `a.firstAt.slice` 抛错、渲染区空白，误判成功能坏了。排查顺序：清掉种子 → import 页面模块手动跑 init 看 THROW 内容 → 定位缺字段。真实用户手改存储/版本迁移也会同样破页，顺手给渲染层字段加 `(x || '—')` 兜底。

**sed -i '' 处理含中文/特殊 Unicode 的替换易报 bad flag** — 替换串里有中文或引号嵌套时 macOS sed 直接语法碎。改用 Python `str.replace`（写前 assert 旧串命中）或先落一个 .cjs/node 脚本跑 JSON 字段改写；批量改 import 行后除 `node --check` 外必须真实加载一次（浏览器或 `node -e "await import(f)"` 看是否模块解析级报错）——逗号丢失这类断裂 --check 可能放行。

**execute_code三引号/花括号转义** — 在execute_code中含中文的三引号嵌套+f-string转义叠加会 SyntaxError；另有一类更隐蔽的：f-string 内嵌 shell grep 模式含字面花括号（如 `f"grep -n 'X = {' -A 10 {f}"`）同样 parse 期报错。**parse 失败 = 整个 cell 原子性不执行，前面已写的文件改动全部丢失、必须重做**。规则：含字面花括号/引号嵌套的命令行一律用字符串拼接或先赋值变量，不用 f-string；同一 cell 里把"写操作"与"高风险探针"分成两个 cell 跑，探针失败不伤写入。对含中文内容的文件直接调 write_file 工具（每次一个文件），不在 execute_code 循环中写。

**测试脚本变量赋值bug** — 在execute_code中写验证脚本时，`comm_page = open(...).onb_page if False else ""` 导致comm_page永远为空字符串，CommunityPage验证误报FAIL。根因: 从复制粘贴时变量名未清理。规则: 验证脚本中每个变量赋值必须独立一行，不要用条件表达式链。

**前端路径不匹配检测方法** — 前后端API路径对比不能只靠grep，需要提取两端的完整路径列表做diff:
```python
# 前端路径提取
frontend_paths = re.findall(r"api\.\w+\(['\"]([^'\"]+)", api_ts_content)
# 后端路径提取
backend_paths = re.findall(r'@router\.\w+\(["\']([^"\']+)', router_content)
# 对比
mismatch = [p for p in frontend_paths if p not in backend_paths]
```

**Agent Team模型不可用降级** — delegate_task的子Agent可能因模型不可用(GLM-5.1返回403)而失败。降级策略: 主Agent直接用execute_code补充失败Agent的审核维度。不要重试同一模型。

**模块未集成死代码** — 新建模块全项目零import零调用。预防: Gate验证加"import链验证"— grep确认新模块被外部import。

**骨架交付冒充完成** — 连续交付了mock/stub代码并声称"完成"，用户最终审计显示功能完成度仅47%。
根因: 后端写好了API但前端用setTimeout模拟，前后端从未打通。
预防规则:
1. Gate 2必须加"前后端打通验证"— 前端页面必须实际调用后端API，不能用mock数据
2. "完成"= 用户可操作的真实功能，不是"文件存在"
3. 每个Sprint的Gate必须包含端到端测试：前端发起请求→后端处理→前端展示结果
4. 交付报告必须区分"后端API就绪"和"前端已接入"两个状态
5. 功能完成度必须按设计文档逐项对比，不能自行定义"完成"

**Express代理到FastAPI** — Vite+Express前端需要代理API请求到FastAPI后端。
方案A(推荐): 在server.ts中用fetch转发，用Express已解析的req.body。
方案B: 用http.request pipe方式——但multipart上传会超时，不推荐。

```typescript
// 方案A: fetch转发（推荐，multipart兼容）
app.use("/api/v1", async (req, res) => {
  const targetUrl = `${BACKEND_URL}/api/v1${req.url}`;
  const headers: Record<string, string> = {};
  if (req.headers.authorization) headers["Authorization"] = req.headers.authorization;
  const fetchOpts: RequestInit = { method: req.method, headers };
  if (req.method !== "GET" && req.method !== "HEAD" && req.body) {
    headers["Content-Type"] = "application/json";
    fetchOpts.body = JSON.stringify(req.body);
  }
  const response = await fetch(targetUrl, fetchOpts);
  const data = await response.json;
  res.status(response.status).json(data);
});
```

注意: 不要用http.request管道方式，multipart上传会失败。不手动读chunk，用Express已解析的req.body。
```typescript
app.use("/api/v1", async (req, res) => {
  const targetUrl = `${BACKEND_URL}/api/v1${req.url}`;
  const headers: Record<string, string> = {};
  if (req.headers.authorization) headers["Authorization"] = req.headers.authorization;
  const fetchOpts: RequestInit = { method: req.method, headers };
  if (req.method !== "GET" && req.method !== "HEAD" && req.body) {
    headers["Content-Type"] = "application/json";
    fetchOpts.body = JSON.stringify(req.body);
  }
  const response = await fetch(targetUrl, fetchOpts);
  const data = await response.json;
  res.status(response.status).json(data);
});
```
注意: 不要用http.request管道方式，multipart上传会失败。不手动读chunk，用Express已解析的req.body。

**write_file引入null字节** — hermes_tools.write_file写入的Python文件偶尔包含null字节(\\x00)，导致SyntaxError。
修复: 每次批量write_file后运行清理:
```python
import os
for r,d,fs in os.walk('app'):
  for f in fs:
    if f.endswith('.py'):
      p=os.path.join(r,f)
      dt=open(p,'rb').read
      if b'\x00' in dt:
        open(p,'wb').write(dt.replace(b'\x00',b''))
```
预防: write_file后立即py_compile验证。

**Redis同步/异步混用** — 用aioredis(async)在同步FastAPI路由中调用.get返回coroutine对象而非值。
症状: `"登录尝试过多，请<coroutine object...>秒后重试"`
修复: 同步路由用`import redis`而非`import redis.asyncio as aioredis`。每个Redis模块用独立的_get_redis工厂函数返回同步连接。

**PostgreSQL密码认证失败** — sudo -u postgres创建用户后，.env中密码可能与实际ALTER USER设置不一致。
修复: 创建用户后必须`PGPASSWORD=xxx psql -U user -d db -h localhost -c 'SELECT 1'`验证连接。.env密码必须与ALTER USER一致。

**tar上传覆盖.env** — 本地.env(含PostgreSQL URL)打包上传覆盖云端.env(含SQLite URL)，导致asyncpg找不到模块。
铁律: tar打包时`--exclude='backend/.env'`排除，云端.env单独创建/维护。

**Pydantic模型替换dict后.get崩溃** — 将`data: dict`改为`data: PydanticModel`后，`data.get("key")`报AttributeError。
铁律: 改schema后立即grep该router所有`.get(`并替换为`data.xxx`。同一router参数名统一用`data`不要混用`req`。

**main.py膨胀(390行→79行重构, 某全栈项目)** — 45个内联路由导致main.py不可维护。
重构步骤: 1)创建common/schemas.py统一Pydantic模型 2)按模块将路由迁移到各自router.py 3)main.py只保留初始化+路由注册+健康检查。重构后main.py < 80行。

**审计-修复循环到9.0** — 从6.0分到7.5分需要多轮修复，但7.5到9.0需要架构级改动(PostgreSQL/Redis连接池/全面类型标注)。
规则: 安全分提升最快(有明确修复模式)，代码质量和架构分需要深层重构。达到7.5是MVP可用水平，9.0需要基础设施升级。
    if f.endswith('.py'):
      p=os.path.join(r,f)
      dt=open(p,'rb').read
      if b'\x00' in dt:
        open(p,'wb').write(dt.replace(b'\x00',b''))
```
预防: write_file后立即py_compile验证。

**bcrypt 5.x与passlib不兼容** — bcrypt 5.x移除了__about__模块，passlib无法读取版本。
修复: pip install 'bcrypt==4.0.1'
症状: (trapped) error reading bcrypt version → register返回500

**datetime时区不一致** — SQLAlchemy模型用datetime.utcnow(naive)，新代码用datetime.now(timezone.utc)(aware)，两者相减报TypeError。
规则: 整个项目统一用datetime.utcnow或统一用datetime.now(timezone.utc)，不能混用。

**JS「查看日/as-of」回退绝不用 toISOString.slice(0,10)** — UTC 日界在本地凌晨 0-8 时窗与本地日差一天，快照锚（流年/流月类按日计算）随之错值且界面标注无从核对。规则：①回退用 getFullYear/getMonth/getDate 本地分量拼接；②提取层即使调用方不传参也把**实际使用的日期**回填进输出字段（界面『截至 X』永不为空=诚实标注闭环），单一真相源在库层而非逐个调用方补传；③回归锁断言回退值===本地今日（注意该等值锁仅在 UTC≠本地窗内能区分错法，主锁应另设格式/非空全天红断言）。

**P0安全审计清单** — 以下P0问题在新项目中必须预防：
1. 批量赋值漏洞 — update_profile的setattr可覆盖role/tier → 白名单字段赋值
2. Prompt注入 — 用户输入直接拼入LLM prompt → _sanitize过滤
3. 文件上传OOM — file.read全量读入 → 流式读取+大小检查
4. TOCTOU竞态 — 额度检查与递增非原子 → SQL UPDATE WHERE原子操作
5. 不安全默认值 — SECRET_KEY/JWT_SECRET硬编码 → 生产环境启动校验
6. 登录暴力破解 — 无频率限制 → 内存计数器(5次/5分钟)

**Agent Team审计评分plateau** — 多轮审计-修复循环中，评分会在某个水平plateau：
```
安全分: 4.4→6.2→7.0→7.5 (提升最快，有明确修复模式)
代码分: 7.2→7.5→7.0→7.0 (波动，新审计发现新问题)
架构分: 8.2→8.0→7.5→7.0 (下降，越来越严格)
```
原因：(1)安全问题有明确修复模式(白名单/限流/sanitize)→提升快；(2)代码质量需要深层重构(原子SQL/异步队列/全局中间件)→提升慢；(3)每次修复可能引入新问题→架构分反而下降。
要突破plateau到9.0+需要：Redis连接池统一、PostgreSQL替代SQLite、全面Pydantic response_model、UUID校验提取为FastAPI依赖。这些是架构级改动。

**保守路径选择逻辑反转** — 三路径选择conservative用max(risk_acceptance)=最激进，应为min(risk_acceptance)=最保守。risk_acceptance高=愿意冒险，不是安全。规则: conservative=min(risk), balanced=max(total), aggressive=max(growth)。

## 全栈产品开发模式

当Sprint用于从零开发完整产品时，增加以下阶段：

### 阶段1：需求讨论与设计
1. **产品定位** — 名称、定位、目标用户、核心价值
2. **现状梳理** — 已有产品、当前管理方式、痛点
3. **功能需求** — 按模块讨论，记录用户原话
4. **技术选型** — 前端/后端/数据库/AI/部署
5. **开发计划** — 分阶段Sprint规划

输出物: 讨论记录 + PRD + 技术架构 + 数据库设计 + API设计 + 开发计划

### 阶段2：独立Agent评审
- 完备性/可靠性/可行性/解耦性
- P0立即修复，P1 Sprint前补齐，P2后续迭代

### 产品生命周期
```
设计中 → 建设中 → 待售卖 → 售卖中
```

### 执行铁律
```
文件创建/批量写入 → execute_code + write_file 直接写（快100倍，不超时）
独立审核/研究 → delegate_task（仅此用途）
多Agent协作 → ruflo蜂群 / Agent Team / 三省六部（不是delegate_task）
```

## 前后端并行模式

当Sprint包含前后端任务时：
1. 用 `delegate_task` 并行分发（前端Agent + 后端Agent）
2. 后端先启动（提供API），前端通过proxy调用
3. 两边完成后统一做集成测试

## 部署闸门：tag ≠ 云端同步（用户全局铁律）

**版本更新（commit+tag）默认只进本地仓库，绝不自动 deploy。** 仅当用户明确说「同步云端/deploy」才执行部署脚本；一次部署授权只覆盖那一次动作，不随后续 Sprint 延续。多载体（web/app、静态/API）时 deploy 范围也按用户点名执行，未点名的服务形态（如明文凭证 API 禁公网）保持不下线。Sprint 收口语要如实写「未同步云端」，让用户知道线上仍是旧版。

### 端口规划
```
已有服务: 3010 (legacy 系统) — 不动
新系统后端: 8002 (FastAPI)
新系统前端: 3009 (Vite/Express)
```

### 数据库选择
- 无PostgreSQL → 用SQLite (`sqlite+aiosqlite:///./myapp.db`)
- **JSONB不兼容SQLite** — 必须将 `from sqlalchemy.dialects.postgresql import JSONB` 改为 `from sqlalchemy import JSON`
- PostgreSQL端口未开 → 用SQLite零配置启动

### 部署步骤
```bash
# 1. 打包(排除venv/node_modules/.git)
tar czf /tmp/myapp-backend.tar.gz --exclude='backend/.venv' backend/ shared/

# 2. 上传
scp -i key.pem /tmp/myapp-backend.tar.gz ubuntu@server:/tmp/

# 3. 解压到独立目录
ssh ubuntu@server "mkdir -p ~/myapp && tar xzf /tmp/myapp-backend.tar.gz -C ~/myapp/"

# 4. 安装依赖
ssh ubuntu@server "cd ~/myapp/backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"

# 5. 创建.env(不要用本地.env上传！)
ssh ubuntu@server "cat > ~/myapp/backend/.env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./myapp.db
SECRET_KEY=$(openssl rand -hex 16)
JWT_SECRET=$(openssl rand -hex 16)
EOF"

# 6. systemd服务
sudo tee /etc/systemd/system/myapp-backend.service << 'EOF'
[Unit]
Description=某全栈项目 Backend
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/myapp/backend
ExecStart=/home/ubuntu/myapp/backend/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002
Restart=always
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable myapp-backend && sudo systemctl start myapp-backend
```

### .env生命周期铁律
**打包上传时本地.env会覆盖云端.env！** 本地用PostgreSQL，云端用SQLite，URL不同。
- 错误做法：tar打包时包含.env → 上传覆盖云端配置 → asyncpg找不到 → 启动失败
- 正确做法：tar用`--exclude='backend/.env'`排除，云端单独创建.env
- 或者：`scp`只上传代码文件，.env在云端手动创建

### Express代理端口修改
server.ts中`BACKEND_URL`默认`http://localhost:8001`，云端后端在8002，必须修改：
```bash
sed -i 's/localhost:8001/localhost:8002/' ~/myapp/web/server.ts
sudo systemctl restart myapp-web
```

### 验证独立性
```bash
ss -tlnp | grep -E '3010|8002|3009'  # 三个端口独立
curl -s http://localhost:3010/...     # 旧系统正常
curl -s http://localhost:8002/health  # 新系统正常
```

## 参考前端集成模式

当用户提供参考前端代码（zip/仓库）时，必须直接使用参考代码，不要重写。

### 正确流程
```
1. 解压/克隆参考代码到项目目录
2. npm install
3. 修改server.ts添加后端代理（见references/express-vite-proxy.md）
4. 批量替换品牌名（sed + 手动修JSX拆分元素）
5. 添加新页面组件（参考代码没有的功能）
6. 修改App.tsx的Tab结构（按故事流排列）
7. 启动验证
```

### 品牌替换铁律
- `sed -i '' 's/OldName/NewName/g'` 可处理90%的文本替换
- JSX拆分元素（如 `Career<span>Forge</span>`）必须手动patch
- 版本标签（如"实验版 v2.4"）需改为产品描述
- 页脚版权文字需更新
- 验证：`grep -rn "OldName" src/` 确认零残留

### 错误模式（已验证失败）
- ❌ 重写参考前端组件 → 风格不一致，用户不满
- ❌ 只改App.tsx不改子组件 → 品牌名残留
- ❌ 用http.request做Express代理 → 超时问题
- ❌ 端口冲突不检查 → 服务启动失败

## 审计模式选择

两种审计模式，按复杂度选择：

| 复杂度 | 模式 | 用法 |
|--------|------|------|
| 低/中 | 单Agent审计 | `delegate_task(goal="审计...", toolsets=["terminal","file"])` |
| 高/极高 | Agent Team审计 | `delegate_task(tasks=[3个并行Agent])` 见下文 |

### 单Agent审计（低/中复杂度）

```
主Agent完成开发 → delegate_task(审计Agent) → 独立读取所有代码 → 产出审计报告 → 主Agent修复问题
```

### Agent Team审计（高/极高复杂度，验证）

用户明确要求"独立审核换成agent team模式，进行综合性的审核"时，用3个并行Agent从不同维度审核：

```python
delegate_task(tasks=[
    {"goal": "代码质量审核: 命名规范/错误处理/代码重复/类型标注/docstring",
     "role": "leaf", "toolsets": ["terminal", "file"]},
    {"goal": "架构评估: pipeline/接口设计/模块依赖/DRY/可测试性",
     "role": "leaf", "toolsets": ["terminal", "file"]},
    {"goal": "安全+边界: 输入验证/异常处理/边界值/注入风险/资源耗尽",
     "role": "leaf", "toolsets": ["terminal", "file"]},
])
```

**优势**: 3个Agent独立读取同一代码库，从不同维度发现不同类别的问题。另一全栈项目 V5实测：Agent 1发现类型标注问题，Agent 2发现伪收敛循环架构缺陷，Agent 3发现5个P0崩溃路径。单Agent不可能一次发现所有这些问题。

**流程**:
```
六部执行完成 → Gate验证通过 → Agent Team 3 Agent并行审核
  → 汇总3份报告 → 提取P0问题 → 修复P0 → 重新Gate验证 → 交付
```

### 审计报告格式
每个审计Agent应产出：
1. **评分** — 每文件/每维度 1-10分
2. **P0问题清单** — 必须修复（会导致崩溃/数据错误）
3. **P1问题清单** — 建议修复（逻辑缺陷/安全隐患）
4. **P2问题清单** — 择机优化（健壮性/可维护性）
5. **改进建议** — 按优先级排序

### 验证的审计模式
Experiment Hub项目验证了两轮独立审计：
- **迭代1审计**: 发现6个P0安全问题(eval注入/SQL注入/裸except/密码哈希/XSS/API无认证)
- **迭代2审计**: 验证P0修复有效性(3/9完全修复, 2/9部分修复, 4/9未修复)
- 审计报告保存到 `audit/audit_iter{N}.md`
- 每轮审计后主Agent修复P0问题，再进入下一轮

### 关键经验
1. **独立审计比自审有效** — 审计Agent发现的问题比主Agent自检多3倍
2. **审计报告要量化** — 用评分(如5.3/10)和具体行号，不要模糊描述
3. **P0修复要验证** — 第二轮审计专门验证第一轮P0修复的有效性
4. **审计Agent不能修改代码** — 只读权限，产出报告，主Agent负责修复

## Agent Team审核模式

当用户要求综合性审核时，用delegate_task(tasks=[...])派发2-3个Agent从不同角度并行审核。
详见 `references/agent-team-review-pattern.md`。

核心要点:
- 每个Agent只做一个视角(用户研究/产品设计/技术架构)
- Agent间不共享上下文
- 主Agent综合所有Agent的产出，找共识和矛盾
- Agent 2超时(600s)时需单独重跑

### 重构Sprint规划模板
```
Sprint R1: 基础设施升级 (Redis/PostgreSQL/连接池)
Sprint R2: 代码规范化 (Pydantic/UUID依赖/错误处理装饰器)
Sprint R3: DRY消除 (datetime统一/import整理/重复逻辑提取)
Sprint R4: 安全加固 (AI额度/审计日志/邀请码/XSS)
Sprint R5: Agent Team终审 + 修复 + 再审
```

### Redis集成模式
**统一连接工厂** — app/common/redis_pool.py单例模式:
- db0=限流(Lua原子脚本) / db1=登录锁 / db2=JWT黑名单
- 同步redis.Redis在async FastAPI中会阻塞事件循环，MVP可用，生产应改redis.asyncio

### PostgreSQL迁移模式
**UUID兼容层** — app/common/types.py: SQLite用String(36), PostgreSQL用原生UUID
**JSONB→JSON** — SQLite不支持JSONB，统一用from sqlalchemy import JSON
**.env铁律** — tar打包必须--exclude='backend/.env'，否则本地密码覆盖云端

### 安全加固检查清单 (14项全部验证)
密钥强制校验/DEBUG互斥/.env权限600/JWT黑名单fail-closed/登录限频5次5分钟/
Lua原子限流/XSS过滤/Prompt注入12模式/密码强度8位+大小写+数字/
白名单赋值/原子化SQL额度/文件上传白名单+流式/CORS显式/全局异常不泄露堆栈

### Agent Team审计迭代模式
审计分不会一次到位，需5轮迭代。7.0-8.0是"良好可用"，9.0+需架构级改造。

## Reference Files

- `references/full-project-audit-methodology.md` — **全量项目审计方法论**(4层Gate+设计文档对比+安全14项+Agent Team回退策略, 某全栈项目 验证)
- `references/alembic-async-sqlalchemy-setup.md` — **Alembic异步迁移指南**(同步驱动转换+SQLite batch模式+env.py模板, 某全栈项目 验证)

- `references/greenfield-cli-project-pattern.md` — **Greenfield project** pattern: CLI+API+Dashboard+SQLite architecture, 7-sprint sequence, gate verification via subprocess (validated )
- `references/engine-app-sprint-example.md` — Bid engine sprint delivery example
- `references/redis-security-infrastructure.md` — Redis-backed限流/登录锁/JWT黑名单模式(某全栈项目 V2.3验证)
- `references/fastapi-engine-pattern.md` — FastAPI multi-engine backend architecture

- `references/python-cli-api-project-scaffold.md` — Python CLI+FastAPI+SQLite项目脚手架Sprint结构、pyproject.toml模板、包结构、pitfalls(Experiment Hub验证)

- `references/fastapi-security-p0-checklist.md` — FastAPI安全审计P0清单(6项必查，某全栈项目实测验证)
- `references/greenfield-frontend-reference-pattern.md` — 参考前端代码作为实现指南的迁移模式
- `references/agent-team-material-review-gate.md` — Sprint开发前的Agent Team材料评审门控(3 Agent并行)

### 功能完成度计算方法
```
功能完成度 = 完全实现数 / 设计功能总数
完全实现 = 后端API + 前端页面 + 前后端打通（调用真实API）
部分实现 = 有代码但mock/未打通
```

## .env生命周期铁律

**tar打包会覆盖云端.env!** 每次上传必须排除.env：
```bash
tar czf backend.tar.gz --exclude='backend/.env' backend/
```
云端.env必须单独管理(密码/密钥与本地不同)。

### 端口隔离铁律
```
已有服务: 3010 (legacy 系统) — 不动
新系统后端: 8002 (FastAPI)
新系统前端: 3009 (Vite/Express)
```
启动前必须 `ss -tlnp` 确认端口未被占用。

### PostgreSQL迁移要点
- 安装: `sudo apt-get install -y postgresql postgresql-contrib`
- 创建用户: `sudo -u postgres psql -c "CREATE USER myapp WITH PASSWORD 'xxx';"`
- UUID兼容: 自定义 `app/common/types.py` 的 `UUID` TypeDecorator，PostgreSQL用原生UUID，SQLite用String(36)
- JSONB→JSON: `from sqlalchemy import JSON` 替代 `from sqlalchemy.dialects.postgresql import JSONB`
- .env铁律: **tar打包时必须排除.env**，否则本地PostgreSQL配置会覆盖云端SQLite配置

### systemd服务模板
```
[Unit]
Description=某全栈项目 Backend
After=network.target
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/myapp/backend
ExecStart=/home/ubuntu/myapp/backend/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
```

### .env生命周期铁律
- **打包上传时本地.env会覆盖云端.env** — 本地用PostgreSQL，云端用SQLite/不同密码
- 正确做法: tar用`--exclude='backend/.env'`排除，云端单独创建.env
- 云端密钥生成: `openssl rand -hex 32`
- 权限: `chmod 600 .env`

### 三库隔离
```
db0 = 限流 (rate_limit)
db1 = 登录锁定 (login_guard)  
db2 = JWT黑名单 (token_blacklist)
```

### 关键陷阱: 同步vs异步Redis
- FastAPI是async框架，但`redis.Redis`是同步客户端
- 同步Redis在async上下文中会阻塞事件循环
- 临时方案: 用同步Redis(可工作但性能差)
- 正确方案: `redis.asyncio` + async/await
- **生产环境必须用异步Redis**

### Lua原子限流脚本
```lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('INCR', key)
if current == 1 then redis.call('EXPIRE', key, window) end
if current > limit then return 0 end
return 1
```

### Token黑名单策略
- fail-open(Redis宕机时放行) = 安全漏洞
- fail-closed(Redis宕机时拒绝) = 可用性风险
- 推荐: fail-closed + 日志告警 + 降级到内存

### 品牌替换铁律
- `sed -i '' 's/OldName/NewName/g'` 处理90%文本
- JSX拆分元素（`Career<span>Forge</span>`）必须手动patch
- 验证: `grep -rn "OldName" src/` 确认零残留

### 审计-修复循环
```
第1轮: Agent Team审计 → 发现14个P0 → 修复 → 测试通过
第2轮: Agent Team重审 → 发现5个新P0 → 修复 → 测试通过
第3轮: Agent Team重审 → 0个P0 → 评分提升
第4轮: 代码优化 → 评分继续提升
```

### 评分提升规律
- 安全分提升最快(有明确修复模式): 5.3→8.5 (+3.2)
- 架构分中等(需要架构级改动): 6.0→8.0 (+2.0)
- 代码分提升最慢(需要深层重构): 6.0→7.5 (+1.5)

### 距9.0的典型差距
- Redis异步客户端
- Redis连接池化
- 全局中间件限流
- Alembic数据库迁移
- 异步任务队列
- 全面response_model覆盖

**Agent Team模型降级:** 3-Agent并行审核时，如果某个模型不可用(如GLM-5.1返回403)，该Agent会失败(max_iterations)。主Agent应立即用execute_code补充执行该维度的审核，不等待重试。
- Agent 1(代码质量)失败 → 主Agent用regex扫描P0/P1问题
- Agent 3(安全审核)失败 → 主Agent检查认证覆盖/密码存储/.env安全
- 降级后仍可产出完整审计报告，只是深度略降

**Pipeline v3 审计→修复循环:**
```
审计(4层Gate + Agent Team) → 产出P0清单 → Writer批量修复 → 审查Agent验证 → 验收Gate确认
```
修复阶段不需要重新全量审计，只需验证P0是否真正修复。验收Gate检查:
1. 具体P0是否消除(如双参数bug→grep确认只有单参数)
2. 删除的文件是否真的不存在
3. 路径修复后前后端是否匹配
4. 全量py_compile确认无语法错误
5. main.py router数量是否正确

## Pitfalls

**.env被tar覆盖** — 打包上传时本地.env会覆盖云端.env。症状: PostgreSQL密码不对→500。修复: tar用`--exclude='backend/.env'`，云端单独维护.env。**每次打包前必须检查是否排除了.env。**

**bcrypt 5.x与passlib不兼容** — bcrypt 5.x移除__about__模块，passlib无法读取版本。修复: `pip install 'bcrypt==4.0.1'`。症状: register返回500。

**Redis同步客户端在async框架中** — FastAPI用async但redis.Redis是同步的。症状: 登录锁显示`<coroutine object>`而非秒数。修复: 用`redis.Redis`(同步)而非`redis.asyncio`，或确保所有Redis调用都是同步的。

**FastRouter双body参数BUG** — `async def f(data: Schema, req: Schema)` 两个同类型body参数导致422。修复: 只保留一个参数名(统一用`data`)。**复现**: learning/router.py 3个函数(create_plan/update_learning_progress/issue_certificate)全部有此bug,用正则 `async def \w+\(.*data:\s*\w+.*req:\s*\w+` 可批量检测。

**Pydantic模型用.get访问** — 将`data: dict`改为`data: PydanticModel`后，`data.get("key")`报AttributeError。必须改为`data.key`。**改schema后立即grep所有.get(调用。**

**测试脚本密码不符合强度要求** — 添加密码强度校验后，测试脚本的`test123456`不满足"大写+小写+数字"要求，导致注册400。修复: 测试密码改为`Test123456!`。

**云厂商安全组未开放端口** — 服务在云端正常运行但外部无法访问。症状: curl返回000。原因: 云厂商安全组只开放了3010，未开放3009/8002。修复: 在云厂商控制台→防火墙→添加规则。

**公网000三层诊断序（服务 active 但外网 000 时）** — 000 有三个独立成因，按序排除：①监听绑定面：`sudo ss -tlnp | grep PORT` 若是 `127.0.0.1` 而非 `0.0.0.0`，是进程自身没放开绑定（常见=代码要求显式环境变量开关如 `Environment=ZHIJI_DEPLOY=1` 而 unit 没配）；②服务器防火墙 `sudo ufw status`；③云控制台安全组/防火墙规则。只查③不查①会在"服务 active+冒烟 000"的假绿假红之间空转。

**老 systemd 不支持 `systemctl edit --stdin` 且静默失败** — 部署脚本用 `systemctl edit --stdin` 写 override 在旧版本 systemd 上报 unrecognized option 后若被吞掉，unit 无 Environment → 服务仍 active 但绑 127.0.0.1，故障极难归因。可移植写法：直写 override 文件 `sudo mkdir -p /etc/systemd/system/<unit>.d && printf '[Service]\nEnvironment=K=V\n' | sudo tee /etc/systemd/system/<unit>.d/x.conf && sudo systemctl daemon-reload`，并用 `systemctl show <unit> -p Environment` + `ss -tlnp` 双验证落地。

**Gate 3误报：间接API调用和静态页面**
- 错误: LoginPage/RegisterPage被标记FAIL(无直接api.引用) → 实际通过AuthContext间接调用
- 错误: PricingPage被标记FAIL → 实际是静态展示页，不需要API调用
- 修复: grep模式改为 `grep -E 'api\.|API\.|fetch\(|useAuth|useQuery'`，增加静态页面豁免列表
- 规则: LandingPage/PricingPage等纯展示页面不参与"前后端打通"检查

**Agent Team 2/3模型不可用导致降级**
- delegate_task的3个Agent中2个因GLM-5.1返回403失败
- 主Agent用execute_code自行补充代码质量+安全审核
- 降级审核深度低于独立Agent(只做regex扫描,不做逐文件阅读)
- 预防: delegate_task时指定可靠的模型,或在context中注明备选模型

**跳过Gate直接进下一个Sprint** — 用户要求"连续交付"
Agent Team审计发现后端25个API端点全部实现，但前端14个组件全部使用mock数据（setTimeout、硬编码常量），前后端完全未打通。最终完成度仅45%。用户明确判定"交付失败"。Gate验证必须包含"前端是否调用后端API"检查。详见 `references/fullstack-delivery-verification.md`。

**参考前端风格未对齐 **
用户提供了参考前端zip，但自建前端使用了完全不同的视觉风格。正确做法是直接使用参考代码，只修改server.ts添加后端代理。详见 `references/fullstack-delivery-verification.md`。

**跳过Gate直接进下一个Sprint**

**审计Agent模型不可用回退** — delegate_task的3个Agent全部因GLM-5.1模型403失败。回退策略: 主Agent直接用execute_code+regex执行等效审核。单次失败后立即切换策略，不要浪费重试。

**P0审计循环** — 一次审计不可能发现所有问题。正确的模式是:
```
初始审计(发现14个P0) → 修复 → 重审(发现5个新P0) → 修复 → 重审(发现1个新P0) → 修复 → 重审(P0=0)
```
每次修复都可能引入新问题(如import改名后引用未更新、duplicate代码未删干净)。必须迭代审计直到P0=0。

**跳过Gate直接进下一个Sprint** — 用户要求"连续交付"不等于"跳过验证"。每个Sprint必须跑Gate，这是质量保证的底线。

**alembic + async SQLAlchemy env.py ** — alembic的env.py必须用同步引擎,不能用`async_engine_from_config`。`psycopg2`不是async驱动,`async_engine_from_config`会报`InvalidRequestError: The asyncio extension requires an async driver`。正确做法:
```python
# 正确: 同步引擎
from sqlalchemy import engine_from_config, pool
connectable = engine_from_config(config.get_section(...), prefix="sqlalchemy.", poolclass=pool.NullPool)

# 错误: 异步引擎 (alembic不支持)
from sqlalchemy.ext.asyncio import async_engine_from_config  # ← 会失败
```
URL转换: `+aiosqlite` → 直接去掉, `+asyncpg` → `+psycopg2`。
SQLite的ALTER TABLE限制需要`render_as_batch=True`。
`alembic stamp head`标记已有数据库为最新(跳过初始migration)。
详见 `references/alembic-async-sqlalchemy-setup.md`。

**批量Sprint跳过中间备份** — 开发多个Sprint时，试图将3-7合并为一次备份。用户明确纠正："每个阶段的产出要按照备份要求进行全量备份"。规则：每个Sprint完成后必须执行完整的四级备份(Git/文件/记忆库/会话记录)，不能因为"连续开发"就跳过中间Sprint的备份。批量开发可以，但批量备份不行。

**PostgreSQL云端部署.env覆盖** — tar打包上传时本地.env覆盖云端.env，导致PostgreSQL密码不匹配(asyncpg认证失败)。症状：systemd反复restart，日志显示InvalidPasswordError。修复：(1)tar时--exclude='backend/.env'；(2)部署后立即sed替换密码；(3)本地.env密码与云端统一。详见references/postgresql-cloud-migration.md。

**AI mock响应关键词匹配顺序** — 当多个功能共享一个mock响应函数时，prompt中的JSON模板示例(如score: 0-100)会触发错误的关键词匹配。症状：学生决策返回面试评分格式。修复：(1)将更具体的匹配放在前面(职业规划顾问优先于score)；(2)用组合条件而非单一关键词。

**CSS/HTML补丁静默失败** — 在大HTML文件(>500行)中用patch替换CSS或JS时，字符串匹配可能因空白差异或转义字符失败。症状: 补丁返回success但内容未改变。验证方法: `grep -c "目标字符串" file.html`确认替换生效。失败时用execute_code直接read+replace+write。实验中枢项目中多次遇到此问题。

**渐变导致可读性问题** — 用户明确要求"不用渐变"。深色主题Dashboard使用纯色方案，详见`dashboard-ui-patterns` skill。

**中文描述缺失** — 技能/工具列表默认显示英文描述。需要维护CN_DESCRIPTIONS映射表或在API层注入中文描述。

**read_file输出写入文件导致语法损坏** — `read_file`返回的内容带行号前缀`     N|`。

**Python版本不一致** — macOS homebrew Python(3.11) vs execute_code Python(3.12)。FastAPI脚本必须用 shebang `#!/usr/bin/env /opt/homebrew/bin/python3` 指定正确路径，或用 `$(which python3)` 确认。

**background进程使用错误Python版本** — `terminal(background=True)` 启动的进程继承的PATH可能与前台shell不同。前台shell的`python3`解析到3.11(Homebrew)，但后台进程的`python3`解析到3.9(系统`~/Library/Python/3.9/`)。症状：后台FastAPI启动报`ModuleNotFoundError`但前台`python3 -c`正常。
- 修复：后台进程必须用绝对路径 `/opt/homebrew/opt/python@3.11/bin/python3.11`
- 验证：`python3 -c "import site; print(site.getsitepackages)"` 对比前后台输出
- 同理适用于`pip install`：必须用`/opt/homebrew/opt/python@3.11/bin/python3.11 -m pip install`

**read_file输出写入文件导致语法损坏** — `read_file`返回的内容带行号前缀`     N|`。如果agent将此输出误写入文件(如通过execute_code中的write_file)，Python文件会被损坏(每行前面有`     1|`)。症状：`IndentationError: unexpected indent`。
- 诊断：`head -1 file.py | grep -q "^[[:space:]]*[0-9]*|"` 检查是否有行号前缀
- 批量修复：`sed -i '' 's/^[[:space:]]*[0-9]*|//' file.py`
- 预防：execute_code中read_file返回的content如果要写回文件，必须先strip行号前缀

**Agent Team模型不可用** — delegate_task派发3个Agent并行审核, 2/3因GLM-5.1 token无权限失败(HTTP 403)。症状: exit_reason=max_iterations, error含"no access to model"。根因: 子Agent继承当前provider的模型, 但token可能无该模型权限。预防: (1)在prompt中指定toolsets=['terminal','file']减少模型依赖; (2)准备手动fallback(主Agent自己执行审核); (3)关键审核不要只靠Agent Team, 主Agent同步做一份。详见references/full-project-design-audit.md。

**并行Agent修改同一文件** — delegate_task的两个子Agent如果都修改 page.tsx, 后写的会覆盖先写的。解决方案：明确划分文件边界, 或串行处理共享文件。

**骨架交付≠功能完成** — 用户要求"全量开发"时，交付mock/stub/空壳页面=交付失败。审计结果显示45%完成度时用户明确说"你这个项目的交付是失败的"。正确做法: 每个功能必须有真实后端逻辑+真实前端UI+前后端打通，三者缺一不可。Gate验证必须检查"功能是否真正可用"而非"文件是否存在"。

**端口冲突未检查** — 前端默认用3001端口，但用户说"3001端口是其它系统使用的，不要占用"。启动服务前必须`lsof -i :PORT`检查端口是否被占用。推荐: 后端8001, 前端3009(避免与常见开发端口冲突)。

**参考前端代码适配模式** — 当用户提供参考前端代码(zip/仓库)时，正确流程是: (1)解压到项目目录 (2)安装依赖 (3)修改品牌名(全局sed替换) (4)修改server.ts添加后端代理 (5)按产品故事流重新组织页面顺序 (6)新增缺失页面组件。错误做法: 自己从零重写前端→风格不一致。正确做法: 基于参考代码修改→风格完全一致。

**页面故事流排列** — 页面/Tab顺序必须按用户旅程故事流排列，不能按功能模块随意排列。某全栈项目的正确故事流: 控制台(概览) → 简历诊断(入口) → 简历优化(深化) → 职业实验(探索) → AI面试(验证) → 求职管理(行动) → 大学生专项(细分) → 个人设置(管理)。用户原话:"页面顺序要按照故事流进行，不要跳跃"。

**骨架/mock代码当交付物** — 用户明确判定"交付失败"。开发Agent倾向于写骨架+mock数据+setTimeout模拟，而不是真正调用后端API。根因：追求文件数量而非功能完整度。
- 错误模式: 前端页面用MOCK_JOBS/mock数据/setTimeout，后端API未被任何组件调用
- 正确模式: 每个页面必须用真实API调用(resumeAPI/interviewAPI等)，mock仅作为AI无API Key时的降级
- 验证方法: `grep -rn 'setTimeout\|MOCK_\|// Mock' web/src/components/` 检查是否有mock残留
- 验证方法: `grep -rn 'api\.\|API\.' web/src/components/` 础认组件有真实API调用
- Gate验证必须加: "前后端打通检查" — 每个页面必须有至少一个真实API调用

**需求-功能对比审查缺失** — 用户要求"确保所有设想和需求都已完成"。在声称"完成"前，必须派发独立Agent对比设计文档(part3_features.md)与实际代码，逐项标记完成状态。
- 错误模式: 只统计文件数和代码行数，不做功能对比
- 正确模式: 派发独立Agent读取设计文档站点地图，逐功能检查后端API+前端页面+前后端打通
- 输出: 功能对比表(功能名|后端API|前端页面|完成状态) + 完成度百分比

**Workspace version drift ** — Running service serves older version than local file. Root cause: process reads from a different directory than the latest source. Diagnostic: `lsof -i :PORT` → get PID → `ps aux | grep PID` → check `cwd` and command path. The process may be running from `~/projects/ai-dashboard/` while the latest file is in `~/Desktop/hermes-workspace/`. Fix: copy latest file to the directory the process reads from, then restart. Prevention: always check which directory the serving process uses before assuming the local file is what's being served.

**端口冲突未检查** — 前端占用3001端口，用户告知该端口被其他系统使用。
- 规则: 启动服务前先检查端口 `lsof -i :PORT`
- 默认端口: 后端8001, 前端3009(避免与常用服务冲突)

**参考前端风格未对齐** — 用户给出参考代码(zip)，要求布局/颜色/交互完全一致。Agent自己重写的前端风格与参考差异大。
- 规则: 用户提供参考代码时，直接使用参考代码(解压替换)，不要自己重写
- 规则: 如果需要修改参考代码，先截图对比确认视觉一致，再做最小改动
- 规则: 参考代码的技术栈(如Vite vs Next.js)保持不变，不要擅自切换框架

**Sprint规划过粗** — "做一个完整系统"不是一个Sprint。每个Sprint应有3-5个具体任务 + 1个可验证的Gate条件。

**子agent超时(600s限制)** — 当delegate_task处理大型代码库(>10K行)时，子agent需要先读取大量文件才能开始修改，容易耗尽600s超时。解决方案：(1) 将一个大task拆成2-3个小task，每个只处理2-3个文件；(2) 在context中直接给出文件关键内容而非让子agent自己读取；(3) 对于"修复所有旧引用"类任务，先从主agent用terminal/grep找出精确的文件和行号，再delegate具体修复。

**用户说"继续"时不要重复规划** — 用户已确认方案后说"继续"，期望看到立即的文件创建/代码修改，而不是又一次方案输出。直接开始执行execute_code或write_file。

**Python f-string中JSON花括号转义** — f-string中嵌入JSON格式示例时,`{{`和`}}`是转义的字面花括号,但`{", ".join(...)}`中的嵌套花括号会导致`SyntaxError: f-string: single '}' is not allowed`。症状: py_compile报错但肉眼看不出问题。修复: 将JSON格式示例在f-string外构建为普通字符串,再通过变量插入f-string。Agent Team审计Agent 1专门发现此问题。

**Pydantic模型替换dict后属性访问错误** — 将路由参数从`data: dict`改为`data: PydanticModel`后，`data.get("key")`会报`AttributeError: 'Model' object has no attribute 'get'`。必须改为`data.key`。同一个router中部分函数改了schema但函数体内仍用.get会导致运行时500。症状：审计Agent反复发现此问题，每次修复后新代码又引入。预防规则：(1)改schema后立即grep该router所有`.get(`调用并替换；(2)用`data.xxx`而非`data.get("xxx")`；(3)路由函数签名参数名统一用`data`不要混用`req`。

**路由参数名混乱** — 同一个router中部分函数用`data: Schema`，部分用`req: Schema`，部分函数签名有两个同类型参数(`data: X, req: X`)导致运行时崩溃。预防规则：(1)整个router统一用`data`作为参数名；(2)每个函数签名只声明一个请求体参数；(3)改完后grep确认无`req.xxx`残留。

**前后端API路径不匹配** — 前端api.ts定义的路径与后端router注册的路径不一致,上线即404。案例:前端`/student/decision-helper` vs 后端`/student/decision`。检测方法:用正则提取前端api.ts中所有路径和后端router中所有路径,逐一对比。Gate 3必须加"路径一致性检查":
```python
# 前端路径
frontend_paths = re.findall(r'["\'](/api/v1/[^"\']+)["\']', api_ts_content)
# 后端路径(加上prefix)
backend_paths = [prefix + route for router in routers]
# 对比
mismatch = set(frontend_paths) - set(backend_paths)
```

**Redis安全基础设施模式** — 当系统需要Redis做限流/登录锁定/Token黑名单时：
1. 用Redis不同db隔离：db0=限流, db1=登录, db2=黑名单
2. 限流用Lua脚本原子INCR+EXPIRE（非原子操作在高并发下窗口错位）
3. 登录锁定：5次失败→写入lock key(TTL=300s)→检查lock key是否存在
4. Token黑名单：logout时`SET blacklist:{token} 1 EX 86400`，认证时`EXISTS blacklist:{token}`
5. 每个模块独立get_redis_db(db)连接，不要共享一个连接
6. 必须有内存降级（Redis不可用时fallback到内存dict）

**.env生命周期铁律** — 打包上传时本地.env会覆盖云端.env！
- 本地用PostgreSQL，云端用SQLite，DATABASE_URL不同
- tar打包时**必须**用`--exclude='backend/.env'`排除
- 云端.env在部署脚本中单独创建（用`openssl rand -hex 32`生成密钥）
- 验证：部署后立即`cat ~/myapp/backend/.env | grep DATABASE_URL`确认

**bcrypt版本锁定** — bcrypt 5.x移除`__about__`模块导致passlib崩溃。requirements.txt必须pin `bcrypt==4.0.1`。

**datetime统一铁律** — 项目内禁止混用`datetime.utcnow`(naive)和`datetime.now(timezone.utc)`(aware)。选一个统一使用。推荐`datetime.now(timezone.utc).replace(tzinfo=None)`。修复后grep确认零残留：`grep -rn 'datetime.utcnow' app/`。

**null字节污染write_file** — hermes_tools.write_file写Python文件偶尔引入`\x00`。每次批量write_file后必须运行清理脚本（见上方）。预防：write_file后立即py_compile验证。

**Python中文方法名违反PEP8** — `def _methodology解读(self)`虽在Python语法上合法,但违反snake_case规范,影响代码搜索/重构工具兼容性,且会传染到配置文件的dict key。Agent Team审计Agent 1发现此问题并标记为P0。修复: 全部改为英文`_methodology_explainer`。

**嵌套dict浅拷贝导致配置污染** — `hooks = UPGRADE_HOOKS.get("key", {}).copy`是浅拷贝,修改`hooks["ch2"]["text"]`会修改原始全局配置。第二次调用时模板变量`{n_surprise}`已被替换且不可恢复。Agent Team架构Agent发现此问题。修复: `import copy; hooks = copy.deepcopy(config.get(...))`。

**TIER_GATE section命名不匹配导致门控失效** — config中定义`TIER_GATE["path"] = PATH_FIELDS`,但调用方用`gate_fields("action", data, tier)`。section名不匹配导致返回空dict,所有字段被过滤。Agent Team架构Agent发现此问题。修复: 确保config中的section名与调用方一致,或在gate_fields中对未知section打warning。

**gate_fields未知section应返回空而非原始数据** — 原实现`if not allowed: return data`(返回未过滤的全部字段)。当section名拼写错误时,所有数据泄露给前端。修复: `if not allowed: return {}`(安全默认值)。

**多产品升级的Sprint编排模式** — 当同时升级N个产品时，推荐编排：Sprint1=备份+基线文档 → Sprint2=共享基础设施(认证/门户) → Sprint3-N=逐产品升级(每个产品1-2个Sprint) → Sprint N+1=联调 → Sprint N+2=审计+交付。详见references/multi-product-upgrade-pattern.md。

**bcrypt 5.x与passlib不兼容** — bcrypt 5.0移除了`__about__`模块，passlib依赖它检测版本。症状：`AttributeError: module 'bcrypt' has no attribute '__about__'`，注册/登录全部500。修复：`pip install 'bcrypt==4.0.1'`。必须在requirements.txt中pin版本。

**Pydantic UUID/Enum序列化失败** — SQLAlchemy模型的UUID主键和Enum字段（如SubscriptionTier）传给Pydantic response_model时，如果schema中定义为`str`但没有validator，Pydantic不会自动转换。症状：API返回空或500。修复：在schema中加`@field_validator("id", mode="before")`做`str(v)`转换，Enum字段同理。每个使用`from_attributes=True`的response schema都需要检查。

**AI mock响应关键词匹配顺序** — 当多个功能共享一个mock响应函数时，prompt中的JSON模板示例（如`"score": 0-100`）会触发错误的关键词匹配。症状：学生决策返回面试评分格式。修复：(1)将更具体的匹配放在前面（"职业规划顾问"优先于"score"）；(2)用组合条件而非单一关键词（"score" AND "overall_score"而非单独"score"）。

**集成测试脚本模式** — 写一个Python测试脚本用urllib直接调用API，避免curl的f-string转义问题。脚本用随机手机号避免额度限制冲突。模式：注册→登录→拿token→测试所有端点→输出PASS/FAIL统计。详见`references/fullstack-integration-test-pattern.md`。

**前端组件未调用后端的检测方法** — 用`grep -rn 'setTimeout\\|MOCK_\\|// Mock' web/src/components/`检测前端是否用了mock数据。用`grep -rn 'fetch\\|axios\\|api\\.' web/src/components/`检测是否有真实API调用。两者结合判断前后端是否真正打通。

**修复未集成反模式** — 创建了utility模块(如usage.py/response.py)但没有在任何router中import使用。审计Agent会检查import链。症状：声称修复了P0但审计评分不升反降。预防：(1)修复后grep确认新模块被实际import；(2)集成测试验证修复生效。

**旧代码残留反模式** — 用新实现替换旧逻辑时，旧代码没有完全删除。症状：`NameError: name 'now' is not defined`（旧的usage reset代码引用了已移除的变量）。预防：patch替换后，重新read_file确认目标区域没有残留代码。

**write_file引入null字节** — 通过execute_code调用write_file写Python文件时，偶尔会在文件中引入`\x00`字节。症状：`SyntaxError: source code string cannot contain null bytes`，Python无法import。修复：`python3 -c "data=open(f,'rb').read; open(f,'wb').write(data.replace(b'\\x00',b''))"`。预防：每次大规模write_file后，用`find app -name '*.py' -exec python3 -m py_compile {} \\;`验证。

**审计-修复循环模式** — 当用户要求"达到9.5分"时，需要多轮审计-修复循环：
```
第1轮: Agent Team审计 → 发现14个P0 → 修复 → 20/20测试通过
第2轮: Agent Team重审 → 发现5个P0(含3个未集成) → 修复 → 20/20通过
第3轮: Agent Team重审 → 0个P0 → 评分7.0/7.0/7.5
第4轮: 代码优化(imports/模板拆分/CORS/密码策略) → 评分7.0/7.0/7.5
```
关键发现：安全分提升最快(4.4→7.5,+3.1)，代码质量和架构分提升较慢(每个+0~0.5)。因为安全问题有明确的修复模式(白名单/限流/sanitize)，而代码质量需要深层重构(原子SQL/异步队列/全局中间件)。
