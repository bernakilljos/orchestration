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

---

# 결정 반영 검증 (fdf2556 이후 · 2026-10-30 오후)

## A. Pillow 13.0.0 — 격리 검증 완료 · 운영 적용 가능 (설치는 승인 대기)
- 영향 확인: CVE-2026-112403 (JPEG draft/thumbnail 축소 시 버퍼 오버플로) — Debian tracker 가 12.3.0 을 vulnerable · 13.0.0 fixed 로 표기. CVE-2026-112398 (FPX JPEG) 영향 범위 `< 13.0.0`. kit 의 `auto-optimize-image.py:95` 가 `thumbnail()` 사용 → **현재 12.3.0 영향 있음**.
- 격리: `%LOCALAPPDATA%\Temppil13` venv (system-site-packages · Pillow 만 13.0.0) · 운영 Python 12.3.0 그대로.
- 회귀 (12.3.0 vs 13.0.0 동일 입력): PNG/JPEG/TIFF/WEBP/GIF 왕복 · JPEG thumbnail · resize·convert 픽셀 해시 **동일** · verify-image-whitespace(2) · verify-render-coverage · auto-optimize-image 출력 **동일** · rapidocr OCR ok · python-pptx/python-docx 이미지 삽입 ok.
- kit 안 RPA·OCR 직접 사용 코드 없음 (pyautogui·pytesseract·rapidocr import 0건).
- 운영 적용 시: `pip install pillow==13.0.0` + requirements 하한 상향 → 승인 후.

## B. Anthropic SDK 2.3.0 — 마이그레이션 검증 완료 · 실 API 호출 전 단계 (운영 교체 승인 대기)
- 차단 원인 해소 경로: langchain-anthropic **1.7.7** = `anthropic>=0.120.0` (상한 없음) · `langchain-core>=1.6.10` 필요 (1.4.6 은 `anthropic<1.0.0`).
- 격리 venv (`%LOCALAPPDATA%\Temp\sdk23lc`: anthropic 2.3.0 + langchain-anthropic 1.7.7 + langchain-core 1.7.3) 에서 stub 서버로 kit 실제 코드 3경로 실행:
  score_task.call_haiku ✓ · haiku-validate.py ✓ · ChatAnthropic.invoke (exec_graph 경로) ✓ — 0.109.2 와 결과 동일.
- 차이: 요청 헤더 `anthropic-version` 2023-06-01 → **2026-10-21**. 실 API 에서의 동작 (응답 필드·과금) 은 미검증 → 승인 시 1회 최소 호출로 확인.
- 부수 발견·수정: haiku-validate.py 가 usage 의 cache 필드가 null 이면 `None * float` TypeError (SDK 버전 무관 · 기존 잠재 결함) → `or 0` 처리.
- 시험 부작용: haiku-validate 가 운영 metrics 에 stub 행 2개 (id 188·189) 기록 → 해당 2행만 삭제.
- 운영 적용 시 requirements: `anthropic>=2.3.0` · `langchain-anthropic>=1.7.7` · `langchain-core>=1.6.10`.

## C. 테스트 브랜치 — 삭제 후보 23개 확정 (삭제 안 함)
- 기준: main 에 없는 commit 0 · main 에서 도달 가능 · worktree 미사용 · sandbox state/self-heal 이벤트/증거 파일 미참조 · 기존 보존 대상(P8·g376·g394·g82·99·100) 제외.
- 전체 repair*/self-heal* 65 중 보존: 미병합 commit 23 · worktree 15 · 증거 참조 17 · 기존 6.
- 백업: `.claude/state/branch-backup-20261030-1611.txt` (이름·SHA · 복구 `git branch <name> <sha>`).
- 발견·수정: 정리 후 checkout 이 없는 기록을 다음 정리가 state 에서 지워 branch 추적이 끊기던 결함 + 디스크 테스트가 실행마다 branch 1개를 남기던 누수.

## D. 다음 단계 계획 — 플랫폼 API · 관측성 · 자원 관리
| 영역 | 목표 | 측정 근거 |
|---|---|---|
| 관측성 | Scheduler tick 별 성공률·재시도·복구 시간·Agent 비용/토큰을 한 테이블로 집계 (self_heal_events · agent_dag_runs · executions 통합 조회) | N회 tick 성공률 · 장애 재발률 |
| 자원 관리 | sandbox 예약·총량 상한을 Agent 동시 실행 수·토큰 예산과 같은 정책 파일로 통합 · 부족 시 대기열 | 자원 부족 상황 복구 증거 |
| 플랫폼 API | goal 등록·이벤트 조회·승인(merge·candidate)을 CLI 하나로 노출 (기존 supervisor/self_healing/tech_discovery CLI 재사용) | 수동 SQL 없이 운영 가능 |
| 장기 안정성 | 실 Scheduler 다회 실행 (예: 24h) 로 성공률·디스크 추세 기록 | 1회 성공이 아닌 반복 성공 |
