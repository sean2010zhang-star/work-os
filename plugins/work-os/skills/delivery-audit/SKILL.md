---
name: delivery-audit
version: 1.0.0
description: 交付审计 — 四类Gate（pre-flight/revision/escalation/abort）自动检查 + 审计报告 + 自动归档
related_skills: [work-os-router, consolidated-iron-laws, sprint-with-tiers]
---

# Delivery-Audit — 交付审计

## 触发条件
任务执行完成后自动触发。基于 delivery-retrospective + ai-dashboard-delivery-checklist 增强。

## Sprint连续交付模式（v2.0新增）

当用户要求"持续开发"、"连续Sprint"、"自动执行下一个Sprint"时，使用此模式：

### 执行流程
```
Sprint N 规划 → 前后端并行开发 → Gate验证 → 交付4件套 → 自动进入 Sprint N+1
```

### 每个Sprint标准产出
1. 后端引擎/模块代码
2. 前端组件代码
3. API路由注册
4. 集成测试（通过proxy验证端到端）

### Sprint间自动衔接
- Gate全部PASS后自动 `git commit + tag (v2.0-sprint-N)`
- 更新 todo list 标记当前Sprint完成
- 立即开始下一个Sprint（不等用户确认）
- 后端重启后必须等待3秒再测试(否则连接拒绝)
- 前端子代理耗时较长(~3-4分钟)，可与后端工作并行

### Sprint文件增长模式
```
Sprint 1: +5 files  (骨架: base.py + schema + parser + main.py + 前端上传)
Sprint 2: +5 files  (引擎×2 + schema + 前端组件×2)
Sprint 3: +4 files  (引擎×2 + 前端组件×2)
Sprint 4: +4 files  (引擎×1 + pipeline + 前端集成 + API更新)
Sprint 5: +3 files  (引擎×1 + 前端组件×1 + API更新)
Sprint 6: +3 files  (引擎×1 + 前端集成 + API更新)
```
每个Sprint的main.py更新频率最高（每Sprint添加import+实例化+端点）。
建议用代码执行工具批量创建引擎文件，patch更新main.py。

### 交付4件套
1. Git commit + tag
2. 功能验证（Gate检查）
3. 记忆库项目文档
4. 会话记录会话记录

## 四类Gate

### Gate 1: Pre-flight（交付物存在性）
- 文件是否已生成？
- 大小是否合理（非空）？
- 不通过 → 记录error_log，通知本体系

### Gate 2: Revision Gate（质量检查，≤3次）
- 对照开发/设计标准逐项检查
- 每项：pass/fail + 具体问题描述
- fail → 打回Agent修复，附问题清单
- 3次不通过 → Gate 3

### Gate 3: Escalation（用户决策）
- 向用户展示不达标项
- 用户选择：强制通过 / 继续修复 / 放弃任务

### Gate 4: Abort Gate（异常终止）
- 异常情况 → 停止执行
- 记录error_log
- 通知用户

## 审计报告格式

```
╔══════════════════════════════════╗
║      DELIVERY AUDIT REPORT       ║
╠══════════════════════════════════╣
║ Task: <task_name>                ║
║ Date: <audit_date>               ║
║ Agent: <executing_agent>         ║
╠══════════════════════════════════╣
║ Gate 1 Pre-flight: PASS/FAIL     ║
║ Gate 2 Revision: PASS/FAIL (Nx)  ║
║ Gate 3 Escalation: N/A/PASS      ║
║ Gate 4 Abort: N/A                ║
╠══════════════════════════════════╣
║ Details:                         ║
║   [1] <check_item>: PASS         ║
║   [2] <check_item>: FAIL → ...   ║
╠══════════════════════════════════╣
║ Conclusion: PASS/FAIL            ║
║ Archive: Git+记忆库                 ║
╚══════════════════════════════════╝
```

## 自动归档触发
所有Gate通过后：
1. Git commit + version tag
3. 记忆库 md文件
4. 写入任务卡片（POST /api/tasks/:id/audit）

