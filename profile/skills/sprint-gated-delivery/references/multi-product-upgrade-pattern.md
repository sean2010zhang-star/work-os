# 多产品全量化升级模式 (实测)

## 编排模式: 12-Sprint Multi-Product Upgrade

适用于：同时升级3-5个独立产品，需要统一品牌+跨产品对接+数据层重构。

### Sprint编排

```
Sprint 1:  版份备份 + 架构基线(3个设计文档)
Sprint 2:  共享基础设施(认证中心+产品门户+SSO)
Sprint 3-4: 产品A升级(数据层+功能)
Sprint 5-6: 产品B升级(前端+后端)
Sprint 7-8: 产品C升级(模型精简+功能完善)
Sprint 9-10: 产品D升级(引擎+前端)
Sprint 11: 全产品联调
Sprint 12: 审计+文档+Git tag
```

### 关键模式

1. **Sprint 1 必须先备份** — Git tag + zip压缩包。后续任何Sprint出问题都可回退。
2. **Sprint 2 做共享层** — 认证/门户/设计系统/统一API契约。产品间对接依赖这些。
3. **每个产品1-2个Sprint** — Sprint 3-4做数据层+基础功能，Sprint 5-6做高级功能。
4. **联调Sprint必须有** — 跨产品API调用、认证token传递、健康检查。
5. **最终Sprint做审计** — Python syntax + next build + py_compile + Git tag v2.0.0。

### 子agent任务拆分策略

| 任务类型 | 推荐粒度 | 原因 |
|----------|---------|------|
| 创建新文件 | 3-4个文件/task | 子agent需要读上下文再写 |
| 修改现有文件 | 2-3个文件/task | 需要先读完整文件再patch |
| Prisma schema迁移 | 先schema→再引用清理 | 两步串行，不可并行 |
| 前端页面创建 | 4-6个页面/task | 页面是独立的，可并行读组件 |
| 后端API+引擎 | 1个模块/task | 引擎代码复杂，需要深度理解 |

### Prisma Schema迁移陷阱

当从schema中移除模型时：
1. `npx prisma db push --accept-data-loss` 会删除表
2. 所有引用被移除模型的文件都会报TS错误
3. 必须搜索并修复: seed.ts, validation-test.ts, API routes, frontend pages
4. 简单方案: 将旧模型引用的脚本加入tsconfig.json的exclude
5. 关联字段修复: 添加缺失的反向relation (如Evaluation→Function)

### Google Fonts离线问题

Next.js `next/font/google` 在无网络环境下构建失败。修复：
- 移除 `import { Inter } from "next/font/google"`
- 移除 `const inter = Inter({...})`
- body className改为 `"antialiased"` (不引用font变量)
- CSS中使用系统字体回退: `font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

### 交付4件套(最终Sprint)

1. Git commit + tag (v2.0.0)
2. 审计报告 (~/Desktop/audit/audit_YYYYMMDD_v2-upgrade.md)
3. 压缩包备份 (~/Desktop/backup-YYYYMMDD/)
4. 设计文档 (API契约+设计系统+DB Schema)
5. 启动命令汇总
