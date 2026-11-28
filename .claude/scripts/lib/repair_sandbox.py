"""repair_sandbox.py — 2026-10-26 외부 AI P1 (Verified Repair 격리 실행).

Git worktree 기반 격리 수정 환경. 수정 → 테스트 → 성공 시만 main 반영 · 실패 시 폐기.
외부 AI 완료 기준 #5 (수정 실패 시 원래 코드 안전 복구) 해결.

흐름:
  create <goal_id>  → .repair-sandbox/<goal_id>/ worktree 생성 (repair/<goal_id> branch)
  test   <goal_id>  → 격리 환경에서 pytest/vitest/custom test cmd 실행 → exit code 리턴
  apply  <goal_id>  → fast-forward merge to main (성공한 변경만)
  discard <goal_id> → worktree 폐기 + branch 삭제 (원본 보호)
  list              → 활성 sandbox 목록

Supervisor REPAIR workflow 와 연계:
  Supervisor goal #N (status=RUNNING) → sandbox create → repair agent 수정 → test → VERIFIED or REPAIRING → apply or discard

best-effort: git worktree 미지원·실패 시 fallback (현재 branch 그대로 작업).
"""
from __future__ import annotations
import os
import sys
import json
import time
import subprocess
import shutil
import tempfile
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
# 2026-10-30 Phase 10-R1: 테스트/운영 Sandbox Root 분리.
#   운영 = ROOT/.repair-sandbox (state: .claude/state/repair-sandboxes.json)
#   테스트 = REPAIR_SANDBOX_ROOT env (기본 TEMP 아래) · state 도 그 root 안 별도 파일
#   → 테스트의 cleanup/discard 는 운영 state·worktree 를 볼 수조차 없다.
OPERATIONAL_SANDBOX_ROOT = ROOT / ".repair-sandbox"
OPERATIONAL_STATE_FILE = ROOT / ".claude" / "state" / "repair-sandboxes.json"
TEST_SANDBOX_ROOT = Path(tempfile.gettempdir()) / "orca-repair-sandbox-test" / ROOT.name


def _resolve_roots():
    env_root = os.environ.get("REPAIR_SANDBOX_ROOT", "").strip()
    root = Path(env_root).resolve() if env_root else OPERATIONAL_SANDBOX_ROOT
    operational = root.resolve() == OPERATIONAL_SANDBOX_ROOT.resolve()
    state = OPERATIONAL_STATE_FILE if operational else root / "_sandbox-state.json"
    return root, state, operational


SANDBOX_ROOT, STATE_FILE, IS_OPERATIONAL_ROOT = _resolve_roots()


def use_test_root() -> Path:
    """테스트 전용 root 로 전환. env 도 설정하므로 supervisor 가 파일로 재로딩한 사본도 같은 root 를 쓴다."""
    global SANDBOX_ROOT, STATE_FILE, IS_OPERATIONAL_ROOT
    os.environ["REPAIR_SANDBOX_ROOT"] = str(TEST_SANDBOX_ROOT)
    SANDBOX_ROOT, STATE_FILE, IS_OPERATIONAL_ROOT = _resolve_roots()
    return SANDBOX_ROOT


def _inside_root(path: Path) -> bool:
    """현재 SANDBOX_ROOT 아래 경로인지 — 다른 root(운영↔테스트) 의 worktree 삭제 차단."""
    try:
        Path(path).resolve().relative_to(SANDBOX_ROOT.resolve())
        return True
    except Exception:
        return False


