"""R354 27차 — 게시된 CI 증거(R354-ci-runs.json)를 GitHub Actions API 원본과 다시 대조.

push 이벤트 run/job 의 head_sha·event·conclusion 을 원본과 비교하고, job 을 범주별로 나눠
success / skipped / failure 를 구분한다. skipped 는 통과로 세지 않는다.
Linux 시험 job 의 pytest 단계 결론도 따로 적는다 (Linux pytest 는 continue-on-error 라 job success 가 시험 통과를 뜻하지 않을 수 있음).
사용: python -X utf8 .ai-collab/evidence/R354-ci-crosscheck.py <40자리 SHA> [...]
"""
import json, pathlib, sys, urllib.request

R = 'https://api.github.com/repos/bernakilljos/orchestration'
POSTED = pathlib.Path(__file__).with_name('R354-ci-runs.json')


def g(u):
    req = urllib.request.Request(u, headers={'User-Agent': 'ci-crosscheck', 'Accept': 'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req, timeout=30))


def category(name):
    n = name.lower()
    if 'windows' in n:
        return 'Windows 필수'
    if n.startswith('test python'):
        return 'Linux ' + name.split()[-1]
    if 'lint' in n:
        return 'Lint'
    if 'pr security comment' in n:
        return 'PR 코멘트 (push 에선 실행 안 함)'
    if 'security' in n:
        return 'Security'
    if 'dependenc' in n:
        return 'Dependency'
    return '기타'


posted = json.loads(POSTED.read_text(encoding='utf-8'))['commits']
out = {}
for sha in sys.argv[1:]:
    p_jobs = {j['id']: j for r in posted.get(sha, {}).get('runs', []) for j in r.get('jobs', [])}
    rows, mismatch = [], []
    runs = g(f'{R}/actions/runs?head_sha={sha}&event=push')['workflow_runs']
    for run in sorted(runs, key=lambda x: x['name']):
        for j in sorted(g(f"{R}/actions/runs/{run['id']}/jobs")['jobs'], key=lambda x: x['name']):
            test_steps = [f"{s['name']}={s['conclusion']}" for s in j.get('steps', []) if 'pytest' in s['name'].lower() or '시험' in s['name']]
            row = {'workflow': run['name'], 'run_id': run['id'], 'event': run['event'], 'run_head_sha': run['head_sha'],
                   'job': j['name'], 'job_id': j['id'], 'job_head_sha': j['head_sha'], 'conclusion': j['conclusion'],
                   'category': category(j['name']), 'test_steps': test_steps, 'html_url': j['html_url']}
            pj = p_jobs.get(j['id'])
            if pj is None:
                mismatch.append(f"게시본에 없음: job {j['id']} {j['name']}")
            else:
                for k in ('head_sha', 'conclusion', 'name'):
                    if pj.get(k) != j.get(k):
                        mismatch.append(f"job {j['id']} {k}: 게시={pj.get(k)} 원본={j.get(k)}")
            if run['event'] != 'push' or run['head_sha'] != sha or j['head_sha'] != sha:
                mismatch.append(f"job {j['id']} SHA/이벤트 불일치")
            rows.append(row)
    missing = set(p_jobs) - {r['job_id'] for r in rows}
    mismatch += [f'원본에 없음: job {i}' for i in sorted(missing)]
    summary = {}
    for r in rows:
        summary.setdefault(r['conclusion'] or 'pending', []).append(r['category'])
    out[sha] = {'runs': len(runs), 'jobs': rows, 'by_conclusion': summary, 'mismatches': mismatch,
                'verdict': '게시본 = 원본' if rows and not mismatch else '불일치 또는 원본 없음'}
print(json.dumps(out, ensure_ascii=False, indent=1))
