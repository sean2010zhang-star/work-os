# API 集成模式

## FastAPI路由注册模式

```python
# api/app/api/v1/__init__.py
from app.api.v1.experiments_v5 import router as experiments_v5_router
api_router.include_router(experiments_v5_router, prefix="/experiments/v5", tags=["experiments-v5"])
```

## Engine -> API 连接模式

```python
# 路由文件中懒导入引擎模块(避免循环依赖)
@router.post("/start")
async def start_experiment(req, user=Depends(get_current_user)):
    from app.services.engine_v5 import ExperimentEngineV5
    engine = ExperimentEngineV5(resume=req.resume_text, tier=req.tier)
    result = engine.run()
    return result
```

## Agent Team审核发现的典型P0问题

| 问题 | 文件 | 修复 |
|------|------|------|
| 内存存储(_experiments = {}) | experiments_v5.py | 替换为SQLAlchemy |
| IDOR漏洞(无user_id过滤) | experiments_v5.py | 查询时加user_id条件 |
| Tier门控bug(walrus operator) | skills_v5.py | `if req.tier in ("pro","vip"):` |
| 跨模块私有变量耦合 | reports.py | 抽象数据访问层 |
| 无response_model | 所有路由 | 定义Pydantic response model |

