"""R303 P0 — 요청 원장 데이터 손실 재발 방지 시험 (모두 임시 폴더 · 운영 원장은 해시로 불변 확인만).

재현하는 사고: 시험이 운영 원장을 덮어 292건 → 1건. 구조 원인 4가지 각각을 막는지 본다.
"""
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER_PY = ROOT / ".claude" / "scripts" / "request-ledger.py"
HOOK_DIR = ROOT / ".claude" / "hooks" / "prompt"
REAL = ROOT / ".claude" / "state" / "request-ledger.json"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "-"


def _env(tmp_path, **extra):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1"}
    env.pop("ORCA_TEST_MODE", None)
    env.update(extra)
    return env


def _run(tmp_path, *args, **extra):
    return subprocess.run([sys.executable, "-X", "utf8", str(LEDGER_PY), *args], env=_env(tmp_path, **extra),
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)


def _ledger(tmp_path):
    return tmp_path / ".claude" / "state" / "request-ledger.json"


def _seed(tmp_path, n):
    p = _ledger(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    reqs = [{"id": f"R{i}", "desc": f"요청 {i}", "status": "completed", "ts": "2026-11-18T00:00:00",
             "evidence": f"증거 {i}", "verification": "PASS"} for i in range(1, n + 1)]
    p.write_text(json.dumps({"session_id": "s", "created_at": "t", "requests": reqs}, ensure_ascii=False), encoding="utf-8")
    return p


def _ids(tmp_path):
    return [r["id"] for r in json.loads(_ledger(tmp_path).read_text(encoding="utf-8"))["requests"]]


def test_operational_ledger_write_blocked_in_test_process():
    """② 시험 프로세스(ORCA_TEST_MODE)가 CLAUDE_PROJECT_DIR 없이 돌면 운영 원장에 못 쓴다."""
    before = _sha(REAL)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env.update({"ORCA_TEST_MODE": "1", "PYTHONUTF8": "1"})
    r = subprocess.run([sys.executable, "-X", "utf8", str(LEDGER_PY), "add", "R303 시험 — 운영 원장에 들어가면 안 됨"],
                       env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 3, r.stderr
    assert "운영 원장 쓰기 차단" in r.stderr
    assert _sha(REAL) == before


def test_corrupt_ledger_recovers_from_prev_and_never_shrinks(tmp_path):
    """① 사고 재현: 원장이 반쪽 파일이 된 상태에서 add → 예전에는 빈 원장으로 시작해 1건만 남았다."""
    _seed(tmp_path, 292)
    assert _run(tmp_path, "add", "첫 저장 (직전본 생성)").returncode == 0
    assert (tmp_path / ".claude" / "state" / "request-ledger.prev.json").exists()
    _ledger(tmp_path).write_text('{"requests": [{"id": "R1"', encoding="utf-8")  # 쓰는 도중 끊긴 모양
    r = _run(tmp_path, "add", "깨진 뒤 등록")
    assert r.returncode == 0, r.stderr
    ids = _ids(tmp_path)
    assert len(ids) == 294 and len(set(ids)) == 294
    assert ids[:292] == [f"R{i}" for i in range(1, 293)]


def test_corrupt_without_backup_refuses_instead_of_overwriting(tmp_path):
    p = _ledger(tmp_path)
    p.parent.mkdir(parents=True)
    p.write_text("{깨짐", encoding="utf-8")
    r = _run(tmp_path, "add", "덮어쓰면 안 됨")
    assert r.returncode == 3 and "백업 없음" in r.stderr
    assert p.read_text(encoding="utf-8") == "{깨짐"


def test_save_refuses_lost_or_duplicate_ids(tmp_path, monkeypatch):
    """④ 기존 ID 가 사라지는 저장·ID 중복 저장은 거부 (원장 = 추가만)."""
    import importlib.util
    _seed(tmp_path, 5)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    spec = importlib.util.spec_from_file_location("rl303", LEDGER_PY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    import pytest
    with pytest.raises(m.LedgerError, match="사라짐"):
        m._save({"session_id": "test", "requests": [{"id": "T_R1", "status": "pending"}]})  # 골든 시험이 하던 덮어쓰기
    with pytest.raises(m.LedgerError, match="중복"):
        d = m._load()
        d["requests"].append(dict(d["requests"][0]))
        m._save(d)
    assert len(_ids(tmp_path)) == 5


def test_concurrent_cli_and_hook_writes_lose_nothing(tmp_path):
    """③ 여러 세션 동시: CLI add 12개 + 프롬프트 hook 등록 12개를 동시에 → 24건 전부 · ID 고유."""
    _seed(tmp_path, 10)
    hook_code = (
        "import sys,os; sys.path.insert(0, os.environ['HOOK_DIR']);"
        "import ledger_auto_register as M;"
        "r=M._append_ledger_entry(sys.argv[1], 'sess-'+sys.argv[2], 'execute');"
        "print(r); sys.exit(0 if r.get('status')=='registered' else 1)")

    def cli(i):
        r = _run(tmp_path, "add", f"동시 CLI {i}")
        return r.returncode, (r.stdout + r.stderr)[-300:]

    def hook(i):
        r = subprocess.run([sys.executable, "-X", "utf8", "-c", hook_code, f"동시 hook {i} 해줘", str(i)],
                           env=_env(tmp_path, HOOK_DIR=str(HOOK_DIR)), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=90)
        return r.returncode, (r.stdout + r.stderr)[-300:]

    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(cli, range(12))) + list(ex.map(hook, range(12)))
    assert [rc for rc, _ in res] == [0] * 24, [o for rc, o in res if rc]
    ids = _ids(tmp_path)
    assert len(ids) == 34 and len(set(ids)) == 34
    descs = [r["desc"] for r in json.loads(_ledger(tmp_path).read_text(encoding="utf-8"))["requests"]]
    assert sum(d.startswith("동시 CLI") for d in descs) == 12 and sum(d.startswith("동시 hook") for d in descs) == 12
    assert not (tmp_path / ".claude" / "state" / "request-ledger.json.lock").exists()


def test_stale_lock_is_reclaimed(tmp_path):
    _seed(tmp_path, 1)
    lock = tmp_path / ".claude" / "state" / "request-ledger.json.lock"
    lock.write_text("99999 0", encoding="utf-8")
    os.utime(lock, (1, 1))  # 죽은 프로세스가 남긴 오래된 잠금
    assert _run(tmp_path, "add", "잠금 회수").returncode == 0
    assert len(_ids(tmp_path)) == 2


def test_clear_archives_instead_of_deleting(tmp_path):
    _seed(tmp_path, 3)
    assert _run(tmp_path, "clear").returncode == 0
    kept = list((tmp_path / ".claude" / "state").glob("request-ledger.cleared-*.json"))
    assert len(kept) == 1 and len(json.loads(kept[0].read_text(encoding="utf-8"))["requests"]) == 3


def test_next_id_uses_max_not_count(tmp_path):
    p = _seed(tmp_path, 3)
    d = json.loads(p.read_text(encoding="utf-8"))
    d["requests"][1]["id"] = "R7"  # 번호에 빈칸이 있어도 중복 번호를 만들지 않는다
    p.write_text(json.dumps(d), encoding="utf-8")
    assert _run(tmp_path, "add", "다음 번호").returncode == 0
    assert _ids(tmp_path)[-1] == "R8"


def test_golden_gate_concurrent_does_not_touch_operational_ledger():
    """사고 원래 경로 — golden-test 의 원장 시험 3개 동시 실행 뒤에도 운영 원장 해시 불변."""
    import importlib.util
    def ids():  # 실제 다른 세션이 그 사이 추가할 수는 있다 → 해시 대신 "기존 ID 전부 유지 + 시험 데이터 없음"
        return [r["id"] for r in json.loads(REAL.read_text(encoding="utf-8"))["requests"]] if REAL.exists() else []
    before = ids()
    spec = importlib.util.spec_from_file_location("golden303", ROOT / ".claude" / "scripts" / "golden-test.py")
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(lambda _: g._run_gate_test(), range(3)))
    after = ids()
    assert after[:len(before)] == before and "T_R1" not in after
