# Long-Run Campaign — Universal Edition (host without Hermes tooling)

The Hermes Edition skill (`profile/skills/longrun-campaign`) assumes delegate_task-style
subagents, skill loading, and profile paths. On Claude Code / Codex / Cursor / dsh hosts,
run the same protocol with these mappings — the discipline is identical, only the plumbing differs:

| Campaign element | Hermes Edition | Universal mapping |
|---|---|---|
| Mission Contract | `campaign/<id>/CONTRACT.md` | same file convention — works everywhere |
| Gate 0 material review | independent `delegate_task` reviewer (read-only) | host's subagent/review mechanism (Claude Code: subagents / `/review`; Codex: separate session; dsh: `ctx.subagents`) with an explicit "read-only, no dev context" prompt |
| Sprint loop + Gates | sprint-gated-delivery skill | follow `sprint-with-tiers` skill (included in the 9 portable skills) |
| Independence | different context per auditor | **non-negotiable**: never let the dev session audit itself; use a fresh session/subagent that sees only artifacts + design docs |
| Checkpoints | mission.json + STATUS.md | same templates in `templates/` — copy them into your repo; commit every Sprint boundary (git becomes the crash-recovery backbone) |
| Budget circuit-breaker | host token stats | if your host can't meter tokens, meter sprints + wallclock only (still 2 of 3 tripwires) |
| Interrupt & report | 5 conditions, stop and ask | same 5 — encode them in your system prompt / AGENTS.md |
| Auto-advance | agent loops phases itself | on hook-capable hosts (Claude Code Stop hooks) this is Gatekeeper territory; until then: a slash command or cron prompt "continue the campaign per CONTRACT.md" per sprint boundary |

Templates to copy: `profile/skills/longrun-campaign/templates/{CONTRACT.md, mission.json, STATUS.md}`
(from the Hermes Edition skill — same files work verbatim here).

Honest limits on non-Hermes hosts: enforcement is advisory (prompt-discipline), token metering
may be unavailable, and auto-advance needs a human/CI nudge per Sprint. Everything else —
contract-first confirmation, Gate 0, regression accumulation, checkpoint trio, 5 interrupt
conditions — is host-independent and fully applicable.


## V3.4 machine-check arsenal on non-Hermes hosts

The 8 scripts in `profile/skills/longrun-campaign/scripts/` are pure Python 3 stdlib
(no Hermes dependency) — any host with a shell can run them at the documented hook points
(scope_check at Gate 2, gate_recorder for all gate commands, gitguard as the sub-agent git
wrapper, cursor_check at crash-restart, heartbeat_check via your own cron). The campaign
SKILL.md table maps each script to its incident archetype and enforcement point.
