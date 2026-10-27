---
description: Adaptive Orchestration 학습 효과 상세 보고 — 재사용·원인·개선 검증·분류·검색 적중률
allowed-tools: Bash(python:*)
---

Adaptive Orchestration 학습 효과를 종합 보고합니다 (Phase 1-3).

측정 축:
- A. 학습 저장 (대화·세션·solution·decision·recurrence·improvements)
- B. 재사용 효과 (Top 재사용 solution + hit_count)
- C. 원인 분석 (recurrence_events.root_cause 저장률)
- D. 개선 검증 (recurrence_improvements · pre/post · VERIFIED)
- E. 재발률 추세 (디자인·개발)
- F. Experience 분류 (TASK/EXPERIENCE/CORRECTION/FAILURE)
- 검색 적중률 (lookup-rule.log 신 포맷)

실행:
```bash
python .claude/scripts/learning-report.py
```

- `python .claude/scripts/learning-report.py json` — JSON
- `python .claude/scripts/learning-report.py short` — 한 줄 (statusline 용)

결과: `docs/LEARNING_REPORT_YYYY-MM-DD.md`
