"""HITL Approval Gate — 위험 작업 감지 + DB 승인 워크플로우.

사용 방법:
  python approval-gate.py detect <command>       # 위험 패턴 매치 -> JSON
  python approval-gate.py request <task_id> <command> <category> <detail>
  (승인·거부는 명령줄 X — 사용자가 프롬프트에 '/approve <id>' · '/reject <id> [사유]' 입력)
  python approval-gate.py list                   # waiting 만
  python approval-gate.py status <task_id>
"""
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from state_db import get_db_path

# 위험 패턴 (CLAUDE.md § 7-11 의 5가지 알림 매트릭스와 정합)
RISK_PATTERNS = {
    "data_loss": [
        (r"\bDROP\s+TABLE\b", "DROP TABLE — 영구 데이터 삭제"),
        (r"\bTRUNCATE\b", "TRUNCATE — 테이블 비우기"),
        # 2026-11-08 P1: 줄 끝 고정($) 이라 닫는 따옴표가 붙으면 못 잡던 것 → 표 이름 뒤 WHERE 유무로 판정
        (r"\bDELETE\s+FROM\s+[\w.\[\]\"`]+(?![\w.\]\"`])(?!\s+WHERE\b)", "DELETE FROM (WHERE 없음) — 전체 삭제"),
        (r"\b(DELETE|UPDATE)\b[^;]*\bWHERE\s+(1\s*=\s*1|true)\b", "WHERE 1=1 — 전체 행 변경"),
        (r"\bUPDATE\s+[\w.\[\]\"`]+\s+SET\b(?![^;]*\bWHERE\b)", "UPDATE (WHERE 없음) — 전체 행 변경"),
        (r"\brm\s+-rf?\s+/\S*", "rm -rf <절대경로> — 시스템/운영 데이터 삭제"),
        (r"\brm\s+-rf?\s+~\S*", "rm -rf ~ — 홈 디렉터리 삭제"),
        (r"\brm\s+-rf?\s+\$\{?HOME\}?", "rm -rf $HOME — 홈 삭제"),
        (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s", "rm -r — 폴더 삭제"),
        (r"\bfind\b[^;&|\n]*\s-delete\b", "find -delete — 일괄 삭제"),
        (r"\brmtree\s*\(", "shutil.rmtree — 폴더 삭제"),
        (r"\bRemove-Item\b[^;\n]*-Recurse\b", "Remove-Item -Recurse — 폴더 삭제"),
        (r"\bgit\s+push\s+--force\b", "force push — 원격 history 덮어쓰기"),
        (r"\bgit\s+reset\s+--hard\b", "git reset --hard — 로컬 변경 손실"),
        (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean -f — 추적 안 된 파일 삭제"),
        (r"\bgit\s+checkout\s+--\s+\.(?=\s|$|[\"'])", "git checkout -- . — 작업 중 변경 폐기"),
        (r"\bgit\s+restore\s+(?:--\S+\s+)*\.(?=\s|$|[\"'])", "git restore . — 작업 중 변경 폐기"),
        (r"\bgit\s+stash\s+(drop|clear)\b", "git stash drop/clear — 보관 변경 삭제"),
        (r"\bgit\s+branch\s+-D\b", "git branch -D — 강제 브랜치 삭제"),
    ],
    "security": [
        (r"^\s*sudo\s+", "sudo — 권한 상승"),
        (r"\bcurl\s+[^|]*\|\s*(bash|sh|python)", "curl | bash — 외부 신뢰 못 한 코드 실행"),
        (r"\bwget\s+[^|]*\|\s*(bash|sh|python)", "wget | sh — 외부 코드 실행"),
        (r"\brunas\s+/user", "runas — 권한 상승"),
        (r"\bchmod\s+\+s\b", "chmod +s — setuid 부여"),
        (r"\b(Invoke-WebRequest|Invoke-RestMethod|iwr|irm|curl|wget|DownloadString)\b[^;\n]*\|\s*(iex|Invoke-Expression)\b",
         "다운로드 내용을 바로 실행 — 외부 코드 실행"),
        (r"\b(iex|Invoke-Expression)\b[^;\n]*\b(Invoke-WebRequest|Invoke-RestMethod|iwr|irm|DownloadString)\b",
         "다운로드 내용을 바로 실행 — 외부 코드 실행"),
        (r"-Verb\s+RunAs\b", "Start-Process -Verb RunAs — 권한 상승"),
        # 2026-11-08 P0-2: 승인 확정은 사용자 프롬프트(/approve) 훅만 한다 — 도구 호출로 승인·DB 변경 X
        # 하위 명령 자리만 (파일 이름 나열 — git add approval-gate.py approve.md — 은 제외 · 2026-11-08 자기 오탐)
        (r"\bapproval[-_]gate(?:\.py)?[\"']?\s+(approve|reject)\b", "자기 승인 — approval-gate approve/reject 직접 호출"),
        (r"\.(approve|reject)\s*\(", "자기 승인 — 승인 함수 직접 호출"),
        (r"\bplatform_api\b[^\n]*\bdecide\b", "자기 승인 — platform_api.decide 직접 호출"),
        (r"\b(UPDATE|INSERT\s+(?:OR\s+\w+\s+)?INTO|REPLACE\s+INTO|DELETE\s+FROM)\s+[\"`\[]?tasks\b", "승인 상태 DB(tasks) 직접 변경"),
        (r"\bapproval_state\s*=\s*['\"]?(approved|executed)", "승인 상태 직접 변경"),
        # 실행·import 만 (컴파일·읽기·검색처럼 파일 이름만 나오는 것은 제외 — 2026-11-08 자기 py_compile 오탐)
        (r"\bpython[\w.]*(?:\s+-[a-zA-Z]+(?:\s+utf8)?)*\s+[\"']?\S*prompt[-_]dispatch\.py|(?:import|from)\s+user_approval\b",
         "사용자 프롬프트 훅 직접 실행 — 승인 위조 경로"),
    ],
    "cost": [
        (r"messages\.batch\.create.*\[.{2000,}", "Batch API 1000+ requests"),
        (r"--(?:set-)?daily-limit\s+\d+", "일일 예산 상한 변경"),
        # 2026-11-08 P0-3: 내부 예산 게이트(dispatch_agent) 밖에서 유료 모델을 직접 부르는 경로
        (r"(?:^|[\s;&|(\"'])codex(?:-a)?(?:\.cmd|\.exe)?\s+(?:exec|e)\b", "codex exec — 유료 모델 직접 호출"),
        (r"(?:^|[\s;&|(\"'])gemini(?:-a)?(?:\.cmd)?\s[^;&|\n]*(?:-p|--prompt)\b", "gemini -p — 유료 모델 직접 호출"),
        (r"(?:^|[\s;&|(\"'])claude(?:\.exe|\.cmd)?\s[^;&|\n]*(?:-p|--print)\b", "claude -p — 유료 모델 직접 호출"),
        (r"\b(api\.anthropic\.com|api\.openai\.com|generativelanguage\.googleapis\.com)\b", "유료 모델 API 직접 호출"),
        (r"\b(anthropic|openai)\b[^\n]*\b(messages|completions|responses)\.create\b", "유료 모델 SDK 직접 호출"),
    ],
    "system": [
        (r"\bsetx\s+\w+", "setx — 영구 환경변수"),
        (r"SetEnvironmentVariable\([^)]*['\"](Machine|User)['\"]", "영구 환경변수 변경"),
        (r"\bSet-ExecutionPolicy\b.*\b(Bypass|Unrestricted)\b", "실행 정책 완화"),
        (r"\breg\s+(add|delete)\s+", "registry 변경"),
        (r"\balembic\s+upgrade\s+head\b", "DB schema 마이그레이션 (운영 영향)"),
        (r"systemctl\s+(enable|disable|mask)", "systemd 서비스 영구 변경"),
        (r">{1,2}\s*[\"']?[^\s;&|\"']*(?:settings(?:\.local)?\.json|(?<![\w-])\.env)(?![\w.-])", "보호 설정 파일 덮어쓰기"),
        (r"\b(cp|mv|copy|move|Copy-Item|Move-Item)\b[^;&|\n]*\s[\"']?\S*(?:settings(?:\.local)?\.json|(?<![\w-])\.env)[\"']?\s*(?:$|[;&|\n])",
         "보호 설정 파일 덮어쓰기"),
        (r"\b(Set-Content|Add-Content|Out-File|tee)\b[^;&|\n]*(?:settings(?:\.local)?\.json|(?<![\w-])\.env)(?![\w.-])", "보호 설정 파일 덮어쓰기"),
        # 2026-11-10 §75: 사용자 전역 Claude 설정(명령·스킬·에이전트·CLAUDE.md·settings) 변경 — 전 프로젝트에 영향.
        #   변수로 경로를 나눠도(G="$HOME/.claude/commands"; cp x "$G/") 같은 글 안에 쓰기 동작과 전역 경로가 함께 있으면 잡는다.
        (r"(?s)\A(?=.*(?:\b(?:cp|mv|rsync|install|robocopy|xcopy|copy|ln|Copy-Item|Move-Item|New-Item|Set-Content|Add-Content"
         r"|Out-File|tee)\b|shutil\.(?:copy|move)|write_(?:text|bytes)\())"
         r"(?=.*(?:\$\{?HOME\}?|~|%USERPROFILE%|%REAL_USERPROFILE%|!REAL_USERPROFILE!|\$env:USERPROFILE|Path\.home\(\)"
         r"|[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+)[\\/\"' ,]+\.claude[\\/\"' ,]+(?:commands|skills|agents|CLAUDE\.md|settings\.json)\b)",
         "사용자 전역 Claude 설정·명령 변경 (모든 프로젝트 영향)"),
    ],
    "irreversible": [
        (r"\bnpm\s+publish\b", "npm publish — 패키지 공개"),
        (r"\bdocker\s+push\b", "docker push — 원격 image 갱신"),
        (r"\bgh\s+(release\s+create|pr\s+merge|repo\s+delete)\b", "github release·merge·repo 삭제"),
        # 2026-11-08 P0-1: 일반 push·-f·+refspec·:branch·--delete·git -C 도 전부 (stash push 는 로컬이라 제외)
        (r"\bgit\b(?![^;&|\n]*\bstash\b)[^;&|\n]*?(?:^|[\s'\"(\[,])push(?=[\s'\"\]),]|$)", "git push — 원격 저장소 변경"),
        (r"\bterraform\s+(apply|destroy)\b", "terraform apply/destroy — 인프라 변경"),
        (r"\bkubectl\s+(apply|delete|replace|patch|rollout|scale)\b", "kubectl — 클러스터 변경"),
        (r"\bvercel\b[^;&|\n]*--prod\b|\b(netlify|firebase)\s+deploy\b", "운영 배포"),
        (r"\bscp\b[^;&|\n]*\s[\w.@-]+:\S*", "scp — 원격 서버로 전송"),
    ],
}

# 승인 1회 사용 유효 시간 (승인 후 이 안에 같은 명령을 실행해야 한다)
APPROVAL_TTL_SEC = 1800
REQUEST_TTL_SEC = 86400   # 대기 요청 유효 기간 (approval-gate-rules.md § 승인 만료 24시간) — 지나면 승인 거부·재요청
CONSUMED_RESULT_WAIT_SEC = 660   # 도구 최대 실행 600초 + 여유 — 이 안에는 실행 중인 행을 새 요청으로 덮지 않는다
USER_APPROVER = "user-prompt"   # 사용자 프롬프트 훅(prompt/user_approval.py) 만 쓰는 승인자 표시


def detect_risk(command: str) -> dict | None:
    """명령 문자열 -> 매치된 위험 dict 반환 (또는 None).
    2026-11-09: 셸은 따옴표·이스케이프를 지운 뒤 실행한다 ("gi"t · g\\it · gi''t · ^git → git) →
    따옴표·이스케이프 문자를 뺀 형태도 같이 검사 (원문에서 패턴이 끊겨 통과하던 우회)."""
    variants = [command]
    dequoted = re.sub(r"[\"'\\^`]", "", command)
    if dequoted != command:
        variants.append(dequoted)
    for category, patterns in RISK_PATTERNS.items():
        for pattern, desc in patterns:
            if any(re.search(pattern, v, re.IGNORECASE | re.MULTILINE) for v in variants):
                return {
                    "category": category,
                    "pattern": pattern,
                    "description": desc,
                    "command": command[:500],
                }
    return None


# ── 2026-11-09 승인 요청 불변성 ──────────────────────────────────────────
# 요청 번호를 명령+폴더 지문으로만 정하면, 범위(HEAD·스크립트 내용)가 달라져도 같은 행을 덮어쓰고
# 실행 완료·만료 기록도 다시 요청할 때 덮였다. → 범위 지문(scope)을 저장하고, 범위가 다르거나
# 이전 요청이 끝났으면 항상 새 번호로 새 행을 만든다. 기존 행은 상태 전이(승인·소비·결과·만료) 외에 고치지 않는다.
def scope_key(base: str, artifacts: dict | None) -> str:
    """명령·폴더 지문(base) + 실행 대상(스크립트 해시·push HEAD·ref·브랜치·원격) → 범위 지문."""
    import hashlib as _h
    body = base + "\n" + json.dumps(artifacts or {}, sort_keys=True, ensure_ascii=True)
    return _h.sha256(body.encode("utf-8")).hexdigest()[:16]


def find_request(field: str, value: str, states: tuple) -> str | None:
    """risk_detail[field] == value 이고 approval_state 가 states 중인 가장 최근 승인 게이트 행."""
    if not value or not states:
        return None
    conn = sqlite3.connect(str(get_db_path()))
    try:
        rows = conn.execute(
            "SELECT task_id, risk_detail, approval_state, created_at FROM tasks WHERE task_file = '<approval-gate>' "
            "AND approval_state IN (%s) AND risk_detail LIKE ? ORDER BY created_at DESC, rowid DESC"
            % ",".join("?" * len(states)), (*states, "%" + value + "%")).fetchall()
        now = int(time.time())
        rows = [(t, d) for t, d, st, c in rows   # 만료된 대기 요청은 다시 안내하지 않는다 (새 요청)
                if not (st == "waiting" and c and now - int(c) > REQUEST_TTL_SEC)]
    finally:
        conn.close()
    for tid, detail in rows:
        try:
            if (json.loads(detail or "{}") or {}).get(field) == value:
                return tid
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


def new_request(command: str, category: str, detail: str, artifacts: dict | None, base: str, scope: str) -> str:
    """항상 새 번호로 새 대기 요청 행을 만든다 (기존 행 수정 없음)."""
    import hashlib as _h
    task_id = "appr-" + _h.sha256(("%s\n%s\n%s" % (scope, time.time_ns(), os.urandom(8).hex())).encode()).hexdigest()[:12]
    risk = {"command": command, "detail": detail, "base": base, "scope": scope}
    if artifacts:
        risk["artifacts"] = artifacts
    conn = sqlite3.connect(str(get_db_path()))
    try:
        conn.execute(
            "INSERT INTO tasks (task_id, task_file, status, created_at, approval_state, risk_category, risk_detail) "
            "VALUES (?, '<approval-gate>', 'waiting_approval', ?, 'waiting', ?, ?)",
            (task_id, int(time.time()), category, json.dumps(risk, ensure_ascii=False)))
        conn.commit()
    finally:
        conn.close()
    return task_id


def request_approval(task_id: str, command: str, category: str, detail: str, artifacts: dict | None = None) -> dict:
    """task 를 waiting_approval state 로 전환.

    artifacts = {스크립트 경로: sha256} — 명령이 실행하는 파일의 승인 시점 내용 (2026-11-09).
    소비할 때 다시 계산해 다르면 그 승인은 쓰지 않는다 (승인 후 스크립트 변경 차단)."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        # task 존재 확인 — 없으면 stub 삽입
        cur = conn.execute("SELECT task_id FROM tasks WHERE task_id = ?", (task_id,))
        row = cur.fetchone()
        now = int(time.time())
        risk = {"command": command, "detail": detail}
        if artifacts:
            risk["artifacts"] = artifacts
        risk_json = json.dumps(risk, ensure_ascii=False)
        if not row:
            conn.execute(
                "INSERT INTO tasks (task_id, task_file, status, created_at, "
                "approval_state, risk_category, risk_detail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task_id, "<approval-gate>", "waiting_approval", now,
                 "waiting", category, risk_json),
            )
        else:
            # 실행 중(consumed)인 행은 덮지 않는다 — 동시 실행 때 결과 기록(record_result)이 사라지던 경합 (2026-11-09 리뷰).
            # 단 도구 최대 실행 시간이 지나도 결과가 없으면(실패·중단) 다시 요청할 수 있어야 한다 → 그때만 덮는다.
            cur_row = conn.execute("SELECT approval_state, risk_detail FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if cur_row and cur_row[0] == "consumed":
                try:
                    consumed_at = int((json.loads(cur_row[1] or "{}") or {}).get("consumed_at") or 0)
                except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
                    consumed_at = 0
                if now - consumed_at < CONSUMED_RESULT_WAIT_SEC:
                    return {"task_id": task_id, "state": "consumed", "category": category}
            conn.execute(
                "UPDATE tasks SET status = 'waiting_approval', "
                "approval_state = 'waiting', risk_category = ?, risk_detail = ? "
                "WHERE task_id = ?",
                (category, risk_json, task_id),
            )
        conn.commit()
        return {"task_id": task_id, "state": "waiting_approval", "category": category}
    finally:
        conn.close()


def approve(task_id: str, by: str = "user") -> dict:
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            "SELECT approval_state, risk_category, risk_detail, created_at FROM tasks WHERE task_id = ?",
            (task_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": f"task_id {task_id} not found"}
        if row[0] != "waiting":
            return {"error": f"task_id {task_id} not waiting (current: {row[0]})"}
        now = int(time.time())
        # 2026-11-09: 24시간 지난 대기 요청은 승인하지 않는다 (기록은 그대로 · 같은 명령을 다시 내면 새 요청)
        if row[3] and now - int(row[3]) > REQUEST_TTL_SEC:
            return {"error": f"task_id {task_id} 대기 {(now - int(row[3])) // 3600}시간 — 24시간 지난 요청은 만료 · "
                             "같은 명령을 다시 실행해 새 요청을 확인한 뒤 승인"}
        conn.execute(
            "UPDATE tasks SET approval_state = 'approved', status = 'pending', "
            "approved_at = ?, approved_by = ? WHERE task_id = ?",
            (now, by, task_id),
        )
        conn.commit()
        return {"task_id": task_id, "state": "approved", "by": by, "at": now,
                "risk_category": row[1], "risk_detail": row[2]}
    finally:
        conn.close()


def reject(task_id: str, by: str = "user", reason: str = "") -> dict:
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            "SELECT approval_state, risk_detail FROM tasks WHERE task_id = ?", (task_id,)
        )
        row = cur.fetchone()
        if not row:
            return {"error": f"task_id {task_id} not found"}
        if row[0] != "waiting":
            return {"error": f"task_id {task_id} not waiting (current: {row[0]})"}
        now = int(time.time())
        # risk_detail 에 reason 머지
        try:
            detail = json.loads(row[1]) if row[1] else {}
        except json.JSONDecodeError:
            detail = {}
        detail["reject_reason"] = reason
        conn.execute(
            "UPDATE tasks SET approval_state = 'rejected', status = 'cancelled', "
            "approved_at = ?, approved_by = ?, risk_detail = ? WHERE task_id = ?",
            (now, by, json.dumps(detail, ensure_ascii=False), task_id),
        )
        conn.commit()
        return {"task_id": task_id, "state": "rejected", "by": by, "reason": reason}
    finally:
        conn.close()


def _merge_detail(raw, **kv) -> str:
    try:
        d = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        d = {"raw": raw}
    if not isinstance(d, dict):
        d = {"raw": d}
    d.update(kv)
    return json.dumps(d, ensure_ascii=False)


def consume_approval(task_id: str, ttl: int = APPROVAL_TTL_SEC, artifacts: dict | None = None) -> str:
    """같은 명령·같은 위치(task_id 가 그 지문)에 대한 사용자 승인 1회 사용.

    상태 뜻 (2026-11-09 · 소비 ≠ 실행 결과):
      approval_state 'consumed' + status 'running' = 승인 1회 사용됨 · 명령 실행 허가 · 결과는 아직 모름
      approval_state 'executed' = 도구 실행이 끝남 (record_result) · 성공/실패는 status 와 risk_detail.result
      실패·중단으로 결과를 못 받으면 'consumed'/'running' 그대로 = 결과 미확인 (성공으로 세지 않는다)
    반환:
      'consumed' = 사용자 프롬프트 승인 · ttl 안 · 승인 때 스크립트 내용과 같음 → 1회 통과
      'changed'  = 승인 뒤 스크립트 내용이 바뀜 → 그 승인 만료 · 호출자가 새로 요청 (fail-closed)
      'waiting'  = 아직 승인 대기 (새 요청 번호 만들지 않음)
      'none'     = 행 없음·거부·만료·이미 사용 → 호출자가 새로 요청 (기존 행 재사용)
    """
    conn = sqlite3.connect(str(get_db_path()))
    try:
        row = conn.execute("SELECT approval_state, risk_detail FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not row:
            return "none"
        if row[0] == "waiting":
            return "waiting"
        now = int(time.time())
        cond = "WHERE task_id = ? AND approval_state = 'approved' AND approved_by = ? AND approved_at >= ?"
        args = (task_id, USER_APPROVER, now - ttl)
        try:
            approved_arts = (json.loads(row[1]) if row[1] else {}).get("artifacts")
        except (json.JSONDecodeError, AttributeError):
            approved_arts = None
        # 2026-11-09: 양쪽 비교 — 승인 때 없던 항목(예: push 의 git:HEAD)이 실행 때 생겨도 '다름' (종전: 승인 쪽이 비면 통과)
        approved_arts = approved_arts or {}
        if approved_arts != (artifacts or {}):
            changed = sorted(p for p in set(approved_arts) | set(artifacts or {})
                             if approved_arts.get(p) != (artifacts or {}).get(p))
            n = conn.execute(
                "UPDATE tasks SET approval_state = 'expired', status = 'cancelled', risk_detail = ? " + cond,
                (_merge_detail(row[1], expire_reason="script_changed", changed=changed, checked_at=now),) + args,
            ).rowcount
            conn.commit()
            return "changed" if n == 1 else "none"
        n = conn.execute(
            "UPDATE tasks SET approval_state = 'consumed', status = 'running', risk_detail = ? " + cond,
            (_merge_detail(row[1], consumed_at=now),) + args,
        ).rowcount
        conn.commit()
        return "consumed" if n == 1 else "none"
    finally:
        conn.close()


def record_result(task_id: str, outcome: str, info: dict | None = None) -> bool:
    """소비된 승인의 실행 결과 기록 (PostToolUse). outcome: 'finished' | 'interrupted' | 'error'.

    'finished' 는 도구가 정상 반환했다는 뜻이다 — 명령 자체의 성공 판정은 info(출력 요약)로 남긴다.
    consumed 가 아닌 행(이미 기록·만료·없음)은 건드리지 않는다."""
    conn = sqlite3.connect(str(get_db_path()))
    try:
        row = conn.execute("SELECT risk_detail FROM tasks WHERE task_id = ? AND approval_state = 'consumed'",
                           (task_id,)).fetchone()
        if not row:
            return False
        now = int(time.time())
        result = {"outcome": outcome, "finished_at": now}
        result.update(info or {})
        n = conn.execute(
            "UPDATE tasks SET approval_state = 'executed', status = ?, completed_at = ?, risk_detail = ? "
            "WHERE task_id = ? AND approval_state = 'consumed'",
            ("done" if outcome == "finished" else "failed", now, _merge_detail(row[0], result=result), task_id),
        ).rowcount
        conn.commit()
        return n == 1
    finally:
        conn.close()


def list_waiting() -> list:
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            "SELECT task_id, risk_category, risk_detail, created_at FROM tasks "
            "WHERE approval_state = 'waiting' ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        out = []
        for tid, cat, detail, ts in rows:
            try:
                d = json.loads(detail) if detail else {}
            except json.JSONDecodeError:
                d = {"raw": detail}
            out.append({
                "task_id": tid,
                "category": cat,
                "command_preview": (d.get("command") or "")[:120],
                "detail": d.get("detail", ""),
                "age_sec": int(time.time()) - (ts or 0),
            })
        return out
    finally:
        conn.close()


def status(task_id: str) -> dict:
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            "SELECT approval_state, risk_category, risk_detail, approved_at, approved_by, "
            "status FROM tasks WHERE task_id = ?",
            (task_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": f"task_id {task_id} not found"}
        return {
            "task_id": task_id,
            "approval_state": row[0],
            "risk_category": row[1],
            "risk_detail": json.loads(row[2]) if row[2] else None,
            "approved_at": row[3],
            "approved_by": row[4],
            "status": row[5],
        }
    finally:
        conn.close()


def main():
    # Windows cp949 회피 — stdout UTF-8 강제
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        pass  # noqa: BLE001
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "detect":
        command = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else sys.stdin.read()
        result = detect_risk(command)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result is None else 10)  # exit 10 = 위험 감지
    elif cmd == "request" and len(sys.argv) >= 5:
        task_id, command, category = sys.argv[2], sys.argv[3], sys.argv[4]
        detail = sys.argv[5] if len(sys.argv) > 5 else ""
        result = request_approval(task_id, command, category, detail)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd in ("approve", "reject"):
        # 2026-11-08 P0-2: 명령줄 승인은 누가 실행했는지 알 수 없다 (Agent 도 같은 권한) → 사용자 프롬프트 /approve 로만
        print(json.dumps({"error": "명령줄 승인·거부 비활성 — 사용자가 프롬프트에 직접 '/approve <id>' 또는 "
                                   "'/reject <id> [사유]' 를 입력해야 기록된다 (prompt/user_approval.py)"},
                         ensure_ascii=False, indent=2))
        sys.exit(3)
    elif cmd == "list":
        print(json.dumps(list_waiting(), ensure_ascii=False, indent=2))
    elif cmd == "status" and len(sys.argv) >= 3:
        print(json.dumps(status(sys.argv[2]), ensure_ascii=False, indent=2))
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
