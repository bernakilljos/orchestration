"""tech_discovery.py — 2026-10-26 외부 AI P0 (Universal Technology Discovery · 최소 실행 루프 scaffold).

목표: 수천 기술 하드코딩 X · 프로젝트 받으면 관련 기술 자동 탐색 · 기능 격차 발굴.

최소 종단 간 흐름 (MVP):
  1. Project Discovery   — 소스·README·package 분석 → 도메인 추정
  2. Domain Discovery    — 상위 20 기술 영역 중 매칭
  3. Technology Research — WebSearch (상위 N 쿼리) · 최신 제품·오픈소스 수집
  4. Capability Inventory — 현재 소스 실측 기능 추출
  5. Gap Analysis        — TO-BE 기능 vs AS-IS → 누락 리스트
  6. Innovation          — 조합 아이디어 (경쟁사 복제 X)
  7. Evidence Save       — orca.db + .claude/state/tech-discovery/ 저장

외부 AI 원칙 반영:
- 기술 이름 하드코딩 X · 상위 20 분류만 seed
- Coverage Gate · Innovation Gate · Discovery Gate (future)
- 기존 Supervisor·Unified Runner·CAS·Memory 재사용 (중복 X)
- WebSearch · WebFetch 로 실시간 조사
- Evidence (출처·버전·날짜) 필수

사용:
  python tech_discovery.py analyze <project_path>
  python tech_discovery.py domain-list
  python tech_discovery.py research "<domain>" [--depth N]
  python tech_discovery.py gap <project_path> <domain>
  python tech_discovery.py evidence <topic> --source URL --version X --date YYYY-MM-DD

scaffold 수준:
- 상위 20 도메인 seed (seed only · 자동 확장 설계)
- orca.db.tech_evidence 테이블 신규
- WebSearch 호출은 Claude 가 agent 내 사용 (이 scaffold 는 저장·조회만)
- 다음 단계: Supervisor REPAIR workflow 처럼 DISCOVERY workflow 추가
"""
from __future__ import annotations
import os
import sys
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"
STATE_DIR = ROOT / ".claude" / "state" / "tech-discovery"


# 외부 AI 상위 20 도메인 (seed only · 자동 확장)
SEED_DOMAINS = {
    "ai-model":           ["LLM", "SLM", "MoE", "추론최적화", "파인튜닝"],
    "ai-agent":           ["Agentic", "멀티에이전트", "MCP", "A2A", "도구호출"],
    "ai-memory":          ["mem0", "GraphMemory", "계층기억", "검색·망각"],
    "search-rag":         ["VectorDB", "HybridSearch", "GraphRAG", "Re-ranking"],
    "document-ai":        ["OCR", "IDP", "LayoutAnalysis", "표·수식·필기"],
    "multimodal":         ["Vision", "Audio", "Video", "Speech", "TTS"],
    "rpa-automation":     ["녹화", "ComputerUse", "Workflow", "BPM", "스케줄"],
    "backend":            ["API", "마이크로서비스", "메시징", "캐시", "이벤트"],
    "frontend":           ["React", "Vue", "Svelte", "렌더링", "상태관리"],
    "ui-ux":              ["디자인시스템", "접근성", "VisualQA", "반응형"],
    "data-engineering":   ["ETL", "CDC", "Streaming", "Lakehouse"],
    "database":           ["RDBMS", "NoSQL", "GraphDB", "NewSQL"],
    "security":           ["IAM", "OAuth", "ZeroTrust", "Secrets", "SAST", "DAST"],
    "cloud":              ["AWS", "Azure", "GCP", "Serverless", "Edge"],
    "devops":             ["CI/CD", "GitOps", "Docker", "Kubernetes", "IaC"],
    "quality-testing":    ["Unit", "E2E", "PropertyTesting", "Mutation"],
    "observability":      ["Logs", "Metrics", "Trace", "OpenTelemetry", "SRE"],
    "mobile-desktop":     ["iOS", "Android", "Electron", "Tauri", "Windows"],
    "distributed":        ["Queue", "Consensus", "Saga", "EventSourcing"],
    "business-platform":  ["SaaS", "결제", "멀티테넌시", "과금", "라이선스"],
}


