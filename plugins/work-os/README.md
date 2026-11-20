# Work OS — Universal Edition (non-Hermes agents)

Portable protocol pack for **any agent host**: Claude Code, Codex CLI, Cursor, Windsurf,
Cline, Copilot, dsh, OpenCode, or anything that reads a system prompt.

> If the host is **Hermes**, don't use this edition — go to the repo root and run
> `./install.sh` (Hermes Edition = full system: SOUL protocol + 47 skills + memory loop +
> first-run interview + installer verification).

## What you get here

| Piece | File(s) | Effect |
|-------|---------|--------|
| The protocol | repo-root `AGENTS.md` | Routing decision on every task, 5 iron laws, 10 recommendations, quality red-lines, closing checklist, memory protocol |
| 8 portable skills | `skills/*/SKILL.md` | router details, methodology overview, iron laws full text, Sprint×Gate tiers, plan-confirm templates, delivery-audit checklists, git versioning, cross-project pitfalls |
| Memory seed | repo-root `memory/` | `_INDEX` + preferences/workflow/decision templates — the feedback loop, file-based, host-agnostic |

## Install (30 seconds, by host)

**Claude Code**
```
/plugin marketplace add sean2010zhang-star/work-os
/plugin install work-os@work-os
```

**Codex CLI**
```
codex plugin marketplace add sean2010zhang-star/work-os
```

**Cursor / Windsurf / Cline / OpenCode / Copilot / dsh / anything else**
```
cp AGENTS.md <your-project>/            # or paste into your system prompt
cp -r skills/* <your-skills-dir>/       # if the host reads SKILL.md; else skip
cp -r memory/ <your-project>/memory/    # then fill 偏好.md with 3-5 of your preferences
```

## What is guaranteed vs best-effort (honest)

- **Guaranteed on every host**: the protocol changes first-move behavior — routing block
  before action, PLAN-before-write for medium+ tasks, honest completion claims. Works as
  pure prompt text.
- **Host-dependent**: skill auto-loading (native on Claude Code/Codex; manual `read`
  elsewhere), and enforcement strength — prompts advise, they don't block. Hard blocking
  (deny/ack/warn gates via hooks) is the Gatekeeper roadmap item
  (repo `docs/gatekeeper-design.md`); it also needs no Hermes.
- **Not in this edition**: the other 7 skills (三省六部 multi-role engineering, M1-M18
  selector, session discipline, QA/infra layers, error-memory, retro) depend on Hermes
  tooling (skill_manage, profiles, cron). On non-Hermes hosts their content is carried by
  `AGENTS.md`'s laws and red-lines instead.

## First-run check

Ask your agent: "Add authentication to my Flask app and a React login page."
A correctly installed Work OS agent replies with a routing block
(`[路由] classification | complexity L3 | ...`) and a PLAN asking for confirmation —
**before** writing files.
