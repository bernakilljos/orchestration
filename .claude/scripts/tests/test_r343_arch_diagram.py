"""R342·R343 근거 기반 아키텍처 도식 엔진 — 사실 원본(spec)에 없는 노드·연결을 그리지 않고, 근거 없는 요소는 거부(또는 [미확인]),
서로 다른 주제 3종에서 장수·포트·저장소가 spec 대로 바뀌며 다른 문서·특정 제품 값이 새어 들어가지 않는다 (렌더 없이 PPTX 텍스트로 확인)."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).resolve().parent / "fixtures" / "arch"
spec_mod = importlib.util.spec_from_file_location("arch_diagram_pptx", ROOT / ".claude" / "scripts" / "arch-diagram-pptx.py")
ad = importlib.util.module_from_spec(spec_mod)
spec_mod.loader.exec_module(ad)
pptx = pytest.importorskip("pptx")


def _load(n):
    return json.loads((FIX / f"spec_{n}.json").read_text(encoding="utf-8"))


def _text(path):
    return " ".join(sh.text_frame.text for s in pptx.Presentation(str(path)).slides for sh in s.shapes if sh.has_text_frame)


def test_unsourced_elements_refused_or_marked(tmp_path):
    c = _load("C")                                            # 보안 로그 수집 노드·연결에 source 없음
    with pytest.raises(ad.SpecError) as e:
        ad.render(c, str(tmp_path / "c.pptx"))
    assert "근거(source) 없는 요소 2개" in str(e.value) and not (tmp_path / "c.pptx").exists()
    r = ad.render(c, str(tmp_path / "c.pptx"), allow_unverified=True)
    assert set(r["unverified"]) == {"container:siem", "container:con→siem"}
    assert _text(tmp_path / "c.pptx").count("[미확인]") >= 2


def test_structure_errors_rejected():
    bad = {"views": [{"type": "container", "nodes": [{"id": "a", "label": "A", "source": "s"}],
                      "edges": [{"from": "a", "to": "ghost", "label": "x", "source": "s"}]}]}
    with pytest.raises(ad.SpecError, match="연결 끝점 노드 없음: ghost"):
        ad.validate(bad)
    with pytest.raises(ad.SpecError, match="노드 id 중복"):
        ad.validate({"views": [{"type": "container", "nodes": [{"id": "a", "source": "s"}, {"id": "a", "source": "s"}]}]})


def test_three_topics_dynamic_and_no_leak(tmp_path):
    texts, slides = {}, {}
    for n in "ABC":
        r = ad.render(_load(n), str(tmp_path / f"{n}.pptx"), allow_unverified=(n == "C"))
        texts[n], slides[n] = _text(tmp_path / f"{n}.pptx"), r["slides"]
        assert all(cl["source"] for cl in r["claims"])         # 모든 요소에 근거(또는 미확인) 기록
    assert slides == {"A": 1, "B": 2, "C": 1}                  # 장수는 spec 의 view 수대로
    own = {"A": ["7443", "RabbitMQ"], "B": ["Oracle 19c", "PostgreSQL 16"], "C": ["51820", "6006"]}
    for n, marks in own.items():
        assert all(m in texts[n] for m in marks)
        for other in "ABC":
            if other != n:
                assert not any(m in texts[other] for m in marks), (n, other)
    assert not any(m in t for t in texts.values() for m in ("9077", "9078", "9079", "9080", "AgentGo"))   # 특정 제품 값 없음


def test_layout_follows_edges_not_fixed_positions():
    pos = ad.layout([{"id": i} for i in "xyz"], [{"from": "x", "to": "y"}, {"from": "y", "to": "z"}])
    assert pos == {"x": (0, 0), "y": (1, 0), "z": (2, 0)}
    pos = ad.layout([{"id": i} for i in "abc"], [{"from": "a", "to": "b"}, {"from": "a", "to": "c"}])
    assert pos["a"][0] == 0 and pos["b"][0] == pos["c"][0] == 1 and pos["b"][1] != pos["c"][1]


def test_reading_order_title_nodes_edges_then_boundary(tmp_path):
    """R345 (Microsoft «Reading Order pane» · 화면낭독기는 개체 순서대로 읽음): 제목 → 노드 → 연결 라벨 → 경계 → 범례."""
    ad.render(_load("A"), str(tmp_path / "a.pptx"))
    names = [sh.text_frame.text.split("\n")[0] for sh in pptx.Presentation(str(tmp_path / "a.pptx")).slides[0].shapes
             if sh.has_text_frame and sh.text_frame.text.strip()]
    i_title, i_node, i_edge = 0, names.index("모바일 앱"), names.index("HTTPS 주문")
    i_bound, i_legend = names.index("클라우드 VPC"), next(i for i, n in enumerate(names) if n.startswith("범례"))
    assert i_title < i_node < i_edge < i_bound < i_legend, names


def _person_flow(steps, **view):
    nodes = [{"id": "user", "label": "담당자", "kind": "person", "source": "s"},
             {"id": "gw", "label": "게이트웨이", "source": "s"}, {"id": "api", "label": "업무 API", "source": "s"}]
    return {"views": [{"type": "container", "nodes": nodes, "edges": [{"from": "user", "to": "gw", "label": "요청", "source": "s"}]},
                      {"type": "dynamic", "title": "조회", "participants": ["user", "gw", "api"], "steps": steps, **view}]}


def test_dynamic_person_flow_requires_response_arrow(tmp_path):
    """R342#1: 사람이 시작한 Dynamic 흐름이 게이트웨이에서 끝나 응답 화살표가 빠졌다 →
    요청자에게 돌아오는 단계가 없으면 거부 · 돌아오면 마지막 화살표가 게이트웨이→담당자로 그려짐 · 단방향 근거가 있으면 허용."""
    go = [{"from": "user", "to": "gw", "label": "조회 요청", "source": "s"},
          {"from": "gw", "to": "api", "label": "전달", "source": "s"},
          {"from": "api", "to": "gw", "label": "결과", "source": "s"}]
    with pytest.raises(ad.SpecError, match="응답 흐름 없음: 요청자 user"):
        ad.validate(_person_flow(go))
    full = go + [{"from": "gw", "to": "user", "label": "응답 화면", "source": "s"}]
    ad.render(_person_flow(full), str(tmp_path / "d.pptx"))
    sl = pptx.Presentation(str(tmp_path / "d.pptx")).slides[1]
    boxes = {sh.text_frame.text.split("\n")[0]: sh for sh in sl.shapes if sh.has_text_frame and sh.text_frame.text.strip()}
    conns = [sh for sh in sl.shapes if sh.shape_type == 9 or getattr(sh, "begin_x", None) is not None]
    arrows = [c for c in conns if c.begin_y != c.end_y or c.begin_x != c.end_x]
    horiz = [c for c in arrows if c.begin_y == c.end_y]                         # 생명선(세로) 제외 = 단계 화살표
    assert len(horiz) == 4
    last = max(horiz, key=lambda c: c.begin_y)
    cx = lambda name: boxes[name].left + boxes[name].width // 2
    assert abs(last.begin_x - cx("게이트웨이")) < 20000 and abs(last.end_x - cx("담당자")) < 20000   # 게이트웨이 → 담당자
    assert "4. 응답 화면" in _text(tmp_path / "d.pptx")
    ad.validate(_person_flow(go, no_response="비동기 접수 — 결과는 메일 (notify.py)"))   # 단방향 근거 = 허용
    for n in "ABC":                                                              # 사람 시작이 아닌 기존 샘플은 그대로
        ad.validate(_load(n), allow_unverified=True)
