# Work OS 使用手册

> 适用版本：v1.8.0（Gatekeeper v0.2）｜ 面向对象：第一次接触本体系的人
> 配套视觉文档：`docs/system-guide.html`（体系分层图 + 主流程图，浏览器直接打开）

---

## 0. 这是什么，解决什么问题

AI Agent 通常"会做事，但没人逼它把事做完、做诚实"。Work OS 是一套**执行纪律系统**，
装进你的 Agent 宿主后，它会在每个任务上强制六个动作：

1. 动手前先输出 **[路由] 决策块**（分类/复杂度/模式，5 行）
2. L3+ 复杂任务**先写 PLAN，等你批准**才开工
3. 按 Sprint 分段执行，每段过 **Gate**（检查不过不许进下一段）
4. 声称完成前必须 **commit + 逐项验证清单**（✅⚠️❌）
5. 完成度 <80% **不许说"完成"**
6. 每次任务教训**写回记忆库**，越用越锋利

一句话：**Skill 决定它知道什么，Agent 决定它怎么想，Harness 决定它能不能跳过。**
前两层靠文本协议，第三层（Gatekeeper CLI + 宿主 hook）用代码拦截——纪律不再靠自觉。

---

## 1. 安装

### 1.1 Hermes 宿主（完整体系，一条命令）

```bash
git clone https://github.com/sean2010zhang-star/work-os
cd work-os && ./install.sh
```

装完你会得到：
- 隔离 profile `~/.hermes/profiles/work-os`（SOUL.md 协议 + 48 skill + 记忆种子）
- **harness 自动接线**：profile `config.yaml` 追加真实 hook 块（pre_tool_call 硬拦截 + pre_verify 完成度门）
- 你自己的模型配置被复制（仓库永不携带任何 key；如 api_key 是占位符，跑一次 `hermes -p work-os model` 补上）
- 首次对话自动进入**偏好采访**（3-6 问，回答后写入 `偏好.md`；说"跳过引导"可略过）

激活：`hermes profile use work-os`（单轮试：`hermes -p work-os chat`）

⚠️ **一次性 consent**：首次启动 hook 时宿主会弹窗询问是否批准 gatekeeper 命令——
这是 Hermes 的安全设计（只认人类批准），你批准一次即可；无 TTY 环境可在
config.yaml 设 `hooks_auto_accept: true` 或启动加 `--accept-hooks`。

### 1.2 Claude Code（真实 hook 硬拦截）

```bash
/plugin marketplace add sean2010zhang-star/work-os
/plugin install work-os@work-os
```

再在你的项目里接 harness（获得代码级拦截，而不是提示词自觉）：

```bash
cd your-project
python3 <work-os仓库路径>/gatekeeper/gatekeeper.py init --host claude_code
python3 <work-os仓库路径>/gatekeeper/gatekeeper.py doctor    # 必须 ALL GREEN
```

这会写入 `.claude/settings.json`：PreToolUse + Stop hook。被拦时模型收到的是
**它违反的那条铁律原文**，它会自己绕道解决而不是硬闯。

### 1.3 其它任意宿主（Codex / Trae / WorkBuddy / Cursor…）

```bash
python3 <仓库路径>/gatekeeper/gatekeeper.py init --host codex|trae|workbuddy|generic
```

适配器会打印/写入该宿主支持的**最强形态**（AGENTS.md 块、.trae/rules、SOP 注入、
提示词粘贴），并如实告诉你哪些是提示级、哪些是代码级。同一内核，同一
`.gatekeeper/` 状态格式——一套大脑六个插头。

### 1.4 首跑验收（2 分钟，判断装没装对）

对 Agent 说：

> 给我的 Flask 应用加认证，并做一个 React 登录页

**正确行为**：写任何文件之前，先输出 `[路由] 分类=代码 | 复杂度=L3 …` 决策块，
然后给你一份带"可证伪验收判据"的 PLAN 等你确认。做不到 = 安装未生效，见 §7 排障。

---

## 2. 日常怎么用（按任务大小）

### 2.1 小任务（L1-L2：查询、改 1-2 个文件）

直接说事。Agent 输出路由块后**不等确认直接做**。你什么都不用管。

### 2.2 中型任务（L3：多文件、多步骤）

