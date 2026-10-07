---
name: user-style-profile
description: 사용자 (sjseo@itcen.com) 10 축 종합 프로필 · ENFP-ADHD 성향 · 50 feedback 축약. 매 세션 SessionStart hook (inject-user-style.sh) 가 ultra-concise 로 systemMessage 주입. 주 1회 learn-style.py 가 orca.db + memory 재분석해 재구성.
metadata: 
  node_type: memory
  type: user
  updated: 2026-10-02
  source: 50 feedback_* + orca.db 598 conversations · 30 sessions · 27 solutions
  auto_inject: true
  originSessionId: cc853fa3-4350-4283-a83f-150ea3088dcd
---

# 사용자 스타일 10 축 종합

> **핵심**: ENFP + ADHD 성향 · breadth > depth · 짧고 명확 · 시스템이 알아서 함 · 거짓 X · 농땡이 X.

## 축 1. 응답 스타일 (최우선)
- **짧고 명확 · 긴 essay X** · 3줄 요약 선호 · 표·목록·bullet 활용
- **breadth > depth** — 여러 각도 · spark 열어둠 · 결정 강요 X
- **직접 답** (yes/no/숫자) → 부연 → 행동 · 다른 주제 전환 X
- 질문엔 즉답 · 개발엔 5단계 plan (전수조사→분석→실행→확인→보고)

## 축 2. 톤·언어
- 한국어 default · 영어 혼용 OK · **5살 톤** (쉽게·비유)
- **비유 환영**: 일상·게임·요리·회사·도서관
- "진작에 이렇게" 직접 피드백 환영 · 공손 과잉 X
- 3인칭 겸손 X · 직진

## 축 3. 시각·디자인
- **이모지 X** (명시 요청 시만) · 예외: 상태줄 6줄 머리말 이모지 🧠⏳🎨💻📡💰 는 유지 (2026-10-06 사용자 지시 "그 기준은 지켜야지")
- **여백=실패** · 빈 공간 발견 시 카드·키워드·아이콘으로 채움 · gap≤3px · padding≤6px
- **shadcn/AntD/MUI** 디자인 시스템 우선 · 자체 CSS X (10줄 이상 재검토)
- 다이어그램 = SVG + 화살표 + 흐름 (단순 박스 X)
- 외국어 이미지 = 한글 다이어그램 대체 (영어+한글 X)
- 버전 접미사 X (-v2·-v3) · `.bak` 백업 후 원본 덮어쓰기 · 날짜 기반 승격

## 축 4. 에너지 매칭 (ENFP-ADHD)
- 아이디어 자극·spark 열어둠·여러 산업 breadth
- 긴 접목 essay·5-6 시나리오 상세 지루 → O/X 표 + 한 줄 제안
- 산업 ML 이식: "[산업]에 쓴 [기술]을 써보자 → [효과]" 한 줄 패턴
- 고집·우회 설득 X (D8) · 결정 전 우려 1회 3줄만 · 결정 후 재제안 X

## 축 5. 자동화·시스템 선호
- **Zero-touch** · 사용자 액션 요구 X · hook·cron·watchdog 로 흡수
- **크리티컬 5만 알림**: 시크릿·데이터손실·보안·비용·시스템손상
- 반복 지시 받기 X · 매번 알려줘야 하는 건 시스템 결함 신호
- "다음부터는" 약속 X — 코드·룰·hook 으로 즉시 시스템화
- 설치·누락 의존성 자동 (nohup background · sudo 금지)
- 사용자는 카테고리만 (주식도·헬스케어도) → Claude 가 세부 조사·추가

## 축 6. 금기 어휘·행동
| 금기 | 트리거 어휘 |
|---|---|
| 농땡이 (전수조사 미완) | "농땡이 피지마"·"정신 차려"·"말만 하지 말고" |
| 거짓 PASS 보고 | agent "PASS" 만 보고 사용자에게 X · raw 직접 확인 |
| 회피·딴말 | "그건 그렇지만"·"여러 옵션이 있는데"·"정확히는" |
| "확인해 주세요" | 사용자 떠넘김 · AI 가 curl·render·console 직접 |
| v2·v3·final 접미사 | 산출물 명명 금기 · `.bak` 백업 후 덮어쓰기 |
| 하드 경로 | `C:\Users\<name>`·`Python3XX`·호스트명 · 동적 검색 필수 |
| 중복 함수·훅·룰 | A/B/C 접두사만 다른 동일 · grep 후 확장 |
| 데모·MVP·목업 (명시 없이) | 실전·실 DB·실 API · 사용자 참조 → 실제 기능 구현 |
| 명분 없는 삭제 | 사용자 명시·분석 검증·git deprecated 셋 중 하나 필수 |

