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

# 3. 사용자 승인 — 사용자가 프롬프트에 직접 입력할 때만 기록 (prompt/user_approval.py · Claude 가 대신 실행 X)
/approve <task_id>

# 4. 실행 — 승인 뒤 같은 명령을 같은 폴더에서 1회 (30분 · 스크립트·HEAD 가 바뀌면 재승인)
#    (2026-11-20 R353: 예전 예시 `approval-gate.py approve|execute` 는 CLI 에 없는 명령이라 삭제 · 현재 CLI = detect·request·withdraw·list·status)
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
| 위 5 카테고리 매치 |  approval-gate 필수 |
| 단순 file write / read |  자동 진행 |
| 외부 API call (read-only) |  자동 진행 |
| `git commit` (local) |  자동 진행 |
| `git push` (origin feature branch) |  자동 진행 |
| `git push` / `git push origin <브랜치>` 단독 (일반 push · 2026-11-13 R250 사용자 위임) |  자동 진행 (비밀값 검사는 유지) |
| 위 일반 push 뒤의 `2>&1`·`\| tail -N`·`\| head -N` (2026-11-14 R255 · 같은 push 인데 형태만 달라 생기던 불필요 요청 제거 · 앞에 `cd` 를 붙이면 저장소·HEAD 확정 불가로 그대로 차단) |  자동 진행 |
| 위 일반 push 앞뒤에 `;`·`&&`·`\|\|` 로 붙은 **읽기 전용** 명령 (`git log·rev-list·status·show·rev-parse`·`git branch --show-current`·`echo` · 뒤의 `\| tail·head·grep·wc`) (2026-11-20 R353 · 실제 효과가 단독 push 와 같음 · `appr-58d5cfe406f7` 형태) — commit·pull·fetch·cd·checkout 이 같이 있으면(올라갈 커밋 확정 불가 · 커밋·원격 반영 독립 규칙) · 따옴표·`$`·백틱·괄호·리다이렉션·`&`·`--output`·push 2개 이상·비일반 push 는 그대로 승인 대상 |  자동 진행 |
| 실행되지 않는 언급 (2026-11-15 R256): grep 검색어(셸 따옴표 규칙 · 큰따옴표 안 `$(…)` 와 셸로 넘기는 파이프는 제외) · 명령 실행 불가로 확정된 `python - <<'EOF'` 본문의 push 단어 (import 허용 목록 · eval/exec/getattr/dunder/os 속성/git 훅 경로 문자열 금지) · request-ledger.py add/complete 인자 (HEAD 와 같은 내용 · 명령에 cd 가 없을 때만 세션 작업 위치 기준) |  자동 진행 |
| 자기 대기 요청 취소 (2026-11-16 R258): `approval-gate.py withdraw <id> <사유>` = 대기 → 만료 (승인 아님 · 게이트가 만든 대기 행만 · 사유·원래 명령 기록 보존) · 작업 종료(Stop)마다 `own-cleanup.py` 가 임시 폴더 안만 지우는 자기 요청을 자동 취소 · 그 밖의 요청은 남은 승인으로 기록만 · 사유 인자는 기록 전용 (HEAD 와 같은 내용일 때만) |  자동 진행 |
| 강제 push (`-f`·`--force`·`+refspec`) · 원격 브랜치 삭제 (`:branch`·`--delete`) · `--mirror`·`--all`·`--tags` · origin 외 원격 · 다른 명령과 연결한 push |  approval-gate |
| SVN 일반 작업 `svn update`·`status`·`diff`·`add`·`delete <작업본 파일>`·`commit`·`revert <파일>`·`cleanup` (2026-11-13 R251 · IFRS = SVN) |  자동 진행 (캐시 인증 `--non-interactive`) |
| SVN 파괴 작업 `svn revert -R`·`cleanup --remove-unversioned`·`svn delete <URL>`(원격 직접 삭제)·`svnadmin` |  approval-gate |
| GitHub 인증: 저장소 로컬 `credential.https://github.com.username` 고정 + `credential.interactive never` (계정 선택 창 대신 즉시 실패·기록) · 다른 계정·전역 설정 변경 X |  (설정 · 2026-11-13) |

CLAUDE.md § 7-11 (Zero-touch 자동화) 와 정합:
- 알림 = 위 5가지만
- 그 외 = 침묵 + 로그

## 승인 만료

기본 24시간 — 그 후 `expired` 상태로 자동 변경. 사용자 재요청 필요. (2026-11-14 R255: 실제로는 상태가 안 바뀌어 61건이 대기로 남았음 → `list` 조회 때 `expire_stale()` 이 24시간 넘은 대기 요청을 expired 로 바꾼다)

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
