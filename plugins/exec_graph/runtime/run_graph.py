#!/usr/bin/env python
"""run_graph.py — graph spec 실행 + state.json 저장

Usage:
    python run_graph.py <spec.yaml> [--input "<text>"]
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from build_graph import load_spec, build_graph


def run(spec_path, user_input=""):
    spec = load_spec(spec_path)
    graph = build_graph(spec)

    # 초기 state — list 우선 체크 (list[str] 가 "str" 포함이라 순서 중요)
    initial = {"input": user_input}
    for field in spec.get("state", []):
        for name, type_hint in field.items():
            if name in initial:
                continue
            t = str(type_hint)
            if "list" in t:
                initial[name] = []
            elif "str" in t:
                initial[name] = ""
            else:
                initial[name] = None

    # 실행
    final_state = graph.invoke(initial)

    # 결과 저장
    project_root = Path(__file__).resolve().parents[3]
    out_dir = project_root / ".claude" / "state" / "graph-runs" / f"{spec['name']}-{datetime.now():%Y%m%d-%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "state.json").write_text(
        json.dumps(final_state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "spec.yaml.copy").write_text(
        Path(spec_path).read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    print(f"[OK] graph run done")
    print(f"  spec: {spec['name']}")
    print(f"  out:  {out_dir}")
    print(f"  state keys: {list(final_state.keys())}")
    return final_state


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", help="yaml spec path")
    parser.add_argument("--input", default="POC test input", help="initial input")
    args = parser.parse_args()
    run(args.spec, args.input)
