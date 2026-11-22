---
name: longrun-campaign
description: "长程自主战役协议 V3.4（武器库完备版）：v1 时间轴全保留 + oil 十项工程机制 + 十迷宫修复 + 八脚本机检武器库（scope_check含孤儿tag与require-clean/gate_recorder负向自检/cursor_check六不变量含漏做方向/fixture_check假测试AST含F4命名契约/value_check取值纪律/heartbeat_check双证据强制cron/arch_check结构主张机检）。用户授权'全量开发/自行执行/直到完成'类长任务时加载。"
version: 3.4.2
author: Work OS
license: MIT
category: foundation
tags: [campaign, autonomous, long-running, gate0, checkpoint, mission-contract, l1l2l3, scope-drift, root-cause, maze-tested]
related_skills: [work-os-router, sprint-gated-delivery, delivery-audit, consolidated-iron-laws, longrun-campaign]
metadata:
  hermes:
    tags: [campaign, autonomous, long-running, gate0, checkpoint]
    related_skills: [work-os-router, sprint-gated-delivery, delivery-audit, longrun-campaign]
---

# Long-Run Campaign V3.1 — 长程战役 × oil-dev 工程机制融合版（十迷宫修复）

> **血统**：v1 = 时间轴协议（Mission Contract + Sprint×Gate）。v2 = 单次变更工程链路（源自社区 oil-dev 方法论）。
> **V3.0** = 十项机制融合。 **V3.1** = 以真实事故为题源的十题中立评测（66/100）后修复 6 处实测漏项 + 3 处裁决空白。
> **V3.2-3.4** = 机检武器库实装与两轮 Runner 复测迭代。方法论见 `profile/skills/protocol-doc-benchmarking/`。
> 双版本分治铁律：协议逻辑变更需同步开源发布版并复跑隐私扫描；案例只进本机版。

## When to Use

- 用户一次性授权覆盖多个 Phase/Sprint 的连续开发（"自行执行""不用等确认""直到完成"）
- 大型多模块系统分期交付，且要求测试/审计独立性
- 需要断点恢复的长任务（跨 context 压缩 / 跨进程重启 / 跨天）

## 铁律的调和

"不用等我确认" ≠ 取消铁律1（方案确认后才能执行）。正确解释：
**把确认前置到战役启动时刻** —— Mission Contract 就是那次确认。
战役期间无需逐 Sprint 确认，但必须遵守 5 个中断上报条件 + Gate 0 缺口规则。

**oil 理念对齐**：不靠复杂提示词"限制"AI，用流程约束"提醒"AI 该做什么；
凡能静态判定的规矩，优先下沉为仓库内确定性检查脚本，而不是文档里的文字叮嘱。
【V3.1】文字禁令的覆盖范围必须显式写出**适用对象**（哪些 agent），否则形同虚设（C7 教训）。

---

## Phase 0: Mission Contract（战役护照，缺失不开工）

写 `campaign/<id>/CONTRACT.md`，与用户逐项确认后冻结。必含 **10 节**：

