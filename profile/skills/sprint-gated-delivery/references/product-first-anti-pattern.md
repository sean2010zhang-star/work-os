# Product-First Anti-Pattern (typical lesson)

## What Happened

典型反例：3 个 Sprint 的开发：
- Sprint 1: Experiment engine (995 lines)
- Sprint 2: Report system (607 lines)
- Sprint 3: Tier differentiation (540 lines)

Total: 1,562 lines of code, 3 HTML reports generated.

User feedback: "一塌糊涂，根本没有让人想付钱订阅的想法"

## Root Cause

Built before understanding:
1. Who are the users (4 types with very different needs)
2. What do they want (specific deliverables, not features)
3. Why would they pay (determinism, not "AI analysis")
4. What's the competitive moat (experiment methodology, not reports)

## The Anti-Pattern

```
Wrong: Technical Architecture → Sprint Development → Product Definition
Right: Product Definition → Technical Architecture → Sprint Development
```

## Warning Signs

- Can't answer "why would someone pay for this" in one sentence
- Don't know what each user type's deliverable looks like (specific text/data)
- Can't explain the difference vs ChatGPT/competitors
- Upgrade hooks are "🔒 upgrade to Pro" instead of information-gap driven
- Free/Pro/VIP differ by feature count, not cognitive depth

## The Fix

Before Sprint 1, complete:
1. User research (who, what pain, what they want, how much they'll pay)
2. Deliverable design (what each user sees at each tier, with concrete examples)
3. Competitive analysis (vs ChatGPT, vs MBTI, vs career counselors)
4. Upgrade mechanism (information gaps, not locks)

## Lesson

The experimental engine is the MOAT (makes deliverables more reliable than ChatGPT).
The deliverables are the PRODUCT (what users see and pay for).
Both matter, but deliverables come first in the design process.
