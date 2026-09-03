# vendor_voltagent

> **출처**: [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) (MIT License, Copyright (c) 2025 VoltAgent)
> **vendoring 사유**: 우리 kit 부족 카테고리 (data-AI, language-specialists) 보강. 154+ 중 5개 선별.
> **근거**: `docs/2026-06-16/tooling-comparison.md` §  4번.

## 선별된 5개 (2026-06-16 기준)

| 카테고리 | agent | 모델 | 우리 kit 부족 사유 |
|---|---|---|---|
| data-AI | `data-scientist` | sonnet | 통계 분석·예측 모델·EDA — `scout` 외 전문 X |
| data-AI | `llm-architect` | opus | LLM 시스템 설계·RAG·fine-tuning — `rag-*` 외 전문 X |
| data-AI | `ml-engineer` | sonnet | ML 파이프라인·serving·재학습 — 전문 X |
| language | `python-pro` | sonnet | Python 3.11+ async·type-safety — language-specialist X |
| language | `typescript-pro` | sonnet | TS 5.0+ generics·full-stack type safety — language-specialist X |

## 라이선스

```bash
MIT License

Copyright (c) 2025 VoltAgent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, ...
```

전체 LICENSE: `LICENSE` 파일 (root) 또는 [원본 저장소](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/LICENSE).

## vendoring 정책

1. **파일명 유지** — kebab-case 외부 표준 (우리 `file-naming.md` § 에이전트 룰 예외, vendor_*/ 안만 적용)
2. **frontmatter 보존** — `name`, `description`, `tools`, `model` 그대로
3. **본문 수정 X** — 우리 룰 (no `?.`, no "owner") 위반 시만 수정 + 변경 기록
4. **재배포 시 LICENSE 동봉**
5. **상위 저장소 갱신 시 git pull 후 선별 재복사 (수동, 분기마다)**

## 사용

설치 후:
```bash
# Claude Code 가 .claude/agents/ 에서 자동 detect
# description 매칭 또는 명시 호출
/agents data-scientist "이 데이터셋 EDA"
/agents llm-architect "RAG 시스템 설계"
/agents python-pro "이 함수 async + type-safe 로"
```

또는 우리 라우팅에서 자동 위임:
- 사용자 prompt 에 "데이터 분석", "예측 모델", "ML 파이프라인" → `data-scientist` / `ml-engineer`
- "LLM 시스템 설계", "RAG", "fine-tuning" → `llm-architect`
- "Python 타입 힌트", "async 리팩토링" → `python-pro`
- "TypeScript generics", "type 안전" → `typescript-pro`

## 우리 kit 와 차이

| 특징 | VoltAgent (vendored) | 우리 기존 kit |
|---|---|---|
| 명명 | kebab-case (`data-scientist.md`) | 번호형 (`agent-XX-<role>.md`) |
| 카테고리 | 10 (core/lang/infra/data-ai/...) | 32 plugins (도구·워크플로우 중심) |
| 강점 | 도메인 specialist | 통합 라우팅·hook·rule·SQLite |
| 통합 | 외부 표준 보존 | 우리 룰·MCP·라우팅 |

## 갱신 가이드

```bash
# 1. 원본 갱신 확인
cd .claude/state/voltagent-clone && git pull

# 2. 선별 재복사 (diff 검토 후)
for f in data-scientist llm-architect ml-engineer; do
  diff plugins/vendor_voltagent/agents/$f.md .claude/state/voltagent-clone/categories/05-data-ai/$f.md
done
```

## 참조

- `docs/2026-06-16/tooling-comparison.md`
- `plugins/exec_orch/references/external-subagents.md`
- `.claude/rules/file-naming.md` § vendor 예외
