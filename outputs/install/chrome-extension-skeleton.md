# Chrome Extension 스켈레톤 — claude.ai Web ↔ CLI 진짜 자동 브릿지

> **미래 과제 · 지금 seed**
> **용도**: 사용자 클립보드 릴레이 없이 web ↔ CLI 자동 왕복
> **API 비용 X** — 사용자 계정 claude.ai 구독만 활용

---

## 문제

- Anthropic 이 claude.ai Web 자동 조작 API 공개 X (Playwright 는 ToS 위반 소지)
- Managed Agents API = 비용 발생
- 지금 = 사용자 수동 copy/paste 릴레이

## 해결책: Chrome Extension

브라우저 확장 프로그램으로 사용자 로그인된 claude.ai 세션 자동 조작.
- **API 비용 X** (사용자 개인 계정 사용)
- **개인 브라우저 내부 자동화** (Anthropic ToS 문제 소지 없음)
- **CLI 파일 브릿지 (`~/.claude/orca/`)** 와 자동 동기화

---

## 아키텍처

```text
┌─────────────────────────────────────┐
│  Chrome Extension                    │
│  ┌──────────────────────────────┐   │
│  │  content-script.js            │   │
│  │  - claude.ai DOM 감지          │   │
│  │  - 첫 프롬프트 자동 seed        │   │
│  │  - 응답 추출                    │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  background.js                │   │
│  │  - Native Messaging (chrome)  │   │
│  │  - CLI 파일 브릿지 동기화       │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  popup.html                    │   │
│  │  - 상태 표시                    │   │
│  │  - 세션·큐 관리                 │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
              │
              │ Native Messaging Host
              ▼
┌─────────────────────────────────────┐
│  CLI (orchestration_v1)              │
│  ~/.claude/orca/ 큐 폴링·저장         │
│  ─ task-<slug>.md (요청)              │
│  ─ result-<slug>.md (응답)            │
└─────────────────────────────────────┘
```

---

## 파일 구조 (개발 시)

```text
orchestration-bridge-extension/
├── manifest.json          # Chrome Extension v3 manifest
├── content-script.js       # claude.ai DOM 조작
├── background.js           # Native Messaging + 큐 sync
├── popup.html              # 상태 UI
├── popup.js
├── icons/
│   ├── icon-16.png
│   ├── icon-48.png
│   └── icon-128.png
├── native-host/
│   ├── manifest.json       # Native Messaging Host manifest
│   └── host.py             # Python 로컬 데몬 (~/.claude/orca/ 폴링)
└── README.md
```

---

## manifest.json (Chrome Extension v3)

```json
{
  "manifest_version": 3,
  "name": "Orchestration Kit Bridge",
  "version": "0.1.0",
  "description": "claude.ai Web ↔ orchestration_v1 CLI 자동 브릿지",
  "permissions": [
    "activeTab",
    "storage",
    "nativeMessaging",
    "clipboardWrite",
    "clipboardRead"
  ],
  "host_permissions": [
    "https://claude.ai/*"
  ],
  "content_scripts": [{
    "matches": ["https://claude.ai/*"],
    "js": ["content-script.js"],
    "run_at": "document_idle"
  }],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon-16.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png"
    }
  }
}
```

---

## content-script.js (claude.ai DOM 조작)

```javascript
// claude.ai 대화 UI 감지 및 자동 seed
(function() {
  const SESSION_BOOTSTRAP = /* outputs/install/session-bootstrap-prompt.md 내용 */;

  // 새 대화 감지 (프롬프트 입력창 비어있고 첫 접속)
  function detectNewChat() {
    const input = document.querySelector('div[contenteditable="true"]');
    if (input && !input.textContent && !sessionStorage.getItem('seeded')) {
      seedPrompt(input);
      sessionStorage.setItem('seeded', 'true');
    }
  }

  // 첫 프롬프트 자동 삽입
  function seedPrompt(input) {
    input.textContent = SESSION_BOOTSTRAP;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    // 사용자에게 확인 요청 (Send 는 수동)
    console.log('[Orchestration Bridge] Bootstrap 프롬프트 삽입 완료');
  }

  // 응답 추출 → CLI 파일 브릿지 전송
  function watchResponses() {
    const observer = new MutationObserver(() => {
      const lastResponse = document.querySelector('.claude-response:last-child');
      if (lastResponse && !lastResponse.dataset.sent) {
        sendToBackground({
          type: 'response',
          content: lastResponse.textContent,
          timestamp: Date.now()
        });
        lastResponse.dataset.sent = 'true';
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function sendToBackground(msg) {
    chrome.runtime.sendMessage(msg);
  }

  detectNewChat();
  watchResponses();
})();
```

