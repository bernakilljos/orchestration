#!/usr/bin/env python3
# 11-25축 추가 전수조사
import pathlib, subprocess, json, re, os, sqlite3
R = pathlib.Path(".")

print("=" * 60)
print("11~25축 추가 전수조사")
print("=" * 60)

# 11. Setup 실행 가능
print("\n[11] Setup 실행 가능성")
setup_bat = R/"setup/setup.bat"
setup_sh = R/"setup/setup.sh"
install_bat = R/"setup/install.bat"
print(f"  setup.bat: {setup_bat.exists()} ({setup_bat.stat().st_size if setup_bat.exists() else 0} B)")
print(f"  setup.sh: {setup_sh.exists()}")
print(f"  install.bat: {install_bat.exists()}")
modules = sorted((R/"setup/modules").glob("*.bat"))
print(f"  setup/modules: {len(modules)}")

# 12. sync drift
print("\n[12] sync-plugins drift")
try:
    r = subprocess.run(["bash", ".claude/scripts/sync-plugins.sh", "--check"],
                       capture_output=True, text=True, timeout=30)
    for l in r.stdout.split("\n")[-8:]:
        s = l.strip()
        if s and any(k in s.lower() for k in ["drift","orphan","conflict","complete","skipped"]):
            print(f"  {s[:100]}")
except Exception as e:
    print(f"  ERR {e}")

# 13. plugin.json schema
print("\n[13] plugin.json schema")
invalid = []
total = 0
for p in R.glob("plugins/*/plugin.json"):
    total += 1
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        for req in ["name","display","version","status"]:
            if req not in d:
                invalid.append(f"{p.parent.name}: missing {req}")
                break
    except json.JSONDecodeError:
        invalid.append(f"{p.parent.name}: JSON parse")
print(f"  total: {total}, invalid: {len(invalid)}")
for i in invalid[:5]: print(f"  FAIL {i}")

# 14. Memory 참조
print("\n[14] Memory 실제 존재")
mem_dir = pathlib.Path.home()/".claude/projects/C--pjt-orchestration-v1/memory"
mem_md = mem_dir/"MEMORY.md"
if mem_md.exists():
    text = mem_md.read_text(encoding="utf-8")
    refs = re.findall(r"\]\((\w[\w_-]*\.md)\)", text)
    missing = [r for r in refs if not (mem_dir/r).exists()]
    print(f"  refs: {len(refs)}, missing: {len(missing)}")
    for m in missing[:5]: print(f"  FAIL {m}")

# 15. settings.json
print("\n[15] settings.json")
for f in [".claude/settings.json", "setup/templates/settings.template.json"]:
    p = R/f
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8-sig"))
            print(f"  {f}: OK ({len(list(d.keys()))} keys)")
        except Exception as e:
            print(f"  FAIL {f}: {type(e).__name__}")
    else:
        print(f"  MISSING {f}")

# 16. Statusline
print("\n[16] Statusline render")
try:
    stdin_sample = '{"model":{"id":"claude-opus-5-5"},"session_id":"test","workspace":{"current_dir":"' + str(R).replace("\\","\\\\") + '"}}'
    r = subprocess.run(["python","-X","utf8",".claude/scripts/statusline_context.py"],
                       input=stdin_sample, capture_output=True, text=True, timeout=10)
    lines = [l for l in r.stdout.split("\n") if l.strip()]
    print(f"  lines: {len(lines)}, rc: {r.returncode}")
    for l in lines[:3]: print(f"  > {l[:100]}")
    if r.stderr:
        print(f"  stderr: {r.stderr[:100]}")
except Exception as e:
    print(f"  ERR {e}")

# 17. 문서 참조 깨짐
print("\n[17] 문서 참조 깨짐")
broken = []
for doc in ["CLAUDE.md","guide.txt","README.md"]:
    p = R/doc
    if not p.exists(): continue
    txt = p.read_text(encoding="utf-8", errors="replace")
    refs = re.findall(r"`([\w./_-]+\.(?:md|sh|py|json))`", txt)
    for r in set(refs):
        if r.startswith("http") or "example" in r.lower(): continue
        if not (R/r).exists():
            broken.append(f"{doc} to {r}")
