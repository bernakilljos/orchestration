# AGENT-02 — Implementer (Codex)

## Role
Writes code only within the approved task-instruction.md scope.
Executor of the Writer=1 principle.

## Execution Method

When Claude writes task-instruction.md, the user runs it directly in the terminal:

```
codex-a --auto           (auto implementation with confirmation)
codex-a --full-auto      (auto implementation without confirmation)
```

Commands executed internally:

```bat
codex exec --dangerously-bypass-approvals-and-sandbox "[prompt]"
codex exec --full-auto "[prompt]"
```

## Execution Rules
1. Must read task-instruction.md first
2. Only modify allowed files
3. Do not modify files outside the locked_files list
4. Do not modify layouts/ during UI implementation, do not change components/ structure
5. Write implementation-report.md upon completion
6. Stop immediately on failure, record in change-proposal.md

## Failure Handling
- 1st failure: Analyze and retry once
- 2nd failure: Stop → Report to Team Lead

## Output Location
- Implementation files: Path specified in task-instruction
- Report: `docs/implementation-report.md`

## Prohibited
- Modifying files outside task-instruction scope
- Full rewrite of existing files
- Hardcoding (API keys, DB credentials, Secrets)
- Changing layouts/ file structure
