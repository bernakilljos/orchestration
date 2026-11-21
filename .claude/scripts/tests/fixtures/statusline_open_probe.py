"""상태줄 1회 실행 중 실제로 연 저장소 소스 파일 목록 (test_r348_perf_trigger 용 · 읽기 전용).
감사 훅 open 이벤트 = import·spec_from_file_location·runpy 가 여는 .py / __pycache__ .pyc 모두 잡힘."""
import io
import json
import os
import re
import runpy
import sys

root = os.path.abspath(sys.argv[1])
seen = set()


def hook(ev, args):
    if ev == "open" and args and isinstance(args[0], str):
        p = os.path.abspath(args[0])
        if p.startswith(root) and p.endswith((".py", ".pyc")):
            seen.add(p)


sys.addaudithook(hook)
target = os.path.join(root, ".claude", "scripts", "statusline_context.py")
sys.stdin = io.StringIO("{}")
sys.argv = [target]
real = sys.stdout
sys.stdout = io.StringIO()
try:
    runpy.run_path(target, run_name="__main__")
except SystemExit:
    pass
sys.stdout = real
PYC = re.compile(r"^(.*)[\\/]__pycache__[\\/]([^.\\/]+)\.[^\\/]+\.pyc$")
out = set()
for p in seen:
    m = PYC.match(p)
    out.add(os.path.join(m.group(1), m.group(2) + ".py") if m else p)
print(json.dumps(sorted(os.path.relpath(p, root).replace(os.sep, "/") for p in out)))
