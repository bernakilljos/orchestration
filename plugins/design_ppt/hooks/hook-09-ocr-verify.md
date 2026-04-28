# HOOK-09 — OCR Overflow Verify (PPT 자동 잘림 검증)

> **목적**: PPT 렌더 명령 실행 후 자동으로 잘림(overflow) 의심 영역 탐지 + Claude 가 후속 OCR 할 슬라이드를 알려줌.
> **출처**: 2026-04-27 자동화 PPT 작업에서 slide-06 terminal 잘림을 사후 발견한 사례 → 자동 사전 탐지로 전환.

---

## Trigger

**Event**: `PostToolUse`
**Matcher**: `Bash`
**Pattern**: `generate-*-ppt.py` 또는 `generate-final-ppt.py` 명령 포함 시

---

## Behavior

1. PPT 렌더링이 끝난 직후 자동 실행
2. `python .claude/scripts/verify-ppt-overflow.py` 호출
3. 모든 `outputs/ppt*/html-source/png-output/` 분석
4. 잘림 의심 슬라이드 발견 시:
   - `outputs/ppt*/overflow-report.md` 자동 생성
   - exit code 2 + system message 로 Claude 에게 알림
   - Claude 는 의심 슬라이드를 `Read` tool 로 직접 OCR 검증
5. 의심 0건이면 silent (성공)

---

## settings.json 등록 (사용자 1회 작업)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/hook-09-ocr-verify.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

또는 더 정밀한 패턴 매칭은 hook 스크립트 내부에서 처리.

---

## 동작 흐름

```
[1] 사용자: /design_ppt "주제" 12
    ↓
[2] Claude: generate-*-ppt.py 실행
    ↓
[3] PostToolUse hook 자동 발화 → verify-ppt-overflow.py
    ↓
[4-A] Clean: silent → Claude 가 정상 보고
[4-B] Suspect: stderr 출력 + Claude 가 Read 로 의심 슬라이드 OCR
    ↓
[5] Claude: 잘림 발견시 HTML 수정 → 재렌더
```

---

## 검증 원리 (verify-ppt-overflow.py)

- 각 PNG 의 **하단 30px** + **우측 30px** 가장자리 픽셀 분석
- RGB < 80 (다크) 인 픽셀 비율 측정
- 임계치 (default 10%) 초과 시 `[!] suspect` 마킹
- 의도된 디자인 (검은 terminal 박스) 도 false-positive 가능 → **Claude OCR 이 최종 판정**

---

## False-Positive 처리

검은 terminal 박스가 하단에 있는 슬라이드는 자주 의심으로 잡힘.
이런 경우:
1. Claude 가 Read 로 OCR
2. 의도된 디자인이면 무시 (의심이지만 실제 잘림 아님)
3. 실제 잘림이면 HTML 수정

---

## Pass Criteria

- [ ] 렌더 후 5초 내 검증 완료
- [ ] suspect 발견 시 `outputs/<dir>/overflow-report.md` 생성
- [ ] exit code 2 로 Claude 에게 신호
- [ ] Claude 가 의심 슬라이드 자동 OCR 검증

## On Failure

- Pillow 미설치 → `pip install Pillow` 안내
- 스크립트 자체 에러 → stderr 출력 후 silent (PPT 렌더 자체는 막지 않음)

---

## 참조

- 검증 스크립트: `.claude/scripts/verify-ppt-overflow.py`
- 함정 체크리스트: `skills/skill-ppt-pitfalls.md`
- 메인 워크플로우: `commands/design_ppt.md`
