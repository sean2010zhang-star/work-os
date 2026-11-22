#!/usr/bin/env bash
# work-os installer — turns YOUR Hermes into a Work OS agent (or installs
# the portable pack on other hosts). Detects host, installs profile + skills +
# memory system, copies YOUR model config (no keys shipped), verifies.
#
# Usage:
#   ./install.sh              # auto-detect host, install
#   ./install.sh --dry-run    # show what would happen
#   ./install.sh --uninstall  # remove the work-os profile
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY=0; UNINS=0
for a in "$@"; do [ "$a" = "--dry-run" ] && DRY=1; [ "$a" = "--uninstall" ] && UNINS=1; done
say(){ printf '\033[1;36m[work-os]\033[0m %s\n' "$*"; }
run(){ if [ "$DRY" = 1 ]; then echo "  DRY: $*"; else "$@"; fi; }

# ── uninstall ─────────────────────────────────────────────────
if [ "$UNINS" = 1 ]; then
  if command -v hermes >/dev/null 2>&1; then
    run hermes profile delete work-os 2>/dev/null || true
  fi
  run rm -rf "$HOME/.hermes/profiles/work-os"
  say "work-os profile removed."; exit 0
fi

# ── host detection ────────────────────────────────────────────
HERMES_BIN="$(command -v hermes || true)"
[ -z "$HERMES_BIN" ] && [ -x "$HOME/.local/bin/hermes" ] && HERMES_BIN="$HOME/.local/bin/hermes"
if [ -z "$HERMES_BIN" ]; then
  say "Hermes not found."
  say "This installer's full path (profile + SOUL + 18+30 skills + memory) requires Hermes:"
  say "  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
  say "then re-run ./install.sh"
  say ""
  say "Or run on your current agent without Hermes:"
  say "  - Claude Code:  /plugin marketplace add sean2010zhang-star/work-os && /plugin install work-os@work-os"
  say "  - Codex CLI:    codex plugin marketplace add sean2010zhang-star/work-os"
  say "  - Any host:     copy AGENTS.md into your system prompt + skills/* into your skills dir"
  say "  - then seed your memory layer: cp -r memory/ <your-project>/memory/ and fill 偏好.md"
  exit 1
fi
say "Hermes detected: $HERMES_BIN"

# ── 1. profile ────────────────────────────────────────────────
PROFILE_DIR="$HOME/.hermes/profiles/work-os"
if [ -d "$PROFILE_DIR" ]; then
  say "Updating existing work-os profile."
else
  say "Creating profile work-os..."
  run "$HERMES_BIN" profile create work-os || { mkdir -p "$PROFILE_DIR"; }
fi

# ── 2. SOUL.md (uppercase filename is load-bearing!) ─────────
run mkdir -p "$PROFILE_DIR"
run cp "$DIR/profile/soul.template.md" "$PROFILE_DIR/SOUL.md"
say "SOUL.md installed (system prompt = Work OS protocol)."

# ── 3. skills ─────────────────────────────────────────────────
run mkdir -p "$PROFILE_DIR/skills"
if command -v rsync >/dev/null; then
  rsync -a --delete --exclude='__pycache__' --exclude='.DS_Store' "$DIR/profile/skills/" "$PROFILE_DIR/skills/"
