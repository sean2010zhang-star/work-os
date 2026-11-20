---
name: longrun-campaign
description: "Use when user authorizes full autonomous multi-phase development: mission contract, Gate 0 material review, sprint auto-advance, checkpoints, budget circuit-breaker."
version: 1.0.0
author: Work OS
license: MIT
metadata:
  hermes:
    tags: [campaign, autonomous, long-running, gate0, checkpoint, mission-contract]
    related_skills: [work-os-router, sprint-gated-delivery, sansheng-liubu-workflow, delivery-audit, consolidated-iron-laws]
category: foundation
tags: [campaign, autonomous, long-running, gate0, checkpoint]
related_skills: [work-os-router, sprint-gated-delivery, sansheng-liubu-workflow, delivery-audit, consolidated-iron-laws]
---

# Long-Run Campaign — 长程自主战役协议

> 场景：用户说"全量开发、自行执行、不用等我确认、每阶段测试审计通过后自动进下一阶段，直到全部完成"。
> 本 skill 把这句话变成一个**有边界、可恢复、可审计的闭环系统**，而不是无限自主承诺。

## When to Use

- 用户一次性授权覆盖多个 Phase/Sprint 的连续开发（"自行执行""不用等确认""直到完成"）
- 大型多模块系统分期交付，且要求测试/审计独立性
- 需要断点恢复的长任务（跨 context 压缩 / 跨进程重启 / 跨天）

## 铁律的调和（先解决表面矛盾）

"不用等我确认" **不等于** 取消铁律1（方案确认后才能执行）。正确解释：
**把确认前置到战役启动时刻** —— Mission Contract 就是那次确认。
战役期间无需逐 Sprint 确认，但必须遵守本 skill 的 5 个中断上报条件。

## Phase 0: Mission Contract（战役护照，缺失不开工）

写 `campaign/<id>/CONTRACT.md`，与用户逐项确认后冻结。必含 8 节：

```markdown
# Mission Contract: <战役名>
1. 目标与范围 —— 做什么、明确不做什么（范围膨胀=中断条件）
2. 分期计划 —— Phase 列表，每 Phase 的模块+可验收交付物
3. 任务约束注入 —— 用户业务约束逐条编号，Gate 0/3 会检查它们：
   - 例: 模块解耦可独立售卖/订阅（检查: 每模块独立部署+接缝定义）
   - 例: 模型独立构建封装（检查: 每模型有独立构建产物+统一调用接口）
4. 预授权范围 —— 覆盖哪些操作免逐次确认（写码/测试/审计/commit）；
   永不预授权: 删除数据、对外发布、花钱、不可逆操作（这些=中断条件）
5. 预算熔断 —— token 上限 / 最长 Sprint 数 / 挂钟时限，任一触顶即停并上报
6. 验收定义 —— "完成"的全局判据（所有 Phase 过 Gate + 全量回归绿 + 用户价值门）
7. 中断上报条件 —— 见下节 5 条，写死
8. 独立性要求 —— 测试/审计 agent 与开发 agent 不同上下文；审计只读
```

**规则**：Contract 未经用户确认 → 不许进入 Phase 1。这就是前置的那次"方案确认"。

## Phase 0.5: Gate 0 材料完备性评审（独立 team agent）

开发开始前，派 **1 个独立评审 agent**（只读）对材料做三维评审，输出 PASS/缺口清单：

| 维度 | 检查项 |
|------|--------|
| 完备 | PRD 每个功能有**可机检的验收标准**；接口契约齐全；数据 schema 齐全；依赖清单齐全；任务约束（Contract §3）都已落到具体功能点 |
| 可靠 | 需求间无自相矛盾；引用的外部系统/模型确实存在且能力核实过；数字/金额有一处来源 |
| 可行 | 分期切法符合模块边界；每 Phase 可独立 Gate 验证；预算估量级合理（Phase 数 × 单 Sprint 实测成本） |

- 缺口清单 → 回补材料 → 重审，直到 PASS 或用户书面接受缺口（记入 Contract）
- **禁止**：评审 agent 顺手改材料（只读铁律）；"先开发边开发边补材料"（垃圾方案会烧光预算）

## Phase 1..N: Sprint 循环（自动推进引擎）

执行细节复用 `sprint-gated-delivery` skill；本层规定循环控制：

