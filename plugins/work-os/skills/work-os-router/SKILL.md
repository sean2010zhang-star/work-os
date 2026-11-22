---
name: work-os-router
description: "Use at task start: route mode, skills, gates in one line."
version: 1.1.0
author: Work OS
license: MIT
metadata:
  hermes:
    tags: [router, workflow, entry-point, work-os]
    related_skills: [work-os-methodology, consolidated-iron-laws, sprint-with-tiers, delivery-audit, longrun-campaign]
category: foundation
tags: [router, workflow, entry-point, work-os]
related_skills: [work-os-methodology, consolidated-iron-laws, sprint-with-tiers, delivery-audit, longrun-campaign]
---

# Work OS Router — 工作体系统一入口

> 本 skill 是整个工作体系（Work OS）的唯一入口。目标：任何任务到达时，
> 先产出一次「路由决策」，再动手。它不重复子 skill 的内容，只负责**串联与裁决**。

## When to Use
- 任何非纯闲聊任务到达时（第一个动作）
- 用户问"我的工作体系/方法论是什么" → 直接加载 work-os-methodology
- 派子 agent 前，为子 agent 生成其路由决策（写进 context）

## 决策模板（每次任务开头输出，≤5行）

```
[路由] 分类=<代码|文档|调研|运维|创意|业务> | 复杂度=<L1-L4> | 模式=<M1-M18>
[Sprint] <轻量|标准|重型> → Gate <1-2|1-4|1-5>
[链路] <本次要加载的 skill 序列>
[记忆] 已读: 索引+偏好+<项目条目或"无项目">; 任务后需更新: <有/无→哪节>
```

## Step 0: 记忆读取（铁律，不可跳过）
1. read `memory/_INDEX.md` → `memory/偏好.md`（系统提示词已强制，此处兜底确认本会话真的读过）
2. 任务涉及具体项目 → 读 `memory/项目/<项目名>.md`
3. 流程疑问 → `memory/工作流规范.md`；"当初为什么" → `memory/决策记录.md`
4. **若 偏好.md 仍是空模板 → 先走首跑采访，再接受正式任务**

## Step 0.5: 战役识别（先于复杂度）
用户一次性授权覆盖多个 Phase/Sprint 的连续执行（"全量开发""自行执行不用等确认"
"测试审计通过后自动进下一阶段直到完成"）→ 这不是普通 L4 任务，
**加载 longrun-campaign（V3.4）**：Mission Contract + Gate 0 + 重量门 + 机检武器库，
把授权变成交付边界，绝不按"跳过确认直接开干"处理。

## Step 1: 分类 + 复杂度
| 复杂度 | 判据 | 方案确认 | 执行方式 |
|--------|------|----------|----------|
| L1 | ≤2文件/查询 | 免 | 直接做 |
| L2 | 独立子任务 | 免 | 并行子代理 |
| L3 | 多步骤/4-10文件 | 需要（写PLAN→确认→执行） | 主Agent+skill链 |
| L4 | 多模块/架构/10+文件 | 需要（或 Mission Contract 前置签署） | 分角色制衡/分阶段 |

## Step 2: 模式裁决（详表见 work-mode-selector / methodology M1-M18）
```
查询/≤2文件 → M1/M2     独立子任务 → M3      验证/调研 → M5/M6
中型功能(默认) → M7     需测试 → M8           5+步 → M9
可拆子任务 → M10       大型工程 → M11/M12(分角色制衡)
商业化 → M15/M16       持续优化 → M18
```

## Step 3: Sprint 级别 → Gate 要求（sprint-with-tiers）
| 级别 | 判据 | Gate | 交付件套 |
|------|------|------|----------|
| 轻量 | ≤3文件, L1-L2 | 1+2 | git commit+tag + 一行摘要 |
| 标准 | 4-10文件, L3 | 1-4 | 完整4件套 |
| 重型 | 10+/架构, L4 | 1-5 | 4件套+全量备份+多模型交叉审计 |

## Step 4: skill 链路装配
输出「链路」行时只列本次真正要用的 skill，宁缺毋滥；加载后按其流程执行。
长战役 → longrun-campaign；常规开发 → plan-confirm-execute + delivery-audit；
文档交付 → 文档类 skill；跨项目教训查询 → common-pitfalls。

## Step 5: 收尾（任务后，与决策行首尾呼应）
1. git commit + tag（project-git-version 流程）
2. 有新偏好/决策/流程/教训 → 更新 memory 对应文件 + _INDEX
3. 教训属于某类任务 → 写入对应 skill（skill 优先于 memory）；
   能写成确定性检查的教训 → 写成脚本（longrun-campaign 武器库范式）
4. 完成度声明前对照设计文档逐项验证（<80% 不说"完成"）

## 硬规则
- 禁止未输出路由决策就开始 L3+ 任务的执行动作
- 路由决策由主 Agent 做，不委托子 Agent；子 Agent 的 context 里由主 Agent 注入其决策行
- 用户说"自行判断后执行" → 路由照做但跳过确认等待，直接执行所选默认路径
- 分类/复杂度判断错了不阻塞：执行中可升档（L2→L3），降档需用户同意

## PITFALLS
- 不要把本 skill 当重型流程用在 L1 查询上——L1 只输出「[路由]…[记忆]已读」两行即可动手。
- "不用等我确认" ≠ 取消铁律1——长任务走 Step 0.5 战役识别，把确认前置为 Mission Contract。
- 记忆文件与宿主 memory 工具内容有重叠时，以记忆库文件为准（更完整、用户可审）。