```markdown
# Mission Contract: <战役名>
1. 目标与范围 —— 做什么、明确不做什么（范围膨胀=中断条件）
2. 分期计划 —— Phase 列表，每 Phase 的模块+可验收交付物
3. 任务约束注入 —— 用户业务约束逐条编号，Gate 0/3 会检查它们
4. 预授权范围 —— 覆盖哪些操作免逐次确认（写码/测试/审计/commit）；
   永不预授权: 删除数据、对外发布（含云端同步！）、花钱、不可逆操作——
   【V3.1·C7】不可逆操作**明文枚举**：删数据 / 改写已推送历史（force-push、reset --soft|--hard、
   rebase、孤儿化 tag）/ 批量删除文件 / 改数据格式或库结构 / deploy / 花钱。
   清单外的"疑似不可逆"按最严档处理并上报。
5. 预算熔断 —— token 上限 / 最长 Sprint 数 / 墙钟时限，任一触顶即停并上报；
   【V3.1·C10】另含**步骤级超时**：单次子 Agent 运行 / 单条门禁命令超时上限（默认 30 分钟），
   见派发契约第 6 要素
6. 验收定义 —— "完成"的全局判据（全 Phase 过 Gate + 全量回归绿 + 用户价值门）；
   【V3.1·C8】必附**约束证据 checklist**：C1..Cn 每条约束 → 对应验收证据（测试名/截图/命令输出），
   无证据条目 = 未验收，<80% 不说完成。
   【V3.2】解耦/模块边界/接口隔离型**结构性主张**的证据必须含 `arch_check.py --isolate <各模块glob>`
   的 PASS 输出（证据形态不得由主张方自选弱证据填满——结构约束只认边界机检）
7. 中断上报条件 —— 见下节 5 条，写死
8. 独立性要求 + 派发偏好 —— 测试/审计与开发不同上下文；审计只读；
   角色偏好表: 探索/实现/审查/挑刺/会诊 各交给谁（agent+模型+只读+超时上限），
   问一次后写入本表持久化，战役内自动按角色路由；返工优先续接原子 Agent 会话。
   【V3.1·C5】每个 pin 的模型须过"模型验证三则"（见独立性保障节）才许入表。
9. 仓库开发约定（单源，Gate 0 实测核验）：
   - quick-test / merge-gate / static-check: <命令>
   - 【V3.1·C2】门禁命令须附**取码方式声明**：一律经 `gate_recorder.py` 执行（subprocess 直取退出码，无 shell 管道），
     禁止 `cmd | tail; echo $?` 这类管道尾码；Gate 0 用 `--negative-selftest` 建立记录链可信
     （失败探针必须先被记红），战役中每 Phase ≥1 次负向抽检（故意让一条真实用例红，确认 gate_log 记红）
   - 【V3.1·C4】开工前提核验：目标仓库必须已 git 化 + 存在可用备份目标（远端 remote 或外接盘），
     缺一即 Gate 0 缺口（"仓库没 git，目录一删即全灭"）
   - high-risk / do-not-edit: <glob 列表>；AGENTS.md 位置与 @引用规范
10. 决策位开关 —— 战役 ≥3 Phase 或预估 >1 天时默认开启：
    主 Agent 只做拆任务/写契约/拍板/验收，不逐行读源码、不亲手改文件；
    看代码细节一律派只读子 Agent 回答一个具体问题
```

**规则**：Contract 未经用户确认 → 不许进入 Phase 1。

## Phase 0.5: Gate 0 材料完备性评审（独立 team agent）

派 1 个独立评审 agent（只读、便宜模型且经模型验证三则）对材料做三维评审，输出 PASS/缺口清单：

| 维度 | 检查项 |
|------|--------|
| 完备 | PRD 每功能有**可机检验收标准**；接口契约、数据 schema、依赖清单齐全；Contract §3 约束都已落到具体功能点且 §6 证据 checklist 成形；**§9 每条命令实测可跑（含负向测试报红确认）、glob 与真实目录匹配、取码方式合规**；**仓库已 git 化 + 备份目标可用** |
| 可靠 | 需求无自相矛盾；引用的外部系统/模型能力核实过——**核实=直连端点+回读实际模型 ID，不是"返回 OK"**；数字/金额有一处来源 |
| 可行 | 分期切法符合模块边界；每 Phase 可独立 Gate；预算量级合理（Phase 数 × 单 Sprint 实测成本） |

- 缺口 → 回补 → 重审，直到 PASS 或用户书面接受缺口（记入 Contract）
- **禁止**：评审 agent 顺手改材料（只读）；"先开发边开发边补材料"
> 题源原型：① 某项目跳过 Gate 0 直接写代码，用户质问后返工；② 某项目未 git 化、目录丢失后只能靠旧备份+变更日志重放重建——两案即 Gate 0「§9 实测核验」与「开工前提 git 化+备份目标」检查项的直接题源。

---

## Phase 1..N: Sprint 循环（自动推进引擎）

### 第一步：Sprint 重量门（L1/L2/L3 分级，拒绝小事大做）

| 档 | 适用 | 流程 |
|----|------|------|
| **L1 轻量直达** | 单模块、原因和改法都清楚的小修/文案/样式；不碰 high-risk | 2–3 句话改法（缺陷先复现）→ 执行 → static-check + 新增用例 + 相邻模块快测 → commit。**跳 Gate 4**，Gate 1/3 合并自检。**改动 ≥2 个文件时仍要跑 scope_check**（V3.0 边缘空白修复）；判档由主 Agent 定并记入 gate_log（留痕即审计素材），拿不准就升 L2 |
| **L2 标准** | 常规单功能、中等重构、1–2 个产品取舍 | 完整循环：Gate 1→2→3→4 |
| **L3 里程碑** | 跨子系统、新数据格式/打包链路、高风险架构变更 | 完整循环 + 落盘规格 + 独立挑刺内审 + Worktree 并行派发 |

