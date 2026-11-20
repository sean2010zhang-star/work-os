# Sprint连续交付模式 — 参考实现

## 多引擎系统v2.0 执行记录 (6 Sprint)

### Sprint节奏
| Sprint | 内容 | 后端文件 | 前端文件 | 耗时 |
|--------|------|----------|----------|------|
| 1 | 基础+文档解析 | 4 (base/schema/parser/main) | 4 (upload/proxy/page) | ~15min |
| 2 | 标准拆解+合规审查 | 3 (extractor/checker/criteria) | 2 (CriteriaView/ComplianceView) | ~10min |
| 3 | 评分+偏离 | 2 (scoring/deviation) | 2 (ScoreView/DeviationView) | ~8min |
| 4 | 报告+Pipeline | 2 (report/pipeline) | 0 (集成到page.tsx) | ~5min |
| 5 | 围标串标 | 1 (collusion_detector) | 1 (CollusionView) | ~8min |
| 6 | 股权+发布 | 2 (equity/report补) | 1 (page.tsx更新) | ~5min |

### 文件增长曲线
- Sprint 1后: 11文件, ~800行
- Sprint 3后: 18文件, ~1500行
- Sprint 6后: 23文件, ~1900行

### delegate_task参数模板
```python
delegate_task(
    goal="创建前端组件...",
    context="项目路径: ~/Desktop/engine-app/\n技术栈: Next.js+shadcn/ui+Tailwind\n暗色主题: bg-[#0e1416], glass-panel...",
    toolsets=["file", "terminal"]
)
```
- context必须包含: 项目路径、技术栈、设计规范、API响应格式
- 子agent无法访问父agent的对话历史

### execute_code批量创建模式
```python
from hermes_tools import write_file
write_file("/path/to/file.py", '''content...''')
# 一次execute_code可创建5-10个文件
```
优于多次单独write_file调用。

### Gate验证execute_code模板
```python
from hermes_tools import terminal, read_file
import json
# Gate 1: 文件检查 (read_file)
# Gate 2: API测试 (curl + json.loads)
# Gate 3: 构建 (terminal npx next build)
# 输出: 表格式PASS/FAIL报告
```

### 全量备份流程 (Sprint全部完成后)

所有Sprint完成后执行5项备份铁律：
1. **Git**: `git add -A && git commit && git tag -a vX.Y-mvp`
2. **外存**: `rsync` 到 `<mount-point>/<external-drive>/backup_YYYYMMDD/`
3. **<vault>**: 更新 `~/Desktop/<vault>/wiki/projects/{project}.md`
4. **session-log**: 写入 `~/Desktop/session-log/session_YYYYMMDD_{project}.md`

