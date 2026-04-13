# 구현 결과 보고서 — [작업명]

> 날짜: [YYYY-MM-DD]
> 담당: Codex / Claude
> 검증: Gemini

---

## 요약

| 항목 | 내용 |
|------|------|
| 작업 | [task-instruction.md 제목] |
| 상태 | 완료 / 부분완료 / 실패 |
| 소요 시간 | [소요시간] |

---

## 완료 조건 결과

| 항목 | 결과 | 비고 |
|------|------|------|
| 라우터 등록 | PASS | src/router/index.js |
| API 연결 | PASS | 환경변수 사용 확인 |
| 린트 통과 | PASS | 에러 0건 |
| 빌드 통과 | PASS | |
| 스모크 테스트 | PASS | 1건 작성 |

---

## 생성/수정 파일

### 생성
- `src/pages/SamplePage.vue` — 신규 페이지

### 수정
- `src/router/index.js` — 라우터 등록 추가

---

## 검증 결과 (Gemini 리뷰)

> gemini-a --verify 실행 결과

| 항목 | 결과 |
|------|------|
| 보안 이슈 | 없음 |
| 하드코딩 | 없음 |
| 성능 이슈 | 없음 |

---

## 남은 이슈

- [ ] [이슈가 있으면 여기에 기록]

---

## 다음 단계

1. Claude 검토 및 채택 결정
2. gemini-a --verify 통과 확인
3. deploy.bat 실행 (--confirmed)