流程固定为 **写方案 → 你确认 → 执行 → Gate → 交付**：

```bash
# Agent 会写 PLAN.md；你在真实终端里批准（只有人类能开闸）：
python3 gatekeeper/gatekeeper.py approve PLAN.md
```

批准后 Agent 连续执行，不再逐次问你。跑完它必须 commit 并交出逐项验证清单。

**想让它全程自主？** 直接说"自行判断后执行，不用等确认"——对 L3 这会放行执行，
但 harness 仍然拦：无批准 PLAN 的写操作、脏工作区声称完成等照样被 deny。
"不用等确认"≠"没有边界"。

### 2.3 大型长程任务（L4：全量开发、通宵自主跑）

说"**全量开发，自行执行直到完成**"类授权，Agent 加载**长程战役协议**
（longrun-campaign），和你签一份 **Mission Contract**（10 节合同）：

| 合同节 | 内容 | 你的责任 |
|--------|------|----------|
| §1-3 | 目标/范围/验收判据（可证伪） | 签前逐条看清 |
| §4 预授权 | 允许它自主做的动作清单 | **永不预授权**：删数据/force-push/花钱/部署 |
| §5 预算熔断 | token 数/Sprint 数/墙钟时间上限 | 定一个你能接受的止损线 |
| §6 验收 | 每条判据 + 证据要求（无证据=未验收） | 事后逐项核对 |
| §8 派发偏好 | 用什么子代理/模型跑哪类活 | 一般照默认 |

签完合同 = 铁律 1 的那次确认已完成，Agent 通宵跑。五种情况它**必须停下来找你**：
Gate 三连 FAIL、预算触顶、范围膨胀、不可逆操作、破坏性回归。中断时进度存
CONTRACT/mission.json/STATUS 三件套，随时断点续跑。

---

## 3. Gatekeeper 命令速查

```bash
GK="python3 <仓库路径>/gatekeeper/gatekeeper.py"

$GK init --host <host>      # 接入宿主（见 §1）
$GK doctor                  # 负向自检：每条 deny 先证明拦得住违规才可信
$GK route --complexity L3 --role developer   # 记录路由决策（对应 [路由] 块）
$GK approve PLAN.md         # 人类专属：批准方案（TTY 或签名文件）
$GK status                  # 看当前会话状态（复杂度/批准/ack/override）
$GK report                  # 规则触发统计 + 过时规则提示（规则新陈代谢）
$GK verify-done             # 交付前自查：commit 新鲜+工作区干净+清单存在
$GK stop                    # 完成度门（宿主 hook 自动调，也可手动预检）
$GK ack --rule <id> --reason "≥10字理由"   # 书面豁免一条"建议级"规则
```

**人类专属、Agent 无法自用的命令**：`approve`、`override`。非交互调用一律拒绝并
记入 append-only 审计（gatekeeper 的核心性质：Agent 不能给自己开绿灯）。

### 默认拦截什么（5 条规则 = 铁律的代码形态）

| 规则 | 时机 | 强度 | 拦截场景 |
|------|------|------|----------|
| iron-1 | 写文件前 | **deny** | L3+ 无批准 PLAN |
| iron-11 | Bash 前 | **deny** | auditor/review 角色跑 git 写命令（防"checkout 冲掉别人未提交工作"） |
| iron-3 | 声称完成 | **deny** | 脏工作区 / 无本次 commit / 无 ✅⚠️❌ 清单 |
| done-gate | "done" 动词 | **deny** | 未过 verify-done；且**拦截必须引用具体失败铁律**（反假拦截公约：harness 只许拦，不许耍赖） |
| iron-0 | 首个动作前 | require-ack | 未路由就动手（跳过需书面理由） |

自定义：`.gatekeeper/rules.json` 可编辑（加严或裁剪），改完必跑 `doctor`。

---

## 4. 记忆闭环（让它越用越锋利）

安装即带四件套种子（`memory/` 或 profile 记忆区）：

```
_INDEX.md      总索引（先读这里）
偏好.md        你的风格约定（首跑采访生成）
工作流规范.md   标准流程 + 事故教训
决策记录.md     重要决策留档（为什么选 A 不选 B）
```

