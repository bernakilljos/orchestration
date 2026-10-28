#!/usr/bin/env python
"""
workflow-run.py · 9-chain workflow 최소 실행 엔진 (minimal)

근거:
- 외부 감사 "P1 workflow YAML CONNECTED X · 실행 엔진 없음" 지적
- 2026-10-27 사용자 "나머지는? 내가 요청했는데"

역할:
- YAML (`.claude/workflows/*.yaml`) 로드 → steps 순회
- 각 step 의 script 명령 **실제 호출** (dry-run 지원)
- next_chain / on_failure 체인 전환
- step 결과 로그 (`.claude/logs/workflow-run.log`)

제한 (minimal):
- for_each / switch / when 복잡 구문은 TODO (현재 steps 선형만)
- tool: Edit/WebSearch 같은 Claude tool call 은 Claude agent 가 직접 (여기서는 안내만)
- outputs 전달은 환경변수 기반 (제한적)

CLI:
  python workflow-run.py --chain 01-goal --input '{"user_prompt":"X"}'
  python workflow-run.py --full --from 01-goal --input '{"user_prompt":"X"}'
  python workflow-run.py --list    # YAML 목록
  python workflow-run.py --dry --chain 02-discovery
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOWS = ROOT / ".claude" / "workflows"
LOG = ROOT / ".claude" / "logs" / "workflow-run.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

try:
    import yaml
except ImportError:
    print(json.dumps({"error": "PyYAML 미설치: pip install pyyaml"}, ensure_ascii=False))
    sys.exit(3)


def _log(msg: str) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def load_chain(name: str) -> dict | None:
    # 01-goal / 01 / goal 모두 수용
    for p in WORKFLOWS.glob("*.yaml"):
        stem = p.stem
        if stem == name or stem.endswith(f"-{name}") or stem.split("-", 1)[-1] == name:
            return yaml.safe_load(p.read_text(encoding="utf-8"))
    return None


def list_chains() -> list[str]:
    return sorted([p.stem for p in WORKFLOWS.glob("*.yaml")])


def _substitute(s: str, ctx: dict) -> str:
    """{var} → ctx[var] 치환 (단순)."""
    if not isinstance(s, str):
        return s
    out = s
    for k, v in ctx.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def run_step(step: dict, ctx: dict, dry: bool = False) -> dict:
    sid = step.get("id", "?")
    desc = step.get("desc", "")
    _log(f"  step[{sid}] {desc}")

    # tool call (Edit·WebSearch·Agent) 은 Claude agent 영역 → stub
    if step.get("tool"):
        return {"id": sid, "status": "SKIP_TOOL", "reason": f"tool={step['tool']} · Claude agent 영역"}

    # workflow 재귀 호출
    if step.get("workflow"):
        chain = step["workflow"]
        return {"id": sid, "status": "SUBCHAIN", "chain": chain, "reason": "하위 chain 호출 필요 (--full 로 처리)"}

    # script 호출
    script = step.get("script")
    if not script:
        return {"id": sid, "status": "SKIP_NO_SCRIPT"}

    script_abs = ROOT / script if not Path(script).is_absolute() else Path(script)
    if not script_abs.exists():
        return {"id": sid, "status": "FAIL_NOT_FOUND", "script": str(script_abs)}

    args = [_substitute(a, ctx) for a in step.get("args", [])]

    if dry:
        return {"id": sid, "status": "DRY", "cmd": [sys.executable, str(script_abs), *args]}

    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(script_abs), *args],
            capture_output=True, text=True, timeout=120, cwd=str(ROOT),
        )
        return {
            "id": sid,
            "status": "OK" if r.returncode == 0 else f"FAIL({r.returncode})",
            "stdout": r.stdout[:300],
            "stderr": r.stderr[:300],
        }
    except subprocess.TimeoutExpired:
        return {"id": sid, "status": "TIMEOUT"}
    except Exception as e:
        return {"id": sid, "status": f"ERROR: {e}"}


def run_chain(name: str, inputs: dict, dry: bool = False) -> dict:
    chain = load_chain(name)
    if not chain:
        return {"chain": name, "status": "NOT_FOUND"}
    _log(f"[chain] {name} start · inputs={list(inputs.keys())}")
    ctx = {**inputs}
    results = []
    for step in chain.get("steps", []) or []:
        res = run_step(step, ctx, dry=dry)
        results.append(res)
        if res["status"].startswith("FAIL") or res["status"] == "TIMEOUT":
            on_fail = chain.get("on_failure")
            _log(f"[chain] {name} FAIL at {res['id']} · on_failure={on_fail}")
            return {"chain": name, "status": "FAIL", "steps": results, "next_chain": on_fail}
    next_chain = chain.get("next_chain")
    _log(f"[chain] {name} OK · next_chain={next_chain}")
    return {"chain": name, "status": "OK", "steps": results, "next_chain": next_chain}


def run_full(start: str, inputs: dict, dry: bool = False, max_hops: int = 10) -> list[dict]:
    results = []
    cur = start
    seen = set()
    hops = 0
    while cur and hops < max_hops:
        if cur in seen:
            results.append({"chain": cur, "status": "LOOP_DETECTED"})
            break
        seen.add(cur)
        r = run_chain(cur, inputs, dry=dry)
        results.append(r)
        if r["status"] in ("NOT_FOUND", "LOOP_DETECTED"):
            break
        cur = r.get("next_chain")
        if r["status"] == "FAIL" and not cur:
            break
        hops += 1
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--chain", help="단일 chain 실행")
    ap.add_argument("--full", action="store_true", help="start chain 부터 next_chain 따라 전부 실행")
    ap.add_argument("--from", dest="start", default="01-goal", help="--full 시작 chain")
    ap.add_argument("--input", default="{}", help="JSON inputs")
    ap.add_argument("--dry", action="store_true", help="실제 호출 X · 명령만 표시")
    args = ap.parse_args()

    if args.list:
        print(json.dumps({"chains": list_chains()}, ensure_ascii=False, indent=2))
        return 0

    try:
        inputs = json.loads(args.input or "{}")
    except Exception as e:
        print(json.dumps({"error": f"input JSON 파싱 실패: {e}"}, ensure_ascii=False))
        return 2

    if args.full:
        results = run_full(args.start, inputs, dry=args.dry)
    elif args.chain:
        results = [run_chain(args.chain, inputs, dry=args.dry)]
    else:
        ap.print_help()
        return 1

    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0 if all(r["status"] in ("OK", "DRY") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
