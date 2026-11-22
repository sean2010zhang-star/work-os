#!/usr/bin/env python3
"""heartbeat_check.py — 子 Agent 心跳/超时外部看门狗【V3.2·C10】。

主 Agent 自身可能卡死导致心跳无人读，故看门狗独立于战役进程运行（可挂 cron）。
  --scan <心跳文件目录>: 每个心跳文件末行含 ts；now-ts 超上限 → STALE 报告并 exit 1。
  心跳行格式（子 Agent 追加）: {"task":"p1s2-impl","ts":1763750000,"step":"gate1"}
用法:
  heartbeat_check.py --scan campaign/<id>/heartbeats --limit 1800 [--json]
"""
import argparse
import glob
import json
import os
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", required=True)
    ap.add_argument("--limit", type=int, default=1800, help="心跳最长静默秒数")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    now = time.time()
    stale, live, broken = [], 0, []
    for p in sorted(glob.glob(os.path.join(a.scan, "*.jsonl")) + glob.glob(os.path.join(a.scan, "*hb*"))) :
        try:
            lines = [l for l in open(p) if l.strip()]
        except OSError as e:
            broken.append(f"{p}: {e}")
            continue
        if not lines:
            broken.append(f"{p}: 空心跳")
            continue
        try:
            mt = os.path.getmtime(p)  # 【V3.3】fs 证据：写心跳必刷新 mtime，不可用 ts 字段伪造
            last = json.loads(lines[-1])
            ts = float(last.get("ts", 0))
        except (ValueError, TypeError, OSError):
            broken.append(f"{p}: 末行非 JSON（心跳格式坏）")
            continue
        name = os.path.basename(p)
        if not ts:
            broken.append(f"{name}: 末行缺 ts 字段")
            continue
        gap_ts = now - ts
        age_mt = now - mt
        if gap_ts < -60:
            broken.append(f"{name}: ts 在未来 {-int(gap_ts)}s（疑似时钟错/伪造）")
            continue
        if age_mt > a.limit or gap_ts > a.limit:
            stale.append({"file": name, "silent_fs_s": int(age_mt),
                          "silent_ts_s": int(gap_ts),
                          "last_step": last.get("step"), "task": last.get("task")})
        else:
            live += 1
    if a.json:
        print(json.dumps({"stale": stale, "live": live, "broken": broken}, ensure_ascii=False))
    else:
        for s in stale:
            print(f"  STALE {s['file']} fs静默{s['silent_fs_s']}s ts静默{s['silent_ts_s']}s 最后步={s['last_step']} task={s['task']}")
        for b in broken:
            print(f"  BROKEN {b}")
        print(f"HEARTBEAT-CHECK limit={a.limit}s live={live} stale={len(stale)} broken={len(broken)}")
        if stale or broken:
            print("RESULT: ALERT——超时任务需主 Agent/人工检查，卡点见最后步")
            sys.exit(1)
        print("RESULT: PASS")


if __name__ == "__main__":
    main()
