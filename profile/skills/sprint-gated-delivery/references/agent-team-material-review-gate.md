# Agent Team Material Review Gate

> Sprint开发前派发独立Agent Team评审材料完备性/可行性/可靠性（门下省门控），PASS 才准开工。同一 schema 与派发模式复用于 Sprint 完成后的独立验收审计（Gate-SN）：goal 写"逐条重跑验收项 + 独立复验清单（测试/交叉校验/耦合grep/端到端冒烟/git谱系）"，输出仍用 `{score, verdict, p0/p1/p2_issues, summary}`，有 P0 即 FAIL。

## Pattern

在第一个Sprint开始前，派发 3 个独立 Agent 并行评审，每个只看一个维度：

```python
delegate_task(tasks=[
    {"goal": "评审产品/内容文档完备性（链条闭环、覆盖缺口）",
     "output_schema": VERDICT_SCHEMA},
    {"goal": "评审架构可行性+解耦性（模块能否独立售卖/封装）",
     "output_schema": VERDICT_SCHEMA},
    {"goal": "评审可靠性实测核验（亲自重跑测试，不信自报告）",
     "output_schema": VERDICT_SCHEMA},
])
```

## 关键实践（提高评审质量与可比性）

- **用 output_schema 强制结构化**：`{score:0-10, verdict:PASS|FAIL, p0_issues:[], p1_issues:[], p2_issues:[], summary}`，required 含 verdict 与 p0_issues。有 P0 即 FAIL 写进 goal 里的判定规则，主 Agent 汇总时不用解析自由文本。
- **给每个 Agent 显式阅读范围与禁区**：列出要读的文件清单，并排除大体积文件（如扫描件 PDF 目录），否则子 Agent 陷"再读"循环超时。
- **可靠性 Agent 必须独立实跑**：在 goal 里写明"不信任项目自称的测试数字，一切以你亲自跑的为准"，并让它验证 git status/tag 谱系连续性。需要参照库时在 scratch 临时目录 `npm i`/`pip install`，勿污染项目。
- **独立性**：三 Agent 不共享上下文；评审 Agent 只读不写；开发 Agent 与测试/审计 Agent 永远分离（用户强制要求"保障测试、审计的独立性"）。
- **goal 里注入已知实测基线**（如"205/205断言、800/800交叉校验、6盘面浏览器实测通过"），让可行性 Agent 不必重复发现，专注评增量。

## 输出格式(每个Agent)

```
评分: X/10
P0问题: [必须修复才能开工]  P1: [建议]  P2: [择机]
结论: PASS / FAIL（有P0即FAIL）
```

任一 Agent FAIL → 汇总 P0 → 修复/补材料 → 复审该维度 → 全 PASS 后才制定 Sprint 计划开工。

## 与Agent Team审计的区别

| 阶段 | 时机 | 目的 | 读什么 |
|------|------|------|--------|
| 材料评审 | Sprint开始前 | 发现规划问题 | 设计文档+参考代码+Sprint计划 |
| 代码审计 | Sprint完成后 | 发现实现问题 | 实际代码 |

两者都用 3 Agent 并行 + verdict schema，但审查对象和时机不同。