def _git(*args: str, cwd: Path = None, check: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
    """git 명령 실행 (ALLOW_VISIBLE_WINDOW env 로 Pre-Execution hook 호환).
    2026-10-26 fix: Python 3.14 Windows subprocess reader thread bug — encoding/errors 명시.
    timeout 300s default (git worktree add 가 Windows + 큰 kit 디렉토리에서 느림)."""
    env = os.environ.copy()
    env["ALLOW_VISIBLE_WINDOW"] = "1"
    try:
        return subprocess.run(
            ["git"] + list(args),
            cwd=str(cwd or ROOT),
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except Exception as e:
        # subprocess 자체 fail — dummy CompletedProcess 리턴 (호출자 returncode 체크 가능)
        return subprocess.CompletedProcess(
            args=["git"] + list(args),
            returncode=1,
            stdout="",
            stderr=f"[_git subprocess failure] {type(e).__name__}: {e}",
        )


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _policy() -> dict:
    p = ROOT / ".claude" / "config" / "sandbox-policy.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def commit_memory() -> dict:
    """가상 메모리(Commit) 사용량·한도·여유 (GB). RAM % 와 별개 지표다.
    2026-11-01 15:50 실측: RAM 68% 인데 commit 한도에 닿아 psutil 이 WinError 1455 (페이징 파일 부족) 로 실패.
    측정 불가 = measured False (0 으로 채우지 않는다)."""
    gb = lambda b: round(b / 1024 ** 3, 2)
    try:
        if os.name == "nt":
            import ctypes

            class _PI(ctypes.Structure):
                _fields_ = [("cb", ctypes.c_ulong), ("CommitTotal", ctypes.c_size_t),
                            ("CommitLimit", ctypes.c_size_t), ("CommitPeak", ctypes.c_size_t),
                            ("PhysicalTotal", ctypes.c_size_t), ("PhysicalAvailable", ctypes.c_size_t),
                            ("SystemCache", ctypes.c_size_t), ("KernelTotal", ctypes.c_size_t),
                            ("KernelPaged", ctypes.c_size_t), ("KernelNonpaged", ctypes.c_size_t),
                            ("PageSize", ctypes.c_size_t), ("HandleCount", ctypes.c_ulong),
                            ("ProcessCount", ctypes.c_ulong), ("ThreadCount", ctypes.c_ulong)]
            pi = _PI()
            pi.cb = ctypes.sizeof(pi)
            if not ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(pi), pi.cb):
                return {"measured": False, "reason": "GetPerformanceInfo failed"}
            used, limit = pi.CommitTotal * pi.PageSize, pi.CommitLimit * pi.PageSize
            phys = pi.PhysicalAvailable * pi.PageSize          # R339: 물리 RAM 여유 (commit 과 별개 지표)
        else:
            info = {}
            with open("/proc/meminfo", encoding="utf-8") as f:
                for line in f:
                    k, v = line.split(":", 1)
                    info[k] = int(v.split()[0]) * 1024
            used, limit = info["Committed_AS"], info["CommitLimit"]
            phys = info.get("MemAvailable")
    except Exception as e:
        return {"measured": False, "reason": f"{type(e).__name__}: {e}"[:200]}
    if not limit:
        return {"measured": False, "reason": "commit limit 0"}
    out = {"measured": True, "used_gb": gb(used), "limit_gb": gb(limit), "free_gb": gb(limit - used),
           "percent": round(used * 100 / limit, 1)}
    if phys is not None:
        out["phys_free_gb"] = gb(phys)
    return out


ADMISSION_LEVELS = ("normal", "constrained", "blocked", "unknown")
_ADM_THREAD_LOCK = threading.Lock()


def _num(raw, default: float, lo: float, hi: float, bad: list, key: str) -> float:
    """정책·환경 값 검증 — 숫자 아님·NaN·무한·범위 밖이면 기본값 + 진단 기록 (잘못된 설정이 판정을 느슨하게 만들지 않게)."""
    import math
    try:
        v = float(raw)
        if math.isfinite(v) and lo <= v <= hi:
            return v
    except (TypeError, ValueError):
        pass
    bad.append(key)
    return default


def admission_thresholds(pol: Optional[dict] = None) -> dict:
    """R375 메모리 압박: 공통 admission 임계값 정본 (sandbox-policy.json · 환경 변수 우선 · 값 검증).
    예전에는 memory_gate(90%)·broker(80/90)·회귀 게이트(80/75/90) 가 숫자를 각자 들고 있었다."""
    pol = _policy() if pol is None else pol
    bad: list = []

    def g(env, key, d, lo, hi):
        return _num(os.environ.get(env, pol.get(key, d)), d, lo, hi, bad, key)

    t = {"constrained_pct": g("ORCA_MEM_CONSTRAINED_PERCENT", "mem_constrained_percent", 80, 1, 100),
         "block_pct": g("ORCA_MAX_COMMIT_PERCENT", "max_commit_percent", 90, 1, 100),
         "resume_pct": g("ORCA_MEM_RESUME_PERCENT", "mem_resume_percent", 75, 0, 100),
         "min_free_gb": g("ORCA_MIN_COMMIT_FREE_GB", "min_commit_free_gb", 2, 0, 1024),
         "min_phys_free_gb": g("ORCA_MIN_PHYS_FREE_GB", "min_phys_free_gb", 1, 0, 1024),
         "task_est_gb": g("ORCA_TASK_EST_GB", "agent_est_gb", 1.0, 0, 64),
         "margin": g("ORCA_ESTIMATE_MARGIN", "estimate_margin", 1.2, 1, 10),
         "max_parallel": int(g("ORCA_AGENT_MAX_PARALLEL", "agent_max_parallel", 3, 1, 64)),
         "constrained_parallel": int(g("ORCA_MEM_CONSTRAINED_PARALLEL", "mem_constrained_parallel", 1, 1, 64)),
         "state_ttl_sec": g("ORCA_MEM_STATE_TTL_SEC", "mem_state_ttl_sec", 3600, 1, 86400)}
    t["block_pct"] = max(t["block_pct"], t["constrained_pct"])        # 상한 < 진입선 = 설정 실수 → 진입선으로
    t["resume_pct"] = min(t["resume_pct"], t["constrained_pct"])      # 재개선 > 진입선 = 진동 → 진입선으로
    t["gap"] = t["constrained_pct"] - t["resume_pct"]
    t["invalid"] = bad[:10]                                            # 진단은 상한 있게
    return t


def _measure_problems(cm: dict) -> list:
    """R375 2차 검토: measured·percent 만 보면 free/phys 누락·NaN·inf 가 정상으로 통과했다.
    판정에 쓰는 필드 전부 유한·범위 검사 · 측정 시각(ts)이 있으면 신선도(60초)도 · 문제 목록 (빈 목록 = 정상)."""
    import math
    if not isinstance(cm, dict) or not cm.get("measured"):
        return ["measured"]
    out = []
    for k, lo, hi in (("percent", 0, 100), ("free_gb", -1e6, 1e6), ("phys_free_gb", 0, 1e6)):
        try:
            v = float(cm.get(k))
            if not (math.isfinite(v) and lo <= v <= hi):
                out.append(k)
        except (TypeError, ValueError):
            out.append(k)
    if cm.get("ts") is not None:
        try:
            ts = float(cm["ts"])
            if not math.isfinite(ts):
                out.append("ts")                          # NaN 은 abs 비교를 통과했다 (R375 3차 검토)
            elif abs(time.time() - ts) > 60:
                out.append("stale")
        except (TypeError, ValueError):
            out.append("ts")
    return out


def memory_admission(cm: Optional[dict] = None, pol: Optional[dict] = None, prior: Optional[str] = None,
                     est_gb: Optional[float] = None) -> dict:
    """공통 자원 admission — 실제 commit·물리 여유와 작업당 예상 비용(est_gb · 없으면 정책 agent_est_gb)으로
    단계와 «지금 새로 시작해도 되는 작업 수»(max_parallel)를 정한다 (순수 함수).
    normal = 정책 동시 실행 · constrained = 선택 작업 미룸·동시 실행 축소 · blocked = 새 작업 시작 X (0)
    · unknown = 측정 불가: 필수 작업은 막지 않되(memory_gate 통과) 선택 작업은 constrained 처럼 제한 (최대 병렬 복귀 X).
    max_parallel 은 여유 예산으로도 깎인다: (여유 − 최소) ÷ (작업당 비용 × 여유율) — 여러 작업이 같은 여유를 중복 소비하지 않게.
    히스테리시스(prior = 직전 단계): constrained 는 resume_pct 아래 · blocked 는 block_pct-gap 아래로 내려가야 풀린다."""
    pol = _policy() if pol is None else pol
    t = admission_thresholds(pol)
    cm = commit_memory() if cm is None else (cm or {})
    per = t["task_est_gb"] if est_gb is None else _num(est_gb, t["task_est_gb"], 0, 64, t["invalid"], "est_gb")
    bad = _measure_problems(cm)
    if bad and "stale" not in bad:   # 부분 측정이어도 유효한 필드만으로 blocked 가 확정되면 blocked (unknown 이 더 느슨해지지 않게)
        import math

        def ok(k):
            try:
                return k not in bad and math.isfinite(float(cm.get(k)))
            except (TypeError, ValueError):
                return False
        need0 = per * t["margin"]
        hits = [f"commit {cm['percent']}%" for _ in [0] if ok("percent") and float(cm["percent"]) > t["block_pct"]]
        hits += ["commit 여유 부족" for _ in [0] if ok("free_gb") and float(cm["free_gb"]) - need0 < t["min_free_gb"]]
        hits += ["물리 RAM 여유 부족" for _ in [0]
                 if ok("phys_free_gb") and float(cm["phys_free_gb"]) - need0 < t["min_phys_free_gb"]]
        if hits:
            return {"level": "blocked", "max_parallel": 0, "defer_optional": True, "commit": cm, "measure_invalid": bad,
                    "reason": f"가상 메모리(commit) {cm.get('used_gb')}/{cm.get('limit_gb')}GB · 여유 {cm.get('free_gb')}GB"
                              f" · 측정 불완전({', '.join(bad)})이지만 {' · '.join(hits)} → blocked · 새로 시작 가능 0",
                    "thresholds": t}
    if bad:
        return {"level": "unknown", "max_parallel": min(t["max_parallel"], t["constrained_parallel"]),
                "defer_optional": True, "commit": cm, "measure_invalid": bad,
                "reason": f"측정 불완전({', '.join(bad)}) — 필수 작업은 계속 · 선택 작업 제한", "thresholds": t}
    pct, free, phys = float(cm["percent"]), float(cm["free_gb"]), float(cm["phys_free_gb"])
    need = per * t["margin"]
    low_commit = free - need < t["min_free_gb"]
    low_phys = phys - need < t["min_phys_free_gb"]
    if low_commit or low_phys or pct > t["block_pct"]:
        level = "blocked"
    else:
        level = "constrained" if pct >= t["constrained_pct"] else "normal"
    held = ""
    if prior == "blocked" and level != "blocked" and pct > t["block_pct"] - t["gap"]:
        level, held = "blocked", f"회복 대기 ({t['block_pct'] - t['gap']:.0f}% 아래에서 해제)"
    elif prior in ("constrained", "blocked") and level == "normal" and pct >= t["resume_pct"]:
        level, held = "constrained", f"회복 대기 ({t['resume_pct']:.0f}% 아래에서 해제)"
    par = {"normal": t["max_parallel"], "constrained": min(t["max_parallel"], t["constrained_parallel"]),
           "blocked": 0}[level]
    if par and need > 0:
        par = max(0, min(par, int(min((free - t["min_free_gb"]) / need, (phys - t["min_phys_free_gb"]) / need))))
    why = ("commit 여유 부족" if low_commit else "") or ("물리 RAM 여유 부족" if low_phys else "")
    reason = (f"가상 메모리(commit) {cm.get('used_gb')}/{cm.get('limit_gb')}GB ({pct}%) · 여유 {free}GB · 물리 여유 {phys}GB"
              f" · 작업당 {need:.2f}GB → {level} · 새로 시작 가능 {par}" + (f" · {why}" if why else "")
              + (f" · {held}" if held else ""))
    return {"level": level, "max_parallel": par, "defer_optional": level != "normal", "commit": cm,
            "reason": reason, "thresholds": t}


def _admission_state_path() -> Optional[Path]:
    """히스테리시스 기록 위치 — 운영/시험 경계 분리: 시험 root 면 그 안 · pytest 실행 중이면 기록 안 함
    (시험끼리·운영 state 와 직전 단계를 공유하지 않게 · 기록 시험은 ORCA_MEM_ADMISSION_STATE 로 명시)."""
    env = os.environ.get("ORCA_MEM_ADMISSION_STATE", "").strip()
    if env:
        return Path(env)
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return None
    if not IS_OPERATIONAL_ROOT:
        return STATE_FILE.with_name("_memory-admission.json")
    return OPERATIONAL_STATE_FILE.with_name("memory-admission.json")


def _read_prior(path: Path, ttl: float) -> Optional[str]:
    """직전 단계 — 없음·손상·미래 시각(시계 오류)·TTL 지남·모르는 값 = None."""
    try:
        st = json.loads(path.read_text(encoding="utf-8"))
        ts, lvl = float(st.get("ts", 0)), st.get("level")
    except Exception:  # noqa: BLE001
        return None
    now = time.time()
    if not (now - ttl <= ts <= now + 60) or lvl not in ("normal", "constrained", "blocked"):
        return None
    return lvl


def admission_now(cm: Optional[dict] = None, pol: Optional[dict] = None, est_gb: Optional[float] = None) -> dict:
    """memory_admission + 직전 단계 읽기·기록 (프로세스 간 히스테리시스).
    읽기-판정-쓰기는 스레드 잠금 + OS 잠금(proc_lock.try_lock · 주인이 죽으면 커널이 해제) 안에서 한다.
    잠금을 0.5초 안에 못 잡거나 기록이 실패하면 기록 없이 판정 (판정 자체는 항상 돌려준다 · state_written 으로 구분)."""
    pol = _policy() if pol is None else pol
    path = _admission_state_path()
    t = admission_thresholds(pol)
    if not path:
        adm = memory_admission(cm, pol, None, est_gb)
        adm["prior"], adm["state_written"] = None, False
        return adm
    pl, fd = None, None
    with _ADM_THREAD_LOCK:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import proc_lock as pl
            for _ in range(10):
                fd = pl.try_lock(str(path) + ".lock")
                if fd is not None:
                    break
                time.sleep(0.05)
        except Exception:  # noqa: BLE001 — 잠금 모듈 없음 = 기록 안 함
            pl, fd = None, None
        try:
            prior = _read_prior(path, t["state_ttl_sec"])
            adm = memory_admission(cm, pol, prior, est_gb)
            adm["prior"], adm["state_written"] = prior, False
            if fd is not None and adm["level"] != "unknown":
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
                    tmp.write_text(json.dumps({"level": adm["level"], "percent": adm["commit"].get("percent"),
                                               "ts": time.time()}), encoding="utf-8")
                    os.replace(tmp, path)
                    adm["state_written"] = True
                except Exception:  # noqa: BLE001 — 기록 실패는 판정에 영향 없음
                    pass
            return adm
        finally:
            if fd is not None and pl is not None:
                pl.release(fd)


def _mem_reservation_path() -> Optional[Path]:
    """R375 2차 검토 P0: 호스트 공통 메모리 예약 장부 — 운영/시험 경계는 히스테리시스 기록과 같다."""
    env = os.environ.get("ORCA_MEM_RESERVATIONS", "").strip()
    if env:
        return Path(env)
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return None
    if not IS_OPERATIONAL_ROOT:
        return STATE_FILE.with_name("_memory-reservations.json")
    return OPERATIONAL_STATE_FILE.with_name("memory-reservations.json")


def _proc_start(pid: int) -> Optional[float]:
    """프로세스 시작 시각 (PID 재사용 구분) · 확인 불가 = None · 없는 프로세스 = -1."""
    try:
        import psutil
        return round(psutil.Process(int(pid)).create_time(), 3)
    except Exception as e:  # noqa: BLE001
        return -1.0 if type(e).__name__ == "NoSuchProcess" else None


def _holder_state(e: dict) -> str:
    """예약 소유 프로세스(주인 + 붙인 자식) 상태 — alive(하나라도 살아 있음·시작 시각 일치) · dead(전부 확인된 종료/재사용) · unknown(조회 불가)."""
    pairs = [(e.get("pid"), e.get("start"))] + [(p.get("pid"), p.get("start")) for p in (e.get("pids") or [])
                                                if isinstance(p, dict)]
    seen_unknown = False
    for pid, start in pairs:
        try:
            st = _proc_start(int(pid))
        except (TypeError, ValueError):
            continue
        if st is None:
            seen_unknown = True
        elif st != -1.0 and (start is None or abs(st - float(start)) <= 1):
            return "alive"
    return "unknown" if seen_unknown else "dead"


def _live_mem(book: dict, now: float) -> dict:
    """살아 있는 예약만 (R375 3차 검토: 살아 있는 작업의 예약을 시간만으로 회수 X).
    소유 프로세스(주인·자식) 중 하나라도 살아 있으면 TTL·시계 이동과 무관하게 유지 · 전부 종료(OOM·강제 종료 포함)·PID 재사용 = 제외 ·
    TTL 은 소유 상태를 조회할 수 없을 때만 적용 (영구 누수 방지) · 손상 항목 제외."""
    live = {}
    for rid, e in (book.get("reservations") or {}).items():
        try:
            ts, ttl, gb = float(e["ts"]), float(e["ttl"]), float(e["gb"])
        except Exception:  # noqa: BLE001
            continue
        import math
        if not (math.isfinite(ts) and math.isfinite(ttl) and 0 <= gb < 1e6):
            continue
        st = _holder_state(e)
        if st == "dead" or (st == "unknown" and not (now - ttl <= ts <= now + 60)):
            continue
        live[rid] = e
    return live


class _MemBook:
    """예약 장부 잠금 (스레드 잠금 + proc_lock OS 잠금 · 주인이 죽으면 커널이 해제).
    ok = 잠금 확보 · read() 는 파일 없음(빈 장부 · 정상)과 손상·접근 실패(corrupt=True · 장부 사용 불가)를 구분한다."""
    def __init__(self, path: Path):
        self.path, self.fd, self.pl, self.ok, self.corrupt = path, None, None, False, False

    def __enter__(self):
        _ADM_THREAD_LOCK.acquire()
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import proc_lock as pl
            self.pl = pl
            for _ in range(40):
                self.fd = pl.try_lock(str(self.path) + ".lock")
                if self.fd is not None:
                    break
                time.sleep(0.05)
        except Exception:  # noqa: BLE001
            self.fd = None
        self.ok = self.fd is not None
        return self

    def read(self) -> dict:
        try:
            raw = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        except Exception:  # noqa: BLE001 — 접근 실패 ≠ 빈 장부
            self.corrupt = True
            return {}
        try:
            d = json.loads(raw)
            if isinstance(d, dict) and isinstance(d.get("reservations", {}), dict):
                return d
        except Exception:  # noqa: BLE001
            pass
        self.corrupt = True                       # 손상 = 다른 프로세스 예약을 알 수 없음 → 선택 작업 보류 (덮어쓰지 않음)
        return {}

    def write(self, d: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def __exit__(self, *a):
        try:
            if self.fd is not None and self.pl is not None:
                self.pl.release(self.fd)
        finally:
            _ADM_THREAD_LOCK.release()


def _observed_list(book: dict, kind: str) -> list:
    obs = book.get("observed") if isinstance(book.get("observed"), dict) else {}
    lst = obs.get(kind) if isinstance(obs.get(kind), list) else []
    if kind == "default" and isinstance(book.get("observed_gb"), list):       # 이전 형식 호환
        lst = list(book["observed_gb"]) + lst
    return [float(x) for x in lst if isinstance(x, (int, float)) and 0 <= x < 64]


def _observed_est(book: dict, base: float, kind: str = "default") -> float:
    """관측 비용 기반 조정 (작업 유형별) — 해제 때 기록된 실제 peak 가 5건 이상이면 p90 과 정책값 중 큰 값 (낮추지 않음 · 안전 쪽)."""
    obs = sorted(_observed_list(book, kind))
    if len(obs) < 5:
        return base
    return max(base, obs[min(len(obs) - 1, int(len(obs) * 0.9))])


def _book_out(live: dict, book: dict) -> dict:
    out = {"reservations": live}
    obs = book.get("observed") if isinstance(book.get("observed"), dict) else {}
    if isinstance(book.get("observed_gb"), list) and book["observed_gb"]:
        obs = dict(obs, default=(list(book["observed_gb"]) + list(obs.get("default") or []))[-50:])
    out["observed"] = {k: list(v)[-50:] for k, v in obs.items() if isinstance(v, list)}
    return out


def _unconsumed(e: dict) -> float:
    """예약 중 아직 실제 RAM 으로 잡히지 않은 몫 = 예약량 − 이미 쓰는 양 (측정에 이미 들어간 만큼 이중 차감 X)."""
    try:
        return max(0.0, float(e["gb"]) - max(0.0, float(e.get("used_gb") or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def reserve_memory(n_wanted: int, owner: str, est_gb: Optional[float] = None, essential: bool = False,
                   pol: Optional[dict] = None, cm: Optional[dict] = None, kind: str = "default") -> dict:
    """판정과 예약을 한 잠금 안에서 — 다른 프로세스 예약의 미소비분을 측정 여유에서 빼고 판정한 뒤 허용 수만큼 장부에 적는다.
    반환 max_parallel = 실제로 확보한 예약 수 (len(granted)) — 호출부는 이 수만큼만 시작한다 (R375 3차 검토).
    장부 잠금 실패·읽기 손상/접근 실패·쓰기 실패 = 선택 작업 0 (예약 없는 시작 금지) · 필수 복구(essential)는
    별도 제한 예산(mem_essential_parallel · 기본 1)으로 장부 없이도 허용하되 unbooked 로 기록.
    unknown(측정 불완전)은 프로세스마다 허용량을 따로 주지 않는다 — 전역 상한(constrained_parallel)에서 다른 예약 수를 뺀다.
    시험 전용 무장부 경로(pytest 중 ORCA_MEM_RESERVATIONS 미지정)는 book='disabled_test' 로 구분."""
    pol = _policy() if pol is None else pol
    t = admission_thresholds(pol)
    path = _mem_reservation_path()
    n_wanted = max(0, int(n_wanted))
    kind = str(kind or "default")[:40]
    if not path:
        adm = admission_now(cm, pol, est_gb)
        adm.update(granted=[], reserved=False, reserved_gb_others=0.0, book="disabled_test")
        adm["max_parallel"] = min(adm["max_parallel"], n_wanted)
        return adm
    ttl = _num(os.environ.get("ORCA_MEM_RESERVATION_TTL_SEC", pol.get("mem_reservation_ttl_sec", 1800)),
               1800, 30, 86400, t["invalid"], "mem_reservation_ttl_sec")
    ess_cap = int(_num(pol.get("mem_essential_parallel", 1), 1, 0, 8, t["invalid"], "mem_essential_parallel"))
    with _MemBook(path) as mb:
        book = mb.read() if mb.ok else {}
        usable = mb.ok and not mb.corrupt
        now = time.time()
        live = _live_mem(book, now)
        base = t["task_est_gb"] if est_gb is None else _num(est_gb, t["task_est_gb"], 0, 64, t["invalid"], "est_gb")
        per = _observed_est(book, base, kind)
        mine = [e for e in live.values() if (e.get("essential") or not essential)]
        others = sum(_unconsumed(e) for e in mine)
        cm0 = commit_memory() if cm is None else dict(cm or {})
        adj = dict(cm0)
        bad = set(_measure_problems(cm0))
        for k in ("free_gb", "phys_free_gb"):           # 유효한 필드는 부분 측정이어도 각각 차감
            if k not in bad and others:
                adj[k] = round(max(0.0 if k == "phys_free_gb" else -1e6, float(cm0[k]) - others), 3)
        adm = admission_now(adj, pol, per)
        k = min(n_wanted, int(adm.get("max_parallel") or 0))
        why = ""
        if adm.get("level") == "unknown":
            k = min(k, max(0, min(t["max_parallel"], t["constrained_parallel"]) - len(mine)))
        if not usable:
            why = "예약 장부 " + ("잠금 실패" if not mb.ok else "손상·접근 실패")
            k = min(k, ess_cap) if essential else 0
        granted = []
        if k:
            start = _proc_start(os.getpid())
            import uuid
            for _ in range(k):
                rid = f"{os.getpid()}-{uuid.uuid4().hex}"
                granted.append(rid)
                live[rid] = {"owner": str(owner)[:80], "kind": kind, "pid": os.getpid(),
                             "start": start if start and start > 0 else None, "pids": [],
                             "gb": round(per * t["margin"], 3), "used_gb": 0.0, "ts": now, "ttl": ttl,
                             "essential": bool(essential)}
            if usable:
                try:
                    mb.write(_book_out(live, book))
                except Exception:  # noqa: BLE001 — 기록 실패 = 확보 실패
                    why = "예약 장부 쓰기 실패"
                    if not essential:
                        granted = []
                    else:
                        granted = granted[:ess_cap]
            if not usable or why:
                granted = [f"unbooked-{g}" for g in granted]      # 필수 복구 제한 예산 (장부 밖)
        adm.update(granted=granted, reserved=bool(granted) and not why, reserved_gb_others=round(others, 3),
                   est_gb_used=per, book="active" if usable and not why else "failed", book_problem=why or None)
        adm["max_parallel"] = len(granted)
        if why and not granted:
            adm["reason"] = f"{adm.get('reason', '')} · {why} → 선택 작업 보류 (예약 없이 시작 X)"
        return adm


def _edit_book(fn) -> bool:
    path = _mem_reservation_path()
    if not path:
        return False
    with _MemBook(path) as mb:
        if not mb.ok:
            return False
        book = mb.read()
        if mb.corrupt:
            return False                                  # 손상 장부는 덮어쓰지 않음 (진단 보존)
        live = _live_mem(book, time.time())
        fn(live, book)
        try:
            mb.write(_book_out(live, book))
            return True
        except Exception:  # noqa: BLE001
            return False


def update_reservations(ids, pids=None, used_gb: Optional[float] = None) -> bool:
    """작업 중 갱신 — 자식 프로세스(PID·시작 시각)를 붙여 부모가 죽어도 자식이 살아 있는 동안 예약 유지 ·
    used_gb = 지금 실제로 쓰는 양 (그만큼은 다른 판정에서 이중 차감하지 않음)."""
    import math
    ids = [i for i in ([ids] if isinstance(ids, str) else list(ids or [])) if not str(i).startswith("unbooked-")]
    if not ids:
        return False
    add = []
    for p in pids or []:
        st = _proc_start(p)
        if st and st > 0:
            add.append({"pid": int(p), "start": st})

    def fn(live, book):
        for rid in ids:
            e = live.get(rid)
            if not e:
                continue
            known = {(x.get("pid"), x.get("start")) for x in e.get("pids") or [] if isinstance(x, dict)}
            e["pids"] = (list(e.get("pids") or []) + [x for x in add if (x["pid"], x["start"]) not in known])[-64:]
            try:
                if used_gb is not None and math.isfinite(float(used_gb)) and float(used_gb) >= 0:
                    e["used_gb"] = round(float(used_gb), 3)
            except (TypeError, ValueError):
                pass
    return _edit_book(fn)


def release_memory(ids, observed_gb: Optional[float] = None, kind: Optional[str] = None) -> bool:
    """예약 해제 (시작 실패·정상 종료·예외 모두 호출) · observed_gb = 실제 peak (작업 유형별 최근 50건 · 비정상 값 무시)."""
    import math
    ids = [ids] if isinstance(ids, str) else list(ids or [])
    booked = [i for i in ids if not str(i).startswith("unbooked-")]
    if not booked:
        return bool(ids)

    def fn(live, book):
        k = kind
        for rid in booked:
            e = live.pop(rid, None)
            if e and not k:
                k = e.get("kind")
        try:
            if observed_gb is not None and math.isfinite(float(observed_gb)) and 0 <= float(observed_gb) < 64:
                obs = book.setdefault("observed", {}) if isinstance(book.get("observed"), dict) else book.setdefault("observed", {})
                obs.setdefault(k or "default", []).append(round(float(observed_gb), 3))
        except (TypeError, ValueError):
            pass
    return _edit_book(fn)


def memory_gate(pol: Optional[dict] = None, cm: Optional[dict] = None, est_gb: Optional[float] = None) -> Optional[dict]:
    """신규 Agent·worktree 시작 전 메모리 확인. blocked = retryable 거부 dict · 그 밖 = None.
    측정 불가(unknown)는 필수 작업을 막지 않는다 (막으면 측정 불가 환경에서 영구 정지) — 호출부가 결과를 기록한다.
    판정 정본 = admission_now (히스테리시스 · commit·물리 여유 · 작업 비용 · 임계값 = sandbox-policy.json)."""
    adm = admission_now(cm, pol, est_gb)
    if adm["level"] == "blocked":
        cm = adm["commit"]
        t = adm["thresholds"]
        return {"ok": False, "retryable": True, "deferred": True, "commit": cm, "admission": adm["level"],
                "reason": f"가상 메모리(commit) 부족: {cm.get('used_gb')}/{cm.get('limit_gb')}GB ({cm.get('percent')}%) · "
                          f"여유 {cm.get('free_gb')}GB · 최소 {t['min_free_gb']}GB·상한 {t['block_pct']}% 기준 · 시작 보류 · "
                          + adm["reason"].split(" → ", 1)[-1]}
    return None


def _estimate_bytes(base_ref: str, sparse_exclude: list) -> int:
    """base_ref 의 tracked 파일 크기 합 (sparse 제외 경로 빼고) = checkout 예상 크기."""
    out = _git("ls-tree", "-r", "-l", base_ref, timeout=60).stdout
    total = 0
    excl = tuple(x.strip("/") + "/" for x in sparse_exclude)
    for line in out.splitlines():
        try:
            meta, path = line.split("	", 1)
            size = meta.split()[3]
        except (ValueError, IndexError):
            continue
        if size.isdigit() and not path.startswith(excl):
            total += int(size)
    return total


# 예약은 디스크 단위 → 운영·테스트 root 공통 파일 1개
RESERVATION_FILE = OPERATIONAL_STATE_FILE.with_name("repair-sandbox-reservations.json")


class _reservation_lock:
    """프로세스 간 예약 파일 잠금 (O_EXCL lock file · 120초 지난 잠금은 죽은 것으로 간주)."""
    def __enter__(self):
        self.path = Path(str(RESERVATION_FILE) + ".lock")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + 60
        while True:
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode()); os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 120:
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                if time.time() > deadline:
                    raise TimeoutError("sandbox reservation lock timeout")
                time.sleep(0.2)

    def __exit__(self, *a):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def _live_reservations() -> dict:
    """예약 중 죽은 프로세스·1시간 지난 예약은 제외."""
    try:
        res = json.loads(RESERVATION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    live = {}
    for k, v in res.items():
        alive = True
        try:
            import psutil
            alive = psutil.pid_exists(int(v.get("pid", 0)))
        except Exception:
            pass
        if alive and time.time() - int(v.get("ts", 0)) < 3600:
            live[k] = v
    return live


def _save_reservations(res: dict) -> None:
    RESERVATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESERVATION_FILE.write_text(json.dumps(res), encoding="utf-8")


def create(goal_id: str, base_ref: str = "HEAD") -> dict:
    """격리 sandbox 생성: git worktree add .repair-sandbox/<goal_id> (base_ref 기준 · 기본 HEAD)."""
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    sandbox_path = SANDBOX_ROOT / str(goal_id)
    branch = f"repair/{goal_id}"

    if sandbox_path.exists():
        return {"ok": False, "reason": f"sandbox 이미 존재: {sandbox_path}", "path": str(sandbox_path)}

    # 2026-10-30 자원 정책 (sandbox-policy.json): sparse checkout 으로 대용량 자산 제외 ·
    # 예상 크기 + 다른 프로세스 예약분 + 활성 sandbox 총량을 보고 부족하면 생성 거부 (retryable · 대기).
    pol = _policy()
    mg = memory_gate(pol)
    if mg:
        return mg
    sparse = list(pol.get("sparse_exclude") or [])
    est = int(_estimate_bytes(base_ref, sparse) * float(pol.get("estimate_margin", 1.2)))
    with _reservation_lock():
        res = _live_reservations()
        reserved = sum(r["bytes"] for r in res.values())
        free = shutil.disk_usage(str(SANDBOX_ROOT)).free
        min_free = float(os.environ.get("REPAIR_SANDBOX_MIN_FREE_GB", pol.get("min_free_gb", 10))) * 1024 ** 3
        active = sum(int(e.get("est_bytes") or 0) for e in _load_state().values()
                     if e.get("status") == "active" and Path(e.get("path", "")).exists())
        cap = float(os.environ.get("REPAIR_SANDBOX_MAX_TOTAL_GB", pol.get("max_total_active_gb", 20))) * 1024 ** 3
        gb = lambda b: round(b / 1024 ** 3, 2)
        if free - reserved - est < min_free:
            return {"ok": False, "retryable": True, "free_gb": gb(free), "reserved_gb": gb(reserved),
                    "estimate_gb": gb(est), "reason": f"디스크 부족: 여유 {gb(free)}GB - 예약 {gb(reserved)}GB "
                                                      f"- 예상 {gb(est)}GB < 최소 {gb(min_free)}GB · 생성 대기"}
        if active + reserved + est > cap:
            return {"ok": False, "retryable": True, "active_gb": gb(active), "reserved_gb": gb(reserved),
                    "estimate_gb": gb(est), "reason": f"활성 sandbox 총량 상한 {gb(cap)}GB 초과 · 생성 대기"}
        res[str(goal_id)] = {"bytes": est, "pid": os.getpid(), "ts": int(time.time())}
        _save_reservations(res)
    try:
        # core.longpaths: 테스트 root(TEMP) 는 경로가 길어 kit 의 259자 파일이 MAX_PATH 초과 → 이 명령에만 적용
        if sparse:
            r = _git("-c", "core.longpaths=true", "worktree", "add", "--no-checkout", "-b", branch,
                     str(sandbox_path), base_ref, timeout=600)
            if r.returncode == 0:
                _git("sparse-checkout", "set", "--no-cone", "/*", *[f"!/{x.strip('/')}/" for x in sparse],
                     cwd=sandbox_path, timeout=60)
                r = _git("-c", "core.longpaths=true", "checkout", cwd=sandbox_path, timeout=600)
        else:
            r = _git("-c", "core.longpaths=true", "worktree", "add", "-b", branch, str(sandbox_path),
                     base_ref, timeout=600)
    finally:
        with _reservation_lock():
            res = _live_reservations()
            res.pop(str(goal_id), None)
            _save_reservations(res)

    # 2026-10-26 fallback v2: 외부 AI 지적 수용 — .git 존재만 X · git 등록 상태까지 검증
    worktree_exists = False
    if sandbox_path.exists() and (sandbox_path / ".git").exists():
        # git worktree list --porcelain 로 공식 등록 확인
        wl = _git("worktree", "list", "--porcelain", timeout=30)
        if wl.returncode == 0 and str(sandbox_path).replace("\\", "/") in wl.stdout.replace("\\", "/"):
            # rev-parse 로 실제 작업 가능한 worktree 인지 확인
            rp = _git("rev-parse", "--is-inside-work-tree", cwd=sandbox_path, timeout=30)
            if rp.returncode == 0 and "true" in rp.stdout.strip():
                worktree_exists = True
    if r.returncode != 0 and not worktree_exists:
        return {"ok": False, "reason": f"worktree add 실패: {r.stderr.strip()[:200]}", "stderr": r.stderr}

    state = _load_state()
    state[str(goal_id)] = {
        "path": str(sandbox_path),
        "branch": branch,
        "created_at": int(time.time()),
        "status": "active",
        "subprocess_rc": r.returncode,  # 디버깅 참조
        "est_bytes": est,
        "sparse_exclude": sparse,
    }
    _save_state(state)
    note = "" if r.returncode == 0 else " (subprocess timeout · worktree 실제 생성 확인됨)"
    return {"ok": True, "path": str(sandbox_path), "branch": branch, "goal_id": goal_id, "note": note}


def test(goal_id: str, test_cmd: str = "") -> dict:
    """격리 환경에서 테스트 실행. test_cmd 없으면 project default 자동 감지."""
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}
    sandbox_path = Path(entry["path"])
    if not sandbox_path.exists():
        return {"ok": False, "reason": f"sandbox path 없음: {sandbox_path}"}

    # test_cmd 자동 감지
    if not test_cmd:
        if (sandbox_path / "package.json").exists():
            test_cmd = "npm test --silent"
        elif (sandbox_path / "pyproject.toml").exists() or (sandbox_path / "pytest.ini").exists():
            test_cmd = "pytest -q"
        elif (sandbox_path / "Cargo.toml").exists():
            test_cmd = "cargo test --quiet"
        else:
            test_cmd = "echo 'no test runner detected · 안전상 PASS 처리 X'; exit 1"

    env = os.environ.copy()
    env["ALLOW_VISIBLE_WINDOW"] = "1"
    try:
        r = subprocess.run(
            test_cmd, shell=True, cwd=str(sandbox_path), env=env,
            capture_output=True, text=True, timeout=600  # 10분 상한
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "test timeout (>600s)", "test_cmd": test_cmd}

    entry["last_test"] = {
        "cmd": test_cmd,
        "exit_code": r.returncode,
        "ts": int(time.time()),
        "stdout_tail": r.stdout[-500:] if r.stdout else "",
        "stderr_tail": r.stderr[-500:] if r.stderr else "",
    }
    state[str(goal_id)] = entry
    _save_state(state)

    return {
        "ok": r.returncode == 0,
        "exit_code": r.returncode,
        "test_cmd": test_cmd,
        "stdout_tail": r.stdout[-500:] if r.stdout else "",
        "stderr_tail": r.stderr[-500:] if r.stderr else "",
    }


def commit_changes(goal_id: str, message: str) -> dict:
    """sandbox 작업 트리 변경을 repair branch 에 commit (apply 전 단계).
    worktree 수정은 commit 전엔 branch 에 없으므로 merge 해도 반영되지 않는다."""
    entry = _load_state().get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}
    cwd = Path(entry["path"])
    st = _git("status", "--porcelain", cwd=cwd, timeout=60)
    if not st.stdout.strip():
        return {"ok": True, "committed": False, "reason": "변경 없음"}
    _git("add", "-A", cwd=cwd, timeout=60)
    r = _git("commit", "-m", message, cwd=cwd, timeout=60)
    if r.returncode != 0:
        return {"ok": False, "reason": f"commit 실패: {r.stderr.strip()[:200]}"}
    sha = _git("rev-parse", "HEAD", cwd=cwd, timeout=30).stdout.strip()
    return {"ok": True, "committed": True, "commit": sha}


def _branch_checked_out(branch: str) -> bool:
    wl = _git("worktree", "list", "--porcelain", timeout=30)
    return f"branch refs/heads/{branch}" in wl.stdout


def apply_merge(goal_id: str, target_branch: str = "main") -> dict:
    """테스트 PASS 한 변경만 target_branch 에 fast-forward merge.

    target_branch="main" (기본) 은 기존 동작 그대로.
    그 외 target 은 checkout 없이 ff 여부 확인 후 update-ref 로만 이동 (작업 트리 무변경).
    """
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}

    last_test = entry.get("last_test") or {}
    if last_test.get("exit_code") != 0:
        return {"ok": False, "reason": "테스트 미통과 — apply 불가 (먼저 test PASS 필요)"}

    branch = entry["branch"]
    if target_branch != "main":
        if _branch_checked_out(target_branch):
            return {"ok": False, "reason": f"{target_branch} 가 worktree 에 checkout 됨 · update-ref 불가"}
        new_sha = _git("rev-parse", branch).stdout.strip()
        old = _git("rev-parse", "--verify", "-q", f"refs/heads/{target_branch}")
        old_sha = old.stdout.strip() if old.returncode == 0 else ""
        if old_sha:
            anc = _git("merge-base", "--is-ancestor", old_sha, new_sha)
            if anc.returncode != 0:
                return {"ok": False, "reason": f"fast-forward 불가 ({target_branch} 가 {branch} 의 조상 아님) · 원본 보호"}
        r = _git("update-ref", f"refs/heads/{target_branch}", new_sha, old_sha)
        if r.returncode != 0:
            return {"ok": False, "reason": f"update-ref 실패: {r.stderr.strip()[:200]}"}
        entry["status"] = "applied"
        entry["applied_at"] = int(time.time())
        entry["applied_to"] = target_branch
        state[str(goal_id)] = entry
        _save_state(state)
        return {"ok": True, "branch": branch, "merged_to": target_branch,
                "from_sha": old_sha, "to_sha": new_sha}
    # 현재 branch 저장
    cur = _git("branch", "--show-current")
    original_branch = cur.stdout.strip()
    try:
        # main checkout + merge --ff-only
        _git("checkout", "main")
        r = _git("merge", "--ff-only", branch)
        if r.returncode != 0:
            # fallback: 일반 merge (충돌 발생 가능)
            r = _git("merge", "--no-ff", "-m", f"fix(repair): sandbox {goal_id} merge", branch)
            if r.returncode != 0:
                return {"ok": False, "reason": f"merge 실패: {r.stderr.strip()[:200]}"}
        entry["status"] = "applied"
        entry["applied_at"] = int(time.time())
        state[str(goal_id)] = entry
        _save_state(state)
        return {"ok": True, "branch": branch, "merged_to": "main"}
    finally:
        if original_branch and original_branch != "main":
            _git("checkout", original_branch, check=False)


def preserve(goal_id: str, keep: bool = True) -> dict:
    """보존 표시 — cleanup_orphans·discard 가 건드리지 않는다 (force 제외)."""
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}
    entry["preserve"] = bool(keep)
    state[str(goal_id)] = entry
    _save_state(state)
    return {"ok": True, "goal_id": goal_id, "preserve": bool(keep)}


def discard(goal_id: str, force: bool = False) -> dict:
    """sandbox 폐기 — worktree remove + branch 삭제. 원본 보호."""
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}
    if entry.get("preserve") and not force:
        return {"ok": False, "reason": f"preserve 표시된 sandbox · discard 거부: {goal_id}"}
    sandbox_path = Path(entry["path"])
    if not _inside_root(sandbox_path):
        return {"ok": False, "reason": f"현재 root({SANDBOX_ROOT}) 밖 경로 · discard 거부: {sandbox_path}"}
    branch = entry["branch"]

    # worktree 제거
    if sandbox_path.exists():
        r = _git("worktree", "remove", "--force", str(sandbox_path))
        if r.returncode != 0:
            # fallback: 수동 디렉토리 삭제
            try:
                shutil.rmtree(sandbox_path, ignore_errors=True)
            except Exception:
                pass
    # branch 삭제
    _git("branch", "-D", branch, check=False)

    entry["status"] = "discarded"
    entry["discarded_at"] = int(time.time())
    state[str(goal_id)] = entry
    _save_state(state)
    return {"ok": True, "goal_id": goal_id, "status": "discarded"}


