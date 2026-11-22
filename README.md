# Work OS — Execution Discipline for AI Agents

**English** · [中文](#work-os--ai-agent-执行纪律体系中文)

> Your agent can *do* the work. Nothing forces it to *finish* the work honestly.
> Work OS is a host-agnostic discipline layer — routing-first protocol, three-tier iron laws,
> Sprint×Gate gating, memory feedback loop — turned from "advice in a doc" into an installable
> system an agent cannot quietly skip.
>
> 一套给 AI Agent 的"执行纪律层"：路由协议 + 铁律 + Sprint/Gate 闸门 + 记忆反馈闭环。

## Why this exists

Agent failure modes are universal and expensive:

- mock data shipped as "done"
- an audit subagent silently reverting uncommitted work
- test fixtures hiding a renderer regression
- reported numbers drifting from their data source
- "all tests pass" claims that evaporate under review
- a 12-hour autonomous run that finishes at 3 AM with no checkpoint and no rollback

Documentation-only discipline keeps getting ignored by agents under pressure. So we packaged
it as **installable software**: the rules arrive as the agent's own system prompt, its skill
library, and a memory loop that gets sharper every week you use it.

## Three layers, not three choices

```
SKILL    decides what the agent KNOWS        → 47 skills (knowledge, procedures, pitfalls)
AGENT    decides HOW the agent thinks        → SOUL.md / AGENTS.md (routing, laws, memory loop)
HARNESS  decides what it CANNOT SKIP         → gatekeeper/ (hooks that deny in code)
```

These stack, they don't compete. Layers 1–2 were always shippable as text; **layer 3 is why
discipline survives pressure**. [`gatekeeper/`](gatekeeper/) is a single-file stdlib Python
CLI that installs real PreToolUse/Stop hooks (Claude Code: hard deny with the violated law
fed back to the model; Hermes/Codex/Trae/WorkBuddy: strongest enforcement each host exposes,
same kernel + same `.gatekeeper/` state — one brain, six connectors). Its core property:
**`approve`/`override` are human-only** (TTY or signature file) — an agent cannot open its
own gates. 13 red-team + golden E2E cases guard every rule.

## What's inside

| Component | What it does |
|-----------|--------------|
| `SOUL.md` / `AGENTS.md` | The protocol: a 5-line routing decision on every task → complexity tiers (L1–L4) → Sprint tiers → Gate 1–5 → closing checklist |
| **5 iron laws** | Violation = delivery failure (plan confirmation for L3+ · real wiring, no mock-as-done · no skipped backups · no skipped gates · no "done" claim under 80% verified) |
| **10 strong recommendations** | Skippable only with a stated reason (read-only auditors, verify-then-change, single-source numbers…) |
| **Quality red-lines** | Fixture honesty, exception-vs-fetch failure distinction, secret-path denylists, git-history anchoring… |
| **48 skills** (Hermes) | Routing, methodology, iron laws, Sprint/Gate tiers, plan templates, delivery-audit checklists, git versioning, cross-project pitfalls, **long-run campaign protocol** (Mission Contract + checkpoints + budget fuse), plus 30 curated external skills (superpowers dev suite, GitHub ops, document tooling, research) |
| **`gatekeeper/`** | The harness layer: single-file CLI + 6 host adapters; deny rules = iron laws in code; human-only approve; 13 red+golden E2E cases |
| `memory/` | Seed structure for the memory-feedback loop (index / preferences / workflow-lessons / decisions / projects) + **mandatory first-run interview** that fills your preferences file |

## Two editions — pick by your host

| | **Hermes Edition** | **Universal Edition** |
|---|---|---|
| For | anyone running [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Claude Code, Codex CLI, Cursor, Windsurf, Cline, Copilot, dsh, OpenCode… |
| Install | `./install.sh` (one command) | marketplace add, or copy `AGENTS.md` |
| Protocol | full system prompt (SOUL.md: routing + laws + red-lines + memory protocol) | `AGENTS.md` (same laws, same loop) |
| Skills | **18 system + 30 curated external** = 48 (incl. **V3.4 campaign protocol** with 8 machine-check scripts) | **8** portable + campaign mapping (`docs/campaign-universal.md`) |
| Memory loop | profile `memory/` seeded; agent reads each task, updates after — full feedback loop | same 4-file seed, wired via `memory/` dir in your project |
| Self-evolution | yes — new skills save into the profile automatically | manual (edit skill files) |
| Enforcement | protocol-disciplined (advisory) | protocol-disciplined; hard hook-blocking = Gatekeeper roadmap |

### Hermes Edition — one command

```bash
git clone https://github.com/sean2010zhang-star/work-os && cd work-os && ./install.sh
# --dry-run to preview · --uninstall to remove
```

1. Detects Hermes (otherwise prints how to get it + the Universal path for your host)
2. Creates an **isolated profile** `work-os` — your existing setup untouched, one command back
3. Installs SOUL.md (full protocol as system prompt) + 18 system skills + 30 curated external skills
4. Seeds `memory/` (never overwrites yours) — first session auto-interviews you to fill preferences
5. Copies **your own** model/provider block from your config (no keys ship in this repo, ever)
6. Checks optional deps (`git`/`node`/`rsync` → which gates/backup layers unlock)
7. **Verifies**: asserts the agent emits a `[路由]` routing block before acting
8. Launches first-run onboarding: `hermes -p work-os`

### Universal Edition

- **Claude Code**: `/plugin marketplace add sean2010zhang-star/work-os` → `/plugin install work-os@work-os`
- **Codex CLI**: `codex plugin marketplace add sean2010zhang-star/work-os`
- **Any other host**: paste repo-root `AGENTS.md` into your system prompt (that alone activates
  routing + iron laws + checklist), copy `plugins/work-os/skills/*` into your skills dir if the
  host reads SKILL.md, seed `memory/` into your project.
- Details & first-run check: `plugins/work-os/README.md`

## The core loop

```
task arrives
  → [ROUTE]     classify | complexity L1-4 | mode | Sprint tier | gate level   ← before any action
  → [CONFIRM]   L3+ requires an approved plan first
  → [EXECUTE]   load matched skills; core logic never delegated; batch ops via code-exec tool
  → [GATE]      1 pre-flight → 2 revision → 3 integration → 4 independent review → 5 user value
  → [CLOSE]     commit+tag · verify completion per-item · 4-layer backup · lessons → memory/skills
```

For long unattended runs, the **Campaign Edition** protocol (V3.4) adds a 10-section signed
Mission Contract, a Gate 0 material review, L1/L2/L3 sprint weight-gating, crash-restart
checkpoints, a token/wall-clock budget fuse — and an **arsenal of 8 deterministic
machine-check scripts** (`scope_check` / `gate_recorder` with negative self-test /
`cursor_check` / `fixture_check` AST scanner / `value_check` / `heartbeat_check` watchdog /
`arch_check` / `gitguard` write-blocker) that turn the rules from prose into gates that
fail closed. See `profile/skills/longrun-campaign/scripts/`, mapping for non-Hermes hosts
in `docs/campaign-universal.md`.

## Protocols you can measure, not just trust

The campaign protocol was iterated through adversarial benchmarking: real incident-derived
maze questions, neutral pre-written rubrics, fresh runners each round (symmetric questions
scored a fused doc 97.5/100; the *same* doc on real-incident questions scored 66 — the bias
lesson is documented). Method: `profile/skills/protocol-doc-benchmarking/` (with a 10-incident
question bank you can reuse to grade any process doc).

## Does it actually work like the author's setup?

Honest, layer-by-layer answer in [`docs/effectiveness.md`](docs/effectiveness.md):
discipline ≈100% day one · method library ~90% · your memory layer grows from zero as you use it ·
vertical domain assets intentionally not included. Includes a 2-minute first-run acceptance test.

## Roadmap

- **v1.4.x (current)** — the discipline pack: protocol + 47 skills + memory seeds + first-run
  interview + campaign protocol. Hermes + Claude Code + Codex adapters.
- **v1.5+** — **Gatekeeper**: thin CLI wrapping Claude Code / Codex / dsh via their hook systems
  and *enforcing* the gates in code (pre-tool-use blocks, stop-hook completion checks).
  Design in `docs/gatekeeper-design.md`.
- **v2.0** — expert-persona packaging for agent-expert platforms (role spec + SOP + knowledge base).

## Philosophy

1. **Unverified delivery = an open-loop system = uncontrollable.** Every claim needs a read-back.
2. **Discipline must be enforceable or it's decoration.** Docs advise; gates block.
3. **Lessons belong where they load** — into the skill for that task type, not a graveyard doc.
4. **The agent is replaceable; the workflow is the asset.** Host-agnostic by design.

## License

MIT — the discipline should be free to fork. That's the point.

---
---

# Work OS — AI Agent 执行纪律体系（中文）

[English](#work-os--execution-discipline-for-ai-agents) · **中文**

> 你的 Agent 会"干活"，但没有任何东西逼它**诚实收尾**。
> Work OS 是一套与宿主无关的执行纪律层——路由优先协议、三级铁律、Sprint×Gate 闸门、
> 记忆反馈闭环——把"写在文档里的建议"变成 Agent 无法绕过的可安装系统。

## 为什么需要它

Agent 的失败模式是普适且昂贵的：

- 用 mock 数据冒充"已完成"
- 审计子代理悄悄回滚未提交的工作
- 测试夹具掩盖渲染回归
- 汇报数字与数据源漂移
- "全部测试通过"经不起独立复查
- 12 小时自主开发在凌晨 3 点崩掉，没有检查点、没有回滚路径

纯文档纪律在压力下总被 Agent 无视——所以我们把它打包成**可安装的软件**：规则直接进入
Agent 的系统提示词、技能库，以及一套每周都在变锋利的记忆反馈闭环。

## 三层叠加，不是三选一

```
SKILL   决定 Agent「知道什么」  → 48 skill（知识、流程、陷阱库）
AGENT   决定 Agent「怎么想」    → SOUL.md / AGENTS.md（路由、铁律、记忆闭环）
HARNESS 决定「能不能跳过」      → gatekeeper/（代码级拦截钩子）
```

三层是叠加关系，不是选型关系。前两层可以靠文本交付，**第三层才是纪律扛住压力的原因**。
[`gatekeeper/`](gatekeeper/) 是单文件零依赖 Python CLI：Claude Code 上写真实
PreToolUse/Stop hook（硬 deny + 把违反的铁律原文回灌给模型）；Hermes/Codex/Trae/WorkBuddy
各接到该宿主能给出的最强形态——同一内核、同一 `.gatekeeper/` 状态格式，一套大脑六个插头。
核心性质：**`approve`/`override` 只认人类**（TTY 或签名文件），Agent 无法给自己开绿灯。
13 条红队+金样例 E2E 守着每一条规则。

## 系统包含什么

| 组件 | 作用 |
|------|------|
| `SOUL.md` / `AGENTS.md` | 协议本体：每个任务先输出 5 行路由决策 → 复杂度分级(L1–L4) → Sprint 分级 → Gate 1–5 → 收尾清单 |
| **5 条铁律** | 违反 = 交付失败（L3+ 必须先确认方案 · 真实前后端联调，禁 mock 冒充 · 禁跳备份 · 禁跳 Gate · 验证不足 80% 禁称"完成"） |
| **10 条强烈建议** | 只能说明理由后跳过（审计代理只读 · 先验证再修改 · 数字单一来源…） |
| **质量红线** | 夹具诚实、异常与取数失败区分、敏感路径黑名单、git 历史锚定… |
| **48 个 skill**（Hermes 版） | 路由、方法论、铁律全文、Sprint/Gate 分级、方案模板、交付审计清单、git 版本管理、跨项目陷阱库、**长程战役协议**（Mission Contract + 断点检查点 + 预算熔断），另含 30 个精选外部 skill（superpowers 开发套件、GitHub 运维、文档工具、研究工具） |
| **`gatekeeper/`** | 第三层 harness：单文件 CLI + 6 宿主适配器；deny 规则=铁律的代码形态；approve 只认人类；13 条红队+金样例 E2E |
| `memory/` | 记忆反馈闭环的种子结构（索引/偏好/工作流教训/决策记录/项目档案）+ **首次运行强制采访**引导你填好偏好文件 |

## 两个版本 — 按你的宿主选择

| | **Hermes Edition** | **Universal Edition** |
|---|---|---|
| 适合 | 使用 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的人 | Claude Code、Codex CLI、Cursor、Windsurf、Cline、Copilot、dsh、OpenCode… |
| 安装 | `./install.sh`（一条命令） | marketplace 添加，或直接拷 `AGENTS.md` |
| 协议 | 完整系统提示词（SOUL.md：路由+铁律+红线+记忆协议） | `AGENTS.md`（同样的法则、同样的闭环） |
| Skill | **18 系统 + 30 精选外部** = 48（含战役协议 V3.4 + 机检武器库） | **9** 个可移植 + 战役协议映射（`docs/campaign-universal.md`） |
| 记忆闭环 | profile 内 `memory/` 预置；Agent 每任务先读、做完即更新 | 同样的 4 文件种子，通过项目 `memory/` 目录接入 |
| 自进化 | 有 — 新 skill 自动存入 profile | 手动（编辑 skill 文件） |
| 强制力 | 协议级约束（建议性） | 协议级约束；hook 硬拦截 = Gatekeeper 路线图 |

### Hermes Edition — 一条命令

```bash
git clone https://github.com/sean2010zhang-star/work-os && cd work-os && ./install.sh
# --dry-run 预览 · --uninstall 卸载
```

1. 自动检测 Hermes（未安装则打印获取方式 + 你所用宿主的 Universal 路径）
2. 创建**隔离 profile** `work-os` —— 现有环境零改动，一条命令切回
3. 安装 SOUL.md（协议即系统提示词）+ 18 个系统 skill + 30 个精选外部 skill
4. 预置 `memory/`（绝不覆盖你自己的）—— 首次会话自动采访你填写偏好
5. 从你的配置**复制你自己的**模型/供应商段（本仓库永远不携带任何 key）
6. 检查可选依赖（`git`/`node`/`rsync` → 解锁对应 Gate/备份层）
7. **验证**：断言 Agent 行动前先输出 `[路由]` 决策块
8. 拉起首跑引导：`hermes -p work-os`

### Universal Edition

- **Claude Code**：`/plugin marketplace add sean2010zhang-star/work-os` → `/plugin install work-os@work-os`
- **Codex CLI**：`codex plugin marketplace add sean2010zhang-star/work-os`
- **其它任意宿主**：把仓库根目录 `AGENTS.md` 粘进系统提示词（仅此一步即可激活路由+铁律+清单）；
  宿主支持 SKILL.md 的话把 `plugins/work-os/skills/*` 拷入技能目录；`memory/` 种子放进项目。
- 细节与首跑自检：`plugins/work-os/README.md`

## 核心循环

```
任务到达
  → [路由]    分类 | 复杂度 L1-4 | 模式 | Sprint 级别 | Gate 级别    ← 先于一切动作
  → [确认]    L3+ 必须先有确认过的方案
  → [执行]    加载匹配 skill；核心逻辑永不外包；批量操作用代码执行工具
  → [闸门]    1 pre-flight → 2 revision → 3 integration → 4 独立复审 → 5 用户价值
  → [收尾]    commit+tag · 逐项验证完成度 · 4 层备份 · 教训回灌 memory/skill
```

长程无人值守开发由 **Campaign Edition** 协议（V3.4）接管：10 节 Mission Contract（授权前置）、
Gate 0 材料评审、L1/L2/L3 重量门、断点三件套、token/墙钟预算熔断——并把文字规矩下沉为
**8 个确定性机检脚本武器库**（scope_check / gate_recorder 负向自检 / cursor_check /
fixture_check 假测试 AST / value_check / heartbeat_check 看门狗 / arch_check / gitguard
git 写拦截闸），见 `profile/skills/longrun-campaign/scripts/`，非 Hermes 宿主映射见
`docs/campaign-universal.md`。

## 协议是可以被测量的，不只是被相信

战役协议经对抗式评测迭代：真实事故改编的迷宫题、预先写死的中立判据、每轮换全新 Runner
（对称题曾给融合版 97.5/100，同一文档换真实事故题只有 66——偏置教训已文档化）。
方法论见 `profile/skills/protocol-doc-benchmarking/`（含十类事故原型题库，可直接给任意流程文档打分）。

## 别人装完能到我本机这个效果？

诚实的分层回答见 [`docs/effectiveness.md`](docs/effectiveness.md)：
纪律层 ≈100% 即装即得 · 方法库 ~90% · 记忆层从 0 随使用生长 · 垂直领域资产有意不包含。
附 2 分钟首跑验收测试。

## 路线图

- **v1.5.x（当前）** — 纪律包本体：协议 + 47 skill + 记忆种子 + 首跑采访 + 战役协议。
  Hermes / Claude Code / Codex 三宿主适配。
- **v1.6（现在）** — **Gatekeeper v0.1 已落地**：`gatekeeper/gatekeeper.py`——harness 层
  成为可运行 CLI，6 宿主适配器（`adapters.py`），deny/ack/warn 三级强度对应三级铁律体系，
  人类专属 approve，规则新陈代谢 report，红队+金样例测试套件。设计稿转为实现注记。
- **v1.7+** — Hermes 插件原生暴露 hook 总线；dsh 过 rc 期后加适配；OS/沙箱级强制在
  limits 里诚实评估，不虚标。
- **v2.0** — Agent 专家平台的专家人设封装（岗位说明书 + SOP + 知识库）。

## 理念

1. **未验证的交付 = 开环系统 = 不可控。** 每个结论必须有回读。
2. **纪律要么可强制，要么是装饰。** 文档只能建议，闸门才能拦截。
3. **教训要存放在会被加载的地方** —— 写进对应任务类型的 skill，而不是没人读的墓碑文档。
4. **Agent 可以换，工作流才是资产。** 天生宿主无关。

## 许可

MIT —— 纪律理应自由 fork。这就是重点。

## System guide (visual)

An illustrated one-page overview of the whole workflow — routing protocol, L1–L4 tiers,
Gate chain, campaign protocol, memory loop — in Chinese+English, zero dependencies:
**[`docs/system-guide.html`](docs/system-guide.html)** (open in any browser).
