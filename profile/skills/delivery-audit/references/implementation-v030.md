# Delivery Audit Implementation Details (v0.3.0)

## addon.py Functions

### run_delivery_audit(task_id, options)
Core 4-gate audit engine. Returns dict with:
- `gates`: dict of gate_name → {checks: [...], pass: bool}
- `conclusion`: "PASS" or "FAIL"
- `summary`: human-readable result
- `gate3_escalation`: bool (true when 3 revisions fail)
- `gates_passed`: list of gate names that passed

Gate logic:
1. Gate 1 reads tasks.json to check result existence and error_log emptiness
2. Gate 2 checks result length (>50 chars), skill_used, completed_at, error count (≤2)
3. Gate 3 auto-passes unless revision_count ≥ 3
4. Gate 4 auto-passes when all prior gates pass

Uses `_load_meta()` / `_save_meta()` from existing addon.py infrastructure (not `_load_task_meta` which doesn't exist).

### set_task_standards(task_id, std_type, standards)
Stores standards under `meta["standards"]` key. `std_type="all"` replaces entire dict; otherwise updates one key.

### get_standards_template(std_type)
Returns hardcoded templates for "dev", "design", "delivery". Unknown type returns all three.

## dashboard_api.py Routes

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| POST | /api/tasks/:id/deliver | triggers audit, updates task status | On PASS→completed, revision→revision, ≥3→pending_approval |
| GET | /api/tasks/:id/audit | returns task["audit"] or null | In do_GET, standalone if block |
| POST | /api/tasks/:id/standards | calls set_task_standards | Also logs event via add_task_event |
| GET | /api/standards/:type | returns template dict | In do_GET, standalone if block |

## Frontend (dashboard.html)

### Tab Integration
Task detail modal has 5 tabs: 基本信息, 时间线, ⚠️错误, 📅事件, 📝审计.
- Tab array: `['基本信息', '时间线', '⚠️ 错误', '📅 事件', '📝 审计']`
- idx===4 triggers `renderAuditTab(tid)`

### Functions
- `renderAuditTab(tid)`: async fetch + render gates
- `renderGateChecks(checks)`: renders check items with icons
- `triggerAudit(tid)`: POST /api/tasks/:id/deliver → refresh tab
- `forcePassAudit(tid)`: POST with {force_pass: true} + confirm dialog

### CSS Classes
`.audit-gate`, `.audit-gate-head`, `.audit-check-row`, `.audit-check-icon`,
`.audit-overall` (pass/fail/pending variants), `.audit-summary`, `.audit-rev-history`,
`.audit-rev-item`, `.audit-actions`

### Event Delegation
Buttons use `data-tid` + `escAttr()` pattern on modal overlay:
- `.td-audit-trigger-btn` → `triggerAudit(event.target.dataset.tid)`
- `.td-audit-force-btn` → `forcePassAudit(event.target.dataset.tid)`
