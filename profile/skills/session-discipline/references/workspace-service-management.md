# Workspace服务管理API模式

## 背景
在workspace_api.py中实现了一键启动/停止项目后端服务的机制。

## 核心设计

### 服务注册表 (SERVICES dict)
```python
SERVICES = {
    "service-id": {
        "name": "显示名称",
        "cwd": "工作目录",
        "cmd": ["启动命令", "参数"],
        "port": 3001,
        "url": "http://localhost:3001",
        "health_url": "http://localhost:3001/api/health",
    }
}
```

### API端点
- `GET /api/services` — 列出所有服务+实时状态(端口探测)
- `POST /api/services/start` — 后台线程启动服务，等待端口就绪
- `POST /api/services/stop` — 终止进程+kill端口
- `POST /api/services/health` — 单次端口健康检查

### 前端交互流程
```
卡片点击 → POST /api/services/start
         → 每500ms轮询 POST /api/services/health
         → 端口就绪 → window.open(url)
         → 超时30s → 提示手动打开
```

### 关键实现
- `_start_service()` 用 `subprocess.Popen` 在后台线程启动
- `_check_port()` 用 socket 探测端口
- `_kill_port()` 用 lsof+os.kill 终止
- 进程管理: `_service_procs` dict 跟踪进程
- 状态管理: `_service_status` dict 跟踪状态(starting/running/stopped/error)
