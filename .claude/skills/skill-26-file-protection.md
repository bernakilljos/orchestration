# Skill 26: File Protection (핵심 파일 보호)

## 목적
codex-auto, gemini-auto, claude-auto가 핵심 설정 파일을 수정/삭제하지 못하도록 보호한다.
실수로 config, settings, main 파일이 깨져서 서버가 다운되는 사고를 방지.

## 트리거
- PreToolUse hook (Edit/Write 시 자동 실행)
- task-instruction.md 작성 시 금지 규칙 자동 삽입

## 보호 대상 파일

### Tier 1: 절대 수정 금지 (hook으로 차단)
```
config.py              서버 설정 (수정 시 서버 다운)
.claude/settings.json  hook 설정 (수정 시 hook 전체 깨짐)
.claude/settings.local.json  권한 설정
.env / .env.local      환경변수 (시크릿 포함)
deploy-config.env      배포 설정
```

### Tier 2: 구조 변경 금지 (경고)
```
main.py / app.py       앱 진입점 (import 순서, 초기화 로직)
manage.py              Django 매니저
package.json           의존성 (버전 변경 주의)
pom.xml                Maven 설정
```

### Tier 3: 삭제 금지 (경고)
```
.claude/tasks/task-instruction.md  현재 지시서
CLAUDE.md              마스터 지시서
.gitignore             git 무시 규칙
```

## Hook 구현

### protect-critical-files.sh (PreToolUse)
```bash
# Edit 또는 Write 시 파일명 확인
# 보호 대상이면 exit 2 (차단)
# 아니면 exit 0 (허용)
```

### settings.json에 등록
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/protect-critical-files.sh" }
        ]
      }
    ]
  }
}
```

## task-instruction.md 자동 삽입

task-instruction.md 작성 시 (agent-01-team-lead) 다음 금지 규칙을 자동 삽입:

```markdown
## 절대 금지 (위반 시 서버 다운)
- **config.py 수정 금지**
- **settings.json 수정 금지**
- **main.py 구조 변경 금지**
- **.env 파일 수정 금지**
```

## Codex/Gemini 특별 규칙

### codex-auto 완료 시
```
task-instruction.md를 done/으로 이동하면 안 됨
→ 복사만 허용: copy task-instruction.md done/
→ 원본은 유지 (다음 워커나 gemini가 참조해야 함)
```

### gemini-auto 완료 시
```
review-result.md만 생성
→ 기존 파일 수정/삭제 금지
```

## 사고 사례 (실제 발생)
```
2026-04-12: codex가 config.py 삭제 → Flask 서버 다운 (4시간 작업 손실)
2026-04-12: codex가 settings.json 덮어씀 → hook 전체 깨짐
2026-04-12: codex가 task-instruction.md를 done/으로 이동 → 지시서 사라짐
→ 이 skill + hook으로 재발 방지
```
