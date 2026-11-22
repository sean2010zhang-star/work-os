#!/usr/bin/env python3
"""fixture_check.py — 夹具真实性 + 测试卫生机检【V3.2·C3】。

对目标测试文件/目录跑静态判据（AST，不执行代码）：
  F1 手造夹具: 测试里 dict/JSON 字面量声称是"引擎/接口返回形状"（函数名/变量含 fixture/payload/response/shape）
     且仓库存在 dump 产物目录时，逐个报出请核对是否来自实跑 dump；
  F2 mock 自证: 测试函数体只有 mock 断言（assert_called*）而无结果断言（assertEqual/==/assertTrue on 返回值）；
  F3 拖慢/副作用: time.sleep(秒数>1)、读写 user home 路径、requests.*/真实网络调用出现在"快测层"文件；
  F4 从未红过（动态）: 配合 --with-run 时对每个新增测试执行一次"注入失败探针"不现实，改为要求
     回归测试文件名含 re-<bugid> 且 fixtures/ 有对应真实 dump 文件（命名契约机检）。
exit 1 = 存在 Must Fix 命中。"""
import argparse, ast, re, sys
from pathlib import Path

SLEEP_MAX = 1.0
NET_PAT = re.compile(r"\b(requests\.|httpx\.|urllib\.request|fetch\(|socket\.)")
HOME_PAT = re.compile(r"(os\.path\.expanduser|Path\.home|~/)")

def f2_mock_only(fn):
    has_result_assert = False
    has_mock_assert = False
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr.startswith("assert"):
                if "called" in n.func.attr:
                    has_mock_assert = True
                else:
                    has_result_assert = True
        if isinstance(n, ast.Assert):  # assert x == y 形态
            has_result_assert = True
    return has_mock_assert and not has_result_assert

def check_file(p: Path, fixtures_dir: Path):
    src = p.read_text(errors="ignore")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [f"{p}: 语法错误，测试根本不会跑（假绿之源）"]
    hits = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test"):
            if f2_mock_only(n):
                hits.append(f"{p}:{n.lineno} F2 mock自证: {n.name} 只有 assert_called* 无结果断言")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "sleep":
            try:
                v = float(n.args[0].value)
            except Exception:
                v = 0
            if v > SLEEP_MAX:
                hits.append(f"{p}:{getattr(n,'lineno',0)} F3 慢测试: sleep({v}) 秒，快测层禁入")
    if HOME_PAT.search(src):
        hits.append(f"{p} F3 副作用: 引用用户 home 路径（读写真实配置风险）")
    if NET_PAT.search(src):
        hits.append(f"{p} F3 网络: 测试层直连外部服务")
    # F1 手造形状字面量（正则启发式，顶层 dict/list 赋值；嵌套形状差靠语义审查）
    for m in re.finditer(r"(?:fixture|shape|payload)_\w+\s*=\s*[\{\[]", src):
        ln = src[:m.start()].count("\n") + 1
        hits.append(f"{p}:{ln} F1 手造形状字面量: 若为引擎/接口返回结构，必须改用 fixtures/ 真实 dump（先实跑 dump 再引用）")
    # F4 复现命名契约机检【V3.4.2】: re-<id> 型回归测试须在 fixtures/ 有对应真实 dump；
    # fixtures/ 目录不存在本身=违规（dump 规程没执行），不再静默跳过
    mnames = {m.group(1) for m in re.finditer(r"(?:re|regress)[_-](\w+)", p.stem)}
    if mnames:
        if not fixtures_dir.is_dir():
            hits.append(f"{p} F4 命名契约: 回归测试存在但 fixtures/ 目录不存在——真实 dump 规程未落地")
        else:
            have = {f.name for f in fixtures_dir.iterdir()}
            for bid in mnames:
                if not any(bid in h for h in have):
                    hits.append(f"{p} F4 命名契约: 回归测试 '{p.name}' 标记 bug={bid} 但 fixtures/ 无对应真实 dump（先实跑复现 dump 再写测试）")
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="测试文件或目录")
    ap.add_argument("--fixtures-dir", default="fixtures")
    a = ap.parse_args()
    root = Path(a.path)
    files = [root] if root.is_file() else sorted(root.rglob("test_*.py")) + sorted(root.rglob("*_test.py"))
    if not files:
        print("FIXTURE-CHECK: 未发现测试文件（孤儿测试/漏测信号）")
        sys.exit(0)
    allh = []
    for f in files:
        allh += check_file(f, Path(a.fixtures_dir))
    for h in allh:
        print("  ✗", h)
    print(f"FIXTURE-CHECK files={len(files)} findings={len(allh)}")
    if allh:
        print("RESULT: MUST_FIX（假测试四判命中）")
        sys.exit(1)
    print("RESULT: PASS")

if __name__ == "__main__":
    main()
