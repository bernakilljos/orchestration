"""
context_reducer.py — 큰 파일을 요약 형태로 축소.

24시간 세션에서 전체 프로젝트 컨텍스트 매번 로드는 낭비.
Markdown·Python 파일을 주요 구조만 유지하면서 축소.
"""

import re
from pathlib import Path
from typing import Optional


def reduce_markdown(path: str, max_chars: int = 8000) -> str:
    """
    Markdown 파일을 max_chars 이하로 축소.

    전략:
      1. frontmatter (---...---) 유지
      2. 헤딩 (## ~ #####) 전부 유지
      3. 코드 블록 중 긴 건 "... N줄 생략 ..." 마커로 요약
      4. 표는 유지
      5. 일반 텍스트 단락은 첫 줄만 유지 + "..."

    원본이 이미 max_chars 이하면 그대로 반환.

    Args:
        path: 파일 경로
        max_chars: 목표 크기

    Returns:
        축소된 텍스트
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
    except (FileNotFoundError, IOError) as e:
        return f"# Error: {path}\nFailed to read: {e}\n"

    if len(content) <= max_chars:
        return content

    lines = content.split("\n")
    result = []
    in_code_block = False
    code_block_lines = []
    in_frontmatter = False
    frontmatter = []

    for i, line in enumerate(lines):
        # Frontmatter 처리
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            frontmatter.append(line)
            continue
        if in_frontmatter:
            frontmatter.append(line)
            if line.strip() == "---" and i > 0:
                in_frontmatter = False
            continue

        # 코드 블록 처리
        if line.strip().startswith("```"):
            if in_code_block:
                # 블록 종료
                if len(code_block_lines) > 10:
                    result.append(code_block_lines[0])  # 첫 줄 (언어 지정)
                    result.append(f"  ... ({len(code_block_lines) - 2} 줄 생략) ...")
                    result.append(code_block_lines[-1])  # 종료 백틱
                else:
                    result.extend(code_block_lines)
                in_code_block = False
                code_block_lines = []
            else:
                # 블록 시작
                in_code_block = True
                code_block_lines = [line]
            continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        # 헤딩 (## ~ #####)
        if re.match(r"^#{2,5}\s", line):
            result.append(line)
            continue

        # 표 (| 로 시작)
        if line.strip().startswith("|"):
            result.append(line)
            continue

        # 일반 텍스트 단락 축소
        if line.strip() and not line.startswith("#"):
            # 첫 줄만 유지
            if result and result[-1] != "":
                # 연속 빈 줄 아님
                result.append(line[:100] + ("..." if len(line) > 100 else ""))
            else:
                result.append(line[:100] + ("..." if len(line) > 100 else ""))
        else:
            # 빈 줄 유지 (구분용)
            if not result or result[-1] != "":
                result.append("")

    # Frontmatter 앞에 붙임
    final = "\n".join(frontmatter) + "\n" + "\n".join(result)

    # 여전히 max_chars 넘으면 끝부터 자르기
    if len(final) > max_chars:
        final = final[:max_chars] + "\n... (truncated)"

    return final


def reduce_python(path: str, max_chars: int = 6000) -> str:
    """
    Python 파일을 API + docstring 뼈대로 축소.

    - import 유지
    - class/def 시그니처 + docstring 유지
    - 함수 본문은 "..." 로 대체 (단, 5줄 이하는 유지)

    Args:
        path: 파일 경로
        max_chars: 목표 크기

    Returns:
        축소된 코드
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
    except (FileNotFoundError, IOError) as e:
        return f"# Error: {path}\n# Failed to read: {e}\n"

    if len(content) <= max_chars:
        return content

    lines = content.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # import 라인 유지
        if line.strip().startswith(("import ", "from ")):
            result.append(line)
            i += 1
            continue

        # class 정의 유지
        if re.match(r"^class\s+\w+", line):
            result.append(line)
            i += 1
            # docstring 찾기
            while i < len(lines) and lines[i].strip().startswith(('"""', "'''", "#")):
                result.append(lines[i])
                i += 1
            continue

        # def 정의 유지
        if re.match(r"^\s*def\s+\w+", line):
            result.append(line)
            i += 1
            # docstring + 첫 5줄 유지
            docstring_lines = 0
            body_lines = 0
            in_docstring = False
            while i < len(lines) and (docstring_lines < 10 or body_lines < 5):
                next_line = lines[i]
                if '"""' in next_line or "'''" in next_line:
                    in_docstring = not in_docstring
                    result.append(next_line)
                    docstring_lines += 1
                elif in_docstring:
                    result.append(next_line)
                    docstring_lines += 1
                elif next_line.strip() and not next_line.strip().startswith("#"):
                    result.append(next_line)
                    body_lines += 1
                    if body_lines >= 5:
                        result.append("        ...")
                        break
                else:
                    result.append(next_line)
                i += 1
            continue

        i += 1

    final = "\n".join(result)

    # 여전히 넘으면 자르기
    if len(final) > max_chars:
        final = final[:max_chars] + "\n# ... (truncated)"

    return final


