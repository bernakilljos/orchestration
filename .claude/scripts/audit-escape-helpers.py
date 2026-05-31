#!/usr/bin/env python3
import argparse
import difflib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = ROOT / "templates"
STATE_DIR = ROOT / ".claude" / "state"
AUDIT_JSON = STATE_DIR / "escape-audit.json"
FIX_DIFF_LOG = STATE_DIR / "escape-fix-diff.log"
INNERHTML_RISKS = STATE_DIR / "innerHTML-risks.txt"

RE_AND = re.compile(r"\.replace\(\s*/&/g\s*,\s*['\"]&amp;['\"]\s*\)")
RE_LT = re.compile(r"\.replace\(\s*/</g\s*,\s*['\"]&lt;['\"]\s*\)")
RE_GT = re.compile(r"\.replace\(\s*/>/g\s*,\s*['\"]&gt;['\"]\s*\)")
RE_DQ = re.compile(r"\.replace\(\s*/\"/g\s*,\s*['\"]&quot;['\"]\s*\)")
RE_SQ = re.compile(r"\.replace\(\s*/'/g\s*,\s*['\"]&#39;['\"]\s*\)")

RE_STRING_CHAIN = re.compile(r"String\((?P<input>.*?)\)(?P<tail>(?:\s*\.replace\([^\n]*?\))+)", re.DOTALL)
RE_INNERHTML_RISK = re.compile(r"\.innerHTML\s*\+?=\s*['\"][^'\"]*['\"]\s*\+\s*[a-zA-Z]")
# 안전 마커: 변수가 esc*()/escape*()/Number()/String()/toLocaleString/toFixed 등으로 wrapped
RE_INNERHTML_SAFE_WRAP = re.compile(
    r"\.innerHTML\s*\+?=\s*['\"][^'\"]*['\"]\s*\+\s*"
    r"(?:esc[A-Za-z]*|escape[A-Za-z]*|_esc|safe[A-Za-z]*|Number|String|JSON\.stringify)\s*\("
)
# 첫 변수가 영어 loop counter (i,j,k,row,col,idx) 또는 숫자 변수면 안전
RE_INNERHTML_SAFE_LOOP_VAR = re.compile(
    r"\.innerHTML\s*\+?=\s*['\"][^'\"]*['\"]\s*\+\s*"
    r"(?:i|j|k|n|m|idx|row|col|cnt|num|cur)\b\s*\+"
)
# 첫 변수가 *Html (다른 함수에서 build한 escape된 문자열)
RE_INNERHTML_SAFE_BUILT = re.compile(
    r"\.innerHTML\s*\+?=\s*['\"][^'\"]*['\"]\s*\+\s*[a-zA-Z_]\w*Html\b"
)


def is_null_safe(inp):
    s = inp.strip()
    if "== null" in s and re.search(r"\?\s*['\"]['\"]\s*:", s):
        return True
    # `value || ''` / `s || ''` / `text || ''` — any var || ''
    if re.search(r"[A-Za-z_$][\w$]*\s*\|\|\s*['\"]['\"]", s):
        return True
    # property access `obj.field || ''`
    if re.search(r"[A-Za-z_$][\w$\.\[\]]*\s*\|\|\s*['\"]['\"]", s):
        return True
    # function preceded by early `if (!var) return ''` guard
    if re.search(r"if\s*\(\s*!\s*[A-Za-z_$][\w$]*\s*\)\s*(?:\{\s*)?return\s*['\"]['\"]", s):
        return True
    return False


def classify_chain(tail):
    has_and = bool(RE_AND.search(tail))
    has_lt = bool(RE_LT.search(tail))
    has_gt = bool(RE_GT.search(tail))
    has_dq = bool(RE_DQ.search(tail))
    has_sq = bool(RE_SQ.search(tail))

    core = has_and and has_lt and has_gt
    if not core:
        return None
    if has_dq and has_sq:
        return "full_5"
    if has_dq:
        return "missing_single_quote"
    if has_sq:
        return "missing_double_quote"
    return "core_3_only"


def normalized_input(inp):
    s = inp.strip()
    if "== null" in s and "? '' :" in s:
        return s
    # String(s || '') or String(s||'') -> null-safe ternary
    m = re.fullmatch(r"([A-Za-z_$][\w$]*)\s*\|\|\s*''", s)
    if m:
        v = m.group(1)
        return v + " == null ? '' : " + v
    # String(s)
    m2 = re.fullmatch(r"([A-Za-z_$][\w$]*)", s)
    if m2:
        v = m2.group(1)
        return v + " == null ? '' : " + v
    return s


