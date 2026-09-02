# 해결책 재사용 룰 (Solution Reuse · 양방향 초최고)

> **근거**: 2026-09-02 사용자 지적 — "처리했던 DB 어떻게 처리했는지 알아야 쉽게 재사용 · 읽기(자동 조회) + 쓰기(처리 결과 기록) 양방향 · 초초초초초 최고".
> **이유**: 세션 히스토리만으로는 부족. **문제 → 해결책 → 재사용** 카탈로그로 진화.

## 절대 룰

**모든 세션 종료 시 문제·해결·파일·명령 자동 캡처 · 다음 세션 UserPromptSubmit 시 관련 solution 자동 조회 · systemMessage 주입.**

## DB 스키마

```sql
CREATE TABLE problem_solutions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  session_id TEXT,
  problem TEXT NOT NULL,           -- 문제·질문·요청
  category TEXT,                    -- db·hook·mcp·rule·skill·commit·install·ui·memory·finetune·embedding·optimize·file·general
  keywords TEXT,                    -- 자동 추출 8 개
  approach TEXT,                    -- 접근·활성 skill·rule
  solution TEXT,                    -- 결정·명령·해결
  files_modified TEXT,              -- 건드린 파일 (file_audit 종합)
  commands_run TEXT,                -- 실행 명령
  verified INTEGER DEFAULT 0,       -- 0=미검증·1=검증 완료
  reusable_score INTEGER DEFAULT 5, -- 0~10 재사용 가치
  problem_hash TEXT,                -- SHA-256 앞 16 · 중복 방지
  UNIQUE(problem_hash)
);
```

## 양방향 시스템

### 쓰기 (자동 캡처)
- **Stop / SessionEnd hook** → `save_solution.py auto`
- 이번 세션 conversations + activations + decisions + file_audit 종합
- 카테고리 자동 분류 (13 유형)
- keywords 자동 추출 (8 개)
- problem_hash 로 중복 방지 (같은 문제 반복 방지)

### 읽기 (자동 조회)
- **UserPromptSubmit hook** → `lookup-history.sh` 확장
- 사용자 프롬프트 키워드 → problem_solutions 검색
- reusable_score DESC + ts DESC 정렬 · top 3
- systemMessage 로 주입 → Claude 자동 인지

### 수동 CLI
```bash
# 문제·해결 수동 등재 (score=8 검증)
python .claude/scripts/save_solution.py manual "문제 요약" "해결 요약" [카테고리] [점수]

# 재사용 검색
python .claude/scripts/save_solution.py search "쿼리 키워드"

# 이번 세션 자동 캡처 (수동 트리거)
python .claude/scripts/save_solution.py auto
```

## 카테고리 매핑 (자동)

| 카테고리 | 트리거 키워드 |
|---|---|
| db | sql·sqlite·database·테이블·orca.db·migration |
| hook | hook·sessionstart·posttooluse·userpromptsubmit |
| mcp | mcp·claude-mem·headroom·task-observer |
| rule | rule·룰·.claude/rules |
| skill | skill·스킬·.claude/skills |
| commit | commit·git·push·branch |
| install | install·setup·pip install·npm install |
| ui | shadcn·tailwind·antd·mui·화면·디자인 |
| memory | memory·메모리·conversations·session_summary·이력 |
| finetune | 파인튜닝·fine-tune·lora·qlora·unsloth |
| embedding | 임베딩·chromadb·vector·sentence-transformers |
| optimize | 최적화·optim·compress·vacuum·cache |
| file | 파일·명명·naming·cleanup·audit |
| general | 위에 없음 |

## reusable_score 기준

| 점수 | 의미 |
|---|---|
| 10 | 완벽 재사용 · 명시 패턴 · 여러 번 통용 |
| 8~9 | 검증된 solution · 사용자 명시 승인 · verified=1 |
| 5~7 | 자동 캡처 · 통상 (default) |
| 2~4 | 부분 solution · 상황별 조정 필요 |
| 0~1 | 실패한 접근 · 참고만 · 반복 금지 |

## Retention

- problem_solutions: **무기한 유지** (카탈로그 자산)
- reusable_score < 3 · 6개월 초과 · 자동 삭제 (검토 후)
- 중복 (problem_hash 동일) · UPSERT (최신으로 갱신)

## 검증·정제

주 1회 (일요일 04:00 · weekly-audit):
- 유사 problem 통합 제안
- verified=0 오래된 것 · 자동 verified=1 승격 (재사용 이력 있으면)
- reusable_score 자동 조정 (검색 hit 다수 → 점수 상향)

## 사용 예 (실전)

```bash
# 검색
$ python .claude/scripts/save_solution.py search "MCP 통합"

## 검색: MCP 통합 · 3 결과

[mcp · score=8 · 2026-09-02 15:30]
  문제: OmniRoute·claude-mem·Headroom 등 5 MCP 통합 원함
  해결: Headroom Apache 2.0 · claude-mem 로컬 · task-observer Skill · OmniRoute route.py 겹침 제외
  파일: .claude/rules/mcp-integration.md, mcp-autostart.sh, setup/modules/16
```

## 금지

1. verified=0 solution 을 자동 적용 X (사용자 확인 필요)
2. reusable_score < 3 자동 재사용 X
3. problem_hash 없이 저장 X (중복 폭주)
4. 개인정보·시크릿 포함 저장 X (마스킹 예정)
5. 대량 저장 후 index 없이 검색 X (성능 저하)

## 관련

- `.claude/scripts/save_solution.py` (양방향 CLI + auto)
- `.claude/hooks/save-session-summary.sh` (Stop/SessionEnd · auto 캡처)
- `.claude/hooks/lookup-history.sh` (UserPromptSubmit · auto 조회)
- `.claude/rules/conversation-history.md` (세션 히스토리 병행)
- CLAUDE.md § 3.1 (5) 세션 히스토리 로드 (2026-09-02)
- `orca.db.problem_solutions` (테이블)
