# Agent Team Review Pattern (Validated)

## When to Use
- Complex product/design decisions needing multiple perspectives
- After major code sprints (Sprint 1-3 validated this)
- When user says "讨论"、"分析"、"评估" with multiple aspects

## Agent Configuration
Use `delegate_task(tasks=[...])` with 2-3 leaf agents, each from a different angle:

```python
delegate_task(tasks=[
    {"goal": "用户研究视角: 分析X类用户的真实需求/痛点/付费意愿",
     "role": "leaf", "toolsets": ["terminal", "file"]},
    {"goal": "产品设计视角: 设计具体的Free/Pro/VIP交付物",
     "role": "leaf", "toolsets": ["terminal", "file"]},
    {"goal": "技术/架构视角: 评估实现方案的可行性",
     "role": "leaf", "toolsets": ["terminal", "file"]},
])
```

## Synthesis Pattern
After all agents return:
1. Read each agent's output
2. Identify consensus points (high confidence)
3. Identify contradictions (need user decision)
4. Create synthesis document combining best insights
5. Present to user for review

## Validated Example
3 agents produced:
- Agent 1 (user research): 4 personas with specific pain points, willingness to pay
- Agent 2 (product design): Free/Pro/VIP deliverables with concrete text examples
- Agent 3 (product consultant): Experiment methodology application + competitive analysis

Key finding: Each agent surfaced insights the others missed.
- User research found "为确定性付费" (not for methodology)
- Product design found specific Aha Moments per persona
- Consultant found experiment loop differentiation vs ChatGPT/MBTI

## Pitfalls
- Agent 2 was interrupted (timeout) — needed separate re-run
- Keep each agent's scope focused (1 perspective, not all)
- Write agent output to files for reference (don't rely on summary alone)
