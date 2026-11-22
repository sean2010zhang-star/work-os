#!/usr/bin/env python3
"""E2E test suite for gatekeeper — red-team (violations must block) + golden (legal flow must pass).
Run: python3 test_gatekeeper.py  (uses real subprocess calls + a temp git repo)"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GK = str(Path(__file__).resolve().parent / "gatekeeper.py")
PASS, FAIL = [], []


def gk(args, ws, input=None, expect_rc=None):
    r = subprocess.run([sys.executable, GK, "--workspace", ws] + args,
                       capture_output=True, text=True, input=input)
    if expect_rc is not None and r.returncode != expect_rc:
        raise AssertionError(f"{' '.join(args)}: rc={r.returncode} want {expect_rc}\n{r.stdout}{r.stderr}")
    return r


def case(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL.append((name, str(e)))
        print(f"  FAIL  {name}: {e}")


def fresh_repo():
    tmp = tempfile.mkdtemp(prefix="gk-e2e-")
    ws = Path(tmp)
    for c in (["git", "init", "-q"], ["git", "config", "user.email", "t@t"], ["git", "config", "user.name", "t"]):
        subprocess.run(c, cwd=ws, capture_output=True)
    (ws / "a.txt").write_text("base")
    subprocess.run(["git", "add", "-A"], cwd=ws, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=ws, capture_output=True)
    gk(["init", "--host", "generic", "--force"], ws)
    return ws


def route(ws, c="L3", role="developer"):
    gk(["route", "--complexity", c, "--role", role, "--reset"], ws)


# ---------------- red-team: every violation MUST be blocked -----------------
def red_plan_before_write():
    ws = fresh_repo()
    route(ws, "L3")
    r = gk(["pre", "--tool", "Write", "--command", "src/app.py"], ws)
    assert r.returncode == 2, f"expected deny(2), got {r.returncode}: {r.stdout}"
    assert "iron-1" in r.stdout


def red_auditor_git():
    ws = fresh_repo()
    route(ws, "L3", role="auditor")
    r = gk(["pre", "--tool", "Bash", "--command", "git reset --hard HEAD~1"], ws)
    assert r.returncode == 2, r.stdout
    assert "iron-11" in r.stdout


def red_stop_dirty():
    ws = fresh_repo()
    route(ws, "L2")
    (ws / "dirty.txt").write_text("x")
    r = gk(["stop"], ws)
    v = json.loads(r.stdout)
    assert v["decision"] == "block" and "uncommitted" in v["reason"], v


def red_stop_no_done_list():
    ws = fresh_repo()
    route(ws, "L2")
    subprocess.run(["git", "add", "-A"], cwd=ws, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "work"], cwd=ws, capture_output=True)
    r = gk(["stop"], ws)
    v = json.loads(r.stdout)
    assert v["decision"] == "block" and "checklist" in v["reason"], v


def red_approve_nonhuman():
    ws = fresh_repo()
    (ws / "PLAN.md").write_text("# plan")
    env = dict(os.environ, GK_ASSUME_YES="1")  # pretend non-TTY automation
    r = subprocess.run([sys.executable, GK, "--workspace", str(ws), "approve", "PLAN.md"],
                       capture_output=True, text=True, env=env,
                       stdin=subprocess.DEVNULL)
    assert r.returncode == 1 and "refused" in (r.stdout + r.stderr).lower(), (r.returncode, r.stdout, r.stderr)


def red_override_nonhuman():
    ws = fresh_repo()
    r = subprocess.run([sys.executable, GK, "--workspace", str(ws), "override", "--reason", "x"],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)


def red_ack_needs_written_reason():
    ws = fresh_repo()
    route(ws, "L1")  # routing-first satisfied; but try ack of an arbitrary rule with short reason
    r = gk(["ack", "--rule", "iron-0-routing-first", "--reason", "no"], ws)
    assert r.returncode == 1, r.stdout


def red_claude_hook_deny_shape():
    ws = fresh_repo()
    route(ws, "L3")
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "x.py", "content": "print(1)"}})
    r = gk(["pre", "--stdin"], ws, input=payload)
    assert r.returncode == 0
    v = json.loads(r.stdout)
    assert v["hookSpecificOutput"]["permissionDecision"] == "deny", v


# ---------------- golden: the legal path must flow --------------------------
def golden_flow_with_signature():
    ws = fresh_repo()
    route(ws, "L3")
    (ws / "PLAN.md").write_text("# plan")
    (ws / ".gatekeeper" / "user_signature").write_text("ship it -user")  # human signature file
    # init appended `.gatekeeper/` to .gitignore — commit that housekeeping first
    subprocess.run(["git", "add", "-A"], cwd=ws, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "chore: gitignore gk state"], cwd=ws, capture_output=True)
    env = dict(os.environ, GK_ASSUME_YES="1")  # non-TTY; approval must come from signature file
    r = subprocess.run([sys.executable, GK, "--workspace", str(ws), "approve", "PLAN.md"],
                       capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
    assert r.returncode == 0 and "approved via signature-file" in r.stdout, (r.returncode, r.stdout, r.stderr)
    r = gk(["pre", "--tool", "Write", "--command", "src/app.py"], ws)
    assert r.returncode in (0, 1), f"write should pass after approve, got {r.returncode}: {r.stdout}"
    # do the work, commit, add done list -> stop allows
    (ws / "src").mkdir()
    (ws / "src" / "app.py").write_text("print('real')")
    subprocess.run(["git", "add", "-A"], cwd=ws, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "feat: app"], cwd=ws, capture_output=True)
    gk(["done-list", "--set", str(ws / "done.md")], ws)
    (ws / "done.md").write_text("- [x] app ✅")
    subprocess.run(["git", "add", "-A"], cwd=ws, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "docs: done list"], cwd=ws, capture_output=True)
    r = gk(["stop"], ws)
    v = json.loads(r.stdout)
    assert v["decision"] == "allow", v


def golden_small_task_no_plan_needed():
    ws = fresh_repo()
    route(ws, "L1")
    r = gk(["pre", "--tool", "Write", "--command", "note.md"], ws)
    assert r.returncode == 0, r.stdout


def golden_l1_never_needs_ack_when_routed():
    ws = fresh_repo()
    r = gk(["pre", "--tool", "Write", "--command", "x"], ws)  # UNrouted -> ack required
    assert r.returncode == 3, f"unrouted write should ack(3), got {r.returncode}: {r.stdout}"
    route(ws, "L2")
    r = gk(["pre", "--tool", "Write", "--command", "x"], ws)  # routed -> allow
    assert r.returncode == 0, r.stdout


def golden_auditor_readonly_ok():
    ws = fresh_repo()
    route(ws, "L3", role="auditor")
    r = gk(["pre", "--tool", "Bash", "--command", "git log --oneline -5"], ws)
    assert r.returncode in (0, 1) and "DENIED" not in r.stdout, r.stdout  # read-only git passes iron-11
    # (deny may still come from iron-0 if routed missing — routed here, and iron-1 only hits Write tools)


def golden_mock_content_only_warns():
    ws = fresh_repo()
    route(ws, "L2")
    (ws / "f.js").write_text("const data = MOCK_DATA;")
    r = gk(["pre", "--tool", "Write", "--file", str(ws / "f.js")], ws)
    assert "WARN" in r.stdout and r.returncode == 0, r.stdout


def main():
    print("RED-TEAM (violations must block):")
    for f in [red_plan_before_write, red_auditor_git, red_stop_dirty, red_stop_no_done_list,
              red_approve_nonhuman, red_override_nonhuman, red_ack_needs_written_reason,
              red_claude_hook_deny_shape]:
        case(f.__name__, f)
    print("GOLDEN (legal flow must pass):")
    for f in [golden_flow_with_signature, golden_small_task_no_plan_needed,
              golden_l1_never_needs_ack_when_routed, golden_auditor_readonly_ok,
              golden_mock_content_only_warns]:
        case(f.__name__, f)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    # doctor as final gate
    r = subprocess.run([sys.executable, GK, "doctor"], capture_output=True, text=True)
    print("doctor:", r.stdout.strip().splitlines()[-1])
    sys.exit(0 if not FAIL and "ALL GREEN" in r.stdout else 1)


if __name__ == "__main__":
    main()
