# 개발 언어별 표준 룰 (Language Standards)

> **근거**: 2026-09-02 사용자 지적 — "개발언어에 따라서 처리".
> **이유**: 언어별 lint·format·test·구조 표준 자동 적용 · 아마추어 코드 X.

## 절대 룰

**언어 감지 → 언어별 표준 자동 적용 (lint·format·test 규칙 · 파일 구조).**

## 언어별 매트릭스

| 언어 | Linter | Formatter | Test | Type | 패키지 관리 | 파일 확장자 |
|---|---|---|---|---|---|---|
| **Python** | **ruff** (rustic·빠름) + mypy | **ruff format** (black 대체·빠름) | pytest + coverage | mypy strict | uv·pip | `.py` |
| **JavaScript** | **ESLint 9** + eslint-config-standard | **Prettier** | vitest · jest | JSDoc | pnpm·npm | `.js` `.mjs` |
| **TypeScript** | **ESLint 9** + typescript-eslint | **Prettier** | vitest | tsc strict | pnpm | `.ts` `.tsx` |
| **Java** | **Checkstyle** + SpotBugs + PMD | google-java-format | JUnit 5 + Mockito | 기본 | maven·gradle | `.java` |
| **Kotlin** | **detekt** | ktlint | JUnit 5 | 기본 | gradle | `.kt` |
| **Go** | **golangci-lint** | gofmt · gofumpt | go test | 기본 | go modules | `.go` |
| **Rust** | **clippy** | rustfmt | cargo test | 기본 | cargo | `.rs` |
| **C/C++** | clang-tidy | clang-format | GoogleTest · Catch2 | 기본 | CMake·Conan | `.c` `.cpp` `.h` |
| **C#** | **Roslyn analyzers** | dotnet format | xUnit · NUnit | 기본 | NuGet | `.cs` |
| **Ruby** | **RuboCop** | RuboCop | RSpec · Minitest | Sorbet | Bundler | `.rb` |
| **PHP** | **PHPStan** + PHP_CodeSniffer | php-cs-fixer | PHPUnit · Pest | 기본 | Composer | `.php` |
| **Swift** | SwiftLint | swift-format | XCTest | 기본 | SPM | `.swift` |
| **Dart/Flutter** | dart analyze | dart format | flutter test | 기본 | pub | `.dart` |
| **Scala** | Scalafix | Scalafmt | ScalaTest · MUnit | 기본 | sbt | `.scala` |
| **Elixir** | Credo | mix format | ExUnit | Dialyxir | mix | `.ex` `.exs` |
| **Haskell** | HLint | ormolu · fourmolu | Hspec | GHC | cabal · stack | `.hs` |
| **Zig** | zig fmt | zig fmt | zig test | 기본 | zig | `.zig` |
| **SQL** | sqlfluff | sqlfluff | tSQLt · pgTAP | 기본 | flyway·alembic | `.sql` |
| **Shell (bash)** | shellcheck | shfmt | bats | 기본 | apt·brew | `.sh` |
| **PowerShell** | PSScriptAnalyzer | Invoke-Formatter | Pester | 기본 | PSGallery | `.ps1` |

## 프로젝트 구조 표준

| 언어 | 필수 파일 |
|---|---|
| Python | `pyproject.toml` (ruff+mypy 설정) · `requirements.txt` or `uv.lock` · `.python-version` |
| Node.js | `package.json` · `pnpm-lock.yaml`·`.nvmrc` · `.eslintrc.json` · `.prettierrc` · `tsconfig.json` (TS 시) |
| Go | `go.mod` · `go.sum` · `.golangci.yml` |
| Rust | `Cargo.toml` · `Cargo.lock` · `rust-toolchain.toml` |
| Java | `pom.xml` (Maven) or `build.gradle` (Gradle) · `.editorconfig` |
| SQL | `migrations/` (Alembic·Flyway·Prisma) |

## 자동 hook 확장 (PostToolUse Edit|Write)

우리 kit 이미 있음:
- Python: `post_write_pycheck.py` (syntax check)

신규 (예정):
- **JS/TS**: `check-js-syntax.sh` (기존 확장 · eslint·prettier 실행)
- **Go**: `.claude/hooks/check-go-fmt.sh` (gofmt 자동)
- **Rust**: `.claude/hooks/check-rust-fmt.sh` (rustfmt 자동)
- **Java**: `.claude/hooks/check-java-fmt.sh` (google-java-format)
- **SQL**: `.claude/hooks/check-sql-lint.sh` (sqlfluff)
- **Shell**: 이미 shellcheck 하는 hook 있음

## 언어 감지 로직

파일 확장자 기준:
```python
LANG_MAP = {
    '.py': 'python', '.pyi': 'python',
    '.js': 'js', '.mjs': 'js', '.cjs': 'js', '.jsx': 'js',
    '.ts': 'ts', '.tsx': 'ts',
    '.java': 'java',
    '.kt': 'kotlin', '.kts': 'kotlin',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.dart': 'dart',
    '.scala': 'scala',
    '.sql': 'sql',
    '.sh': 'bash', '.bash': 'bash',
    '.ps1': 'powershell',
    '.c': 'c', '.cpp': 'cpp', '.h': 'c', '.hpp': 'cpp',
    '.cs': 'csharp',
    '.ex': 'elixir', '.exs': 'elixir',
    '.hs': 'haskell',
    '.zig': 'zig',
}
```

## 언어별 특화 룰

### Python
- **ruff 우선**: `ruff check` + `ruff format` (black 대체 · 10~100x 빠름)
- **mypy strict**: `--strict` 모드
- **uv 우선**: pip 대체 (10x 빠름 · 2024 최신)
- `pyproject.toml` 표준
- 함수 · 클래스 docstring (Google style)
- Type hint 필수

### TypeScript
- **strict mode** 필수
- **ES2024+** target
- Never use `any` · `unknown` 필수
- ESLint 9 flat config (`eslint.config.js`)

### Go
- **표준 layout**: `cmd/·internal/·pkg/`
- Error handling 명시 (`if err != nil`)
- Go 1.22+ (range over int·slices)

### Rust
- **Edition 2024**
- `clippy::pedantic` 활용
- `unsafe` 최소화 · 사유 명시

### Java
- **Java 21 LTS** default
- Records·Sealed classes 활용
- Spring Boot 3+ (Java 17+)

## 금지

1. **언어 감지 없이 lint·format X**
2. **한 프로젝트에 여러 formatter 설정 X** (혼란)
3. **버전 오래된 도구 X** (Python 3.8 이하·Node 18 이하·Java 8 등)
4. **CI 없이 lint 요구 X** (자동 hook 활용)
5. **표준 무시 · 자체 스타일 X** (팀 확장성)

## 관련

- `.claude/hooks/check-*.sh` (언어별 자동 hook)
- `.claude/rules/indentation.md` (들여쓰기 표준)
- `.claude/rules/file-naming.md` (파일 명명)
- `.claude/rules/production-file-management.md` (2026-09-02)
