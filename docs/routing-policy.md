# Routing Policy — Budget Ceiling + Quota-Aware Router

> **Version**: 1.0 (Phase 2)
> **Updated**: 2026-04-23
> **Status**: Active
>
> 24/7 automated task routing with budget protection and quota management.
> All tasks are classified and routed before execution based on SQLite state.

---

## 1. Quick Start

### Set Daily Budget Limit

```bash
python .claude/scripts/route.py --set-daily-limit 50.00
```

Default: unlimited (no cap).

### Check System Status

```bash
python .claude/scripts/route.py --status
```

Output:
```
Budget: $2.31 / $50.00 (4.6%) — OK
Quota Status:
  claude-opus-4-7      OK
  claude-sonnet-4-6    OK
  claude-haiku-4-5     OK
  codex                OK
  gemini               OK
```

### Get Routing Decision for a Task

```bash
python .claude/scripts/route.py --task-type design --estimated-tokens 5000
```

Output:
```json
{
  "ai": "claude-opus-4-7",
  "use_thinking": true,
  "thinking_budget": 8000,
  "use_caching": true,
  "worker_count": 1,
  "estimated_cost_usd": 0.1275,
  "reason": "design + thinking(8000)",
  "fallback_chain": [
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "gemini"
  ]
}
```

---

## 2. Decision Tree

```
┌─ Breaker Tripped?
│  └─ YES → BREAKER (no new tasks)
│  └─ NO ↓
│
├─ Task Type?
│  ├─ DESIGN / REFACTOR / AMBIGUOUS
│  │  └─ Opus 4.7 + thinking(8000)
│  │     Fallback: Sonnet, Haiku, Gemini
│  │
│  ├─ IMPLEMENT
│  │  ├─ <200 tokens → Sonnet 4.6
│  │  ├─ 200-800k tokens → Opus 4.7
│  │  └─ ≥800k tokens → Codex (parallel) or Gemini
│  │
│  ├─ VERIFY
│  │  ├─ <500k tokens → Haiku 4.5
│  │  └─ ≥500k tokens → Gemini
│  │
│  ├─ DOCUMENT → Sonnet 4.6
│  │
│  ├─ SIMPLE → Sonnet 4.6 or Haiku 4.5
│  │
│  └─ RETRY (retry_count > 0)
│     └─ If prior_ai was Sonnet/Haiku → escalate to Opus
│
└─ Check Preferred AI Quota
   ├─ OK → Use it
   ├─ Exceeded → Walk fallback chain
   └─ All exceeded → WAIT (600+ sec backoff)
```

---

## 3. Budget Breaker Logic

### Activation

When daily spend exceeds `daily_limit_usd`:

1. Breaker automatically trips
2. All `route()` calls return `AI=BREAKER`
3. Workers detect this and backoff
4. New tasks **DO NOT START**
5. In-flight tasks **CONTINUE** to completion

### Auto-Reset

- **UTC Midnight**: Breaker auto-resets, `today_spent_usd = 0`
- **Manual Reset**: `python .claude/scripts/route.py --reset-breaker`

### Viewing Status

```bash
python .claude/scripts/route.py --status
```

If breaker is tripped, it will show:
```
Budget: $50.50 / $50.00 (101.0%) — TRIPPED
```

### Override (Emergency)

If you need to force-continue despite budget overage:

```bash
python .claude/scripts/route.py --reset-breaker
```

This **resets the flag only**. It does not reset the spend counter.

---

## 4. Quota Management

### Auto-Expiry

When an AI hits quota limits (rate_limit, quota_exceeded errors):

1. Quota flag automatically set with 2-hour expiry
2. `route()` skips that AI, uses fallback
3. When expiry time passes, flag auto-clears
4. AI is available again

### Manual Clear

```bash
python .claude/scripts/route.py --clear-quota claude-opus-4-7
```

### Viewing Quota Status

```bash
python .claude/scripts/route.py --status
```

Shows each AI as `OK` or `EXCEEDED`.

---

## 5. Task Classification

When calling `route()` in your code or CLI:

| Type | When | Example |
|------|------|---------|
| **design** | Architecture decisions, design patterns | "Design a new plugin system for..." |
| **implement** | Code implementation, feature building | "Implement the routing module..." |
| **verify** | Validation, testing, code review | "Review this PR for bugs" |
| **document** | Documentation, research, summaries | "Write API docs for..." |
| **refactor** | Code refactoring, optimization | "Refactor the database layer" |
| **simple** | Template filling, minor edits, typos | "Fix a typo in README" |

---

## 6. Thinking + Caching Strategy

### Thinking (Extended Thinking)

Auto-enabled for:
- `DESIGN`, `REFACTOR` task types
- Ambiguous task descriptions
- Retry attempts (if prior AI was smaller)

Budget: 8000 tokens for first retry, 4000 for second.

**Never** enable thinking for:
- Template filling
- Single-file edits
- Simple verification