## API集成
- POST /api/tasks/:id/deliver → 触发审计
- GET /api/tasks/:id/audit → 获取审计报告
- 审计结果写入任务卡片meta

## Architecture Reference
See `references/fastapi-nextjs-dual-server.md` for reusable FastAPI+Next.js dual-server architecture pattern (proxy routing, engine-based backend, startup commands).
See `references/sidebar-step-navigation-pattern.md` for sidebar step-navigation UI pattern (document-driven multi-step workflows).
See `references/criteria-extraction-pattern.md` for bid document criteria extraction (keyword expansion, dynamic extraction, table parsing).

## 交付4件套（标准交付物）

每次Sprint交付必须包含：
1. **Git commit** — feat: Sprint N complete - [description]
2. **Gate验证报告** — Python syntax + Frontend build + API health
3. **交付审计报告** — docs/sprintN-delivery-report.md（用本skill的审计报告格式）
4. **版本tag** — 里程碑版本打tag（如 v0.1.0-mvp）
5. **状态更新** — todo list更新为completed

## 项目版本归档流程（用户要求全量备份时使用）

当用户说"全量备份"、"归档"、"准备迭代"时，执行以下流程：

### Step 1: 代码备份
```bash
# 创建Git tag
git tag -a vX.Y-stable -m "项目名 VX.Y Stable — 功能摘要"
# 生成归档zip（排除node_modules/.git）
git archive --format=zip --prefix=项目名/ -o <release-dir>/项目名-vX.Y-stable.zip vX.Y-stable
```

### Step 2: 文档全量更新（并行）
用子代理并行更新3份核心文档：

1. **PRODUCT_FULL_SPEC.md** — 产品需求文档对齐实际功能
   - 章节: 概述/用户画像/功能需求(每页详细)/技术架构/数据模型/API文档/非功能需求/版本规划
2. **FEATURE_LIST.md** — 功能清单
   - 逐页面: 布局/交互/数据流/截图占位符
3. **DELIVERY_REPORT.md** — 交付报告
   - 章节: 概览/前端清单(行数+功能)/后端清单/已知问题/启动指南/后续规划

### Step 3: XMind全景脑图
用Python zipfile生成.xmind文件（零依赖），覆盖5大分支：
产品概述 / 前端页面 / 后端架构 / 技术实现 / 版本规划

### Step 4: 最终归档
```bash
git add -A && git commit -m "docs: 全量文档更新 + XMind脑图"
git tag -d vX.Y-stable; git tag -a vX.Y-stable -m "..."
git archive --format=zip -o <release-dir>/项目名-vX.Y-stable.zip vX.Y-stable
```

**产出物清单**：
- Git tag `vX.Y-stable`
- `<release-dir>/项目名-vX.Y-stable.zip`
- 3份更新后的.md文档
- 1份.xmind脑图

## 软件Sprint交付模式

将四类Gate应用于软件开发Sprint：

### Sprint Gate检查清单
```
Gate 1 Pre-flight:
  [ ] 所有新增Python文件 py_compile通过
  [ ] 前端 npm run build 通过（含vue-tsc类型检查）
  [ ] 文件数量与预期一致
  [ ] 无未使用的import（TS6133）

Gate 2 Revision:
  [ ] API端点可访问（curl健康检查）
  [ ] 前端页面渲染无JS错误（browser console）
  [ ] 数据库Schema与ORM模型一致
  [ ] Git commit message符合规范

Gate 3 Escalation（仅FAIL时）:
  [ ] 向用户展示不达标项
  [ ] 用户选择：强制通过/继续修复

Gate 4 Abort（仅异常时）:
  [ ] 记录error_log
  [ ] 通知用户
```

### 交付4件套
每个Sprint完成后必须产出：
1. Git commit（feat: Sprint N complete）
2. 交付审计报告（docs/sprintN-delivery-report.md）
3. 代码验证通过（Python syntax + Frontend build）
4. 功能验证（API端点 + 页面渲染）
5. 版本tag（可选，里程碑时使用）

