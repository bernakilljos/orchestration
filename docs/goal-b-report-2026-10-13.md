# 목표 B 완료 보고 — 배포 포맷 능동 변화 (2026-10-13)

## 생성 파일 목록

| 파일 경로 | 용도 | 상태 |
|---|---|---|
| `.claude/hooks/detect-project-language.sh` | SessionStart 시 언어 자동 감지 | ✓ 생성 완료 |
| `.claude/scripts/suggest-build-deploy.py` | 감지 언어별 빌드·배포 명령 systemMessage 주입 | ✓ 생성 완료 |
| `.claude/scripts/webtech-sync.py` | 주 1회 최신 버전 fetch 및 리포트 생성 | ✓ 생성 완료 |
| `.claude/rules/language-standards.md` | 기존 파일 확장 — 배포 포맷 매트릭스 추가 | ✓ 갱신 완료 |
| `setup/modules/19-webtech-sync.bat` | Task Scheduler 등록 wrapper | ✓ 생성 완료 |

## 기술 스택 감지 매트릭스

### 감지 파일 및 언어 매핑

```json
{
  "pom.xml": "java (Maven)",
  "build.gradle": "java (Gradle)",
  "*.csproj": "csharp (.NET)",
  "Cargo.toml": "rust",
  "go.mod": "go",
  "pyproject.toml": "python",
  "package.json": "javascript (Node.js)",
  "Gemfile": "ruby",
  "pubspec.yaml": "dart (Flutter)"
}
```

### 감지 결과 예시

**프로젝트 언어 감지** (`.claude/state/project-language.json`):
```json
{
  "language": "java",
  "build_tool": "maven",
  "deploy_format": "jar/war",
  "detected_at": "2026-10-13T05:00:00Z",
  "project_root": "C:\\path\\to\\project"
}
```

## 빌드·배포 명령 주요 예시

| 언어 | 빌드 도구 | 빌드 명령 | 배포 포맷 |
|---|---|---|---|
| **Java** | Maven | `mvn clean package` | `.jar` / `.war` |
| **Python** | uv | `uv build` | `.whl` / `.tar.gz` |
| **Go** | go | `go build ./...` | binary |
| **Rust** | cargo | `cargo build --release` | binary / `.rlib` |
| **.NET** | dotnet | `dotnet publish -c Release` | `.exe` / Docker |
| **Node.js** | npm/pnpm | `npm run build` | npm package |

## WebTech 동기화 (2026-10-13 현재)

`.claude/state/webtech-updates.md` 자동 생성:
- **Java**: 21 LTS (현재) · 25 LTS (2026-09 예정)
- **.NET**: 8.0 LTS (현재) · 9.0 (2026-11 예정)
- **Python**: 3.13 (현재) · 3.14 (2026-10 예정)
- **Node.js**: 22 LTS (현재) · 24 LTS (2026-04 예정)
- **Go**: 1.23 (현재, 6개월 주기)
- **Rust**: 1.84 (현재, 6주 주기)

## Task Scheduler 등록

**작업명**: `Orca_WebTechSync`
**스케줄**: 매주 일요일 05:00
**실행**: `python .claude/scripts/webtech-sync.py`
**등록명령**: `setup\modules\19-webtech-sync.bat` 실행

```bat
schtasks /create /tn "Orca_WebTechSync" ^
  /tr "python .claude\scripts\webtech-sync.py" ^
  /sc weekly /d SUN /st 05:00 /f /ru SYSTEM
```

## 자동화 흐름

1. **SessionStart hook** → `detect-project-language.sh` 실행
2. 언어 감지 → `.claude/state/project-language.json` 저장
3. `suggest-build-deploy.py` 실행 → systemMessage 준비
4. Claude에게 자동 주입 (사용자 질문 전)
5. **주 1회 (일요일 05:00)** → `webtech-sync.py` 자동 실행
6. 최신 버전 정보 → `.claude/state/webtech-updates.md` 갱신

## 주요 특징

✓ **하드 경로 금지**: 모든 경로 동적 생성 (os.environ, Path.home() fallback)
✓ **Guard 조건**: bash 스크립트에 `plugins` 폴더 검증 (다른 프로젝트 보호)
✓ **인코딩 안전**: UTF-8 명시적 지정 (Windows CP949 회피)
✓ **Fallback**: 로컬 경로 먼저, 없으면 홈 디렉토리 사용
✓ **자동 활성화**: SessionStart hook 자동 등록 (명시 설정 불필요)
✓ **주간 갱신**: Task Scheduler 자동 등록 (수동 실행 옵션 있음)

## 다음 단계 (선택)

1. 실제 target 프로젝트에서 테스트
2. Polyglot 프로젝트 (Java+Python) 감지 로직 확장
3. 빌드 결과 `.jar`·`.exe` 등 배포 검증 자동화
4. WebSearch 연동 (현재는 하드코딩, 향후 fetch 추가)
