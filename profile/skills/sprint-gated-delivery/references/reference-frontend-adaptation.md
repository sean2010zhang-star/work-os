# Reference Frontend Adaptation Workflow

When user provides a reference frontend (zip file or repo), follow this workflow:

## Step 1: Extract and Analyze
```bash
unzip reference.zip -d /tmp/ref/
# Identify: framework (React/Next/Vite), styling (Tailwind/CSS), icons, animations
# Note: package.json dependencies, server architecture
```

## Step 2: Replace Current Frontend
```bash
# Backup current
mv web web.bak
# Extract reference
mkdir web && unzip reference.zip -d web/
# Install dependencies
cd web && npm install
```

## Step 3: Brand Replacement
```bash
# Find all brand references
grep -rn "OldBrand" src/ --include='*.tsx' --include='*.ts'
# Replace (handle JSX splits like <span>Brand</span>)
sed -i '' 's/OldBrand/NewBrand/g' src/**/*.tsx
# Also check: version labels, subtitles, footers, meta tags
```

## Step 4: Add New Pages Matching Reference Style
- Use same color scheme (check tailwind.config or CSS variables)
- Use same icon library (lucide-react, etc.)
- Use same animation library (motion/framer-motion)
- Use same component patterns (card layout, button styles)
- NEW pages should look like they belong with the reference pages

## Step 5: Story Flow Tab Ordering
Tabs should follow user journey, NOT technical module structure:
1. 控制台 (overview/dashboard)
2. 核心功能1 (entry point - e.g. resume diagnosis)
3. 核心功能2 (deepening - e.g. resume optimization)
4. 核心功能3 (exploration - e.g. career experiments)
5. 核心功能4 (validation - e.g. AI interview)
6. 核心功能5 (action - e.g. job management)
7. 扩展功能 (student/learning/community)
8. 设置 (personal settings)

## Step 6: API Integration
- Modify server.ts to proxy /api/* to backend
- OR update components to call backend directly via fetch/axios
- Test proxy: `curl -X POST http://localhost:PORT/api/v1/auth/register ...`

## Pitfalls
- **Don't rewrite from scratch** — User gave you reference code for a reason. Use it.
- **Don't skip brand replacement** — Check JSX splits like `<span>Career</span><span>Forge</span>`
- **Don't use dark theme when reference is light** (or vice versa) — Match the reference
- **Don't put technical module order** — Use story flow order
