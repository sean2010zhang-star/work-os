# Frontend Component Merge + Debug Pattern

## Merging Components from Multiple ZIP Sources

### Workflow
1. Extract both ZIPs to temp directories
2. Compare component lists — identify unique vs overlapping
3. Copy unique components to project
4. Merge types.ts — append new interfaces (don't overwrite)
5. Update App.tsx — add imports, state, handlers, tabs, views
6. Build to verify (`npm run build`)

### Critical Pitfalls

#### 1. `read_file` Returns Line Numbers
```
# WRONG: write_file writes line numbers as content
content = read_file("App.tsx").get("content", "")
write_file("App.tsx", content)  # Writes "     1|import..."

# RIGHT: strip line numbers before writing
lines = content.split('\n')
clean = [l.split('|', 1)[1] if '|' in l and l.strip()[0].isdigit() else l for l in lines]
write_file("App.tsx", '\n'.join(clean))
```

#### 2. Type-Only Imports Must Use `import type`
```typescript
// WRONG: esbuild strips type-only exports, import fails at runtime
import { UserType, Tier } from "./types/v5";

// RIGHT: explicit type import
import type { UserType, Tier } from "./types/v5";
```

#### 3. Import Path from Nested to Sibling
```typescript
// WRONG: when App.tsx is in src/app/, types/v5 is at src/types/v5
import { UserType } from "../types/v5";  // resolves to wrong path

// RIGHT: check actual file location relative to import
import { UserType } from "./types/v5";  // if both in src/
```

#### 4. `sed` Multi-line Append Unreliable
```bash
# WRONG: sed 'a\' with multiple lines fails on macOS
sed -i '' '/pattern/a\
line1\
line2' file.tsx

# RIGHT: use Python for multi-line insertions
python3 -c "
content = open('file.tsx').read()
content = content.replace('old', 'new')
open('file.tsx', 'w').write(content)
"
```

#### 5. Duplicate Additions from Multiple sed/python Passes
When combining sed and Python edits, state/handler blocks get added twice.
Always verify with grep after each pass:
```bash
grep -c "app-state marker" App.tsx  # should be 1, not 2
```

## Vite Blank Page Debugging

### Step 1: Check Browser Console
```javascript
// In browser console
document.getElementById('root')?.innerHTML  // empty = React not rendering
```

### Step 2: Check for Import Errors
```javascript
// Test individual imports
import('/src/types.ts').then(m => Object.keys(m)).catch(e => e.message)
import('/src/components/SkillsGapView.tsx').then(m => typeof m.default)
```

### Step 3: Add Error Boundary
```typescript
class ErrorBoundary extends Component<{}, {error: Error|null}> {
  static getDerivedStateFromError(error: Error) { return {error}; }
  render() {
    if (this.state.error) {
      return <pre>{this.state.error.message}\n{this.state.error.stack}</pre>;
    }
    return this.props.children;
  }
}

// Wrap App
<ErrorBoundary><App /></ErrorBoundary>
```

### Step 4: Check TypeScript Type Exports
```javascript
// Types exported as 'export type' don't exist at runtime
import('/src/types.ts').then(m => Object.keys(m))
// Returns [] if only interfaces/types are exported
```

### Step 5: Check Mock Data Field Names
Mock data must match the TypeScript interface exactly:
```typescript
// Interface expects 'name', mock uses 'title' → silent failure
interface Hypothesis { name: string; }
const mock = { title: "test" };  // WRONG
const mock = { name: "test" };   // RIGHT
```

## App.tsx Merge Checklist

When merging components from external sources:

- [ ] Copy components to src/components/
- [ ] Copy utils to src/utils/
- [ ] Merge types.ts (append, don't overwrite)
- [ ] Add imports to App.tsx
- [ ] Add state for new data model
- [ ] Add handlers for new actions
- [ ] Add tab buttons to nav
- [ ] Add view renderers to main
- [ ] Verify with `npm run build`
- [ ] Test in browser (not just build)
