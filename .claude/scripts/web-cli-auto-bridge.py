#!/usr/bin/env python3
"""web-cli-auto-bridge.py — Web ↔ CLI 완전 자동 양방향 브릿지

Anthropic Managed Agents API (2026-07-22+) 사용.
사용자가 web (claude.ai) 에서 대화 → API 가 감지 → CLI 로 forward → 결과 web 으로.

전제:
  - Anthropic API key (환경변수 ANTHROPIC_API_KEY 또는 .env)
  - `pip install anthropic>=0.40.0`

용도:
  - 사용자 계정 연동 없이 API 만으로 web·CLI 세션 통합
  - 매 turn 마다 orchestration_v1 헌장 A~F 자동 seed
  - 애매·위험만 사용자에게 (자율 진행)

사용법:
  export ANTHROPIC_API_KEY=sk-...
  python .claude/scripts/web-cli-auto-bridge.py --start
  # → daemon 모드 · 백그라운드에서 event stream 수신

  # 세션 생성:
  python .claude/scripts/web-cli-auto-bridge.py --new-session

  # 세션에 지시:
  python .claude/scripts/web-cli-auto-bridge.py --send "<지시>"

근거: outputs/install/web-cli-bridge.md § 방식 3
근거: 2026-08-12 사용자 요구 — "web 보내면 명령프롬프트 → cli → web 자동"
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("[ERROR] pip install anthropic>=0.40.0 필요")
    sys.exit(1)


ROOT = Path(__file__).resolve().parent.parent.parent
BOOTSTRAP_PROMPT = ROOT / "outputs/install/session-bootstrap-prompt.md"
STATE_DIR = ROOT / ".claude/state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
SESSION_FILE = STATE_DIR / "web-cli-session.json"


def load_bootstrap() -> str:
    """세션 부트스트랩 프롬프트 로드 (헌장 A~F + 대상 확정 + 감정 매핑 + 실전 원칙)."""
    if not BOOTSTRAP_PROMPT.exists():
        raise FileNotFoundError(f"부트스트랩 프롬프트 없음: {BOOTSTRAP_PROMPT}")
    return BOOTSTRAP_PROMPT.read_text(encoding="utf-8")


def create_session() -> dict:
    """새 Managed Agent session 생성 (bootstrap 자동 seed)."""
    client = Anthropic()
    bootstrap = load_bootstrap()

    # Managed Agents API (2026-07-22+): initial_events 로 seed
    agent = client.agents.create(
        name="orchestration_v1_bridge",
        model="claude-opus-5",
        system=bootstrap,  # ← 헌장 A~F + 대상 확정 등 자동 seed
    )
    session = client.agents.sessions.create(
        agent_id=agent.id,
        initial_events=[
            {"type": "user.message", "content": "orchestration_v1 헌장 A~F 준수 확인"}
        ],
    )
    state = {"agent_id": agent.id, "session_id": session.id, "thread_id": session.default_thread_id}
    SESSION_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"[NEW SESSION] agent={agent.id} session={session.id}")
    return state


def load_session() -> dict:
    if not SESSION_FILE.exists():
        return create_session()
    return json.loads(SESSION_FILE.read_text(encoding="utf-8"))


def send(prompt: str) -> None:
    """세션에 지시 전송 + 응답 stream 출력."""
    client = Anthropic()
    state = load_session()

    # user.message 이벤트 append
    client.agents.sessions.threads.append(
        session_id=state["session_id"],
        thread_id=state["thread_id"],
        events=[{"type": "user.message", "content": prompt}],
    )

    # stream 응답 수신 (실시간)
    print(f"[SEND] {prompt}\n[RESPONSE]")
    stream = client.agents.sessions.threads.stream(
        session_id=state["session_id"],
        thread_id=state["thread_id"],
    )
    for event in stream:
        etype = getattr(event, "type", "")
        if etype == "text.delta":
            print(event.delta, end="", flush=True)
        elif etype == "tool_use":
            print(f"\n[TOOL] {event.tool_name}({event.tool_input})", flush=True)
        elif etype == "tool_result":
            print(f"\n[RESULT] {event.tool_result}", flush=True)
    print()


def daemon() -> None:
    """웹훅 수신 대기 모드 (환경·메모리 lifecycle 반응)."""
    print("[DAEMON] Managed Agents webhook 수신 대기 (Ctrl+C 종료)")
    print("[SETUP] webhook URL 을 Anthropic Console 에 등록: environment.* / memory_store.*")
    # 실제 webhook receiver 구현 시 여기에 HTTP server (Flask/FastAPI)
    print("[TODO] webhook receiver 구현 (환경별 · 사용자 코드)")


def main():
    ap = argparse.ArgumentParser(description="Web ↔ CLI 자동 브릿지")
    ap.add_argument("--new-session", action="store_true", help="새 세션 생성")
    ap.add_argument("--send", type=str, help="지시 전송")
    ap.add_argument("--start", action="store_true", help="daemon 모드")
    ap.add_argument("--status", action="store_true", help="세션 상태")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY 환경변수 필요")
        sys.exit(1)

    if args.new_session:
        create_session()
    elif args.send:
        send(args.send)
    elif args.start:
        daemon()
    elif args.status:
        state = load_session()
        print(json.dumps(state, indent=2))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
