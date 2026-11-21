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


# ── R343#1 (R354 13차 큐): Deployment·DFD·Trust boundary 전용 배치 ─────────────────────────────
#   깊이 기반 배치는 경계를 무시해 서로 다른 경계의 노드가 같은 열에 섞이고, 경계 상자가 겹치거나 남의 노드를 감싼다.
#   Microsoft Threat Modeling Tool·OWASP Threat Dragon 의 DFD 는 신뢰 경계를 지나는 데이터 흐름을 위협 분석 대상으로 본다.
def _zoned(vtype):
    n = lambda i, z=None, k="container": {"id": i, "label": i.upper(), "kind": k, "source": "s", **({"boundary": z} if z else {})}
    nodes = [n("user", None, "person"), n("web", "DMZ"), n("api", "내부망"), n("db", "내부망", "store"),
             n("waf", "DMZ"), n("auth", "내부망"), n("idp", None, "external")]
    e = lambda a, b: {"from": a, "to": b, "label": f"{a}-{b}", "source": "s"}
    edges = [e("user", "waf"), e("waf", "web"), e("web", "api"), e("user", "auth"), e("api", "db"), e("auth", "idp")]
    return {"views": [{"type": vtype, "title": vtype, "nodes": nodes, "edges": edges}]}


def _geom(path):
    s = pptx.Presentation(str(path)).slides[0]
    rects, boxes = [], {}
    for sh in s.shapes:
        if sh.shape_type != 1:
            continue
        if sh.auto_shape_type == 1:                       # RECTANGLE = 경계 상자
            rects.append((sh.left, sh.top, sh.left + sh.width, sh.top + sh.height))
        elif sh.has_text_frame and sh.text_frame.text.strip():
            boxes[sh.text_frame.text.split("\n")[0]] = (sh.left + sh.width // 2, sh.top + sh.height // 2)
    return rects, boxes


def _inside(pt, r):
    return r[0] < pt[0] < r[2] and r[1] < pt[1] < r[3]


def _bad_boundaries(spec, path):
    rects, boxes = _geom(path)
    members = defaultdict_list(spec)
    overlap = any(not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])
                  for i, a in enumerate(rects) for b in rects[i + 1:])
    foreign = [lbl for lbl, c in boxes.items() for r in rects
               if _inside(c, r) and not any(all(_inside(boxes[m], r) for m in ms) and lbl in ms for ms in members.values())]
    return overlap, foreign, len(rects)


def defaultdict_list(spec):
    g = {}
    for nd in spec["views"][0]["nodes"]:
        if nd.get("boundary"):
            g.setdefault(nd["boundary"], []).append(nd["label"])
    return g


def test_depth_layout_mixes_boundaries_repro(tmp_path):
    """수정 전 결함 재현: container(깊이 기반)는 DMZ·내부망 상자가 겹치거나 남의 노드를 감싼다."""
    sp = _zoned("container")
    ad.render(sp, str(tmp_path / "c.pptx"))
    overlap, foreign, _ = _bad_boundaries(sp, tmp_path / "c.pptx")
    assert overlap or foreign


@pytest.mark.parametrize("vtype", ["deployment", "dfd"])
def test_zone_layout_keeps_boundaries_exclusive(tmp_path, vtype):
    sp = _zoned(vtype)
    r = ad.render(sp, str(tmp_path / "z.pptx"))
    overlap, foreign, nrect = _bad_boundaries(sp, tmp_path / "z.pptx")
    assert nrect == 2 and not overlap and not foreign, (overlap, foreign)
    pos = ad.zone_layout(sp["views"][0]["nodes"], sp["views"][0]["edges"])
    cols = {}
    for nd in sp["views"][0]["nodes"]:
        cols.setdefault(nd.get("boundary") or nd["id"], set()).add(pos[nd["id"]][0])
    keys = list(cols)
    assert all(not (cols[a] & cols[b]) for i, a in enumerate(keys) for b in keys[i + 1:])   # 경계마다 열을 따로 가짐
    assert pos["user"][0] < pos["waf"][0] < pos["api"][0] < pos["idp"][0]                    # 흐름 방향 왼→오
    # 경계를 지나는 흐름만 crossings 로 보고 (경계 안 흐름 waf→web · api→db 제외)
    assert sorted(r["crossings"]) == sorted(["user→waf", "web→api", "user→auth", "auth→idp"])
    assert "신뢰 경계 통과" in _text(tmp_path / "z.pptx")


def test_dfd_rule_store_and_external_only_via_process():
    """DFD 규칙 (Yourdon·Gane-Sarson): 저장소·외부 개체끼리 직접 연결하지 않고 처리(process)를 거친다."""
    sp = _zoned("dfd")
    sp["views"][0]["edges"].append({"from": "idp", "to": "db", "label": "직접", "source": "s"})
    with pytest.raises(ad.SpecError, match="DFD 흐름 규칙.*idp→db"):
        ad.validate(sp)
    sp["views"][0]["type"] = "deployment"                 # 배포도에는 이 규칙을 적용하지 않음
    ad.validate(sp)
