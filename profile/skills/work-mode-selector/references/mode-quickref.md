# 工作模式速查表

## 决策树(简化版)

```
查询？→ M1 | 小修？→ M2 | 并行？→ M3 | 验证？→ M5 | 调研？→ M6
测试？→ M8 | 创业？→ M15/M16 | 部署？→ M13 | 审查？→ M17
看板？→ M9 | 中型？→ M4 | 子任务？→ M10 | 大型？→ M11/M12
10+并行？→ M14 | 持续？→ M18 | 其他 → M7(默认)
判定后: M7+建议叠加M4四角色增强
```

## 模式→skill映射

| 模式 | 必须加载的skill |
|------|----------------|
| M4 四角色 | sansheng-liubu-workflow |
| M5 实验 | spike / prototype |
| M6 研究 | deep-research |
| M7 方案 | plan-confirm-execute + writing-plans |
| M8 TDD | tdd + verification-loop |
| M9 Kanban | kanban-orchestrator + kanban-worker |
| M10 子agent | subagent-driven-development |
| M11 三省六部 | sansheng-liubu-workflow + team-builder |
| M12 三省六部+团队 | sansheng-liubu-workflow + agent-team-execution + kanban-orchestrator |
| M13 gstack | gstack系列skill |
| M14 蜂群 | swarm-agents |
| M15 OPC | opc-orchestrator |
| M16 创业 | opc-orchestrator + ai-startup-agent + independent-consultant |
| M17 对抗 | santa-method / heavyskill |
| M18 自主循环 | continuous-agent-loop |

## 四角色增强叠加

四角色(规划者/设计师/工程师/审查者)可叠加到M7-M16:
- M7+M4: 方案由4角度审查
- M8+M4: 工程师写代码+审查者写测试并行
- M9+M4: 4角色各领看板任务
- M10+M4: 规划拆任务→设计出方案→工程师delegate→审查review
- M13+M4: 对齐CEO/Design/Eng/QA
- M16+M4: 战略/产品/技术/市场验证
