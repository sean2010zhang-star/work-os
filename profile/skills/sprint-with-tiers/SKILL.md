---
name: sprint-with-tiers
description: "V2.0 Sprint三级制度 — 轻量/标准/重型，按任务复杂度匹配流程重量。小任务管理开销降70%，大任务保持完整流程。"
version: 2.0.0
category: foundation
tags: [sprint, gate, delivery, tiers, v2]
---

# Sprint三级制度 V2.0

## 设计原则

V1.0问题: 所有Sprint走相同完整流程，3个文件的小任务和30个文件的大任务开销相同。
V2.0方案: 三级Sprint，轻量Sprint管理开销<15%，标准<30%，重型<45%。

---

## 三级定义

### 轻量Sprint
- **适用**: ≤3文件, L1-L2任务, M1/M2/M5/M6模式
- **Gate**: Gate 1(文件存在) + Gate 2(API可curl/语法通过)
- **审核**: 无Agent Team
- **备份**: Git commit + session-log一行摘要
- **耗时**: 5-15分钟管理开销

### 标准Sprint
- **适用**: 4-10文件, L3任务, M7-M10模式
- **Gate**: Gate 1-4(含Agent Team终审)
- **审核**: Agent Team 3 Agent并行
- **备份**: 完整4件套(Git/文件/<vault>/session-log)
- **耗时**: 30-60分钟管理开销

### 重型Sprint
- **适用**: 10+文件, L4/架构变更, M11-M16模式
- **Gate**: Gate 1-5(含用户价值门)
- **审核**: 多模型交叉审计 + Agent Team
- **备份**: 完整4件套 + 全量备份(外存rsync)
- **耗时**: 60-120分钟管理开销

---

## Gate 5门控体系

| Gate | 名称 | 轻量 | 标准 | 重型 |
|------|------|------|------|------|
| 1 | Pre-flight(文件存在) | ✅ | ✅ | ✅ |
| 2 | Revision(API+语法+构建) | ✅ | ✅ | ✅ |
| 3 | Integration(前后端打通) | - | ✅ | ✅ |
| 4 | 终审(Agent Team) | - | ✅ | ✅ |
| 5 | 用户价值(V2.0新增) | - | - | ✅ |

### Gate 1: Pre-flight
- 所有预期文件存在且非空
- 无TODO/FIXME/HACK标记

### Gate 2: Revision
- API端点可curl调用(返回200)
- py_compile/node --check通过
- 核心功能端到端测试

### Gate 3: Integration
- 前端组件调用真实API(非mock)
- grep检测: 无setTimeout/MOCK_常量
- 间接API调用(useAuth) = 有效
- 静态页面(Landing/Pricing)豁免

### Gate 4: Agent Team终审
```python
delegate_task(tasks=[
    {"goal": "代码质量: 命名/错误处理/类型标注/重复", "toolsets": ["terminal","file"]},
    {"goal": "架构评估: 接口/依赖/DRY/可测试性", "toolsets": ["terminal","file"]},
    {"goal": "安全+边界: 输入验证/异常/注入/边界值", "toolsets": ["terminal","file"]},
])
```
- 评分≥7/10 + P0=0 = PASS
- 模型不可用 → 主Agent用execute_code补充

### Gate 5: 用户价值 (V2.0新增)
- 能用一句话说清"用户为什么需要"
- 和竞品/现有方案的区别已明确
- 每个用户类型的交付物已定义
- 不通过 → 停下来做产品研究

---

## 交付4件套

| 件套 | 轻量 | 标准 | 重型 |
|------|------|------|------|
| Git commit+tag | ✅ | ✅ | ✅ |
| 文件备份(tar.gz) | - | ✅ | ✅ |
| <vault>更新 | - | ✅ | ✅ |
| session-log会话记录 | 一行摘要 | 完整记录 | 完整记录 |

---

## Sprint成本追踪 (V2.0新增)

Gate报告中增加成本字段:
```
Sprint N 成本报告:
  开发token: X
  审计token: Y (占比Z%)
  备份token: W
  总计: X+Y+W
  P0发现: N个
  每P0成本: (X+Y+W)/N tokens
```

---

## 蜂群限流 (与V1.0兼容)

| 蜂种 | 工具 | 适用 | 限流 |
|------|------|------|------|
| 工兵蜂 | execute_code | 批量代码 | ≤50次/批 |
| 侦察蜂 | delegate_task | 调研 | ≤3并行,只读 |
| 战斗蜂 | 主Agent | 核心逻辑 | 不可委托 |
| 审计蜂 | delegate_task | 审核 | 3并行,只读 |

---

## 自动推进规则

- Gate全PASS → 自动下一Sprint
- Gate有FAIL → 修复重验，最多3次
- 3次FAIL → Escalation

---

## 全功能交付铁律

**禁止骨架/mock/stub。每个Sprint交付可运行的完整功能。**

验收标准:
```
[ ] 后端: 每个API有真实DB操作
[ ] 前端: 每个页面调用真实API
[ ] 前端: 无setTimeout/MOCK_
[ ] 集成: curl端到端测试通过
[ ] 服务: 后端health返回200
```

---

## Pitfalls

- 轻量Sprint不要升级为标准(除非发现新需求)
- 标准Sprint不要降级为轻量(除非scope缩小)
- Gate 3误报: useAuth=间接API=有效
- Agent Team模型不可用: 主Agent补充执行
- 每个Sprint独立备份，不能批量跳过中间Sprint
- 用户说"继续"时直接执行，不要重复输出方案

---

## V1.0→V2.0 映射

| V1.0 | V2.0 |
|------|------|
| sprint-gated-delivery全文 | 本skill(精简版) |
| sprint-gated-delivery的Pitfalls | common-pitfalls库 + 本skill Pitfalls |
| sprint-gated-delivery的实测数据 | V1.0 backup保留，本skill引用关键数据 |
| 无分级 | 新增轻量/标准/重型三级 |
| Gate 4层 | Gate 5层(新增用户价值门) |
| 无成本追踪 | 新增Sprint成本报告 |
