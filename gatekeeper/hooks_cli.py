#!/usr/bin/env python3
"""hooks_cli.py — host-hook entry point for gatekeeper.

Reads the hook payload as JSON on stdin (Claude Code and Hermes shell-hooks use the
SAME envelope shape: hook_event_name/tool_name/tool_input), routes to the right
gatekeeper check, and speaks the host dialect on stdout.

  pre_tool_call / PreToolUse  -> eval write/bash rules; block = {"action":"block","message":...}
  pre_verify / Stop           -> clean-close check; block = {"decision":"block","reason":...}
                                  (Hermes _parse_pre_verify accepts both dialects)

Exit codes: always 0 for pre_verify (dialect carries the verdict); for pre_tool_call we
also return exit 2 as a belt-and-braces block signal (Claude Code / Hermes both honor it).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gatekeeper import eval_pre_tool_use, state_paths, workspace  # noqa: E402

# Hermes tool names -> canonical names used in rules
TOOL_ALIAS = {
    "write_file": "Write", "Write": "Write", "write": "Write",
    "patch": "Edit", "Edit": "Edit", "MultiEdit": "Edit",
    "terminal": "Bash", "Bash": "Bash", "shell": "Bash",
    "execute_code": "Bash", "code_execution": "Bash",
    "done": "done", "finish": "done", "complete_task": "done",
}


def parse_payload(raw: str) -> dict:
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def extract(data: dict) -> tuple:
    tool_raw = data.get("tool_name") or data.get("toolName") or ""
    tool = TOOL_ALIAS.get(tool_raw, tool_raw)
    ti = data.get("tool_input") or data.get("args") or {}
    if not isinstance(ti, dict):
        ti = {}
    command = ti.get("command", "") or ti.get("code", "") or ""
    content = ti.get("new_string", "") or ti.get("content", "") or ti.get("file_text", "") or ""
    if not command and not content:
        # Edit/patch-style payloads may carry only a path; the rule engine still checks state
        command = ti.get("path", "") or ""
    return tool, command, content


def main() -> int:
    data = parse_payload(sys.stdin.read())
    event = str(data.get("hook_event_name") or data.get("event") or "").lower()
    # workspace resolution order: --workspace arg > $GK_WORKSPACE > payload cwd
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--workspace", default=None)
    pre.add_argument("--dry-run", action="store_true")
    ns, _ = pre.parse_known_args()
    if ns.workspace is None:
        ns.workspace = os.environ.get("GK_WORKSPACE") or data.get("cwd") or None
    ws = workspace(ns)

    if not state_paths(ws)["session"].exists():
        # not a gatekeeper-managed workspace: fail open, never break an unrelated host
        return 0

    if "verify" in event or event in ("stop", "subagent_stop", "agent_loop_stopped"):
        from gatekeeper import cmd_stop
        args = argparse.Namespace(workspace=str(ws), stdin=False)
        # capture cmd_stop output verbatim — its dialect is already dual-compatible
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_stop(args)
        verdict = buf.getvalue().strip()
        if verdict and '"block"' in verdict:
            print(verdict)
        return 0

    tool, command, content = extract(data)
    v = eval_pre_tool_use(ws, tool, command, content)
    if v["decision"] == "deny":
        # dual dialect in one object: Hermes reads action/message, Claude legacy reads decision/reason,
        # Claude modern hookSpecificOutput is emitted separately below when asked
        print(json.dumps({"action": "block", "message": v["reason"],
                          "decision": "block", "reason": v["reason"]}, ensure_ascii=False))
        return 2 if not ns.dry_run else 0
    if v["decision"] == "ack":
        print(json.dumps({"action": "block", "message": v["reason"],
                          "decision": "block", "reason": v["reason"]}, ensure_ascii=False))
        return 2 if not ns.dry_run else 0
    if v["decision"] == "warn":
        # informational context, non-blocking (pre_tool_call ignores 'context'; stderr is safe)
        print(f"gatekeeper WARN: {v['reason']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
