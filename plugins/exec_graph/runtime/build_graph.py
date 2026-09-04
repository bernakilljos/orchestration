#!/usr/bin/env python
"""build_graph.py — yaml graph spec -> langgraph StateGraph

Usage:
    python build_graph.py <spec.yaml>

Returns: langgraph CompiledGraph 객체 (run_graph.py 에서 invoke).
"""
import sys
import yaml
from pathlib import Path
from typing import TypedDict, Annotated
from operator import add

try:
    from langgraph.graph import StateGraph, START, END
except ImportError:
    print("[FAIL] langgraph 미설치 — pip install langgraph langchain langchain-anthropic")
    sys.exit(1)


def load_spec(spec_path):
    """yaml spec 파싱"""
    with open(spec_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_state_class(state_def):
    """spec.state 정의 -> TypedDict 동적 생성"""
    fields = {}
    for field in state_def:
        # field: dict like {"input": "str"} or {"critiques": "list[str]"}
        for name, type_hint in field.items():
            if type_hint == "str":
                fields[name] = str
            elif type_hint == "list[str]":
                fields[name] = Annotated[list, add]  # parallel append
            elif type_hint.startswith("list"):
                fields[name] = list
            else:
                fields[name] = str  # default
    return TypedDict("GraphState", fields)


def make_node_fn(node_def):
    """node 정의 -> 실행 함수 (mock — 실제 LLM 호출은 사용자 구현)

    실제 호출 패턴 (placeholder):
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=node_def["agent"])
        result = llm.invoke(prompt.format(**state))
    """
    node_id = node_def["id"]
    agent = node_def.get("agent", "claude-opus-4-8")
    prompt_tpl = node_def.get("prompt", "")

    def node_fn(state):
        # POC: prompt template 변수 치환 + 결과 state 갱신
        # 실제 LLM 호출은 사용자가 langchain_anthropic 등으로 구현
        rendered = prompt_tpl
        for k, v in state.items():
            rendered = rendered.replace("{" + k + "}", str(v))

        # POC 모드: dry-run 결과
        result = f"[{node_id} via {agent}] would process: {rendered[:80]}..."

        # 상태 갱신 키 = node_id (또는 spec 의 state field name)
        # multi-angle-verify 예시: draft -> state["draft"], critique-1 -> state["critiques"]
        if node_id == "draft":
            return {"draft": result}
        elif node_id.startswith("critique"):
            return {"critiques": [result]}
        elif node_id == "synthesize":
            return {"final": result}
        else:
            return {node_id: result}

    return node_fn


def build_graph(spec):
    """spec -> CompiledGraph"""
    State = build_state_class(spec.get("state", [{"input": "str"}]))
    graph = StateGraph(State)

    # nodes 등록
    for node in spec["nodes"]:
        graph.add_node(node["id"], make_node_fn(node))

    # edges 등록 (START -> first node, last node -> END 자동)
    first_node = spec["nodes"][0]["id"]
    last_node = spec["nodes"][-1]["id"]
    graph.add_edge(START, first_node)

    # spec.edges 처리
    for edge in spec.get("edges", []):
        src = edge["from"]
        dst = edge["to"]
        if isinstance(src, list) and isinstance(dst, str):
            # fan-in (parallel -> single)
            for s in src:
                graph.add_edge(s, dst)
        elif isinstance(src, str) and isinstance(dst, list):
            # fan-out (single -> parallel)
            for d in dst:
                graph.add_edge(src, d)
        elif isinstance(src, str) and isinstance(dst, str):
            graph.add_edge(src, dst)

    graph.add_edge(last_node, END)
    return graph.compile()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_graph.py <spec.yaml>")
        sys.exit(1)
    spec = load_spec(sys.argv[1])
    compiled = build_graph(spec)
    print(f"[OK] graph built: {spec['name']} ({len(spec['nodes'])} nodes)")
