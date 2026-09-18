"""8 트랙 신사업 종합 docx 빌더."""
from __future__ import annotations
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


HERE = Path(__file__).parent
OUT = HERE / "신사업-8트랙-종합.docx"


def set_cell_bg(cell, color_hex: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def add_heading(doc: Document, text: str, level: int = 1, color: str = "1F4E79") -> None:
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor.from_string(color)
        run.font.name = "맑은 고딕"


def add_para(doc: Document, text: str, bold: bool = False, size: int = 11) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "맑은 고딕"
    run.font.size = Pt(size)
    if bold:
        run.bold = True


def add_table(doc: Document, headers: list[str], rows: list[list[str]], header_bg: str = "1F4E79") -> None:
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        c = tbl.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.color.rgb = RGBColor.from_string("FFFFFF")
        r.font.name = "맑은 고딕"
        r.font.size = Pt(10)
        set_cell_bg(c, header_bg)
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            c = tbl.rows[ri + 1].cells[ci]
            c.text = ""
            p = c.paragraphs[0]
            r = p.add_run(str(val))
            r.font.name = "맑은 고딕"
            r.font.size = Pt(9)
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def build() -> Path:
    doc = Document()
    # 페이지 여백
    for s in doc.sections:
        s.left_margin = Cm(1.5)
        s.right_margin = Cm(1.5)
        s.top_margin = Cm(1.5)
        s.bottom_margin = Cm(1.5)

    # 타이틀
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("ITCEN ESG 신사업 8 트랙 종합")
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = RGBColor.from_string("1F4E79")
    r.font.name = "맑은 고딕"
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = sub.add_run("2026-09-07 개정 · 학교법인 유지 · 8 트랙 확정")
    sr.italic = True
    sr.font.size = Pt(10)
    sr.font.color.rgb = RGBColor.from_string("666666")
    sr.font.name = "맑은 고딕"

    # 1. 요약
    add_heading(doc, "1. 요약 (Executive)", level=1)
    add_table(doc, ["항목", "값"], [
        ["신사업 라인", "8 트랙"],
        ["강제 근거", "정보보호산업진흥법·자본시장법·보조금관리법·사립학교법·에너지법·저작권법·개보법·AI법 (2026)"],
        ["대상 시장", "지정 700사·상장사 2500·수급기관 100조+·사학법인 1400·다소비 4000+·AI 도입 전 기업"],
        ["자격 로드맵", "CISA + CFE + CIPP/K = 3개 (1·2·3·8 트랙 90% 커버) + KICPA·KEEP·KOCCA (특화)"],
        ["우리 회사 재사용", "설계평가·운영평가·시나리오 지표·리스크 모니터링 (RMS 방법론)"],
    ])

    # 2. 8 트랙 정본 표
    doc.add_paragraph()
    add_heading(doc, "2. 8 트랙 정본 표", level=1)
    add_table(doc, ["#", "트랙", "강제 근거", "벌금·처벌", "대상 규모", "우리 채널"], [
        ["1", "정보공시", "정보보호산업진흥법 §13", "과태료 1천만 이하", "지정 700+", "정보보안"],
        ["2", "AI 토큰 감사", "AI법 2026 대비", "예방·유출 시 개보법 매출 3%", "전 기업", "정보보안·CIO"],
        ["3", "부정거래 통합 감사", "자본시장법 §176·178·443", "부당이득 3배·무기 or 5년 이상 (5억+)", "상장사 2500", "감사위"],
        ["★4", "국고보조금 사후관리", "보조금관리법 §29·30·40·41", "부정수급 5배 벌금·5년 이하 징역·반환+가산금", "수급기관 (연 100조+)", "회계법인·비영리"],
        ["★5", "학교법인 감사보고서 자동", "사립학교법 §31·32 + 사학기관 재무·회계규칙", "임원취임승인 취소·시정명령·배임·횡령 형사", "사학법인 1400 (대학·중고등)", "회계법인"],
        ["★6", "에너지 이용 합리화 진단", "에너지법 §32·78", "1~2천만 과태료·개선명령 위반 시 형사", "다소비 4000+ (2000toe+)", "대기업 시설·에너지"],
        ["★7", "AI 학습 데이터 저작권 감사", "저작권법 (2026 개정) + AI 저작권 가이드 2024", "5년 이하 징역·5천만 벌금+침해이익 손배", "AI 개발사·학습 데이터 사용 기업", "AI 감사 확장"],
        ["★8", "Zero-Knowledge ML 감사", "개보법 §29 안전조치+AI법·PIA 대응", "유출 시 개보법 매출 3% 과징금 (예방 SaaS)", "AI 도입 기업·개인정보 취급", "정보공시 확장"],
    ])

    # 3. 학교법인 실행 전략
    doc.add_paragraph()
    add_heading(doc, "3. 5 학교법인 감사보고서 자동 · 실행 전략", level=1)
    add_para(doc, "벽 → 극복 방안", bold=True)
    add_table(doc, ["벽", "극복 방안"], [
        ["KICPA (공인회계사) 필수", "회계법인 파트너십 (삼일·한영·삼정) · 우리는 SW 툴 공급 · 감사인 지위는 파트너"],
        ["사학기관 재무·회계규칙", "규칙 표준 서식 자동화 · 사학진흥재단 공동사업 검토"],
        ["회계법인 독점", "White-label OEM 모델 · 회계법인 브랜드로 배포 · 수수료 셰어"],
        ["B2B2B 3단계", "회계사 SaaS 시장 진입 · 개별 회계사·중소 회계법인 target"],
    ])
    doc.add_paragraph()
    add_para(doc, "RMS 방법론 재활용", bold=True)
    add_table(doc, ["RMS 요소", "학교법인 활용"], [
        ["리스크 시나리오 지표", "학교 재무 리스크 (미납·미수·부실 채권) 시나리오"],
        ["설계평가·운영평가", "학교 내부통제 평가"],
        ["리스크 모니터링", "학교 재무 KPI 대시보드"],
        ["이상 감지", "사학법인 특유 이상 거래 (교비 유용·부속병원 회계 등)"],
    ])

    # 4. 자격 로드맵
    doc.add_paragraph()
    add_heading(doc, "4. 자격 로드맵", level=1)
    add_para(doc, "A. 필수 3개 (1·2·3·8 트랙 90% 커버)", bold=True)
    add_table(doc, ["우선", "자격", "발급", "응시료 (KRW)", "준비 기간", "트랙 커버"], [
        ["1", "CISA", "ISACA", "77만 (회원 $575)", "6~12개월", "1·2·3·8"],
        ["2", "CFE", "ACFE", "60만 ($450) + Prep 130만", "3~6개월", "3·4"],
        ["3", "CIPP/K", "IAPP + KISA", "75만 ($550)", "3~6개월", "1·7·8"],
    ])
    add_para(doc, "= 3개 합 · 약 210만 (자습 기준) · 8~18개월", size=10)
    doc.add_paragraph()
    add_para(doc, "B. 특화 자격 (4·5·6·7 트랙 도메인)", bold=True)
    add_table(doc, ["트랙", "자격", "필수도"], [
        ["4 국고보조금", "KICPA (공인회계사) or 감사인 교육 (한국공인회계사회)", "★★"],
        ["5 학교법인", "KICPA 필수 or 회계법인 파트너십 + 사학감사 실무 세미나", "★★★"],
        ["6 에너지 진단", "KEEP (에너지공단 진단자)", "★★★ 필수"],
        ["7 AI 저작권", "KOCCA AI 저작권 교육 + 저작권법 실무", "★★"],
    ])
    doc.add_paragraph()
    add_para(doc, "C. AI 감사 보조 (2·7·8 강화)", bold=True)
    add_para(doc, "• AICE Professional (한경·KT · 12만)\n• AWS Certified ML Specialty ($300)\n• 빅데이터 분석기사 (KDATA · 국가공인)", size=10)

    # 5. RMS 방법론 매핑
    doc.add_paragraph()
    add_heading(doc, "5. 우리 회사 지표 매핑 (RMS 방법론 재활용)", level=1)
    add_table(doc, ["트랙", "설계평가", "운영평가", "시나리오 지표", "리스크 모니터링"], [
        ["1 정보공시", "○", "○", "○", "○"],
        ["2 AI 토큰", "○", "○", "○", "○"],
        ["3 부정거래", "○", "○", "○", "○"],
        ["4 국고보조금", "○", "○", "○", "○"],
        ["5 학교법인", "○", "○", "○", "○"],
        ["6 에너지 진단", "○", "○", "○", "○"],
        ["7 AI 저작권", "○", "○", "○", "○"],
        ["8 ZK ML", "○", "○", "○", "○"],
    ])
    add_para(doc, "8 트랙 전체 = 우리 RMS 방법론 재활용 가능. 도메인 감시 지표만 트랙별 특화.", size=10)

    # 6. Phase
    doc.add_paragraph()
    add_heading(doc, "6. 우선순위 · 3 페이즈", level=1)
    add_table(doc, ["Phase", "시기", "트랙", "이유"], [
        ["Phase 1", "즉시 · Q4 2026", "1 정보공시 · 2 AI 토큰 감사", "정면 fit · 기존 지표 재활용"],
        ["Phase 2", "단기 · H1 2027", "3 부정거래 · 8 ZK ML", "자본시장법 정면 · CIPP/K 취득 후"],
        ["Phase 3", "중기 · H2 2027", "4 국고보조금 · 5 학교법인 · 6 에너지 · 7 AI 저작권", "특화 자격·파트너십 준비 후"],
    ])

    # 7. 우리 회사 강점
    doc.add_paragraph()
    add_heading(doc, "7. 우리 회사 강점 (ITCEN ESG)", level=1)
    add_table(doc, ["자산", "재활용"], [
        ["ICM Agent Go", "감사 자동화 엔진 → 모든 트랙 base"],
        ["RMS", "리스크 시나리오·설계평가·운영평가·모니터링 방법론"],
        ["Contabulo", "데이터 파이프라인·감사조서 자동화"],
        ["CCP", "컴플라이언스 관리 플랫폼"],
    ])
    add_para(doc, "8 트랙 전체 = 4 자산 조합으로 구현 가능. 신규 개발 최소·재활용 최대.", size=10)

    # 8. 결정 사항
    doc.add_paragraph()
    add_heading(doc, "8. 결정 사항 (팀장 승인 필요)", level=1)
    for item in [
        "☐ 8 트랙 확정",
        "☐ Phase 1 즉시 착수 (1·2)",
        "☐ 자격 로드맵 예산 승인 (약 210만 × 담당자 N)",
        "☐ KICPA·KEEP·KOCCA 특화 자격 담당자 배정",
        "☐ 회계법인 파트너십 협의 (4·5 트랙 · 삼일·한영·삼정)",
    ]:
        add_para(doc, item, size=11)

    doc.save(OUT)
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"[OK] {p}")
