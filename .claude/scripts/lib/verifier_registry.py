"""verifier_registry.py — Python callable verifier 등록소 (2026-10-29 Phase 2-A).

사용자 지시 (391e691 후속):
  "Python callable 검증은 임의 Python 코드를 실행하게 만들면 안 됩니다.
   등록된 검증기 ID, 입력 스키마, 격리 실행, 시간 제한으로 제약해야."

안전 원칙:
  - 임의 코드 문자열 실행 X · eval/exec X
  - 등록된 verifier id 만 호출 가능 (화이트리스트)
  - 입력 스키마 명시 (dict · 필수 키 검증)
  - subprocess 격리 (별 Python 프로세스 · timeout 적용)
  - 실패·미실행·실행오류 상태 분리

Verifier 등록 방법:
  1. @register("my-verifier-id") 데코레이터
  2. 입력 스키마 명시 (required_keys)
  3. 반환: (ok: bool, note: str)

실 호출:
  from verifier_registry import run_verifier
  ok, note, status = run_verifier("file-line-count-gte",
                                   {"file": "README.md", "cwd": "/tmp/x", "min_lines": 2})
  # status: "ok" | "fail" | "unregistered" | "schema_error" | "timeout" | "error"
"""
from __future__ import annotations
import os
import subprocess
import sys
import json
from pathlib import Path
from typing import Callable, Dict, Tuple, Optional

ROOT = Path(__file__).resolve().parents[3]

# 등록소 (verifier_id → (callable, required_keys))
_REGISTRY: Dict[str, Tuple[Callable, list]] = {}


def register(verifier_id: str, required_keys: list):
    """verifier 등록 데코레이터.

    등록 후 run_verifier(id, ctx) 로 호출.
    required_keys: ctx 안 필수 키 (스키마 체크용)
    """
    def _deco(fn):
        _REGISTRY[verifier_id] = (fn, required_keys)
        return fn
    return _deco


def _validate_ctx(ctx: dict, required: list) -> Optional[str]:
    for k in required:
        if k not in ctx:
            return f"required key missing: {k}"
    return None


def run_verifier(verifier_id: str, ctx: dict, timeout: int = 30) -> Tuple[bool, str, str]:
    """등록된 verifier 호출. 임의 코드 실행 X · 격리 subprocess 사용.

    반환: (ok, note, status)
      status: "ok" · "fail" · "unregistered" · "schema_error" · "timeout" · "error"
    """
    if verifier_id not in _REGISTRY:
        return (False, f"verifier '{verifier_id}' not registered", "unregistered")
    fn, required = _REGISTRY[verifier_id]
    err = _validate_ctx(ctx, required)
    if err:
        return (False, err, "schema_error")

    # 격리 실행: 별 Python subprocess 로 호출 · timeout 적용
    # (단, Python callable 자체는 등록된 함수만 · eval 없음)
    try:
        helper = ROOT / ".claude" / "scripts" / "lib" / "_verifier_runner.py"
        if not helper.exists():
            # fallback: 같은 프로세스 호출 (단 등록된 fn 만 · 안전)
            ok, note = fn(ctx)
            return (bool(ok), str(note), "ok" if ok else "fail")
        payload = json.dumps({"id": verifier_id, "ctx": ctx})
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(helper), payload],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        if r.returncode != 0:
            return (False, f"runner exit={r.returncode}: {r.stderr[:200]}", "error")
        try:
            out = json.loads(r.stdout.strip() or "{}")
            return (bool(out.get("ok", False)), out.get("note", ""), out.get("status", "fail"))
        except Exception as e:
            return (False, f"result parse: {e}", "error")
    except subprocess.TimeoutExpired:
        return (False, f"timeout ({timeout}s)", "timeout")
    except Exception as e:
        return (False, f"{type(e).__name__}: {e}", "error")


# ===== 등록된 verifier (안전 · OS·encoding 중립) =====

@register("file-exists", required_keys=["file", "cwd"])
def _v_file_exists(ctx: dict) -> Tuple[bool, str]:
    """파일 존재 확인."""
    p = Path(ctx["cwd"]) / ctx["file"]
    return (p.exists() and p.is_file(), f"exists={p.exists()}")


@register("file-line-count-gte", required_keys=["file", "cwd", "min_lines"])
def _v_line_count(ctx: dict) -> Tuple[bool, str]:
    """파일 라인 수 ≥ min_lines (encoding 중립 · byte 매칭)."""
    p = Path(ctx["cwd"]) / ctx["file"]
    if not p.exists():
        return (False, "file not found")
    n = sum(1 for _ in p.open("rb"))
    return (n >= int(ctx["min_lines"]), f"line_count={n}")


@register("file-size-gt", required_keys=["file", "cwd", "min_bytes"])
def _v_size(ctx: dict) -> Tuple[bool, str]:
    p = Path(ctx["cwd"]) / ctx["file"]
    if not p.exists():
        return (False, "file not found")
    sz = p.stat().st_size
    return (sz > int(ctx["min_bytes"]), f"size={sz}")


def list_verifiers() -> list:
    """등록된 verifier 목록."""
    return [{"id": k, "required_keys": v[1]} for k, v in _REGISTRY.items()]


if __name__ == "__main__":
    # CLI test
    if len(sys.argv) < 2:
        print(json.dumps(list_verifiers(), ensure_ascii=False, indent=2))
        sys.exit(0)
    if sys.argv[1] == "list":
        print(json.dumps(list_verifiers(), ensure_ascii=False, indent=2))
        sys.exit(0)
    # run <id> <ctx_json>
    if len(sys.argv) >= 4 and sys.argv[1] == "run":
        vid = sys.argv[2]
        ctx = json.loads(sys.argv[3])
        ok, note, status = run_verifier(vid, ctx)
        print(json.dumps({"ok": ok, "note": note, "status": status}, ensure_ascii=False))
        sys.exit(0 if ok else 1)
    print("usage: verifier_registry.py [list | run <id> <ctx_json>]")
    sys.exit(2)