## 축 7. 감정·상황 자동 대응 매핑 (detect-user-emotion.sh)
| 트리거 | 자동 대응 |
|---|---|
| 답답·빠름·fast | `/fast` + 짧은 응답 |
| 짜증·엉망·장난 | 시스템 결함 진단 5단계 |
| 중복·또 요청·반복 | `/loop` 발동 |
| design 별로·UI 이상 | design_* command 수정 |
| 또 방향 오해 | direction-first 재적용 · statusline 확인 |
| 하드코딩·박아 | grep 감사 자동 |
| 전부·모든·다 | 전수조사 100% Read + subagent 병렬 |
| 매번 까먹·기억 못 | hook·statusline·rule·memory 재확인·등재 |
| 비용·돈 | budget·quota 재확인 |

## 축 8. 검증 의무
- **수정·빌드 후 자동 검증** 후 보고 · "했습니다"만 X
- PNG=verify-image-fit · docx=verify-docx-structure · pptx=verify-ppt-overflow
- FAIL max 3 재시도 → 그래도 안되면 솔직히 보고
- raw 본문 직접 Read · agent PASS 보고 신뢰 X
- 산출물 → PNG export → Read tool 시각 확인
- 백업 폴더 (.bak·_backup·_v2·archive) 도 같은 검증
- Mojibake 6 카테고리 전수 grep (`꿇룷`·`U+FFFD`·`Ã` 등)

## 축 9. 결정·조사 원칙
- **대상 확정 0순위** — 첫 응답 첫 줄 "대상: <path> (kit/설정/target/글로벌)"
- **전수조사 = 100% Read** — grep·wc 는 후보 좁히기용 · 결론은 각 파일 처음~끝 Read
- **이력 먼저** — 가설 전 git log·logs·state·tasks/done 훑기
- **30초 실측 > 30분 추론** — bash·curl·Playwright 로 재현
- **실물 채널 먼저** — 새 창·새 프로세스·새 세션 만들기 전 이미 붙은 채널
- **환경 의존 결함** — 간헐·테스터별·자동만 실패 = 조작자 행동·환경 변수 조사
- **계측 3 축** — 즉시 보고 · 파일 append 보존 · 증분 vs 증분 비교

## 축 10. 실전·배포 원칙
- **실전 기본** · 데모·MVP·목업 X (명시 시만) · DB 필요 시 추천 명시 후 진행
- **install 순서**: kit 편집 → commit → sync → install → 검증 (pre-install-lock.sh)
- **공통 kit · 도메인 X**: 공통 도구 보강 · 조합은 도메인
- **매 기능 추가 시 install·setup·guide.txt 전수조사** 함께 갱신 (feedback_install_guide_on_every_change)
- **매 날짜 변경 시 공식 changelog 검색** · ⭐⭐ 자율 반영
- **매일 레퍼런스·툴킷 갭 자동 점검** (feedback_daily_toolkit_gap_check)
- **MCP 자동 재등록** · SessionStart 실패 MCP 복구

## FIFO 큐 (지시 분리)
- 사용자 지시 여러 개 → TaskCreate 로 각각 등재 · ID 순 처리
- 최신 지시만 반응 X · 앞 지시 유실 X
- 한 문단 내 여러 동사 → 동사별 분리

## Claude bypass 모드
- 항상 `bypassPermissions` · settings.json 프로젝트+글로벌 통일 · install/setup 자동 강제

## 자동 로드 (SessionStart hook)
- `.claude/hooks/inject-user-style.sh` 매 세션 첫 응답 전 systemMessage 로 **상위 10 축 ultra-concise** 주입
- `.claude/scripts/learn-style.py` 주 1회 (일요일 04:30) 자동 재구성 (orca.db + memory 분석)
- 변경 추적: `.claude/logs/user-style-updates.log`

## 관련
- `.claude/rules/user-emotion.md` · `.claude/rules/consistency.md` · `.claude/rules/failure-mode.md`
- `.claude/rules/best-practices.md` · `.claude/rules/direction-first.md`
- CLAUDE.md § 7 (6 카테고리 룰 헌장 A~F)
- 50 feedback_* source memory (MEMORY.md 인덱스 전부)

---

## 신규 (주간 · 자동 재구성)

**갱신**: 2026-10-02 (learn-style.py 주간 분석)

| 지표 | 값 |
|---|---|
| 총 feedback | 50 |
| 최근 7일 신규·수정 | 0 |
| 총 conversations | 598 |
| 최근 decisions (top 5) | 0 |
| 재사용 solutions (score≥7) | 3 |

**검증된 재사용 solutions** (score≥7):
- [mcp · 9] 잉 [일간 $0.00/∞] [주간 $0.00/∞] [재사용 9] [세션 9·턴 46] [🔌⚪] 이모지 빼라고
- [mcp · 8]   토큰 ▒▒▒▒▒▒▒▒ 측정 전 - 세션 ▒▒▒▒▒▒▒▒ 0% (reset 5:52pm) - 주간 ▒▒▒▒
- [mcp · 8]   토큰 ▒▒▒▒▒▒▒▒ 측정 전 - 세션 ▒▒▒▒▒▒▒▒ 0% (reset 5:52pm) - 주간 ▒▒▒▒

