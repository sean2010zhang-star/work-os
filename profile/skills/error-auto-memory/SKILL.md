---
name: error-auto-memory
description: "错误自动记忆 — 工具执行失败时自动记录错误、分析根因、寻找修复方案，写入经验库。下次遇到同样问题时自动规避，实现犯一次错终身免疫。"
version: 1.0.0
tags: [error, memory, learning, resilience, auto-fix]
---

# 错误自动记忆

## When to Use
当工具执行失败时自动触发，不需要用户请求。

## 触发条件

| 失败类型 | 例子 | 优先级 |
|---------|------|--------|
| terminal 命令失败(exit_code!=0) | npm install 超时, pip 版本冲突 | 高 |
| API 调用失败(4xx/5xx) | 外部 API 限流, GitHub token 过期 | 高 |
| 文件操作失败 | 权限不足, 路径不存在 | 中 |
| 搜索无结果 | 关键词太具体, 索引未更新 | 低 |
| 用户否定(3+次) | "不对"、"错了"、"重来" | 高 |

## 自动处理流程

### Step 1: 捕获错误上下文
```
错误类型: {tool_name} failed with {error}
命令: {exact_command}
环境: {working_dir, python_version, os}
```

### Step 2: 分析根因
用以下分类判断:
- **环境问题**: 缺少依赖、版本不兼容、路径错误
- **权限问题**: 文件权限、API token、网络限制
- **逻辑错误**: 参数错误、顺序错误、条件遗漏
- **已知陷阱**: skill中已记录的Pitfall

### Step 3: 查找修复方案
1. 先查已有 skill 的 Pitfalls 部分
2. 搜索 session_search 历史中的类似错误
3. 尝试常见修复(升级、换源、加参数)

### Step 4: 记录到经验库
格式: `~/.hermes/error-memory.jsonl`

```json
{
  "timestamp": "T10:30:00",
  "error_type": "pip_install_timeout",
  "command": "uv pip install torch",
  "root_cause": "PyPI源慢+包体积大",
  "fix": "用--index-url指定清华源或用--find-links本地安装",
  "skill_patch": "mlops/training/pytorch-fsdp: 添加国内镜像源说明",
  "confidence": 0.9,
  "occurrences": 1
}
```

### Step 5: 条件性更新 skill
当同一错误出现 2+ 次时:
- 自动在对应 skill 的 Pitfalls 部分追加
- 使用 skill_manage(action="patch")

## 错误记忆查询

在执行操作前，先查询经验库:
```
1. 读取 ~/.hermes/error-memory.jsonl
2. 匹配当前命令/工具/环境
3. 如果命中: 直接应用已知修复方案，跳过试错
4. 如果未命中: 正常执行，失败后走上述流程
```

## 记忆衰减

| 条件 | 操作 |
|------|------|
| 同一错误修复后30天未复现 | confidence *= 0.8 |
| confidence < 0.3 | 从经验库删除 |
| 修复方案被skill更新覆盖 | 标记为superseded |
| 用户明确否定修复方案 | 立即删除 |

## 与 continuous-learning 的关系

| 维度 | continuous-learning | error-auto-memory |
|------|-------------------|-------------------|
| 触发时机 | 会话结束(Stop hook) | 工具执行失败时(实时) |
| 记录粒度 | 整个会话的模式 | 单个错误的根因+修复 |
| 存储位置 | skill文件 | error-memory.jsonl |
| 置信度 | 无 | 0.3-0.9 衰减 |
| 自动应用 | 否(需人工review) | 是(命中即应用) |

两者互补: error-auto-memory处理即时失败，continuous-learning提取长期模式。

## 实现状态

| 组件 | 状态 | 路径 |
|------|------|------|
| SKILL.md | ✅ | ~/.hermes/skills/foundation/error-auto-memory/ |
| MEMORY注入 | ✅ | 每次turn自动加载经验库查询规则 |
| 扫描脚本 | ✅ | ~/.hermes/scripts/error_memory_scan.py |
| Cron job | ✅ | error-memory-scan (每6小时, job_id: 09d5c03e4955) |
| 经验库文件 | 运行时创建 | ~/.hermes/error-memory.jsonl |

## 脚本说明: error_memory_scan.py

扫描 Hermes session DB 中的工具执行失败，提取结构化错误信息写入经验库。

支持的错误模式:
- terminal_failure: exit_code != 0 的命令
- python_error: Traceback + Error 类型
- install_failure: npm/pip/uv 安装失败
- http_error: HTTP 4xx/5xx
- safety_blocked: Hermes 安全拦截

自动推断修复方案:
- timeout → 换源/加超时参数
- permission → chmod/--user
- rate_limit → 等待重试
- disk_space → 清理缓存

## 实现状态

| 组件 | 状态 | 路径 |
|------|------|------|
| SKILL.md | ✅ 已创建 | ~/.hermes/skills/foundation/error-auto-memory/ |
| 扫描脚本 | ✅ 已创建 | ~/.hermes/scripts/error_memory_scan.py |
| Cron job | ✅ 运行中 | error-memory-scan (每6小时, job_id: 09d5c03e4955) |
| 经验库 | ⚠️ 首次扫描时自动创建 | ~/.hermes/error-memory.jsonl |
| MEMORY规则 | ✅ 已注入 | 每次对话自动加载经验库查询规则 |

## 反模式

- 不要记录用户的拼写错误或临时网络波动
- 不要在同一个会话中重复记录同一错误
- 不要自动修改用户的代码，只修改skill和配置
- confidence < 0.5 的修复方案不要自动应用