**中途升级**：执行中发现碰 high-risk、超出允许文件、冒出新产品取舍 → 停手升级重新对齐。L1 碰 high-risk 仍必须过 Gate 2。

### 派发契约（每 Sprint 实现任务锁死**六要素**）

```
1. 方向与验收   —— 本 Sprint 外部行为变化 + 可机检完成标准
2. 允许路径     —— glob 白名单（供 scope_check 比对）+ 禁改路径（来自 Contract §9）
3. 必复用基建   —— explore 简报里点名的现成组件/共享模块
4. 测试快规则   —— 写码期间只跑 static-check（秒级）；完工跑关联快测一次；
                   全量回归与打包只在 Gate 3 / Phase 边界跑。
                   【V3.1·C2】快测/门禁一律直取退出码，禁管道尾码；失败最多重跑 3 轮即停报
5. git 写禁令   — — 执行子 Agent 的**一切 git 调用强制经由 `gitguard.py --workspace <repo> -- git <子命令>`**
                   （只读白名单透传、写动词 exit 2 拒绝、deny 入 gitguard_audit.jsonl——V3.4 起
                   禁令从文字升级为技术拦截闸，适用对象=所有被派 agent；提交与历史操作由主 Agent 统一执行）；
                   需要干净基线用 git worktree add 另开（gitguard 由主 Agent 安装为子 Agent 的 git 包装别名，
                   hook 级 OS 强制仍登记为边界）
6. 超时与心跳   —— 每次派发带超时上限（默认=min(Contract §5 步骤上限, 单任务预估×2)）；
                   子 Agent 每完成一个验证步骤向 campaign/<id>/heartbeats/<task>.jsonl
                   追加一行 {"task","ts","step"}；主 Agent 等待超上限→终止进程、读回心跳判卡点、按 FAIL 计；
                   同一任务超时连续 2 次 → 中断上报条件 2。
                   【V3.2·C10】心跳是文件不是口供：独立 `heartbeat_check.py --scan heartbeats --limit <秒>`
                   挂 cron 做外部看门狗，主 Agent 自身卡死也报（STALE/BROKEN 即告警）
```

汇报格式（固定 ≤15 行）：结论 / 改动文件 / 命令与结果 / **实际使用的模型与 runner**【V3.1·C5】/ 待决问题 / 未验证部分。

并行写码子 Agent 之间**允许路径两两不重叠**；只读子 Agent 可共用主工作目录但受第 5 要素写禁令约束。
每个写码子 Agent 一个独立 worktree（`git worktree add`），登记进 mission.json 供收尾合并。

### 机检武器库（scripts/，V3.2 全部实测通过；按"能静态判定→脚本化"回灌判据沉淀）

