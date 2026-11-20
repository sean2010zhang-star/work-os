---
name: work-mode-selector
description: 工作模式选择器 v3 — 18种工作模式 + 四角色增强层。31个skill/tool/agent组合。
version: 3.0
category: foundation
---

# 工作模式选择器 v3

## 触发条件
- 用户发出任何任务指令时
- 复杂度判断前必须先扫描此skill
- 禁止跳过模式选择直接执行(简单查询除外)，不可跳过

## 18种工作模式

### ── 基础层 ──

### M1 速查模式 — 单工具直查
- 特征: 信息查询、状态检查、文件读取
- 执行: 直接1-2个tool call
- 例: "查一下服务状态"、"读某个文件"

### M2 直做模式 — 简单任务直接执行
- 特征: 单文件修改、小配置变更、简单生成
- 执行: 3-5个tool call
- 例: "改个配置项"、"生成个简单页面"

### ── 协作层 ──

### M3 并行模式 — 独立子任务并行
- 特征: 多个互不依赖的任务
- 执行: delegate_task batch (最多3并行)
- 加载: agent-team-execution
- 例: "同时写3份文档"

### M4 四角色协作模式 — 轻量多角色
- 特征: 需要设计+实现+验证，中型任务
- 执行: 4角色分工
  - 规划者(Coordinator): 拆解任务、分配角色
  - 设计师(Designer): 方案设计、UI/架构
  - 工程师(Engineer): 编码实现
  - 审查者(QA): 验证+测试
- 加载: sansheng-liubu-workflow (简化版)
- 例: "做一个登录页面"、"重构评分模块"
- ★ 四角色可叠加到M7-M13，作为增强层(见下方)

### M5 实验模式 — 一次性验证
- 特征: 需要验证可行性、快速试错
- 执行: spike/prototype，失败就丢弃
- 加载: spike 或 prototype
- 例: "试试这个方案行不行"

### M6 研究模式 — 深度调研
- 特征: 需要多源信息、深入分析
- 执行: deep-research + iterative-retrieval
- 加载: deep-research
- 例: "调研竞品"、"分析技术方案"

### ── 工程层 ──

### M7 方案模式 — 确认后执行
- 特征: 2+文件修改、新功能、架构调整
- 执行: plan-confirm-execute三步走
- 加载: plan-confirm-execute + writing-plans
- 可叠加M4增强: 方案阶段由4角色分别审查

### M8 TDD模式 — 测试驱动
- 特征: 有明确输入输出、需要质量保证
- 执行: RED→GREEN→REFACTOR循环
- 加载: tdd + verification-loop
- 可叠加M4增强: 工程师写代码+审查者写测试

### M9 Kanban模式 — 看板跟踪
- 特征: 5+步骤、需要进度可见、可中断恢复
- 执行: kanban-orchestrator分解 → kanban-worker执行
- 加载: kanban-orchestrator + kanban-worker
- 可叠加M4增强: 4角色各领看板任务

### M10 子agent驱动 — 计划+委派
- 特征: 可拆分为独立子任务、需要review
- 执行: 写计划 → delegate子agent → 2-stage review
- 加载: subagent-driven-development
- 可叠加M4增强: 规划者拆任务，工程师delegate，审查者review

### ── 大型工程层 ──

### M11 三省六部模式 — 多角色协作
- 特征: 大型工程、多模块
- 执行: 中书省(规划) → 门下省(审查) → 尚书省(执行) → 御史台(QA)
- 加载: sansheng-liubu-workflow + team-builder

### M12 三省六部+Agent团队 — 最大编排
- 特征: 超大型工程，多Agent并行
- 执行: 三省六部 + Agent Team并行(前端/后端/引擎/测试)
- 加载: sansheng-liubu-workflow + agent-team-execution + kanban-orchestrator
- 例: "多引擎系统7大引擎全部实现"

