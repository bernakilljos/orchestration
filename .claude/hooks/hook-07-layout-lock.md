# HOOK-07 — Layout Lock

## Trigger
Auto-run when a UI implementation task starts (after HOOK-01).

## Purpose
Prevent AI from arbitrarily changing the layout structure.
Force reuse by copying existing patterns.

## Steps

### 1. Register layout file list as locked
```
Add to locked_files in current-tasks.json:
  - docs/design-system/layouts/**
  - docs/design-system/components/**
  - ai_design_reference_system/layouts/**
  - ai_design_reference_system/components/**
```

### 2. Check design reference existence
```
Check if docs/design-system/ or ai_design_reference_system/ folder exists
  - Exists → Print available layout pattern list
  - Missing → [WARN] No design reference found → Recommend running AGENT-06 first
```

### 3. Inject rules for implementation AI
Auto-append to bottom of task-instruction.md:

```markdown
## [LAYOUT-LOCK] Layout Lock Rules

- layouts/ files: Absolutely no modifications allowed
- components/ files: No structural changes (only add business logic)
- No inventing new layouts: Must copy one of the patterns below

### Available Layout Patterns
[Auto-inserted: file list from layouts/ folder]

### Available Components
[Auto-inserted: file list from components/ folder]
```

## Pass Criteria
- [ ] layouts/, components/ registered in locked_files
- [ ] LAYOUT-LOCK rules inserted into task-instruction.md
- [ ] Design reference folder accessible

## On Failure
- No design reference found → Run AGENT-06 then retry
- locked_files conflict → Report to Team Lead
