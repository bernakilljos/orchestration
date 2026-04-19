# 플러그인 구조 규칙

> **적용 범위**: `plugins/<name>/` 모든 플러그인
> **근거**: Source of Truth 원칙 + sync 일관성

## 필수 구조

```
plugins/<name>/
├── plugin.json              필수 — 스키마 v1.2 이상
├── README.md                필수 — 사용법·예시
├── commands/                선택 — /slash-command 정의
│   └── *.md
├── skills/                  선택 — 자동 활성화 스킬
│   └── *.md
├── agents/                  선택 — 전문 에이전트
│   └── agent-*.md
├── hooks/                   선택 — 훅 (md 스펙 + sh 스크립트)
│   ├── hook-*.md
│   └── *.sh
└── SPEC.md                  조건부 — status=spec-only 일 때 필수
```

## 명명 규칙

- 플러그인 이름: `<prefix>_<feature>` (소문자·언더스코어)
- prefix 는 `.claude-plugin/plugin.json` 의 `prefix_convention` 에 등록된 것만
- 커맨드 파일: `<action>.md` (kebab-case 허용, 예: `yt-upload.md`)
- 스킬 파일: `skill-<NN>-<topic>.md` 또는 `<feature>-<purpose>.md`
- 훅 파일: `hook-<NN>-<event>.md` + 동명 `.sh` 스크립트

## plugin.json 필수 필드 (v1.2)

```json
{
  "name": "...",
  "display": "...",
  "prefix": "...",
  "version": "...",
  "status": "stable|experimental|spec-only|deprecated",
  "phase": 0
}
```

세부는 [`frontmatter.md`](frontmatter.md).

## 의존성 표기

`plugin.json.dependencies.plugins` 배열에 필요한 플러그인 이름 명시.
순환 의존 금지 — `resolve-plugin-order.py` 위상정렬 실패 시 에러.

## 새 플러그인 만들 때

```bash
cp -r plugins/_template plugins/<new_name>
# plugin.json 에서 name·prefix·display 수정
bash .claude/scripts/sync-plugins.sh
python .claude/scripts/validate-plugin-schema.py <new_name>
```
