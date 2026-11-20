# 多产品全量化升级 Sprint 编排模板

> 来源: 五产品v2.0升级实测(12 Sprint全部PASS)

## Sprint 编排结构

当同时升级N个产品时，推荐以下编排：

```
Sprint 1:  版本备份 + 架构基线文档(API契约/设计系统/DB Schema)
Sprint 2:  共享基础设施(认证中心/产品门户/SSO)
Sprint 3-4:  产品A升级(数据层+功能)
Sprint 5-6:  产品B升级(前端+后端)
Sprint 7-8:  产品C升级(模型精简+功能完善)
Sprint 9-10: 产品D升级(引擎+前端)
Sprint 11: 全产品联调 + 跨系统对接验证
Sprint 12: 外部审计 + Git tag + 四层备份
```

## 每个Sprint的Gate检查项

### 后端Sprint Gate
- [ ] Python syntax: `python3 -m py_compile` 每个修改的.py
- [ ] 新文件存在且非空
- [ ] 数据库迁移成功(Prisma: `npx prisma db push`)
- [ ] 核心API端点返回正确结果

### 前端Sprint Gate
- [ ] Build通过: `npm run build`
- [ ] 新页面文件存在且行数合理(>100行)
- [ ] JS语法检查通过(如适用)
- [ ] 侧边栏/导航已更新

### 联调Sprint Gate
- [ ] 每个产品独立可启动
- [ ] 跨产品跳转/调用正常
- [ ] Health端点全部返回200
- [ ] API契约合规检查

## 子agent超时处理模式

当delegate_task超时时，按以下策略拆分：

1. **大文件读取型任务** — 先从主agent用grep/find定位精确行号，再delegate具体修复
2. **多文件修改型任务** — 拆为每2-3个文件一个子agent
3. **Schema迁移型任务** — 拆为: (a)写新schema (b)修复引用 (c)验证build 三步
4. **全产品扫描型任务** — 不用delegate，用execute_code串行扫描

## 四层备份检查清单

```bash
# Git
for dir in product1 product2 product3; do
  git -C $dir tag -l "vX.Y.Z"
  git -C $dir status --porcelain | wc -l
done

# 外部存储
ls -lh <mount-point>/*/hermes-backup/vX.Y.Z-YYYYMMDD/

# 记忆库
ls <vault>/{项目}.md

```
