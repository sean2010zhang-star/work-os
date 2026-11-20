# Effectiveness: what you actually get vs the reference machine

Honest answer to "will this work like the author's setup?" — the system has four layers,
and the installer reproduces them unevenly. Knowing which is which prevents disappointment.

## The four-layer model

| Layer | What it is | Ships in this repo? | Equivalence on install day |
|-------|-----------|---------------------|----------------------------|
| **L1 Discipline** | Routing protocol, 5 iron laws, 10 recommendations, quality red-lines, Sprint×Gate tiers, campaign contract | Yes — SOUL.md / AGENTS.md + 17 system skills, verbatim same rules (only project examples stripped) | **≈100%.** Behavior change is immediate and model-independent-ish: routing block first, PLAN before write for L3+, honest completion claims. Verified by A/B test: an agent with zero prior context, given only AGENTS.md text, restructured its task response (interrupted itself to request confirmation, defined falsifiable "integration complete" criteria). |
| **L2 Method library** | How-tos: audit checklists, plan templates, git versioning, pitfall lists, 30 curated external skills (superpowers dev suite, GitHub ops, document tooling, research) | Yes — the general/common part | **≈90%** for engineering & document workflows. |
| **L3 Memory layer** | The user's accumulated preferences, project dossiers, decision ledger, workflow lessons — the per-person context the agent reads every task | **Structure ships, content is yours** (seeded templates + mandatory first-run interview that fills 偏好.md) | **0 on day one → 60-70% after 2-4 weeks of use**, because the feedback loop (read → work → update after lessons) is installed and now mandatory. |
| **L4 Domain assets** | Industry-specific skills and environment quirks vertical/domain assets the original author built for a specific business (pricing engines, bidding systems, personal integrations) | **Deliberately excluded** — these are competitively sensitive and/or private | **0%. By design.** Custom engagements available separately. |

## What "same effect as the author" really means

- The **first-week experience ≈ the author's experience at month zero** — same rules biting
  on day one, same interview seeding preferences, same campaign protocol ready.
- **Convergence over time**: L3 is generative. The memory protocol + `longrun-campaign`
  checkpoints + skill self-evolution channel (agent saves new skills into its profile as it
  works) means every user's install grows its own L3 — it will approach, then diverge from,
  the author's setup as their work differs. That's the design intent: this is a *system that
  accumulates*, not a snapshot of one person's accumulation.
- Things L4-shaped users may notice missing: vertical workflows. If your domain is covered
  in the pack (general software, docs, research), expect near-parity; if it isn't, expect
  excellent *discipline* plus the tooling to build your own vertical skills fast.

## Honest limits

1. **Model dependence**: laws are prompt-level; compliance rate scales with the host model's
   instruction-following. Strong models: near-deterministic. Weak models: useful but leaky —
   hard enforcement (hook-level deny) is the Gatekeeper roadmap item.
2. **Token metering** in campaign budgets depends on host stats availability.
3. **Universal Edition** (non-Hermes hosts) = L1 (~70%: no SOUL-level forced injection, no
   auto-campaign detection) + half of L2 + L3 via manual file wiring. The Hermes Edition is
   the full experience.

## Measuring it yourself (first-run acceptance test)

After install, ask your agent: *"Add authentication to my Flask app and a React login page."*
A working install replies — **before touching files** — with a routing block
(`[路由] 分类=代码 | 复杂度=L3 …`), complexity-tiered plan, and a confirmation request.
Then run one small real task and check the closing: commit+tag made? completion marked
✅⚠️❌ item-by-item? If yes on both ends, L1 is live.
