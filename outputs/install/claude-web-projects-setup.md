# Claude.ai Projects — 복붙 안 하는 자동 seed 방법

> **문제**: 매 대화마다 `session-bootstrap-prompt.md` 복사·붙여넣기 = 사용자 노동.
> **해결**: **Claude.ai Projects** — 한 번 세팅, 이후 모든 대화 자동 seed.

---

## 1분 세팅 (한 번만)

1. **https://claude.ai** 로그인
2. 왼쪽 사이드바 **Projects** → **+ Create Project**
3. Project 이름: `orchestration_v1 kit` (또는 원하는 이름)
4. **System instructions** (또는 "Custom instructions") 필드에:
   - `outputs/install/session-bootstrap-prompt.md` 전체 내용 붙임
   - 또는 "붙여넣기 프롬프트" 섹션만 (```text 안 내용)
5. **Save**

## 이후 사용

- Projects 사이드바에서 `orchestration_v1 kit` 클릭
- 새 대화 시작 → **첫 응답부터 헌장 A~F 자동 준수**
- 지시만 하면 됨 (프롬프트 복붙 X)

## 여러 컴퓨터·모바일 자동 동기화

- Claude.ai Projects 는 **Anthropic 계정** 기준 저장
- **아이폰·안드로이드 claude.ai 앱** 열면 같은 Project 로그인 시 자동 로드
- **PC/노트북 브라우저** 도 마찬가지
- Project instructions 는 클라우드 저장 → 어느 기기든 자동

## 여러 Project (분리 관리)

| Project 이름 | System instructions | 용도 |
|---|---|---|
| `orchestration_v1 kit` | session-bootstrap-prompt.md | 이 kit 원칙 준수 |
| `RMS 실운영` | + RMS 도메인 지식 | RMS 프로젝트 |
| `ITCEN ESG` | + ESG 요구사항 | 회사 업무 |

각 Project 는 독립 대화 히스토리 · 파일 · instructions.

## 업데이트

kit 원칙 변경 시:
1. `outputs/install/session-bootstrap-prompt.md` 수정
2. Claude.ai Projects → 해당 Project → Settings → System instructions 교체
3. 다음 대화부터 자동 반영

## Bookmarklet (대체 방법)

Projects 못 쓸 때 (예: Claude Free tier 는 Projects 제한 있음):

```javascript
javascript:(function(){
  const prompt = `[여기에 session-bootstrap-prompt.md 내용 붙임]`;
  const el = document.querySelector('div[contenteditable="true"]');
  if (el) { el.textContent = prompt; el.dispatchEvent(new Event('input',{bubbles:true})); }
})();
```

1. 브라우저 북마크 → 새 북마크 → URL 필드에 위 JS 붙임 (프롬프트 내용은 미리 escape)
2. claude.ai 새 대화 → 북마크 클릭 → 자동 삽입
3. 사용자가 Send 클릭

## Managed Agents API (완전 자동)

프로그래밍 통합 시:

```python
from anthropic import Anthropic
client = Anthropic()

with open("outputs/install/session-bootstrap-prompt.md") as f:
    bootstrap = f.read()

response = client.messages.create(
    model="claude-opus-5",
    system=bootstrap,  # ← 여기에 프롬프트
    messages=[{"role": "user", "content": user_input}],
)
```

`system` 필드 = 매 요청 자동 seed. 복붙 X, 코드에 저장.

## 요약

**가장 빠른 방법 = Claude.ai Projects** (1분 세팅, 이후 자동)

**참조**:
- `outputs/install/session-bootstrap-prompt.md` (프롬프트 원본)
- `outputs/install/web-cli-bridge.md` (Web ↔ CLI 브릿지 4방식)
- Anthropic docs: https://support.anthropic.com/en/articles/9517075