def list_sandboxes() -> list:
    state = _load_state()
    result = []
    for gid, entry in state.items():
        result.append({
            "goal_id": gid,
            "status": entry.get("status"),
            "path": entry.get("path"),
            "branch": entry.get("branch"),
            "last_test_exit": (entry.get("last_test") or {}).get("exit_code"),
            "lifecycle": lifecycle(entry),
            "created_at": datetime.fromtimestamp(entry.get("created_at", 0)).isoformat(timespec='seconds'),
        })
    return result


TERMINAL_OK = ("applied",)
TERMINAL_FAIL = ("discarded", "failed")


def _settled_at(entry: dict, now: int) -> int:
    return int(entry.get("applied_at") or entry.get("failed_at") or entry.get("discarded_at")
               or entry.get("created_at") or now)


def lifecycle(entry: dict, retention_sec: int = 86400, now: Optional[int] = None) -> str:
    """ACTIVE / VERIFIED / FAILED / RETAINED / CLEANUP_ELIGIBLE / REMOVED."""
    now = now or int(time.time())
    st = entry.get("status") or ""
    if st.endswith("_checkout_removed"):
        return "REMOVED"
    if entry.get("preserve"):
        return "RETAINED"
    if st in TERMINAL_OK or st in TERMINAL_FAIL:
        if now - _settled_at(entry, now) > retention_sec:
            return "CLEANUP_ELIGIBLE"
        return "VERIFIED" if st in TERMINAL_OK else "FAILED"
    return "ACTIVE"