- **每个任务前**：Agent 先读 `_INDEX.md` + `偏好.md`（SOUL 强制）
- **每个任务后**：有新偏好/决策/流程变化 → 主动写回对应文件并更新索引
- **新坑**：教训写进对应 skill（下次同类任务自动加载），不只写 memory

效果分层（诚实口径，详见 `docs/effectiveness.md`）：纪律层 ≈100% 即装即得；
方法库 ~90%；记忆层从 0 开始、使用 2-4 周后成型；垂直领域资产有意不包含（需自建）。

---

## 5. 质量门与验证清单（你收到的每个"完成"长什么样）

每个 Sprint 交付都带一份逐项清单：

```
- [x] 登录接口联调 ✅ 证据：curl 返回 200 + token 校验日志（附复现命令）
- [⚠] 移动端适配  ⚠ 证据：视口 375px 截图，但深链未测
- [❌] 导出 PDF    ❌ 未做，原因：依赖库缺，列入下 Sprint
```

规则：**"完成度 <80% 不许说完成"**；每条结论必须带**别人可复跑的证据**
（命令/路径/数字同源）。审计代理只读、不许碰 git 写命令——这条由 harness 强制。

---

## 6. 运维与发布（项目方）

```bash
./release.sh v1.8.0     # 发布闸：git archive 导出→内容级隐私扫→版本一致性→导出内跑 27 条测试→zip
```

- 分发**永远走 `git archive`/release.sh**，不要直接 zip 目录（会带上 __pycache__ 里的绝对路径）
- 两套宿主测试：`gatekeeper/test_gatekeeper.py`（15 引擎）+ `test_adapters.py`（12 适配/协议）
- 改动纪律：协议逻辑变更需本机版与发布版同步 + 全树隐私复扫 0 命中后才 commit+tag

---

## 7. 排障 FAQ

**Q：Agent 没输出 [路由] 块？**
A：确认激活了 work-os profile（`hermes profile list`）；Claude Code 确认插件已 install。
跑 `hermes -p work-os chat` 单轮验证 SOUL 是否加载。

**Q：Hermes 启动时弹 hook consent 询问？**
A：设计如此（宿主安全机制），你（人类）批准一次；或 config.yaml 设 `hooks_auto_accept: true`。

**Q：被 harness deny 了，但我就是要做？**
A：说明它撞了哪条铁律。合法路径：小任务用 `route --complexity L1/L2`；方案任务
`approve PLAN.md`（真实终端）；确实要破例用 `override --reason "..."`（同样只认人类），
破例记录进 append-only 审计，不会被抹掉。

**Q：approve 提示"no interactive TTY"？**
A：无终端环境（cron/CI）下人类可预先放置签名文件：`echo '<你的暗号>' > .gatekeeper/user_signature`。

**Q：安装脚本报 rsync 缺失？**
A：v1.8 起自动降级 `cp -R` 路径，不会中断。

**Q：docx/pptx/xlsx 技能脚本报 SyntaxError？**
A：那些脚本用 `match` 语句，需 Python ≥3.10（Hermes 自带 3.11 即可；系统 python3.9 不行）。

**Q：想卸载？**
A：`./install.sh --uninstall`（删 profile）；宿主项目里删 `.gatekeeper/` + 还原
`.claude/settings.json` 的 hooks 段即可，gatekeeper 不碰其它任何东西。

---

## 8. 术语表

| 术语 | 含义 |
|------|------|
| L1-L4 | 复杂度档位（免确认→并行→PLAN 确认→战役合同） |
| Sprint / Gate | 分段执行 / 段间质检门（G1 文件存在…G5 用户价值） |
| PLAN / Mission Contract | 中型任务的方案 / 长程战役的 10 节授权合同 |
| Harness | 宿主 hook 层——把铁律变成代码拦截（gatekeeper） |
| done-gate / 反假拦截公约 | 拦"完成"必须引用具体失败铁律；harness 只许拦不许耍赖 |
| 规则新陈代谢 | `report` 统计规则触发频次，僵尸规则建议降级/脚本化/删除 |
| fail-closed | hook 超时/崩溃时默认拦截而非放行（Hermes 适配器启用） |

---

*手册与代码同源：v1.8.0 实测行为。发现手册与实物不符，按体系纪律这本身就是 P1 bug——欢迎 issue。*