```
for Phase in Contract.phases:
  for Sprint in Phase:
    1. 开发（主 agent / 蜂群按限流：工兵蜂=代码执行工具批量写，侦察蜂≤3并行只读，
       审计蜂≤3并行只读，战斗蜂=核心逻辑主 agent 亲自做）
    2. Gate 1 Pre-flight → Gate 2 Revision（语法/构建/单测）
       → Gate 3 Integration（真实打通 + 回归套件全量跑 —— 见下"防回归"）
       → Gate 4 独立终审（team agent，与开发不同上下文，只读，区间制范围）
    3. FAIL 处理：修复→重审；同 Gate 连续 3 FAIL → 中断上报（不静默跳过）
    4. PASS → 交付件套（commit+tag/状态文件更新/摘要）→ 自动进下一个 Sprint
  Phase 边界: 全量回归 + 10 行进度摘要落盘 + 预算核对
战役结束: Gate 5 用户价值门（对照 Contract §6 逐项验证后才声明"完成"）
```

### 防回归（长战役的头号死法：后 Phase 破坏前 Phase）

- 测试套件**累积不清零**：每个 Sprint 新增用例并入 `tests/regression/`，此后每个 Gate 3 全量跑
- 每 Phase 结束额外跑一次跨 Phase 集成回归
- 破坏旧用例 = 新 P0，触发中断上报评估是否回滚

### 断点恢复（checkpoint 三件套，每个 Sprint 边界必更新）

```
campaign/<id>/CONTRACT.md   # 冻结，很少变
campaign/<id>/mission.json  # 机器态: phase/sprint 游标, gates 结果, 预算消耗, 未决项
campaign/<id>/STATUS.md     # 人读态: 最近 10 行摘要 + 当前在做什么 + 下一步
```

**任何新会话/被压缩后/崩溃重启**：第一动作 = 读这三个文件恢复游标，而不是从头重做。
上下文被压缩时，这三个文件就是外置记忆。

### 中断上报（5 条，触发即停等用户）

1. 同 Gate 连续 3 FAIL
2. 预算熔断触顶（token/Sprint 数/时限）
3. 范围膨胀：要做的事超出 Contract §1/§3
4. 触碰不可逆操作（删数据、对外发布、花钱）——预授权不覆盖
5. 破坏性回归：旧用例大面积转红且非本次变更预期

上报格式：现象 → 证据（gate_log/测试输出）→ 选项 A/B → 建议。等用户拍板后继续。

## 独立性保障（用户点名要的"测试、审计独立"）

- 测试/审计 agent 与开发 agent **不同上下文**，不看开发过程对话，只看产物+设计文档
- 审计代理**只读**；并行开发期间绝对禁止 git checkout/stash/reset/restore（会冲掉主会话未提交改动）；需要干净基线用 `git worktree add` 独立目录
- 审查范围**区间制**（从 tagX 到 tagY），派单前先 commit 当期成果，防漂移误判
- P0 修复后必须重审，迭代到 P0=0

## 进度可观察（用户随时可插话）

- 每个 Sprint 边界：STATUS.md 更新 + 追加一行 `gate_log.jsonl`（gate/结果/证据路径/预算消耗）
- 每个 Phase 边界：给用户 10 行摘要（做了什么/证据/下一步/预算百分比）
- 用户中途改需求 → 视为 Contract 变更，走"修订 Contract → 重新 Gate 0 增量评审 → 继续"，不许口头直接改道

## 交付（战役结束）

1. 对照 Contract §2 全 Phase × 全功能逐项标 ✅⚠️❌📅（铁律 5，<80% 不说完成）
2. 全量回归最终绿 + gate_log 完整可查
3. 5 件套归档 + 复盘（delivery-retrospective）
4. 新教训回灌本 skill 或对应 skill

## PITFALLS

- 把"不用等确认"理解成取消 Gate/取消防回归 —— 授权的是**节奏**，不是**质量门**。
- Gate 0 流于形式：评审 agent 没拿到可机检的验收标准就"看着挺全"→ PASS 了个寂寞。检查项必须逐条对表。
- mission.json 与 STATUS.md 忘记同步 = 断点恢复时游标错乱，重做/漏做 Sprint。每个 Sprint 边界一起更新，别只更新一个。
- 预算只算 token 不算墙钟：通宵战役里单 Sprint 卡死 2 小时也是熔断，设时限。
- 让开发 agent 兼任"自审"图快：独立性的最低成本形态是"不同上下文的 leaf agent"，省这个=白测。
- Contract 冻结后口头打补丁 → 一切修订走 CONTRACT.md 版本化（v1.1, v1.2…），否则验收时各说各话。
