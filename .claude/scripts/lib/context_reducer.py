"""
context_reducer.py ?????뚯씪???붿빟 ?뺥깭濡?異뺤냼.

24?쒓컙 ?몄뀡?먯꽌 ?꾩껜 ?꾨줈?앺듃 而⑦뀓?ㅽ듃 留ㅻ쾲 濡쒕뱶????퉬.
Markdown-Python ?뚯씪??二쇱슂 援ъ“留??좎??섎㈃??異뺤냼.
"""

import re
from pathlib import Path
from typing import Optional


def reduce_markdown(path: str, max_chars: int = 8000) -> str:
    """
    Markdown ?뚯씪??max_chars ?댄븯濡?異뺤냼.

    ?꾨왂:
      1. frontmatter (---...---) ?좎?
      2. ?ㅻ뵫 (## ~ #####) ?꾨? ?좎?
      3. 肄붾뱶 釉붾줉 以?湲?嫄?"... N以??앸왂 ..." 留덉빱濡??붿빟
      4. ?쒕뒗 ?좎?
      5. ?쇰컲 ?띿뒪???⑤씫? 泥?以꾨쭔 ?좎? + "..."

    ?먮낯???대? max_chars ?댄븯硫?洹몃?濡?諛섑솚.

    Args:
        path: ?뚯씪 寃쎈줈
        max_chars: 紐⑺몴 ?ш린

    Returns:
        異뺤냼???띿뒪??
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
        # Frontmatter 泥섎━
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            frontmatter.append(line)
            continue
        if in_frontmatter:
            frontmatter.append(line)
            if line.strip() == "---" and i > 0:
                in_frontmatter = False
            continue

        # 肄붾뱶 釉붾줉 泥섎━
        if line.strip().startswith("```"):
            if in_code_block:
                # 釉붾줉 醫낅즺
                if len(code_block_lines) > 10:
                    result.append(code_block_lines[0])  # 泥?以?(?몄뼱 吏??
                    result.append(f"  ... ({len(code_block_lines) - 2} 以??앸왂) ...")
                    result.append(code_block_lines[-1])  # 醫낅즺 諛깊떛
                else:
                    result.extend(code_block_lines)
                in_code_block = False
                code_block_lines = []
            else:
                # 釉붾줉 ?쒖옉
                in_code_block = True
                code_block_lines = [line]
            continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        # ?ㅻ뵫 (## ~ #####)
        if re.match(r"^#{2,5}\s", line):
            result.append(line)
            continue

        # ??(| 濡??쒖옉)
        if line.strip().startswith("|"):
            result.append(line)
            continue

        # ?쇰컲 ?띿뒪???⑤씫 異뺤냼
        if line.strip() and not line.startswith("#"):
            # 泥?以꾨쭔 ?좎?
            if result and result[-1] != "":
                # ?곗냽 鍮?以??꾨떂
                result.append(line[:100] + ("..." if len(line) > 100 else ""))
            else:
                result.append(line[:100] + ("..." if len(line) > 100 else ""))
        else:
            # 鍮?以??좎? (援щ텇??
            if not result or result[-1] != "":
                result.append("")

    # Frontmatter ?욎뿉 遺숈엫
    final = "\n".join(frontmatter) + "\n" + "\n".join(result)

    # ?ъ쟾??max_chars ?섏쑝硫??앸????먮Ⅴ湲?
    if len(final) > max_chars:
        final = final[:max_chars] + "\n... (truncated)"

    return final


def reduce_python(path: str, max_chars: int = 6000) -> str:
    """
    Python ?뚯씪??API + docstring 堉덈?濡?異뺤냼.

    - import ?좎?
    - class/def ?쒓렇?덉쿂 + docstring ?좎?
    - ?⑥닔 蹂몃Ц? "..." 濡??泥?(?? 5以??댄븯???좎?)

    Args:
        path: ?뚯씪 寃쎈줈
        max_chars: 紐⑺몴 ?ш린

    Returns:
        異뺤냼??肄붾뱶
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

        # import ?쇱씤 ?좎?
        if line.strip().startswith(("import ", "from ")):
            result.append(line)
            i += 1
            continue

        # class ?뺤쓽 ?좎?
        if re.match(r"^class\s+\w+", line):
            result.append(line)
            i += 1
            # docstring 李얘린
            while i < len(lines) and lines[i].strip().startswith(('"""', "'''", "#")):
                result.append(lines[i])
                i += 1
            continue

        # def ?뺤쓽 ?좎?
        if re.match(r"^\s*def\s+\w+", line):
            result.append(line)
            i += 1
            # docstring + 泥?5以??좎?
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

    # ?ъ쟾???섏쑝硫??먮Ⅴ湲?
    if len(final) > max_chars:
        final = final[:max_chars] + "\n# ... (truncated)"

    return final


