---
description: "Anthropic 공식 security-guidance plugin 설치 안내"
allowed-tools: Bash, Read
---

# /sec_guidance-install

> **목적**: Anthropic 공식 marketplace 에서 security-guidance plugin 설치.

## 사용법

Claude Code 세션 안에서:

```text
/plugin install security-guidance@claude-plugins-official
```

## 설치 후 확인

```text
/plugin list
```

`security-guidance` 항목이 표시되면 활성. Write/Edit/MultiEdit 호출 시 자동 가드.

## 비용

**무료**. 모델 호출 0회 (정적 패턴 매치만).

## 우리 워크플로우

설치만으로 즉시 활성. 별도 설정 X.

추가 깊은 감사는 `/sec-scan` (semgrep + gitleaks + bandit) 권장.

## 참조

- `../README.md` — 25 패턴 카테고리
- `../skills/skill-sec-guidance.md` — 통합 가이드
