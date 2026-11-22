#!/usr/bin/env python3
"""gate_recorder.py — 门禁/快测执行记录器【V3.2·C2】。

解决管道尾码假绿：命令经 subprocess 直取退出码（无 shell 管道），结果结构化追加进 gate_log.jsonl。
--negative-selftest: 先用一个必然失败的探针走同一记录链，确认"红会被记成红"（采集链自检），
                     再执行真实命令。战役 Gate 0 的仓库级负向测试（故意红一条真实用例）
                     应通过本记录器执行，保证记录链本身可信。

用法:
  gate_recorder.py --workspace <repo> --gate-log <path> --name "gate3-p0s2" \
      [--base-ref tagX..tagY] --negative-selftest -- <命令...>
退出码 = 被测命令退出码（BLOCK≠0 语义保留）。"""
import argparse, json, subprocess, sys, time
from pathlib import Path

def record(gate_log, entry):
    with open(gate_log, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def run_cmd(cmd):
    r = subprocess.run(cmd, shell=False, capture_output=True, text=True)
    return r.returncode, (r.stdout[-2000:] + r.stderr[-2000:])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--gate-log", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--base-ref", default="")
    ap.add_argument("--negative-selftest", action="store_true")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    if not cmd:
        sys.exit("no command after --")
    Path(a.gate_log).parent.mkdir(parents=True, exist_ok=True)

    if a.negative_selftest:
        # 探针：必然失败，且不经 shell 管道 —— 记录链必须记成非零
        probe_rc, _ = run_cmd([sys.executable, "-c", "import sys; sys.exit(1)"])
        record(a.gate_log, {"name": a.name + ":negative-probe", "exit": probe_rc,
                            "ts": int(time.time())})
        if probe_rc == 0:
            print("GATE-REC: 记录链自检失败（失败探针未被记红）——先修记录器")
            sys.exit(2)
        print("GATE-REC: negative-probe 记红 OK（退出码传播链可信）")

    rc, tail = run_cmd(cmd)
    record(a.gate_log, {"name": a.name, "exit": rc, "cmd": " ".join(cmd),
                        "base_ref": a.base_ref, "ts": int(time.time())})
    print(f"GATE-REC {a.name}: exit={rc}")
    if rc != 0:
        print(tail)
        print("RESULT: GATE FAIL (真实退出码，非管道尾码)")
    sys.exit(rc)

if __name__ == "__main__":
    main()
