# 侧边栏+步骤流程 — 前端架构模式

## 适用场景
数据驱动的多步骤工作流应用（评审、审批、分析报告生成等）

## 架构
```
┌─────────┬────────────────────────────┐
│ Sidebar │    Main Content Area       │
│ (fixed) │    (scrollable)            │
│         │                            │
│ Step 1  │    [当前步骤内容]           │
│ Step 2  │                            │
│ Step 3  │    根据activeStep切换       │
│ Step 4  │    渲染对应组件             │
│         │                            │
│ ─────── │                            │
│ History │                            │
└─────────┴────────────────────────────┘
```

## 核心状态
```typescript
type StepKey = "step1" | "step2" | "step3" | "step4" | "history";

const [currentStep, setCurrentStep] = useState<StepKey>("step1");
const [completedSteps, setCompletedSteps] = useState<Set<StepKey>>(new Set());
```

## Step状态三态
- **completed**: 绿色check图标，可点击回看
- **current**: 蓝色高亮，带描述文字
- **locked**: 灰色，不可点击（前置步骤未完成）

## 导航逻辑
```typescript
// 只有前一步完成或当前步骤才可点击
const isClickable = isCompleted || isCurrent 
  || idx === 0 
  || completedSteps.has(STEPS[idx - 1]?.key);
```

## 用户偏好
- 不要顶部Tab切换 → 用左侧sidebar导航
- 不要手动输入表单作为独立tab → 纯文档驱动流程
- 每步骤有"下一步"按钮引导流程
- 历史记录作为独立section放在sidebar底部

## 暗色主题配色
- Sidebar: `bg-[#0a0d10]` (比主背景更深)
- 主内容: `bg-[#0e1416]`
- 卡片: `bg-white/[0.03] border-white/10`
- 步骤指示器: `bg-blue-600`(当前) / `bg-green-600/20`(完成) / `bg-white/[0.05]`(待解锁)
