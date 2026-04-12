# SKILL-13 — Parallel Dispatch (Claude Subagent System)

## Purpose
When user gives a task, Claude decides how to split and execute in parallel.
Claude is ALWAYS the orchestrator — user gives instructions, Claude executes.

---

## Decision Flow

```
User instruction received
  → Claude analyzes scope and complexity
  → Small (< 200 lines, 1-2 files): Handle directly, no split
  → Medium (200-500 lines, 3-5 files): Split into 2-3 subagents
  → Large (500+ lines, 5+ files): Split into N subagents (up to agent+skill count)
  → External delegation needed: Write task-instruction.md for Codex/Gemini
```

## How Claude Parallelizes (Agent Tool)

Claude uses the built-in Agent tool to spawn subagents within the conversation.
Each subagent runs independently and returns results.

### Parallel-Safe Operations (can run simultaneously)
```
[P] SKILL-01  research          File exploration, risk scan
[P] SKILL-04  context-summary   Summarize large files
[P] SKILL-12  domain-detect     Stack auto-detection
[P] SKILL-06  test              Test generation
[P] SKILL-10  quality-verify    Performance + quality check
[P] SKILL-08  design            Asset generation
[P] AGENT-04  architect         Design decisions
[P] AGENT-06  designer          Design reference check
```

### Sequential Operations (must wait for dependencies)
```
[S] AGENT-01  team-lead         Task split (runs FIRST)
[S] SKILL-02  implement         After research + architect
[S] SKILL-03  review            After implementation
[S] SKILL-05  deploy            After review + quality gate
[S] SKILL-07  rollback          Only on failure
[S] AGENT-05  monitor           After deploy
[S] SKILL-09  memory-reset      At context 80%
```

## Dispatch Patterns

### Pattern 1 — Research Burst (task start)
```
Spawn in parallel:
  Agent: SKILL-01 research (explore files, find risks)
  Agent: SKILL-04 context-summary (summarize 500+ line files)
  Agent: SKILL-12 domain-detect (if domain-profile.md missing)

Wait for all → Claude synthesizes → decide approach
```

### Pattern 2 — Implementation Split (large feature)
```
Claude (team-lead) splits into subtasks:
  task-01-api.md      [P] Backend API endpoints
  task-02-store.md    [P] Frontend store/state
  task-03-page.md     [S] Frontend pages (depends on 01+02)
  task-04-tests.md    [P] Test generation

Spawn parallel agents for [P] tasks:
  Agent 1: implement task-01
  Agent 2: implement task-02
  Agent 3: implement task-04

Wait → then run [S] tasks:
  Agent 4: implement task-03

Then spawn parallel:
  Agent 5: SKILL-10 quality-verify
  Agent 6: SKILL-06 test (run tests)
```

### Pattern 3 — Review + Quality (post-implementation)
```
Spawn in parallel:
  Agent: SKILL-10 quality-verify (4-area check)
  Agent: SKILL-06 test (run all tests)
  Agent: Write task-instruction.md for Gemini verify

Wait for all → Claude makes final decision
```

### Pattern 4 — Full Auto (user away)
```
Claude runs Continuous Dev Loop:
  1. Pick next priority item
  2. Pattern 1 (research burst)
  3. Pattern 2 (implementation split)
  4. Pattern 3 (review + quality)
  5. If all pass → commit → pick next item
  6. If fail → fix → retry (max 3)
  7. Repeat until user says stop or no items left
```

## Subagent Prompt Template

When spawning a subagent via Agent tool:
```
"You are a {role} subagent for the orchestration pipeline.
Project: {PROJECT_ROOT}
Task: {specific task description}
Rules: Follow CLAUDE.md and context/rules.md.
Scope: Only modify files listed below.
Files: {file list}
Report: Return results in this format:
  - Status: DONE/FAIL
  - Files modified: [list]
  - Issues found: [list]
  - Time taken: Xms"
```

## Claude-Auto (Unattended Mode)

For autonomous execution when user is away:
```bash
claude-auto              # 18 workers (default = agent + skill count)
claude-auto 20           # 20 workers
claude-auto 1            # single sequential worker
```

Each worker runs `claude -p` non-interactively, picks tasks from `.claude/tasks/`.

## Rules

1. Claude ALWAYS decides the split — user gives the goal, Claude plans execution
2. Never spawn more subagents than there are independent work units
3. Cap parallel file modifications: Writer=1 per file (no two agents touch same file)
4. Subagents do NOT call Codex/Gemini — only Claude main orchestrator does
5. After all subagents complete, Claude main reviews and merges results
6. If subagent fails, Claude main decides: retry, fix, or escalate to user
