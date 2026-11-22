#!/usr/bin/env python3
"""value_check.py — 取值纪律机检【V3.4·C6】：把"禁手抄显示值"从文字叮嘱下沉为静态检查。

判据（AST+正则，Python stdlib）:
  V1 敏感常量硬编码: 测试/脚本源码里出现 key/token/secret/api_key= <长度>=16 的字面量
     → 应改为从代码模块 import 常量或直调取值函数；
  V2 观测值转录: 字面量含 '…'/'...'(U+2026/省略号) 或 '***'(打码形态) 出现在赋值右侧
     → 手抄打码值的直接指纹，必须程序化取原始值；
  V3 目测比对: assert 左右一侧为裸字符串字面量且另一侧来自存储读取(localStorage/sessionStorage/getItem)
     → 提示改 import 常量。
用法: value_check.py --path <文件或目录>
【V3.4.2】修 Runner 实测两处不符：删 docstring 不存在的 --patterns 声称；V3 目测比对对 JS/TS 用正则判据（Python 走 AST，JS 无 ast 模块）。
"""
import argparse
import ast
import re
import sys
from pathlib import Path

SENS = re.compile(r"(?i)(api[_-]?key|token|secret|password|storage[_-]?key)\s*=\s*['\"]([^'\"]{16,})['\"]")
MASKED = re.compile(r"['\"][^'\"]*(…|\*{3}|\\u2026)[^'\"]*['\"]")
STORAGE_READ = re.compile(r"(localStorage|sessionStorage)\s*\.\s*getItem|getStorageKey|storage\.get")
def js_v3_findings(src, p):
    """两趟行级判据：先收集 'var X = ...getItem(...)' 的变量名，再找 X === '字面量' 比较。"""
    hits = []
    store_vars = set()
    for i, line in enumerate(src.splitlines(), 1):
        m = re.search(r"(?:var|let|const)?\s*(\w+)\s*=\s*(?:localStorage|sessionStorage)\s*\.\s*getItem\(", line)
        if m:
            store_vars.add(m.group(1))
        if re.search(r"(?:localStorage|sessionStorage)\s*\.\s*getItem\([^)]*\)\s*(?:===?|!==?)\s*['\"]", line):
            hits.append(f"{p}:{i} V3 目测比对(JS): getItem 结果与字面量直接比较，改 import 常量")
        for v in store_vars:
            if re.search(rf"\b{v}\s*(?:===?|!==?)\s*['\"]", line) or re.search(rf"['\"][^'\"]+['\"]\s*(?:===?|!==?)\s*{v}\b", line):
                hits.append(f"{p}:{i} V3 目测比对(JS): 存储值变量 {v} 与裸字面量比较，字面量改 import 常量")
    return hits


def check_file(p: Path):
    src = p.read_text(errors="ignore")
    hits = []
    for m in SENS.finditer(src):
        ln = src[:m.start()].count("\n") + 1
        hits.append(f"{p}:{ln} V1 敏感值硬编码(手抄指纹): 改从代码模块 import 常量或直调取值函数")
    for m in MASKED.finditer(src):
        seg = src[max(0, m.start()-40):m.start()]
        if "=" in seg:
            ln = src[:m.start()].count("\n") + 1
            hits.append(f"{p}:{ln} V2 打码/省略号形态值被写入代码: U+2026 可能是真实内容，须程序化 grep 原始文件取值")
    if p.suffix in (".js", ".ts", ".jsx", ".tsx"):
        hits += js_v3_findings(src, p)
        return hits
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return hits
    for n in ast.walk(tree):
        if isinstance(n, ast.Assert):
            code = ast.unparse(n)
            if STORAGE_READ.search(code) and re.search(r"['\"]\w+['\"]", code):
                hits.append(f"{p}:{n.lineno} V3 目测比对: 存储读取值与裸字面量断言，字面量改 import 常量")
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    a = ap.parse_args()
    root = Path(a.path)
    files = [root] if root.is_file() else sorted(root.rglob("*.py")) + sorted(root.rglob("*.js")) + sorted(root.rglob("*.ts"))
    allh = []
    for f in files:
        allh += check_file(f)
    for h in allh:
        print("  x", h)
    print(f"VALUE-CHECK files={len(files)} findings={len(allh)}")
    sys.exit(1 if allh else 0)


if __name__ == "__main__":
    main()