else
  # rsync is a REQUIRED dep here (not optional): degrade to rm+cp so installs don't die mid-flight
  say "rsync missing — using rm+cp fallback for system skills (slower, same result)"
  mkdir -p "$PROFILE_DIR/skills"
  rm -rf "$PROFILE_DIR/skills"/* 2>/dev/null || true
  cp -R "$DIR/profile/skills/." "$PROFILE_DIR/skills/"
  find "$PROFILE_DIR/skills" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
fi
NSK="$(ls "$DIR/profile/skills" | wc -l | tr -d ' ')"
say "$NSK system skills installed (incl. sprint-gated-delivery + longrun-campaign) → self-evolution channel open (skill_manage writes here)."

# ── 3b. commonly-used external skills (curated: superpowers suite, github ops,
#         anthropic doc tooling, agent-engineering, research) ──────────────
if [ -d "$DIR/profile/skills-ext" ]; then
  if [ "$DRY" = 1 ]; then
    echo "  DRY: rsync skills-ext -> $PROFILE_DIR/skills/"
  else
    if command -v rsync >/dev/null; then
      rsync -a --exclude='__pycache__' --exclude='.DS_Store' "$DIR/profile/skills-ext/" "$PROFILE_DIR/skills/"
    else
      cp -R "$DIR/profile/skills-ext/." "$PROFILE_DIR/skills/"
      find "$PROFILE_DIR/skills" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    NE="$(ls "$DIR/profile/skills-ext" | wc -l | tr -d ' ')"
    TOT="$(ls -d "$PROFILE_DIR/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')"
    say "$NE curated external skills added ($TOT total in profile skills)."
  fi
fi

# ── 4. memory system (seeded, never overwriting user's) ──────
run mkdir -p "$PROFILE_DIR/memory/项目"
for f in _INDEX.md 偏好.md 工作流规范.md 决策记录.md; do
  if [ -f "$PROFILE_DIR/memory/$f" ]; then
    say "memory/$f exists — kept yours."
  elif [ -f "$DIR/memory/$f" ]; then
    run cp "$DIR/memory/$f" "$PROFILE_DIR/memory/$f"
  elif [ "$f" = "_INDEX.md" ]; then
    run cp "$DIR/memory/_INDEX.md" "$PROFILE_DIR/memory/_INDEX.md" 2>/dev/null || true
  else
    if [ "$DRY" = 1 ]; then echo "  DRY: seed $PROFILE_DIR/memory/$f"; else
      printf '# %s\n\n（首次使用时填写）\n' "$f" > "$PROFILE_DIR/memory/$f"
    fi
  fi
done
[ -f "$PROFILE_DIR/memory/_INDEX.md" ] || run cp "$DIR/memory/_INDEX.md" "$PROFILE_DIR/memory/_INDEX.md"
say "memory/ seeded: _INDEX + 偏好 + 工作流规范 + 决策记录 + 项目/"

# ── 5. model config: copy from user's active config, NOT from pack ──
SRC_CFG="$HOME/.hermes/config.yaml"
DST_CFG="$PROFILE_DIR/config.yaml"
if [ "$DRY" = 0 ]; then
python3 - "$SRC_CFG" "$DST_CFG" <<'PYEOF'
import sys, re
src, dst = sys.argv[1], sys.argv[2]
block = []
try:
    txt = open(src, encoding="utf-8").read()
    # extract model: section (provider/default/base_url; strip api_key lines)
    m = re.search(r'^model:\n((?:^[ \t]+.*\n)+)', txt, re.M)
    if m:
        for line in m.group(1).splitlines():
            if "api_key" in line:
                line = re.sub(r'(api_key:\s*).*', r'\1""  # set via: hermes -p work-os config set / .env', line)
            block.append(line)
except FileNotFoundError:
    pass
try:
    cur = open(dst, encoding="utf-8").read() if __import__("os").path.exists(dst) else ""
except FileNotFoundError:
    cur = ""
out = cur
if block:
    model_yaml = "model:\n" + "\n".join(block) + "\n"
    if re.search(r'^model:\n(?:[ \t]+.*\n)+', out or "", re.M):
        out = re.sub(r'^model:\n(?:[ \t]+.*\n)+', model_yaml, out or "", flags=re.M)
    else:
        out = (out or "") + "\n" + model_yaml
open(dst, "w", encoding="utf-8").write(out or model_yaml or "")
print("[work-os] model block copied from your config (api_key masked — set yours via `hermes -p work-os model` or .env)")
PYEOF
fi

# ── 6. dependencies ───────────────────────────────────────────
say "Optional dependencies check:"
command -v git >/dev/null && say "  git  ✓ (version iron-law works)" || say "  git  ✗ REQUIRED — install first"
command -v node >/dev/null && say "  node ✓ (JS syntax red-line available)" || say "  node ○ optional: install for the 'node --check' red-line"
command -v gh >/dev/null && say "  gh   ✓ (github backup layer available)" || say "  gh   ○ optional: GitHub backup layer"
command -v rsync >/dev/null && say "  rsync ✓ (fast path; cp -R fallback used if absent)"
say "Accounts: LLM provider — copied from your Hermes config above; GitHub token — only if"
say "you adopt that backup layer; the pack ships placeholders, never keys."

# ── 7. verify (SOUL loaded = routing block appears) ───────────
if [ "$DRY" = 0 ]; then
  say "Verification: one-shot identity+routing test (may take ~30s)..."
  OUT="$("$HERMES_BIN" -p work-os chat -q "不要执行任何操作。按你的工作协议，对任务'写一个hello world脚本'只输出路由决策块和一句话说明你的体系来源。" 2>&1 | tail -20)"
  if echo "$OUT" | grep -q "\[路由\]"; then
    say "PASS — SOUL active, agent emits routing decision."
  else
    say "WARN — no [路由] block detected. Check SOUL.md case (must be uppercase) and run:"
    echo "$OUT" | sed 's/^/    /'
  fi
  run "$HERMES_BIN" profile use work-os 2>/dev/null && say "work-os is now your default profile. Switch back: hermes profile use default" || say "Activate with: hermes profile use work-os  (or hermes -p work-os)"
  # ── 7b. harness layer (layer 3) ──────────────────────────────
if [ -f "$DIR/gatekeeper/gatekeeper.py" ]; then
  # wire real tool-level hooks into the profile config (Hermes shell-hooks: pre_tool_call/pre_verify)
  GK_PROFILE="$HOME/.hermes/profiles/work-os"
  if [ -d "$GK_PROFILE" ]; then
    python3 "$DIR/gatekeeper/gatekeeper.py" --workspace "$GK_PROFILE" init --host hermes 2>/dev/null \
      && say "harness wired: hooks block added to profile config.yaml (approve the consent prompt once on next launch, or set hooks_auto_accept)" \
      || say "harness wiring skipped (existing hooks block?) — see gatekeeper/README.md"
  fi
  say "Per-project harness: python3 $DIR/gatekeeper/gatekeeper.py init --host <host>  # Claude Code = real hooks, Hermes profile = already wired above"
fi

# ── 8. first-run onboarding: preference interview (L3 cold-start fix) ──
  # SOUL.md hard rule: empty 偏好.md template → agent auto-interviews at first turn.
  if [ -t 0 ]; then
    say "Launching interactive Work OS session — it will detect the empty 偏好.md and"
    say "interview you (4 groups of questions) before taking any task. Say '跳过引导' to skip."
    say "Re-enter any time: hermes -p work-os"
    "$HERMES_BIN" -p work-os || say "session exited — run: hermes -p work-os"
  else
    say "Non-interactive shell: the first 'hermes -p work-os' session will"
    say "auto-interview you (SOUL rule: empty 偏好.md → guided fill before first task)."
  fi
else
  say "DRY-RUN complete — no changes made."
fi
say ""
say "Done. Try: hermes -p work-os chat -q \"帮我重构这个模块\"  → first reply should be a routing decision."
