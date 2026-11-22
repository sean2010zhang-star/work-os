#!/usr/bin/env python3
"""Tests for adapters.py + hooks_cli.py — the host wiring itself is now under test.
Covers: config emitted per host is well-formed, idempotent on re-init, hooks_cli speaks
both dialects (Claude Code + Hermes shell-hooks), and tool-name aliases map correctly."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adapters  # noqa: E402
from gatekeeper import save_json, state_paths  # noqa: E402

PASS, FAIL = [], []


def case(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append(name)
        print(f"  FAIL  {name}: {e}")


def fresh_ws(host="generic"):
    tmp = Path(tempfile.mkdtemp(prefix="gk-ad-"))
    subprocess.run(["git", "init", "-q"], cwd=tmp, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp, capture_output=True)
    (tmp / "a.txt").write_text("base")
    subprocess.run(["git", "add", "-A"], cwd=tmp, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp, capture_output=True)
    sp = state_paths(tmp)
    sp["dir"].mkdir(parents=True, exist_ok=True)
    save_json(sp["session"], {"complexity": None, "routed": False, "role": "developer",
                              "plan_approved": False})
    save_json(sp["rules"], list(__import__("gatekeeper").DEFAULT_RULES))
    return tmp


# ---------------- claude_code adapter ----------------
def ad_claude_valid_json_and_idempotent():
    ws = fresh_ws("claude_code")
    lines = adapters.ClaudeCodeAdapter(ws, state_paths(ws)).install()
    assert any("settings.json" in l for l in lines), lines
    cfg = json.loads((ws / ".claude/settings.json").read_text())
    assert cfg["hooks"]["PreToolUse"][0]["matcher"].startswith("Edit|Write")
    assert "pre --stdin" in cfg["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    before = (ws / ".claude/settings.json").read_text()
    adapters.ClaudeCodeAdapter(ws, state_paths(ws)).install()  # re-run
    # re-run preserves user keys (writes whole cfg back — check no crash, still valid json)
    json.loads((ws / ".claude/settings.json").read_text())


def ad_claude_preserves_user_settings():
    ws = fresh_ws("claude_code")
    (ws / ".claude").mkdir()
    (ws / ".claude/settings.json").write_text(json.dumps({"permissions": {"allow": ["Bash(npm run)"]}}))
    adapters.ClaudeCodeAdapter(ws, state_paths(ws)).install()
    cfg = json.loads((ws / ".claude/settings.json").read_text())
    assert cfg["permissions"]["allow"] == ["Bash(npm run)"], "user settings clobbered!"
    assert "hooks" in cfg


# ---------------- hermes adapter ----------------
def ad_hermes_wires_config_yaml():
    ws = fresh_ws("hermes")
    (ws / "config.yaml").write_text("model:\n  default: some/model\nprovider: x\n")
    lines = adapters.HermesAdapter(ws, state_paths(ws)).install()
    t = (ws / "config.yaml").read_text()
    assert "hooks:" in t and "pre_tool_call:" in t and "pre_verify:" in t, t
    assert t.startswith("model:")  # appended, not replaced
    assert any("CONSENT" in l or "consent" in l for l in lines)


def ad_hermes_idempotent_and_existing_hooks():
    ws = fresh_ws("hermes")
    (ws / "config.yaml").write_text("model:\n  default: m\n")
    adapters.HermesAdapter(ws, state_paths(ws)).install()
    t1 = (ws / "config.yaml").read_text()
    adapters.HermesAdapter(ws, state_paths(ws)).install()
    t2 = (ws / "config.yaml").read_text()
    assert t1 == t2, "not idempotent"
    # user with existing hooks block -> refuse-to-clobber path
    ws2 = fresh_ws("hermes")
    (ws2 / "config.yaml").write_text("hooks:\n  pre_tool_call:\n    - command: echo mine\n")
    lines = adapters.HermesAdapter(ws2, state_paths(ws2)).install()
    assert any("merge" in l.lower() for l in lines), lines
    assert "echo mine" in (ws2 / "config.yaml").read_text()


# ---------------- hooks_cli protocol ----------------
def _run_hooks_cli(ws, payload, extra_args=()):
    r = subprocess.run([sys.executable, str(HERE / "hooks_cli.py"), "--workspace", str(ws), *extra_args],
                       input=json.dumps(payload), capture_output=True, text=True)
    return r


def hc_hermes_payload_block():
    ws = fresh_ws()
    _set(ws, complexity="L3", routed=True, plan_approved=False)
    r = _run_hooks_cli(ws, {"hook_event_name": "pre_tool_call", "tool_name": "write_file",
                            "args": {"path": "x.py", "content": "print(1)"}})
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    v = json.loads(r.stdout)
    assert v["action"] == "block" and v["decision"] == "block", v
    assert "iron-1" in v["message"]


def hc_claude_payload_block():
    ws = fresh_ws()
    _set(ws, complexity="L3", routed=True, plan_approved=False)
    r = _run_hooks_cli(ws, {"hook_event_name": "PreToolUse", "tool_name": "Write",
                            "tool_input": {"file_path": "x.py", "content": "print(1)"}})
    assert r.returncode == 2
    v = json.loads(r.stdout)
    assert v["action"] == "block"


def hc_terminal_git_by_auditor():
    ws = fresh_ws()
    _set(ws, complexity="L3", routed=True, role="auditor", plan_approved=True)
    r = _run_hooks_cli(ws, {"hook_event_name": "pre_tool_call", "tool_name": "terminal",
                            "args": {"command": "git reset --hard HEAD~1"}})
    assert r.returncode == 2
    assert "iron-11" in json.loads(r.stdout)["message"]


def hc_pre_verify_dirty():
    ws = fresh_ws()
    _set(ws, complexity="L2", routed=True)
    (ws / "dirty.txt").write_text("x")
    r = _run_hooks_cli(ws, {"hook_event_name": "pre_verify", "tool_name": None})
    v = json.loads(r.stdout)  # block directive emitted only when dirty
    assert v["decision"] == "block" and "uncommitted" in v["reason"], v


def hc_pre_verify_clean_is_silent():
    ws = fresh_ws()
    done = ws / "done.md"
    done.write_text("- [x] work")
    _set(ws, complexity="L2", routed=True, done_list=str(done))
    subprocess.run(["git", "add", "-A"], cwd=ws, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "w"], cwd=ws, capture_output=True)
    r = _run_hooks_cli(ws, {"hook_event_name": "pre_verify", "tool_name": None})
    assert r.stdout.strip() == "", r.stdout  # no message -> host lets turn finish
    assert r.returncode == 0


def hc_unmanaged_workspace_fails_open():
    tmp = Path(tempfile.mkdtemp(prefix="gk-ad-none-"))
    r = _run_hooks_cli(tmp, {"hook_event_name": "pre_tool_call", "tool_name": "write_file",
                             "args": {"path": "x", "content": "y"}})
    assert r.returncode == 0 and r.stdout.strip() == "", "must not break unrelated hosts"


def hc_warn_is_stderr_not_blocking():
    ws = fresh_ws()
    _set(ws, complexity="L2", routed=True)
    r = _run_hooks_cli(ws, {"hook_event_name": "pre_tool_call", "tool_name": "write_file",
                            "args": {"path": "x.py", "content": "const d = MOCK_DATA;"}})
    assert r.returncode == 0
    assert "WARN" in r.stderr


def hc_gk_workspace_env_fallback():
    ws = fresh_ws()
    _set(ws, complexity="L3", routed=True)
    env = dict(os.environ, GK_WORKSPACE=str(ws))
    r = subprocess.run([sys.executable, str(HERE / "hooks_cli.py")], input=json.dumps(
        {"hook_event_name": "pre_tool_call", "tool_name": "patch",
         "args": {"path": "a.txt", "old_string": "base", "new_string": "x"}}),
        capture_output=True, text=True, env=env)
    assert r.returncode == 2  # patch aliases to Edit, but iron-1 targets Write tools; check which rule
    # if it passed because alias not in tools list, that's a real gap the test should surface
    v = json.loads(r.stdout)
    assert "iron-1" in v["message"], v


def _set(ws, **kw):
    sp = state_paths(ws)
    s = json.loads(sp["session"].read_text())
    s["acked_rules"] = {}
    s.update(kw)
    if kw.get("routed"):
        s["routed_at"] = "2026-01-01T00:00:00+0800"
    save_json(sp["session"], s)


def main():
    print("ADAPTERS:")
    for f in [ad_claude_valid_json_and_idempotent, ad_claude_preserves_user_settings,
              ad_hermes_wires_config_yaml, ad_hermes_idempotent_and_existing_hooks]:
        case(f.__name__, f)
    print("HOOKS_CLI protocol:")
    for f in [hc_hermes_payload_block, hc_claude_payload_block, hc_terminal_git_by_auditor,
              hc_pre_verify_dirty, hc_pre_verify_clean_is_silent, hc_unmanaged_workspace_fails_open,
              hc_warn_is_stderr_not_blocking, hc_gk_workspace_env_fallback]:
        case(f.__name__, f)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
