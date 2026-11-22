# Gatekeeper — 最小纪律 Harness 立项设计文档

状态：**v0.1 已实现** → `gatekeeper/`（本文件转为实现注记；差异见其 README）｜作者：work-os｜日期：2026-11-20
一句话：**不造 agent 引擎，造纪律闸门**——一个薄壳 CLI，用现有宿主（Claude Code / Codex / dsh headless）的 hook 机制，把 work-os 的铁律与 Gate 从"文档建议"变成"代码拦截"。

---

## 1. 为什么存在（问题陈述）

现有 harness 解决"能不能干活"，没人解决"是不是诚实交付"：

| 真实事故（本体系实测） | 通用性 | 引擎级方案有没有 |
|------------------------|--------|------------------|
| 前端 mock 数据冒充完成，宣布 ship | 每个用 agent 的团队都踩 | ❌ dsh approval policy 只管危险命令 |
| 审计子代理 git checkout 冲掉主会话未提交改动 | 多 agent 并发的结构性缺陷 | ❌ |
| 手造测试夹具掩盖渲染退化 | QA 通用陷阱 | ❌ |
| 宣称数字与数据源漂移 | 报告类任务通病 | ❌ |
| 完成度 <80% 宣布"完成" | agent 汇报激励问题 | ❌ |

结论：**纪律层是真空市场**。引擎（dsh 28万★）和产品壳（WorkBuddy 全平台）都有人做，"方法即代码"的强制层没有人做。

## 2. 定位与非目标

**定位**：host-agnostic discipline gate。宿主负责思考与执行，Gatekeeper 负责拦截与验收。

**非目标（明确不做）**：
- ❌ 自研 agent loop / LLM 调用 / 上下文管理（dsh、Hermes 已解决，且不竞争）
- ❌ 产品 UI / 云端托管 / 账号体系（WorkBuddy 的赛道）
- ❌ 改变宿主的执行能力——Gatekeeper 只让"不合格交付"过不去

## 3. 架构总览

```
┌─────────────────────────────────────────────────┐
│                  宿主 Agent（可替换）               │
│   Claude Code / Codex CLI / dsh headless / …     │
└──────┬──────────────────────────────┬───────────┘
       │ hook 注入点                    │ 会话读写
┌──────▼──────────────────────────────▼───────────┐
│                gatekeeper (Python CLI)            │
│                                                   │
│  hooks/           state/            rules/        │
│  ├─ session_start ├─ session.json   ├─ laws.yaml  │
│  ├─ pre_tool_use  ├─ gate_log.jsonl ├─ gates.yaml │
│  └─ stop          └─ plan.md        └─ redlines.  │
│                                                   │
│  命令: init / check / audit / report / override   │
└───────────────────────────────────────────────────┘
```

核心组件三件：**规则引擎**（YAML 声明式，来自铁律集）、**会话状态机**（路由决策 → 执行 → Gate → 收尾）、**拦截钩子**（宿主 hook 协议适配器）。

## 4. Hook 拦截方案（核心设计）

### 4.1 三个强制点

| 强制点 | 宿主实现 | 干什么 | 拦截规则（对应铁律） |
|--------|----------|--------|---------------------|
| **SessionStart** | Claude Code `SessionStart` hook；Codex 无 hook → 降级为协议注入；dsh `session/started` 事件 | 注入 AGENTS.md 路由协议 + memory/偏好；初始化 session.json（complexity 未定） | 律前协议：无路由决策不许进执行 |
| **PreToolUse** | Claude Code `PreToolUse` hook（matcher: Edit/Write/Bash）；Codex `hooks.json`；dsh `agent/pre-step` waterfall（bail 即拦截） | ① Edit/Write 前检查 session.json：complexity≥L3 且无 plan_approved → **deny**（铁律1）；② Bash 命令含 `git checkout|stash|reset` 且 role=auditor → **deny**（铁律11）；③ Write 内容命中 mock 特征（`setTimeout.*fake|MOCK_|// mock data`）且该文件被声明为真实实现 → **warn+require tag**（铁律2） | 写操作前置闸门 |
| **Stop / SubagentStop** | Claude Code `Stop` hook；dsh `turn/end` 事件 | 宣布完成时跑 Gate：① git status 干净+有新 commit → 否则 deny stop（铁律3+收尾）；② 完成度清单缺失 → deny（铁律5）；③ 追加 gate_log.jsonl 审计行 | 完成声明后置闸门 |

### 4.2 拦截强度分级

```
deny(硬拦截) > require-ack(要求 agent 书面说明理由后放行) > warn(记录+提示) > log-only(纯审计)
```

每条规则在 rules.yaml 里带强度字段，用户可调。**默认**：5 条不可违反铁律=deny，10 条建议=require-ack，N 条红线=warn。这是"三级铁律体系"的代码化。

### 4.3 适配器模式（跨宿主关键）

