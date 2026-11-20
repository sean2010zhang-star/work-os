# delegate_task超时模式与规避

## 核心铁律
**delegate_task绝不用于批量文件创建(200+行/文件必超时)。**

## 实测数据

| 任务 | 方式 | 耗时 | 结果 |
|------|------|------|------|
| 6文件×200行(B2B前端) | delegate_task | 600s | ❌ 超时 |
| 14个子页面(C2C前端) | delegate_task | 600s | ❌ 超时 |
| 14个子页面 | execute_code | 15s | ✅ |
| 45个组件(5×9系统) | execute_code | 54s | ✅ |
| 9个设置页 | execute_code | 13s | ✅ |
| 5个集成测试 | execute_code | 7s | ✅ |

## 超时根因
- delegate_task有600s硬超时
- 每个200+行文件需要: 读上下文+生成内容+write_file+验证
- 6文件 = 1200行内容生成 ≈ 500-700秒 → 必超时

## 正确模式

### execute_code用于(快速批量):
```python
from hermes_tools import write_file
for name, content in files.items():
    write_file(path, content)
```

### delegate_task用于(独立审核):
```python
delegate_task(
    goal="审核9个系统的代码质量...",
    toolsets=["file"]  # 只读，不写
)
```

## 反模式
- ❌ delegate_task创建6+个大文件(必超时)
- ❌ delegate_task做批量前端页面(必超时)
- ❌ 超时后重试同样方式(还是超时)
- ✅ 超时后改用execute_code(秒级完成)