| 脚本 | 拦截事故型 | 接入点 |
|---|---|---|
| `scope_check.py --check-history [--require-clean]` | 范围漂移 / reflog 历史改写（含 checkout 分支切换）/ **孤儿 tag** / **派单前工作区不干净**（V3.3 机检化"派单前先 commit"，剥夺执行器 checkout/stash 动机；注：`checkout -- <file>` 不写 reflog，由 require-clean+回归兜底） | Gate 2 首步；派发前置；中断条件 3/4 证据机检 |
| `gate_recorder.py --negative-selftest` | 门禁假绿：subprocess 直取退出码（无 shell 管道），失败探针先证"红会被记红"再记真实门禁；结果追加 gate_log.jsonl | Gate 0 建立；每 Gate 3/merge-gate 统一用它跑门禁；每 Phase ≥1 次真实用例负向抽检 |
| `cursor_check.py` | 游标错乱：6 条不变量（末行 gate==游标 / FAIL 必标 blocked / 不在已 PASS Sprint【防重做】/ next_action 非空 / STATUS 不落后 / **planned_sprints 游标前无 PASS=漏做**【V3.3 对偶方向】） | 崩溃恢复第二动作；Sprint 收尾自检 |
| `fixture_check.py` | 假测试四判中可静态判定部分：mock 自证（AST 无结果断言）、慢测试（sleep>1s）、手造形状字面量（顶层 dict/list 字面量启发式；嵌套形状差靠语义审查）、home/网络副作用、**F4 命名契约【V3.4 实装】：`re-<bugid>` 型回归测试必须在 fixtures/ 有对应真实 dump，缺=打回** | Gate 2 扫本 Sprint 新增测试；MUST_FIX=打回 |
| `value_check.py`【V3.4·C6】 | **取值纪律机检**：敏感值硬编码指纹、打码/省略号（U+2026/`***`）形态值写入代码、存储读取值与裸字面量目测比对——把"禁手抄显示值"从文字下沉为静态检查（真实事故型：省略号假故障排查数小时） | Gate 2 随 fixture_check 跑；merge-gate 可接入 |
| `heartbeat_check.py --scan --limit` | 卡死无人知：**双证据=文件 mtime（不可伪造）+ ts（未来 ts>60s 报 BROKEN 防绕过）**；STALE/BROKEN 即告警，主 Agent 自身失能也能报 | **战役启动时强制注册 cron（V3.4 起由"建议"改"强制"）**；Phase 边界手跑 |
| `arch_check.py --isolate [--via]` | **结构主张稀释**：AST 查跨 isolate 模块 import（经接口层的 import 因不在 isolate 集内天然豁免；绕行动态 import/间接耦合链靠审查语义兜底） | §6 checklist 涉解耦约束时 Gate 3 跑；FAIL=该条目证据不成立 |

| `gitguard.py -- git <cmd>`【V3.4·C1/C7】 | **git 只读白名单技术闸**：执行 agent 一切 git 调用强制经此，写动词（reset/checkout/commit/push/rebase/tag 创建/stash 写…）exit 2 拒绝并记 deny 审计，只读透传——git 写禁令从文字升级为拦截（10 组动词实测全对） | 派发契约第 5 要素的执行载体；主 Agent 安装为子 agent 的 git 包装 |

**已知机检边界（诚实登记，V3.4.2 按 Runner 实测两轮迭代）**：三件套/gate_log 写入原子性（无文件锁）、模型直连验证脚本、变更日志重放操作规程、gitguard 的 OS 级强制（依赖派单模板注入，直呼 git 真路径仍可绕——沙箱/hook 级未做）、"活着但死循环"心跳不老化问题（靠派发超时兜）、mtime 可被 touch 伪造（双证据仍弱于内核审计）——七项仍为流程/半机械条款。
【V3.4.2 修复】gitguard 白名单收紧（config/remote/symbolic-ref/reflog 移条件组，20/20 动词实测）；arch_check 相对 import 解析后比对（跨模块相对引用实测 FAIL）；fixture_check F4 在 fixtures/ 缺失时报违规不静默；value_check JS 走两趟行级判据（bad 抓到/good 不误报）。真实战役复跑中若产生事故证据优先将其脚本化。

### 执行循环

```
for Phase in Contract.phases:
  for Sprint in Phase:
    0. 重量门定档 L1|L2|L3（判档记入 gate_log）
    1. 探索（侦察蜂 delegate_task，便宜模型且经验证三则，只读，≤3 并行，按子系统目录切片，
       只按行号精读 40–100 行，禁整文件塞主上下文）
       熟悉仓库的单点定位直接 rg，不跑全仓脚本
    2. 开发（决策位开启时主 Agent 不亲自写；关闭时战斗蜂=核心逻辑主 Agent 亲自做。
       工兵蜂=execute_code 批量写，审计蜂 ≤3 并行只读）
    3. Gate 1 Pre-flight → Gate 2 Revision【scope_check --check-history 机检：
       diff 集合差 + reflog 历史改写 + 孤儿 tag，非空即阻塞】
       → fixture_check 扫本 Sprint 新增测试（MUST_FIX 命中=打回）
       → 方案符合度三查（范围/本期不做/必复用）→ 五维审查+假测试四判（L2/L3 独立干净上下文）
       → Gate 3 Integration【经 gate_recorder 执行：增量回归（Phase 边界全量），
          退出码直取+留痕，负向探针抽检每 Phase ≥1 次】
       → Gate 4 独立终审（Agent Team 3-agent，只读，区间制，含"对照 §6 checklist 约束逐条有证据"项；L1 跳过）
    4. FAIL：修复→按 §缺陷处置协议 走根因流程→重审；同 Gate 连续 3 FAIL → 中断上报
    5. PASS → 交付5件套 + 断点三件套更新 + cursor_check 自检 PASS → 自动进下一 Sprint
  Phase 边界: 跨 Phase 全量回归 + 10 行进度摘要 + 预算核对（token/Sprint/墙钟三轴都报）
            + heartbeat_check 手跑一次 + 轻量治理步（死链/文档新鲜度/孤儿测试/worktree 盘点）
战役结束: Gate 5 用户价值门 → 对照 §6 checklist 逐项 ✅⚠️❌📅 后才许声明"完成"
```

