# Orchestration Health — 2026-11-16

**점수**: 36/100 · **판정**: CRITICAL · **조치**: CHANGE CANDIDATE

- 충돌: 8 ⚠
- 중복: 8 ⚠
- orphan: 37 ⚠
- drift: 5 ⚠
- golden: 13/13 ✅
- request: 154/259 ⚠
- codex: 0 fail/24h ✅
- stop_gate: 2/2 ✅
- 전파: 0/3 ⚠
- 재발률: 90% ⚠
- standing: 16/17 ✅

## CHANGE CANDIDATE (자동 수정 X · 사용자 승인 후만)

- 충돌: {'rule': {'auto': 2, 'file': 2, 'no': 2}, 'hook': {'check': 11, 'detect': 8, 'auto': 5}}
- 중복: {'rule': {'auto': 2, 'file': 2, 'no': 2}, 'hook': {'check': 11, 'detect': 8, 'auto': 5}}
- orphan: ['10x.md', 'artifacts.md', 'brief.md', 'check-services.md', 'compare.md']
- drift: 점검 필요
- request: 승인대기 62 · 검증중 17 · 진행 1
- 전파: 점검 필요
- 재발률: 점검 필요
