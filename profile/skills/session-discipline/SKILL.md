---
name: session-discipline
description: 会话纪律 — 每次对话结束的全量备份流程 + 工作模式选择 + 常见反模式。
version: 1.3.0
category: foundation
---

# 会话纪律 Skill

## 触发条件
- 每次对话结束前
- 用户说"备份"/"提交"/"保存"
- 完成了重要功能修改或设计工作后

## 全量备份 (4项，缺一不可)

每次对话结束必须执行以下4项备份：

| # | 备份目标 | 命令/方式 | 验证 |
|---|----------|-----------|------|
| 1 | **Git** | 先检查`git status`，若非repo则`git init`+`.gitignore`+首commit | `git status` clean |

**⚠️ L1 Git pitfall**: 不是所有项目目录都有git repo。执行前先`git status`检查，若返回"not a git repository"则：
1. `git init`
2. 创建`.gitignore`（排除data/*.db, uploads/, __pycache__/, *.pyc）
3. `git add -A && git commit -m "init: 项目初始化"`
然后才能正常commit变更。
| 2 | **外存** | `rsync -a --exclude='.git' --exclude='node_modules' src/ <mount-point>/<external-drive>/backup_YYYYMMDD/` | 目标目录存在且有内容 |
| 3 | **<vault>** | `write_file ~/Desktop/<vault>/wiki/projects/<name>.md` | 文件存在且日期为今天 |
| 4 | **session-log** | `write_file ~/Desktop/session-log/session_YYYYMMDD_<项目名>_<topic>.md` | 文件存在，文件名含项目名便于查找 |

**外存路径**: `<mount-point>/<external-drive>/backup_YYYYMMDD/`

**备份内容清单**:
- 所有今天修改过的项目目录
- 设计文档(PRD/架构/功能/商业化)
- 商业计划书HTML
- 会话摘要(session-log)



## 工作模式选择

开始任何非trivial任务前，先判断复杂度：

```
L1 简单 → 直接执行
L2 并行 → delegate_task(仅审核/研究)
L3 复杂 → plan-confirm-execute (写方案→确认→执行)
L4 大型 → GStack pipeline + 三省六部 + 蜂群限流
```

详见 plan-confirm-execute skill 的 L1-L4 框架。

## 文件创建铁律

**绝不走delegate_task创建大文件(200+行必超时600s)**。

| 模式 | 6文件×200行 | 3文件×200行 | 1文件×200行 |
|------|------------|------------|------------|
| delegate_task | ❌ 必超时 | ⚠️ 可能超时 | ✅ 通常OK |
| execute_code+write_file | ✅ 5-10秒 | ✅ 3-5秒 | ✅ 1-2秒 |

**正确模式**:
```python
# execute_code中批量写文件(比delegate_task快100倍)
from hermes_tools import write_file
for sys, content in files.items():
    write_file(path, content)
```

**delegate_task仅用于**: 独立审核/研究/轻量任务(读文件+分析+返回摘要)
**绝不用于**: 批量文件创建/大型代码生成/多系统并行开发

**L4最优组合(实测验证)**:
- **GStack pipeline**: 我直接规划+执行(不走子agent)
- **三省六部注册**: 方案→自审→执行→验证(全流程闭环)
- **蜂群限流**: 批量任务用execute_code(受控并行)
- **独立审核**: delegate_task(仅审核/研究)

## 商业计划书风格规范

**用户明确要求**: FlowForge暗色风格，**不用**Apple白底风格。

| 要素 | FlowForge风格(正确) | Apple风格(禁用) |
|------|-------------------|----------------|
| 背景 | #0e1416 暗色 | 白色 |
| CSS框架 | Tailwind CDN | 纯CSS |
| 效果 | glass-panel毛玻璃 | 简洁圆角 |
| 主色 | #4cd7f6 (cyan) | #0071e3 (Apple blue) |
| accent | #d4af37 (gold) | 无 |
| 字体 | Inter + JetBrains Mono | SF Pro |
| 动画 | 光斑+glow | 无 |

参考文件: `~/Desktop/FlowForge商业计划书.html`

## Memory写入规范 

每次写入MEMORY.md时必须遵守:

| 禁止写入 | 原因 | 替代方案 |
|----------|------|----------|
| API key/密码 | 安全风险+浪费字符 | 存.env或脚本内 |
| 版本号(如v0.14.0) | 易过时，污染每次对话 | 存skill或hermes --version |
| 端口号(如:8090) | 服务可能停止/变更 | 标注"按需启动" |
| 数量统计(如60实体) | 数据持续变化 | 用graphiti实时查询 |
| 临时状态 | 会过时 | 不存，用session_search回溯 |

每条memory = 1个决策级稳定事实，不超过200字符。
API key、配置详情等易变信息存skill的references/或脚本内。


### Cron Jobs
- 每日22:00 backup_all.py (job_id: fd6ddf36c9a9)
- 每日08:00 health_check.py (job_id: 1573b340d53d)


**外存rsync注意事项**
- 排除: `--exclude='node_modules' --exclude='.next' --exclude='.git' --exclude='__pycache__'`
- 大项目用 `terminal(background=True, notify_on_complete=True)`
- 外存路径: `<mount-point>/<external-drive>/backup_YYYYMMDD/`

**外存rsync超时:** 全量rsync `~/.hermes/skills/` 到外存超过120s timeout。原因: skills目录含大量小文件(数千个)。修复: 改用tar.gz压缩后复制，速度快10x+：
```bash
cd ~/.hermes && tar czf "<mount-point>/<external-drive>/backup_YYYYMMDD/hermes-skills-YYYYMMDD.tar.gz" \
  --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='.venv' \
  skills/foundation/ skills/software-development/ skills/business/ skills/autonomous-ai-agents/ skills/devops/
```
只打包核心category目录而非全量skills，进一步减少体积。铁律: skills目录备份用tar.gz不用rsync。

### state.db维护
- 位置: `~/.hermes/state.db` (500-600MB)
- 月度维护: `~/.hermes/scripts/monthly_db_maintenance.py`
- WAL积压: `PRAGMA wal_checkpoint(TRUNCATE)`
- VACUUM: `sqlite3 ~/.hermes/state.db "VACUUM;"`

### compression参数调优
- 默认threshold: 0.50 → 推荐: 0.70 (减少~30%分段频率)
- `hermes config set compression.threshold 0.70`

## 备份颗粒度标准
备份内容必须达到范例页面的颗粒度：
- 每个项目/阶段独立toggle块
- toggle内含完整子内容(表格/代码块/列表)
- 量化数据(文件数/代码行/服务数/路由数)
- 决策记录(为什么选这个方案/淘汰了什么)
- 不是简单的"完成了X"，而是"X的详细状态"

## 全量审查模式


审查维度：代码质量、功能完整性、架构合理性、安全测试、测试覆盖率。
输出：审查报告（PASS/FAIL）+ 问题清单 + 改进建议 + 安全评估。

## 全量备份铁律

用户说:"不是备份你给我的总结内容，我要全量的信息。我的问题，你的主要思考过程，你给我的全量的详细的回答。"

**正确做法**: 备份文件必须包含每轮对话的:
1. **用户问题原文** — 逐字复制,不改写
2. **思考过程** — 我为什么这么做,读了什么,判断了什么
3. **回答全文** — 完整的回答文本,包括所有表格/代码块/分析,不是摘要

**错误做法**:
- ❌ 只写"回答要点"或bullet总结
- ❌ 把2000字回答压缩成200字摘要
- ❌ 跳过中间的分析过程只保留结论

**正确格式**:
```markdown
# 第N轮: [主题]

## 用户问题
[用户原话,逐字]

## 思考过程
[我读了什么文件,加载了什么技能,做了什么判断]

## 回答全文
[完整的回答文本,包括所有:
 - 问题分析
 - 表格对比
 - 代码示例
 - 设计方案
 - 执行计划
 不要压缩,不要摘要]
```

**反模式**:
```markdown
## 回答要点
- 要点1
- 要点2
- 要点3
```
这是摘要,不是全量备份。用户要的是完整回答,可以反复琢磨和细化。

## 反模式 (禁止)

 - ❌ 结构化备份平铺(必须按项目分层，条目含问题+思考+结果+数据)
- ❌ 跳过备份直接结束对话
- ❌ 高价值分析产出跳过结构化备份
- ❌ 只做Git commit不做其他3项备份
- ❌ 备份时不验证目标文件是否存在
- ❌ L4任务不加载skill直接执行
- ❌ 复杂任务不写方案就动手
- ❌ 大版本发布前不进行全量审查
