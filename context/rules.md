# Project Work Rules

## AI Role Assignment

| Work Type | Assigned | Execution Method |
|-----------|----------|-----------------|
| Design / Judgment / Approval | Claude | Direct handling |
| Implementation (500+ lines) | Codex | codex-a --auto |
| Implementation (500- lines) | Claude | Direct handling |
| Verification / Review | Gemini | gemini-a --verify |

## Claude Behavior Rules

- Do not create execution wrappers for Claude (claude-a.bat, claude-auto.bat, etc.) -> Claude implements directly in the conversation
- Do not say "I'll start right away" and then ask additional questions -> Confirm information first, then declare start
- After writing task-instruction.md, Codex/Gemini handle it automatically -> Claude consolidates results and finalizes

## Encoding Rules (Important)

- Do not write Korean strings directly in .js / .ts / .java server files
  -> If Codex saves as CP949, it will break in UTF-8 runtime
  -> Use English messages OR convert to Korean on the frontend (Vue)
- .vue / .html files are saved as UTF-8 (Claude can use Korean directly when writing)
- .bat / .md files are CP949 (auto-converted by install.bat)

## Design Rules

- Design references: Save screen images in docs\screens\ folder
- Layout lock: AI modification of layouts/ folder is prohibited (HOOK-07)
- Component structure: Only business logic can be added to components/ folder
- Color palette: Define in project context/project.md and follow
- Dark mode default: Background #0f1117, Card #1e2333, Border #2d3550
- Icons: Use emoji or inline SVG (avoid external icon libraries)

## Code Rules

- Optional chaining `?.` usage prohibited -> explicit null check
- Hardcoding prohibited -> reference process.env or config
  - Paths, exclusion patterns, ports, domains, etc. all separated into variables/config
  - bat files: Declare as set variables at the top
  - JS/TS: Reference config.js or .env
- Keep existing variable names (arbitrary changes prohibited)
- Prohibited to use the word "juIn" in comments

## File Modification Rules

- Only modify files specified in task-instruction.md
- Full rewrite of existing files prohibited
- Direct modification of DB / .sql files prohibited (suggestions only)
- Simultaneous modification of the same file prohibited (Writer=1)

## Deployment Rules

- prod deployment requires `--confirmed` flag
- Must pass quality-gate.bat before deployment
- rollback.bat auto-executes on failure

## Notifications

- Task completion: notify.bat good
- Deployment failure: notify.bat warning
