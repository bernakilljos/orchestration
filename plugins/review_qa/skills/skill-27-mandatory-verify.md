# Skill 27: Mandatory Verification (필수 검증)

## 목적
모든 코드 변경 후 검증을 **강제**한다.
검증 없이 완료 처리하는 것을 원천 차단.

## 핵심 원칙
```
1. 구현했으면 반드시 검증해라 — 예외 없음
2. 검증 실패하면 완료 아니다 — done/ 이동 차단
3. 검증은 자동이다 — 사람이 안 해도 hook이 한다
```

## 트리거
- codex-auto 태스크 완료 시 (자동)
- gemini-auto 검증 시 (자동)
- claude-auto 구현 완료 시 (자동)
- `git commit` 전 (pre-commit hook)

## 검증 단계 (5단계)

### Stage 1: 문법 검증 (자동 — hook)
```
Python: py_compile.compile() → SyntaxError 감지
JS/Vue: node --check → 파싱 에러 감지
Java:   javac -d /tmp → 컴파일 에러 감지
→ 실패 시: 태스크 완료 처리 차단
```

### Stage 2: 인코딩 검증 (자동 — hook)
```
UTF-8 확인: file 명령어로 인코딩 감지
깨진 한글: \ufffd 연속 패턴 감지
UTF-16 차단: BOM 확인
→ 실패 시: 파일 복원 + 경고
```

### Stage 3: 보호 파일 검증 (자동 — hook)
```
config.py, settings.json, .env 변경 여부
→ 변경됐으면: git checkout으로 원복 + 경고
```

### Stage 4: 기능 검증 (gemini-auto 또는 수동)
```
서버 기동 테스트: python main.py / npm run dev
API 엔드포인트 호출: curl http://localhost/health
UI 렌더링 확인: playwright MCP
→ 실패 시: review-result.md에 "불합격" 기록
```

### Stage 5: 통합 검증 (Claude 또는 수동)
```
전체 테스트 스위트: pytest / npm test
린트: eslint / pylint
빌드: npm run build / mvn package
→ 실패 시: Claude가 수정 후 재검증
```

## codex-auto 강제 검증 흐름

```
codex-auto가 태스크 실행
  ↓
codex 완료
  ↓
post-impl-verify.sh 자동 실행 ← Stage 1,2,3
  ↓ 통과?
  ├─ YES → lock 해제, git commit
  └─ NO  → 에러 출력, lock 유지, done/ 이동 안 함
           → 다음 워커가 다시 시도하거나 Claude 에스컬레이션
```

## gemini-auto 강제 검증 흐름

```
gemini-auto가 검증 시작
  ↓
반드시 실행해야 할 것:
  1. 변경된 파일 목록 확인
  2. 각 파일 문법 검증
  3. import 체인 검증 (import X → X 파일 존재?)
  4. 서버 기동 테스트 (가능하면)
  5. review-result.md 작성 (합격/불합격 필수)
  ↓
review-result.md 없으면 → 검증 미완료 → 재실행
```

## task-instruction.md 자동 삽입 규칙

모든 task-instruction.md에 자동으로 추가:
```markdown
## 검증 (필수 — 생략 금지)
- [ ] 변경 파일 전체 문법 검증 (python -c "import py_compile; ...")
- [ ] 서버 기동 확인 (python main.py 또는 npm run dev)
- [ ] 인코딩 확인 (UTF-8, 한글 깨짐 없음)
- [ ] 보호 파일 미변경 확인 (config.py, settings.json)
```

## 사고 사례
```
2026-04-12: codex가 api.py에 깨진 한글 삽입 → SyntaxError → 서버 다운
2026-04-12: gemini가 제안서만 쓰고 검증 안 함 → 버그 그대로 배포
→ 이 skill + hook으로 검증을 강제화
```
