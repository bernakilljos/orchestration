---
description: "사용자 명시 지시 시 발동 — outputs/·docs/·.claude/ 정리 (dry-run 기본, 명시 시 실삭제)"
allowed-tools: Bash, Read, Glob
---

# /cleanup — 폴더 정리 on-demand

자동 정리 (cleanup-pollution.sh) 외 **사용자 지시 시만** 정리 발동.

## 사용

```bash
/cleanup outputs                # outputs/ 30일+ 산출물 (ppt·doc·png) dry-run
/cleanup outputs --apply        # 실제 archive (outputs/_archive/) 또는 삭제
/cleanup docs                   # docs/YYYY-MM-DD/ 90일+ → docs/_archive/
/cleanup screens                # docs/screens/ 분석 이미지 14일+
/cleanup state                  # .claude/state/ 비활성 캐시 (orca.db 외)
/cleanup logs                   # .claude/logs/ 14일+ (자동 cleanup-pollution 보완)
/cleanup tasks                  # .claude/tasks/done/ 30일+ (자동 보완)
/cleanup plugins                # spec-only plugin 휴면 → deprecated 표시 (수동 review)
/cleanup all                    # 위 8개 dry-run 일괄
/cleanup all --apply            # 전체 일괄 실삭제
```

## 자동 트리거 (사용자 자연어)

`/cleanup` 외에 다음 발화 시 활성:
- "outputs 정리해줘", "docs 정리해줘"
- "임시 파일 정리"
- "오래된 산출물 archive"

## 처리 매트릭스 (handler: `.claude/scripts/cleanup-on-demand.sh`)

| target | 경로 | TTL | 처리 |
|---|---|---|---|
| `outputs` | `outputs/*/` | 30일+ | `outputs/_archive/YYYY-MM/` 이동 (실삭제 X 안전) |
| `docs` | `docs/YYYY-MM-DD/` | 90일+ | `docs/_archive/` 이동 (영구문서 `docs/*.md` 제외) |
| `screens` | `docs/screens/`, `docs/screens/_*` | 14일+ | 삭제 |
| `state` | `.claude/state/` (orca.db·session·workers 제외) | 30일+ | 삭제 |
| `logs` | `.claude/logs/*.log` | 14일+ | 삭제 (cleanup-pollution 보완) |
| `tasks` | `.claude/tasks/done/*` | 30일+ | 삭제 (cleanup-pollution 보완) |
| `plugins` | `plugins/<spec-only>` 마지막 commit 90일+ | — | plugin.json 에 `"deprecated": true` 추가 (수동 review) |

## 안전 장치

- **dry-run 기본** — `--apply` 명시 없으면 시뮬레이션만
- **archive 우선** — 삭제 대신 `_archive/YYYY-MM/` 이동 (outputs·docs)
- **보호 목록** — `.claude/state/orca.db`·`.env`·`.git/`·`.claude-plugin/` 절대 건드림 X
- **백업** — 실삭제 전 `tar.gz` 백업 → `.claude/backups/cleanup-<ts>.tar.gz`

## 결과 보고 표준

```text
=== cleanup outputs (dry-run) ===
스캔 대상: outputs/ppt-team/, outputs/ppt-plugins/, outputs/ppt-automation/, ...
30일+ 후보: 47 파일 (총 234 MB)
  - outputs/ppt-team/2026-03-15/ (12 파일, 89 MB)
  - outputs/ppt-plugins/2026-03-22/ (8 파일, 56 MB)
  - ...
처리: archive → outputs/_archive/2026-03/ 예정
실삭제: --apply 옵션 필요
```

## 금지

- 자동 발동 X (사용자 명시 지시 필요)
- 보호 목록 건드림 X
- `--apply` 없이 실삭제 X
- 백업 없이 archive 이동 X

## 참조

- `.claude/rules/cleanup-policy.md` (기본 정리 정책)
- `.claude/scripts/cleanup-pollution.sh` (자동·SessionStart hook)
- `.claude/scripts/cleanup-on-demand.sh` (이 command 의 handler)
- `.claude/rules/best-practices.md` § Zero-touch 자동화 (자동 정리 한계)
