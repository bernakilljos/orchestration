---
description: "kit 기능 투어 — 신규 사용자 or 안 쓴 기능 체험 가이드"
allowed-tools: Bash(ls:*), Read
---

## 사용법
```text
/walkthrough          # 전체 투어 (10 섹션)
/walkthrough emotion  # user-emotion 매핑 체험 (62+ 트리거)
/walkthrough design   # statusline 디자인·개발 지수 설명
/walkthrough resume   # 자동 복구 (resume-last-24h) 설명
/walkthrough 5중      # 5중 자동 발동 (context 기반)
```

## 투어 섹션 (전체 모드)

### 1. statusline 6줄
토큰 · 한도(세션·주간) · 디자인(이모지·여백·버전관리·산출물기한) · 개발(증명지시·미반영·전수조사skip) · 상태(MCP·재사용·cache·errors·하드코딩·fast) · 비용

### 2. user-emotion 자동 매핑 (62+)
답답→fast · 짜증→진단 · 미쳐→brainstorm · 모르겠→explainlikeim5 · 리뷰→code-reviewer · ...

### 3. 수정 → 증명 체인
"수정해" 감지 → verify-after-edit-mandatory.md 5단계 (pre→수정→post→작동→보고)

### 4. 자동 복구 (resume-last-24h)
재부팅·세션 종료 시 orca.db 최근 24h 자동 로드

### 5. 쓰레기 정리
3일+ pending·tmp·lock → cleanup-summary-YYYYMMDD.md 요약 후 삭제

### 6. 5중 자동 발동
1중 어휘 매칭 · 2중 orca.db 패턴 · 3중 지수 임계 · 4중 재사용 · 5중 외부신호

### 7. 반복 패턴 자동 학습
learn-user-patterns.py 매주 · suggest-learned-patterns.py dry-run (조심 모드)

### 8. 룰 위반 지수 (rule-adherence)
90일 window · 7일 재발률 · 디자인·개발 매트릭스

### 9. install-to / 다중 프로젝트
IFRS·RMS·ICM·calc 전수 kit 반영 · 글로벌 settings 포인터

### 10. MCP 통합
Headroom (압축 60~95%) + claude-mem (자동 세션 관측) + task-observer (skill 개선)

## Your task

사용자 입력 `$ARGUMENTS` 로 섹션 선택:
- 빈 입력 → 전체 10 섹션 요약
- 섹션 이름 → 그 섹션만 상세 (파일 경로·실행 명령·실측 결과)

각 섹션 끝에 **"지금 체험 명령"** 1줄 포함.

예: `/walkthrough emotion` →
```text
## user-emotion 자동 매핑 (62+)
...
지금 체험: 아무 프롬프트에 "답답해" 입력 → systemMessage 로 fast 모드 자동 추천
```
