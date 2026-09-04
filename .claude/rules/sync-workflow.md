# Sync 워크플로우 규칙

> **핵심 원칙**: `plugins/` 가 Source of Truth. `.claude/` 는 sync 결과물.

## 편집 규칙

| 대상 | 편집 가능 | 비고 |
|------|:---------:|------|
| `plugins/<name>/` |  | 모든 편집은 여기서 |
| `.claude/commands/` |  | 자동 생성 — 편집 시 sync 로 덮어씀 |
| `.claude/skills/` |  | 자동 생성 |
| `.claude/scripts/` |  | sync 대상 아님 (인프라) |
| `.claude/settings.json` |  | 수동 설정 |
| `.claude/hooks/*.sh` |  | 수동 스크립트 |

## 편집 → 배포 플로우

```bash
# 1. plugins/ 에서 편집
vim plugins/exec_orch/commands/godmode.md

# 2. 미리보기
bash .claude/scripts/sync-plugins.sh --dry

# 3. 실제 sync
bash .claude/scripts/sync-plugins.sh

# 4. 검증
python .claude/scripts/validate-plugin-schema.py

# 5. 커밋 (plugins/ + .claude/ 둘 다)
git add plugins/ .claude/
git commit -m "..."
```

## sync-plugins.sh 옵션 (v2)

| 옵션 | 용도 |
|------|------|
| (없음) | 실제 동기화 |
| `--dry` | 미리보기, 파일 변경 없음 |
| `--check` | 드리프트·orphan 점검만 |
| `--verbose` | 상세 출력 (diff 포함) |

## 종료 코드

- `0` — 정상
- `2` — drift 또는 orphan 감지 (경고)

## 충돌 해결 (rename map)

여러 플러그인에 동일 파일명 존재 시 (`install.md`, `status.md`, `make.md`):
- `sync-plugins.sh` 의 `RENAME_MAP` 에 접두사 부여 규칙 등록
- 예: `mcp_dev/install.md` → `mcp_dev-install.md`

새 플러그인 추가 시 동명 파일 생기면 `RENAME_MAP` 에 추가 필요.

## 의존성 순서

`resolve-plugin-order.py` 가 `plugin.json.dependencies.plugins` 읽어 위상정렬.
순환 의존 감지 시 경고.

## Orphan 대응

`.claude/commands|skills/` 에 있으나 `plugins/` 원본 없는 파일:
- 경고: sync-plugins.sh 가 자동 탐지
- 해결: `plugins/<name>/commands/<name>.md` 로 이동 또는 삭제
- 예외: `skill-01 ~ skill-45` 레거시 번호 스킬은 orphan 경고 제외
