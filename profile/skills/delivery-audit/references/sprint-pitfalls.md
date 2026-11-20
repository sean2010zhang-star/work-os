# Sprint开发常见Pitfalls

## read_file输出写入文件时行号污染

**问题**: `read_file`返回的内容格式为 `     1|content`（带行号前缀）。如果将此输出直接`write_file`回同一文件，行号会被写入文件内容，导致语法错误。

**症状**: 页面渲染异常，TypeScript报 `Import is not allowed here`，每行开头有 `     N|     N|     N|` 前缀。

**修复**:
```python
import re
cleaned = []
for line in lines:
    cleaned_line = re.sub(r'^\s*\d+\|', '', line)
    cleaned.append(cleaned_line)
```

**预防**: 不要用`read_file`的输出直接`write_file`。用`patch`做定向修改，或用`terminal`的`cat`读取原始内容。

---

## delegate_task子agent修改文件后父agent未重新读取

**问题**: 子agent通过`write_file`创建/修改了文件，父agent直接`patch`该文件时基于旧缓存，可能覆盖子agent的修改或匹配失败。

**症状**: `No entry matched` 或文件内容被意外覆盖。

**预防**: 子agent返回后，父agent在编辑前必须先`read_file`或`search_files`重新读取文件当前状态。

---

## TypeScript组件导入遗漏

**问题**: 通过`delegate_task`批量创建组件后，在page.tsx中添加新组件import时，如果只添加了组件import但遗漏了组件内使用的icon import（如`ShieldAlert`），TypeScript构建会失败。

**症状**: `npx next build` 报 `Cannot find name 'ShieldAlert'` 或类似错误。

**预防**: 创建组件时检查所有lucide-react图标导入。子agent返回后立即运行`npx next build`验证。

---

## FastAPI后端Python版本不匹配

**问题**: 系统`python3`可能是不同版本（如3.9 vs 3.11），某些包只安装在特定版本的site-packages中。

**症状**: `ModuleNotFoundError: No module named 'fastapi'`

**诊断**:
```bash
pip3 show fastapi | grep Location
which python3
/opt/homebrew/bin/python3 --version
```

**修复**: 在main.py shebang中指定正确的Python路径：
```python
#!/usr/bin/env /opt/homebrew/bin/python3
```

---

## Next.js dev server缓存旧代码

**问题**: Turbopack dev server可能缓存旧的页面渲染结果，修改page.tsx后刷新浏览器仍显示旧版。

**症状**: 截图/视觉检查发现暗色主题未生效、Tab未显示等。

**修复**: 完全停止并重启dev server:
```bash
pkill -f "next dev"
npx next dev -p 3002
```

---

## Git .next目录污染

**问题**: `.next/` build缓存目录如果已被git跟踪（之前误提交），即使`.gitignore`有`.next/`，`git add -A`仍会显示大量`.next`变更。

**修复**:
```bash
git rm -r --cached .next/
git commit -m "chore: remove .next from tracking"
```

---

## 浏览器不可用时的页面验证策略

**问题**: `browser_navigate`失败（Chrome未安装），无法进行交互式测试。

**替代方案**:
1. `npx playwright install chromium` 安装无头浏览器
2. `npx playwright screenshot --browser chromium --wait-for-timeout 2000 URL /tmp/screenshot.png` 截图
3. `vision_analyze` 分析截图
4. `curl` 测试API端点（最可靠的集成测试）
