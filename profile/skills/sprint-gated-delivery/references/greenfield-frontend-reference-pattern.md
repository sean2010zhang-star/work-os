# Greenfield Frontend: Reference Code as Implementation Guide

> 实测。用户提供参考前端zip(<reference-frontend>.zip)，
> 基于此进行"前端的完善和丰富"。

## Pattern

When user provides a reference frontend (zip/tar/clone):

1. 解压到临时目录 /tmp/project-ref/
2. 分析参考代码: package.json(types.ts(App.tsx(components/(server.ts(constants.ts
3. 提取设计语言: 色彩方案/组件模式/交互模式
4. 迁移策略: 保留视觉DNA + 升级框架 + 补充后端 + 模块化拆分

## Pitfalls

- 参考代码AI密钥: 迁移时通过config统一管理
- Mock数据: 200行fallback应抽离为独立模块
- CSS非标准色值: slate-550等替换为标准色值
- 状态管理: useState膨胀后立即引入Zustand