### 缺陷处置协议（Gate 失败与线上 bug 通用）

1. **先复现再动**：写失败测试（或可重复命令/手动步骤），确认它真的失败；没有复现不下结论、不宣布修好。
2. **找根因**：git bisect（临时 worktree 里跑）/ 从错误值往回追（模块边界加临时日志，交付前全删）/ 有对照则缩小差异。根因判据＝完整因果链每环对得上 `file:line` 且能解释全部现象（含为什么以前没出现）。**诊断期不改产品代码**。
   【V3.1·C6】**值来源纪律**（往回追的第一站常是观测层）：
   - 测试/排查涉及的一切常量（key/token/配置值/存储键）**禁止手抄工具或界面显示值**——显示层会把敏感形态值打码/省略号化/截断，省略号可能是 U+2026 真实内容而非截断；
   - 正确来源=从代码模块 import 常量、直调取值函数、或程序化 grep 原始文件；
   - 异常值出现时**先怀疑观测层（显示/转录/截断），再怀疑被测层**，两步排除后才许立"功能坏了"结论。
3. **修在源头**：在坏数据第一次产生处修。报错处加 try-catch/空判/sleep/放宽测试/多重同改——不算修复。
4. **个例 or 普遍**：问"为什么会写错"。普遍→全仓扫同写法命中点，≤5 处且非 high-risk 一起修+各补测试；超过则清单交用户或升级 L3。
5. **防再犯**：优先写成项目内确定性检查（接 scope 同族脚本、入 merge-gate）；判不出的才加一行审查重点进 AGENTS.md/REVIEW.md（注明来源案例；只命中一处不加）。
6. **止损**：连续两三个猜测被推翻或修两轮仍红 → 派两路独立只读会诊（不同 agent/不同上下文），对照结论；均无解且属边缘功能 → 提议砍功能/简化交互。

### 假测试与假夹具判据【V3.1·C3 修复，源自五维细则展开】

审查/验收新增测试时按四判逐条过（命中即 Must Fix）：
1. **夹具必须是真实输出 dump**：涉及引擎/接口返回结构的测试夹具，先实跑一次 dump 真实输出形状存入 `fixtures/`，以它为准；手造字段形状=掩盖渲染退化（`f.year` vs `f.date.year` 型事故）。
2. **mock 自证拦截**：把内部依赖全 mock 掉只测假返回值、全文无实质业务断言的"测试"不算测试。
3. **无副作用隔离**：塞固定秒数 sleep 拖慢回归、弹窗抢焦点、读写用户真实配置/数据、调用真实外部服务的用例 = 坏测试，重做。
4. **复现关**：缺陷回归测试必须先演示"修复前失败"再演示"修复后通过"，从未红过的"回归测试"直接拒收。
【V3.2】判据 1-3 中可静态判定的部分由 `fixture_check.py` AST 机检（mock 自证/sleep>1s/手造形状字面量/home 与网络副作用），Gate 2 对本 Sprint 新增测试文件默认扫描，MUST_FIX=打回；dump 来源与复现关仍需审查 agent 语义确认。
配套：门禁命令自身每年至少一次**负向测试**（故意红一条确认门禁报红，见 §9）。

### 防回归（长战役头号死法：后 Phase 破坏前 Phase）

- 测试套件累积不清零：每 Sprint 新增用例并入 `tests/regression/`
- 节奏分层：Sprint 内跑增量（新增+相邻模块），Phase 边界跑全量累积回归；破坏旧用例 = 新 P0，触发中断评估回滚
> 题源原型：某项目一个阶段的产出曾被复审 agent 的 git checkout 冲掉，全靠回归测试转红才发现——禁令自 V3.1 起扩展为**派发契约第 5 要素：对所有被派 agent 生效**，不只审计。

