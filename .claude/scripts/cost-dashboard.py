"""비용-활성 대시보드 — orca.db 데이터 HTML 시각화.

generates: .claude/state/dashboard.html (열면 시각화 표시)
"""
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB = PROJECT_ROOT / ".claude" / "state" / "orca.db"
OUT = PROJECT_ROOT / ".claude" / "state" / "dashboard.html"


def query_all():
    if not DB.exists():
        return {"error": "orca.db not found"}
    conn = sqlite3.connect(str(DB))
    data = {}
    # 최근 24h decisions
    try:
        cur = conn.execute("SELECT ai_classified, COUNT(*) FROM decisions WHERE ts >= datetime('now','-24 hours') GROUP BY ai_classified")
        data["decisions_24h"] = dict(cur.fetchall())
    except Exception:
        data["decisions_24h"] = {}
    # activations top
    try:
        cur = conn.execute("SELECT layer, name, COUNT(*), AVG(duration_ms) FROM activations GROUP BY layer, name ORDER BY COUNT(*) DESC LIMIT 10")
        data["activations_top"] = [{"layer": r[0], "name": r[1], "count": r[2], "avg_ms": round(r[3] or 0, 1)} for r in cur.fetchall()]
    except Exception:
        data["activations_top"] = []
    # determinism warning
    try:
        cur = conn.execute("SELECT prompt_hash, COUNT(DISTINCT result_hash), COUNT(*) FROM determinism WHERE result_hash != '' GROUP BY prompt_hash HAVING COUNT(DISTINCT result_hash) > 1 LIMIT 5")
        data["determinism_issues"] = [{"hash": r[0], "unique": r[1], "total": r[2]} for r in cur.fetchall()]
    except Exception:
        data["determinism_issues"] = []
    conn.close()
    return data


def render(data: dict) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>orchestration_v1 Dashboard</title>
<style>
body {{ font-family:'Segoe UI',sans-serif; padding:30px; background:#F5F8FC; }}
h1 {{ color:#1F3864; }}
.card {{ background:white; padding:20px; border-radius:14px; box-shadow:0 4px 16px rgba(0,0,0,0.08); margin-bottom:20px; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ background:#1F3864; color:white; padding:10px; text-align:left; }}
td {{ padding:8px; border-bottom:1px solid #eee; }}
.warn {{ color:#C00000; font-weight:700; }}
</style></head><body>
<h1>[STAT] orchestration_v1 Dashboard</h1>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

<div class="card">
  <h2>[TGT] Decisions (24h) — AI 분류 분포</h2>
  <table><tr><th>AI</th><th>호출 수</th></tr>
  {''.join(f'<tr><td>{ai}</td><td>{n}</td></tr>' for ai, n in data.get('decisions_24h', {}).items())}
  </table>
</div>

<div class="card">
  <h2>[FAST] Activations Top 10 — Skill/Hook/Subagent</h2>
  <table><tr><th>Layer</th><th>Name</th><th>Count</th><th>Avg ms</th></tr>
  {''.join(f'<tr><td>{r["layer"]}</td><td>{r["name"]}</td><td>{r["count"]}</td><td>{r["avg_ms"]}</td></tr>' for r in data.get('activations_top', []))}
  </table>
</div>

<div class="card">
  <h2>[WARN] Non-Determinism Issues</h2>
  {f'<p class="warn">{len(data.get("determinism_issues", []))} 개 prompt 가 다른 결과 반환</p>' if data.get('determinism_issues') else '<p>[OK] 모두 결정론적</p>'}
  <table><tr><th>prompt_hash</th><th>unique 결과</th><th>total 실행</th></tr>
  {''.join(f'<tr><td>{r["hash"]}</td><td>{r["unique"]}</td><td>{r["total"]}</td></tr>' for r in data.get('determinism_issues', []))}
  </table>
</div>

</body></html>"""


if __name__ == "__main__":
    data = query_all()
    html = render(data)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(json.dumps({"dashboard": str(OUT), "data_summary": {k: len(v) if isinstance(v, (list, dict)) else v for k, v in data.items()}}, ensure_ascii=False, indent=2))
