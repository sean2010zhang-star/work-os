# Main.py Bloat Refactoring Pattern

## Problem
FastAPI main.py grows to 300-400+ lines with inline route definitions.

## Detection
```bash
grep -c "@app\\." app/main.py  # If > 10, needs refactoring
wc -l app/main.py              # If > 150 lines, needs refactoring
```

## Solution: Move inline routes to module routers

### Step 1: Identify routes by module
```bash
grep "@app\\." app/main.py | grep -oP '"/api/v1/\\w+' | sort -u
```

### Step 2: Move each route to its router.py

Before (in main.py):
```python
@app.post("/api/v1/experiments/industry-trend")
async def industry_trend(data: dict, current_user=Depends(get_current_user)):
    return await analyze_industry_trend(data.get("industry", ""))
```

After (in experiment/router.py):
```python
from app.experiment.trends import analyze_industry_trend

@router.post("/industry-trend")
async def industry_trend(data: dict, current_user: User = Depends(get_current_user)) -> dict:
    return await analyze_industry_trend(data.get("industry", ""))
```

### Step 3: Clean up main.py to < 80 lines
Only keep: App init, CORS, exception handler, router registrations, /health, /modules.

### Step 4: Move function imports from main.py to module routers

## Verified: production deployment
- main.py: 390 lines -> 79 lines (-80%)
- 45 inline routes -> 0 (moved to 9 module routers)
- Integration tests: 20/20 pass after refactoring
