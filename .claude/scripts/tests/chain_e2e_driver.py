"""V1.1 C 무료 종단 시험 (test_phase20 이 subprocess 로 실행 · 모듈 ROOT 가 import 시점에 정해져 같은 프로세스에선 격리 불가) — 실제 agent_repair_chain 을 임시 git 저장소에서 실행.
유료 Agent 호출(dispatch_agent)만 가짜로 바꾸고 sandbox·runner·pytest·회귀·Judge 결합·반영은 실제 코드.
운영 DB·운영 sandbox 를 건드리지 않도록 ROOT·sandbox root 를 모두 임시 폴더로 지정한다.
usage: python chain_e2e_driver.py <kit_root> <work_dir>"""
import json
import os
import subprocess
import sys
from pathlib import Path

KIT = Path(sys.argv[1]).resolve()
WORK = Path(sys.argv[2]).resolve()
T = WORK / "repo"
os.environ["CLAUDE_PROJECT_DIR"] = str(T)
os.environ["ORCHESTRATION_ROOT"] = str(T)
os.environ["REPAIR_SANDBOX_ROOT"] = str(WORK / "sandboxes")
os.environ["REPAIR_SANDBOX_MIN_FREE_GB"] = "1"


def git(*a, cwd=T):
    return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True, encoding="utf-8")


BUG = "def weight_fee(kg):\n    return kg * 2  # rate\n"
LABEL = "def label_fee(kg):\n    return kg * 2  # rate\n"
TEST = ("from demo.shipping import weight_fee\n\n"
        "def test_weight_fee():\n    assert weight_fee(10) == 30\n")
REGRESS = ("from demo.shipping import weight_fee\n\n"
           "def test_zero_and_scale():\n    assert weight_fee(0) == 0\n    assert weight_fee(2) == 6\n")


def build_repo():
    (T / "demo").mkdir(parents=True)
    (T / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (T / "demo" / "shipping.py").write_text(BUG, encoding="utf-8")
    (T / "demo" / "label.py").write_text(LABEL, encoding="utf-8")          # 같은 버그를 가진 복사본
    (T / "demo" / "test_shipping.py").write_text(TEST, encoding="utf-8")
    (T / "demo" / "test_regress.py").write_text(REGRESS, encoding="utf-8")
    (T / ".claude" / "config").mkdir(parents=True)
    (T / ".claude" / "config" / "sandbox-policy.json").write_bytes(
        (KIT / ".claude" / "config" / "sandbox-policy.json").read_bytes())
    (T / ".gitignore").write_text(".claude/state/\n__pycache__/\n.pytest_cache/\n",encoding="utf-8")
    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@t"); git("config", "user.name", "t")
    git("add", "-A"); git("commit", "-qm", "init")
    git("branch", "apply-target")


build_repo()
_init = subprocess.run([sys.executable, str(KIT / ".claude" / "scripts" / "init-state-db.py")],
                       capture_output=True, text=True, env=os.environ)
assert _init.returncode == 0, _init.stdout + _init.stderr
sys.path.insert(0, str(KIT / ".claude" / "scripts" / "lib"))
import supervisor as sup        # noqa: E402
import repair_sandbox as sb     # noqa: E402
import real_repair_chain as rc  # noqa: E402
import independent_verifier as iv  # noqa: E402

assert Path(sup.DB).resolve().is_relative_to(T), sup.DB          # 운영 DB 아님
assert not sb.IS_OPERATIONAL_ROOT and sb.SANDBOX_ROOT.resolve().is_relative_to(WORK)
# conftest 와 같은 이유로 실행 PC 의 가상 메모리에 결과가 좌우되지 않게 고정
sb.commit_memory = lambda: {"measured": True, "used_gb": 8.0, "limit_gb": 32.0, "free_gb": 24.0, "percent": 25.0}
iv.JUDGE_QUEUE = T / ".claude" / "state" / "judge-queue"
iv.JUDGE_QUEUE.mkdir(parents=True, exist_ok=True)
iv.EXTERNAL_EVIDENCE = T / ".claude" / "state" / "external-evidence.jsonl"

calls = []


def make_agent(fix_body):
    def fake_dispatch(prompt, cwd, model, tools, role="fix", **kw):
        calls.append({"role": role, "prompt": prompt})
        if role == "fix":
            (Path(cwd) / "demo" / "shipping.py").write_text(fix_body, encoding="utf-8")
            return {"ok": True, "role": role, "model": model, "result": '{"edit_file":"demo/shipping.py"}'}
        verdict = {"satisfies_requirement": True, "missing_requirements": [], "unexpected_side_effects": [],
                   "scope_adequacy": "ok", "confidence": 9, "recommendation": "VERIFIED", "reasoning": "fake"}
        return {"ok": True, "role": role, "model": model, "result": json.dumps(verdict)}   # 세션·비용 없음 = mock
    return fake_dispatch


def run(name, fix_body):
    calls.clear()
    gid = sup.create_goal(f"C e2e {name}")
    sbx = sb.create(str(gid))
    assert sbx.get("ok"), sbx
    rc.dispatch_agent = make_agent(fix_body)
    out = rc.agent_repair_chain(gid, str(gid), "python -m pytest -q demo/test_shipping.py",
                                allow_paths=["demo/shipping.py"], protected_paths=["demo/test_shipping.py",
                                                                                  "demo/test_regress.py"],
                                apply_target="apply-target", max_fix_rounds=1)
    judge_prompts = [c["prompt"] for c in calls if c["role"] == "judge"]
    hf = iv.JUDGE_QUEUE / f"goal-{gid}.json"
    handoff = json.loads(hf.read_text(encoding="utf-8")) if hf.exists() else {}
    return {"name": name, "goal": gid, "ok": out.get("ok"), "failed_stage": out.get("failed_stage"),
            "stages": [s["stage"] for s in out["stages"]],
            "regression": out.get("regression"), "policy": out.get("policy"),
            "judge_called": bool(judge_prompts),
            "judge_prompt_shows_label_copy": any("label.py" in p for p in judge_prompts),
            "judge_prompt_shows_regression": any("demo/test_regress.py exit 0" in p for p in judge_prompts),
            "judge_prompt_external_missing": any("requests: no official-source record" in p for p in judge_prompts),
            "judge_prompt_external_record": any(EV_URL in p and EV_QUOTE in p for p in judge_prompts),
            "final": (handoff.get("final_verdict") or {}),
            "apply_target_file": git("show", "apply-target:demo/shipping.py").stdout}


EV_URL = "https://requests.readthedocs.io/en/latest/"
EV_QUOTE = "Requests is an elegant and simple HTTP library for Python"
EXT_BODY = "import requests  # noqa\n\ndef weight_fee(kg):\n    return kg * 3  # rate\n"
results = [
    run("hardcoded-fix", "def weight_fee(kg):\n    return 30 if kg == 10 else kg * 2  # rate\n"),
    run("external-dep", EXT_BODY),
    run("root-cause-fix", "def weight_fee(kg):\n    return kg * 3  # rate\n"),
]
# 공식 자료 기록 후 같은 외부 의존 변경 (근본 수정이 대상 브랜치에 먼저 반영돼 이 건의 apply 는 판정 대상 아님)
iv.record_external_evidence("requests", EV_URL, "2.32", "read", EV_QUOTE)
results.append(run("external-dep-recorded", EXT_BODY))
results.append({"main_source_unchanged": git("status", "--porcelain", "demo").stdout == "",
                "main_branch_file": git("show", "main:demo/shipping.py").stdout})
print(json.dumps(results, ensure_ascii=False, indent=1, default=str))
