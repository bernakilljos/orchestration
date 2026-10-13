#!/usr/bin/env python3
"""
suggest-build-deploy.py — 감지된 언어별 빌드·배포 명령 매트릭스 생성
SessionStart hook 이 detect-project-language.json 읽은 후 이 스크립트 실행
결과는 systemMessage 로 Claude 에게 주입 가능
"""

import json
import os
from pathlib import Path

def load_project_language():
    """project-language.json 로드"""
    state_file = Path.home() / ".claude" / "projects" / "C--pjt-orchestration-v1" / ".claude" / "state" / "project-language.json"

    # local fallback
    if not state_file.exists():
        state_file = Path(".claude/state/project-language.json")

    if not state_file.exists():
        return {"language": "unknown", "build_tool": "", "deploy_format": ""}

    try:
        with open(state_file) as f:
            return json.load(f)
    except:
        return {"language": "unknown", "build_tool": "", "deploy_format": ""}

# 빌드·배포 매트릭스
BUILD_DEPLOY_MATRIX = {
    "java": {
        "maven": {
            "build": "mvn clean package",
            "test": "mvn test",
            "package": "mvn assembly:assembly",
            "publish": "mvn deploy -DrepositoryId=central",
            "formats": [".jar", ".war", ".ear"],
            "notes": "pom.xml 확인 · assembly plugin 설정"
        },
        "gradle": {
            "build": "gradle build",
            "test": "gradle test",
            "package": "gradle jar",
            "publish": "gradle publish",
            "formats": [".jar", ".war", ".aar"],
            "notes": "build.gradle 또는 build.gradle.kts 확인"
        }
    },
    "csharp": {
        "dotnet": {
            "build": "dotnet build",
            "test": "dotnet test",
            "package": "dotnet pack",
            "publish": "dotnet publish -c Release",
            "formats": [".dll", ".nupkg", ".exe"],
            "notes": "*.csproj 또는 .sln 대상 · net6.0+ LTS 권장"
        }
    },
    "rust": {
        "cargo": {
            "build": "cargo build --release",
            "test": "cargo test",
            "package": "cargo package",
            "publish": "cargo publish",
            "formats": ["binary", ".rlib", ".so"],
            "notes": "Cargo.toml 확인 · target/release/ 생성"
        }
    },
    "go": {
        "go": {
            "build": "go build ./...",
            "test": "go test ./...",
            "package": "go build -o ./bin/<name>",
            "publish": "go install",
            "formats": ["binary", ".so"],
            "notes": "go.mod 확인 · go 1.22+ 권장"
        }
    },
    "python": {
        "uv": {
            "build": "uv build",
            "test": "uv run pytest",
            "package": "uv build --wheel",
            "publish": "uv publish",
            "formats": [".whl", ".tar.gz"],
            "notes": "pyproject.toml 확인 · pip 대체로 10x 빠름"
        },
        "pip": {
            "build": "python -m build",
            "test": "pytest",
            "package": "python -m build --wheel",
            "publish": "python -m twine upload dist/*",
            "formats": [".whl", ".tar.gz"],
            "notes": "setup.py 또는 pyproject.toml · Python 3.9+"
        }
    },
    "javascript": {
        "npm": {
            "build": "npm run build",
            "test": "npm test",
            "package": "npm pack",
            "publish": "npm publish",
            "formats": ["npm package", ".tgz"],
            "notes": "package.json 확인 · node 18+ LTS"
        },
        "pnpm": {
            "build": "pnpm build",
            "test": "pnpm test",
            "package": "pnpm pack",
            "publish": "pnpm publish",
            "formats": ["npm package", ".tgz"],
            "notes": "pnpm-lock.yaml 확인 · npm 대비 10% 빠름"
        },
        "yarn": {
            "build": "yarn build",
            "test": "yarn test",
            "package": "yarn pack",
            "publish": "yarn publish",
            "formats": ["npm package", ".tgz"],
            "notes": "yarn.lock 확인 · yarn 4.x berry 권장"
        }
    },
    "ruby": {
        "bundler": {
            "build": "bundle exec rake build",
            "test": "bundle exec rspec",
            "package": "gem build *.gemspec",
            "publish": "gem push *.gem",
            "formats": [".gem"],
            "notes": "Gemfile 확인 · ruby 3.0+"
        }
    },
    "dart": {
        "flutter": {
            "build": "flutter build apk",  # Android default
            "test": "flutter test",
            "package": "flutter pub publish",
            "publish": "flutter pub publish",
            "formats": [".apk", ".ipa", ".aab"],
            "notes": "pubspec.yaml 확인 · Flutter 3.0+"
        },
        "pub": {
            "build": "dart compile exe lib/main.dart",
            "test": "dart test",
            "package": "dart pub get",
            "publish": "dart pub publish",
            "formats": [".exe", ".snap"],
            "notes": "pubspec.yaml 확인 · Dart CLI"
        }
    },
    "unknown": {}
}

def generate_system_message():
    """systemMessage 형식으로 빌드·배포 가이드 생성"""
    project_lang = load_project_language()
    lang = project_lang.get("language", "unknown")
    build_tool = project_lang.get("build_tool", "")

    if lang == "unknown":
        return "## Project Language Detection\n\n❌ 감지 실패: 지원 빌드 파일 (pom.xml/build.gradle/Cargo.toml/go.mod/pyproject.toml/package.json 등) 없음. 경로 재확인."

    message = f"## 감지된 프로젝트 언어: {lang.upper()} · {build_tool}\n\n"

    if lang not in BUILD_DEPLOY_MATRIX:
        message += f"⚠ {lang} 은 아직 매트릭스 미지원.\n"
        return message

    lang_matrix = BUILD_DEPLOY_MATRIX[lang]

    if not lang_matrix:
        return message

    # 첫 번째 빌드 도구 (primary)
    primary_tool = next(iter(lang_matrix.keys()))
    commands = lang_matrix[primary_tool]

    message += f"### {primary_tool.upper()} 명령\n\n"
    message += f"| 작업 | 명령 |\n"
    message += f"|-----|------|\n"
    message += f"| build | `{commands.get('build', 'N/A')}` |\n"
    message += f"| test | `{commands.get('test', 'N/A')}` |\n"
    message += f"| package | `{commands.get('package', 'N/A')}` |\n"
    message += f"| publish | `{commands.get('publish', 'N/A')}` |\n\n"

    message += f"**배포 포맷**: {', '.join(commands.get('formats', []))}\n\n"
    message += f"**주의**: {commands.get('notes', 'N/A')}\n\n"

    # 대체 도구 (if any)
    if len(lang_matrix) > 1:
        message += f"### 대체 도구\n\n"
        for alt_tool in list(lang_matrix.keys())[1:]:
            message += f"- **{alt_tool}**: `{lang_matrix[alt_tool].get('build', 'N/A')}`\n"

    return message

def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # JSON 출력
        project_lang = load_project_language()
        lang = project_lang.get("language", "unknown")

        if lang in BUILD_DEPLOY_MATRIX:
            print(json.dumps(BUILD_DEPLOY_MATRIX[lang], indent=2))
        else:
            print("{}")
    else:
        # systemMessage 형식
        print(generate_system_message())

if __name__ == "__main__":
    main()
