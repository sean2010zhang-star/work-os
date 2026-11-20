---
name: infrastructure-layer
description: "V2.0基础设施层 — 合并记忆体系+三层备份+自动化+外部工具集成。从V1.0的L8+L9+L10+session-discipline合并为一个。"
version: 2.0.0
category: foundation
tags: [memory, backup, automation, tools, v2]
---

# 基础设施层 V2.0

> 合并V1.0: memory-system-design + session-discipline(L8/L9/L10)

---

## 一、记忆体系

### 四层结构

| 层级 | 存储 | 用途 | 容量 |
|------|------|------|------|
| Layer 1 | memory工具 | 精简索引(验证2次+的稳定事实) | 2200字符 |
| Layer 2 | ~/.hermes/memory/ | 完整内容(分层目录) | 无限 |
| Layer 3 | Graphiti-Lite | 知识图谱(实体+关系+检索) | 自动 |
| Layer 4 | session_search | 原始对话证据 | SQLite FTS5 |

**关键**: memory是"索引"，session_search是"原始证据"，skill是"方法论"。

### 六条设计原则(论文arXiv:2605.12978)

1. **原始证据优先** — session_search是真相，memory是索引指针
2. **溯源标注** — 每条memory附来源(session_id/日期)
3. **低频整合** — 条件: 2次验证 + 7天稳定 + 不可检索
4. **防过度泛化** — 规则附适用边界+反例
5. **防过度特化** — 不绑定临时变量名/文件名
6. **定期衰减** — 每月审计，删30天未引用的

### 写memory检查清单

- [ ] 7天后仍有效？
- [ ] 已2次验证？
- [ ] session_search不可快速检索？
- [ ] 避免了过度泛化/特化？
- [ ] 附带了适用边界？
- [ ] 不是过程性知识(应放skill)？

### MEMORY压缩(>80%时)

优先级1 删除: 流程知识→skill, 临时状态→删除, 可检索冗余→删除
优先级2 压缩: 删示例, 合并同主题, 删连接词, 指向skill
目标: <60%健康, >80%危险, >95%不可写入

---

## 二、三层备份制度 (V2.0从5层简化)

### 设计原则

V1.0: 5层全手动 → 执行率~40%
V2.0: 3层分频率 → 目标执行率>90%

### 三层定义

| 层级 | 内容 | 频率 | 自动化 |
|------|------|------|--------|
| L1 自动 | Git commit + session-log一行摘要 | 每次对话结束 | 全自动 |
| L2 半自动 | <vault>结构化备份 | 每周/每个Sprint | 脚本辅助 |
| L3 全量 | 外存rsync | 每月 | 手动触发 |

### L1 自动备份 (每次)

```bash
git add -A && git commit -m "session: $(date +%Y%m%d)"
echo "$(date +%Y%m%d) [项目名] [摘要]" >> ~/Desktop/session-log/sessions.log
```

### L2 半自动备份 (每周/Sprint)

```bash
# <vault>
write_file ~/Desktop/<vault>/wiki/hermes/{项目}.md "## $(date +%Y%m%S)\n[内容]"

```

### L3 全量备份 (每月/用户要求时)

完整4层备份:
1. Git commit + tag
2. tar.gz → ~/hermes-backup/
3. <vault>详细更新
4. session-log完整记录

外存: rsync到 <mount-point>/<external-drive>/
Skills目录: 用tar.gz不用rsync(小文件太多)

### 全量备份铁律

用户说"全量备份"时5层全部执行。
备份内容必须包含: 用户问题原文 + 思考过程 + 回答全文(不是摘要)。

---

## 三、自动化组件

| 组件 | 频率 | 说明 |
|------|------|------|
| Graphiti-Lite同步 | 每2小时 | cron自动同步对话到知识图谱 |
| 记忆审计 | 每月1日 | memory_audit.py |
| Sprint连续交付 | 实时 | Gate PASS → 自动下一Sprint |
| 子Agent并行 | 实时 | delegate_task批量(最多3) |
| 体系健康度 | 每月1日 | 6指标检查 |

---

## 四、外部工具集成

| 类别 | 工具 | 用途 |
|------|------|------|
| MCP | mcporter / native-mcp | 外部工具服务 |
| Agent | claude-code / codex / opencode | 委派编码 |
| 蜂群 | swarm-agents(ruflo) | 100+专用Agent |
| 美股 | Twelve Data | 美股行情 |
| A股 | AKShare(fallback) + Sina(主) | A股500+接口 |
| 平台 | <vault> / Git / 外存 | 备份管理 |
| 创业 | Google Workspace / Linear / Airtable | 运营工具 |

---

## 五、state.db维护

| 风险 | 症状 | 修复 |
|------|------|------|
| WAL积压 | >100MB | PRAGMA wal_checkpoint(TRUNCATE) |
| B树损坏 | integrity_check!=ok | 从备份恢复 |
| 文件膨胀 | >1GB | VACUUM |

月度脚本: ~/.hermes/scripts/monthly_db_maintenance.py
compression threshold: 0.50 → 推荐0.70

---

## 六、知识分层存放规则

| 类型 | 存放 | 生命周期 | 示例 |
|------|------|----------|------|
| 底层逻辑(Why) | memory | 永久 | "反馈闭环必须执行" |
| 操作流程(How) | skill | 随版本更新 | "node --check验证JS" |
| 执行结果(What) | <vault> | 归档 | "v0.2.14修复引号错误" |

---

## V1.0→V2.0 映射

| V1.0 | V2.0 |
|------|------|
| memory-system-design | 本skill第一节 |
| session-discipline(备份部分) | 本skill第二节 |
| L8自动化体系 | 本skill第三节 |
| L9外部集成 | 本skill第四节 |
| L10记忆体系 | 本skill第一节 |
| 5层备份 | 3层备份(简化) |