### M13 gstack模式 — 结构化开发流程
- 特征: 产品开发全流程
- 执行: design-consultation → plan-eng-review → ship → review → qa
- 加载: gstack系列skill
- 可叠加M4增强: 4角色映射到gstack各阶段

### M14 Hermes+ruflo — 蜂群多Agent
- 特征: 需要10+Agent大规模并行
- 执行: ruflo蜂群框架，100+专用Agent
- 加载: swarm-agents
- 可叠加M4增强: 4角色作为蜂群的协调层

### ── 专项模式 ──

### M15 OPC模式 — 一人公司运营
- 特征: 创业/商业运营相关
- 执行: OPC全流程(利基→价值→MVP→转化→资产→退出)
- 加载: opc-orchestrator + 对应子skill
- 例: "设计商业模式"、"做运营健康审查"

### M16 创业模式 — 完整创业方法论
- 特征: 从0到1的创业项目，需要方法论指导
- 执行: OPC方法论 + Anthropic创始人手册 + 图解创业
  - Phase 0 利基定位: opc-niche-positioning + independent-consultant
  - Phase 1 价值设计: opc-value-proposition + startup-visual-guide
  - Phase 2 MVP: opc-mvp-designer + experiment-driven
  - Phase 3 转化: opc-conversion-loop + startup-agent
  - Phase 4 资产: opc-asset-ops
  - Phase 5 规模化: ai-native-startup + ai-startup-agent
- 加载: opc-orchestrator + ai-startup-agent + startup-agent + independent-consultant + opc-startup-integrated
- 适用: 新产品从0到1、商业化验证、创业全链路
- 例: "多引擎系统如何商业化"、"从0开始做独立咨询"

### ── 验证层 ──

### M17 对抗验证 — 多agent交叉验证
- 特征: 高风险决策、需要多角度验证
- 执行: Santa方法，Generator-Evaluator对抗
- 加载: santa-method 或 heavyskill
- 例: "架构方案是否合理"

### M18 自主循环 — 持续自主执行
- 特征: 长时间运行、持续优化
- 执行: continuous-agent-loop + 自动重试
- 加载: continuous-agent-loop / autoresearch (公开上游仓库)
- 例: "持续优化准确率"

## 四角色协作 — 增强层

四角色(规划者/设计师/工程师/审查者)可叠加到以下模式，提升能力:

| 基础模式 | +四角色增强 | 效果 |
|----------|------------|------|
| M7 方案  | 规划者写方案，设计师出架构，审查者确认 | 方案更全面 |
| M8 TDD   | 工程师写实现，审查者写测试，并行执行 | 质量更高 |
| M9 Kanban | 4角色各领看板任务，审查者做Gate | 分工更清晰 |
| M10 子agent | 规划者拆任务→设计师出方案→工程师delegate→审查者review | 流程更规范 |
| M11 三省六部 | 四角色映射到三省六部的子角色 | 更细化 |
| M13 gstack | 规划者=CEO review，设计师=design review，工程师=eng，审查者=QA | 对齐gstack |
| M14 蜂群 | 四角色作为蜂群协调层，管理下级Agent | 有统领 |
| M16 创业 | 规划者=战略，设计师=产品，工程师=技术，审查者=市场验证 | 创业全链路 |

使用方式: 判定基础模式后，追加"+M4"标记
例: "本任务判定为M10+M4(子agent+四角色增强)"

## 选择决策树

