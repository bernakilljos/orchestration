"""R354 27차 — 세 대상의 실제 활성 SessionStart 에서 memory_guard 가 실행된 기록을 읽기 전용으로 수집.

출처: Claude Code 세션 기록(jsonl)의 async_hook_response 첨부 (stdout·stderr·exitCode·hookName·command).
활성 스크립트 해시: 실행 시각이 현재 설치본의 수정 시각 이후면 그 실행은 현재 설치본(해시 기록)으로 본다.
그보다 앞선 실행은 '이전 설치본' 으로만 표시한다 (그 시점 해시는 알 수 없음 = 미관측).
운영 파일·설정·로그에 쓰지 않는다. 사용자 홈 경로는 %USERPROFILE% 로 가린다.
"""
import datetime, hashlib, json, os, pathlib, re

TARGETS = {
    'orchestration_v1': os.environ.get('R354_KIT', 'C:/pjt/orchestration_v1'),
    'IFRS_PJT': os.environ.get('R354_IFRS', 'C:/IFRS_PJT'),
    'ICMAI_PJT': os.environ.get('R354_ICMAI', 'C:/ICMAI_PJT'),
}
HOME = pathlib.Path.home()
PROJ = HOME / '.claude' / 'projects'


def mask(s):
    for v in {str(HOME), str(HOME).replace('\\', '/'), str(HOME).replace('\\', '\\\\')}:
        s = s.replace(v, '%USERPROFILE%')
    return re.sub(r'/c/Users/[^/\s]+', '/c/Users/%USERNAME%', s)


def proj_key(path):
    return re.sub(r'[^A-Za-z0-9]', '-', str(pathlib.Path(path)))


res = {'fetched_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'targets': {}}
for name, t in TARGETS.items():
    T = pathlib.Path(t)
    sh = T / 'plugins/exec_orch/hooks/memory_guard.sh'
    st = sh.stat()
    installed = {
        'sha256_12': hashlib.sha256(sh.read_bytes()).hexdigest()[:12],
        'mtime_utc': datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat(timespec='seconds'),
    }
    pdir = PROJ / proj_key(T)
    recs = []
    for f in sorted(pdir.glob('*.jsonl')) if pdir.is_dir() else []:
        with open(f, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                if '"async_hook_response"' not in line or 'memory_guard' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                a = o.get('attachment') or {}
                if a.get('type') != 'async_hook_response' or 'memory_guard' not in a.get('command', ''):
                    continue
                ts = o.get('timestamp', '')
                when = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')) if ts else None
                m = re.search(r'대상 프로젝트: (\S+)', a.get('stdout', ''))
                recs.append({
                    'timestamp': ts, 'session': f.stem[:8], 'cli_version': o.get('version'),
                    'hookName': a.get('hookName'), 'command': a.get('command'), 'exitCode': a.get('exitCode'),
                    'target_project_line': mask(m.group(1)) if m else None,
                    'stdout': mask(a.get('stdout', '')), 'stderr': mask(a.get('stderr', '')),
                    'script': ('현재 설치본 ' + installed['sha256_12']) if when and when.timestamp() >= st.st_mtime
                              else '이전 설치본 (그 시점 해시 미관측)',
                })
    log = T / '.claude/logs/memory-guard.log'
    tail = mask(log.read_text(encoding='utf-8', errors='replace')).splitlines()[-5:] if log.exists() else []
    cur = [r for r in recs if r['script'].startswith('현재')]
    res['targets'][name] = {
        'installed_script': installed,
        'session_dir_exists': pdir.is_dir(),
        'records_total': len(recs),
        'records_current_script': len(cur),
        'status': '관측' if cur else ('이전 설치본만 관측' if recs else '미관측 (활성 세션 기록 0건 · 오류 없음/정상의 근거 아님)'),
        'records': recs[-5:],
        'memory_guard_log_tail': tail,
    }
print(json.dumps(res, ensure_ascii=False, indent=1))
