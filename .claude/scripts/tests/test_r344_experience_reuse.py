"""R344 기존 DB(orca.db problem_solutions) 경험 재사용 — 관련성 높고 검증된 기억만 · 노출 수 자기 강화 제거 · 알림 프롬프트 제외.

실측(2026-11-20): 매 프롬프트 같은 [검증완료] 기록(붙여 넣은 세션 인계문)이 주입되며 hits 1096→1128 로 오름 —
낱말 1개 일치로 통과 + 동점 정렬이 hit_count(주입될 때마다 +1). 임시 DB 로만 시험 (운영 DB 쓰기 없음)."""
import importlib.util
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
_spec = importlib.util.spec_from_file_location("inject_experience_r344", ROOT / ".claude" / "hooks" / "prompt" / "inject_experience.py")
ie = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ie)


def _db(tmp_path, rows):
    p = tmp_path / "orca.db"
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE problem_solutions (id INTEGER PRIMARY KEY, problem TEXT, solution TEXT, category TEXT, "
              "reusable_score INTEGER, verified INTEGER, hit_count INTEGER, session_id TEXT, experience_type TEXT, "
              "apply_count INTEGER, last_hit_ts TEXT)")
    c.executemany("INSERT INTO problem_solutions (id,problem,solution,category,reusable_score,verified,hit_count,session_id,"
                  "experience_type,apply_count) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    c.commit()
    c.close()
    return p


def test_single_word_overlap_not_injected_and_apply_beats_hits(tmp_path, monkeypatch):
    monkeypatch.setattr(ie, "DB", _db(tmp_path, [
        (1, "세션 인계문 붙여넣기 claude 새 세션", "claude", "commit", 10, 1, 1128, "", None, 0),       # 낱말 1개만 겹침 (claude)
        (2, "회귀 게이트 메모리 대기 낭비", "절대 여유 판정", "perf", 9, 1, 3, "", None, 5),            # 2개 겹침 · 적용 5
        (3, "회귀 게이트 메모리 대기 반복", "대기 시간 조정", "perf", 9, 1, 900, "", None, 0),          # 2개 겹침 · 노출만 많음
    ]))
    got = ie._find_experiences(["회귀", "게이트", "claude", "메모리"], top=3, current_project="C:/pjt/orchestration_v1")
    ids = [r[0] for r in got]
    assert 1 not in ids                     # 무관 기록(낱말 1개 일치) 제외
    assert ids[:2] == [2, 3]                # 같은 관련도면 노출 수(900) 가 아니라 실제 적용(5) 이 앞


def test_notification_prompt_skipped_without_hit_update(tmp_path, monkeypatch):
    db = _db(tmp_path, [(2, "회귀 게이트 메모리 대기", "x", "perf", 9, 1, 3, "", None, 0)])
    monkeypatch.setattr(ie, "DB", db)
    ctx = SimpleNamespace(payload={"prompt": "<task-notification>\n<task-id>abc</task-id> 회귀 게이트 메모리 완료"},
                          project_dir="C:/pjt/orchestration_v1")
    assert ie.run(ctx) is None
    assert sqlite3.connect(db).execute("SELECT hit_count FROM problem_solutions").fetchone()[0] == 3
    ctx.payload = {"prompt": "회귀 게이트 메모리 대기를 줄여줘"}
    out = ie.run(ctx)
    assert out and "회귀 게이트 메모리 대기" in out
    assert sqlite3.connect(db).execute("SELECT hit_count FROM problem_solutions").fetchone()[0] == 4


def test_unverified_other_project_not_leaked(tmp_path, monkeypatch):
    monkeypatch.setattr(ie, "DB", _db(tmp_path, [
        (5, "ifrs 결산 화면 회귀 게이트", "x", "dev", 9, 0, 0, "ifrs-session", None, 0),            # 미검증 · 다른 프로젝트
        (6, "orchestration 회귀 게이트 정리", "y", "dev", 9, 0, 0, "orchestration-s", None, 0),     # 미검증 · 같은 프로젝트
    ]))
    ids = [r[0] for r in ie._find_experiences(["회귀", "게이트"], current_project="C:/pjt/orchestration_v1")]
    assert ids == [6]
