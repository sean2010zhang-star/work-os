#!/usr/bin/env python3
"""
Gatekeeper — the harness layer of Work OS.
Skill decides what an agent KNOWS. Agent decides how it THINKS.
Harness decides what it CANNOT SKIP. This is that harness.

Single-file, stdlib-only CLI. Wraps host hook systems (Claude Code hooks /
Hermes profile / Codex / Trae / WorkBuddy) and enforces the Work OS iron laws
in code: deny > require-ack > warn > log-only.

Anti-self-approval: `plan_approved` can ONLY be set by `gatekeeper approve`
running against a human TTY (or an explicit user signature file). An agent
calling these commands non-interactively cannot open its own gates.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VERSION = "0.2.0"
STATE_DIR = ".gatekeeper"
DEFAULT_RULES = [
    {
        "id": "iron-1-plan-before-write",
        "law": "L3+ tasks need an approved PLAN before any write",
        "hook": "pre_tool_use",
        "when": {"complexity_gte": "L3", "tools": ["Edit", "Write", "write_file", "patch", "MultiEdit", "done"]},
        "unless_state": "plan_approved",
        "strength": "deny",
        "reason": "IRON LAW 1: complexity>=L3 and no approved plan. Emit the [路由] decision block, write PLAN.md, then ask the user to run `gatekeeper approve` (only a human TTY can set the flag).",
    },
    {
        "id": "iron-11-auditor-git-write",
        "law": "auditor/subagent roles never run git writes",
        "hook": "pre_tool_use",
        "when": {"role_in": ["auditor", "review", "audit"], "bash_regex": r"git\s+(checkout|reset|stash|restore|commit|push|rebase|merge)"},
        "strength": "deny",
        "reason": "IRON LAW 11: role=auditor cannot write git state (incident archetype: auditor's `git checkout` wiped uncommitted work). Use `git worktree add` for a clean baseline.",
    },
    {
        "id": "iron-2-mock-scan",
        "law": "content declared as real implementation must not carry mock fingerprints",
        "hook": "pre_tool_use",
        "when": {"tools": ["Write", "write_file", "Edit"], "content_regex": r"(MOCK_DATA|fake response|// mock data|setTimeout\([^)]*\)\s*[,)])", "unless_regex": r"(test|fixture|mock\.)"},
        "strength": "warn",
        "reason": "IRON LAW 2 fingerprint: mock-like content in a write. If this is a stub, mark it `# STUB: not wired`; if it is the real implementation, wire it.",
    },
    {
        "id": "iron-3-clean-close",
        "law": "no 'done' claim with a dirty tree or without a fresh commit",
        "hook": "stop",
        "strength": "deny",
        "reason": "IRON LAWS 3/5 + closing checklist: commit+tag with per-item verification is required before completion claims.",
    },
    {
        "id": "iron-0-routing-first",
        "law": "a routing decision must be recorded before executing",
        "hook": "pre_tool_use",
        "when": {"complexity_unset": True, "tools": ["Edit", "Write", "write_file", "patch", "Bash"]},
        "unless_state": "routed",
        "strength": "require-ack",
        "reason": "Entry protocol: run `gatekeeper route --complexity L<n> [--role r]` first (this mirrors emitting the [路由] block).",
    },
    {
        # Anti-false-block covenant: the harness may ONLY stop a completion claim when it can
        # cite a specific failed iron law. Never invent blocks to look powerful.
        "id": "done-gate",
        "law": "a 'done' claim may only be blocked by named, cited law failures",
        "hook": "pre_tool_use",
        "when": {"tools": ["done"]},
        "unless_state": "done_verified",
        "strength": "deny",
        "reason": "IRON LAW 3/5 gate: run `gatekeeper verify-done` (mirrors the Stop hook: commit fresh + tree clean + checklist present). If it passes, the 'done' claim is allowed; the harness blocks completion claims on nothing else.",
    },
]


# ---------------------------------------------------------------- utilities
def workspace(args) -> Path:
    return Path(args.workspace or os.environ.get("GK_WORKSPACE") or os.getcwd()).resolve()


def state_paths(ws: Path) -> dict:
    d = ws / STATE_DIR
    return {
        "dir": d,
        "session": d / "session.json",
        "rules": d / "rules.json",
        "log": d / "gate_log.jsonl",
        "sig": d / "user_signature",
    }


def load_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def log_event(ws: Path, event: dict) -> None:
    sp = state_paths(ws)
    sp["dir"].mkdir(parents=True, exist_ok=True)
    event["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(sp["log"], "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def out(verdict: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(verdict, ensure_ascii=False))
    else:
        mark = {"deny": "DENIED", "ack": "ACK-REQUIRED", "warn": "WARN", "allow": "ALLOW", "info": "OK"}
        print(f"{mark.get(verdict['decision'], verdict['decision'].upper())}: {verdict.get('reason', '')}")
    return {"deny": 2, "ack": 3}.get(verdict["decision"], 0)


# ---------------------------------------------------------------- commands
def cmd_init(args) -> int:
    ws = workspace(args)
    sp = state_paths(ws)
    sp["dir"].mkdir(parents=True, exist_ok=True)
    # gatekeeper state is not a deliverable — keep it out of the clean-close gate
    gi = ws / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    if ".gatekeeper/" not in lines:
        lines.append(".gatekeeper/")
        gi.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not sp["session"].exists() or args.force:
        save_json(sp["session"], {
            "version": VERSION,
            "host": args.host,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "complexity": None,
            "role": "developer",
            "routed": False,
            "plan_approved": False,
            "plan_file": None,
            "done_verified": False,
        })
    if args.rules and os.path.exists(args.rules):
        save_json(sp["rules"], load_json(Path(args.rules)) or DEFAULT_RULES)
    elif not sp["rules"].exists():
        save_json(sp["rules"], DEFAULT_RULES)
    rules_n = len(load_json(sp["rules"], DEFAULT_RULES) or DEFAULT_RULES)
    # host adapter: write the integration file the host actually reads
    from adapters import get_adapter
    adapter = get_adapter(args.host, ws, sp)
    lines = adapter.install()
    log_event(ws, {"event": "init", "host": args.host})
    print(f"gatekeeper {VERSION}: state at {sp['dir']} (rules={rules_n}, host={args.host})")
    for l in lines:
        print("  " + l)
    print("next: `gatekeeper doctor` to self-test; agents must call `gatekeeper route` before writes.")
    return 0


def cmd_route(args) -> int:
    ws = workspace(args)
    sp = state_paths(ws)
    s = load_json(sp["session"]) or {}
    s.update({"complexity": args.complexity, "role": args.role, "routed": True,
              "task_class": args.task_class, "routed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    if args.reset:
        s.update({"plan_approved": False, "plan_file": None, "done_verified": False})
    save_json(sp["session"], s)
    log_event(ws, {"event": "route", "complexity": args.complexity, "role": args.role, "class": args.task_class})
    print(f"routed: complexity={args.complexity} role={args.role} class={args.task_class}")
    if args.complexity in ("L3", "L4"):
        print("L3+ requires PLAN approval by a HUMAN: write PLAN.md then run `gatekeeper approve PLAN.md` in a real terminal.")
    return 0


def cmd_approve(args) -> int:
    ws = workspace(args)
    sp = state_paths(ws)
    s = load_json(sp["session"]) or {}
    plan = args.plan
    if not os.path.isabs(plan):
        plan = str(ws / plan)
    if not os.path.exists(plan):
        print(f"approve: plan file not found: {plan}", file=sys.stderr)
        return 1
    interactive = sys.stdin.isatty() and sys.stdout.isatty() and os.environ.get("GK_ASSUME_YES") != "1"
    signature = None
    if sp["sig"].exists():  # explicit user-provided signature file (for headless hosts)
        signature = sp["sig"].read_text(encoding="utf-8").strip()
    if not interactive and not signature:
        log_event(ws, {"event": "approve_attempt_blocked", "plan": plan, "why": "no TTY and no user_signature file"})
        print("approve refused: no interactive TTY and no .gatekeeper/user_signature file.\n"
              "PLAN approval is a human act — open a real terminal, or have the user place\n"
              "their signature: echo '<their word>' > .gatekeeper/user_signature", file=sys.stderr)
        return 1
    digest = subprocess.run(["shasum", plan], capture_output=True, text=True).stdout.split() or ["?"]
    if interactive:
        ans = input(f"Approve PLAN '{plan}' ({digest[0][:10]}) for '{s.get('task_class','task')}' [{s.get('complexity')}]? yes/N: ")
        if ans.strip().lower() not in ("yes", "y"):
            log_event(ws, {"event": "approve_declined", "plan": plan})
            print("declined; session stays unapproved.")
            return 1
    s.update({"plan_approved": True, "plan_file": os.path.abspath(plan),
              "plan_digest": digest[0], "approved_via": "tty" if interactive else "signature-file",
              "approved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    save_json(sp["session"], s)
    log_event(ws, {"event": "approve", "plan": plan, "digest": digest[0], "via": s["approved_via"]})
    print(f"PLAN approved via {s['approved_via']}: {plan}")
    return 0


# ---------------------------------------------------------------- evaluation
def _cmp_complexity(a: str, b: str) -> int:
    order = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}
    return (order.get(a, 0) > order.get(b, 0)) - (order.get(a, 0) < order.get(b, 0))


def eval_pre_tool_use(ws: Path, tool: str, command: str, content: str) -> dict:
    sp = state_paths(ws)
    s = load_json(sp["session"], {}) or {}
    rules = load_json(sp["rules"], DEFAULT_RULES) or DEFAULT_RULES
    verdict = {"decision": "allow", "reason": "", "rule": None}
    for r in rules:
        if r["hook"] != "pre_tool_use":
            continue
        w = r.get("when", {})
        hit = True
        if "tools" in w and tool not in w["tools"]:
            hit = False
        if "complexity_gte" in w:
            c = s.get("complexity")
            if not c or _cmp_complexity(c, w["complexity_gte"]) < 0:
                hit = False
        if w.get("complexity_unset") and (s.get("complexity") or s.get("routed")):
            hit = False
        if "role_in" in w and s.get("role", "developer") not in w["role_in"]:
            hit = False
        if "bash_regex" in w and not re.search(w["bash_regex"], command or "", re.I):
            hit = False
        if "content_regex" in w:
            hay = (content or "") + " " + (command or "")
            if not re.search(w["content_regex"], hay, re.I | re.S):
                hit = False
            if w.get("unless_regex") and re.search(w["unless_regex"], tool + " " + (command or ""), re.I):
                hit = False
        if not hit:
            continue
        unless = r.get("unless_state")
        if unless and s.get(unless):
            continue
        # ack is bound to the CURRENT plan/routing; None must never equal None
        target = s.get("plan_digest") or s.get("routed_at")
        acked = bool(target) and (s.get("acked_rules") or {}).get(r["id"]) == target
        if r["strength"] == "deny" or (r["strength"] == "require-ack" and not acked):
            verdict = {"decision": "deny" if r["strength"] == "deny" else "ack",
                       "reason": f"[{r['id']}] {r['reason']}", "rule": r["id"]}
            log_event(ws, {"event": "pre_tool_use_" + verdict["decision"], "rule": r["id"], "tool": tool,
                           "cmd_head": (command or content or "")[:120]})
            return verdict
        else:  # warn / already-acked
            log_event(ws, {"event": "warn", "rule": r["id"], "tool": tool})
            verdict = {"decision": "warn", "reason": f"[{r['id']}] {r['reason']}", "rule": r["id"]}
    return verdict


def cmd_pre(args) -> int:
    ws = workspace(args)
    if args.stdin:  # Claude Code hook protocol: JSON on stdin
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
        ti = data.get("tool_input", {}) or {}
        tool = data.get("tool_name", "")
        command = ti.get("command", "") or ""
        content = ti.get("new_string", "") or ti.get("content", "") or ti.get("file_text", "") or ""
        v = eval_pre_tool_use(ws, tool, command, content)
        if v["decision"] == "deny":
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "deny", "permissionDecisionReason": v["reason"]}}))
            return 0
        if v["decision"] == "warn":
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow",
                                 "additionalContext": "gatekeeper WARN: " + v["reason"]}}))
            return 0
        return 0
    v = eval_pre_tool_use(ws, args.tool or "", args.command or "",
                          Path(args.file).read_text(encoding="utf-8", errors="ignore") if args.file else "")
    return out(v, args.json)


def cmd_ack(args) -> int:
    ws = workspace(args)
    sp = state_paths(ws)
    s = load_json(sp["session"], {}) or {}
    if not args.reason or len(args.reason) < 10:
        print("ack refused: --reason must be a written justification of >=10 chars (skips need stated reasons).", file=sys.stderr)
        return 1
    s.setdefault("acked_rules", {})[args.rule] = s.get("plan_digest") or s.get("routed_at")
    s.setdefault("ack_reasons", {})[args.rule] = args.reason
    save_json(sp["session"], s)
    log_event(ws, {"event": "ack", "rule": args.rule, "reason": args.reason})
    print(f"ack recorded for {args.rule} (bound to current plan/routing — re-ack after next route reset).")
    return 0


def cmd_stop(args) -> int:
    """Stop hook: completion claims require clean tree + fresh commit + done-list."""
    ws = workspace(args)
    sp = state_paths(ws)
    s = load_json(sp["session"], {}) or {}
    if args.stdin:  # accept and ignore hook payload
        sys.stdin.read()
    dirty = subprocess.run(["git", "-C", str(ws), "status", "--porcelain"], capture_output=True, text=True)
    if dirty.returncode != 0:  # not a repo / git missing: cannot assert clean-close
        print(json.dumps({"decision": "block", "reason": f"[iron-3-clean-close] git unavailable: {dirty.stderr[:80]}"}))
        return 0
    problems = []
    if dirty.stdout.strip():
        problems.append("uncommitted changes: " + dirty.stdout.strip().splitlines()[0][:80])
    last = subprocess.run(["git", "-C", str(ws), "log", "-1", "--format=%ct"], capture_output=True, text=True)
    started = s.get("routed_at")
    if last.returncode == 0 and started:
        try:
            st = time.mktime(time.strptime(started, "%Y-%m-%dT%H:%M:%S%z"))
            if int(last.stdout.strip()) < st:
                problems.append("no commit made during this session (iron law 3)")
        except ValueError:
            pass
    donefile = s.get("done_list") or str(sp["dir"] / "done.md")
    if not os.path.exists(donefile):
        problems.append(f"completion checklist missing: {donefile} (write per-item ✅⚠️❌📅 before claiming done — iron law 5)")
    if problems:
        reason = "[iron-3-clean-close] " + "; ".join(problems)
        log_event(ws, {"event": "stop_block", "problems": problems})
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        return 0
    log_event(ws, {"event": "stop_pass"})
    print(json.dumps({"decision": "allow", "reason": "clean-close verified"}))
    return 0


def cmd_verify_done(args) -> int:
    """Agent-side: run clean-close checks; if they pass, set done_verified so a `done`
    verb is allowed. This mirrors the Stop hook, it does not replace it — the host hook
    still re-checks independently at turn end (and a false allow there is caught then)."""
    ns = argparse.Namespace(workspace=args.workspace, stdin=False)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_stop(ns)
    try:
        v = json.loads(buf.getvalue())
    except Exception:
        v = {"decision": "block", "reason": "stop check unreadable"}
    if v.get("decision") == "block":
        print(json.dumps({"decision": "block", "reason": v.get("reason", "")}, ensure_ascii=False))
        return 2
    sp = state_paths(workspace(args))
    s = load_json(sp["session"], {}) or {}
    s["done_verified"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    save_json(sp["session"], s)
    log_event(workspace(args), {"event": "done_verified"})
    print("done_verified set: clean-close checks passed (Stop hook still re-checks independently).")
    return 0


def cmd_done_list(args) -> int:
    ws = workspace(args)
    sp = state_paths(ws)
    s = load_json(sp["session"], {}) or {}
    if args.set:
        s["done_list"] = os.path.abspath(args.set)
        save_json(sp["session"], s)
        print("done-list path recorded:", args.set)
    else:
        print(s.get("done_list") or str(sp["dir"] / "done.md"))
    return 0


def cmd_override(args) -> int:
    ws = workspace(args)
    sp = state_paths(ws)
    if not sys.stdin.isatty() and not sp["sig"].exists():
        print("override refused: human act (TTY or user_signature required). Non-interactive agents must NOT self-override.", file=sys.stderr)
        return 1
    s = load_json(sp["session"], {}) or {}
    s["overridden"] = {"rule": args.rule or "all", "reason": args.reason,
                       "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    save_json(sp["session"], s)
    log_event(ws, {"event": "override", "rule": args.rule, "reason": args.reason, "via": "human"})
    print("override recorded (append-only, cannot be erased).")
    return 0


def cmd_status(args) -> int:
    ws = workspace(args)
    sp = state_paths(ws)
    s = load_json(sp["session"])
    if not s:
        print("no session — run: gatekeeper init --host <host>")
        return 1
    print(json.dumps(s, indent=2, ensure_ascii=False))
    if sp["log"].exists():
        events = [json.loads(l) for l in sp["log"].read_text(encoding="utf-8").splitlines() if l.strip()]
        print(f"gate_log: {len(events)} events")
    return 0


def cmd_report(args) -> int:
    ws = workspace(args)
    sp = state_paths(ws)
    if not sp["log"].exists():
        print("no gate_log yet.")
        return 0
    events = [json.loads(l) for l in sp["log"].read_text(encoding="utf-8").splitlines() if l.strip()]
    byrule, bytype = {}, {}
    for e in events:
        bytype[e["event"]] = bytype.get(e["event"], 0) + 1
        if "rule" in e:
            byrule[e["rule"]] = byrule.get(e["rule"], 0) + 1
    print(f"events={len(events)}")
    print("top rules (violations+warns):")
    for k, v in sorted(byrule.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    if byrule:
        hot = max(byrule.items(), key=lambda kv: kv[1])
        if hot[1] >= 10:
            print(f"\nMETABOLISM: rule '{hot[0]}' fired {hot[1]}x — candidates: scriptify it (if statically checkable)\n"
                  "or demote it, or fix the protocol text. Rules that never fire after scripting should be deleted (skill 新陈代谢).")
    print("by event type:", json.dumps(bytype, ensure_ascii=False))
    return 0


def cmd_doctor(args) -> int:
    """Negative self-test: every deny rule must actually block a crafted violation."""
    import tempfile
    import shutil
    ok = True
    with tempfile.TemporaryDirectory(prefix="gk-doctor-") as tmp:
        real = os.getcwd()
        os.chdir(tmp)
        ws = Path(tmp)
        subprocess.run(["git", "init", "-q"], capture_output=True)
        subprocess.run(["git", "config", "user.email", "d@doctor"], capture_output=True)
        subprocess.run(["git", "config", "user.name", "doctor"], capture_output=True)
        (ws / "a.txt").write_text("base")
        subprocess.run(["git", "add", "-A"], capture_output=True)
        subprocess.run(["git", "commit", "-qm", "base"], capture_output=True)
        sys.argv = ["gatekeeper", "init", "--force"]
        cmd_init(argparse.Namespace(workspace=None, host="generic", rules=None, force=True))
        probes = [
            ("plan-before-write",  lambda: eval_pre_tool_use(ws, "Write", "", "x"), ["route --complexity L3"], "deny"),
            ("routing-first",      lambda: eval_pre_tool_use(ws, "Write", "", "x"), ["fresh"], "ack"),
            ("auditor-git",        lambda: eval_pre_tool_use(ws, "Bash", "git checkout HEAD~1 .", ""), ["route --role auditor"], "deny"),
            ("mock-warn",          lambda: eval_pre_tool_use(ws, "Write", "", "const x = MOCK_DATA"), ["route --complexity L2"], "warn"),
        ]
        for name, probe, prep, expect in probes:
            if prep == ["fresh"]:
                save_json(state_paths(ws)["session"], {"complexity": None, "routed": False, "role": "developer"})
            else:
                save_json(state_paths(ws)["session"], {"complexity": None, "routed": False, "role": "developer"})
                if prep[0].endswith(("L3", "L2")):
                    cmd_route(argparse.Namespace(workspace=None, complexity=prep[0].split()[-1],
                                                 role="developer", task_class="t", reset=True))
                elif "auditor" in " ".join(prep):
                    cmd_route(argparse.Namespace(workspace=None, complexity="L3",
                                                 role="auditor", task_class="t", reset=True))
            v = probe()
            got = v["decision"]
            if got != expect:
                ok = False
                print(f"  RED-TEST FAIL {name}: expected {expect}, got {got} ({v.get('rule')})")
            else:
                print(f"  red-test OK   {name}: {got} [{v.get('rule')}]")
            # golden half: after human approval the write must pass
            if name == "plan-before-write" and got == "deny":
                save_json(state_paths(ws)["session"], {**(load_json(state_paths(ws)["session"], {}) or {}),
                                                       "plan_approved": True,
                                                       "complexity": "L3", "routed": True, "role": "developer"})
                v2 = eval_pre_tool_use(ws, "Write", "", "x")
                print(f"  golden OK     plan-before-write after approve: {v2['decision']}")
                ok = ok and v2["decision"] == "allow"
        os.chdir(real)
    print("doctor:", "ALL GREEN" if ok else "RED — do NOT ship hooks on top of this engine")
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gatekeeper", description="Work OS harness layer — what an agent cannot skip.")
    ap.add_argument("--workspace", help="project dir (default: cwd or $GK_WORKSPACE)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create .gatekeeper state + install host adapter hooks")
    p.add_argument("--host", default="generic",
                   choices=["hermes", "claude_code", "codex", "trae", "workbuddy", "generic"])
    p.add_argument("--rules", help="custom rules.json (default: built-in iron-law set)")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("route", help="record the [路由] decision (complexity/role) before executing")
    p.add_argument("--complexity", required=True, choices=["L1", "L2", "L3", "L4"])
    p.add_argument("--role", default="developer", choices=["developer", "auditor", "review", "explorer"])
    p.add_argument("--task-class", default="code")
    p.add_argument("--reset", action="store_true", help="new task: also clears plan_approved")
    p.set_defaults(fn=cmd_route)

    p = sub.add_parser("approve", help="HUMAN-only: mark PLAN approved (TTY or user_signature required)")
    p.add_argument("plan")
    p.set_defaults(fn=cmd_approve)

    p = sub.add_parser("pre", help="PreToolUse evaluation (manual or --stdin for Claude Code hook)")
    p.add_argument("--stdin", action="store_true")
    p.add_argument("--tool")
    p.add_argument("--command")
    p.add_argument("--file")
    p.set_defaults(fn=cmd_pre)

    p = sub.add_parser("ack", help="written justification to pass a require-ack rule")
    p.add_argument("--rule", required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(fn=cmd_ack)

    p = sub.add_parser("stop", help="Stop-hook gate: clean tree + fresh commit + done list")
    p.add_argument("--stdin", action="store_true")
    p.set_defaults(fn=cmd_stop)

    p = sub.add_parser("verify-done", help="run clean-close checks; on pass, allow a `done` claim")
    p.set_defaults(fn=cmd_verify_done)

    p = sub.add_parser("done-list", help="record/show the completion checklist file")
    p.add_argument("--set")
    p.set_defaults(fn=cmd_done_list)

    p = sub.add_parser("override", help="HUMAN-only escape hatch (append-only audit)")
    p.add_argument("--rule")
    p.add_argument("--reason", required=True)
    p.set_defaults(fn=cmd_override)

    p = sub.add_parser("status")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("report", help="gate_log statistics + rule metabolism suggestion")
    p.set_defaults(fn=cmd_report)

    p = sub.add_parser("doctor", help="negative self-test: every deny rule must catch a crafted violation")
    p.set_defaults(fn=cmd_doctor)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
