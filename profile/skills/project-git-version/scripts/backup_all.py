#!/usr/bin/env python3
"""
全量自动备份脚本 — 每日cron调度
4项备份: Git + 外存rsync + <vault> + session-log
cron job: backup_all.py (每日22:00)

注意事项:
- 外存rsync大目录可能超时，按需排除大文件夹
- 日志写入 ~/.hermes/data/backup_log.json
"""
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime

HOME = Path.home()
TODAY = datetime.now().strftime("%Y%m%d")
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
LOG = []

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    LOG.append(line)
    print(line, flush=True)

def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip()
    except Exception as e:
        return False, str(e)

def backup_git():
    log("═══ Git备份 ═══")
    projects = [
        ("engine-app", HOME / "Desktop/engine-app"),
        ("hermes-workspace", HOME / "Desktop/hermes-workspace"),
    ]
    for name, path in projects:
        if not path.exists():
            log(f"  {name}: 路径不存在，跳过")
            continue
        ok, out = run(f"cd '{path}' && git add -A && git diff --cached --quiet 2>/dev/null")
        if ok:
            log(f"  {name}: clean，无需commit")
        else:
            ok2, out2 = run(f"cd '{path}' && git commit -m 'auto-backup {TODAY}' 2>&1 | tail -1")
            log(f"  {name}: {out2}")

def backup_external():
    log("═══ 外存备份 ═══")
    ext = Path("<mount-point>/<external-drive>/")
    if not ext.exists():
        log("  ❌ 外存未挂载，跳过")
        return False
    dst = ext / f"backup_{TODAY}"
    dst.mkdir(parents=True, exist_ok=True)
    syncs = [
        ("engine-app", HOME / "Desktop/engine-app", "--exclude='.next' --exclude='node_modules' --exclude='.git'"),
        ("hermes-workspace", HOME / "Desktop/hermes-workspace", "--exclude='__pycache__' --exclude='.git'"),
        ("需求管理应用", HOME / "Desktop/需求管理应用", "--exclude='node_modules' --exclude='.next' --exclude='.git' --exclude='__pycache__'"),
        ("bscea-fpa-tool", HOME / "projects/bscea-fpa-tool", "--exclude='__pycache__' --exclude='.git' --exclude='node_modules'"),
    ]
    for name, src, excludes in syncs:
        if not src.exists():
            log(f"  {name}: 源不存在，跳过")
            continue
        ok, _ = run(f"rsync -a {excludes} '{src}/' '{dst}/{name}/'", timeout=300)
        log(f"  {name}: {'OK' if ok else 'FAILED'}")
    return True

def backup_vault():
    log("═══ <vault>备份 ═══")
    wiki = HOME / "Desktop/<vault>/wiki/projects"
    wiki.mkdir(parents=True, exist_ok=True)
    projects_info = [
        ("engine-app", HOME / "Desktop/engine-app", "多引擎系统v2", "设计中"),
        ("hermes-workspace", HOME / "Desktop/hermes-workspace", "Hermes Workspace", "运行中"),
    ]
    for name, path, display_name, status in projects_info:
        if not path.exists():
            continue
        ok, last_commit = run(f"cd '{path}' && git log --oneline -1 2>/dev/null")
        ok2, changes = run(f"cd '{path}' && git status --short 2>/dev/null | wc -l")
        clean = changes.strip() == "0"
        content = f"# {display_name}\n\n> 自动更新: {NOW}\n\n## 基本信息\n- 路径: {path}/\n- 状态: {status}\n- Git: {'clean' if clean else f'{changes.strip()} uncommitted'}\n- 最新commit: {last_commit if ok else 'N/A'}\n"
        (wiki / f"{name}.md").write_text(content)
        log(f"  {name}.md: OK")

def backup_opc_doc():
    log("═══ session-log备份 ═══")
    opc = HOME / "Desktop/session-log"
    opc.mkdir(parents=True, exist_ok=True)
    session_file = opc / f"session_{TODAY}_auto-backup.md"
    content = f"# {TODAY} 自动备份检查\n\n> {NOW}\n\n备份项: Git + 外存 + <vault> + session-log\n"
    session_file.write_text(content)
    log(f"  {session_file.name}: OK")


if __name__ == "__main__":
    log(f"全量备份开始 — {NOW}")
    backup_git()
    backup_external()
    backup_vault()
    backup_opc_doc()
    log_file = HOME / ".hermes/data/backup_log.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        logs = json.loads(log_file.read_text()) if log_file.exists() else []
    except:
        logs = []
    logs.append({"date": TODAY, "time": NOW, "lines": len(LOG), "success": True})
    if len(logs) > 90:
        logs = logs[-90:]
    log_file.write_text(json.dumps(logs, ensure_ascii=False, indent=2))
    log(f"全量备份完成 — {len(LOG)}项操作")