def _ensure_schema() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(DB), timeout=10) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS tech_domains (
          domain_id TEXT PRIMARY KEY,
          display_name TEXT,
          seed_capabilities TEXT,
          created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tech_evidence (
          evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
          domain_id TEXT,
          topic TEXT NOT NULL,
          technology TEXT,
          capability TEXT,
          source_url TEXT,
          version TEXT,
          confirmed_at TEXT,
          summary TEXT,
          saved_at INTEGER NOT NULL,
          FOREIGN KEY (domain_id) REFERENCES tech_domains(domain_id)
        );
        CREATE INDEX IF NOT EXISTS idx_evidence_domain ON tech_evidence(domain_id, saved_at DESC);
        CREATE TABLE IF NOT EXISTS tech_gaps (
          gap_id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_path TEXT NOT NULL,
          domain_id TEXT NOT NULL,
          as_is TEXT,
          to_be TEXT,
          gap_description TEXT,
          priority TEXT CHECK(priority IN ('low','medium','high','critical')),
          verified INTEGER DEFAULT 0,
          saved_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_gaps_project ON tech_gaps(project_path, priority, saved_at DESC);
        CREATE TABLE IF NOT EXISTS tech_discovery_runs (
          run_id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_path TEXT NOT NULL,
          domains_scanned INTEGER,
          evidence_count INTEGER,
          gaps_found INTEGER,
          innovations_proposed INTEGER,
          coverage_score REAL,
          started_at INTEGER NOT NULL,
          ended_at INTEGER,
          status TEXT CHECK(status IN ('running','completed','failed'))
        );
        """)
        # seed domains 적재 (idempotent)
        now = int(time.time())
        for did, caps in SEED_DOMAINS.items():
            c.execute(
                "INSERT OR IGNORE INTO tech_domains (domain_id, display_name, seed_capabilities, created_at) "
                "VALUES (?, ?, ?, ?)",
                (did, did.replace("-", " ").title(), json.dumps(caps, ensure_ascii=False), now)
            )


def _detect_project_signals(project_path: Path) -> Dict[str, List[str]]:
    """프로젝트 소스에서 도메인 추정 signal 추출.
    (최소 scaffold — package.json·requirements.txt·README 키워드 매칭)"""
    signals = {}
    candidates = [
        ("package.json", "frontend"),
        ("tsconfig.json", "frontend"),
        ("requirements.txt", "backend"),
        ("pyproject.toml", "backend"),
        ("go.mod", "backend"),
        ("Dockerfile", "devops"),
        ("docker-compose.yml", "devops"),
        (".github/workflows", "devops"),
        ("terraform/", "cloud"),
        ("k8s/", "cloud"),
        ("README.md", None),
    ]
    for name, suggested_domain in candidates:
        p = project_path / name
        if p.exists():
            if suggested_domain:
                signals.setdefault(suggested_domain, []).append(name)
            if name == "README.md":
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore").lower()
                    kw_domain = {
                        "ocr": "document-ai", "mem0": "ai-memory", "rag": "search-rag",
                        "llm": "ai-model", "agent": "ai-agent", "mcp": "ai-agent",
                        "react": "frontend", "vue": "frontend", "svelte": "frontend",
                        "postgresql": "database", "mongodb": "database",
                        "oauth": "security", "jwt": "security",
                        "pytest": "quality-testing", "jest": "quality-testing",
                    }
                    for kw, dom in kw_domain.items():
                        if kw in text:
                            signals.setdefault(dom, []).append(f"README:{kw}")
                except Exception:
                    pass
    return signals


def analyze_project(project_path: str) -> Dict[str, Any]:
    """1. Project Discovery → 관련 도메인 자동 추정."""
    _ensure_schema()
    pp = Path(project_path).resolve()
    if not pp.exists():
        return {"ok": False, "reason": f"path 없음: {pp}"}

    signals = _detect_project_signals(pp)
    with sqlite3.connect(str(DB), timeout=10) as c:
        cur = c.execute(
            "INSERT INTO tech_discovery_runs "
            "(project_path, domains_scanned, evidence_count, gaps_found, innovations_proposed, "
            " started_at, status) VALUES (?, ?, 0, 0, 0, ?, 'running')",
            (str(pp), len(signals), int(time.time()))
        )
        run_id = cur.lastrowid

    out_file = STATE_DIR / f"analyze-{run_id}.json"
    out_file.write_text(
        json.dumps({"project_path": str(pp), "signals": signals, "run_id": run_id,
                    "ts": datetime.now().isoformat(timespec='seconds')},
                   ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return {"ok": True, "run_id": run_id, "signals": signals, "detected_domains": list(signals.keys()),
            "next": "research <domain> for each detected domain"}


def list_domains() -> List[Dict[str, Any]]:
    _ensure_schema()
    with sqlite3.connect(str(DB), timeout=10) as c:
        rows = c.execute(
            "SELECT domain_id, display_name, seed_capabilities FROM tech_domains ORDER BY domain_id"
        ).fetchall()
    return [{"domain_id": r[0], "display_name": r[1],
             "seed_capabilities": json.loads(r[2]) if r[2] else []} for r in rows]


def save_evidence(domain_id: str, topic: str, technology: str = "", capability: str = "",
                  source_url: str = "", version: str = "", confirmed_at: str = "",
                  summary: str = "") -> int:
    """3. Technology Research 결과 저장 (Claude 가 WebSearch 후 호출)."""
    _ensure_schema()
    now = int(time.time())
    with sqlite3.connect(str(DB), timeout=10) as c:
        cur = c.execute(
            "INSERT INTO tech_evidence "
            "(domain_id, topic, technology, capability, source_url, version, confirmed_at, summary, saved_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (domain_id, topic, technology, capability, source_url, version,
             confirmed_at or datetime.now().strftime("%Y-%m-%d"), summary, now)
        )
        return cur.lastrowid or 0


def save_gap(project_path: str, domain_id: str, as_is: str, to_be: str,
             gap_description: str, priority: str = "medium") -> int:
    """5. Gap Analysis 저장."""
    _ensure_schema()
    with sqlite3.connect(str(DB), timeout=10) as c:
        cur = c.execute(
            "INSERT INTO tech_gaps "
            "(project_path, domain_id, as_is, to_be, gap_description, priority, saved_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_path, domain_id, as_is, to_be, gap_description, priority, int(time.time()))
        )
        return cur.lastrowid or 0


def trigger_discovery_prompt(project_path: str, max_queries: int = 5) -> Dict[str, Any]:
    """R42 (R4) 2026-10-27 사용자 외부 AI 지시 "WebSearch 실제 연결" fix.

    tech_discovery.py 는 Python · WebSearch tool 직접 호출 불가 (Claude agent 전용).
    대신 Claude agent 가 받아서 수행할 **구조화된 WebSearch 지시 프롬프트** 생성.

    흐름:
        1. analyze_project() 로 도메인 추정
        2. 각 도메인별 WebSearch 쿼리 N개 생성
        3. prompt + queries dict 반환 → Claude agent 가 WebSearch 호출
        4. 결과를 save_evidence() 로 저장

    Returns:
        {
            "project": str,
            "domains": [...],
            "websearch_queries": [{"domain_id": ..., "queries": [...], "max_depth": N}],
            "instruction": "Claude agent: 각 query 에 WebSearch 호출 후 save_evidence 저장",
        }
    """
    analysis = analyze_project(project_path)
    queries = []
    for d in analysis.get("domains", []):
        did = d.get("id") if isinstance(d, dict) else d
        did = did or "unknown"
        queries.append({
            "domain_id": did,
            "queries": [
                f"{did} 최신 기술 2026",
                f"{did} 오픈소스 top 10 github",
                f"{did} AS-IS vs TO-BE 비교",
                f"{did} 경쟁 제품 비교 2026",
                f"{did} 신기능 로드맵",
            ][:max_queries],
            "max_depth": 2,
        })
    return {
        "project": str(project_path),
        "domains_detected": len(queries),
        "websearch_queries": queries,
        "instruction": (
            "Claude agent 는 각 query 에 WebSearch tool 을 호출하고 "
            "결과를 tech_discovery.save_evidence() 로 저장. "
            "evidence 저장 후 coverage_audit() 로 gap 측정 · gap 발견율 ≥30% 이면 "
            "supervisor.create_goal(workflow_type='REPAIR') 로 자동 백로그 생성."
        ),
        "next_step": "claude agent -> WebSearch -> save_evidence -> coverage_audit",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 12 (2026-10-30): 실제 조사 실행.
#   AS-IS = 프로젝트 manifest 의존성 + 설치 버전 (기술명 하드코딩 X)
#   조사 = headless Agent (WebSearch/WebFetch) · 근거(URL·확인일) 없는 결과는 저장 거부
#   후보 = gap 마다 tech_candidates(proposed) · approve_candidate 한 것만 goal 큐로
# ─────────────────────────────────────────────────────────────────────────────

def project_inventory(project_path: str) -> List[Dict[str, str]]:
    """requirements*.txt · pyproject [project].dependencies · package.json 에서 의존성 추출 + 설치 버전."""
    import re as _re
    pp = Path(project_path)
    deps: Dict[str, Dict[str, str]] = {}

    def add(name, spec, src):
        name = name.strip().lower()
        if name and name not in deps:
            deps[name] = {"name": name, "declared": spec.strip(), "source": src}
    for req in sorted(pp.glob("requirements*.txt")):
        for line in req.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.split("#")[0].split(";")[0].strip()
            m = _re.match(r"^([A-Za-z0-9_.\-\[\]]+)\s*(.*)$", line)
            if m:
                add(m.group(1).split("[")[0], m.group(2), req.name)
    pj = pp / "package.json"
    if pj.exists():
        try:
            d = json.loads(pj.read_text(encoding="utf-8"))
            for sec in ("dependencies", "devDependencies"):
                for k, v in (d.get(sec) or {}).items():
                    add(k, str(v), f"package.json:{sec}")
        except Exception:
            pass
    try:
        from importlib import metadata as _md
        for d in deps.values():
            try:
                d["installed"] = _md.version(d["name"])
            except Exception:
                d["installed"] = ""
    except Exception:
        pass
    return list(deps.values())


def _ensure_candidate_schema() -> None:
    with sqlite3.connect(str(DB), timeout=10) as c:
        c.execute("CREATE TABLE IF NOT EXISTS tech_candidates ("
                  " candidate_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER, gap_id INTEGER,"
                  " title TEXT NOT NULL, rationale TEXT, evidence_urls TEXT, priority TEXT,"
                  " status TEXT NOT NULL DEFAULT 'proposed', goal_id INTEGER,"
                  " created_at INTEGER NOT NULL, decided_at INTEGER, decided_by TEXT)")


def run_discovery(project_path: str, max_items: int = 5, model: str = "claude-sonnet-5-5",
                  dispatch=None) -> Dict[str, Any]:
    """analyze → inventory → Agent 웹 조사 → 근거 검증 → evidence/gap/candidate 저장."""
    sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
    if dispatch is None:
        import real_repair_chain as _rc
        dispatch = _rc.dispatch_agent
    _ensure_candidate_schema()
    an = analyze_project(project_path)
    if not an.get("ok"):
        return an
    run_id = an["run_id"]
    inv = project_inventory(project_path)
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = (
        f"Today is {today}. You are researching a software project's dependencies.\n"
        f"Detected domains: {an.get('detected_domains')}\n"
        f"Dependency inventory (name, declared constraint, installed version):\n"
        + "\n".join(f"- {d['name']} | {d['declared'] or '-'} | {d.get('installed') or 'not installed'}" for d in inv)
        + f"\n\nPick at most {max_items} dependencies where a newer release, deprecation, security fix or major "
        "capability change is most likely to matter. For each, use WebSearch/WebFetch to confirm from an official "
        "source (project docs, release notes, changelog, PyPI/npm page, security advisory). Do not guess versions.\n"
        "Reply with ONLY one JSON object:\n"
        '{"findings":[{"domain":"...","technology":"<dependency name>","latest_version":"...",'
        '"capability":"<what changed>","constraints":"<breaking changes / requirements>",'
        '"source_url":"https://...","checked_at":"YYYY-MM-DD"}],'
        '"gaps":[{"domain":"...","technology":"...","as_is":"<installed/declared>","to_be":"<target>",'
        '"description":"<why it matters for this project>","priority":"low|medium|high|critical",'
        '"evidence_urls":["<must be source_url values from findings>"]}]}'
    )
    ag = dispatch(prompt, str(ROOT), model, ["WebSearch", "WebFetch"], role="discovery",
                  timeout=900, max_budget_usd=3.0)
    m = __import__("re").search(r"\{.*\}", ag.get("result") or "", __import__("re").S)
    try:
        data = json.loads(m.group(0)) if m else {}
    except Exception:
        data = {}
    saved, rejected, candidates = [], [], []
    urls_ok = set()
    for f in data.get("findings") or []:
        url = (f.get("source_url") or "").strip()
        if not url.startswith(("https://", "http://")) or not f.get("technology"):
            rejected.append({"kind": "finding", "item": f, "reason": "no source_url/technology"})
            continue
        eid = save_evidence(f.get("domain") or "unknown", topic=f"dependency:{f['technology']}",
                            technology=f["technology"], capability=f.get("capability", ""), source_url=url,
                            version=f.get("latest_version", ""), confirmed_at=f.get("checked_at") or today,
                            summary=f.get("constraints", ""))
        urls_ok.add(url)
        saved.append({"evidence_id": eid, "technology": f["technology"], "version": f.get("latest_version"),
                      "source_url": url})
    now = int(time.time())
    for g in data.get("gaps") or []:
        ev = [u for u in g.get("evidence_urls") or [] if u in urls_ok]
        if not ev:
            rejected.append({"kind": "gap", "item": g, "reason": "evidence_urls not in verified findings"})
            continue
        pr = g.get("priority") if g.get("priority") in ("low", "medium", "high", "critical") else "medium"
        gid = save_gap(str(Path(project_path).resolve()), g.get("domain") or "unknown",
                       g.get("as_is", ""), g.get("to_be", ""), g.get("description", ""), pr)
        title = f"{g.get('technology')}: {g.get('as_is')} → {g.get('to_be')}"
        with sqlite3.connect(str(DB), timeout=10) as c:
            cid = c.execute("INSERT INTO tech_candidates (run_id, gap_id, title, rationale, evidence_urls, priority, "
                            "status, created_at) VALUES (?,?,?,?,?,?, 'proposed', ?)",
                            (run_id, gid, title, g.get("description", ""), json.dumps(ev), pr, now)).lastrowid
        candidates.append({"candidate_id": cid, "gap_id": gid, "title": title, "priority": pr})
    with sqlite3.connect(str(DB), timeout=10) as c:
        c.execute("UPDATE tech_discovery_runs SET evidence_count=?, gaps_found=?, ended_at=?, status=? WHERE run_id=?",
                  (len(saved), len(candidates), int(time.time()), "completed" if ag.get("ok") else "failed", run_id))
    result = {"ok": bool(ag.get("ok")) and bool(saved), "run_id": run_id, "inventory_size": len(inv),
              "agent_session_id": ag.get("agent_session_id"), "invocation": ag.get("invocation"),
              "cost_usd": ag.get("cost_usd"), "num_turns": ag.get("num_turns"), "evidence": saved,
              "candidates": candidates, "rejected": rejected, "agent_result_tail": (ag.get("result") or "")[-1500:]}
    (STATE_DIR / f"discovery-{run_id}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                                        encoding="utf-8")
    return result


def approve_candidate(candidate_id: int, approved_by: str) -> Dict[str, Any]:
    """승인된 후보만 goal 큐로 (source_ref=discovery:<id>). 이미 결정된 후보는 재처리 X."""
    _ensure_candidate_schema()
    sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
    import supervisor as _sup
    with sqlite3.connect(str(DB), timeout=10) as c:
        row = c.execute("SELECT title, rationale, evidence_urls, status FROM tech_candidates WHERE candidate_id=?",
                        (candidate_id,)).fetchone()
    if not row:
        return {"ok": False, "reason": "candidate not found"}
    if row[3] != "proposed":
        return {"ok": False, "reason": f"already {row[3]}"}
    gid = _sup.create_goal(f"[discovery] {row[0]} · {row[1][:200]} · evidence: {row[2]}", max_retry=1,
                           timeout_h=72, source_ref=f"discovery:{candidate_id}")
    with sqlite3.connect(str(DB), timeout=10) as c:
        c.execute("UPDATE tech_candidates SET status='approved', goal_id=?, decided_at=?, decided_by=? "
                  "WHERE candidate_id=?", (gid, int(time.time()), approved_by, candidate_id))
    return {"ok": True, "candidate_id": candidate_id, "goal_id": gid}


def coverage_audit(run_id: int) -> Dict[str, Any]:
    """Coverage Gate: 조사가 상위 20 도메인 중 얼마나 포괄? 핵심 영역 누락?"""
    _ensure_schema()
    with sqlite3.connect(str(DB), timeout=10) as c:
        row = c.execute(
            "SELECT project_path, domains_scanned FROM tech_discovery_runs WHERE run_id=?",
            (run_id,)
        ).fetchone()
        if not row:
            return {"ok": False, "reason": "run 없음"}
        project_path, domains_scanned = row
        # 각 도메인별 evidence·gap 개수
        rows = c.execute(
            "SELECT d.domain_id, "
            "COALESCE((SELECT COUNT(*) FROM tech_evidence e WHERE e.domain_id=d.domain_id),0), "
            "COALESCE((SELECT COUNT(*) FROM tech_gaps g WHERE g.domain_id=d.domain_id AND g.project_path=?),0) "
            "FROM tech_domains d",
            (project_path,)
        ).fetchall()
    covered = sum(1 for r in rows if r[1] > 0)
    total = len(rows)
    coverage_pct = (covered / total * 100) if total else 0
    missing = [r[0] for r in rows if r[1] == 0]
    return {
        "ok": True,
        "run_id": run_id,
        "coverage_pct": round(coverage_pct, 1),
        "covered_domains": covered,
        "total_domains": total,
        "missing_domains": missing[:10],
        "gate_pass": coverage_pct >= 30,  # 상위 30% 이상 커버 시 pass (설정 가능)
    }


def summary_report(project_path: str = "") -> Dict[str, Any]:
    _ensure_schema()
    with sqlite3.connect(str(DB), timeout=10) as c:
        where = "WHERE project_path=?" if project_path else ""
        params = (project_path,) if project_path else ()
        runs = c.execute(
            f"SELECT run_id, project_path, status, started_at FROM tech_discovery_runs {where} "
            f"ORDER BY started_at DESC LIMIT 5", params
        ).fetchall()
        evidence_total = c.execute("SELECT COUNT(*) FROM tech_evidence").fetchone()[0]
        gaps_total = c.execute(
            "SELECT COUNT(*) FROM tech_gaps" + (" WHERE project_path=?" if project_path else ""),
            params
        ).fetchone()[0]
    return {
        "recent_runs": [{"run_id": r[0], "project": r[1][:50], "status": r[2],
                         "started": datetime.fromtimestamp(r[3]).isoformat(timespec='seconds')} for r in runs],
        "total_evidence": evidence_total,
        "total_gaps": gaps_total,
    }


def main(argv):
    if len(argv) < 2:
        print("usage: tech_discovery.py {analyze|domain-list|evidence|gap|coverage|summary|ensure}")
        return 2
    cmd = argv[1]
    if cmd == "discover":
        mx = int(argv[argv.index("--max") + 1]) if "--max" in argv else 5
        print(json.dumps(run_discovery(argv[2] if len(argv) > 2 and not argv[2].startswith("--") else str(ROOT),
                                       max_items=mx), ensure_ascii=False, indent=2))
        return 0
    if cmd == "approve-candidate":
        by = argv[argv.index("--by") + 1] if "--by" in argv else "manual"
        print(json.dumps(approve_candidate(int(argv[2]), by), ensure_ascii=False, indent=2))
        return 0
    if cmd == "candidates":
        _ensure_candidate_schema()
        with sqlite3.connect(str(DB), timeout=10) as c:
            rows = c.execute("SELECT candidate_id, run_id, title, priority, status, goal_id FROM tech_candidates "
                             "ORDER BY candidate_id DESC LIMIT 30").fetchall()
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    if cmd == "ensure":
        _ensure_schema()
        print("[tech_discovery] schema ensured · 20 seed domains loaded")
        return 0
    if cmd == "analyze":
        if len(argv) < 3:
            print("usage: tech_discovery.py analyze <project_path>")
            return 2
        r = analyze_project(argv[2])
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    if cmd == "trigger":
        if len(argv) < 3:
            print("usage: tech_discovery.py trigger <project_path> [--max-queries N]")
            return 2
        max_q = 5
        if "--max-queries" in argv:
            i = argv.index("--max-queries")
            if i + 1 < len(argv):
                max_q = int(argv[i + 1])
        print(json.dumps(trigger_discovery_prompt(argv[2], max_q), ensure_ascii=False, indent=2))
        return 0
    if cmd == "domain-list":
        print(json.dumps(list_domains(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "evidence":
        kw = {argv[i].lstrip("-").replace("-", "_"): argv[i+1] for i in range(2, len(argv)-1, 2) if argv[i].startswith("--")}
        eid = save_evidence(**kw)
        print(json.dumps({"evidence_id": eid, "ok": eid > 0}, ensure_ascii=False))
        return 0 if eid > 0 else 1
    if cmd == "gap":
        kw = {argv[i].lstrip("-").replace("-", "_"): argv[i+1] for i in range(2, len(argv)-1, 2) if argv[i].startswith("--")}
        gid = save_gap(**kw)
        print(json.dumps({"gap_id": gid, "ok": gid > 0}, ensure_ascii=False))
        return 0 if gid > 0 else 1
    if cmd == "coverage":
        if len(argv) < 3:
            print("usage: tech_discovery.py coverage <run_id>")
            return 2
        r = coverage_audit(int(argv[2]))
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("gate_pass") else 1
    if cmd == "summary":
        pp = argv[2] if len(argv) > 2 else ""
        print(json.dumps(summary_report(pp), ensure_ascii=False, indent=2))
        return 0
    print(f"unknown cmd: {cmd}")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[tech_discovery] fatal: {e}", file=sys.stderr)
        sys.exit(1)