def build_project_summary(root: str, max_total_chars: int = 30000) -> str:
    """
    프로젝트 루트에서 주요 파일들을 축소·합성한 요약 반환.

    포함 대상 (우선순위):
      1. CLAUDE.md (전체 유지)
      2. README.md (축소 가능)
      3. .claude/rules/*.md (전체, 이미 짧음)
      4. plugins/*/plugin.json (이름·display·status만 추출)
      5. docs/architecture-patterns.md (축소)

    max_total_chars 넘으면 lower priority 섹션부터 자름.

    Args:
        root: 프로젝트 루트 경로
        max_total_chars: 최대 합성 크기

    Returns:
        요약 텍스트
    """
    root_path = Path(root)
    sections = []

    # 1. CLAUDE.md (전체)
    claude_md = root_path / "CLAUDE.md"
    if claude_md.exists():
        try:
            content = claude_md.read_text(encoding="utf-8")
            sections.append(("CLAUDE.md", content, 1))
        except Exception:
            pass

    # 2. README.md (축소)
    readme = root_path / "README.md"
    if readme.exists():
        sections.append(("README.md", reduce_markdown(str(readme), max_chars=3000), 2))

    # 3. .claude/rules/*.md (전체)
    rules_dir = root_path / ".claude" / "rules"
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.md")):
            try:
                content = rule_file.read_text(encoding="utf-8")
                sections.append((f"rules/{rule_file.name}", content, 3))
            except Exception:
                pass

    # 4. plugins/*/plugin.json (축소)
    plugins_dir = root_path / "plugins"
    if plugins_dir.exists():
        plugin_summary = "# Plugin Summary\n\n"
        for plugin_dir in sorted(plugins_dir.glob("*")):
            if not plugin_dir.is_dir():
                continue
            plugin_json = plugin_dir / "plugin.json"
            if plugin_json.exists():
                try:
                    import json

                    data = json.loads(plugin_json.read_text(encoding="utf-8"))
                    plugin_summary += (
                        f"- **{data.get('name', plugin_dir.name)}**: "
                        f"{data.get('display', '(no display)')} "
                        f"(status: {data.get('status', 'unknown')})\n"
                    )
                except Exception:
                    pass
        if plugin_summary != "# Plugin Summary\n\n":
            sections.append(("plugins/summary", plugin_summary, 4))

    # 5. docs/architecture-patterns.md (축소)
    arch_patterns = root_path / "docs" / "architecture-patterns.md"
    if arch_patterns.exists():
        sections.append(
            (
                "architecture-patterns.md",
                reduce_markdown(str(arch_patterns), max_chars=4000),
                5,
            )
        )

    # 우선순위 정렬 (낮은 priority 번호가 높은 우선순위)
    sections.sort(key=lambda x: x[2])

    # 크기 제약 내에서 섹션 축적
    result = "# Project Summary\n\n"
    current_size = len(result)

    for name, content, _ in sections:
        section = f"\n## {name}\n\n{content}\n"
        if current_size + len(section) <= max_total_chars:
            result += section
            current_size += len(section)
        else:
            # 남은 공간에 헤더만이라도
            if current_size + 50 <= max_total_chars:
                result += f"\n## {name}\n(truncated - no space)\n"
            break

    if current_size < max_total_chars:
        result += f"\n\n---\nTotal size: {current_size} / {max_total_chars} chars\n"

    return result


if __name__ == "__main__":
    # 테스트
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if file_path.endswith(".md"):
            print(reduce_markdown(file_path))
        elif file_path.endswith(".py"):
            print(reduce_python(file_path))
    else:
        # 프로젝트 요약 생성
        summary = build_project_summary(".")
        print(summary)
