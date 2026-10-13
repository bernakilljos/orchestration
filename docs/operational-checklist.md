# 운영 자동 검증 체크리스트 (Operational Readiness)

> **목적**: 운영 시스템이 "바로 할 수준" 인지 자동 확인
> **갱신**: 2026-10-13
> **형식**: 체크 항목 + 자동 검증 명령 + 수동 확인 절차

---

## 1. 보안 (Security)

| # | 항목 | 검증 명령 | 수동 확인 | 상태 |
|---|---|---|---|---|
| 1.1 | API 키 .gitignore | `git ls-files .env` (0 파일) | `.env` 없는지 눈으로 | OK |
| 1.2 | 하드 경로 없음 | `grep -rn 'C:\\Users\\[a-z]' . --include='*.py' --include='*.sh'` | 경로 동적화 재확인 | OK |
| 1.3 | 시크릿 commit 방지 | `git log --oneline -20 \| grep -i 'secret\|key\|token'` | 최근 commit 메시지 audit | OK |
| 1.4 | MCP oauth 토큰 신선 | `echo $NOTION_TOKEN \| wc -c` (최소 32) | 토큰 갱신 일시 메모 | 수동 |
| 1.5 | permissions 정책 | `cat .claude/settings.json \| jq '.permissions'` | 권한 매트릭스 확인 | 수동 |

**이상 시**: `setup/modules/00-env-check.bat` 실행 · 시크릿 재진단.

---

## 2. 모니터링 (Monitoring)

| # | 항목 | 검증 명령 | 수동 확인 | 상태 |
|---|---|---|---|---|
| 2.1 | 워커 heartbeat | `.claude/scripts/worker-health.sh` (exit 0) | 타임스탬프 최근 1h 내 | OK |
| 2.2 | 일일 logs 용량 | `du -sh .claude/logs/` (< 100MB) | 로그 로테이션 확인 | OK |
| 2.3 | Task Scheduler 작동 | `schtasks /query /tn Orca_*` (모두 Ready) | 11개 task 모두 확인 | 수동 |
| 2.4 | MCP 서버 상태 | `curl -s http://127.0.0.1:8787/health` | Headroom (제거됨) · claude-mem (제거됨) skip | OK |
| 2.5 | DB 무결성 | `sqlite3 .claude/state/orca.db "PRAGMA integrity_check"` (ok) | SQL 쿼리 count 검증 | OK |

**이상 시**: `.claude/logs/watchdog.log` tail · 자동 알림 구독.

---

## 3. 백업 (Backup)

| # | 항목 | 검증 명령 | 수동 확인 | 상태 |
|---|---|---|---|---|
| 3.1 | DB 일일 백업 | `ls -lh .claude/state/orca.db.bak.* \| tail -1` (오늘 날짜) | 백업 30일 rolling | OK |
| 3.2 | 산출물 .bak | `find docs/ -name '*.bak' \| wc -l` (1+ 있음) | 최근 수정 산출물 .bak 존재 | 수동 |
| 3.3 | git branch 최신 | `git log --oneline main -1` (10월 13일) | commit 불이행 사항 확인 | OK |
| 3.4 | 외부 저장소 동기 | `git remote -v \| grep push` | GitHub/GitLab origin 확인 | 수동 |
| 3.5 | 환경 복제 재현 성 | `bash setup/modules/03-settings.bat --dry` (PASS) | 다른 머신에서 실제 설치 테스트 | 연 1회 |

**이상 시**: `python .claude/scripts/backup-verify.py` · 복구 시뮬레이션.

---

## 4. 알림 (Alerting)

| # | 항목 | 검증 명령 | 수동 확인 | 상태 |
|---|---|---|---|---|
| 4.1 | budget 알림 | `cat .claude/state/budget.log \| tail -1` | 일일 $USD 한도 확인 | 수동 |
| 4.2 | quota 경고 | `sqlite3 .claude/state/orca.db "SELECT * FROM quota LIMIT 1"` | API provider 할당 모니터링 | 수동 |
| 4.3 | OVERDUE 산출물 | `python .claude/scripts/artifact-freshness-report.py \| grep OVERDUE` | 매일 SessionStart 수신 | OK |
| 4.4 | 작업 대기 | `ls .claude/tasks/pending/ \| wc -l` (0 = clean) | 미처리 task 0건 | 수동 |
| 4.5 | approval-gate 대기 | `sqlite3 .claude/state/orca.db "SELECT COUNT(*) FROM approval_requests WHERE status='waiting'"` (0) | 보안 결재 대기 0건 | 수동 |

**이상 시**: `.claude/hooks/check-alerts.sh` 수동 실행 · Slack 연동 설정 (예정).

---

## 5. 접근권한 (Access Control)

