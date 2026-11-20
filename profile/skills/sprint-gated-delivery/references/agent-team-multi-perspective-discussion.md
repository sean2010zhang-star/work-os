# Agent Team Multi-Perspective Discussion Pattern

## When to Use

Product decisions, strategy questions, design reviews where a single perspective is insufficient.

NOT for: code audits (use the 3-agent code/architecture/security pattern instead).

## Configuration

```python
delegate_task(tasks=[
    {"goal": "你是[角色1]。从[视角1]分析[问题]", "role": "leaf", "toolsets": ["terminal", "file"]},
    {"goal": "你是[角色2]。从[视角2]分析[问题]", "role": "leaf", "toolsets": ["terminal", "file"]},
    {"goal": "你是[角色3]。从[视角3]分析[问题]", "role": "leaf", "toolsets": ["terminal", "file"]},
])
```

## Role Examples

| Perspective | Role | Focus |
|------------|------|-------|
| User Research | 用户研究专家 | Pain points, willingness to pay, current solutions |
| Product Design | 产品设计专家 | Deliverables, features, tier differentiation |
| Domain Expert | 行业专家 | Methodology application, competitive landscape |
| Technical | 技术架构师 | Feasibility, performance, scalability |
| Business | 商业分析师 | Revenue model, unit economics, go-to-market |

## Synthesis Pattern

After all agents complete:
1. Read each agent's full output
2. Identify consensus (high confidence)
3. Identify contradictions (need resolution)
4. Identify unique insights (only one agent found)
5. Synthesize into a unified document

## Example

3 agents discussed "what should the deliverables be for 4 user types x 3 tiers":
- Agent 1 (User Research): Identified 4 user types' real pain points and willingness to pay
- Agent 2 (Product Design): Designed specific Free/Pro/VIP deliverables with concrete text
- Agent 3 (Product Consultant): Defined how the experiment methodology applies to each user type

Result: 512-line synthesis document with actionable deliverables for all 12 combinations.

## Pitfalls

- Agent 2 timed out (600s) → needed separate re-run with focused scope
- Agents produce overlapping content → main agent must deduplicate
- Agents may contradict each other → main agent must resolve, not just concatenate
