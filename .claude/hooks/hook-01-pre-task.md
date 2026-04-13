# HOOK-01 — Pre-Task (Auto-run before task starts)

## Trigger
Auto-run when new task starts. Must pass before implementation begins.

## Steps

### 1. Register task
Update `.claude\tasks\current-tasks.json`:

```json
{
  "task_id": "TASK-NNN",
  "title": "Task title",
  "target_files": ["path/to/file"],
  "locked_files": ["path/to/file"],
  "writer": "codex",
  "agent": "codex",
  "priority": "high",
  "status": "research",
  "started_at": "ISO8601",
  "acceptance_criteria": [],
  "dependencies": []
}
```

### 2. File conflict check
```bat
rem Check for conflicts between locked_files and new task target files
type .claude\tasks\current-tasks.json
rem Claude: parse JSON and check for locked file collisions
```

### 3. Confirm task-instruction.md exists
```bat
if exist ".claude\tasks\task-instruction.md" (
  echo [OK] task-instruction.md found
) else (
  echo [BLOCK] task-instruction.md missing - must create first
)
```

### 4. Context cache check (500+ line files)
```bat
rem Find large files that need summarizing
for /r src %%f in (*.vue *.jsx *.tsx *.java *.py *.go *.js *.ts *.cs *.rb) do (
  for /f %%c in ('find /c /v "" "%%f"') do (
    if %%c GEQ 500 echo [LARGE] %%f ^(%%c lines^) - summarize needed
  )
)
```

### 5. UI screen reference
```bat
rem Check if relevant screens exist in docs\screens\
dir docs\screens\*.jpg 2>nul && echo [OK] Screen references available || echo [INFO] No screen references
```

## Pass Criteria
- [ ] current-tasks.json registered
- [ ] No locked_files conflict
- [ ] task-instruction.md exists
- [ ] Large files summarized

## On Failure
Resolve the failed item and re-run. Do NOT start implementation before passing.