def build_project_summary(root: str, max_total_chars: int = 30000) -> str:
    """
    ?꾨줈?앺듃 猷⑦듃?먯꽌 二쇱슂 ?뚯씪?ㅼ쓣 異뺤냼-?⑹꽦???붿빟 諛섑솚.

    ?ы븿 ???(?곗꽑?쒖쐞):
      1. CLAUDE.md (?꾩껜 ?좎?)
      2. README.md (異뺤냼 媛??
      3. .claude/rules/*.md (?꾩껜, ?대? 吏㏃쓬)
      4. plugins/*/plugin.json (?대쫫-display-status留?異붿텧)
      5. docs/architecture-patterns.md (異뺤냼)

    max_total_chars ?섏쑝硫?lower priority ?뱀뀡遺???먮쫫.

    Args:
        root: ?꾨줈?앺듃 猷⑦듃 寃쎈줈
        max_total_chars: 理쒕? ?⑹꽦 ?ш린

    Returns:
        ?붿빟 ?띿뒪??
    """
    root_path = Path(root)
    sections = []

    # 1. CLAUDE.md (?꾩껜)
    claude_md = root_path / "CLAUDE.md"
    if claude_md.exists():
        try:
            content = claude_md.read_text(encoding="utf-8")
            sections.append(("CLAUDE.md", content, 1))
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            pass

    # 2. README.md (異뺤냼)
    readme = root_path / "README.md"
    if readme.exists():
        sections.append(("README.md", reduce_markdown(str(readme), max_chars=3000), 2))

    # 3. .claude/rules/*.md (?꾩껜)
    rules_dir = root_path / ".claude" / "rules"
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.md")):
            try:
                content = rule_file.read_text(encoding="utf-8")
                sections.append((f"rules/{rule_file.name}", content, 3))
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                pass

    # 4. plugins/*/plugin.json (異뺤냼)
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
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                    pass
        if plugin_summary != "# Plugin Summary\n\n":
            sections.append(("plugins/summary", plugin_summary, 4))

    # 5. docs/architecture-patterns.md (異뺤냼)
    arch_patterns = root_path / "docs" / "architecture-patterns.md"
    if arch_patterns.exists():
        sections.append(
            (
                "architecture-patterns.md",
                reduce_markdown(str(arch_patterns), max_chars=4000),
                5,
            )
        )

    # ?곗꽑?쒖쐞 ?뺣젹 (??? priority 踰덊샇媛 ?믪? ?곗꽑?쒖쐞)
    sections.sort(key=lambda x: x[2])

    # ?ш린 ?쒖빟 ?댁뿉???뱀뀡 異뺤쟻
    result = "# Project Summary\n\n"
    current_size = len(result)

    for name, content, _ in sections:
        section = f"\n## {name}\n\n{content}\n"
        if current_size + len(section) <= max_total_chars:
            result += section
            current_size += len(section)
        else:
            # ?⑥? 怨듦컙???ㅻ뜑留뚯씠?쇰룄
            if current_size + 50 <= max_total_chars:
                result += f"\n## {name}\n(truncated - no space)\n"
            break

    if current_size < max_total_chars:
        result += f"\n\n---\nTotal size: {current_size} / {max_total_chars} chars\n"

    return result


if __name__ == "__main__":
    # ?뚯뒪??
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if file_path.endswith(".md"):
            print(reduce_markdown(file_path))
        elif file_path.endswith(".py"):
            print(reduce_python(file_path))
    else:
        # ?꾨줈?앺듃 ?붿빟 ?앹꽦
        summary = build_project_summary(".")
        print(summary)

