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

---

# 승인 실행 결과 (adde43a 이후)

## E. Pillow 13.0.0 운영 적용 — **롤백 (미적용)**
- 백업: `.claude/state/pillow-upgrade-20261030-1619/` (pip freeze · Python 3.14.2 · pillow-12.3.0 wheel).
- Pillow 만 설치 (의존성 미설치 옵션) 후 pip check: **fastembed 0.8.0 이 `pillow<13.0` 요구** → 승인 조건 "종속 패키지 호환성" 불충족 → 즉시 12.3.0 복구. 복구 후 pip check 충돌 0 · 다른 패키지 변화 0 (freeze 비교).
- 원인: 격리 검증이 fastembed 를 보지 않았음 (검증 누락). fastembed 는 kit 코드 미사용 · 다른 패키지도 의존 X · 최신 fastembed 0.9.1 은 `pillow<14.0` 허용.
- 해결 선택지 (승인 필요): ① fastembed 0.9.1 동시 업그레이드 ② 미사용 fastembed 제거 ③ 12.3.0 유지 (CVE-2026-112403 노출 유지).

## F. 테스트 브랜치 — 8개 삭제 · 15개 보존
- 삭제 (일반 안전 삭제 옵션 · 직전 SHA·미병합 0·worktree·DB/state/evidence/ledger 재검증): P12-MA-1793341087 · applied-check-1793341272 · g103-safe · g95-safe · life-verified ×4. 기록 `.claude/state/branch-cleanup-20261030.json`.
- 보존 15: Ledger·evidence 가 해당 SHA(모두 main 에 있는 commit) 를 언급 → "운영 기록 참조 없음" 조건 불충족으로 보수 보존.

## G. 관측성 (`.claude/scripts/lib/ops_metrics.py` · 읽기 전용)
- scheduler tick 완주율 · goal 상태·복구율 · self-heal 성공률·평균 시도 · Agent 별 성공률·DAG 비용 · 실행 exit0/검증·p50/p95 · 토큰·비용 · Judge 판정 분포 · 디스크·sandbox 생애주기·예약 · 복구 추적 ID.
- 측정 없음 = UNKNOWN (기존 metrics 49건 토큰 0 기록 → UNKNOWN · 크기 정보 없는 옛 sandbox → `+UNKNOWN×n`).
- Agent(headless claude) 1회마다 실제 토큰·비용·지연을 metrics 에 기록 (`claude-agent:<role>`) — 이전엔 미기록.
- 실 scheduler (10/29 16:30 ~ 10/30 16:20): tick 32 시작·32 완주 · 15분+ 공백 3회 (최대 11.5h · PC 꺼짐 추정) → **24h 연속 검증 아님**.

## H. 자원 정책 단일 계층 (`.claude/config/sandbox-policy.json`)
- 디스크 (sparse·min_free·총량 상한·예약) + `agent_max_parallel` 3 · `agent_max_budget_usd` 3.0 · `heal_max_events_per_tick` 1 — 기존 값 그대로 이관 (완화 X). dispatch_agent·run_dag·process_events 가 이 파일을 읽음.

## I. Platform API PoC (`.claude/scripts/lib/platform_api.py` · 로컬 · 서버 없음)
- register_goal (PENDING 등록만) · goal_status · evidence · approvals (위험 task·planner·discovery·self-heal merge 대기) · decide (task·proposal·candidate → 기존 승인 함수 위임) · agents · resources.
- 안전: 명령 실행 X · merge 등 운영 작업 미노출 · Agent/자동화 식별자 승인 거부 (시험: `claude-agent` 승인 거부 · `merge` 거부 · goal 등록 후 task 0).