### 连续Sprint模式
用户要求"持续开发"时，Sprint间不暂停。Gate PASS后直接开始下一个Sprint。只有Gate FAIL时才暂停。

## Sprint连续交付模式

当用户要求"连续Sprint"时，Gate验证嵌入每个Sprint结束：

```
Sprint N → Gate 1+2 → 4件套(Git tag + 会话记录 + 记忆库 + 状态) → Sprint N+1
```

Gate全部PASS → 自动推进，不等用户确认。
Gate有FAIL → 修复后重新验证，3次FAIL → Escalation。

详细流程见 `sprint-gated-delivery` skill。

## Pitfalls

### 代码执行工具 read_file → write_file 行号污染
`代码执行工具` 中调用 `read_file()` 返回的内容**带有行号前缀**（如 `     1|\"use client\";`）。如果直接将此内容传给 `write_file()`，行号会成为文件内容的一部分，导致构建失败。

**错误模式:**
```python
r = read_file("/path/to/file.tsx")
write_file("/path/to/file.tsx", r["content"])  # ❌ 行号被写入
```

**修复:**
```python
import re
r = read_file("/path/to/file.tsx")
lines = r["content"].split("\n")
cleaned = [re.sub(r'^\s*\d+\|', '', line) for line in lines]
write_file("/path/to/file.tsx", "\n".join(cleaned))
```

**替代方案:** 用 `patch()` 做精确替换，避免读写整个文件。

### .next/ 等构建目录被Git追踪
Next.js项目的 `.next/` 目录如果在首次commit前没有 `.gitignore`，会被git追踪。后续每次 `git status` 都会显示大量无关的构建文件变更，干扰真正的代码变更。

**症状:** `git status` 显示数十个 `.next/` 文件变更，实际代码改动只有几个文件。

**修复:**
```bash
# 从git索引中移除（保留本地文件）
git rm -r --cached .next/
git commit -m "chore: remove .next from tracking"
```

**预防:** 创建Next.js项目时，第一步就确认 `.gitignore` 包含 `.next/`、`node_modules/`、`*.tsbuildinfo`。

### Python环境路径（macOS Homebrew）
FastAPI后端必须显式使用 `/opt/homebrew/bin/python3`，系统默认 `python3` 可能没有安装 fastapi/uvicorn 等包。
```bash
# 正确
/opt/homebrew/bin/python3 main.py
# 可能失败（系统Python没有fastapi）
python3 main.py
```

### 前端功能完整性检查
用户反馈："前端页面似乎没有把当初功能都设计完"。根因：前端只实现了部分PRD功能，缺少完整的业务流程串联。

**症状**: 页面有基本UI但缺少关键流程步骤（如只有上传没有评审结果、只有单步没有多步流程）。

**预防 — PRD对齐检查清单**:
```
[ ] 对照PRD功能清单逐项核对前端实现
[ ] 业务流程是否完整串联（不只是单页面功能）
[ ] 是否有"下一步"引导（用户不知道接下来做什么）
[ ] 历史记录/状态持久化是否实现
[ ] 文件大小限制是否合理（大项目需500MB+）
```

**设计模式 — 侧边栏步骤导航**（适用于文档驱动的多步流程）:
```
┌──────┬─────────────────────────────┐
│ 侧边栏 │       主内容区                │
│      │                             │
│ ① 上传招标  ← 当前高亮              │
│ ② 上传投标  ← 已完成(绿色勾)         │
│ ③ 一键评审  ← 待解锁(灰色)           │
│ ④ 评审结果                           │
│ ──── │                             │
│ 📁 历史                             │
└──────┴─────────────────────────────┘
```
状态机: completed(Set) + current(step) + locked(未解锁)
点击条件: 只能点击已完成步骤的下一步或当前步骤
组件: `Sidebar.tsx` 固定左侧240px, `page.tsx` 按step切换内容

