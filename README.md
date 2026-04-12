# Orchestration Kit - Multi-AI Automation Framework

Claude(Team Lead) + Codex(Implementation) + Gemini(Review) 3 AI role-sharing orchestration.

---

## Quick Start (3 steps)

### Step 1 - Install
```bat
install.bat C:\projects\myproject
```

### Step 2 - Configure server (for deploy only)
`.claude/deploy-config.env` - fill in server info.
Skip if not deploying.

### Step 3 - Start working
```
Open Claude Code in the project folder
Tell Claude: "Build X feature"
Claude writes task-instruction.md
Run: codex-a --auto
Run: gemini-a --verify
Claude reviews results
```

---

## AI Roles

| AI | Role | How |
|----|------|-----|
| Claude | Team Lead: design, judge, approve | Direct in session |
| Codex | Implementer: 500+ line implementation | `codex-a --auto` |
| Gemini | Reviewer: verify, search, supplement | `gemini-a --verify` |

---

## Pipeline

### Standard Pipeline
```
Request received
  -> [HOOK-00]  init           First time: detect stack, create folders
  -> [SKILL-04] context        Summarize 500+ line files first
  -> [HOOK-01]  pre-task       Register task, lock files, check conflicts
  -> [SKILL-01] research       Explore files, identify risks
  -> [AGENT-01] team-lead      Write task-instruction.md
  -> [SKILL-02] implement      codex-a --auto (or Claude direct for small tasks)
  -> [HOOK-02]  quality-gate   Build / secret / quality check
  -> [SKILL-03] review         gemini-a --verify
  -> [HOOK-03]  post-review    Adopt review, update learning
  -> [HOOK-04]  pre-deploy     Final check before deploy
  -> [SKILL-05] deploy         EC2 auto deploy
  -> [AGENT-05] monitor        Health check loop
```

### Fast Pipeline (parallel - use when starting fresh or simple tasks)
```
[Parallel start]
  -> SKILL-01 research     + SKILL-04 context-summary  (run together)
  -> AGENT-01 team-lead    write task-instruction.md
  -> codex-a --auto        implement
  -> gemini-a --verify     review (skip if low risk)
  -> Claude adopts         done
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `codex-a` | Codex interactive mode |
| `codex-a --auto` | Codex reads task-instruction.md and implements |
| `codex-a --full-auto` | No confirmation prompts |
| `codex-a --analyze` | Full source analysis |
| `gemini-a` | Gemini interactive mode |
| `gemini-a --verify` | Gemini reviews against task-instruction.md |
| `gemini-a --analyze` | Full source analysis |
| `gemini-a --loop` | Continuous watch mode (30s interval) |

---

## Session Resume

If Claude session is interrupted mid-task:
```
1. New session opens
2. Claude detects .claude/context-cache/session-snapshot.md
3. Claude outputs: [RESUME] Previous session found
                   Task: xxx  Completed: research, implement  Next: gemini-a --verify
                   Continue? [Y/N]
4. Approve -> resumes from next step
```

Snapshot is saved automatically at:
- Context 80% reached
- Each pipeline step completed
- User requests save

---

## File Structure

```
orchestration_v1/
  README.md
  CLAUDE.md                         <- Master instructions for Claude
  install.bat                       <- Windows install
  install.sh                        <- Linux/Mac install
  .claude/
    settings.local.json             <- Full permissions
    deploy-config.env.example       <- Deploy config template
    tasks/
      task-instruction.md           <- Task spec (Claude writes this)
      current-tasks.json
      task-memory.json
    context-cache/
      session-snapshot.md           <- Session resume state
    agents/
      agent-01-team-lead.md
      agent-02-implementer.md
      agent-03-reviewer.md
      agent-04-architect.md
      agent-05-monitor.md
      agent-06-designer.md
    skills/
      skill-01-research.md
      skill-02-implement.md
      skill-03-review.md
      skill-04-context-summary.md
      skill-05-deploy.md
      skill-06-test.md
      skill-07-rollback.md
      skill-08-design.md
      skill-09-memory-reset.md
    hooks/
      hook-00-init.md
      hook-01-pre-task.md
      hook-02-post-impl.md
      hook-03-post-review.md
      hook-04-pre-deploy.md
      hook-05-post-deploy.md
      hook-06-notify.md
      hook-07-layout-lock.md
    scripts/
      codex-a.bat / codex-a.sh
      gemini-a.bat / gemini-a.sh
      init.bat / init.sh
      deploy.bat / deploy.sh
      ...
    learning/
      failure-patterns.json
      optimization-rules.json
```

---

## Dev Rules (apply to all projects)

```
Frontend:  Vue 2.x - no optional chaining (?.) - explicit null checks
Backend:   Spring Boot 2.x / Node.js Express
DB:        MSSQL / MySQL / Oracle / SQLite
Alert:     mapActions("alert",[ADD_ALERT]) / this.ADD_ALERT({message, color})
No hardcoding: use process.env or config
No comment containing word "juIn"
```

---

## Extend

```
New skill:  .claude/skills/skill-10-name.md  + .claude/scripts/name.bat
New agent:  .claude/agents/agent-07-name.md
New hook:   .claude/hooks/hook-08-name.md
-> Add to CLAUDE.md loading order and insert into pipeline
```
