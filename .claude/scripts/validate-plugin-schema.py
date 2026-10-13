#!/usr/bin/env python3
"""
plugin.json ?ㅽ궎留?寃利????꾩닔 ?꾨뱶-???prefix ?쇱튂-?섏〈 李몄“ ?좏슚???뺤씤.

?ъ슜踰?
  python .claude/scripts/validate-plugin-schema.py              ?꾩껜 寃利?
  python .claude/scripts/validate-plugin-schema.py <plugin>     ?⑥씪 寃利?
  python .claude/scripts/validate-plugin-schema.py --strict     寃쎄퀬???ㅽ뙣濡?

exit 0 = OK, 1 = error, 2 = warning
"""
import json, sys, re
from pathlib import Path

# Windows cp949 ???
try:
    sys.stdout.reconfigure(encoding='utf-8')
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    pass

REQUIRED = ["name", "display", "prefix", "version", "status", "phase"]
STATUSES = {"stable", "experimental", "spec-only", "deprecated"}
PREFIX_RE = re.compile(r"^[a-z][a-z0-9]*_$")
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")

errors = []
warnings = []
plugins_dir = Path("plugins")

target = None
strict = False
for arg in sys.argv[1:]:
    if arg == "--strict":
        strict = True
    elif not arg.startswith("-"):
        target = arg

# ?꾩껜 ?뚮윭洹몄씤 紐⑸줉 (?섏〈 李몄“ ?좏슚??泥댄겕??
all_plugins = {p.name for p in plugins_dir.iterdir() if p.is_dir() and not p.name.startswith("_")}

def validate(plugin_name):
    p = plugins_dir / plugin_name / "plugin.json"
    if not p.exists():
        errors.append(f"{plugin_name}: plugin.json ?놁쓬")
        return

    try:
        pj = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"{plugin_name}: JSON ?뚯떛 ?ㅽ뙣 ??{e}")
        return

    # ?꾩닔 ?꾨뱶
    for f in REQUIRED:
        if f not in pj:
            errors.append(f"{plugin_name}: ?꾩닔 ?꾨뱶 ?꾨씫 ??{f}")

    # name ?쇱튂
    if pj.get("name") != plugin_name:
        errors.append(f"{plugin_name}: name ?꾨뱶({pj.get('name')}) != ?붾젆?좊━紐?)

    # name ?⑦꽩
    name = pj.get("name", "")
    if name and not NAME_RE.match(name):
        errors.append(f"{plugin_name}: name ?⑦꽩 ?꾨컲 ({name}) ???뚮Ц???レ옄+?몃뜑?ㅼ퐫??)

    # prefix ?⑦꽩
    prefix = pj.get("prefix", "")
    if prefix and not PREFIX_RE.match(prefix):
        errors.append(f"{plugin_name}: prefix ?⑦꽩 ?꾨컲 ({prefix}) ??xxx_ ?뺥깭")

    # prefix ??name ?쇱튂 (name??prefix濡??쒖옉?댁빞)
    if prefix and name and not name.startswith(prefix):
        warnings.append(f"{plugin_name}: name({name})??prefix({prefix})濡??쒖옉 ????)

    # version ?⑦꽩
    ver = pj.get("version", "")
    if ver and not VERSION_RE.match(ver):
        errors.append(f"{plugin_name}: version ?⑦꽩 ?꾨컲 ({ver}) ??x.y ?먮뒗 x.y.z")

    # status ?좏슚??
    status = pj.get("status")
    if status and status not in STATUSES:
        errors.append(f"{plugin_name}: status ?좏슚媛??꾨떂 ({status}) ??{STATUSES}")

    # phase 踰붿쐞
    phase = pj.get("phase")
    if phase is not None and not (isinstance(phase, int) and 0 <= phase <= 3):
        errors.append(f"{plugin_name}: phase ?좏슚媛??꾨떂 ({phase}) ??0~3 ?뺤닔")

    # dependencies.plugins 李몄“ ?좏슚??
    deps = pj.get("dependencies", {}).get("plugins", [])
    for d in deps:
        if d not in all_plugins:
            errors.append(f"{plugin_name}: 議댁옱?섏? ?딅뒗 ?섏〈 ?뚮윭洹몄씤 ({d})")

    # entry_points.core_skills ?뚯씪 議댁옱 ?щ?
    core_skills = pj.get("entry_points", {}).get("core_skills", [])
    skills_dir = plugins_dir / plugin_name / "skills"
    if skills_dir.exists():
        skill_files = {f.stem for f in skills_dir.glob("*.md")}
        for s in core_skills:
            if s not in skill_files:
                warnings.append(f"{plugin_name}: core_skill '{s}' ?뚯씪 ?놁쓬")

    # entry_points.default_command ?뚯씪 議댁옱 ?щ?
    default_cmd = pj.get("entry_points", {}).get("default_command")
    if default_cmd:
        cmd_file = plugins_dir / plugin_name / "commands" / f"{default_cmd}.md"
        if not cmd_file.exists():
            warnings.append(f"{plugin_name}: default_command '{default_cmd}' ?뚯씪 ?놁쓬")


# ?ㅽ뻾
targets = [target] if target else sorted(all_plugins)
for t in targets:
    validate(t)

# 異쒕젰
print(f"=== plugin.json ?ㅽ궎留?寃利?({len(targets)}媛? ===\n")
if errors:
    print(f"[RED] ?ㅻ쪟 {len(errors)}:")
    for e in errors:
        print(f"   - {e}")
    print()
if warnings:
    print(f"[YEL] 寃쎄퀬 {len(warnings)}:")
    for w in warnings:
        print(f"   - {w}")
    print()
if not errors and not warnings:
    print("[OK] ?꾨? ?듦낵")

if errors:
    sys.exit(1)
if warnings and strict:
    sys.exit(2)
sys.exit(0)

