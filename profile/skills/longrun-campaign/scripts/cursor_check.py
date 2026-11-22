#!/usr/bin/env python3
"""cursor_check.py — 断点恢复游标一致性机检【V3.2·C9】。

机器不变量（违反任一即 BLOCK，禁止续跑/重做）：
  I1  gate_log.jsonl 末行 name == mission.json.cursor.last_gate（末次记录已入游标）
  I2  gate_log 末行 exit != 0 时 cursor.state 必须是 blocked（FAIL 未标卡即错乱）
  I3  cursor.sprint 不在 sprint_history 的 PASS 集合内（游标不许停在已完成 Sprint）
  I4  next_action 非空
  I5  STATUS.md 把已 PASS 的 Sprint 标为"未开始/待做" = 人读态落后机器态
exit 0=游标自洽可续跑；exit 1=错乱，先修游标再动手。"""
import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign-dir", required=True)
    a = ap.parse_args()
    d = Path(a.campaign_dir)
    m = json.loads((d / "mission.json").read_text())
    cur = m.get("cursor", {})
    hist = m.get("gates", {}).get("sprint_history", [])
    done = set(h.get("sprint") for h in hist if h.get("result") == "PASS")
    done.discard(None)
    problems = []

    lines = []
    gl = d / "gate_log.jsonl"
    if gl.exists():
        lines = [l for l in gl.read_text().splitlines() if l.strip()]

    if lines:
        last = json.loads(lines[-1])
        lg_name = last.get("name")
        cg_last = cur.get("last_gate")
        if lg_name != cg_last:
            problems.append("I1 gate_log 末行=%s 但 cursor.last_gate=%s（游标未随末次 Gate 更新）"
                            % (lg_name, cg_last))
        if last.get("exit", 0) != 0 and cur.get("state") != "blocked":
            problems.append("I2 末行 exit=%s 非 0 但 state=%s（FAIL 未标 blocked）"
                            % (last.get("exit"), cur.get("state")))
    else:
        problems.append("I0 gate_log.jsonl 缺失或为空")

    if cur.get("sprint") in done:
        problems.append("I3 游标停在已 PASS 的 Sprint %s——续跑会重做已完成工作"
                        % cur.get("sprint"))
    if not m.get("next_action"):
        problems.append("I4 next_action 为空——恢复后无从继续")
    # I6【V3.3】漏做方向：计划序列中游标之前的 Sprint 必须有 PASS 记录
    planned = m.get("planned_sprints") or []
    if planned and cur.get("sprint") in planned:
        pos = planned.index(cur.get("sprint"))
        skipped = [s for s in planned[:pos] if s not in done]
        if skipped:
            problems.append("I6 计划中位于游标前却无 PASS 记录: %s——疑似漏做跳过" % skipped)

    st = d / "STATUS.md"
    if st.exists():
        text = st.read_text(errors="ignore")
        for s in sorted(done):
            if s in text:
                seg = text.split(s, 1)[-1][:60]
                if ("未开始" in seg) or ("待做" in seg):
                    problems.append("I5 STATUS 把已 PASS 的 %s 标为未做（按裁规则以机器态为准，修 STATUS）" % s)

    print("CURSOR-CHECK phase=%s sprint=%s state=%s done=%s gate_log_lines=%d"
          % (cur.get("phase"), cur.get("sprint"), cur.get("state"),
             sorted(done), len(lines)))
    for p in problems:
        print("  x", p)
    if problems:
        print("RESULT: BLOCK——先修游标再动手")
        sys.exit(1)
    print("RESULT: PASS——游标自洽，按 next_action 续跑")


if __name__ == "__main__":
    main()
