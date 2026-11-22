#!/usr/bin/env python3
"""scope_check.py — 长程战役 V3.1 范围漂移 + 历史改写确定性检查。

用法:
  python3 scope_check.py --workspace <repo> [--base main] [--allow 'src/export/**' 'tests/**'] \
      [--high-risk 'src/storage/**'] [--do-not-edit 'vendor/**'] [--check-history] \
      [--reflog-limit 15] [--allow-tags v1.0 v1.1]

行为:
  1) 采集 git 改动文件集合（工作区未提交 + 相对 base 已提交），与 --allow glob 做集合差，
     输出 [超出允许范围]/[高风险目录]/[禁改目录] 三组。
  2) 【V3.1·C7】--check-history 启用两组机检：
     - [历史改写]: 近 --reflog-limit 条 HEAD reflog 匹配 reset/rebase/amend/forced-update；
     - [孤儿tag]:  指向提交不被任何本地/远程分支包含的 tag（reset --soft 折叠提交后
       发布 tag 变孤儿 = 本机真实事故型），--allow-tags 白名单除外。
  任何 [超出允许范围]/[禁改目录]/[历史改写]/[孤儿tag] 非空 → RESULT: BLOCK, exit 1（Gate 2 阻塞信号）。
  只读脚本：不写文件、不改 git 状态。仅标准库，Python 3.10+。
"""
import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path


def git(ws, *args):
    """致命查询：失败即退出（用于必需的前置查询）。"""
    r = subprocess.run(["git", "-C", str(ws), *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def git_safe(ws, *args):
    """探测性查询：失败返回空串，不整脚本退出。"""
    r = subprocess.run(["git", "-C", str(ws), *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def changed_files(ws, base):
    files = set()
    out = git(ws, "status", "--porcelain=v1", "-uall")
    for line in out.splitlines():
        if len(line) > 3:
            files.add(line[3:].split(" -> ")[-1].strip('"'))
    if base:
        out = git_safe(ws, "diff", "--name-only", f"{base}...HEAD")
        files.update(l for l in out.splitlines() if l)
    return sorted(files)


def matches(path, globs):
    return any(fnmatch.fnmatch(path, g) or path.startswith(g.rstrip("/*") + "/")
               for g in globs)


def history_rewrites(ws, limit):
    # 【V3.3】加入 checkout: ——分支切换类 reflog 也属执行器禁动操作
    # 注: `git checkout -- <file>`（冲工作区）不写 HEAD reflog，由 --require-clean + 回归兜底
    out = git_safe(ws, "reflog", "HEAD", "--format=%gd %gs", f"--max-count={limit}")
    pat = re.compile(r"reset:|rebase|amend|checkout:|update by push.*forced|forced-update", re.I)
    return [line.strip() for line in out.splitlines() if pat.search(line)]


def workdir_dirty(ws):
    """【V3.3】派单前置机检素材：主工作区未提交改动清单。"""
    out = git(ws, "status", "--porcelain=v1", "-uall")
    return sorted(set(l[3:].split(" -> ")[-1].strip('"')
                      for l in out.splitlines() if len(l) > 3))


def orphan_tags(ws, exclude):
    tags = [t for t in git_safe(ws, "tag", "--list").splitlines() if t.strip()]
    branches = git_safe(ws, "for-each-ref", "--format=%(refname)",
                        "refs/heads", "refs/remotes").split()
    orphans = []
    for t in tags:
        if t in exclude:
            continue
        sha = git_safe(ws, "rev-parse", "--verify", f"{t}^{{commit}}").strip()
        if not sha:
            orphans.append(f"{t} 标签对象损坏（无法解析 commit）")
            continue
        reachable = any(
            subprocess.run(["git", "-C", str(ws), "merge-base", "--is-ancestor",
                            sha, b], capture_output=True).returncode == 0
            for b in branches)
        if not reachable:
            orphans.append(f"{t} -> {sha[:8]} 不被任何本地/远程分支包含（疑似孤儿/被折叠）")
    return orphans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--base", default=None)
    ap.add_argument("--allow", nargs="*", default=None,
                    help="契约允许路径 glob；不传则只报 high-risk/do-not-edit")
    ap.add_argument("--high-risk", nargs="*", default=[])
    ap.add_argument("--do-not-edit", nargs="*", default=[])
    ap.add_argument("--check-history", action="store_true",
                    help="检测 reflog 历史改写 + 孤儿 tag（V3.1）")
    ap.add_argument("--require-clean", action="store_true",
                    help="派单前置：主工作区有未提交改动即 BLOCK（V3.3·C1）")
    ap.add_argument("--reflog-limit", type=int, default=15)
    ap.add_argument("--allow-tags", nargs="*", default=[])
    a = ap.parse_args()
    ws = Path(a.workspace)
    dirty = workdir_dirty(ws)
    if a.require_clean and dirty:
        print(f"SCOPE-CHECK workspace={ws} --require-clean")
        for f in dirty:
            print(f"  - {f}  <- 派单前工作区不干净：先 commit 当期成果再派单（V3.3·C1 机检）")
        print("RESULT: BLOCK")
        sys.exit(1)
    files = changed_files(ws, a.base)

    outside = [f for f in files if a.allow and not matches(f, a.allow)]
    high = [f for f in files if matches(f, a.high_risk)]
    banned = [f for f in files if matches(f, a.do_not_edit)]
    hist = history_rewrites(ws, a.reflog_limit) if a.check_history else []
    orph = orphan_tags(ws, set(a.allow_tags)) if a.check_history else []

    print(f"SCOPE-CHECK workspace={ws} base={a.base or '(工作区)'} total_changed={len(files)}")
    blocked = False
    for label, group, action in (
        ("超出允许范围", outside, "逐条确认: 必要改动需说明，顺手发散=阻塞"),
        ("高风险目录", high, "必须走独立干净上下文深审 (Gate 2 独立档)"),
        ("禁改目录", banned, "阻塞，除非契约明示允许"),
        ("历史改写", hist, "阻塞并触发中断上报条件4（不可逆/历史改写），核对 reflog"),
        ("孤儿tag", orph, "阻塞：tag 指向提交不在任何分支上，先查是否被 reset/rebase 折叠"),
    ):
        print(f"[{label}] {len(group)}")
        for f in group:
            print(f"  - {f}  <- {action}")
    if outside or banned or hist or orph:
        blocked = True
    if blocked:
        print("RESULT: BLOCK")
        sys.exit(1)
    if high:
        print("RESULT: NEEDS_DEEP_REVIEW")
        sys.exit(0)
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
