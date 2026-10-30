# 운영 안정화 검토 — 2026-10-30 (기준 f1369ff)

## 1. 디스크 부족 사고 원인·조치
- 원인: sandbox = `git worktree add` = HEAD 의 tracked 파일 전체 checkout. 별도 복사 로직 없음 (repair_sandbox·supervisor·self_healing 에 copytree 0건).
  HEAD tracked 2.45GB 중 `docs/screens` (디자인 참조 이미지) 2.44GB · 코드 수 MB.
- 조치: `.claude/config/sandbox-policy.json` 의 `sparse_exclude` 로 sparse checkout → sandbox 2.45GB → 36MB · 생성 1.5초.
  생성 전 예상 크기(ls-tree 합 × margin) + 다른 프로세스 예약분 + 활성 sandbox 총량 상한 확인 → 부족 시 retryable 거부 (self-heal 이벤트는 pending 으로 대기).
  생애주기 ACTIVE / VERIFIED / FAILED / RETAINED / CLEANUP_ELIGIBLE / REMOVED · ACTIVE·RETAINED 는 나이와 무관하게 제거 X · 운영 root 의 출처 불명 폴더는 보고만.

## 2. Pillow (후보 #2) — 보안 영향 분석 · 수정 Proposal (승인 대기 · 미적용)
| 항목 | 내용 |
|---|---|
| 설치 | 12.3.0 (Python 3.14.2 user site-packages · venv/lockfile 없음) · requirements `>=10.0.0` |
| CVE-2026-40192 (FITS GZIP decompression bomb) | 10.3.0 ~ 12.2.0 이전 영향 · 12.2.0 수정 → **현재 설치 영향 없음** |
| 12.3.0 수정 CVE (CVE-2026-54058·59197·59198·59199·59205·59203 등) | 이미 12.3.0 → **영향 없음** |
| 13.0.0 (2026-10-21) 수정 | JPEG 디코더 버퍼 오버플로·TIFF OOB read·Exif 루프 등 Critical 다수 · **12.3.0 영향 범위 공식 확인 못 함 (미확인)** |
| 영향 코드 경로 | `Image.open` 사용 스크립트 9개 · 외부 출처 JPEG (docs/screens 수집 이미지) 를 여는 classify-*·verify-* 스크립트 |
| 호환성 | `pip install --dry-run pillow==13.0.0` → 충돌 없이 해석 |
| Proposal | ① 13.0.0 GHSA 별 영향 범위 확인 ② 별도 venv 에서 9개 스크립트 회귀 ③ requirements 하한 `>=10.0.0` → 보안 수정 버전으로 상향 (다른 머신 install 이 취약 버전에 머무는 것 방지). 운영 의존성 변경이므로 승인 후 진행 |

## 3. ChromaDB (후보 #3) — 비교 결과: 구현 Proposal 없음
- 이미 kit 의 벡터 저장소 (`rag-recall.py` · auto-planner prompt hook · ai_rag plugin) · 인덱스 2.9MB.
- 격차 = 1.5.6 → 1.5.9 patch 수준 · 기능·성능 격차 근거 없음 → 정기 유지보수 대상일 뿐 구현 goal 불필요.

## 4. Anthropic SDK 호환성 (운영 SDK 변경 없음)
| 항목 | 실측 |
|---|---|
| 런타임 | 단일 Python 3.14.2 (user install) · venv·lockfile 없음 |
| 설치 / 요구 / 최신(PyPI) | 0.109.2 / `>=1.17.0` / 2.3.0 |
| 불일치 원인 | **langchain-anthropic 1.4.6 이 `anthropic<1.0.0` 요구** → 요구 버전 설치 불가 상태. langchain 사용처 = plugins/exec_graph/runtime/build_graph.py 1곳 |
| kit 호출 형태 | `Anthropic(api_key)` + `messages.create(model, max_tokens, system(str·cache_control 블록), messages)` · `RateLimitError`·`APIError` (3 파일) |
| 오프라인 stub 서버 시험 | 0.109.2 ✓ · 1.17.0 ✓ · 2.3.0 ✓ (호출·응답 파싱·예외 클래스 모두 정상) |
| 2.x 차이 | 요청 헤더 `anthropic-version: 2026-10-21` (0.x·1.x 는 `2023-06-01`) · httpx → httpx2 · opentelemetry-api 의존 추가 |
| 결론 | kit 코드 수정 불필요 · 차단 요인은 langchain-anthropic 핀 · API 버전 변경은 실 API 호출(비용·인증) 검증 필요 → 승인 후 별도 venv 에서 |

## 5. 테스트 브랜치 (삭제 안 함 · 승인 대기)
37개 중 main 에 없는 commit 보유 22 · worktree 사용 중 7 · 둘 다 아님 15 (삭제 안전 후보).
목록·기준: 세션 보고 표 참조 (`git rev-list --count main..<branch>` · `git worktree list --porcelain`).