## J. 반복 안정성 (scheduler 와 같은 명령 · 실측 시간만)
- 1차 3 사이클 (134.6초): 2/3 · 실패 1 = policy 단계 ROOT 전체 git status 비교 오탐 (Agent 는 허용 파일만 수정 — 세션 기록 확인). 수정: Agent 가 건드릴 수 있는 경로만 비교 + 이벤트 결과에 policy 결과 저장.
- 2차 3 사이클 (145.5초): **3/3** · 매 사이클 heal-tick 2개 동시 → 처리 [0,1] (중복 차단) · 1회차 디스크 부족 대기 → 재개 · 정상 goal VERIFIED · 기존 운영 sandbox 항목 불변 · 승인 대기 22→22 · P8 보존.

---

# 보안 패치 운영 적용 · SDK 실 API · 승인 오탐 (876932d 이후)

## K. Pillow 13.0.0 + fastembed 0.9.1 — **운영 적용 완료**
- dry-run: 두 패키지 외 변경 0. 격리 venv (system-site-packages): pip check 신규 충돌 0 (남은 semgrep↔opentelemetry · torchvision↔torch 는 운영에 원래 있던 것과 동일) · 이미지/OCR/pptx·docx/fastembed import · unit 41/41 · Phase 5 39/39.
- 운영: 백업 `.claude/state/pillow-fastembed-upgrade-*` (pip freeze·pip check·pillow 12.3.0·fastembed 0.8.0 wheel) → 두 패키지만 설치 → pip check 변경 전과 동일 · 다른 패키지 변화 0 → 재검증 unit 41/41 · P5 39/39 · P3 26/26 · P2 20/20 · 실 Task Scheduler 1회 정상. 롤백 불필요.

## L. Anthropic SDK 2.3.0 실 API 1회 — **BLOCKED (유효 키 없음)**
- 사용 가능 자격 증명: 환경 변수 ANTHROPIC_API_KEY 1개 (10자 · 실제 키 아님) · .env 없음. 인증 변경 금지 → 새 키 발급 X.
- 1회 호출 (격리 venv · 재시도 0 · max_tokens 5 · "ping" · 프로젝트 데이터 0): HTTP 401 authentication_error "invalid x-api-key" · request_id req_011CgY3oUm5muqHrt2zFrtkk · 전송 헤더 anthropic-version 2026-10-21 · 비용 $0.
- 서버는 새 버전 헤더에 버전 오류가 아닌 인증 단계 응답 → 정상 응답·과금 검증은 유효 키 제공 후. 운영 SDK 0.109.2 유지.

## M. 승인 오탐
- appr-7195ea9e0833: 실행 0건 확인 후 approval-gate reject (사용자 결정).
- 원인: 감지가 명령 문자열 전체를 보아 '언급' 도 차단 · hook 입력은 JSON 이라 줄바꿈이 문자로 들어와 기존 heredoc 판별도 동작하지 않았음 (실측).
- 수정 (approval_gate_detect._strip_inert_text): cat 이 파일로만 쓰는 heredoc 본문 · 검색 명령의 따옴표 검색어만 제외 · 셸/python 실행 heredoc · 파이프 · 같은 줄 다른 명령은 그대로 검사. 회귀 test_approval_gate_mentions.py (실제 hook 입력 JSON 경로) + 실 hook 경로 재확인 (문서 heredoc 통과).
- 이 세션이 추가로 만든 승인 대기 (실행 0 · 사용자 reject 필요): appr-4cb62e15545a (grep 검색어) · appr-8ef6fc12516a (python -c 안 문자열 — 코드 실행이라 차단 유지가 맞음) · appr-bf94f42db1b4 (수정 전 실 hook 확인) · appr-6c010e008077 (Phase 12 의 실제 브랜치 강제 삭제 시도 — 이후 일반 삭제로 대체됨).

## N. 관측성·API 보강
- scheduler: 실제 실패 (START 후 END 없음) 와 미실행 공백 분리 · 분모(관측 구간 기대 tick)·분자 표시 — 23.88h 동안 33/33 완주 · 실패 0 · 기대 144 대비 coverage 22.9% · 공백 3회 (최대 690분) → 연속 운영 증거 부족.
- Platform API 요청별 감사 로그 `.claude/logs/platform-api-audit.jsonl` (시각·작업·요청자·인자·결과) · 자동화 식별자 승인 거부도 기록.