def fix_tail(tail):
    cat = classify_chain(tail)
    if cat == "missing_single_quote":
        return tail + ".replace(/'/g,'&#39;')", True
    if cat == "missing_double_quote":
        return tail + ".replace(/\"/g,'&quot;')", True
    return tail, False


def collect_chains(content):
    items = []
    for m in RE_STRING_CHAIN.finditer(content):
        inp = m.group("input")
        tail = m.group("tail")
        cat = classify_chain(tail)
        if not cat:
            continue
        start = m.start()
        line = content.count("\n", 0, start) + 1
        items.append({
            "start": m.start(),
            "end": m.end(),
            "line": line,
            "input": inp,
            "tail": tail,
            "category": cat,
            "null_safe": is_null_safe(inp),
        })
    return items


def apply_fix(content, items):
    if not items:
        return content, []

    edits = []
    updated = content
    shift = 0
    for item in items:
        orig = updated[item["start"] + shift:item["end"] + shift]
        original_input = item["input"]
        fixed_input = normalized_input(original_input)
        fixed_tail, tail_changed = fix_tail(item["tail"])
        input_changed = fixed_input != original_input.strip()

        if not tail_changed and not input_changed:
            continue

        replacement = "String(" + fixed_input + ")" + fixed_tail
        updated = updated[:item["start"] + shift] + replacement + updated[item["end"] + shift:]
        shift += len(replacement) - len(orig)
        edits.append({
            "line": item["line"],
            "before": orig,
            "after": replacement,
        })

    return updated, edits


def audit_templates(fix=False):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "summary": {
            "files_scanned": 0,
            "helpers": {
                "full_5": 0,
                "missing_single_quote": 0,
                "missing_double_quote": 0,
                "core_3_only": 0,
                "null_safe_missing": 0,
            },
            "innerHTML_risks": 0,
            "files_changed": 0,
        },
        "files": [],
    }

    diff_lines = []
    risk_lines = []

    for path in sorted(TEMPLATES_DIR.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        content = path.read_text(encoding="utf-8")
        report["summary"]["files_scanned"] += 1

        chains = collect_chains(content)
        file_entry = {
            "file": rel,
            "helpers": [],
        }

        for item in chains:
            report["summary"]["helpers"][item["category"]] += 1
            if not item["null_safe"]:
                report["summary"]["helpers"]["null_safe_missing"] += 1
            file_entry["helpers"].append({
                "line": item["line"],
                "category": item["category"],
                "null_safe": item["null_safe"],
            })

        for idx, line in enumerate(content.splitlines(), start=1):
            if not RE_INNERHTML_RISK.search(line):
                continue
            if RE_INNERHTML_SAFE_WRAP.search(line):
                continue
            if RE_INNERHTML_SAFE_LOOP_VAR.search(line):
                continue
            if RE_INNERHTML_SAFE_BUILT.search(line):
                continue
            risk_lines.append(rel + ":" + str(idx))

        if fix:
            new_content, edits = apply_fix(content, chains)
            if edits and new_content != content:
                path.write_text(new_content, encoding="utf-8")
                report["summary"]["files_changed"] += 1
                for e in edits:
                    diff_lines.append("## " + rel + ":" + str(e["line"]))
                    diff_lines.append("- " + e["before"])
                    diff_lines.append("+ " + e["after"])

        if file_entry["helpers"]:
            report["files"].append(file_entry)

    report["summary"]["innerHTML_risks"] = len(risk_lines)

    AUDIT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    INNERHTML_RISKS.write_text("\n".join(risk_lines) + ("\n" if risk_lines else ""), encoding="utf-8")

    if fix:
        FIX_DIFF_LOG.write_text("\n".join(diff_lines) + ("\n" if diff_lines else ""), encoding="utf-8")

    return report


def main():
    parser = argparse.ArgumentParser(description="Audit and fix escape helpers in templates.")
    parser.add_argument("--fix", action="store_true", help="Apply automatic fixes for 4-char escape helpers and null-safe input")
    args = parser.parse_args()

    report = audit_templates(fix=args.fix)
    print("Scanned files:", report["summary"]["files_scanned"])
    print("full_5:", report["summary"]["helpers"]["full_5"])
    print("missing_single_quote:", report["summary"]["helpers"]["missing_single_quote"])
    print("missing_double_quote:", report["summary"]["helpers"]["missing_double_quote"])
    print("core_3_only:", report["summary"]["helpers"]["core_3_only"])
    print("null_safe_missing:", report["summary"]["helpers"]["null_safe_missing"])
    print("innerHTML_risks:", report["summary"]["innerHTML_risks"])
    if args.fix:
        print("files_changed:", report["summary"]["files_changed"])


if __name__ == "__main__":
    main()