def mark(goal_id: str, status: str) -> dict:
    """외부 흐름(self-healing 실패 등)이 sandbox 결과 상태를 기록 → 보존 기간 후 정리 대상."""
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": "sandbox 없음"}
    entry["status"] = status
    entry[f"{status}_at"] = int(time.time())
    state[str(goal_id)] = entry
    _save_state(state)
    return {"ok": True}


def cleanup_orphans(max_age_sec: int = 86400) -> dict:
    """고아 sandbox 정리 (2026-10-29 Phase 2-B 완결).
    - state 에 등록됐지만 worktree 디렉토리 없음 → 상태만 삭제
    - state 에 없지만 .repair-sandbox/ 안 디렉토리 있음 → worktree remove 시도
    - active 상태로 N 시간+ 방치 → discard 호출 (안전 default)
    """
    state = _load_state()
    removed_entries = []
    removed_dirs = []
    stale_discarded = []
    now = int(time.time())

    # 1. state 안 등록돼 있지만 디렉토리 없음 → state 삭제
    stale_active = []
    for gid, entry in list(state.items()):
        path = Path(entry.get("path", ""))
        if str(entry.get("status", "")).endswith("_checkout_removed"):
            continue                      # checkout 만 제거된 기록은 branch 추적용으로 유지
        if path and not path.exists():
            del state[gid]
            removed_entries.append({"goal_id": gid, "reason": "path_missing"})
            continue
        if not _inside_root(path):
            continue
        # 2. 생애주기 기준 정리 (2026-10-30 사용자 지시 "나이 기준만으로 운영 Sandbox 삭제 X")
        #    ACTIVE·RETAINED 는 절대 제거 X (오래된 ACTIVE 는 보고만) · CLEANUP_ELIGIBLE 만 checkout 제거 · branch 유지
        stage = lifecycle(entry, max_age_sec, now)
        if stage == "ACTIVE" and now - int(entry.get("created_at", now)) > max_age_sec:
            stale_active.append({"goal_id": gid, "age_sec": now - int(entry.get("created_at", now))})
        elif stage == "CLEANUP_ELIGIBLE":
            r = _git("worktree", "remove", "--force", str(path), timeout=120)
            if r.returncode == 0:
                entry["status"] = f"{entry.get('status')}_checkout_removed"
                entry["checkout_removed_at"] = now
                stale_discarded.append({"goal_id": gid, "checkout_removed": True,
                                        "age_sec": now - _settled_at(entry, now)})

    _save_state(state)

    # 3. root 안 디렉토리인데 state 에 없음 → 운영 root 는 보고만 (출처 불명 자산 보호) · 테스트 root 는 제거
    orphan_report = []
    if SANDBOX_ROOT.exists():
        state_paths = {str(Path(e.get("path", "")).resolve()) for e in state.values()
                       if e.get("path")}
        for child in SANDBOX_ROOT.iterdir():
            if not child.is_dir() or str(child.resolve()) in state_paths:
                continue
            if IS_OPERATIONAL_ROOT:
                orphan_report.append(str(child))
                continue
            r = _git("worktree", "remove", "--force", str(child), timeout=30)
            if r.returncode != 0:
                shutil.rmtree(child, ignore_errors=True)
            removed_dirs.append({"path": str(child), "worktree_remove_rc": r.returncode})

    # 4. git worktree prune (끊어진 참조 정리)
    _git("worktree", "prune", timeout=30, check=False)

    return {
        "ok": True,
        "removed_state_entries": removed_entries,
        "removed_orphan_dirs": removed_dirs,
        "cleanup_eligible_removed": stale_discarded,
        "stale_active_retained": stale_active,
        "orphan_dirs_reported": orphan_report,
    }


