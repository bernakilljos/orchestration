# exec_scheduler — 크론 잡·워크플로우 스케줄러 (모든 정기 작업의 기반)

> **Status**: spec-only (Phase 1) | **Prefix**: `exec_` | **버전**: 0.1

## ⚠️ 현재 상태

이 플러그인은 **스펙만** 있고 실구현은 없습니다. `install 후 플랫폼`에서 구현.
상세 스펙: [`SPEC.md`](SPEC.md)

## 📋 커맨드 (예정)

- `/cron` — 크론 잡 등록 (YAML 선언형)
- `/workflow` — DAG 워크플로우 정의
- `/run-now` — 즉시 실행
- `/status` — 실행 중 + 다음 예약
- `/history` — 실행 이력·성공률
- `/retry-policy` — 재시도 정책 (exponential backoff)

## 🔗 의존성

- **플러그인**: exec_orch

## 📝 로드맵

- `docs/2026-04-19/로드맵.md` § Phase 1
