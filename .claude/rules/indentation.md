# 들여쓰기 규칙

## JSON (plugin.json, settings.json, marketplace.json)
- **2 스페이스** 고정
- 키 순서: 스키마 정의 순서 유지 (필수 먼저)

## Markdown (.md)
- 리스트·중첩: **2 스페이스**
- 코드 블록 내부: 원본 언어 규칙 따름
- frontmatter YAML: **2 스페이스**

## Python (.py)
- PEP 8 — **4 스페이스**
- 타입 힌트 권장

## Bash (.sh)
- **2 스페이스** (가독성)
- 구조:
  ```bash
  if [ "$x" = "y" ]; then
    do_something
  fi
  ```

## Windows Batch (.bat)
- **2 스페이스** 또는 탭 (일관성 유지)

## YAML (frontmatter)
- **2 스페이스**
- 문자열은 큰따옴표 (한글·특수문자 안전)

## 금지
- 탭/스페이스 혼용
- 파일 간 들여쓰기 섞이면 `sed -i 's/\t/  /g'` 로 일괄 통일 후 커밋
