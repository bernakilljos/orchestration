# 다른 PC · 다른 세션 셋업 안내

이 문서를 **그대로 복사해서 다른 PC 의 Claude Code 세션에 붙여넣으면** 된다.
(git clone → 워크트리 분리 → Edge 확장 로드 → 중계 서버까지)

---

## A. 다른 세션에 붙여넣을 프롬프트 (복사용)

```
아래 순서로 셋업해줘. 각 단계는 실행하고 결과를 확인한 다음 다음으로 넘어가.

■ 1) 저장소 받기
   git clone https://github.com/bernakilljos/ICMAI.git C:\icm
   cd C:\icm
   git checkout phase8
   ★경로에 한글·한자를 넣지 마. ASCII 경로(C:\icm)로만 받아.
     (이 프로젝트는 한글 경로 때문에 인코딩 사고가 난 이력이 있다)

■ 2) 역할 확인 — 세션끼리 서로 안 보이니 범위를 지켜야 한다
   · 이 세션이 맡을 일 : (개발  /  검증)  ← 수석이 지정한 쪽만 한다
   · 다른 세션이 만지는 파일은 건드리지 않는다
   · 같은 파일을 두 세션이 고치면 한쪽 수정이 조용히 사라진다(에러도 안 난다)

■ 3) 브랜치 분리 — 개발 세션이면 반드시
   git worktree add C:\icm-dev -b dev
   cd C:\icm-dev
   ★브랜치만 바꾸는 것(git checkout)으로는 분리가 안 된다.
     작업 폴더가 하나라서 다른 세션이 보는 파일도 같이 바뀐다.
     워크트리는 폴더가 따로 생기니 물리적으로 안 겹친다.

■ 4) Python 환경
   cd C:\icm  (또는 C:\icm-dev)
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ★Python 3.13 을 쓴다(3.14 는 일부 휠이 없다).

■ 5) .env 준비 — git 에 없다(시크릿이라 제외됨)
   copy .env.example .env
   그리고 수석에게 실제 값을 받아 채운다.
   ★.env 를 커밋하지 마.

■ 6) Edge 확장 로드 (ask-web 브리지)
   ① Edge 주소창 → edge://extensions
   ② 좌측 하단 「개발자 모드」 켜기
   ③ 「압축을 풀린 항목 로드」 클릭
   ④ 이 폴더 선택 :  C:\icm\Project1.5\tools\ask_web_extension
   ⑤ 확장 아이콘 → 중계 주소가 127.0.0.1:9080 인지 확인
   ★확장 소스는 git 에 들어 있다(6개 파일). 따로 받을 것 없다.
   ★Chrome 에서도 같은 방식으로 된다(manifest v3 공통).

■ 7) 중계 서버 띄우기
   cd C:\icm\Project1.5
   .venv\Scripts\python scripts\ask_web_relay.py
   → 9080 에서 뜬다. 이 창은 켜 둔다.
   ★9077 / 9078 / 9079 는 제품 서버 포트다. 건드리지 마.

■ 8) 브라우저 쪽 준비
   ① Edge 에서 claude.ai 로그인
   ② develop 프로젝트의 대화 화면을 열어 둔다
   ③ 확장 팝업 → 필요할 때만 「자동 전송」을 켠다
      (켜 두면 대기 질문이 계속 나가 레이트 리밋에 걸릴 수 있다)
      즉시 보내려면 「지금 보내기 (1회)」

■ 9) 동작 확인 (여기까지 해야 완료다)
   .venv\Scripts\python scripts\ask_web_relay.py ask "셋업 확인용 테스트"
   → 질문 id 가 출력된다
   확장 팝업에서 「지금 보내기 (1회)」 → 잠시 후
   .venv\Scripts\python scripts\ask_web_relay.py answer <위에서 나온 id>
   → 답이 나오면 셋업 성공.
   ★돌아온 답이 내가 보낸 질문과 똑같으면 회수 실패다(에코).
     그때는 content.js 의 SEL_* 셀렉터가 깨진 것 — 수석에게 보고해.

■ 10) 셋업 끝나면 보고할 것
   · clone 경로 / 워크트리 경로
   · 이 세션이 맡은 역할(개발 or 검증)
   · 9번 확인 결과(답 회수 성공/실패)
```

---

## B. 두 세션 병행 규칙 (짧게)

| | 검증 세션 | 개발 세션 |
|---|---|---|
| 폴더 | `C:\icm` (phase8) | `C:\icm-dev` (dev) |
| 루프 | CLI ↔ Web 반복 | CLI ↔ Codex 반복 |
| 커밋 | 검증 통과분 | Codex 산출물 |

- 합치기 : 개발 세션이 `dev` 에 커밋 → 검증 세션이 `phase8` 에서 merge → 재확인
- **커밋 게이트는 CLI 가 쥔다.** Web 답도, Codex 코드도 실측 전에는 완료가 아니다.
- 세션끼리는 실시간으로 서로를 못 본다. 겹침 방지는 **범위를 나누는 것**뿐이다.

## C. 워크트리에서 서버(9077~9079)까지 띄울 거면

코드만 고치고 커밋할 거면 이 절은 건너뛴다.

- `.env` · `local_data` 는 gitignore 대상이라 워크트리에 안 따라온다 → 복사해야 한다
- 포트가 하나뿐이라 양쪽에서 동시에 못 띄운다 → 한쪽 포트를 `.env` 로 바꿔라
- 콜드부팅 후 waitress bind 에 ~15초 걸린다. 9초 만에 확인하면 오판한다
