# 全栈集成审计模式 (实测)

## 问题
Gate 1/2 只验证文件存在+语法通过，不验证前后端是否真正打通。
结果: 8个Sprint全部PASS，但需求审查完成度仅45%。

## 解决方案: Gate 3 + Gate 4

### Gate 3: 前后端打通验证
```bash
# 检查前端组件是否调用后端API
grep -rn 'API\.\|api\.' web/src/components/ --include='*.tsx' | wc -l
# 检查是否有mock数据
grep -rn 'setTimeout\|MOCK_\|mock' web/src/components/ --include='*.tsx'
# 检查api.ts是否有对应定义
grep -rn 'export const.*API' web/src/services/api.ts
```

### Gate 4: 需求-功能对比审查
1. 读取设计文档中的功能清单
2. 对每个功能标记: ✅完全 / ⚠️部分 / ❌未实现 / 📅推迟
3. 计算完成度 = (完全+部分) / (总数-推迟)
4. 完成度<80% → 继续补齐，不声称完成

### Agent Team需求审查Prompt模板
```
读取产品设计文档{path}，提取所有功能点。
对每个功能，检查后端是否有API端点、前端是否有页面、前端是否调用了后端API。
输出完成度百分比和缺失功能清单。
```

## P0审计循环模式
```
审计 → 修复 → 重审 → 修复 → 重审 → P0=0
```
每次修复可能引入新问题:
- import改名后引用未更新 (uuid → uuid_mod)
- duplicate代码未删干净 (双重LLM调用)
- 时区不一致 (datetime.now(timezone.utc) vs datetime.utcnow())
- null字节 (patch操作引入)

## 常见P0修复陷阱
| 陷阱 | 案例 | 预防 |
|------|------|------|
| 改名不全 | uuid改uuid_mod但L77仍用uuid.UUID | 改名后全局grep验证 |
| 旧代码残留 | 用量检查换了新函数但旧代码没删 | 重写整个函数而非patch |
| 时区不一致 | usage.py用aware, model用naive | 统一用datetime.utcnow() |
| null字节 | write_file引入\0字节 | 写后python3检查 |
| 未集成 | 创建了usage.py但router没import | grep确认被import |