```python
class HostAdapter(Protocol):
    def install_hooks(self, rules) -> None: ...   # 写宿主 hook 配置
    def emit_decision(self, verdict) -> dict       # 宿主 hook 协议返回格式
    def state_paths(self) -> StatePaths            # 会话状态放哪
```

MVP 只做 `claude_code.py`（hook 体系最成熟：PreToolUse 支持 JSON 输出 `permissionDecision: deny` + reason 回灌给模型）。`codex.py` 次之（hooks.json 能力较弱，部分规则降级为协议层）。`dsh.py` 留接口（等 dsh 过 rc 期；它的 `agent/pre-step` waterfall + approval policy 其实是三者中最配的）。**没有 hook 的宿主**：Gatekeeper 退化为 `gatekeeper check` 手动命令 + AGENTS.md 自律——协议仍然有效，强度降一级。

### 4.4 会话状态机

```
created → routed(complexity/模式已判定) → planned(L3+ 已确认) 
        → executing → gating → closed(commit+tag+完成度验证)
任何状态 ──override(用户签名)──→ 跳转（记入 gate_log，不可抹除）
```

session.json 是唯一真相源；hook 决策全部依据它，agent 自己不能写 `plan_approved=true`（只有 `gatekeeper approve` 命令/用户签名能置位）——这是防"agent 给自己开绿灯"的关键设计。

## 5. rules.yaml 示例（铁律的代码形态）

```yaml
- id: iron-1-plan-before-write
  law: "方案确认后才能执行"
  hook: pre_tool_use
  match: {tool: [Edit, Write], complexity: ">=L3"}
  unless: {state.plan_approved: true}
  strength: deny
  reason_to_agent: "L3+ 任务未确认 PLAN。先输出路由决策并写 PLAN.md 等用户 approve。"
- id: iron-3-clean-close
  law: "备份不可跳过"
  hook: stop
  check: {cmd: "git status --porcelain", expect_empty: true}
  and: {cmd: "git log -1 --format=%ct", newer_than: session.started_at}
  strength: deny
```

## 6. 与 work-os v1.1 的关系

- AGENTS.md / skills/ = 协议的**声明层**（人读、agent 自律）
- gatekeeper = 同一协议的**强制层**（机器拦截），规则 ID 与铁律 ID 一一对应
- 记忆回灌闭环：gate_log.jsonl 月度跑 `gatekeeper report` → 违反频率统计 → 高频违反的规则要么降级要么修协议（体系健康度指标的代码采集版）

## 7. 技术栈与规模估计

Python 3.11+，零重依赖（stdlib + pyyaml）；单包 `gatekeeper/`；预估 MVP 代码量 800–1500 行。不用 TS（避开与 dsh 正面同构）、不用框架（薄壳原则）。

## 8. 里程碑（Sprint 分级制执行）

| Sprint | 内容 | Gate | 验收标准 |
|--------|------|------|----------|
| S1 轻量 | `init` + claude_code adapter + SessionStart 注入 | 1+2 | 新 Claude Code 会话自动带路由协议；golden 链测试 |
| S2 标准 | PreToolUse 三规则（plan-before-write / auditor git-guard / mock-scan）+ state 机 + approve 命令 | 1-4 | 红队测试：故意违规 5 例全被 deny，正常流程 0 误伤 |
| S3 标准 | Stop hook（clean-close + 完成度清单）+ gate_log + `report` | 1-4 | 上述 P0 事故 5 例重放，全部在当时代被拦截（用事故报告做 fixtures） |
| S4 重型 | codex adapter + rules 自定义文档 + v0.1 release (shipped in repo v1.7.0) | 1-5 | 双宿主 E2E；用户价值门：找一个非本人团队试用给反馈 |

风险预案：① 误伤（正常操作被 deny）→ require-ack 兜底 + `override` 逃生门 + 规则可关；② 宿主 hook 协议变更 → adapter 隔离，回归测试锁 golden；③ agent 学会绕 hook（如用 python 脚本写文件躲开 Edit 工具）→ Bash 侧内容检查补充，且明确声明"防失误不防恶意"。

## 9. 开源策略

Apache-2.0（比 MIT 多专利授权条款，适合当产品推）；仓库 `work-os/gatekeeper` 独立成 org 子仓；README 首屏放 5 个真实事故重放 demo（每个 30 秒 GIF），差异化一目了然。

## 10. 待拍板项（设计决策，需要用户确认）

1. 语言选型 Python（我推荐，薄壳+你的技能栈）vs TypeScript（蹭 dsh 生态流量）？
2. License：Apache-2.0（推荐）vs MIT？
3. 仓库组织：sean2010zhang-star/work-os 单仓双子包（推荐 MVP 期）vs 立即建 org？
4. 开源首发范围：只做 Claude Code adapter（快）vs 双宿主（慢但 README 更有说服力）？
