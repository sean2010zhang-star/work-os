# 侧边栏步骤导航模式

> 适用于文档驱动的多步流程应用（评审、审批、数据处理pipeline）

## 组件结构

```
src/components/layout/Sidebar.tsx  — 固定左侧240px导航
src/app/page.tsx                   — 主内容区按step切换
```

## Sidebar.tsx 核心

```tsx
export type StepKey = "step1" | "step2" | "step3" | "step4" | "history";

interface SidebarProps {
  currentStep: StepKey;
  completedSteps: Set<StepKey>;
  onStepClick: (step: StepKey) => void;
}
```

### 步骤状态三态
- **completed**: 绿色勾图标，可点击回看
- **current**: 蓝色高亮+圆角边框，右侧箭头
- **locked**: 灰色不可点击（前序步骤未完成）

### 点击逻辑
```tsx
const isClickable = isCompleted || isCurrent 
  || idx === 0 
  || completedSteps.has(STEPS[idx - 1]?.key);
```

### 底部统计
侧边栏底部显示关键指标（引擎数、文件数等）

## page.tsx 状态机

```tsx
const [currentStep, setCurrentStep] = useState<StepKey>("step1");
const [completedSteps, setCompletedSteps] = useState<Set<StepKey>>(new Set());

const markCompleted = (step: StepKey) => {
  setCompletedSteps(prev => new Set([...prev, step]));
};

// 步骤完成时自动跳转下一步
const goToNext = () => {
  markCompleted(currentStep);
  const idx = STEPS.findIndex(s => s.key === currentStep);
  if (idx < STEPS.length - 1) setCurrentStep(STEPS[idx + 1].key);
};
```

## 设计规范 (FlowForge暗色)

```
侧边栏: bg-[#0a0d10], border-r border-white/5
步骤指示器: w-7 h-7 rounded-full
  completed: bg-green-600/20 text-green-400
  current: bg-blue-600 text-white
  locked: bg-white/[0.05] text-gray-600
主内容区: ml-60 px-8 py-6
品牌区: 顶部带logo+版本号
```

## 适用场景

- 招标文件→投标文件→评审→结果（本项目）
- 数据采集→清洗→分析→报告
- 需求→设计→开发→测试→部署
- 任何有明确前后依赖的多步流程
