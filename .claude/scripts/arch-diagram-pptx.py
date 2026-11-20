#!/usr/bin/env python3
"""arch-diagram-pptx — 사실 원본(JSON spec) → 편집 가능한 아키텍처 도식 PPTX (R342·R343 · python-pptx native shape).

특정 제품·포트·장수·색을 엔진에 넣지 않는다 — 노드·연결·경계·조건은 전부 spec 에서 온다.
모든 노드·연결에 source(근거: 파일/절/줄/버전) 가 있어야 한다. 없으면 거부 (--allow-unverified 면 «미확인» 표시로 그림).

usage:
  python arch-diagram-pptx.py <spec.json> <out.pptx> [--allow-unverified]   # 생성 + 근거 대조표(stdout JSON)
  python arch-diagram-pptx.py --check <spec.json>                         # 검증만

spec:
  {"title": "...", "views": [
     {"type": "container", "title": "...", "subtitle": "...",
      "nodes": [{"id","label","kind":"person|container|store|optional|external","boundary":"이름","source":"..."}],
      "edges": [{"from","to","label","optional":bool,"source":"..."}]},
     {"type": "dynamic", "title": "...", "participants": ["id",...] (nodes 는 같은 문서의 container view 에서 찾음),
      "steps": [{"from","to","label","optional":bool,"source":"..."}]}]}
"""
import json
import sys
from collections import defaultdict, deque

KINDS = ("person", "container", "store", "optional", "external")


class SpecError(ValueError):
    pass


def validate(spec: dict, allow_unverified: bool = False) -> dict:
    """근거 대조 — 반환: {"claims": [...], "unverified": [...]} · 구조 오류·근거 없음(허용 안 함) = SpecError."""
    claims, unverified, errors = [], [], []
    nodes = {}
    for v in spec.get("views") or []:
        for n in v.get("nodes") or []:
            if n.get("id") in nodes:
                errors.append(f"노드 id 중복: {n.get('id')}")
            if n.get("kind", "container") not in KINDS:
                errors.append(f"노드 종류 오류: {n.get('id')} {n.get('kind')}")
            nodes[n.get("id")] = n
    if not nodes:
        errors.append("노드 없음")
    for v in spec.get("views") or []:
        if v.get("type") not in ("container", "dynamic"):
            errors.append(f"view 종류 오류: {v.get('type')}")
        items = [("node", n) for n in v.get("nodes") or []] + [("edge", e) for e in (v.get("edges") or v.get("steps") or [])]
        for p in v.get("participants") or []:
            if p not in nodes:
                errors.append(f"참여자 노드 없음: {p}")
        for kind, it in items:
            if kind == "edge":
                for end in (it.get("from"), it.get("to")):
                    if end not in nodes:
                        errors.append(f"연결 끝점 노드 없음: {end} ({it.get('label')})")
            ref = f"{v.get('type')}:{it.get('id') or (str(it.get('from')) + '→' + str(it.get('to')))}"
            src = str(it.get("source") or "").strip()
            claims.append({"view": v.get("type"), "element": ref, "label": it.get("label"), "source": src or "미확인"})
            if not src:
                unverified.append(ref)
    if unverified and not allow_unverified:
        errors.append("근거(source) 없는 요소 %d개: %s — 원본 문서·코드·설정에서 찾아 적거나 --allow-unverified (미확인 표시)"
                      % (len(unverified), ", ".join(unverified[:8])))
    if errors:
        raise SpecError(" · ".join(errors))
    return {"claims": claims, "unverified": unverified, "nodes": nodes}


def layout(nodes: list, edges: list) -> dict:
    """연결 관계로 열(깊이) 결정 → {id: (col, row)} · 진입 없는 노드가 0열 · 순환은 등장 순서로 끊음."""
    ids = [n["id"] for n in nodes]
    inc = defaultdict(int)
    out = defaultdict(list)
    for e in edges:
        if e["from"] in ids and e["to"] in ids and e["from"] != e["to"]:
            out[e["from"]].append(e["to"])
            inc[e["to"]] += 1
    depth = {}
    q = deque([i for i in ids if inc[i] == 0] or ids[:1])
    for i in q:
        depth[i] = 0
    while q:
        a = q.popleft()
        for b in out[a]:
            if b not in depth:
                depth[b] = depth[a] + 1
                q.append(b)
    for i in ids:
        depth.setdefault(i, 0)
    rows = defaultdict(int)
    pos = {}
    for i in ids:
        c = depth[i]
        pos[i] = (c, rows[c])
        rows[c] += 1
    return pos


