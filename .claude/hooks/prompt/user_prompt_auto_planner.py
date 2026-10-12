"""user-prompt-auto-planner.sh 이식 — 대상 확정 + 5단계 plan + MoE 분류 + 메모리 recall 주입.

원본은 python 5개 (프롬프트 추출·분류·키워드회상·활동로그·결정로그) 를 매번 띄웠다.
여기서는 전부 in-process. 무거운 RAG(chromadb) 만 detached 워커로 남긴다.
"""
from __future__ import annotations

import json
import os
import re
import sys

from _common import (
    HOOKS_DIR,
    bash_strip,
    load_script,
    msys_path,
    read_text,
    search,
)

TRIGGER_PATTERN = "해줘|고쳐줘|확인|점검|왜|뭐야|되니|되네|안돼|안되|작네|크네|짤려|짤린|짤림|잘림|잘리|짤리|여백|여전|넘쳐|안보|글씨|보여야|잘되|잘됨|잘하|부족|틀렸|틀린|발동|농땡이|전수조사|정신|회피|딴말|무시|또|놓쳤|fix|build|verify|check|review|test|update|add|change|왜이리|방지|보완|이미지|메모리|성능"
SUBAGENT_BIG_PATTERN = "전수조사|전체.*탐색|전체.*검색|모든.*파일|모든.*폴더|코드베이스|whole.?code|grep.*all"
SUBAGENT_REVIEW_PATTERN = "리뷰|review|코드 검토|PR 검토"
OUTPUT_TEMPLATE = (
    "{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"[대상 확정 REQUIRED — 0순위]\\n"
    "★ 첫 응답 첫 줄 형식 (매 지시 필수): 대상: <path> (kit/설정/target/글로벌) — 맞으면 진행, 아니면 정정\\n"
    "★ 4갈래 후보:\\n"
    "  1) ${PROJECT_ROOT} (kit 자체 감사-룰-hook)\\n"
    "  2) ${PROJECT_ROOT}/setup/templates/ (install 배포용 template)\\n"
    "  3) install 대상 실운영 프로젝트 (경로 물어봐 — 사용자가 '실운영'-'하드코딩 실측'-'재발 방지 헌장'-비즈니스 지표명 언급 시)\\n"
    "  4) ~/.claude/ (글로벌 설정)\\n"
    "★ 대상 확정 전 grep-Read-Edit-Bash 착수 = 룰 위반. 자동 후보 나열도 X 하고 kit 뒤지기 시작 = 재발.\\n"
    "상세: .claude/rules/direction-first.md - feedback_confirm_target_first.md\\n"
    "\\n"
    "[auto-planner ENFORCED]\\n"
    "사용자 메시지에 작업 지시-결함 지적-점검 키워드 감지. 5단계 의무 발동:\\n"
    "1) 전수조사 — 인접 시스템-전역까지 모든 위치 훑기 (단일 후보로 결론 X)\\n"
    "2) 분석 — diff/md5sum/본문으로 내용 검증 (파일명만 보고 단정 X)\\n"
    "3) 실행 — 발견한 문제를 코드로 수정\\n"
    "4) 확인 — 자동 검증 (verify-image-fit / verify-docx-pages / verify-docx-structure / verify-ppt-overflow) 발동-PASS 확인\\n"
    "5) 보고 — 표-목록으로 결과 + 남은 결정사항\\n"
    "\\n"
    "금기:\\n"
    "- 대상 확정 없이 실행 착수 (0순위 위반)\\n"
    "- 부분 처리 (한 파일만 보고 답변)\\n"
    "- 검증 X 하고 완료 보고\\n"
    "- 사용자에게 결정 떠넘기기 (크리티컬 5가지 외)\\n"
    "- 회피-딴말 (직접 답 -> 부연 -> 행동)\\n"
    "- 매번 사용자 지시 기다림 (auto-planner 자동 발동)\\n"
    "\\n"
    "자동 발동 트리거: auto-planner.md skill\\n"
    "\\n"
    "${GUIDE}${SUBAGENT_GUIDE}${MEMORY_GUIDE}${ALARM_GUIDE}${COMPACT_GUIDE}\"}}"
)

# 원본 버그 호환 — 키워드 회상 결과가 0건이면 `grep -c ... || echo 0` 이 "0\n0" 을 만들고
# log-decision.py 가 int("0\n0") 로 죽어 decisions 에 기록되지 않았다 (회상 1건+ 일 때만 기록).
# 또 log-decision.py 는 인자가 있으면 argv[1] (= "--ai") 을 메시지로 저장한다.
# 동작 그대로 보존. 고치려면 두 값을 False / 프롬프트로 바꾼다.
COMPAT_SKIP_ZERO_HIT_DECISION = True
COMPAT_DECISION_MSG = "--ai"


def _read_rag_cache(root) -> str:
    cache = root / ".claude" / "state" / "rag-last.json"
    if cache.is_file():
        return bash_strip(read_text(cache))
    return "[]"


