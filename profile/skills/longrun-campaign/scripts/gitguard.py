#!/usr/bin/env python3
"""gitguard.py — git 命令只读白名单闸【V3.4·C1/C7】：把"agent 禁 git 写操作"从文字禁令升级为技术拦截。

用法（子 Agent 派发契约第 5 要素改为强制经由本闸执行 git）:
  gitguard.py --workspace <repo> -- git log --oneline -5      # PASS-THROUGH（白名单内，执行并透传退出码）
  gitguard.py --workspace <repo> -- git reset --soft HEAD~2   # DENIED（exit 2，拒绝执行）
白名单（只读动词）: status log diff show blame ls-files cat-file rev-parse merge-base
  for-each-ref rev-list describe
条件动词（仅只读形态）: reflog[裸/show/exists] tag[--list] branch[读旗标]
  stash[仅list] config[仅--get/--get-all] remote[-v/show/get-url] worktree[仅list]
  symbolic-ref[仅单参读形态]
其余一切动词与写形态（commit push reset checkout rebase merge config写 remote add
  symbolic-ref写 reflog expire tag创建 branch -D ...）= DENIED。
【V3.4.2】应 Runner 实测指出的白名单过宽问题而收紧。--audit 追加每次调用到 JSONL。"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

READONLY = {"status", "log", "diff", "show", "blame", "ls-files", "cat-file",
            "rev-parse", "merge-base", "for-each-ref", "rev-list",
            "describe", "worktree"}  # V3.4.2 收紧：config/remote/symbolic-ref/reflog 移入条件组
CONDITIONAL = {  # 动词本身可读，但带写旗标/写形态即拒
    "tag": {"--list", "-l", "-n"},
    "branch": {"--list", "-a", "-r", "--show-current", "-v", "-vv"},
    "stash": {"list"},
    "config": {"--get", "--get-all"},
    "remote": {"-v", "-vv", "--verbose", "show", "get-url"},
    "symbolic-ref": {"SHOW_ONE"},   # 仅允许 1 参数读形态
    "reflog": {"show", "exists"},   # expire/delete 拒
}


def decide(args):
    if not args:
        return "DENIED", "无 git 子命令"
    verb = args[0]
    rest = args[1:]
    if verb in READONLY:
        if verb == "worktree":
            if not rest or rest[0] == "list":
                return "ALLOW", "worktree list"
            return "DENIED", f"worktree {rest[0] if rest else ''} 为写操作"
        return "ALLOW", verb
    if verb in CONDITIONAL:
        allowed = CONDITIONAL[verb]
        if verb == "stash" and rest == ["list"]:
            return "ALLOW", "stash list"
        if verb == "symbolic-ref":
            return ("ALLOW", "symbolic-ref 读") if len(rest) == 1 and not rest[0].startswith("-") \
                else ("DENIED", f"symbolic-ref {rest} 为写 ref 操作")
        if verb == "reflog":
            return ("ALLOW", "reflog show") if (not rest or rest[0] in allowed) \
                else ("DENIED", f"reflog {rest[0]} 破坏性")
        if verb == "tag":
            if not rest or any(r in allowed for r in rest):
                return "ALLOW", "tag 只读"
            return "DENIED", f"tag 创建/删除 {rest}"
        if verb == "branch":
            if any(r.startswith(("-d", "-D", "-m", "-M", "-c", "-C")) for r in rest) \
               or (rest and not rest[0].startswith("-") and len(rest) >= 1 and rest[0] not in allowed):
                return "DENIED", f"branch 写 {rest}"
            return "ALLOW", "branch 只读"
        if any(r in allowed for r in rest):
            if verb == "remote" and rest and rest[0] in ("add", "set-url", "remove", "rename", "prune"):
                return "DENIED", f"remote {rest[0]} 为写操作"
            return "ALLOW", f"{verb} (read flags)"
        return "DENIED", f"{verb} 带非只读参数 {rest}"
    return "DENIED", f"{verb} 为写操作"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--audit", default=None, help="审计日志路径（JSONL）")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    args = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if args and args[0] == "git":
        args = args[1:]
    verdict, why = decide(args)
    if a.audit:
        with open(a.audit, "a") as f:
            f.write(json.dumps({"ts": int(time.time()), "verdict": verdict,
                                "args": " ".join(args), "why": why}, ensure_ascii=False) + "\n")
    if verdict == "DENIED":
        print(f"GITGUARD: DENIED —— {why}")
        print("写操作须由主 Agent 统一执行（派发契约第5要素技术化）。deny 已入审计。")
        sys.exit(2)
    print(f"GITGUARD: ALLOW —— {why}，透传执行")
    r = subprocess.run(["git", "-C", a.workspace, *args])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
