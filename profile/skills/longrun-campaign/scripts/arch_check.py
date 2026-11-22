#!/usr/bin/env python3
"""arch_check.py — 结构主张机检（解耦/单独订阅型约束的证据不再是口供）【V3.2·C8】。

用法:
  arch_check.py --workspace <repo> --isolate 'src/huangli/**' 'src/zejiri/**' 'src/ziwei/**' \
      [--via 'src/core/interfaces.py'] [--ext lib]
判据: 每个 isolate 模块的文件 import 其他 isolate 模块 = 违规（模块间只许经 --via 接口层通信，
  不写 --via 则任何跨 isolate import 全违规）。AST 解析 import，路径映射到模块目录。
exit 1 = 主张被稀释（存在违规 import），该 §6 checklist 条目证据不足。"""
import argparse
import ast
import fnmatch
import sys
from pathlib import Path


def module_of(path, patterns):
    for i, pat in enumerate(patterns):
        base = pat.rstrip("/*")
        if str(path).startswith(base + "/"):
            return i
    return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--isolate", nargs="+", required=True)
    ap.add_argument("--via", default=None)
    ap.add_argument("--ext", default="py")
    a = ap.parse_args()
    ws = Path(a.workspace)
    pats = [p for p in a.isolate]
    via_mod = None
    if a.via:
        via_mod = module_of(Path(a.via), pats)
    violations = []
    for pat in pats:
        base = ws / pat.rstrip("/*")
        if not base.exists():
            violations.append(f"{pat}: 目录不存在（约定 glob 与真实目录脱节）")
            continue
        for f in base.rglob(f"*.{a.ext}"):
            try:
                tree = ast.parse(f.read_text(errors="ignore"))
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                mods = []
                if isinstance(n, ast.Import):
                    mods = [al.name for al in n.names]
                elif isinstance(n, ast.ImportFrom):
                    mods = [n.module or ""]
                    # 【V3.4.2】相对 import 不再静默豁免：按文件位置解析成路径后同样比对 isolate 集
                    if n.level:
                        resolved = []
                        for m0 in mods:
                            d = f.parent  # 文件所在目录
                            for _ in range(n.level - 1):
                                d = d.parent
                            resolved.append(str((d / m0.replace(".", "/"))
                                                .relative_to(ws)) if m0 else "")
                        mods = [r for r in resolved if r]
                for m in mods:
                    mpath = m.replace(".", "/")
                    for j, p2 in enumerate(pats):
                        if j == pats.index(pat):
                            continue
                        base2 = p2.rstrip("/*")
                        if mpath.startswith(base2) or str(ws / mpath).startswith(str(ws / base2)):
                            # 【V3.3 语义明确】跨 isolate 直引一律违规；--via 是接口层（自身不在
                            # isolate glob 内），经它的 import 天然不在此报——违规信息里指出应走的接口层
                            violations.append(
                                f"{f.relative_to(ws)}:{getattr(n,'lineno',0)} import '{m}' "
                                f"直入另一 isolate 模块 {base2}"
                                + ("" if not a.via else f"（应改经接口层 {a.via}）"))
    for v in violations:
        print("  x", v)
    print(f"ARCH-CHECK isolate={len(pats)} violations={len(violations)}")
    if violations:
        print("RESULT: FAIL——解耦主张被稀释，§6 对应约束证据不成立")
        sys.exit(1)
    print("RESULT: PASS——模块边界干净")


if __name__ == "__main__":
    main()
