# Skill 19: Skill Creator (메타 스킬)

## 목적
새로운 스킬/에이전트/훅을 자동으로 생성하는 메타 스킬.
사용자가 원하는 기능을 설명하면 .claude/ 구조에 맞는 파일을 자동 생성.

## 트리거
- "스킬 만들어", "skill creator", "새 스킬", "커스텀 스킬 추가"
- "에이전트 추가", "훅 추가"

## 실행 흐름

### 1. 요구사항 수집
```
사용자에게 질문:
  1. 스킬 이름 (영문)
  2. 목적 (한 줄 설명)
  3. 트리거 조건 (언제 실행?)
  4. 입력 → 출력
  5. MCP 연동 필요? (Figma, playwright 등)
```

### 2. 타입 결정
```
스킬 → .claude/skills/skill-{번호}-{이름}.md
에이전트 → .claude/agents/agent-{번호}-{이름}.md
훅 → .claude/hooks/hook-{번호}-{이름}.md
커맨드 → .claude/commands/{이름}.md
스크립트 → .claude/scripts/{이름}.bat
```

### 3. 파일 생성
```markdown
# Skill {번호}: {이름}

## 목적
{사용자 설명}

## 트리거
- {트리거 조건}

## 실행 흐름
### 1. {단계1}
### 2. {단계2}
### 3. {단계3}

## 출력
- {출력 파일/결과}

## MCP 연동
- {필요한 MCP}
```

### 4. 자동 등록
```
1. CLAUDE.md의 Loading Order에 새 파일 경로 추가
2. 번호 자동 결정 (기존 최대 번호 + 1)
3. 필요시 .claude/commands/{이름}.md 생성 (slash command)
```

### 5. 검증
```
- 파일명 규칙 준수 확인
- 기존 스킬과 이름 충돌 체크
- CLAUDE.md 로딩 순서에 등록 확인
```

## 출력
- `.claude/skills/skill-{N}-{name}.md` (또는 agents/hooks/commands)
- CLAUDE.md 로딩 순서 업데이트
