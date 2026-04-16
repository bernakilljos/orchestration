# HOOK-00 — Init (First-time project setup)

## Purpose
Run once when first applying the orchestration kit to a new project.
install.bat calls this automatically.

## Execution (Windows)
```bat
.claude\scripts\init.bat [project-path]
```

## Steps

### Step 1 — Create folders
```
docs\adr\
docs\deploy-history\
docs\screens\         (UI reference screenshots)
.claude\context-cache\
.claude\tasks\
.claude\learning\
```

### Step 2 — Auto-detect stack

| Detected | Detection Rule |
|----------|----------------|
| Vue 2 | package.json has "vue": "^2" |
| Vue 3 | package.json has "vue": "^3" |
| Spring Boot | pom.xml exists |
| Node Express | package.json has "express" |
| MSSQL | *.properties / *.yml has sqlserver |
| MySQL | *.properties / *.yml has mysql |
| Oracle | *.properties / *.yml has oracle |

Result saved to `.claude\tasks\task-memory.json` under `project_stack`.

### Step 3 — Generate file list
```
docs\file-list.txt         Full source file list
docs\large-files.txt       Files over 500 lines
docs\project-structure.md  Project structure summary
```

Windows commands:
```bat
dir /s /b src\*.vue src\*.js src\*.java > docs\file-list.txt
for /f "tokens=*" %%f in ('dir /s /b src\*.vue src\*.js src\*.java') do (
  for /f %%c in ('find /c /v "" "%%f"') do (
    if %%c GEQ 500 echo %%c %%f >> docs\large-files.txt
  )
)
```

### Step 4 — Create deploy-config.env
Copy `.claude\deploy-config.env.example` to `.claude\deploy-config.env` (if missing).

### Step 5 — CLI verification
Check: claude / codex / gemini / git installed.

## Re-run
Re-run when stack changes or new team member joins.

## Extension Points
- Can auto-chain to skill-01-research after run
- Automates brownfield project analysis
