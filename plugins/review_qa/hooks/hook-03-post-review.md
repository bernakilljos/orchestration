# HOOK-03 — Post-Review (After Gemini review completes)

## Trigger
Auto-run after Gemini review. Last gate before merge.

## Steps

### 1. Parse review items
```bat
rem Extract MUST items from review
findstr /i "MUST:" docs\review-result.txt > docs\must-items.txt
for /f %%c in ('find /c /v "" "docs\must-items.txt"') do echo MUST items: %%c
```

### 2. Team Lead adoption decision
Read `docs\must-items.txt`, decide adopt/reject,
then write `docs\review-decision.md`.

### 3. If adopted items exist → re-run Codex
```bat
if exist docs\review-decision.md (
  if not "%~z0"=="0" (
    .claude\scripts\codex.bat --auto docs\review-decision.md
  )
)
```

### 4. Update learning (failure patterns)
Claude reads `.claude\learning\failure-patterns.json` and appends
new patterns if applicable, then saves.

### 5. Mark task complete
Claude reads `.claude\tasks\current-tasks.json`,
sets `status: "done"` and `completed_at` timestamp,
updates `.claude\tasks\task-memory.json`.

### 6. Auto-generate release note
```bat
echo ## Release Note - %DATE% > docs\release-note.md
echo. >> docs\release-note.md
echo ### Changed >> docs\release-note.md
type .claude\tasks\task-instruction.md | findstr /n "^" | findstr /b "[1-9]:" >> docs\release-note.md
echo. >> docs\release-note.md
echo ### Files >> docs\release-note.md
type docs\changed-files.txt >> docs\release-note.md
echo. >> docs\release-note.md
echo Team: Lead=Claude Impl=Codex Review=Gemini >> docs\release-note.md
```

## Final Merge Checklist
- [ ] All MUST items resolved
- [ ] Quality gate re-passed (if re-implemented)
- [ ] Release note created
- [ ] locked_files released

## Git Commit (Windows)
```bat
git add .
git commit -m "feat: [task title from current-tasks.json]"
git push origin develop
```