def main(argv):
    if len(argv) < 2:
        print("usage: repair_sandbox.py {create|test|apply|discard|list} [goal_id] [test_cmd]")
        return 2
    cmd = argv[1]
    if cmd == "list":
        print(json.dumps(list_sandboxes(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "cleanup-orphans":
        max_age = 86400
        for i, a in enumerate(argv):
            if a == "--max-age-sec" and i + 1 < len(argv):
                try:
                    max_age = int(argv[i + 1])
                except Exception:
                    pass
        r = cleanup_orphans(max_age_sec=max_age)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    if len(argv) < 3:
        print(f"usage: repair_sandbox.py {cmd} <goal_id> [...]")
        return 2
    goal_id = argv[2]
    if cmd == "create":
        print(json.dumps(create(goal_id), ensure_ascii=False, indent=2))
    elif cmd == "test":
        test_cmd = argv[3] if len(argv) > 3 else ""
        r = test(goal_id, test_cmd)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    elif cmd == "apply":
        r = apply_merge(goal_id)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    elif cmd == "discard":
        r = discard(goal_id, force="--force" in argv)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif cmd == "preserve":
        r = preserve(goal_id, keep="--off" not in argv)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"unknown cmd: {cmd}")
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[repair_sandbox] fatal: {e}", file=sys.stderr)
        sys.exit(1)
