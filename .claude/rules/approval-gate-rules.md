# Approval Gate (HITL) 룰

> **근거**: CLAUDE.md § 7-23 (`위험 작업 승인 없이 실행 금지`).
> **이유**: 비가역 / 보안 / cost / system / data-loss 5 카테고리는 자동 실행 시 복구 불가.

## 절대 룰

**위험 명령 감지 시 `approval-gate.py detect` → 매치되면 `waiting_approval` 등록 → 사용자 `/approve <task_id>` 받은 후만 실행.**

## 위험 5 카테고리

| 카테고리 | 예시 명령 |
|---|---|
| **data_loss** | `DROP TABLE`, `rm -rf`, `git reset --hard` (force), 비가역 delete |
| **security** | `curl \| bash`, `sudo`, key/PAT 노출, 권한 상승 |
| **cost** | Batch API 1000+ request, `aws s3 cp` 대량, OpenAI bulk |
| **system** | `npm publish`, `docker push prod`, OS 설정·레지스트리 변경 |
| **irreversible** | `git push --force` main/master, `terraform apply -auto-approve`, deploy prod |

CLAUDE.md § 7-11 알림 5가지와 정합 (시크릿·데이터·보안·비용·시스템).

## 흐름

```bash
# 1. 자동 감지
python .claude/scripts/approval-gate.py detect "rm -rf /var/data/*"
# Output: {"category":"data_loss","severity":"critical","matched":"rm -rf"}

# 2. 등록 (Claude 자동)
python .claude/scripts/approval-gate.py request \
  --task <task_id> \
  --command "rm -rf /var/data/*" \
  --category data_loss \
  --reason "DB 마이그레이션 후 staging 정리"

# 3. 사용자 승인
/approve <task_id>
# 또는
python .claude/scripts/approval-gate.py approve <task_id>

# 4. 실행 (승인 후만)
python .claude/scripts/approval-gate.py execute <task_id>
```

## DB schema (v2)

```sql
CREATE TABLE approval_requests (
  task_id TEXT PRIMARY KEY,
  command TEXT NOT NULL,
  category TEXT CHECK(category IN ('data_loss','security','cost','system','irreversible')),
  severity TEXT CHECK(severity IN ('low','medium','high','critical')),
  reason TEXT,
  status TEXT CHECK(status IN ('waiting_approval','approved','rejected','executed','expired')),
  requested_at TEXT NOT NULL,
  approved_at TEXT,
  executed_at TEXT,
  expires_at TEXT,
  user_decision TEXT
);
```

마이그레이션: `python .claude/scripts/migrate-approval-gate.py`

## 자동 매칭 패턴 (`approval-gate.py detect`)

```python
PATTERNS = {
  "data_loss": [
    r"\bDROP\s+TABLE\b", r"\bDELETE\s+FROM\b.*WHERE\s+1=1",
    r"\brm\s+-rf\b", r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-fd\b", r"\btruncate\s+table\b",
  ],
  "security": [
    r"curl[^|]*\|\s*(bash|sh)", r"\bsudo\b",
    r"\bchmod\s+777\b", r"export\s+\w*(KEY|TOKEN|SECRET)\s*=",
  ],
  "cost": [
    r"\baws\s+s3\s+cp\b.*--recursive",
    r"\bopenai\s+.*batch", r"\bnpm\s+publish\b",
  ],
  "system": [
    r"\bdocker\s+push\b.*prod",
    r"\bnpm\s+publish\b", r"\bsetx?\b\s+/M",
  ],
  "irreversible": [
    r"\bgit\s+push\s+--force\b.*\b(main|master)\b",
    r"\bterraform\s+apply\s+--auto-approve\b",
  ],
}
```

## 5 카테고리 외 — 일반 안내 룰

| 상황 | 안내? |
|---|---|
| 위 5 카테고리 매치 | ✅ approval-gate 필수 |
| 단순 file write / read | ❌ 자동 진행 |
| 외부 API call (read-only) | ❌ 자동 진행 |
| `git commit` (local) | ❌ 자동 진행 |
| `git push` (origin feature branch) | ❌ 자동 진행 |
| `git push` (origin main) | ✅ approval-gate |

CLAUDE.md § 7-11 (Zero-touch 자동화) 와 정합:
- 알림 = 위 5가지만
- 그 외 = 침묵 + 로그

## 승인 만료

기본 24시간 — 그 후 `expired` 상태로 자동 변경. 사용자 재요청 필요.

## 금지

1. **위험 명령 즉시 실행** — approval-gate 우회 = § 7-23 위반
2. **detect 결과 무시** — pattern 매치 되었는데 진행
3. **사용자 미응답 시 자동 진행** — 명시 승인 없이 X
4. **expired 후 자동 재요청** — 사용자 의도 확인 필수

## Watchdog 통합

- waiting_approval > 1시간 → Slack/Notion outbox 알림 (있을 때만)
- expired 자동 정리 (cleanup-pollution.sh)

## 참조

- `CLAUDE.md § 7-23` (절대 룰)
- `CLAUDE.md § 7-11` 알림 5가지 (정합)
- `plugins/exec_orch/skills/skill-approval-gate.md`
- `.claude/scripts/approval-gate.py` (핸들러)
- `.claude/scripts/migrate-approval-gate.py` (DB v2)
- `.claude/rules/failure-mode.md` § 알림 허용
- `.claude/rules/best-practices.md` § Zero-touch 자동화
