# Work OS 生产环境教训 

来源: P1级issue #5563 + 社区分析

## 四个互相咬合的问题

### 1. Token失血
- 12小时连续对话被切成15个session
- 每新开session，历史消息重新注入API
- 2.6M token中89%是历史重放
- **根因**: compression threshold太低(0.50)
- **缓解**: 提高到0.70，减少分段频率

### 2. SQLite三周后损坏
- B树页面损坏，18个session永久丢失
- **根因**: 多进程并发写入同一个state.db
- **缓解**: 月度integrity_check + VACUUM + WAL checkpoint
- **架构真相**: WAL模式支持并发读，但写入仍需串行化

### 3. Memory 2200字符上限
- 复杂项目根本装不下
- 旧记忆被新记忆覆盖
- **缓解**: memory只存决策级铁律，过程性知识进skill
- **架构真相**: MEMORY.md是唯一"每次注入"的记忆层

### 4. 环境幻觉
- AI声称自己在"信息已过期的云容器"里(实际在本地WSL2)
- **根因**: 前三个问题的叠加效应
- session分段丢失环境上下文 → memory装不下环境信息 → 压缩摘要包含错误信息

## 核心洞察

"自我进化"和"工程稳定性"是天然矛盾的。

让agent自己写memory/skill/session → 状态空间持续膨胀 → 更多token消耗 + 更高损坏概率 + 更多幻觉。

两周看到优势，三四周开始集中看到代价。

## 官方态度

- Nous发布了Curator(5月初)
- 功能: 30天没用标stale，90天移到archive
- 等于官方承认Skill自动创建的副作用是真实的
- 但Curator只解决L3层(skills)，不解决token/SQLite/memory

## 运维纪律

- 每三周清理一次memory目录
- 每月跑一次数据库完整性检查
- compression threshold设为0.70
- WAL checkpoint加入watchdog