### Pydantic验证 + pymupdf表格None值
pymupdf的 `tab.extract()` 返回的表格单元格可能为 `None`（空单元格）。
如果Pydantic模型定义为 `list[list[list[str]]]`，验证会报错：
```
Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
```

**修复方案（双重保险）:**
1. Schema类型放宽: `list[list[list[str | None]]]`
2. Parser提取时清洗: `[[cell if cell is not None else "" for cell in row] for row in raw]`

```python
# schemas/document.py
class PageContent(BaseModel):
    tables: list[list[list[str | None]]] = []

# parsers/document_parser.py
raw = tab.extract()
clean = [[cell if cell is not None else "" for cell in row] for row in raw]
tables.append(clean)
```

**教训:** 外部库返回的数据永远不能信任其类型，必须做防御性清洗再传入Pydantic模型。

## Sprint连续执行模式

当用户要求"每个Sprint完成后自动执行下一个Sprint"时，使用以下模式：

### Sprint结构模板
每个Sprint遵循固定结构：
1. **后端引擎创建** — `代码执行工具`批量写入Python文件(engine + schema)
2. **API路由更新** — `patch` main.py添加import + 实例化 + 端点
3. **后端重启** — `process kill` → `terminal background`启动新进程
4. **前端组件** — `子代理`并行创建TSX组件(含暗色主题)
5. **构建验证** — `npx next build` 确认TypeScript通过
6. **Gate验证** — 代码执行工具运行完整审计(文件检查+API测试+构建)
7. **Git提交+Tag** — `git add` → `git commit` → `git tag -a v2.0-sprintN`
8. **会话记录记录** — 写入会话记录

### Gate验证脚本模式
```python
# Gate 1: 文件存在性 (read_file检查每个文件)
# Gate 2: API端点 (curl每个端点验证返回)
# Gate 3: 引擎完整性 (curl /api/health检查引擎数量)
# Gate 4: 构建 (npx next build)
```

### 连续Sprint注意事项
- 每个Sprint的Git tag必须在下一个Sprint开始前打上
- 后端重启后必须等待2-3秒再测试(否则连接拒绝)
- 前端子代理耗时较长(~3-4分钟)，可与后端工作并行
- Sprint 1创建基础骨架，后续Sprint增量添加引擎

## FastAPI + Next.js 混合架构注意事项

### Python环境检测
macOS上系统Python可能没有fastapi。始终用`/opt/homebrew/bin/python3`启动后端。
检查方式: `pip3 list | grep fastapi` (显示Location确定site-packages路径)

### Next.js API Proxy模式
前端通过`/api/proxy?target=/api/xxx`转发到FastAPI后端(8000端口)。
Proxy route.ts需处理multipart/form-data(文件上传)和JSON两种content-type。

### .next构建产物
.next/应加入.gitignore。如果已被git跟踪，需`git rm -r --cached .next/`后重新提交。

### main.py路由陷阱
BaseHTTPRequestHandler中`do_GET`不存在`method`变量，不能在if条件中使用`&& method == "GET"`。
FastAPI无此问题，但路由注册顺序 matters — 更具体的路径必须在通用路径之前。

## Sprint连续执行模式

当用户要求"持续开发，每个sprint完成后自动执行下一个"时:

1. **每个Sprint = 一个功能交付单元**
   - 前后端并行开发 (子代理)
   - Gate 1: Pre-flight (文件存在性)
   - Gate 2: Revision (API端点+构建+功能验证)
   - Git commit + tag (vX.Y-sprintN)
   - 会话记录会话记录

2. **自动推进条件**
   - 全部Gate PASS → 自动进入下一个Sprint
   - 任意Gate FAIL → 修复后重试，不自动推进

3. **交付4件套**
   - Git commit + tag
   - 功能验证通过
   - 记忆库项目文档更新
   - 会话记录会话记录

## 注意事项
- Revision最多3次打回
- 3次后自动Escalation
- 用户可强制通过
- 审计报告自动归档