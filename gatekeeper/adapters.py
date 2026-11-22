"""
Host adapters — the missing third layer.

Same kernel (gatekeeper.py), thin mapping onto each host's loading conventions:
where hooks are declared, how a deny must be spoken, where state lives.

Hosts:
  claude_code : mature hooks  -> real .claude/settings.json PreToolUse/Stop hooks
  hermes      : no hook bus yet -> profile SOUL wiring + cron watchdog + manual pre/stop
  codex       : AGENTS.md native -> prompt-injected discipline + git-guard alias
  trae        : rules files (.trae/rules) -> project rules pointing at CLI
  workbuddy   : 自定义专家/SOP -> expert-package wiring doc
  generic     : paste-into-system-prompt protocol text

Every adapter returns human-readable install lines; only claude_code writes
enforcement automatically. The others wire what they CAN and document the rest.
"""
import json
import os
from pathlib import Path


class BaseAdapter:
    name = "base"
    enforces = False  # True = writes an executable hook the host runs

    def __init__(self, ws: Path, sp: dict):
        self.ws = ws
        self.sp = sp

    def _gk(self) -> str:
        # absolute path to the gatekeeper CLI for use in host configs
        return os.environ.get("GK_BIN", str(Path(__file__).resolve().parent / "gatekeeper.py"))

    def install(self):
        return [f"{self.name}: manual mode — agents must run `gatekeeper pre`/`gatekeeper stop` at the discipline points."]


class ClaudeCodeAdapter(BaseAdapter):
    name = "claude_code"
    enforces = True

    def install(self):
        cfg_dir = self.ws / ".claude"
        cfg_dir.mkdir(exist_ok=True)
        f = cfg_dir / "settings.json"
        cfg = {}
        if f.exists():
            try:
                cfg = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                cfg = {}
        gk = self._gk()
        hooks = cfg.setdefault("hooks", {})
        hooks["PreToolUse"] = [{
            "matcher": "Edit|Write|MultiEdit|Bash",
            "hooks": [{"type": "command",
                       "command": f"python3 {gk} --workspace {self.ws} pre --stdin"}],
        }]
        hooks["Stop"] = [{
            "hooks": [{"type": "command",
                       "command": f"python3 {gk} --workspace {self.ws} stop --stdin"}],
        }]
        f.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return [
            "claude_code: WROTE .claude/settings.json — PreToolUse + Stop now hard-enforced",
            "  deny flows back to the model as permissionDecisionReason (agent sees the law it hit).",
            "  note: PLAN approval stays human-only; agents cannot self-approve.",
        ]


class HermesAdapter(BaseAdapter):
    name = "hermes"

    def install(self):
        soul_line = (
            "\n## Gatekeeper enforcement (harness layer)\n"
            "- Before ANY file write or shell command on an L3+ task: "
            "`python3 {gk} --workspace <project> pre --tool <t> --command '<cmd>' --json`; "
            "exit 2 = STOP, the reason is an iron law.\n"
            "- Record routing: `gatekeeper route --complexity L<n> --role <r>` right after the [路由] block.\n"
            "- Before claiming done: `gatekeeper stop --json` must print allow; keep a done.md ✅⚠️❌ list.\n"
            "- `approve`/`override` are HUMAN commands (TTY or user_signature); never run them yourself.\n"
        ).format(gk=self._gk())
        return [
            "hermes: no hook bus exposed to plugins yet — wired as SOUL-enforced manual discipline:",
            "  append this block to your profile SOUL.md (idempotent):",
            soul_line,
            "  optional cron watchdog: run `gatekeeper report` daily; gate_log is append-only.",
        ]


class CodexAdapter(BaseAdapter):
    name = "codex"

    def install(self):
        f = self.ws / "AGENTS.md"
        block = (
            "\n<!-- gatekeeper -->\n## Gatekeeper (harness)\n"
            "Before writing files run: `python3 {gk} --workspace . pre --tool Write --file <f> --json` (exit 2 = blocked).\n"
            "After routing: `gatekeeper route --complexity L<n>`. Before 'done': `gatekeeper stop --json` == allow.\n"
            "Never call `approve`/`override` yourself; they are human gates.\n"
        ).format(gk=self._gk())
        f.write_text(f.read_text(encoding="utf-8") + block if f.exists() else block.lstrip("\n<!-- gatekeeper -->\n"), encoding="utf-8")
        return ["codex: AGENTS.md updated with gatekeeper commands (prompt-enforced; codex hooks are limited)."]


class TraeAdapter(BaseAdapter):
    name = "trae"

    def install(self):
        d = self.ws / ".trae" / "rules"
        d.mkdir(parents=True, exist_ok=True)
        (d / "gatekeeper.md").write_text(
            "# Gatekeeper rules (Work OS harness)\n"
            "1. Run `python3 {gk} --workspace . route --complexity L<n>` right after your routing block.\n"
            "2. Any Edit/Write while a gate returns exit 2 is a law violation — stop and fix the precondition.\n"
            "3. `gatekeeper stop --json` must return allow before saying 'done'.\n"
            "4. approve/override belong to the human.\n".format(gk=self._gk()), encoding="utf-8")
        return ["trae: .trae/rules/gatekeeper.md written (project-rules enforcement)."]


class WorkbuddyAdapter(BaseAdapter):
    name = "workbuddy"

    def install(self):
        return [
            "workbuddy: paste into the expert's SOP/系统提示词 (专家入驻包模式):",
            f"  python3 {self._gk()} --workspace <project> pre/stop as hard checkpoints;",
            "  see expert-package/岗位说明书.md for the full expert definition.",
        ]


class GenericAdapter(BaseAdapter):
    name = "generic"

    def install(self):
        return [
            "generic host: no adapter config exists — protocol-only mode.",
            f"  inject into system prompt: run each write through `python3 {self._gk()} pre ...`;",
            "  the laws still bind at prompt level, just not code-enforced.",
        ]


ADAPTERS = {c.name: c for c in
            (ClaudeCodeAdapter, HermesAdapter, CodexAdapter, TraeAdapter, WorkbuddyAdapter, GenericAdapter)}


def get_adapter(host: str, ws: Path, sp: dict) -> BaseAdapter:
    return ADAPTERS.get(host, GenericAdapter)(ws, sp)
