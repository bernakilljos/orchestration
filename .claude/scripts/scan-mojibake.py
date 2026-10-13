#!/usr/bin/env python3
"""?꾩껜 ?꾨줈?앺듃 mojibake (?쒓? 源⑥쭚) ?ㅼ틪"""
import sys, re
from pathlib import Path

try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

MOJIBAKE_PATTERNS = [
    re.compile(r'[횂횄][\x80-\xBF]{2,}'),
    re.compile(r'[챠챙챤챦챨챰챵처]{2,}'),
    re.compile(r'\\u[0-9a-f]{4}\\u[0-9a-f]{4}'),
]
REPL = '\ufffd'
SKIP_DIRS = ['.git', 'node_modules', 'outputs', '.claude/logs', 'docs/upgrade', 'setup/Output', '.claude/context-cache']
SKIP_EXTS = {'.pyc', '.pptx', '.xlsx', '.docx', '.pdf', '.zip', '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.wav', '.exe', '.dll', '.log', '.m4a'}

hits = []
for path in Path('.').rglob('*'):
    if not path.is_file():
        continue
    path_str = str(path).replace('\\', '/')
    if any(s in path_str for s in SKIP_DIRS):
        continue
    if path.suffix.lower() in SKIP_EXTS:
        continue
    try:
        if path.stat().st_size > 500_000:
            continue
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        continue
    try:
        txt = path.read_text(encoding='utf-8')
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        continue
    if REPL in txt:
        hits.append((path_str, 'REPL_CHAR', txt.count(REPL)))
        continue
    for pat in MOJIBAKE_PATTERNS:
        m = pat.search(txt)
        if m:
            hits.append((path_str, f'{m.group()[:30]}', 1))
            break

print(f"=== Mojibake ?ㅼ틪: {len(hits)} 嫄?===\n")
for p, pat, cnt in hits[:60]:
    print(f"  {p}  [{pat}] x{cnt}")

if not hits:
    print("[OK] ?꾨줈?앺듃 ??mojibake ?놁쓬")
else:
    print(f"\n珥?{len(hits)} ?뚯씪 ??git checkout HEAD -- <file> 濡?蹂듦뎄 寃??)

