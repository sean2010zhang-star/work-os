# Gatekeeper — the Harness Layer of Work OS

> **Skill decides what an agent KNOWS. Agent decides how it THINKS.
> Harness decides what it CANNOT SKIP.** This is the harness.

The Work OS repo ships layers 1 and 2 (47 skills = knowledge; AGENTS.md/SOUL.md = how to
think). Gatekeeper is layer 3: a single-file, stdlib-only Python CLI that wires into your
host's hook system and **enforces the iron laws in code** — an agent cannot quietly skip
them anymore.

```
gatekeeper.py      # the CLI + rules engine + session state machine (zero dependencies)
adapters.py        # host mapping: claude_code · hermes · codex · trae · workbuddy · generic
test_gatekeeper.py # 13 red-team + golden E2E cases — run this before trusting any rules edit
```

## 60-second start

```bash
cd your-project
python3 /path/to/work-os/gatekeeper/gatekeeper.py init --host claude_code   # or hermes/codex/trae/generic
python3 /path/to/work-os/gatekeeper/gatekeeper.py doctor                    # negative self-test, must be ALL GREEN
```

Claude Code gets **hard enforcement**: `.claude/settings.json` PreToolUse + Stop hooks.
Deny reasons flow back to the model as `permissionDecisionReason` — the agent literally
sees which iron law it hit and what to do instead.

## What gets enforced (default rules = iron laws, code form)

| Rule | Hook | Strength | Law |
|------|------|----------|-----|
| `iron-0-routing-first` | PreToolUse | require-ack | no write before a recorded routing decision |
| `iron-1-plan-before-write` | PreToolUse | **deny** | L3+ needs a HUMAN-approved PLAN |
| `iron-11-auditor-git-write` | PreToolUse | **deny** | auditor/review roles cannot run git writes (the "checkout wiped uncommitted work" incident class) |
| `iron-2-mock-scan` | PreToolUse | warn | mock fingerprints in real-implementation writes |
| `iron-3-clean-close` | Stop | **deny** | no "done" with a dirty tree, no fresh commit, or no ✅⚠️❌ checklist |

Strengths map to the three-tier law system: **deny** = the 5 inviolable iron laws ·
**require-ack** = the 10 recommendations (skip needs a written ≥10-char reason, bound to
the current routing so re-routing invalidates old acks) · **warn** = red-lines.
Rules are editable JSON (`.gatekeeper/rules.json`) — `gatekeeper report` shows which fire
and suggests demoting/scripting/deleting the stale ones (rule metabolism).

## The anti-self-approval property

`plan_approved` can only be set by:
- an **interactive TTY** run of `gatekeeper approve PLAN.md`, or
- a **user_signature file** the human placed (`.gatekeeper/user_signature`).

An agent running non-interactively gets refused (and the attempt is logged, append-only).
Same for `override`. The harness's core guarantee: **the agent cannot open its own gates.**

## Host support reality check (honest)

| Host | Wiring | Enforcement |
|------|--------|-------------|
| claude_code | `.claude/settings.json` hooks | **code-enforced** deny/warn, reasons back-flow to model |
| hermes | SOUL.md block (printed) + `pre/stop` as protocol-mandated CLI calls + cron watchdog for `report` | protocol-enforced (hook bus not yet exposed to plugins) |
| codex | AGENTS.md command block | prompt-enforced |
| trae | `.trae/rules/gatekeeper.md` | project-rules enforced |
| workbuddy | SOP paste (see `expert-package/`) | prompt-enforced |
| generic | paste-into-system-prompt text | advisory |

All hosts share the same kernel and the same `.gatekeeper/` state format — one brain,
six connectors. That is the whole point of `adapters.py`.

## Known limits (registered, not hidden)

- Denies on tool-call *metadata*; an agent deliberately writing via `python -c "open(...)"`
  evades the Write matcher — the Bash-side content scan covers part of it. **Designed to
  prevent accidents and drift, not to defeat a hostile model.** OS/sandbox-level forcing is
  out of scope for a thin CLI (see `docs/gatekeeper-design.md` § risk notes).
- `stop` requires git in the workspace; non-git dirs get an honest block, not a fake pass.
- Ack state is per routing/plan digest: re-route → acks expire by design.

## Verify before trusting

```bash
python3 test_gatekeeper.py    # 13 cases: violations MUST block + legal flow MUST pass
```

Tests follow the campaign protocol's own standard: negative probes first (a rule that can't
fail a crafted violation is not trusted), golden path second (no false blocking).
