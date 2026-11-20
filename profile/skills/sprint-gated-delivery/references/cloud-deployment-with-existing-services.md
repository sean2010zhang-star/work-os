# Cloud Deployment with Existing Services Pattern

## Problem
Deploying a new system to a server that already has production services running. Must not affect existing services.

## Verified: production deployment on your cloud provider (<your-server-ip>8)
- Existing: a legacy service on port 3010 (uvicorn)
- New: example backend on port 8002, frontend on port 3009
- Both running independently, no conflicts

## Deployment Steps

### 1. Pre-deployment reconnaissance
```bash
ssh ubuntu@server "ss -tlnp"  # Check occupied ports
ssh ubuntu@server "free -h && df -h /"  # Check resources
ssh ubuntu@server "python3 --version && node --version"  # Check runtimes
```

### 2. Package locally, upload, extract
```bash
# Local: pack excluding venv/node_modules/.git
tar czf /tmp/myapp-backend.tar.gz --exclude='backend/.venv' --exclude='.git' backend/ shared/
scp /tmp/myapp-backend.tar.gz ubuntu@server:/tmp/

# Remote: extract to independent directory
ssh ubuntu@server "mkdir -p ~/myapp && tar xzf /tmp/myapp-backend.tar.gz -C ~/myapp/"
```

### 3. .env management — CRITICAL
**Pitfall**: tar extraction overwrites .env with local development values.

Solution: Upload .env separately AFTER tar extraction:
```bash
# Generate strong keys
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Create cloud .env
cat > /tmp/myapp-cloud.env << EOF
DATABASE_URL=sqlite+aiosqlite:///./myapp.db
SECRET_KEY=$SECRET_KEY
JWT_SECRET=$JWT_SECRET
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=["http://server-ip:3009"]
EOF

# Upload and set permissions
scp /tmp/myapp-cloud.env ubuntu@server:/tmp/
ssh ubuntu@server "cp /tmp/myapp-cloud.env ~/myapp/backend/.env && chmod 600 ~/myapp/backend/.env"
```

### 4. systemd services (independent from existing)
```ini
# /etc/systemd/system/myapp-backend.service
[Unit]
Description=<app> Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/myapp/backend
ExecStart=/home/ubuntu/myapp/backend/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 5. Frontend proxy (server.ts) must point to correct backend port
```typescript
const BACKEND_URL = "http://localhost:8002";  // NOT 8001
```

### 6. Verify independence
```bash
# Both services must return healthy
curl http://localhost:3010/health  # Existing service
curl http://localhost:8002/health  # New service
ss -tlnp | grep -E '3010|8002|3009'  # All ports listening
```

## Security Checklist
- [ ] .env permissions 600 (not 644)
- [ ] ENVIRONMENT=production set
- [ ] SECRET_KEY/JWT_SECRET randomly generated (not defaults)
- [ ] CORS restricted to specific IPs
- [ ] No hardcoded secrets in code defaults

## Pitfalls
- **tar overwrites .env**: Always re-apply cloud .env after tar extraction
- **SQLite JSONB**: Use `JSON` not `JSONB` from sqlalchemy
- **SQLite UUID**: Use custom TypeDecorator (see sqlite-uuid-compatibility.md)
- **Python version mismatch**: Server Python 3.10 vs local 3.11 — test import on server
- **NODE_ENV=production**: Frontend needs `npm run build` for production mode; use development mode if no build step
- **systemd env inheritance**: Backend process inherits systemd environment, not shell .bashrc