### 断点恢复（checkpoint 三件套，每 Sprint 边界必更新）

```
campaign/<id>/CONTRACT.md   # 冻结，修订走版本化 v1.1/v1.2
campaign/<id>/mission.json  # 机器态: 游标/gates/预算/未决项/worktree登记表/子Agent会话ID/心跳路径/next_action
campaign/<id>/STATUS.md     # 人读态: 滚动10条摘要+当前+下一步
```
新会话/压缩后/崩溃重启：第一动作=读三件套恢复游标，不许从头重做；
**第二动作=跑 `cursor_check.py --campaign-dir <dir>`**，PASS 才许按 next_action 续跑，BLOCK 先修游标（机检替代手工核对，V3.2·C9）。
【V3.1·C4】**三件套自身仓外副本**：每次 Sprint 边界更新三件套后，同步复制到仓库外备份目标（`campaign/<id>/` 本就应在项目目录之外；若在项目内则每次更新后 cp 到远端/外接盘指定路径）——否则"目录一删全灭"时游标同灭，恢复第一动作落空。
【V3.1·C10】**外部 watchdog**：主 Agent 可能自身卡死导致心跳无人读——长战役（>1 天）建议配 cron/守护任务定期扫心跳文件 mtime，超上限未更新即告警（能静态判定→脚本化，本条是自家回灌判据的应验项）。
【V3.1·C9 裁决空白修复】**冲突裁规则：mission.json（机器态）为唯一权威**，gate_log.jsonl 为第二证据；
与 STATUS.md 不一致时以 mission.json+gate_log 为准，恢复 STATUS 文字，反向（改机器态迁就人读态）禁止。
恢复后动手前必须先核对 gate_log 末行与 next_action 一致。
决策位模式下主上下文只装需求/方案/契约/子 Agent ≤15 行汇报——从源头防上下文污染导致的游标错乱。

### 中断上报（5 条，触发即停等用户）

1. 同 Gate 连续 3 FAIL
2. 预算熔断触顶（token/Sprint 数/墙钟；步骤超时连续 2 次也计入）
3. 范围膨胀：超出 Contract §1/§3（scope_check 脚本连续两轮报越界即算）
4. 触碰不可逆操作（按 §4 明文枚举清单判定，清单外疑似不可逆按最严档）——**上报前先派独立只读 Agent 回答三问：
   会影响什么/能不能撤回/有没有漏掉**，三问结论并入上报证据
5. 破坏性回归（旧用例大面积转红且非预期）

上报格式：现象 → 证据（gate_log/测试输出/独立三问结论）→ 选项 A/B → 建议。一次往返拍板。

## 独立性保障

- 测试/审计 agent 与开发不同上下文，只看产物+设计文档；审计只读
- 并行开发期**所有被派 agent** 禁 git checkout/stash/reset/restore/commit/push（派发契约第 5 要素）；审查范围区间制（tagX→tagY），派单前先 commit 当期成果
- 【V3.1·C5】**模型验证三则**（凡 pin 模型/通道，入 §8 偏好表或 Gate 0 核实前必过）：
  1. **直连端点验证，不经 fallback 链**——fallback 会把 A 通道的请求静默降级成 B 模型回答，"返回 OK"是假象；
  2. **回读响应体中的实际模型 ID**与指定 pin 值核对，不一致即通道不可信；
  3. **验证与使用同参数**（同 runner/同配置优先级）；汇报模板强制含"实际使用的模型"字段留痕。
  **自报复核**：子 Agent 汇报"实际模型"字段属自报，主 Agent 须以网关/会话记录抽查核对至少 1 次每 Phase（自报字段不可单独作为完成证据，同"外部自报不能替代真实测试"条款）。
- 独立审查返回的每条 Must Fix，主 Agent 回读对应代码确认成立再交用户/执行方（防误报）
- P0 修复后重审，迭代到 P0=0
- 外部 CLI Agent 的自报结果不能替代工作区检查与真实测试；发出去的任务文本可能进入第三方 provider，**不含密钥/凭据**

## 进度可观察