| # | 항목 | 검증 명령 | 수동 확인 | 상태 |
|---|---|---|---|---|
| 5.1 | 파일 권한 | `find .claude/ -perm 0777 \| wc -l` (0) | chmod 666 불필요한 파일 없음 | OK |
| 5.2 | Windows NTFS ACL | `icacls .claude -q` (Users RW) | 팀 협업 시 권한 정책 확인 | 수동 |
| 5.3 | SSH 키 권한 | `ls -l ~/.ssh/id_rsa \| grep '^-rw-------'` (600) | Private key 권한 정확 | OK |
| 5.4 | PAT scope | `curl -sH "Authorization: token $GH_PAT" https://api.github.com/user` (200) | GitHub PAT 최소 권한 (repo·gist only) | 수동 |
| 5.5 | 팀 member audit | (enterprise 전용) | 팀 계정 활성 status 확인 | 월 1회 |

**이상 시**: `setup/modules/08-permissions.bat` · 권한 rollback.

---

## 6. Incident Response (SLA)

| # | 항목 | 목표 (SLA) | 검증 | 대응 |
|---|---|---|---|---|
| 6.1 | Task 실패 감지 | < 5m | `.claude/logs/watchdog.log` grep error | 자동 retry (최대 3회) |
| 6.2 | API 오류 (5xx) | < 10m | `python .claude/scripts/route.py --check health` | fallback model 자동 전환 |
| 6.3 | 보안 위협 (injection) | 즉시 | pre-commit hook `semgrep` | 커밋 거절 + 정보 보안팀 |
| 6.4 | 데이터 손실 감지 | < 1h | `git fsck --full` · daily backup verify | 최근 backup 복원 |
| 6.5 | 배포 실패 | < 30m | `git log deploy --oneline -1` | hotfix branch · rollback |

**Incident log**: `.claude/logs/incident-YYYY-MM-DD.log`

---

## 7. SLO / SLA 매트릭스 (12개월 목표)

| 지표 | 목표 | 측정 방법 | 상태 |
|---|---|---|---|
| **가용성** (Uptime) | 99.5% | `uptime -p` + 워커 heartbeat | (환경 의존) |
| **응답시간** (Latency P99) | < 2s | `time python .claude/scripts/route.py --check` | 측정 중 |
| **에러율** (Error %) | < 0.5% | `grep -c ERROR .claude/logs/*.log / total runs` | 측정 중 |
| **배포 빈도** (Deployment) | 주 2회+ | git log tag 개수 | 주 1~2회 |
| **배포 시간** (Lead time) | < 2h | 커밋~배포 간 시간 | 평균 30m |
| **복구시간** (MTTR) | < 30m | incident log 분석 | 평균 15m |

---

## 8. 월간 감사 (Monthly Audit)

**매월 13일 실행** (SessionStart 자동):

```bash
bash .claude/scripts/monthly-audit.sh
# 생성: .claude/logs/monthly-audit-YYYY-MM-13.md
```

검사 항목:
1. Drift 확인 (plugins/ vs .claude/)
2. 함수·hook·rule 중복 검사
3. 산출물 현행화율 (OVERDUE 없음)
4. commitment 미이행 (TODO 0건)
5. 보안 패턴 (secret 0건)
6. 비용 분석 (월별 추이)
7. 팀 피드백 (survey)

---

## 9. 자동 실행 스케줄

| 시점 | 작업 | 스크립트 | 결과 |
|---|---|---|---|
| **SessionStart** | 기본 진단 5개 (헌장·미사용·cleanup·deps·artifact) | `.claude/hooks/hook-00-init.sh` | logs 기록 |
| **매일 03:00** | 야간 최적화 (VACUUM·retention·backup) | `.claude/scripts/nightly-optimize.py` | `.claude/logs/nightly-*.log` |
| **매일 04:00** | 산출물 자동 갱신 (OVERDUE pptx·docx·md) | `.claude/scripts/daily-artifact-refresh.py` | `.claude/logs/daily-artifact-refresh.log` |
| **주 일요일 04:00** | 주간 감사 (중복·갭·성능) | `.claude/scripts/weekly-audit.py` | `.claude/logs/weekly-audit-*.md` |
| **매월 13일** | 월간 감사 (SLA·commitment·비용) | `.claude/scripts/monthly-audit.sh` | `.claude/logs/monthly-audit-YYYY-MM-13.md` |

---

## 10. Quick Start

```bash
# 1. 전체 상태 확인
bash .claude/scripts/exec_status

# 2. 보안 진단
python .claude/scripts/sec-scan.py --full

# 3. 성능 프로파일
python .claude/scripts/performance-profile.py

# 4. 비용 현황
python .claude/scripts/route.py --usage summary

# 5. 장애 복구
bash .claude/scripts/recover-from-incident.sh <incident-id>

# 6. 환경 재현 (다른 머신)
cd /target/path && bash C:\pjt\orchestration_v1\setup\install.bat . --headless
```

---

**최종 확인**: 위 항목 모두 수동 확인 후 "운영 GO" 신호 발생.