def _spawn_rag(root, prompt: str) -> None:
    """RAG(의미 검색) 갱신 — 17초 걸리는 chromadb 로드라 동기 경로 불가 -> detached 1개 (락 있으면 skip)."""
    script = root / ".claude" / "scripts" / "rag-recall.py"
    lock = root / ".claude" / "state" / "rag-running"
    if not script.is_file() or lock.exists():
        return
    if os.environ.get("PROMPT_DISPATCH_NO_SPAWN") == "1":  # 테스트용
        return
    import subprocess

    try:
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.touch()
        env = dict(os.environ, AP_PROMPT=prompt, PYTHONIOENCODING="utf-8")
        kw = {}
        if os.name == "nt":
            kw["creationflags"] = 0x08000000 | 0x00000008  # CREATE_NO_WINDOW | DETACHED_PROCESS
        else:
            kw["start_new_session"] = True
        subprocess.Popen(
            [sys.executable, "-X", "utf8", str(HOOKS_DIR / "prompt-dispatch.py"), "--rag-worker"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            close_fds=True,
            **kw,
        )
    except Exception:
        try:
            lock.unlink()
        except OSError:
            pass


def rag_worker() -> None:
    """detached 워커 본체 — 결과를 rag-last.json 에 쓰고 락 해제 (성공 시에만 교체)."""
    from _common import ROOT

    state = ROOT / ".claude" / "state"
    cache, tmp, lock = state / "rag-last.json", state / "rag-last.json.tmp", state / "rag-running"
    try:
        prompt = os.environ.get("AP_PROMPT", "").strip()
        mod = load_script("rag-recall")
        results = mod.search(prompt, 3)
        with open(tmp, "wb") as f:
            f.write((json.dumps(results, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        os.replace(tmp, cache)
    except Exception:
        pass
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def _lines(rx: str, text: str, label: str, limit: int) -> list[str]:
    """grep -oE '"key": "..."' | sed | head -N."""
    return [f"- ({label}) {m}" for m in re.findall(rx, text)][:limit]


def run(ctx):
    # 2026-09-19: context-usage-pct.py 등 하위 프로세스가 이 세션 transcript 를 읽도록 stdin 의 transcript_path 를 환경에 둔다
    tp = ctx.payload.get("transcript_path") or ""
    if tp and isinstance(tp, str):
        os.environ["CLAUDE_TRANSCRIPT_PATH"] = tp

    p = ctx.payload.get("prompt") or ""
    if not isinstance(p, str):
        p = str(p)
    prompt = bash_strip(p[:1000])

    if not search(TRIGGER_PATTERN, prompt):
        return None

    root = ctx.root

    # MoE 자동 분류
    ai, reason = "claude", "기본"
    cls = load_script("classify-task")
    if cls is not None:
        try:
            res = cls.classify(prompt.strip())
            ai = res.get("ai") or ai
            reason = res.get("reason") or reason
        except Exception:
            pass
    ctx.mark("classify")

    # 키워드 3-tier 회상
    rec_text = "[]"
    rec = load_script("recall-memory")
    if rec is not None:
        try:
            rec_text = json.dumps(rec.recall(prompt.strip()), ensure_ascii=False, indent=2)
        except Exception:
            rec_text = ""
    ctx.mark("recall")

    # RAG — 이전 프롬프트가 만든 캐시를 읽고, 갱신은 detached 로
    rag_text = _read_rag_cache(root)
    _spawn_rag(root, prompt)

    if ai == "codex":
        guide = f"[MoE 자동] codex 위임 권장 ({reason}). 자동 dispatch: python .claude/scripts/auto-dispatch.py"
    elif ai == "gemini":
        guide = f"[MoE 자동] Gemini Flash 권장 ({reason}). gemini-auto 워커 활용"
    elif ai == "haiku":
        guide = f"[MoE 자동] Haiku 권장 ({reason}). haiku-auto 워커 활용"
    else:
        guide = f"[MoE 자동] Claude 직접 처리 ({reason})"

    subagent = ""
    if search(SUBAGENT_BIG_PATTERN, prompt):
        subagent = "\\n\\n[Subagent 자동] '큰 코드베이스 탐색' 감지 -> Task tool 로 Explore subagent 자동 호출 권장 (메인 컨텍스트 격리)"
    elif search(SUBAGENT_REVIEW_PATTERN, prompt):
        subagent = "\\n\\n[Subagent 자동] '코드 리뷰' 감지 -> Task tool 로 code-reviewer subagent 자동 호출 권장"

    # 활동 로그 (원본: background python) — orca.db.activations + hook-trace.log
    la = load_script("log-activation")
    if la is not None:
        try:
            trig = "" if prompt.startswith("--") else prompt
            la.log("hook", "user-prompt-auto-planner", trig, "success", 0)
        except Exception:
            pass
    ctx.mark("log-activation")

    # Memory 자동 recall 문구 (원본 grep/sed 파이프라인을 정규식으로)
    mem_lines = _lines(r'"description"\s*:\s*"([^"]*)"', rec_text, "kw", 3)
    rag_lines = _lines(r'"preview"\s*:\s*"([^"]*)"', rag_text, "rag", 2)
    combined = mem_lines + rag_lines
    memory_guide = ""
    if combined:
        memory_guide = (
            "\\n\\n[Memory 자동 recall — kw=키워드 / rag=의미] 관련 학습 (재발 방지):\\n"
            + "".join(ln + "\\n" for ln in combined)
        )

    # 결정 로그 (원본: background python)
    ld = load_script("log-decision")
    if ld is not None:
        mem_count = sum(1 for ln in rec_text.split("\n") if '"file"' in ln)
        if mem_count > 0 or not COMPAT_SKIP_ZERO_HIT_DECISION:
            try:
                ld.log(COMPAT_DECISION_MSG, ai, mem_count)
            except Exception:
                pass
    ctx.mark("log-decision")

    out = (
        OUTPUT_TEMPLATE.replace("${PROJECT_ROOT}", msys_path(root))
        .replace("${GUIDE}", guide)
        .replace("${SUBAGENT_GUIDE}", subagent)
        .replace("${MEMORY_GUIDE}", memory_guide)
        .replace("${ALARM_GUIDE}", "")
        .replace("${COMPACT_GUIDE}", "")
    )
    # 원본은 JSON 텍스트를 직접 조립해 stdout 으로 냈다 — 같은 방식으로 해석 (깨지면 평문 취급)
    try:
        return json.loads(out)["hookSpecificOutput"]["additionalContext"]
    except Exception:
        return out