```
任务到达
  │
  ├─ 查询/读取？ ─────────────────→ M1 速查
  ├─ ≤2文件小修？ ─────────────────→ M2 直做
  ├─ 多个独立子任务？ ─────────────→ M3 并行
  ├─ 验证可行性？ ─────────────────→ M5 实验
  ├─ 调研分析？ ───────────────────→ M6 研究
  ├─ 有明确测试要求？ ─────────────→ M8 TDD
  ├─ 多角度验证？ ─────────────────→ M17 对抗
  ├─ 创业/商业化？ ───────────────→ M16 创业 / M15 OPC
  ├─ 设计→实现→部署？ ────────────→ M13 gstack
  ├─ 5+步骤需跟踪？ ──────────────→ M9 Kanban
  ├─ 中型功能？ ───────────────────→ M4 四角色
  ├─ 可拆为子任务？ ───────────────→ M10 子agent
  ├─ 大型多模块？ ─────────────────→ M11 三省六部
  ├─ 超大型多引擎？ ───────────────→ M12 三省六部+团队
  ├─ 10+模块并行？ ────────────────→ M14 蜂群
  ├─ 持续优化？ ───────────────────→ M18 自主循环
  └─ 其他 ─────────────────────────→ M7 方案(默认)

  判定后问: 是否需要+M4四角色增强？
```

## 任务→模式映射表

| 任务类型 | 推荐模式 | 加载skill |
|----------|----------|-----------|
| 查状态/读文件 | M1 | 无 |
| 改配置/小修 | M2 | 无 |
| 同时做3+独立任务 | M3 | agent-team-execution |
| 做一个功能模块 | M4+M7 | plan-confirm-execute |
| 试试方案行不行 | M5 | spike/prototype |
| 调研分析 | M6 | deep-research |
| 重构/新功能 | M7(+M4) | plan-confirm-execute |
| 实现计算逻辑 | M8(+M4) | tdd |
| 完成一个页面 | M9(+M4) | kanban-orchestrator |
| 实现5+个API | M10(+M4) | subagent-driven-development |
| 构建完整产品 | M11(+M4) | sansheng-liubu-workflow |
| 多引擎系统 | M12 | sansheng-liubu + agent-team |
| 开发+部署功能 | M13(+M4) | gstack系列 |
| 10+模块并行 | M14(+M4) | swarm-agents |
| 一人公司运营 | M15 | opc-orchestrator |
| 创业从0到1 | M16 | opc+startup+independent-consultant |
| 架构/安全审查 | M17 | santa-method/heavyskill |
| 持续优化实验 | M18 | continuous-agent-loop |

## 常见错误(历史踩坑)

1. **模式太少** — v1只有4级(L1-L4)，用户指出不够。v3有18种+四角色增强。
2. **跳过模式选择直接执行** — 复杂任务(如构建多引擎系统)直接动手，未走M12三省六部。
3. **四角色只当独立模式** — 四角色是增强层，可叠加到M7-M16任意模式。
4. **忽略专项模式** — 创业(M16)、OPC(M15)、gstack(M13)、蜂群(M14)都是独立模式，不能硬塞进其他模式。

## 执行铁律

1. **任务到达先判断模式** — 不可跳过，必须告知用户判定结果
2. **M7以上必须加载对应skill** — skill中有详细流程和陷阱
3. **模式选择必须告知用户** — "本任务判定为MX模式"
4. **四角色增强必须主动建议** — M7+时询问是否叠加M4
5. **M11/M12/M16需用户确认方案** — 禁止未确认就执行，容易方向偏离
6. **每个模式执行完做备份** — 备份铁律4项

## 审计铁律

> **M5-M18任务完成后必须触发外部审计(external-audit skill)。不可跳过。**

审计级别自动判定:
- 低复杂度(M5/M6, ≤10 calls): 客观工具
- 中复杂度(M7/M8/M9, 10-30 calls): 客观工具 + 独立LLM
- 高复杂度(M10+, 30+ calls): 客观工具 + 独立LLM + Peer Review
- 极高复杂度(M11/M12/M16): 客观工具 + 多模型交叉审计

详见: external-audit skill

## REFERENCE

- sansheng-liubu-workflow: 三省六部制
- plan-confirm-execute: 方案确认
- heavyskill: HeavySkill并行推理
- swarm-agents: 蜂群框架
- gstack系列: gstack skill
- opc-orchestrator: OPC全流程
- ai-startup-agent: AI创业方法论
- startup-agent: 创业Agent
- independent-consultant: 独立咨询顾问