### Prompt Caching

Always enabled. Provides ~90% cost reduction on system + CLAUDE.md context.

3-level cache TTL:
1. System block: 5 min
2. Project context: 1 hour
3. Session state: 3 hours

---

## 7. Worker Integration

### Pre-Flight Check (Every Loop Iteration)

Workers run this before each task:

```batch
python .claude/scripts/lib/pre_task_check.py <ai_type>
```

Exit codes:
- `0` → OK, proceed
- `2` → Breaker tripped, wait 10 min
- `3` → Quota exceeded, wait 10 min
- `1` → Unexpected error

### Worker Backoff Policy

| Scenario | Backoff | Retry |
|----------|---------|-------|
| Breaker tripped | 10 min | Loop restarts |
| Quota exceeded | 10 min | Loop restarts |
| Task failure (non-quota) | 60 sec | Task retried |

---

## 8. Cost Tracking

### View 24h Metrics

```bash
python .claude/scripts/route.py --metrics --hours 24
```

Output:
```
AI: claude-opus-4-7
  Calls: 42
  Success rate: 92.8%
  Input tokens: 2,150,000
  Output tokens: 890,000
  Total cost: $12.50
  Avg latency: 4500ms
  Cache hits: 28
```

### Pricing Reference (2026-04)

| Model | Input (1M) | Output (1M) | Cache Read | Cache Write |
|-------|-----------|-----------|-----------|-----------|
| Opus 4.7 | $15.00 | $75.00 | $1.50 | $18.75 |
| Sonnet 4.6 | $3.00 | $15.00 | $0.30 | $3.75 |
| Haiku 4.5 | $0.80 | $4.00 | $0.08 | $1.00 |
| Codex | $2.50 | $10.00 | — | — |
| Gemini Flash | $0.075 | $0.30 | — | — |

---

## 9. Task-Level Override (Future)

In task frontmatter, you can optionally specify preferred AI:

```yaml
---
title: My Task
prefer_ai: claude-opus-4-7
ignore_breaker: false
---
```

This is **not yet implemented** but reserved for Phase 3.

---

## 10. Troubleshooting

### Breaker Tripped but Budget Should Be OK?

**Cause**: Clock skew or budget limit set too low.

**Fix**:
```bash
# View current spend
python .claude/scripts/route.py --status

# If wrong, manually reset
python .claude/scripts/route.py --reset-breaker

# Raise limit if needed
python .claude/scripts/route.py --set-daily-limit 100.00
```

### Quota Exceeded but AI Should Be Available?

**Cause**: Expiry time not yet reached, or quota flag stuck.

**Fix**:
```bash
# Manual clear
python .claude/scripts/route.py --clear-quota codex

# Verify
python .claude/scripts/route.py --status
```

### Worker Stuck in Backoff Loop?

**Cause**: Breaker or quota not recovering.

**Check**:
```bash
# 1. View status
python .claude/scripts/route.py --status

# 2. If breaker is stuck
python .claude/scripts/route.py --reset-breaker

# 3. Stop workers and restart
# (Close windows or Ctrl+C)
# Then: codex-auto, gemini-auto, claude-auto as needed
```

### How to Manually Trip Breaker (Testing)?

```bash
python .claude/scripts/route.py --trip-breaker
```

Workers will immediately backoff. To reset:

```bash
python .claude/scripts/route.py --reset-breaker
```

---

## 11. Configuration Files

### Daily Limit Storage

Stored in SQLite:
```
.claude/state/orca.db → budget table → daily_limit_usd
```

### Quota Flags

Stored in SQLite:
```
.claude/state/orca.db → quota table → (ai, exceeded, expires_at)
```

### Worker State

Stored in SQLite:
```
.claude/state/orca.db → workers table
```

SQLite provides atomic updates without file race conditions.

---

## 12. Interaction with Orca Auto

When Orca Auto is running (`orca-auto.bat` or `/orcauto-start`):

1. Every loop iteration, workers call `pre_task_check.py`
2. Breaker or quota triggers 10-min backoff (automatic)
3. Status visible via `route.py --status`
4. Watchdog monitors SQLite state (future Phase 3)

No manual intervention needed for normal operation.

---

## 13. Future Enhancements (Phase 3)

- [ ] Task-level `prefer_ai` override in frontmatter
- [ ] Watchdog auto-stop on repeated quota errors
- [ ] Cost prediction before task starts
- [ ] Daily email report with budget summary
- [ ] Slack notification on breaker trip
- [ ] Per-plugin cost cap

---

## 14. References

- Router logic: `.claude/scripts/lib/router.py`
- CLI tool: `.claude/scripts/route.py`
- Pricing data: `.claude/scripts/lib/pricing.py`
- State management: `.claude/scripts/lib/state_db.py`
- Pre-flight check: `.claude/scripts/lib/pre_task_check.py`
- Routing skill: `plugins/exec_orch/skills/route_dispatch.md`
