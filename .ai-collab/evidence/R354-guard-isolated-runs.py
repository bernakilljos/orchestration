"""대상 실제 설치본 memory_guard.sh 를 격리 사본에서 실제 등록 명령 원문으로 실행 (운영 폴더 불변 확인)."""
import hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile, datetime
sys.path.insert(0, '.claude/hooks/prompt'); from _common import bash_exe
TARGETS = ['C:/pjt/orchestration_v1', 'C:/IFRS_PJT', 'C:/ICMAI_PJT']
def tree_sig(t):
    # 보호 대상 = memory_guard 가 쓸 수 있는 곳 (기록 파일·data·설정·스크립트) · .claude/state 는 다른 세션이 계속 쓰므로 비교 대상 아님
    T = pathlib.Path(t); h = hashlib.sha256(); n = 0
    for rel in ('.claude/logs/memory-guard.log', 'data', '.claude/settings.json', '.claude/settings.local.json',
                'plugins/exec_orch/hooks/memory_guard.sh', '.claude/hooks/memory_guard.sh'):
        P = T / rel
        files = [P] if P.is_file() else (sorted(x for x in P.rglob('*') if x.is_file()) if P.is_dir() else [])
        h.update(f'{rel}:{"exists" if P.exists() else "absent"}'.encode())
        for f in files:
            h.update(str(f).encode()); h.update(f.read_bytes()); n += 1
    return h.hexdigest()[:16], n
res = {'fetched_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'bash': 'Git Bash (_common.bash_exe)', 'targets': {}}
for t in TARGETS:
    T = pathlib.Path(t)
    cfg = json.loads((T / '.claude/settings.json').read_text(encoding='utf-8'))
    reg = [h for ev, gs in cfg['hooks'].items() if ev == 'SessionStart' for g in gs for h in g.get('hooks', []) if 'memory_guard' in h.get('command', '')]
    cmd = reg[0]['command']
    script = (T / 'plugins/exec_orch/hooks/memory_guard.sh').read_bytes()
    before_log = (T / '.claude/logs/memory-guard.log').read_bytes() if (T / '.claude/logs/memory-guard.log').exists() else b''
    sig0 = tree_sig(t)
    runs = {}
    with tempfile.TemporaryDirectory() as d:
        D = pathlib.Path(d); home = D / 'home'; home.mkdir()
        cp = home / 'copy'; (cp / '.claude').mkdir(parents=True)
        shutil.copyfile(T / '.claude/settings.json', cp / '.claude/settings.json')
        (cp / 'plugins/exec_orch/hooks').mkdir(parents=True)
        (cp / 'plugins/exec_orch/hooks/memory_guard.sh').write_bytes(script)
        other = home / 'other'; (other / '.claude').mkdir(parents=True); (other / '.claude/settings.json').write_text('{}')
        (other / 'data').mkdir(); (other / 'data/strategy_memory.json').write_text('[{"id":"x"}]')
        base = {k: v for k, v in os.environ.items() if k not in ('CLAUDE_PROJECT_DIR', 'MEMORY_GUARD_ALLOW_FOREIGN_PROJECT')}
        base.update(HOME=str(home), TMPDIR=str(home))
        def run(name, env_extra, command=None, data=False):
            if data:
                (cp / 'data').mkdir(exist_ok=True); (cp / 'data/strategy_memory.json').write_text('[{"id":"a"},{"id":"b"},{"id":"c"}]')
            e = dict(base); e.update(env_extra)
            p = subprocess.run([bash_exe(), '-c', command or cmd], env=e, cwd=str(home), capture_output=True, timeout=60)
            log = cp / '.claude/logs/memory-guard.log'
            runs[name] = {'rc': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace'), 'stderr': p.stderr.decode('utf-8', 'replace'),
                          'copy_log_lines': log.read_text(encoding='utf-8').count('\n') if log.exists() else 0}
        cpd = str(cp)
        run('1_정상_데이터없음(운영과 같은 상태)', {'CLAUDE_PROJECT_DIR': cpd})
        run('2_env_다른_프로젝트', {'CLAUDE_PROJECT_DIR': str(other)}, f'bash "{cpd}/plugins/exec_orch/hooks/memory_guard.sh"')
        run('3_env_다른_프로젝트+명시적허용', {'CLAUDE_PROJECT_DIR': str(other), 'MEMORY_GUARD_ALLOW_FOREIGN_PROJECT': '1'}, f'bash "{cpd}/plugins/exec_orch/hooks/memory_guard.sh"')
        run('4_env_누락', {}, f'bash "{cpd}/plugins/exec_orch/hooks/memory_guard.sh"')
        run('5_env_없는_폴더', {'CLAUDE_PROJECT_DIR': str(home / "no-such")}, f'bash "{cpd}/plugins/exec_orch/hooks/memory_guard.sh"')
        (cp / '.claude/logs').mkdir(parents=True, exist_ok=True); shutil.move(str(cp / '.claude/logs'), str(home / 'logs-moved'))
        (cp / '.claude/logs').write_text('not a dir')
        run('6_기록_실패', {'CLAUDE_PROJECT_DIR': cpd})
        (cp / '.claude/logs').unlink()
        run('7_정상_데이터있음', {'CLAUDE_PROJECT_DIR': cpd}, data=True)
    sig1 = tree_sig(t)
    after_log = (T / '.claude/logs/memory-guard.log').read_bytes() if (T / '.claude/logs/memory-guard.log').exists() else b''
    res['targets'][t] = {'registration': reg[0], 'script_md5_12': hashlib.md5(script).hexdigest()[:12],
                         'ops_signature_before': sig0, 'ops_signature_after': sig1, 'ops_unchanged': sig0 == sig1 and before_log == after_log,
                         'ops_memory_guard_log_lines': after_log.count(b'\n'), 'runs': runs}
out = pathlib.Path('.ai-collab/evidence/R354-guard-isolated-runs.json')
out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
for t, v in res['targets'].items():
    print(t, v['script_md5_12'], 'ops_unchanged=', v['ops_unchanged'], v['ops_signature_before'])
    for k, r in v['runs'].items():
        first = [l for l in r['stdout'].splitlines() if l.startswith(('[SKIP]', '[INFO] 대상', '[INFO] 전략'))][:2]
        print('  ', k, 'rc', r['rc'], first, '| err:', r['stderr'].strip().splitlines()[:1], '| copylog', r['copy_log_lines'])
