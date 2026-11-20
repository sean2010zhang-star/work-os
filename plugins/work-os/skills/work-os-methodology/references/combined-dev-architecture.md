# 复杂项目联合开发架构: GStack Pipeline + 三省六部 + 蜂群限流 + 独立Agent Team + Sprint+Gate


## 四层架构总览

```
Layer 1: 三省六部制 (结构化注册层)
  中书省(规划拆解) → 门下省(审核封驳) → 尚书省(执行) → 审查院(独立审计)

Layer 2: GStack Pipeline (执行层)
  六部映射: 吏部(路由)/户部(资源)/礼部(文档)/兵部(工程)/刑部(测试)/工部(部署)
  Pipeline: validator → processor → scorer → optimizer

Layer 3: 蜂群限流 (差异化执行层)
  工兵蜂: 代码执行工具批量创建 (100x快于子代理)
  侦察蜂: 子代理调研验证 (只读不写)
  战斗蜂: 主Agent核心实现 (不可委托)
  审计蜂: 子代理只读审核 (独立上下文)

Layer 4: 独立Agent Team + Sprint+Gate (质量保障+交付层)
  3 Agent并行只读审计 + 4层Gate门控 + 4件套归档
```

## 蜂群限流铁律

1. 文件创建/批量写入 → 代码执行工具 (绝不子代理, 必超时600s)
2. 独立审核/研究 → 子代理 (仅此用途)
3. 核心逻辑/算法 → 主Agent直接实现 (不委托)
4. 工兵蜂写完后必须py_compile验证 + \x00清理
5. 侦察蜂只产出分析报告, 不修改任何文件
6. 审计蜂只产出审计报告, 不修改任何代码

## 独立Agent Team审计

### 3 Agent配置
```python
dispatch_subagents([
    {goal: "代码质量审核: 命名规范/错误处理/类型标注/代码重复/docstring", read_only: true},
    {goal: "架构评估: pipeline实现/接口设计/模块依赖/DRY/可测试性", read_only: true},
    {goal: "安全+边界审核: 输入验证/异常处理/边界值/注入风险/资源耗尽", read_only: true},
])
```

### 独立性保障
- 上下文隔离: 不看主Agent执行过程/调试记录/修复历史
- 权限隔离: 只读(terminal+file), 不能write_file/patch
- 视角隔离: 三维度互补, 单Agent不可能全覆盖

### 审计-修复循环
```
初始审计(发现P0) → 修复 → 重审(可能发现新P0) → 修复 → 重审(P0=0) → 放行
```
迭代规律:
- 安全分提升最快 (有明确修复模式: 白名单/限流/sanitize)
- 代码分提升较慢 (需深层重构: DRY/类型标注/原子SQL)
- 每次修复可能引入新问题 → 必须重审

## 4层Gate门控

| Gate | 名称 | 检查内容 | 判定 |
|------|------|----------|------|
| 1 | Pre-flight | 文件存在且非空, 无TODO/FIXME | 11/11通过=PASS |
| 2 | Revision | API可curl, 核心功能测试, 构建通过 | 每项PASS/FAIL |
| 3 | Integration | 前端调用真实API(无mock/setTimeout), grep验证 | 每页面三项PASS |
| 4 | Agent Team终审 | 代码≥7/10 + 架构≥7/10 + 安全≥7/10 + P0=0 | 3 Agent均PASS |

Gate全PASS → 4件套归档 → 自动下一Sprint
任一FAIL → 修复 → 重验 (最多3次)
3次FAIL → Escalation

## 12条执行铁律

1. 任务到达先判定模式(M1-M18), 不可跳过
2. M7+必须加载对应skill
3. 文件创建用代码执行工具, 绝不用子代理
4. 核心逻辑主Agent直接实现, 不委托
5. 审计Agent只读不写, 独立上下文
6. Gate4必须Agent Team 3 Agent审核通过
7. P0修复后必须重审(迭代直到P0=0)
8. 前后端必须打通(真实API调用, 非mock)
9. 完成度<80%禁止声称"完成"
10. 每个Sprint必须完整4件套归档
11. 连续执行= Gate全PASS自动推进
12. 3次FAIL必须Escalation, 不可静默跳过

## 实测数据

| 项目 | Agent Team P0 | 单Agent P0 | 关键发现 |
|------|---------------|------------|----------|
| 另一全栈项目 V5 | 6 | 2 | conservative路径反转(架构Agent独有) |