---

## background.js (Native Messaging)

```javascript
let nativePort = null;

function connectNativeHost() {
  nativePort = chrome.runtime.connectNative('com.orchestration_v1.bridge');
  nativePort.onMessage.addListener((msg) => {
    // CLI 로부터 새 task 도착 → claude.ai 에 입력
    if (msg.type === 'task') {
      chrome.tabs.query({ url: 'https://claude.ai/*' }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, { type: 'insert-prompt', content: msg.content });
        }
      });
    }
  });
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'response') {
    // claude.ai 응답 → CLI 파일 브릿지로 저장
    if (!nativePort) connectNativeHost();
    nativePort.postMessage({ type: 'result', content: msg.content, timestamp: msg.timestamp });
  }
});
```

---

## native-host/host.py (CLI 로컬 데몬)

```python
"""Native Messaging Host — Chrome ↔ CLI 파일 브릿지 sync."""
import json
import sys
import struct
from pathlib import Path

ORCA = Path.home() / ".claude" / "orca"
ORCA.mkdir(parents=True, exist_ok=True)
QUEUE = ORCA / "queue"
RESULTS = ORCA / "results"
QUEUE.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

def read_message():
    length_bytes = sys.stdin.buffer.read(4)
    if not length_bytes:
        return None
    length = struct.unpack("i", length_bytes)[0]
    return json.loads(sys.stdin.buffer.read(length).decode())

def send_message(msg):
    encoded = json.dumps(msg).encode()
    sys.stdout.buffer.write(struct.pack("i", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()

def main():
    # Chrome 로부터 응답 수신 → CLI 결과 저장
    # 동시에 CLI queue 폴링 → Chrome 으로 새 task 전송
    while True:
        msg = read_message()
        if msg is None:
            break
        if msg["type"] == "result":
            ts = msg["timestamp"]
            (RESULTS / f"{ts}-a.md").write_text(msg["content"], encoding="utf-8")

        # CLI queue 폴링
        for task_file in QUEUE.glob("*.md"):
            content = task_file.read_text(encoding="utf-8")
            send_message({"type": "task", "content": content})
            task_file.rename(RESULTS / task_file.name.replace(".md", "-q.md"))

if __name__ == "__main__":
    main()
```

---

## 개발 로드맵

| Phase | 작업 | 시간 |
|---|---|---|
| 1 | manifest.json + content-script (자동 seed 만) | 1일 |
| 2 | background + Native Messaging 기본 | 2일 |
| 3 | Native Host Python 데몬 | 1일 |
| 4 | 응답 추출·큐 sync | 2일 |
| 5 | popup UI (세션·큐 상태) | 1일 |
| 6 | 테스트·에러 처리 | 2일 |

**총 ~9일** 개인 개발. 완성 후 Chrome Web Store 심사 (개인용은 unpacked 로드로 skip 가능).

---

## 지금 즉시 활용 가능한 대안

Chrome Extension 완성 전:
1. **Claude.ai Projects** — System instructions 로 자동 seed (매 대화 복붙 X)
2. **Bookmarklet** — 북마크 클릭 = 프롬프트 자동 삽입 (Send 는 수동)
3. **파일 브릿지 + Termius** — 아이폰·모바일 SSH 로 CLI 큐 파일 관리

---

## 관련

- `outputs/install/web-cli-bridge.md` (4 방식 상세)
- `outputs/install/session-bootstrap-prompt.md` (Extension 에 embed 할 프롬프트)
- `outputs/install/claude-web-projects-setup.md` (Projects 세팅)
- `outputs/install/kit-catalog.md § 12.5` (API 비용 매트릭스)
- `.claude/scripts/web-cli-auto-bridge.py` (Managed Agents API 대안 · 유료)

---

**우선순위 결정**: 지금은 Claude.ai Projects + 파일 브릿지로 충분. Chrome Extension 은 사용자 명시 요청 시 개발 착수.
