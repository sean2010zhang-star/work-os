#!/usr/bin/env python3
"""
模式执行日志 — 记录每次模式选择和执行结果
用法: 
  from mode_logger import log_mode, recommend_mode
  
  # 记录模式执行
  log_mode("M10", "构建多引擎系统", success=True, elapsed_s=300)
  
  # 获取推荐模式
  mode = recommend_mode("构建完整产品")
"""
import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path.home() / ".hermes/data/mode_log.json"

def _load():
    try:
        return json.loads(LOG_FILE.read_text())
    except:
        return {"version": "1.0", "entries": []}

def _save(data):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def log_mode(mode: str, task_desc: str, skills_loaded: list = None, 
             success: bool = True, elapsed_s: int = 0, notes: str = ""):
    """记录一次模式执行"""
    data = _load()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "task": task_desc[:100],
        "skills": skills_loaded or [],
        "success": success,
        "elapsed_s": elapsed_s,
        "notes": notes[:200],
    }
    data["entries"].append(entry)
    # 保留最近500条
    if len(data["entries"]) > 500:
        data["entries"] = data["entries"][-500:]
    _save(data)
    return entry

def get_stats():
    """获取模式使用统计"""
    data = _load()
    entries = data.get("entries", [])
    if not entries:
        return {"total": 0, "modes": {}}
    
    modes = {}
    for e in entries:
        m = e["mode"]
        if m not in modes:
            modes[m] = {"count": 0, "success": 0, "fail": 0, "avg_elapsed": 0}
        modes[m]["count"] += 1
        if e.get("success"):
            modes[m]["success"] += 1
        else:
            modes[m]["fail"] += 1
    
    # 计算成功率
    for m in modes:
        total = modes[m]["count"]
        modes[m]["success_rate"] = round(modes[m]["success"] / total * 100, 1) if total > 0 else 0
    
    return {"total": len(entries), "modes": modes}

def recommend_mode(task_keywords: str) -> str:
    """基于历史数据推荐模式(简单关键词匹配)"""
    data = _load()
    entries = data.get("entries", [])
    
    # 找历史上类似任务的成功模式
    keyword_list = task_keywords.lower().split()
    candidates = {}
    for e in entries:
        if not e.get("success"):
            continue
        task_lower = e.get("task", "").lower()
        matches = sum(1 for kw in keyword_list if kw in task_lower)
        if matches > 0:
            m = e["mode"]
            candidates[m] = candidates.get(m, 0) + matches
    
    if candidates:
        best = max(candidates, key=candidates.get)
        return best
    return "M7"  # 默认方案模式
