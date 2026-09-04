#!/usr/bin/env python3
"""
plugin.json 스키마 검증 — 필수 필드-타입-prefix 일치-의존 참조 유효성 확인.

사용법:
  python .claude/scripts/validate-plugin-schema.py              전체 검증
  python .claude/scripts/validate-plugin-schema.py <plugin>     단일 검증
  python .claude/scripts/validate-plugin-schema.py --strict     경고도 실패로

exit 0 = OK, 1 = error, 2 = warning
"""
import json, sys, re
from pathlib import Path

# Windows cp949 대응
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
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

# 전체 플러그인 목록 (의존 참조 유효성 체크용)
all_plugins = {p.name for p in plugins_dir.iterdir() if p.is_dir() and not p.name.startswith("_")}

def validate(plugin_name):
    p = plugins_dir / plugin_name / "plugin.json"
    if not p.exists():
        errors.append(f"{plugin_name}: plugin.json 없음")
        return

    try:
        pj = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"{plugin_name}: JSON 파싱 실패 — {e}")
        return

    # 필수 필드
    for f in REQUIRED:
        if f not in pj:
            errors.append(f"{plugin_name}: 필수 필드 누락 — {f}")

    # name 일치
    if pj.get("name") != plugin_name:
        errors.append(f"{plugin_name}: name 필드({pj.get('name')}) != 디렉토리명")

    # name 패턴
    name = pj.get("name", "")
    if name and not NAME_RE.match(name):
        errors.append(f"{plugin_name}: name 패턴 위반 ({name}) — 소문자+숫자+언더스코어")

    # prefix 패턴
    prefix = pj.get("prefix", "")
    if prefix and not PREFIX_RE.match(prefix):
        errors.append(f"{plugin_name}: prefix 패턴 위반 ({prefix}) — xxx_ 형태")

    # prefix ↔ name 일치 (name이 prefix로 시작해야)
    if prefix and name and not name.startswith(prefix):
        warnings.append(f"{plugin_name}: name({name})이 prefix({prefix})로 시작 안 함")

    # version 패턴
    ver = pj.get("version", "")
    if ver and not VERSION_RE.match(ver):
        errors.append(f"{plugin_name}: version 패턴 위반 ({ver}) — x.y 또는 x.y.z")

    # status 유효성
    status = pj.get("status")
    if status and status not in STATUSES:
        errors.append(f"{plugin_name}: status 유효값 아님 ({status}) — {STATUSES}")

    # phase 범위
    phase = pj.get("phase")
    if phase is not None and not (isinstance(phase, int) and 0 <= phase <= 3):
        errors.append(f"{plugin_name}: phase 유효값 아님 ({phase}) — 0~3 정수")

    # dependencies.plugins 참조 유효성
    deps = pj.get("dependencies", {}).get("plugins", [])
    for d in deps:
        if d not in all_plugins:
            errors.append(f"{plugin_name}: 존재하지 않는 의존 플러그인 ({d})")

    # entry_points.core_skills 파일 존재 여부
    core_skills = pj.get("entry_points", {}).get("core_skills", [])
    skills_dir = plugins_dir / plugin_name / "skills"
    if skills_dir.exists():
        skill_files = {f.stem for f in skills_dir.glob("*.md")}
        for s in core_skills:
            if s not in skill_files:
                warnings.append(f"{plugin_name}: core_skill '{s}' 파일 없음")

    # entry_points.default_command 파일 존재 여부
    default_cmd = pj.get("entry_points", {}).get("default_command")
    if default_cmd:
        cmd_file = plugins_dir / plugin_name / "commands" / f"{default_cmd}.md"
        if not cmd_file.exists():
            warnings.append(f"{plugin_name}: default_command '{default_cmd}' 파일 없음")


# 실행
targets = [target] if target else sorted(all_plugins)
for t in targets:
    validate(t)

# 출력
print(f"=== plugin.json 스키마 검증 ({len(targets)}개) ===\n")
if errors:
    print(f"[RED] 오류 {len(errors)}:")
    for e in errors:
        print(f"   - {e}")
    print()
if warnings:
    print(f"[YEL] 경고 {len(warnings)}:")
    for w in warnings:
        print(f"   - {w}")
    print()
if not errors and not warnings:
    print("[OK] 전부 통과")

if errors:
    sys.exit(1)
if warnings and strict:
    sys.exit(2)
sys.exit(0)
