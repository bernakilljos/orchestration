"""HITL Approval Gate — 위험 작업 감지 + DB 승인 워크플로우.

사용 방법:
  python approval-gate.py detect <command>       # 위험 패턴 매치 -> JSON
  python approval-gate.py request <task_id> <command> <category> <detail>
  python approval-gate.py approve <task_id> [by]
  python approval-gate.py reject  <task_id> [by] [reason]
  python approval-gate.py list                   # waiting 만
  python approval-gate.py status <task_id>
"""
import json
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
        (r"\bDELETE\s+FROM\s+\w+\s*;?\s*$", "DELETE FROM (WHERE 없음) — 전체 삭제"),
        (r"\brm\s+-rf\s+[/~]\s*$", "rm -rf / — 루트 삭제"),
        (r"\brm\s+-rf\s+\$HOME", "rm -rf $HOME — 홈 삭제"),
        (r"\bgit\s+push\s+--force\b", "force push — 원격 history 덮어쓰기"),
        (r"\bgit\s+reset\s+--hard\s+(origin|upstream)/", "git reset --hard remote — 로컬 변경 손실"),
        (r"\bgit\s+branch\s+-D\b", "git branch -D — 강제 브랜치 삭제"),
    ],
    "security": [
        (r"^\s*sudo\s+", "sudo — 권한 상승"),
        (r"\bcurl\s+[^|]*\|\s*(bash|sh|python)", "curl | bash — 외부 신뢰 못 한 코드 실행"),
        (r"\bwget\s+[^|]*\|\s*(bash|sh|python)", "wget | sh — 외부 코드 실행"),
        (r"\brunas\s+/user", "runas — 권한 상승"),
        (r"\bchmod\s+\+s\b", "chmod +s — setuid 부여"),
    ],
    "cost": [
        (r"messages\.batch\.create.*\[.{2000,}", "Batch API 1000+ requests"),
        (r"--daily-limit\s+\d{3,}", "daily limit 100+ USD"),
    ],
    "system": [
        (r"\bsetx\s+\w+", "setx — 영구 환경변수"),
        (r"\breg\s+(add|delete)\s+", "registry 변경"),
        (r"\balembic\s+upgrade\s+head\b", "DB schema 마이그레이션 (운영 영향)"),
        (r"systemctl\s+(enable|disable|mask)", "systemd 서비스 영구 변경"),
    ],
    "irreversible": [
        (r"\bnpm\s+publish\b", "npm publish — 패키지 공개"),
        (r"\bdocker\s+push\s+.*:(prod|latest)\b", "docker push prod — 운영 image 갱신"),
        (r"\bgh\s+release\s+create\b", "github release 생성"),
        (r"\bgit\s+push\s+(origin|upstream)\s+--tags", "tag push — 버전 publish"),
        (r"\bterraform\s+apply\b.*-auto-approve", "terraform apply -auto-approve — 인프라 변경"),
    ],
}


def detect_risk(command: str) -> dict | None:
    """명령 문자열 -> 매치된 위험 dict 반환 (또는 None)."""
    for category, patterns in RISK_PATTERNS.items():
        for pattern, desc in patterns:
            if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
                return {
                    "category": category,
                    "pattern": pattern,
                    "description": desc,
                    "command": command[:500],
                }
    return None


def request_approval(task_id: str, command: str, category: str, detail: str) -> dict:
    """task 를 waiting_approval state 로 전환."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        # task 존재 확인 — 없으면 stub 삽입
        cur = conn.execute("SELECT task_id FROM tasks WHERE task_id = ?", (task_id,))
        row = cur.fetchone()
        now = int(time.time())
        risk_json = json.dumps({"command": command, "detail": detail}, ensure_ascii=False)
        if not row:
            conn.execute(
                "INSERT INTO tasks (task_id, task_file, status, created_at, "
                "approval_state, risk_category, risk_detail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task_id, "<approval-gate>", "waiting_approval", now,
                 "waiting", category, risk_json),
            )
        else:
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
            "SELECT approval_state, risk_category, risk_detail FROM tasks WHERE task_id = ?",
            (task_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"error": f"task_id {task_id} not found"}
        if row[0] != "waiting":
            return {"error": f"task_id {task_id} not waiting (current: {row[0]})"}
        now = int(time.time())
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
        pass
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
    elif cmd == "approve" and len(sys.argv) >= 3:
        result = approve(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "user")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "reject" and len(sys.argv) >= 3:
        by = sys.argv[3] if len(sys.argv) > 3 else "user"
        reason = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        result = reject(sys.argv[2], by, reason)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "list":
        print(json.dumps(list_waiting(), ensure_ascii=False, indent=2))
    elif cmd == "status" and len(sys.argv) >= 3:
        print(json.dumps(status(sys.argv[2]), ensure_ascii=False, indent=2))
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
