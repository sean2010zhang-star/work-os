---
name: work-os-router
description: "Use at task start: route mode, skills, gates in one line."
version: 1.0.0
author: 本体系 (user Work OS)
license: MIT
metadata:
  work-os:
    tags: [router, workflow, entry-point, work-os]
    related_skills: [work-os-methodology, auto-router, consolidated-iron-laws, work-mode-selector, delivery-audit]
category: foundation
tags: [router, workflow, entry-point, work-os]
related_skills: [work-os-methodology, auto-router, consolidated-iron-laws, work-mode-selector, delivery-audit]
---

# Work OS Router — 工作体系统一入口

> 本 skill 是整个工作体系（Work OS）的唯一入口。目标：任何任务到达时，
> 先产出一次「路由决策」，再动手。它不重复子 skill 的内容，只负责**串联与裁决**。

## When to Use
- 任何非纯闲聊任务到达时（第一个动作）
- 用户问"我的工作体系/方法论是什么"→ 直接加载 work-os-methodology
- 派子 agent 前，为子 agent 生成其路由决策（写进 context）

## 决策模板（每次任务开头输出，≤5行）

```
[路由] 分类=<代码|文档|调研|运维|创意|业务> | 复杂度=<L1-L4> | 模式=<M1-M18>
[Sprint] <轻量|标准|重型> → Gate <1-2|1-4|1-5>
[链路] <本次要加载的 skill 序列>
[记忆] 已读: _INDEX + 全局偏好 + <项目条目或"无项目">; 任务后需更新: <有/无→哪节>
```

## Step 0: 记忆读取（铁律，不可跳过）
1. read `memory/_INDEX.md` → `memory/偏好.md`（系统提示词已强制，此处兜底确认本会话真的读过；memory/ 路径按部署说明映射）
2. 任务涉及具体项目 → 读 `memory/项目/<项目名>.md`
3. 流程疑问 → `工作流规范.md`；"当初为什么" → `决策记录.md`

## Step 1: 分类 + 复杂度（分类表复用 auto-router）
| 复杂度 | 判据 | 方案确认 | 执行方式 |
|--------|------|----------|----------|
| L1 | ≤2文件/查询 | 免 | 直接做 |
| L2 | 独立子任务 | 免 | 子代理 并行 |
| L3 | 多步骤/4-10文件 | 需要（写PLAN→确认→执行） | 主Agent+skill链 |
| L4 | 多模块/架构/10+文件 | 需要 | 三省六部/分阶段 |

## Step 2: 模式裁决（详表见 work-mode-selector / methodology-overview M1-M18）
```
查询/≤2文件 → M1/M2     独立子任务 → M3      验证/调研 → M5/M6
中型功能(默认) → M7     需测试 → M8           5+步 → M9(Kanban)
可拆子任务 → M10       大型工程 → M11/M12(三省六部)
商业化 → M15/M16       持续优化 → M18
```

## Step 3: Sprint 级别 → Gate 要求（sprint-with-tiers）
| 级别 | 判据 | Gate | 交付件套 |
|------|------|------|----------|
| 轻量 | ≤3文件, L1-L2 | 1+2 | git commit+tag + 一行摘要 |
| 标准 | 4-10文件, L3 | 1-4 | 完整4件套 |
| 重型 | 10+/架构, L4 | 1-5 | 4件套+全量备份+多模型交叉审计 |

## Step 4: skill 链路装配（从 auto-router 匹配表取，M7+ 必加载）
输出「链路」行时只列本次真正要用的 skill，宁缺毋滥；加载后按其流程执行。

## Step 5: 收尾（任务后，与决策行首尾呼应）
1. git commit + tag（project-git-version 流程）
2. 有新偏好/决策/流程/教训 → 更新记忆库（memory/）对应节 + _INDEX
3. 教训属于某类任务 → 写入对应 skill（skill 优先于 memory）
4. 完成度声明前对照设计文档逐项验证（<80% 不说"完成"）

## 硬规则
- 禁止未输出路由决策就开始 L3+ 任务的执行动作
- 路由决策由主 Agent 做，不委托子 Agent；子 Agent 的 context 里由主 Agent 注入其决策行
- 用户说"自行判断后执行" → 路由照做但跳过确认等待，直接执行所选默认路径
- 分类/复杂度判断错了不阻塞：执行中可升档（L2→L3），降档需用户同意

## PITFALLS
- auto-router 的 Step5 (POST /api/tasks) 依赖外部看板服务；本机无该服务时跳过卡片创建，路由决策仍要输出。
- 不要把本 skill 当重型流程用在 L1 查询上——L1 只输出「[路由]…[记忆]已读」两行即可动手。
- 记忆库文件（memory/偏好.md）与宿主碎片记忆内容有重叠时，以记忆库文件为准（更完整、用户可审）。