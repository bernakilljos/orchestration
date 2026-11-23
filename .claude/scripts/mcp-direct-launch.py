#!/usr/bin/env python
"""mcp-direct-launch — 사용자 범위 MCP 중 `cmd /c npx [-y] <패키지> …` 로 등록된 서버를 `node <진입 파일> …` 로 바꾼다.

R357 (2026-11-23 실측 · sequential-thinking 같은 서버 비교):
  cmd /c npx -y  = 프로세스 7개 (cmd·conhost·npx·cmd·node(npx-cli)·cmd·node) · 트리 private 157~181MB
  node 직접      = 프로세스 4개 · 57MB  → 서버 1개당 약 100MB · 세션 동안 계속 떠 있는 npx-cli node 가 사라짐
  또 npx -y 는 시작할 때마다 패키지 저장소를 확인해 세션 시작 경합 때 «30초 연결 시간 초과» 가 났다 (이번 세션 5개).

방식:
  1) 패키지를 고정 위치에 설치 — npx 캐시(_npx/<해시>) 는 이름이 바뀌고 지워질 수 있어 경로로 쓰지 않는다
     위치 = %LOCALAPPDATA%\\orca-mcp (Windows) · ~/.local/share/orca-mcp (그 밖) · ORCA_MCP_DIR 로 변경
  2) package.json 의 bin 으로 진입 파일을 찾고, 실제 MCP initialize 응답을 받은 서버만 바꾼다 (실패 = 그대로 둠)
  3) 인자·환경 변수·type 등 나머지 설정은 그대로 · 이전 등록은 .claude/state/mcp-direct-backup.json 에 보관
  4) 등록 변경은 공식 CLI 로만 (claude mcp remove -s user → claude mcp add-json -s user) · ~/.claude.json 직접 쓰기 X
  변경은 다음 세션부터 적용된다 (지금 떠 있는 서버는 그대로).

범위: 사용자(user) + 이 저장소의 local · 프로젝트 공유 .mcp.json 은 건드리지 않음
사용: python mcp-direct-launch.py --check | --apply [--only 이름,…] | --rollback [이름,…] | --auto (24시간에 1번 --apply)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / ".claude" / "logs" / "mcp-direct.log"
BACKUP = ROOT / ".claude" / "state" / "mcp-direct-backup.json"
MARK = ROOT / ".claude" / "state" / "mcp-direct-last.txt"
NOWIN = 0x08000000 if os.name == "nt" else 0


def base_dir() -> Path:
    if os.environ.get("ORCA_MCP_DIR"):
        return Path(os.environ["ORCA_MCP_DIR"])
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "orca-mcp"
    return Path.home() / ".local" / "share" / "orca-mcp"


def log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except OSError:
        pass


def servers() -> list:
    """[(범위, 이름, 설정)] — 사용자 범위 + 이 저장소의 local 범위 (~/.claude.json projects[<저장소>].mcpServers)."""
    p = Path.home() / ".claude.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for n, e in (d.get("mcpServers") or {}).items():
        out.append(("user", n, e))
    want = os.path.normcase(os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or str(ROOT)))
    for key, proj in (d.get("projects") or {}).items():
        if isinstance(proj, dict) and os.path.normcase(os.path.abspath(key)) == want:
            for n, e in (proj.get("mcpServers") or {}).items():
                out.append(("local", n, e))
    return out


def parse_npx(entry: dict):
    """(패키지 지정, 패키지 이름, 나머지 인자) 또는 None — cmd /c npx [-y] pkg … · npx [-y] pkg …"""
    cmd = str(entry.get("command") or "")
    args = [str(a) for a in (entry.get("args") or [])]
    base = os.path.basename(cmd).lower()
    if base in ("cmd", "cmd.exe") and len(args) >= 2 and args[0].lower() == "/c" and args[1].lower() in ("npx", "npx.cmd"):
        rest = args[2:]
    elif base in ("npx", "npx.cmd"):
        rest = args
    else:
        return None
    while rest and rest[0] in ("-y", "--yes"):
        rest = rest[1:]
    if not rest or rest[0].startswith("-"):
        return None
    spec = rest[0]
    name = spec
    if spec.startswith("@"):
        at = spec.find("@", 1)
        name = spec if at < 0 else spec[:at]
    elif "@" in spec:
        name = spec.split("@", 1)[0]
    return spec, name, rest[1:]


def entry_file(base: Path, name: str):
    pj = base / "node_modules" / Path(*name.split("/")) / "package.json"
    try:
        d = json.loads(pj.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    b = d.get("bin")
    if isinstance(b, dict) and b:
        short = name.split("/")[-1]
        rel = b.get(short) or next(iter(b.values()))
    elif isinstance(b, str):
        rel = b
    else:
        rel = d.get("main")
    if not rel:
        return None
    f = (pj.parent / rel).resolve()
    return f if f.is_file() else None


def npm_install(base: Path, specs: list) -> bool:
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        log("npm 없음 — 설치 건너뜀")
        return False
    base.mkdir(parents=True, exist_ok=True)
    if not (base / "package.json").exists():
        (base / "package.json").write_text('{"name":"orca-mcp","private":true}\n', encoding="utf-8")
    try:
        p = subprocess.run([npm, "install", "--prefix", str(base), "--no-audit", "--no-fund", "--loglevel=error", *specs],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600, creationflags=NOWIN)
    except Exception as e:  # noqa: BLE001
        log("npm install 실패: %s" % e)
        return False
    if p.returncode != 0:
        log("npm install rc=%s %s" % (p.returncode, (p.stderr or "")[-400:]))
    return p.returncode == 0


def probe(cmd: list, env: dict | None, timeout: float = 30.0) -> bool:
    """MCP initialize 요청에 result 가 오면 True (서버 트리는 끝나면 정리)."""
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             env={**os.environ, **(env or {})}, creationflags=NOWIN)
    except Exception:  # noqa: BLE001
        return False
    req = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "orca-probe", "version": "1"}}}
    ok = {"v": False}

    def rd():
        try:
            p.stdin.write((json.dumps(req) + "\n").encode())
            p.stdin.flush()
            t_end = time.time() + timeout
            while time.time() < t_end:
                line = p.stdout.readline()
                if not line:
                    return
                try:
                    msg = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue          # 서버가 stdout 에 다른 줄을 먼저 쓰는 경우
                if msg.get("id") == 1 and "result" in msg:
                    ok["v"] = True
                    return
        except Exception:  # noqa: BLE001
            return
    th = threading.Thread(target=rd, daemon=True)
    th.start()
    th.join(timeout)
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True, creationflags=NOWIN, timeout=15)
        else:
            p.kill()
    except Exception:  # noqa: BLE001
        pass
    return ok["v"]


def claude_cli():
    return shutil.which("claude.exe") or shutil.which("claude") or shutil.which("claude.cmd")


def reregister(name: str, new: dict, scope: str = "user") -> bool:
    cli = claude_cli()
    if not cli:
        log("claude CLI 없음 — %s 재등록 못 함" % name)
        return False
    kw = dict(capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, creationflags=NOWIN, stdin=subprocess.DEVNULL)
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or str(ROOT)   # local 범위는 저장소 폴더 기준
    r1 = subprocess.run([cli, "mcp", "remove", name, "-s", scope], cwd=cwd, **kw)
    r2 = subprocess.run([cli, "mcp", "add-json", name, json.dumps(new, ensure_ascii=False), "-s", scope], cwd=cwd, **kw)
    if r2.returncode != 0:
        log("%s add-json 실패 rc=%s %s · remove rc=%s" % (name, r2.returncode, (r2.stderr or r2.stdout)[-300:], r1.returncode))
        return False
    return True


def load_backup() -> dict:
    try:
        return json.loads(BACKUP.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_backup(b: dict) -> None:
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    tmp = BACKUP.with_suffix(".tmp")
    tmp.write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, BACKUP)


def plan(only=None):
    out = []
    for scope, name, e in servers():
        if only and name not in only or not isinstance(e, dict):
            continue
        r = parse_npx(e)
        if r:
            out.append((scope, name, e, *r))
    return out


def cmd_check(only=None) -> int:
    base = base_dir()
    rows = plan(only)
    if not rows:
        print("바꿀 대상 없음 (cmd /c npx 로 등록된 사용자 범위 MCP 0개)")
    for scope, name, e, spec, pkg, rest in rows:
        f = entry_file(base, pkg)
        print("%-6s %-22s %-45s → %s" % (scope, name, spec, ("node " + str(f)) if f else "(아직 설치 안 됨)"))
    return 0


def cmd_apply(only=None) -> int:
    base = base_dir()
    rows = plan(only)
    if not rows:
        log("apply: 대상 없음")
        print("대상 없음")
        return 0
    node = shutil.which("node") or shutil.which("node.exe")
    if not node:
        log("node 없음 — 중단")
        print("node 없음")
        return 1
    npm_install(base, sorted({spec for _s, _n, _e, spec, _p, _r in rows}))
    bk = load_backup()
    changed = 0
    for scope, name, e, spec, pkg, rest in rows:
        f = entry_file(base, pkg)
        if not f:
            log("%s: 진입 파일 못 찾음 (%s) — 그대로 둠" % (name, pkg))
            print("%-22s 그대로 (진입 파일 없음)" % name)
            continue
        new = dict(e)
        new["command"] = "node"
        new["args"] = [str(f)] + rest
        if not probe([node, str(f)] + rest, e.get("env") if isinstance(e.get("env"), dict) else None):
            log("%s: 직접 실행 initialize 응답 없음 — 그대로 둠" % name)
            print("%-22s 그대로 (직접 실행 응답 없음)" % name)
            continue
        bk[name] = {"saved_at": time.strftime("%Y-%m-%d %H:%M:%S"), "scope": scope, "entry": e}
        save_backup(bk)
        if reregister(name, new, scope):
            changed += 1
            log("%s: %s → node %s" % (name, " ".join([str(e.get("command"))] + [str(a) for a in e.get("args") or []]), f))
            print("%-22s 바꿈 → node %s" % (name, f))
        else:
            print("%-22s 실패 (로그 참고)" % name)
    return 0 if changed or not rows else 1


def cmd_rollback(only=None) -> int:
    bk = load_backup()
    n = 0
    for name, rec in list(bk.items()):
        if only and name not in only:
            continue
        if reregister(name, rec["entry"], rec.get("scope", "user")):
            log("%s: 되돌림" % name)
            del bk[name]
            n += 1
    save_backup(bk)
    print("되돌림 %d개" % n)
    return 0


def main(argv) -> int:
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = set(argv[i + 1].split(",")) if i + 1 < len(argv) else None
    if "--rollback" in argv:
        i = argv.index("--rollback")
        names = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else ""
        return cmd_rollback(set(names.split(",")) if names else None)
    if "--apply" in argv:
        return cmd_apply(only)
    if "--auto" in argv:
        try:
            if time.time() - MARK.stat().st_mtime < 86400:
                return 0
        except OSError:
            pass
        MARK.parent.mkdir(parents=True, exist_ok=True)
        MARK.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
        if not plan():
            return 0
        return cmd_apply()
    return cmd_check(only)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
