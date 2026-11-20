---
name: project-git-version
description: 项目Git版本管理 — 自动commit+版本号+tag，支持回滚。每次代码变更后自动版本管理。
version: 1.0.0
---

# 项目Git版本管理

对 ~/projects/ 下所有项目做规范的Git版本管理。

## 适用项目

| 项目 | 路径 | Git状态 |
|------|------|---------|
| ai-dashboard | ~/projects/ai-dashboard | ✅ 已有 |
| my-app | ~/projects/my-app | ✅ 已有 |
| tradingagents | ~/projects/tradingagents | ✅ 已有 |
| free-claude-code | ~/projects/free-claude-code | ✅ 已有 |

## 日常操作

### 1. 保存当前版本（每次代码变更后必做）

```bash
cd ~/projects/<project>
./version.sh "描述本次变更" [patch|minor|major]
```

- **patch** (默认): Bug修复、小改动 → 0.1.0→0.1.1
- **minor**: 新功能、新模块 → 0.1.0→0.2.0  
- **major**: 架构重构、破坏性变更 → 0.1.0→1.0.0

### 2. 查看历史版本

```bash
cd ~/projects/<project>
git log --oneline --decorate
git tag -l
```

### 3. 回滚到指定版本

```bash
# 回滚到指定tag（保留工作区）
git checkout v0.1.0

# 回滚到指定commit（保留工作区）
git checkout <commit-hash>

# 回到最新版本
git checkout main
```

### 4. 紧急回滚（撤销最近一次commit）

```bash
# 软回滚（保留文件修改，撤销commit）
git reset --soft HEAD~1

# 硬滚（彻底删除最近修改）
git reset --hard HEAD~1
```

**相对计数回滚安全规则**（`reset --soft HEAD~N` 踩过坑）：
- amend、重打 tag、或链上刚追加过提交后，HEAD~N 指向的已不是你以为的位置——N 多数一步就会把不该合并的提交一起吞进下一个 commit（message 与实际内容脱节，谱系说谎）。执行前必须先 `git log --oneline -N+2` 打印将要被吞的区间逐个确认；能用具名锚就不用相对计数：`git reset --soft <tag或commit>`。
- 发现折叠错误后的补救同样走锚：`git reset --soft <正确tag>` + 临时 branch 保对象，重切链，全程 `git log` 复核。
- **重整/回滚命令被网关 BLOCKED（超时未批）时：保持现状，不重试、不换路径绕行**，把当前实际状态（含事故描述）如实报告用户等拍板。事故本身可保持——工作树内容逐项验证正确优先于历史整洁。

## Commit规范

格式: `v<版本号> <类型>: <描述>`

类型:
- `feat`: 新功能
- `fix`: Bug修复
- `refactor`: 重构
- `style`: 样式/UI调整
- `docs`: 文档
- `chore`: 构建/工具

## 版本号规则 (Semantic Versioning)

```
MAJOR.MINOR.PATCH
  │     │     └── Bug修复、小改动
  │     └──────── 新功能（向后兼容）
  └────────────── 破坏性变更
```

## 注意事项

- data/ 目录下的JSON数据文件已加入.gitignore（含任务/记忆等运行时数据）
- 每次回答后如果改了代码，必须执行 version.sh 保存版本
- 回滚前先用 `git stash` 保存未提交的修改
- Next.js项目的.next/目录必须在.gitignore中。如果已被git跟踪，需执行:
  `git rm -r --cached .next/` 后重新commit
- Python项目的__pycache__/和uploads/目录也应加入.gitignore
- 多Sprint项目使用 `git tag -a v2.0-sprintN` 格式打标签
- tag 指向旧 commit 而 HEAD 已前进时，重打 tag 用 `git tag -f` 后必须 `git log --oneline -1` + `git tag --points-at HEAD` 双向确认；发现 tag 落空点（旧 tip）说明中间 commit 被 amend/reset 挪动过，先理清链再打。
- Gate/sprint tag 之后若追加修复提交（审计清偿、增量功能），同样补打递延小版本 tag（v1.4.0→v1.4.1→v1.4.2）保持版本谱系连续——谱系里不留裸 commit；wiki/知识库的版本谱系表逐 tag 补行（commit hash+验证数字），回退点精确到每个清偿步。tag 指向 gate 原 commit 不动（annotated peel 保持），新 tag 指新 HEAD。

## 备份铁律

每次对话结束必须执行4项全量备份（用户多次强调，不可遗忘）:

| 序号 | 项目 | 方式 | 说明 |
|------|------|------|------|
| 1 | Git | git add -A && git commit | 所有活跃项目 |
| 2 | 外存 | rsync到 <external-drive>/backup_YYYYMMDD/ | 4个项目目录 |
| 3 | 记忆库 | 更新 <memory-vault>/projects/*.md | 项目状态文件 |
| 4 | 会话记录 | 写入 <session-log>/session_YYYYMMDD_*.md | 会话记录 |

自动化: 定时任务 job每日22:00执行 `backup_all.py`（job_id: fd6ddf36c9a9）
手动执行: `python3 记忆库/scripts/backup_all.py`

## WHEN 触发条件

- 代码变更后需要版本管理
- 用户说"提交"/"版本"/"回滚"/"commit"/"tag"
- 项目需要规范化版本号管理
- 对话结束前（备份铁律）

## REFERENCE 参考文献

- 语义化版本 2.0.0 (Semantic Versioning)
- Conventional Commits 规范
- Git 官方文档
- 备份脚本: `scripts/backup_all.py`
- 巡检脚本: `记忆库/scripts/health_check.py`（定时任务每日08:00）
- 外存路径: `<external-drive>/backup_YYYYMMDD/`

## LIMITS 局限

- 不处理merge冲突（需用户手动解决）
- 不替用户决定版本号飞跃级别（major/minor/patch由用户指定）
- 不自动推送到远程仓库
- 外存未挂载时rsync跳过（不报错）
