#!/usr/bin/env python3
"""backup_all.py — 多项目备份模板（配置驱动，无内置私有路径）。

用法:
  1. 复制本文件到你的环境
  2. 修改 PROJECTS / EXT_ROOT / CLOUD_ROOT 为你自己的值
  3. python3 backup_all.py [--dry-run]
"""
from pathlib import Path
import json, subprocess, sys, datetime as dt

HOME = Path.home()
# ── EDIT THESE for your environment ─────────────────────────────
PROJECTS = [  # (name, path)
    ("my-app", HOME / "projects" / "my-app"),
    # add yours...
]
EXCLUDES = {
    "default": "--exclude='node_modules' --exclude='.git' --exclude='__pycache__'",
    # per-project overrides here
}
ARCHIVE_NOTES = [  # (name, path, description, status)
    ("my-app", HOME / "projects" / "my-app", "my application", "active"),
]
EXT_ROOT = Path("/media/<external-drive>")  # adjust to your OS mount convention          # external drive mount
LOG = Path(__file__).parent / "data" / "backup_log.json"
# ───────────────────────────────────────────────────────────────

def rsync_backup(name, path, extra_exclude=""):
    if not path.exists():
        return f"SKIP {name}: {path} not found"
    stamp = dt.datetime.now().strftime("%Y%m%d")
    dest = EXT_ROOT / f"backup_{stamp}" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = f"rsync -rc --delete {EXCLUDES['default']} {extra_exclude} '{path}/' '{dest}/'"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return f"{'OK' if r.returncode == 0 else 'FAIL'} {name} -> {dest}"

def main():
    dry = "--dry-run" in sys.argv
    results = []
    for name, path, *_ in [(p[0], p[1]) for p in PROJECTS]:
        line = f"[dry] would rsync {path}" if dry else rsync_backup(name, path)
        results.append(line)
        print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log = json.loads(LOG.read_text()) if LOG.exists() else []
    log.append({"ts": dt.datetime.now().isoformat(), "dry_run": dry, "results": results})
    LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False))
    print(f"logged {len(results)} entries -> {LOG}")

if __name__ == "__main__":
    main()
