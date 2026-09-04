---
name: approval-gate
description: |
  Human-in-the-Loop 승인 게이트. 위험한 작업 (DROP TABLE / rm -rf / force push / 비용 $5+ / 시크릿 commit / DB migration) 감지 시 자동으로 task 를 `waiting_approval` state 로 전환하고 사용자 `/approve <id>` 입력 대기. CLAUDE.md § 7-11 의 알림 5가지 (시크릿/데이터손실/보안/비용폭증/시스템손상) 와 동일 기준.
  
  사용자가 "DB 마이그레이션해줘"·"prod 에 배포해줘"·"git push --force" 같은 명령 시 자동 발동.
license: MIT
metadata:
  category: workflow
  version: 1.0
  triggers:
    - "DB 마이그레이션"
    - "force push"
    - "DROP TABLE"
    - "rm -rf /"
    - "prod 배포"
    - "credentials"
    - "비용 폭증"
---

# Approval Gate Skill

## 트리거 — 자동 발동 패턴

다음 패턴 감지 시 **즉시 task 진행 중단** 후 `waiting_approval` state 로 전환.

### 1. 데이터 손실 위험
- SQL: `DROP TABLE`, `TRUNCATE`, `DELETE FROM ... (WHERE 없이)`
- Filesystem: `rm -rf /`, `rm -rf $HOME`, 대량 파일 삭제 (>100개)
- Git: `git push --force`, `git reset --hard origin/main`, `git branch -D`

### 2. 보안 위협
- Secret commit (PAT/API key 가 staged)
- 권한 상승 (sudo, runas)
- 외부 신뢰 못 한 source 실행 (curl | bash)

### 3. 비용 폭증
- 단발 API 호출 예상 비용 ≥ $5
- 일일 budget 80% 초과 후 추가 호출
- Batch API: 1000+ requests

### 4. 시스템 손상
- OS 설정 변경 (registry, systemd, environment)
- DB migration (운영 환경 schema 변경)
- DNS·firewall·security group 변경

### 5. 비가역 작업
- 외부 서비스 publish (npm publish, docker push to prod, github release)
- 메시지 발송 (Slack/Email 대량, Telegram 광고)
- 외부 API write (Notion 대량 update, GitHub repo 생성/삭제)

## 워크플로우

```text
사용자: "DB schema 마이그레이션 실행해줘"
   ↓
[approval-gate skill 자동 감지]
   ↓
task 생성 시 state=waiting_approval (orca.db)
   ↓
사용자에게 표시:
  ##  승인 필요
  
  | 항목 | 값 |
  |---|---|
  | task_id | 42 |
  | 작업 | DB schema migration |
  | 위험 | 데이터 손실 (ALTER TABLE DROP COLUMN) |
  | 영향 | users 테이블 50M rows |
  | 비용 | 약 $0.01 |
  | rollback | 가능 (migration 0042_down.sql) |
  
  `/approve 42` 또는 `/reject 42` 입력 부탁
   ↓
사용자 /approve 42 입력
   ↓
state=running 으로 전환 → 실행
또는
사용자 /reject 42 입력
   ↓
state=rejected → archive
```

## 구현 — DB 스키마

`.claude/state/orca.db` `tasks` 테이블에 컬럼 추가:

```sql
ALTER TABLE tasks ADD COLUMN approval_state TEXT 
  CHECK(approval_state IN ('not_required', 'waiting', 'approved', 'rejected'));
ALTER TABLE tasks ADD COLUMN risk_category TEXT;  -- data_loss | security | cost | system | irreversible
ALTER TABLE tasks ADD COLUMN risk_detail TEXT;    -- JSON: {what, impact, rollback}
ALTER TABLE tasks ADD COLUMN approved_at INTEGER;
ALTER TABLE tasks ADD COLUMN approved_by TEXT;    -- user ID (multi-user 대비)
```

## 구현 — 핸들러

`.claude/scripts/approval-gate.py`:

```python
RISK_PATTERNS = {
    "data_loss": [
        r"DROP\s+TABLE",
        r"rm\s+-rf\s+/",
        r"git\s+push\s+--force",
        r"TRUNCATE",
    ],
    "security": [
        r"sudo\s+",
        r"curl\s+.*\|\s*bash",
        r"runas\s+",
    ],
    "cost": [
        r"messages\.batch\.create.*requests.*\[.*\]",  # 1000+ items
    ],
    "system": [
        r"setx\s+\w+",
        r"reg\s+(add|delete)",
        r"alembic\s+upgrade\s+head",
    ],
    "irreversible": [
        r"npm\s+publish",
        r"docker\s+push.*prod",
        r"gh\s+release\s+create",
    ],
}

def detect_risk(command: str) -> dict | None:
    """명령 문자열 → 위험 패턴 매치 시 dict, 아니면 None"""
    for category, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {"category": category, "pattern": pattern, "command": command}
    return None
```

## 명령

- `/approve <task_id>` — 승인 후 실행
- `/reject <task_id>` — 거부 + 사유 입력
- `/approvals` — 대기 중인 승인 list

## 강화 (이중삼중)

1. skill: 이 파일
2. command: `commands/approve.md`, `reject.md`, `approvals.md`
3. handler: `.claude/scripts/approval-gate.py`
4. DB schema: `tasks.approval_state` (마이그레이션 0042)
5. hook: PreToolUse — 위험 명령 감지 시 차단 + waiting_approval 전환
6. CLAUDE.md § 7-23 금지: "위험 작업 승인 없이 실행"

## 참조

- CLAUDE.md § 7-11 (알림 5가지)
- `.claude/rules/best-practices.md` § Zero-touch 자동화
- Anthropic "Building Effective Agents" — human-in-the-loop
- LangGraph human-in-the-loop pattern
