---
paths:
  - "**/*.ps1"
  - "**/*.psm1"
  - "**/pom.xml"
  - "**/build.gradle*"
  - "**/*.csproj"
  - "**/Cargo.toml"
  - "**/go.mod"
  - "**/pyproject.toml"
  - "**/package.json"
  - ".claude/hooks/tool/ensure_ps1_bom.py"
---
# 개발 언어별 표준 룰 (Language Standards)

> **전문**: `.claude/rules-ref/language-standards.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**언어 감지 → 언어별 표준 자동 적용 (lint·format·test 규칙 · 파일 구조 · 빌드·배포 명령).**

---

## 금지

1. **언어 감지 없이 lint·format X**
2. **한 프로젝트에 여러 formatter 설정 X** (혼란)
3. **버전 오래된 도구 X** (Python 3.8 이하·Node 18 이하·Java 8 등)
4. **CI 없이 lint 요구 X** (자동 hook 활용)
5. **표준 무시 · 자체 스타일 X** (팀 확장성)

### PowerShell 한글 인코딩 (2026-11-09 · 헌장 D22)
한글이 한자처럼 보이면 문자열을 바꾸지 말고 아래 세 층을 따로 확인한다.

| 층 | 증상 | 기준 |
|---|---|---|
| 파일 인코딩 | PS 5.1 이 BOM 없는 .ps1 을 cp949 로 읽어 문자열·정규식이 깨짐 | 한글 든 .ps1/.psm1/.psd1 = **UTF-8 BOM** (pwsh 7 은 BOM 없어도 UTF-8 · 둘 다 되게 BOM) · hook `ensure_ps1_bom` 이 저장·실행 직전 자동 부착 |
| 콘솔 출력 | 파이프·캡처된 출력이 cp949 바이트 | 캡처할 스크립트는 `[Console]::OutputEncoding = [Text.Encoding]::UTF8` 명시 · 아니면 받는 쪽에서 cp949 로 디코딩 |
| 파일 기록 | PS 5.1 `Set-Content`·`Add-Content` 기본 = ANSI | 항상 `-Encoding utf8` 명시 |
| 외부 프로그램 | `net`·`schtasks` 등 출력 = OEM 코드페이지 | 문자열 비교·정규식으로 판정 X → cmdlet 객체·SID 로 판정 |

- Windows 그룹은 표시 이름(Administrators·관리자) 말고 **SID** 로 확인 (`S-1-5-32-544` 관리자 · `S-1-5-32-545` 사용자). 조회 실패는 성공이 아니라 실패로 기록.
- 검증: PS 5.1 `Parser.ParseFile` 로 한글 문자열 보존 여부를 BOM 유무별로 확인 (`test_phase20_v10_safety.py` 회귀).
