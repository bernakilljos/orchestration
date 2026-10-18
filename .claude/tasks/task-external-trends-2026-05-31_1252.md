# Task: external-trends-2026-05-31_1252

## 1) Role
You are a senior prompt engineering researcher. Apply newly-discovered techniques to this kit's skills/rules.

## 2) Context
- Project: orchestration_v1 (multi-AI orchestration kit)
- Changed sources: anthropic-docs-prompting anthropic-release-notes hn-prompt-engineering promptingguide-sitemap reddit-prompt-engineering
- Existing skill: plugins/exec_orch/skills/prompt-techniques.md (12 기법 매트릭스)
- Read first: CLAUDE.md, .claude/rules/best-practices.md, prompt-techniques.md

## 3) Files (수정 허용)
- plugins/exec_orch/skills/prompt-techniques.md (새 기법 추가)
- plugins/exec_orch/codex/task-instruction-template.md (template 보강)
- .claude/rules/best-practices.md (관련 룰 보강)

## 4) Acceptance criteria
- 새 기법이 12 기법 매트릭스에 없으면 추가 (WHAT/WHEN/HOW 한 줄씩)
- 라우팅 별 기본 적용 표에 매핑
- task-instruction-template 의 § 1~10 어디에 적용할지 명시

## 5) Reasoning (CoT)
1. 변경 raw 본문 읽고 핵심 기법·뉴스 추출
2. 12 기법 매트릭스와 비교 — 신규 / 중복 / 보강 분류
3. 신규면 추가, 보강이면 example 갱신

## 6) Negative constraints
- 추측·헛소문 추가 X (소스 URL + 발견 일자 명시 필수)
- 12 기법 → 30 기법 무한 확장 X (실제 사용 검증된 것만)
- description 1024 byte 초과 X

## 7) 변경 디테일
## anthropic-docs-prompting
- URL: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
- SHA: e3e3ca13e1c444e38ab7cf585bb336b0d1655629baf22b9b74dc9ebe8c578a86
- diff (top 50 lines):
```diff

```

## anthropic-release-notes
- URL: https://docs.anthropic.com/en/release-notes/claude-code
- SHA: eb21ff7386a47b7ebd0594dd1881fee7e554ca0ba64fa35b4c58a6638c0f24fc
- diff (top 50 lines):
```diff

```

## hn-prompt-engineering
- URL: https://hnrss.org/newest?q=prompt+engineering
- SHA: 6f693a58ae78904aad2f994689b1f8d8481a0d732bc5f780f478e173e5261859
- diff (top 50 lines):
```diff

```

## promptingguide-sitemap
- URL: https://www.promptingguide.ai/sitemap.xml
- SHA: 9f6c9ddc54b8949fc68c1d1aa7796732c3863f9746bef76451b3001200cf0e38
- diff (top 50 lines):
```diff

```

## reddit-prompt-engineering
- URL: https://www.reddit.com/r/PromptEngineering/.rss
- SHA: d115ad179ddb1de70635b8831000c2a84318c6a0d5f7be6a6587134c88992d01
- diff (top 50 lines):
```diff

```


## 8) 완료 검증
- python .claude/scripts/validate-plugin-schema.py
- bash .claude/scripts/sync-plugins.sh --check
