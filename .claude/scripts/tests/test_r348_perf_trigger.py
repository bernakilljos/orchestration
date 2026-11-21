"""R354 13차 큐 중 발견: 성능 게이트 «상태줄 1회» 트리거가 lib/*.py 전체라, 상태줄이 불러오지도 않는 모듈
(independent_verifier.py · R348#1) 을 바꿔도 측정·차단됐다 (같은 조건 교대 측정 HEAD 568ms · 변경 666ms 범위 겹침 ·
-X importtime 에 independent_verifier 없음). 트리거 = 상태줄이 실제로 여는 저장소 파일 + 상태줄 자신.
반대 방향(상태줄이 새 모듈을 불러오는데 트리거에 없음)을 이 시험이 실제 실행으로 막는다."""
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROBE = Path(__file__).resolve().parent / "fixtures" / "statusline_open_probe.py"


def _item(name):
    cfg = json.loads((ROOT / ".claude" / "config" / "perf-budget.json").read_text(encoding="utf-8"))
    return next(i for i in cfg["items"] if i["name"] == name)


def _loaded():
    r = subprocess.run([sys.executable, "-X", "utf8", str(PROBE), str(ROOT)], capture_output=True, text=True,
                       encoding="utf-8", timeout=120, cwd=str(ROOT))
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_statusline_trigger_covers_every_loaded_repo_module():
    loaded = _loaded()
    # trace.py 는 추적·원장 상태가 있을 때만 열린다 (CI 러너엔 없음 · a2d5cb83 Windows 필수 잡 실패 원인) → 상태줄 자신만 필수
    assert ".claude/scripts/statusline_context.py" in loaded, loaded
    trig = _item("상태줄 1회")["triggers"]
    missing = [p for p in loaded if not any(fnmatch.fnmatch(p, g) for g in trig)]
    assert not missing, f"상태줄이 여는데 성능 트리거에 없는 파일: {missing}"


def test_statusline_trigger_not_whole_lib():
    trig = _item("상태줄 1회")["triggers"]
    assert ".claude/scripts/lib/*.py" not in trig
    assert not any(fnmatch.fnmatch(".claude/scripts/lib/independent_verifier.py", g) for g in trig)
