#!/usr/bin/env python3
"""
Sprint Gate验证模板 — 可复用的Sprint审计脚本
适配 FastAPI + Next.js 双服务器架构

用法: 复制此文件，修改 PROJECT_DIR 和 CHECK_ITEMS
"""
import json
import urllib.request
import os

PROJECT_DIR = os.path.expanduser("~/Desktop/engine-app")
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3002"

# ─── Gate 1: Pre-flight (文件存在性) ───
GATE1_FILES = [
    # (path_relative_to_project, description)
    # ("backend/engines/xxx.py", "XXX引擎"),
    # ("src/components/xxx.tsx", "XXX组件"),
]

# ─── Gate 2: API端点验证 ───
GATE2_ENDPOINTS = [
    # (method, path, body_json_or_none, description)
    # ("GET", "/api/health", None, "健康检查"),
    # ("POST", "/api/score", '{"objective":{}}', "评分"),
]

def check_gate1():
    """文件存在性检查"""
    print("\n[Gate 1: Pre-flight]")
    all_pass = True
    for rel_path, desc in GATE1_FILES:
        full = os.path.join(PROJECT_DIR, rel_path)
        exists = os.path.isfile(full)
        size = os.path.getsize(full) if exists else 0
        status = "PASS" if exists and size > 0 else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {desc}: {rel_path} ({size} bytes)")
    return all_pass

def check_gate2():
    """API端点验证"""
    print("\n[Gate 2: API Endpoints]")
    all_pass = True
    for method, path, body, desc in GATE2_ENDPOINTS:
        try:
            url = f"{BACKEND_URL}{path}"
            if method == "GET":
                resp = urllib.request.urlopen(url, timeout=10)
            else:
                data = body.encode() if body else b"{}"
                req = urllib.request.Request(url, data=data, method="POST",
                    headers={"Content-Type": "application/json"})
                resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read())
            ok = "success" in result or "status" in result or "detail" in result
            status = "PASS" if ok else "FAIL"
            if not ok:
                all_pass = False
        except Exception as e:
            status = "FAIL"
            all_pass = False
        print(f"  [{status}] {method} {path} ({desc})")
    return all_pass

def check_gate3(expected_engines=None):
    """引擎完整性检查"""
    print("\n[Gate 3: Engine Completeness]")
    try:
        resp = urllib.request.urlopen(f"{BACKEND_URL}/api/health", timeout=10)
        data = json.loads(resp.read())
        engines = [e["name"] for e in data.get("engines", [])]
        print(f"  Registered: {len(engines)} engines")
        if expected_engines:
            missing = [n for n in expected_engines if n not in engines]
            if missing:
                print(f"  [FAIL] Missing: {missing}")
                return False
            print(f"  [PASS] All {len(expected_engines)} engines registered")
        return True
    except Exception as e:
        print(f"  [FAIL] Health check failed: {e}")
        return False

def check_gate4():
    """前端构建检查"""
    print("\n[Gate 4: Frontend Build]")
    import subprocess
    try:
        result = subprocess.run(
            ["npx", "next", "build"],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120
        )
        ok = result.returncode == 0 and "Generating static pages" in result.stdout
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] Next.js build")
        if not ok:
            print(f"  Error: {result.stderr[:200]}")
        return ok
    except Exception as e:
        print(f"  [FAIL] Build failed: {e}")
        return False

def run_audit(sprint_name="Sprint N", expected_engines=None):
    """运行完整审计"""
    print(f"{'=' * 60}")
    print(f"  {sprint_name} DELIVERY AUDIT REPORT")
    print(f"{'=' * 60}")

    g1 = check_gate1()
    g2 = check_gate2()
    g3 = check_gate3(expected_engines)
    g4 = check_gate4()

    all_pass = g1 and g2 and g3 and g4
    print(f"\n{'=' * 60}")
    print(f"  Gate 1 Pre-flight: {'PASS' if g1 else 'FAIL'}")
    print(f"  Gate 2 API:        {'PASS' if g2 else 'FAIL'}")
    print(f"  Gate 3 Engines:    {'PASS' if g3 else 'FAIL'}")
    print(f"  Gate 4 Build:      {'PASS' if g4 else 'FAIL'}")
    print(f"  {'=' * 50}")
    print(f"  CONCLUSION: {'PASS ✅' if all_pass else 'FAIL ❌'}")
    print(f"{'=' * 60}")
    return all_pass

if __name__ == "__main__":
    # 示例: 自定义后运行
    run_audit("Sprint 1", expected_engines=["document_parser"])