print(f"  broken: {len(broken)}")
for b in broken[:8]: print(f"  FAIL {b}")

# 18. permission
print("\n[18] permission mode")
try:
    s = json.loads((R/".claude/settings.json").read_text(encoding="utf-8-sig"))
    perm = s.get("permissions", {})
    mode = perm.get("defaultMode") or perm.get("mode") or "(not set)"
    print(f"  defaultMode: {mode}")
    print(f"  allow: {len(perm.get('allow') or [])}, deny: {len(perm.get('deny') or [])}")
except Exception as e:
    print(f"  ERR {e}")

# 19. Dockerfile
print("\n[19] Dockerfile")
df = R/"Dockerfile"
if df.exists():
    txt = df.read_text(encoding="utf-8", errors="replace")
    print(f"  FROM: {'FROM ' in txt}, WORKDIR: {'WORKDIR ' in txt}, CMD/ENTRYPOINT: {'CMD ' in txt or 'ENTRYPOINT ' in txt}")
    print(f"  HEALTHCHECK: {'HEALTHCHECK ' in txt}, USER: {'USER ' in txt}")
    print(f"  size: {df.stat().st_size} B")

# 20. .env
print("\n[20] .env.example")
env_ex = R/".env.example"
print(f"  .env.example: {env_ex.exists()}")
if env_ex.exists():
    lines = [l for l in env_ex.read_text(encoding="utf-8").split("\n") if "=" in l and not l.strip().startswith("#")]
    print(f"  변수: {len(lines)}")

# 21. Backup rotation
print("\n[21] Backup disk")
total = 0; cnt = 0
for p in R.rglob("*.bak*"):
    if ".git" in str(p): continue
    total += p.stat().st_size
    cnt += 1
print(f"  bak files: {cnt}, {total/1024/1024:.1f} MB")

# 22. orca.db
print("\n[22] orca.db health")
dbf = R/".claude/state/orca.db"
if dbf.exists():
    try:
        conn = sqlite3.connect(f"file:{dbf}?mode=ro", uri=True, timeout=5)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        integrity = cur.fetchone()[0]
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print(f"  integrity: {integrity}")
        print(f"  tables: {len(tables)}")
        print(f"  size: {dbf.stat().st_size/1024:.0f} KB")
        conn.close()
    except Exception as e:
        print(f"  ERR {e}")

# 23. plugin 순환 의존
print("\n[23] plugin 순환 의존")
deps = {}
for p in R.glob("plugins/*/plugin.json"):
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        name = d.get("name", p.parent.name)
        deps[name] = (d.get("dependencies") or {}).get("plugins") or []
    except: pass
cycles = []
def dfs(n, path, seen):
    if n in seen: return
    if n in path:
        cycles.append(" -> ".join(path + [n]))
        return
    for dep in deps.get(n, []):
        dfs(dep, path + [n], seen | {n})
for n in deps:
    dfs(n, [], set())
print(f"  plugins: {len(deps)}, cycles: {len(cycles)}")

# 24. [[link]] 참조
print("\n[24] [[link]] broken")
broken_links = []
rule_files = {p.stem: p for p in (R/".claude/rules").glob("*.md")}
memory_files = {p.stem: p for p in mem_dir.glob("*.md")} if mem_dir.exists() else {}
for p in list(rule_files.values()) + list(memory_files.values()):
    txt = p.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"\[\[([\w_-]+)\]\]", txt):
        link = m.group(1)
        if link not in rule_files and link not in memory_files:
            broken_links.append(f"{p.name} to [[{link}]]")
print(f"  broken: {len(broken_links)}")
for b in broken_links[:5]: print(f"  FAIL {b}")

# 25. shebang
print("\n[25] .sh shebang")
no_shebang = []
total_sh = 0
for p in R.rglob("*.sh"):
    if ".git" in str(p): continue
    total_sh += 1
    try:
        first = p.read_text(encoding="utf-8", errors="replace")[:50]
        if not first.startswith("#!"):
            no_shebang.append(str(p.relative_to(R)))
    except: pass
print(f"  total .sh: {total_sh}, no shebang: {len(no_shebang)}")
for n in no_shebang[:5]: print(f"  FAIL {n}")
print("\n" + "=" * 60)
