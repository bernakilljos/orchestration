# sec_guidance — Anthropic 공식 security-guidance 통합

> **출처**: Anthropic 공식 plugin (2026-05-27 출시, Week 22). 무료. 모델 호출 0회.
> **마켓플레이스**: `claude-plugins-official`

## 무엇

Write/Edit/MultiEdit 도구 호출 **직전**에 25개 위험 패턴을 정규식으로 검출. 매치 시 경고 + 수정 제안 → 사용자가 진행 여부 결정. **모델 비용 0** (정적 검사만).

## 검출 카테고리 (8개 주요)

| # | 카테고리 | 패턴 예 |
|---|---|---|
| 1 | Command injection (GitHub Actions) | `${{ inputs.* }}` 직접 shell 삽입 |
| 2 | `child_process.exec()` unsafe | shell=true + 사용자 입력 |
| 3 | `eval()` / `new Function()` | 동적 코드 평가 |
| 4 | XSS — `dangerouslySetInnerHTML` | React unsafe HTML |
| 5 | XSS — `innerHTML` | DOM 직접 삽입 |
| 6 | Python `pickle` deserialization | 신뢰 못한 입력 |
| 7 | `os.system()` injection | shell 명령 결합 |
| 8 | 기타 17개 (SQL injection·hardcoded secret 등) | 공식 doc 참조 |

## 설치 (사용자)

Claude Code 세션 안에서:
```text
/plugin install security-guidance@claude-plugins-official
```

또는 setup/modules 가 자동 설치 (`install-sec-guidance.bat` — 추후 추가).

## 우리 sec-scan 과의 관계

| 도구 | 시점 | 비용 | 깊이 |
|---|---|---|---|
| **sec_guidance** (Anthropic) | Write/Edit pre-hook | $0 | 25 패턴 정규식 |
| **/sec-scan** (우리 plug_dev) | 작업 완료 후 명시적 | $0 | semgrep+gitleaks+bandit (수백 룰) |

**관계**: 보완적. sec_guidance = 실시간 가드, /sec-scan = 깊은 감사. 둘 다 활성 권장.

## 참조

- `skills/skill-sec-guidance.md` — 통합 가이드
- Anthropic blog: https://www.anthropic.com/news (Week 22, 2026-05-25)
- 공식 repo: github.com/anthropics/claude-plugins-official/plugins/security-guidance
