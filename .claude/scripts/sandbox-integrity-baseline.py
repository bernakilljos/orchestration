"""운영 Sandbox·Evidence·Sandbox 기록 SHA-256 무결성 기준선 (읽기 전용 · 2026-11-03 T4).

사용:
  python sandbox-integrity-baseline.py baseline            # 기준선 생성 (.claude/state/integrity-baseline/)
  python sandbox-integrity-baseline.py verify <manifest>   # 기준선 대비 변경·삭제·추가 비교

원칙:
- 대상 파일은 열어서 읽기만 한다 (쓰기·이동·삭제 0). git 은 --no-optional-locks 로 index 갱신도 하지 않는다.
- 1MB 단위 스트리밍 해시 · 결과는 JSONL 로 바로 기록 (메모리에 전체 목록을 들고 있지 않음).
- 기준선 시점에 이미 sandbox commit 과 다른 파일은 '정상 기준' 으로 가정하지 않고 drift_at_baseline 으로 따로 표시.
- 저장 위치는 운영 sandbox 바깥 (.claude/state/integrity-baseline/ · gitignore 대상).
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SANDBOX_ROOT = ROOT / ".repair-sandbox"
STATE = ROOT / ".claude" / "state"
SANDBOX_RECORD = STATE / "repair-sandboxes.json"
OUT_DIR = STATE / "integrity-baseline"
CHUNK = 1024 * 1024


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts))


def _git(cwd: Path, *args: str) -> str:
    r = subprocess.run(["git", "--no-optional-locks", *args], cwd=str(cwd), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=300)
    return r.stdout if r.returncode == 0 else ""


def _walk(base: Path):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames.sort()
        for name in sorted(filenames):
            yield Path(dirpath) / name


def _entry(kind: str, group: str, path: Path) -> dict:
    st = path.stat()
    return {"kind": kind, "group": group, "path": path.relative_to(ROOT).as_posix(), "size": st.st_size,
            "mtime": _iso(st.st_mtime), "ctime": _iso(st.st_ctime), "sha256": sha256(path)}


def baseline() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    manifest = OUT_DIR / f"manifest-{stamp}.jsonl"
    summary = {"created_at": _iso(time.time()), "manifest": manifest.relative_to(ROOT).as_posix(),
               "sandboxes": {}, "evidence": {}, "sandbox_record": {}, "errors": []}
    with open(manifest, "w", encoding="utf-8") as out:
        # 1. 운영 sandbox (폴더별)
        for sb in sorted(p for p in SANDBOX_ROOT.iterdir() if p.is_dir()) if SANDBOX_ROOT.exists() else []:
            files = size = 0
            for f in _walk(sb):
                try:
                    e = _entry("sandbox_file", sb.name, f)
                except OSError as ex:
                    summary["errors"].append({"path": str(f), "error": str(ex)})
                    continue
                out.write(json.dumps(e, ensure_ascii=False) + "\n")
                files += 1
                size += e["size"]
            # 기준선 시점에 이미 sandbox commit 과 다른 파일 (정상 기준으로 가정하지 않음)
            drift = [ln for ln in _git(sb, "status", "--porcelain", "--untracked-files=all").splitlines() if ln]
            summary["sandboxes"][sb.name] = {"files": files, "bytes": size,
                                             "head": _git(sb, "rev-parse", "HEAD").strip() or None,
                                             "drift_at_baseline": drift[:200], "drift_count": len(drift)}
        # 2. Evidence JSON
        for f in sorted(STATE.glob("*evidence*.json")):
            e = _entry("evidence", "evidence", f)
            try:
                json.loads(f.read_text(encoding="utf-8"))
                e["json_valid"] = True
            except Exception as ex:
                e["json_valid"] = False
                e["json_error"] = str(ex)[:200]
            out.write(json.dumps(e, ensure_ascii=False) + "\n")
            summary["evidence"][f.name] = {k: e[k] for k in ("size", "sha256", "mtime", "json_valid")}
        # 3. Sandbox 기록 (파일 전체 + 항목별 · 새 항목 추가는 정상이므로 항목 단위로 비교)
        if SANDBOX_RECORD.exists():
            e = _entry("sandbox_record", "record", SANDBOX_RECORD)
            out.write(json.dumps(e, ensure_ascii=False) + "\n")
            rec = json.loads(SANDBOX_RECORD.read_text(encoding="utf-8"))
            for key in sorted(rec):
                blob = json.dumps(rec[key], ensure_ascii=False, sort_keys=True).encode("utf-8")
                path = (rec[key] or {}).get("path") if isinstance(rec[key], dict) else None
                item = {"kind": "sandbox_record_entry", "group": "record", "path": key,
                        "sha256": hashlib.sha256(blob).hexdigest(),
                        "status": (rec[key] or {}).get("status") if isinstance(rec[key], dict) else None,
                        "dir_exists": bool(path and Path(path).exists())}
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
            summary["sandbox_record"] = {"file_sha256": e["sha256"], "entries": len(rec)}
    summary["totals"] = {"sandboxes": len(summary["sandboxes"]),
                         "sandbox_files": sum(v["files"] for v in summary["sandboxes"].values()),
                         "sandbox_bytes": sum(v["bytes"] for v in summary["sandboxes"].values()),
                         "drift_files": sum(v["drift_count"] for v in summary["sandboxes"].values()),
                         "evidence": len(summary["evidence"]),
                         "record_entries": summary["sandbox_record"].get("entries", 0),
                         "errors": len(summary["errors"])}
    summary["manifest_sha256"] = sha256(manifest)
    (OUT_DIR / f"summary-{stamp}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                                   encoding="utf-8")
    return summary


def verify(manifest: Path) -> dict:
    """기준선 대비: 기존 파일 변경·삭제 = 위반 · 새 sandbox/새 기록 항목 추가 = 정상(보고만)."""
    changed, missing, record_changed, record_missing = [], [], [], []
    seen_groups, seen_files = set(), set()
    rec = json.loads(SANDBOX_RECORD.read_text(encoding="utf-8")) if SANDBOX_RECORD.exists() else {}
    with open(manifest, encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            if e["kind"] in ("sandbox_file", "evidence"):
                p = ROOT / e["path"]
                seen_groups.add(e["group"])
                seen_files.add(e["path"])
                if not p.exists():
                    missing.append(e["path"])
                elif p.stat().st_size != e["size"] or sha256(p) != e["sha256"]:
                    changed.append(e["path"])
            elif e["kind"] == "sandbox_record_entry":
                cur = rec.get(e["path"])
                if cur is None:
                    record_missing.append(e["path"])
                elif hashlib.sha256(json.dumps(cur, ensure_ascii=False, sort_keys=True)
                                    .encode("utf-8")).hexdigest() != e["sha256"]:
                    record_changed.append(e["path"])
    added_files = [f.relative_to(ROOT).as_posix() for g in sorted(seen_groups - {"evidence"})
                   for f in _walk(SANDBOX_ROOT / g)
                   if (SANDBOX_ROOT / g).exists() and f.relative_to(ROOT).as_posix() not in seen_files]
    new_sandboxes = sorted(p.name for p in SANDBOX_ROOT.iterdir() if p.is_dir() and p.name not in seen_groups) \
        if SANDBOX_ROOT.exists() else []
    return {"ok": not (changed or missing or record_changed or record_missing),
            "changed": changed[:200], "missing": missing[:200], "record_changed": record_changed,
            "record_missing": record_missing, "added_files_in_existing_sandboxes": added_files[:200],
            "new_sandboxes": new_sandboxes,
            "new_record_entries": sorted(set(rec) - _record_keys(manifest))}


def _record_keys(manifest: Path) -> set:
    keys = set()
    with open(manifest, encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            if e["kind"] == "sandbox_record_entry":
                keys.add(e["path"])
    return keys


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "baseline":
        s = baseline()
        print(json.dumps({k: s[k] for k in ("created_at", "manifest", "manifest_sha256", "totals")},
                         ensure_ascii=False, indent=1))
    elif len(sys.argv) >= 3 and sys.argv[1] == "verify":
        r = verify(Path(sys.argv[2]) if Path(sys.argv[2]).is_absolute() else ROOT / sys.argv[2])
        print(json.dumps(r, ensure_ascii=False, indent=1))
        sys.exit(0 if r["ok"] else 1)
    else:
        print(__doc__)
        sys.exit(2)