- 每 Sprint 边界：STATUS.md + `gate_log.jsonl` 追加（含重量门判档、scope_check 结果、心跳摘要）
- 每 Phase 边界：10 行摘要（做了什么/证据/下一步/**三轴预算%**）+ 轻量治理步输出
- 用户中途改需求 = Contract 修订（版本化）→ Gate 0 增量评审 → 继续
- （可选）分支看板：mission.json 记录各 worktree/分支状态，随时可渲染

## 收尾

1. 对照 Contract §2 全 Phase × 全功能逐项 ✅⚠️❌📅（<80% 不说完成）
2. 对照 Contract §6 约束证据 checklist：C1..Cn 每条有证据链接，无证据=未验收
3. 全量回归绿 + gate_log 完整 + 所有 worktree 已合并或经确认清理
4. 交付4件套（commit+tag / 文件备份 / 记忆库项目条目 / 会话记录）
5. delivery-retrospective 复盘 + 教训回灌。**回灌判据**：先问这条教训能否写成确定性检查/脚本，
   能→写进目标仓库 merge-gate；不能→才写进 skill 文字。同时执行**规则新陈代谢**：
   误报为 0 触发或被脚本接管的文字规则→提议删除。

## PITFALLS

- 把"不用等确认"理解成取消 Gate/取消防回归——授权的是**节奏**，不是**质量门**。
- Gate 0 流于形式：没有可机检验收标准就 PASS 了个寂寞。
- **小事大做**：L1 级修补走了 L3 全套流程 = 预算黑洞。
- **每改两行跑全量**：全量回归只在 Phase 边界；写码期间只跑秒级 static-check。
- 范围漂移只靠审计 agent"看着办"：必须跑 scope_check 脚本做集合差。
- Contract §9 没实测就冻结：测试命令/glob 与仓库真实状态脱节，整役继承错误前提。
- 【V3.1】**门禁自己假绿**：`cmd | tail; echo $?` 取的是尾命令退出码——门禁命令必须声明取码方式并做一次负向测试（故意红一条确认报红），否则整役的 Gate 3 是纸糊的。
- 【V3.1】**手造夹具测绿掩盖退化**：夹具字段形状与引擎真实输出不符，"回归测试"永远绿。先 dump 真实输出再写测试；从未红过的回归测试直接拒收。
- 【V3.1】**目测抄值**：工具/界面把敏感形态值打码或省略号化（而 U+2026 可能是真实内容），手抄导致假故障排查数小时。常量一律程序化从代码直取；异常值先怀疑观测层再怀疑被测层。
- 【V3.1】**静默降级假验证**：指定 provider 返回 OK，实际是 fallback 链另一模型在答——成本估算与能力结论全错。pin 模型必过验证三则（直连+回读 ID+同参数）。
- 【V3.1】**禁令不写适用对象**：`git reset --soft` 折掉两个提交、发布 tag 孤儿化——审计禁令救不了修复 agent。写禁令必须点名"对哪些 agent 生效"；agent 一律不碰 git 写操作。
- 【V3.1】**卡死无人知**：墙钟总闸之外必须有事前检测——子 Agent 超时上限+心跳文件；token 预算没触顶不代表时间没卡死。
- 【V3.1】**仓库没 git 就开役**：目录一删全灭，只剩外接盘旧备份。Gate 0 开工前提=git 化+备份目标可用。
- 【V3.1】**状态文件冲突无裁规则**：三件套不一致时以 mission.json+gate_log 为准，禁止反向迁就。
- mission.json 与 STATUS.md 不同步 = 恢复游标错乱。一起更新。
- 探索/审计蜂用主模型单价跑 = 成本可砍一半不做；侦察蜂必须显式 pin 便宜档（且经验证三则）。
- 主 Agent 亲自读遍源码"顺手改两行"（决策位开启时）：上下文污染正是断点错乱成因。
- 开发 agent 自审图快：独立性最低成本形态=不同上下文 leaf agent。
- Contract 冻结后口头打补丁 → 一切修订走 CONTRACT.md 版本化。
- 教训回灌只加文字规则不加脚本、只加不删 → skill 膨胀到无人读，等于没有。
- **两版漂移**：改了本机版协议逻辑没同步开源版 → 两路径各做同样 patch 并复跑隐私扫描。
- **评测出题偏置**：从被测文档"对称取并集"倒推题目会让融合版虚高（V3.0 实测 97.5→66）。考题必须来自文档外的真实事故，判据中立预写。