def render(spec: dict, out_path: str, allow_unverified: bool = False) -> dict:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
    from pptx.enum.text import PP_ALIGN
    from pptx.oxml.ns import qn
    from lxml import etree

    rep = validate(spec, allow_unverified)
    nodes = rep["nodes"]
    unverified = set(rep["unverified"])
    FONT = spec.get("font", "맑은 고딕")
    INK, MUTED, LINE = RGBColor(0x1F, 0x29, 0x37), RGBColor(0x6B, 0x72, 0x80), RGBColor(0x37, 0x41, 0x51)
    WARN, BLUE = RGBColor(0xB4, 0x53, 0x09), RGBColor(0x1D, 0x4E, 0xD8)
    FILL = {"person": RGBColor(0xE0, 0xE7, 0xFF), "container": RGBColor(0xDB, 0xEA, 0xFE), "store": RGBColor(0xD1, 0xFA, 0xE5),
            "optional": RGBColor(0xF3, 0xF4, 0xF6), "external": RGBColor(0xFE, 0xF3, 0xC7)}

    def txt(shape, text, size=12, bold=False, color=INK, align=PP_ALIGN.CENTER):
        tf = shape.text_frame
        tf.clear()
        tf.word_wrap = True
        for i, line in enumerate(str(text).split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            r = p.add_run()
            r.text = line
            r.font.size, r.font.bold, r.font.name, r.font.color.rgb = Pt(size if i == 0 else max(9, size - 2)), bold and i == 0, FONT, color

    def head(s, title, sub):
        t = s.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.7))
        txt(t, title, 24, True, INK, PP_ALIGN.LEFT)
        if sub:
            t2 = s.shapes.add_textbox(Inches(0.5), Inches(0.95), Inches(12.3), Inches(0.4))
            txt(t2, sub, 13, False, MUTED, PP_ALIGN.LEFT)

    def arrowhead(conn, dashed):
        conn.line.color.rgb, conn.line.width = LINE, Pt(1.5)
        if dashed:
            conn.line.dash_style = 4
        etree.SubElement(conn.line._get_or_add_ln(), qn("a:tailEnd")).set("type", "triangle")

    def box(s, nid, x, y, w, h, ref):
        n = nodes[nid]
        kind = n.get("kind", "container")
        shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        shp.fill.solid()
        shp.fill.fore_color.rgb = FILL[kind]
        shp.line.color.rgb, shp.line.width = LINE, Pt(1.25)
        if kind == "optional":
            shp.line.dash_style = 4
        label = n.get("label", nid) + ("\n[미확인]" if ref in unverified else "")
        txt(shp, label, 13, True, WARN if ref in unverified else INK)
        return shp

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for v in spec["views"]:
        s = prs.slides.add_slide(prs.slide_layouts[6])
        head(s, v.get("title", ""), v.get("subtitle", ""))
        if v["type"] == "container":
            vn, ve = v.get("nodes") or [], v.get("edges") or []
            pos = layout(vn, ve)
            ncol = max(c for c, _ in pos.values()) + 1
            nrow = max(r for _, r in pos.values()) + 1
            H = 1.0
            W = min(2.3, (11.8 - (ncol - 1) * 1.6) / ncol) if ncol > 1 else 2.3   # 라벨 칸 최소 1.6in 확보
            gx = min(2.0, (11.8 - ncol * W) / max(1, ncol - 1)) if ncol > 1 else 0
            gy = min(1.3, (5.0 - nrow * H) / max(1, nrow - 1)) if nrow > 1 else 0
            x0, y0 = 0.6, 1.9
            xy = {i: (x0 + c * (W + gx), y0 + r * (H + gy)) for i, (c, r) in pos.items()}
            # 경계 (spec 의 boundary 이름별 · 노드 바깥 여백)
            groups = defaultdict(list)
            for n in vn:
                if n.get("boundary"):
                    groups[n["boundary"]].append(n["id"])
            for name, members in groups.items():
                xs = [xy[m][0] for m in members]
                ys = [xy[m][1] for m in members]
                bx, by = min(xs) - 0.25, min(ys) - 0.5
                bh = max(ys) - min(ys) + H + 0.5 + 0.45          # 위 0.5 (연결 라벨) · 아래 0.45 (경계 이름)
                b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(bx), Inches(by), Inches(max(xs) - min(xs) + W + 0.5),
                                       Inches(bh))
                b.fill.background()
                b.line.color.rgb, b.line.width, b.line.dash_style = BLUE, Pt(1.5), 7
                t = s.shapes.add_textbox(Inches(bx + 0.1), Inches(max(ys) + H + 0.05), Inches(3.5), Inches(0.35))   # 경계 이름은 아래 안쪽 (위는 연결 라벨 자리)
                txt(t, name, 11, True, BLUE, PP_ALIGN.LEFT)
            shp = {n["id"]: box(s, n["id"], *xy[n["id"]], W, H, f"container:{n['id']}") for n in vn}
            for e in ve:
                a, b = e["from"], e["to"]
                (ca, ra), (cb, rb) = pos[a], pos[b]
                if ca == cb:
                    sa, sb = (2, 0) if rb > ra else (0, 2)
                else:
                    sa, sb = (3, 1) if cb > ca else (1, 3)
                c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 0, 0)
                c.begin_connect(shp[a], sa)
                c.end_connect(shp[b], sb)
                arrowhead(c, e.get("optional"))
                ref = f"container:{a}→{b}"
                ax, ay = xy[a]
                bxx, byy = xy[b]
                pt = {0: (W / 2, 0), 1: (0, H / 2), 2: (W / 2, H), 3: (W, H / 2)}   # 연결점 (위·왼·아래·오른)
                p1 = (ax + pt[sa][0], ay + pt[sa][1])
                p2 = (bxx + pt[sb][0], byy + pt[sb][1])
                mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2      # 선의 중점 — 대상마다 달라 라벨이 겹치지 않음
                if ca == cb:      # 세로선 — 중점 오른쪽
                    lx, ly, lw = mx + 0.1, my - 0.17, 1.9
                elif abs(p1[1] - p2[1]) < 0.05:   # 가로선 — 중점 위
                    lw = max(0.8, abs(p2[0] - p1[0]) - 0.1)
                    lx, ly = mx - lw / 2, my - 0.4
                else:             # 대각선 — 중점 오른쪽 (선과 겹치지 않게)
                    lx, ly, lw = mx + 0.12, my - 0.17, 1.8
                t = s.shapes.add_textbox(Inches(lx), Inches(ly), Inches(lw), Inches(0.35))
                txt(t, e.get("label", "") + (" [미확인]" if ref in unverified else ""), 10, False,
                    WARN if ref in unverified else MUTED, PP_ALIGN.CENTER if (ca != cb and abs(p1[1] - p2[1]) < 0.05) else PP_ALIGN.LEFT)
            legend = []
            if any(e.get("optional") for e in ve) or any(n.get("kind") == "optional" for n in vn):
                legend.append("실선 = 항상 · 점선 = 선택·조건부")
            if groups:
                legend.append("파란 점선 상자 = 경계")
            if unverified:
                legend.append("[미확인] = 근거 없음")
            if legend:
                t = s.shapes.add_textbox(Inches(0.5), Inches(6.85), Inches(12.3), Inches(0.4))
                txt(t, "범례: " + " · ".join(legend), 11, False, INK, PP_ALIGN.LEFT)
        else:
            parts = v.get("participants") or []
            step_w = min(2.5, 12.3 / max(1, len(parts)))
            xs = {}
            for i, p in enumerate(parts):
                x = 0.5 + i * step_w
                box(s, p, x, 1.5, step_w - 0.3, 0.8, f"container:{p}")
                xs[p] = x + (step_w - 0.3) / 2
                ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(xs[p]), Inches(2.3), Inches(xs[p]), Inches(7.0))
                ln.line.color.rgb, ln.line.dash_style = RGBColor(0x9C, 0xA3, 0xAF), 4
            steps = v.get("steps") or []
            gap = min(0.75, 4.4 / max(1, len(steps)))
            y = 2.6
            for k, st in enumerate(steps, 1):
                a, b = st["from"], st["to"]
                ref = f"dynamic:{a}→{b}"
                label = f"{k}. {st.get('label', '')}" + (" [미확인]" if ref in unverified else "")
                if a == b:
                    t = s.shapes.add_textbox(Inches(xs[a] + 0.15), Inches(y + 0.05), Inches(step_w), Inches(0.35))
                    txt(t, label, 11, True, RGBColor(0x04, 0x78, 0x57), PP_ALIGN.LEFT)
                else:
                    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(xs[a]), Inches(y + 0.3), Inches(xs[b]), Inches(y + 0.3))
                    arrowhead(c, st.get("optional"))
                    span = min(abs(xs[b] - xs[a]), step_w) - 0.2
                    t = s.shapes.add_textbox(Inches(min(xs[a], xs[b]) + 0.1), Inches(y - 0.05), Inches(span), Inches(0.35))
                    txt(t, label, 11, False, WARN if ref in unverified else INK,
                        PP_ALIGN.LEFT if abs(xs[b] - xs[a]) > step_w + 0.1 else PP_ALIGN.CENTER)
                y += gap
    prs.save(out_path)
    return {"out": out_path, "slides": len(spec["views"]), "claims": rep["claims"], "unverified": rep["unverified"]}


def main(argv):
    if len(argv) >= 3 and argv[1] == "--check":
        try:
            r = validate(json.load(open(argv[2], encoding="utf-8")), "--allow-unverified" in argv)
            print(json.dumps({"ok": True, "claims": len(r["claims"]), "unverified": r["unverified"]}, ensure_ascii=False))
            return 0
        except SpecError as e:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            return 2
    if len(argv) < 3:
        print(__doc__)
        return 2
    try:
        r = render(json.load(open(argv[1], encoding="utf-8")), argv[2], "--allow-unverified" in argv)
    except SpecError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, **r}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
