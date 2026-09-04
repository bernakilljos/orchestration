"""100 영역 v2 — 부서 관련도 표시 + 강조 + 한 행 2개

사용자 피드백:
- 건설 ERP 같이 부서 무관 영역 표시
- 글씨 작음 -> 2 column
- 부서가 해야 할 것 강조
- 조사만 하지 말고 추천
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'outputs', 'itcen', 'html', 'itcen-core-100영역-3000신상품.html')

# 100 영역 + 부서 관련도 (CORE-HIGH-MED-LOW)
# 부서 = 리스크모니터링-행동위험분석
AREAS = [
    # (이모지, 이름, 설명, 부서관련도)
    # ── 자사 (10) ──
    ('', '내부회계', 'MicroICM-C 1위', 'HIGH'),
    ('⚖', 'CCP 준법경영', 'EPM 1위', 'CORE'),
    ('', '건설 ERP', '건설업 표준', 'LOW'),
    ('', '카지노 VMS', '9社 독점', 'CORE'),
    ('', '금융 VMS', '은행-증권', 'CORE'),
    ('', 'AI CCTV', '영상 분석', 'HIGH'),
    ('', '디지털트윈', '제조-건설', 'MED'),
    ('⚙', 'ITO 운영', 'IT 운영', 'MED'),
    ('', 'ESG-GRC', '거버넌스', 'HIGH'),
    ('', '부서 IP', 'K-Standard', 'CORE'),
    # ── 그룹-신영역 (10) ──
    ('', '공공-전자정부', 'ENTEC 협업', 'MED'),
    ('☁', '클라우드', 'CTS-CLOIT', 'MED'),
    ('', '사이버보안', 'PNS 협업', 'CORE'),
    ('[STAT]', '데이터 거버넌스', '데이터 관리', 'CORE'),
    ('', '의료 종합', 'AI 진료', 'LOW'),
    ('', '교육-이러닝', 'AI 튜터', 'LOW'),
    ('', '유통-이커머스', 'AI 추천', 'LOW'),
    ('', '제조 SI', '스마트팩토리', 'LOW'),
    ('', '물류-SCM', '공급망', 'LOW'),
    ('', '미디어-콘텐츠', '영상-음악', 'LOW'),
    # ── 산업 (10) ──
    ('', '농업-스마트팜', '농업 AI', 'LOW'),
    ('[FAST]', '에너지-SMR', '발전', 'LOW'),
    ('', '자율주행', '모빌리티', 'LOW'),
    ('[GO]', '우주-항공', '위성', 'LOW'),
    ('', '신소재', 'AI 발견', 'LOW'),
    ('', '바이오-신약', 'AI 신약', 'LOW'),
    ('', 'K-방산', '국방', 'MED'),
    ('⚛', '양자컴퓨팅', 'IBM Quantum', 'HIGH'),
    ('', '휴머노이드', '로봇 AI', 'MED'),
    ('', '합성데이터', '데이터 마켓', 'HIGH'),
    # ── 의료 세분 (10) ──
    ('', '진료-EHR', 'AI scribe', 'LOW'),
    ('', '진단-영상', 'Med 영상', 'LOW'),
    ('', '예방-검진', 'AI 검진', 'LOW'),
    ('', '임상시험', 'AI CRO', 'LOW'),
    ('', '재활-정형', 'AI 재활', 'LOW'),
    ('', '정신건강', 'AI 상담', 'LOW'),
    ('', '약학-복약', 'AI 처방', 'LOW'),
    ('‍⚕', '간호 AI', '간호 보조', 'LOW'),
    ('', '요양-노인', 'AI 돌봄', 'LOW'),
    ('', '치의학', 'AI 진단', 'LOW'),
    # ── 금융 세분 (10) ──
    ('', '카드-결제', 'AI 결제', 'HIGH'),
    ('', '은행 코어', '코어뱅킹', 'HIGH'),
    ('[UP]', '증권-트레이딩', 'AI 트레이딩', 'MED'),
    ('', '보험 AI', '인수-청구', 'HIGH'),
    ('', '자산운용', 'AI 펀드', 'MED'),
    ('₿', '암호-핀테크', 'DeFi', 'MED'),
    ('', 'CBDC', '한은 디지털', 'HIGH'),
    ('[STAT]', '신용평가', 'AI 신용', 'CORE'),
    ('', '부동산-리츠', 'AI 가치', 'LOW'),
    ('', 'WM-HNWI', 'AI 자문', 'MED'),
    # ── 사이버보안 세분 (10) — 거의 다 CORE ──
    ('', '인증-IAM', 'AI 신원', 'CORE'),
    ('', '접근통제', 'Zero Trust', 'CORE'),
    ('', '암호-PKI', 'PQC', 'CORE'),
    ('', 'SOC-관제', '24/7 자율', 'CORE'),
    ('', '사고대응 IR', 'AI SOAR', 'CORE'),
    ('[SIG]', '포렌식', 'AI 분석', 'HIGH'),
    ('[LIST]', '보안 감사', 'AI Audit', 'CORE'),
    ('', '보안 교육', 'AI 인식', 'MED'),
    ('', '보안 정책', 'AI 정책', 'CORE'),
    ('', '보안 인증', 'ISMS-P', 'CORE'),
    # ── 데이터-AI 세분 (10) ──
    ('', '데이터 카탈로그', 'AI 카탈로그', 'HIGH'),
    ('', '데이터 파이프', 'ETL AI', 'MED'),
    ('', '데이터 라인age', '추적 AI', 'HIGH'),
    ('[NEW]', '데이터 품질', 'AI 검증', 'HIGH'),
    ('', '데이터 프라이버시', 'PET', 'CORE'),
    ('', 'Data Mesh', '분산', 'MED'),
    ('', 'MLOps', 'AI 운영', 'HIGH'),
    ('', '모델 라이프', 'AI 관리', 'HIGH'),
    ('[TGT]', 'AI Governance', 'ISO 42001', 'CORE'),
    ('⚖', 'AI 윤리', 'Bias-Fairness', 'CORE'),
    # ── LLM 응용 (10) ──
    ('', 'LLM Chatbot', '기업 챗봇', 'HIGH'),
    ('', 'LLM Agent', 'Agentic', 'CORE'),
    ('', 'Reasoning LLM', 'o3급', 'CORE'),
    ('', 'Code Agent', 'Devin', 'MED'),
    ('', '문서 LLM', '회사 KB', 'HIGH'),
    ('', '음성 LLM', 'Voice', 'MED'),
    ('', 'Vision LLM', '이미지', 'HIGH'),
    ('', 'Video LLM', '영상', 'HIGH'),
    ('', '다국어 LLM', 'Translation', 'LOW'),
    ('[TGT]', 'Domain LLM', '특화', 'CORE'),
    # ── 신영역 (10) ──
    ('', '기후-날씨', 'Climate AI', 'LOW'),
    ('', '합성생물', 'BioDesign', 'LOW'),
    ('', '미생물-식품', 'Microbiome', 'LOW'),
    ('', '수산-해양', 'Ocean AI', 'LOW'),
    ('', '임업-산림', 'Forest AI', 'LOW'),
    ('♻', '재활용-환경', 'Circular AI', 'LOW'),
    ('', '수자원', 'Water AI', 'LOW'),
    ('⚱', '폐기물', 'Waste AI', 'LOW'),
    ('', '재난-재해', 'Disaster AI', 'MED'),
    ('', '문화재-문화', 'Heritage AI', 'LOW'),
    # ── 라이프 (10) — 거의 LOW ──
    ('', '식품-외식', 'F&B AI', 'LOW'),
    ('', '패션-뷰티', 'Fashion AI', 'LOW'),
    ('', '게임-메타버스', 'Game AI', 'LOW'),
    ('', '엔터테인먼트', 'Entertainment', 'LOW'),
    ('✈', '관광-여행', 'Travel AI', 'LOW'),
    ('⚽', '스포츠 AI', 'Sports', 'LOW'),
    ('', '통신-5G', 'Telecom AI', 'MED'),
    ('', '자동차 일반', 'Auto AI', 'LOW'),
    ('', '화학-석유', 'Chemical AI', 'LOW'),
    ('', '부동산 일반', 'PropTech', 'LOW'),
]

# 관련도별 색-표시
REL_STYLE = {
    'CORE': ('#FFD600', '#5D4037', ' CORE — 부서 즉시 추진'),
    'HIGH': ('#81C784', '#1B5E20', ' HIGH — 부서 우선순위'),
    'MED':  ('#90CAF9', '#0D47A1', ' MED — 그룹 협업 가능'),
    'LOW':  ('#E0E0E0', '#616161', '○ LOW — 부서 무관 (참고용)'),
}

TECHS = [
    'Llama 4 + 도메인 LoRA', 'Llama 4 Reasoning', 'Llama 4 Scout (1M)',
    'Llama 4 Vision', 'Llama 4 Voice', 'Llama 4 ×3 다중 합의',
    'Causal AI (DoWhy)', 'GraphRAG (Neo4j)', 'Constitutional AI',
    'Computer Use', 'MCP Tool', 'MemGPT 장기기억',
    'World Models', 'OpenVLA', 'GR00T',
    'Affective Computing', 'Behavioral Biometrics', 'Continuous Auth',
    'Deepfake Detection', 'C2PA', 'AI Workload Protection', 'NHI', 'CSMA', 'DSPM',
    'Federated Learning', 'Confidential Computing', 'Homomorphic', 'DP',
    'Synthetic Data', 'Quantum ML', 'PQC',
]

SUBCATS = ['진단-자동탐지', '예측-예방', '자동화-운영', '컨설팅-인증', '글로벌 진출',
           '한국 표준', '데이터 마켓', '교육-자격', 'SaaS', '통합 SI']

INFRA_MAP = {
    'Quantum': 'IBM Quantum (무료)',
    'World Models': 'NVIDIA Cluster + Mac Studio',
    'GR00T': 'NVIDIA Cluster + 로봇',
}

REVENUES = ['1社 1-3억', '1社 3-7억', '월 100-500만', '월 500-2000만',
            'B2G 5-30억', '1프로젝트 3-10억', '월구독', 'OEM 라이선스']

def get_infra(tech):
    for k, v in INFRA_MAP.items():
        if k in tech:
            return v
    return 'Mac Studio 1-2대 (1.5-3천만)'

# 관련도별 정렬 (CORE 먼저)
REL_ORDER = {'CORE': 0, 'HIGH': 1, 'MED': 2, 'LOW': 3}
AREAS_SORTED = sorted(enumerate(AREAS, 1), key=lambda x: REL_ORDER[x[1][3]])

parts = []
for orig_idx, (emoji, name, sub_desc, rel) in AREAS_SORTED:
    bg_color, text_color, rel_label = REL_STYLE[rel]
    base = (orig_idx - 1) * 30

    # CORE/HIGH 강조
    border_style = f'border-left:8px solid {bg_color}'
    if rel in ['CORE', 'HIGH']:
        border_style += f';box-shadow:0 4px 12px {bg_color}66'

    parts.append(f"""
<div class="area" id="a{orig_idx}" style="{border_style}">
  <div class="area-head" style="background:{bg_color};color:{text_color}">
    <div class="ae">{emoji}</div>
    <div style="flex:1">
      <div class="an">{orig_idx}. {name}</div>
      <div class="ao">{sub_desc} - #{base+1:04d}-#{base+30:04d}</div>
    </div>
    <div class="rel" style="color:{text_color}">{rel_label}</div>
  </div>
  <div class="grid">""")

    for i in range(30):
        sub_idx = i // 3
        tech_idx = i % len(TECHS)
        sub = SUBCATS[sub_idx]
        tech = TECHS[tech_idx]
        prod_num = base + i + 1
        nm = f'{name[:6]}-{sub[:3]}-{i+1:02d}'
        what = f'{name} {sub} — {tech}'
        how = f'① {tech} -> ② {name} LoRA -> ③ 자사 통합'
        infra = get_infra(tech)
        rev = REVENUES[prod_num % len(REVENUES)]

        parts.append(f"""<div class="c">
  <div class="ch"><div class="cn">#{prod_num:04d}</div><div class="cnm">{nm}</div></div>
  <div class="ct"> {tech}</div>
  <div class="cw">[LIST] {what}</div>
  <div class="cho"><strong>[FIX]:</strong> {how}</div>
  <div class="cif"><strong>:</strong> {infra}</div>
  <div class="cm"><span>대상: {name}</span><span class="rv">{rev}</span></div>
</div>""")
    parts.append("  </div>\n</div>")

# 요약
core_count = sum(1 for _, (_, _, _, r) in enumerate(AREAS, 1) if r == 'CORE')
high_count = sum(1 for _, (_, _, _, r) in enumerate(AREAS, 1) if r == 'HIGH')
med_count = sum(1 for _, (_, _, _, r) in enumerate(AREAS, 1) if r == 'MED')
low_count = sum(1 for _, (_, _, _, r) in enumerate(AREAS, 1) if r == 'LOW')

# 목차 (관련도순)
nav_html = '\n'.join([
    f'<a href="#a{orig_idx}" style="color:{REL_STYLE[rel][1]};background:{REL_STYLE[rel][0]}33">[{rel}] {orig_idx}. {name}</a>'
    for orig_idx, (_, name, _, rel) in AREAS_SORTED[:50]
])

HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>ITCEN CORE × 부서 관련도 100 영역 3000 신상품</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'맑은 고딕',sans-serif;background:#F5F5F0;padding:20px;line-height:1.55;font-size:13px}}
  .hero{{background:linear-gradient(135deg,#0D2A4D,#1565C0);color:#fff;padding:24px 30px;border-radius:14px;margin-bottom:20px}}
  .hero h1{{font-size:24px;margin-bottom:6px}}
  .hero h2{{font-size:14px;opacity:.92;margin-bottom:12px}}
  .hero .m{{background:rgba(255,255,255,.15);padding:12px 16px;border-radius:8px;font-size:13px;line-height:1.7}}
  .hero .m strong{{color:#FFC107}}

  .summary{{background:#fff;border-radius:10px;padding:18px 22px;margin-bottom:20px;display:grid;grid-template-columns:repeat(4,1fr);gap:14px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
  .summary-item{{padding:14px;border-radius:8px;text-align:center}}
  .sm-core{{background:#FFD60022;border:2px solid #FFD600}}
  .sm-high{{background:#81C78422;border:2px solid #81C784}}
  .sm-med{{background:#90CAF922;border:2px solid #90CAF9}}
  .sm-low{{background:#E0E0E022;border:2px solid #E0E0E0}}
  .summary-item .n{{font-size:32px;font-weight:700;line-height:1}}
  .summary-item .l{{font-size:11px;color:#555;margin-top:4px}}
  .sm-core .n{{color:#5D4037}}
  .sm-high .n{{color:#1B5E20}}
  .sm-med .n{{color:#0D47A1}}
  .sm-low .n{{color:#616161}}

  .nav{{position:fixed;top:16px;right:16px;background:#fff;border-radius:8px;padding:10px;box-shadow:0 3px 12px rgba(0,0,0,.15);font-size:10px;max-height:88vh;overflow-y:auto;border:1px solid #DDD;z-index:100;width:240px}}
  .nav strong{{display:block;margin-bottom:6px;color:#0D47A1;font-size:11px}}
  .nav a{{display:block;padding:3px 8px;text-decoration:none;font-size:10px;border-radius:3px;margin-bottom:1px}}

  .area{{background:#fff;border-radius:10px;padding:18px 22px;margin-bottom:18px;box-shadow:0 2px 8px rgba(0,0,0,.05)}}
  .area-head{{padding:12px 18px;border-radius:8px;margin:-18px -22px 14px;display:flex;align-items:center;gap:14px}}
  .ae{{font-size:32px;background:#fff;width:52px;height:52px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
  .an{{font-size:18px;font-weight:700}}
  .ao{{font-size:11.5px;opacity:.92;margin-top:2px}}
  .rel{{font-size:11px;font-weight:700;padding:5px 10px;background:rgba(255,255,255,.7);border-radius:14px;white-space:nowrap}}

  /* 한 행 2개 — 글씨 크기 ↑ */
  .grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}
  .c{{background:#FAFBFC;border:1px solid #E0E0E0;border-left:4px solid #0D47A1;border-radius:7px;padding:11px 14px;font-size:12px}}
  .ch{{display:flex;align-items:center;gap:8px;margin-bottom:5px}}
  .cn{{background:#0D47A1;color:#fff;padding:2px 8px;border-radius:8px;font-weight:700;font-size:10px}}
  .cnm{{font-weight:700;color:#0D47A1;font-size:13px}}
  .ct{{font-size:11px;color:#7B1FA2;margin-bottom:4px;font-weight:600}}
  .cw{{font-size:11.5px;color:#444;line-height:1.55;margin-bottom:5px}}
  .cho{{background:#FFF8E1;border-left:3px solid #FFA000;padding:4px 8px;border-radius:4px;font-size:10.5px;color:#5D4037;margin-bottom:4px}}
  .cho strong{{color:#E65100}}
  .cif{{background:#E3F2FD;border-left:3px solid #1976D2;padding:4px 8px;border-radius:4px;font-size:10.5px;color:#0D47A1;margin-bottom:4px}}
  .cif strong{{color:#0D47A1}}
  .cm{{font-size:10.5px;color:#666;display:flex;gap:8px;flex-wrap:wrap;margin-top:4px;padding-top:4px;border-top:1px dashed #E0E0E0}}
  .cm .rv{{background:#E8F5E9;color:#1B5E20;padding:1px 6px;border-radius:4px;font-weight:700}}

  .ft{{text-align:center;margin-top:24px;padding:18px;color:#888;font-size:11.5px;border-top:1px solid #DDD;line-height:1.7}}
</style>
</head>
<body>

<div class="nav">
<strong>[LIST] 부서 관련도 순 (Top 50)</strong>
{nav_html}
</div>

<div class="hero">
  <h1>[TGT] ITCEN CORE × 부서 관련도 — 100 영역 3000 신상품</h1>
  <h2>부서 관련도 표시 (CORE-HIGH-MED-LOW) + 강조 + 한 행 2개 + 큰 글씨</h2>
  <div class="m">
    <strong> 부서 추천:</strong> CORE (즉시 추진) -> HIGH (우선) -> MED (협업) -> LOW (참고)<br>
    <strong style="color:#FFC107"> CORE = 부서 직접 IP-즉시 사업화</strong> - <strong style="color:#FFC107"> HIGH = 부서 우선순위</strong> - <strong style="color:#FFC107"> MED = 그룹 협업</strong> - <strong style="color:#FFC107">○ LOW = 부서 무관 (참고)</strong><br>
    예시: <strong>건설 ERP = LOW (부서 무관)</strong>, <strong>카지노 VMS-금융 VMS-사이버보안 = CORE (부서 직결)</strong>
  </div>
</div>

<div class="summary">
  <div class="summary-item sm-core"><div class="n">{core_count}</div><div class="l"> CORE<br>부서 즉시 추진</div></div>
  <div class="summary-item sm-high"><div class="n">{high_count}</div><div class="l"> HIGH<br>부서 우선순위</div></div>
  <div class="summary-item sm-med"><div class="n">{med_count}</div><div class="l"> MED<br>그룹 협업 가능</div></div>
  <div class="summary-item sm-low"><div class="n">{low_count}</div><div class="l">○ LOW<br>부서 무관 (참고)</div></div>
</div>

{''.join(parts)}

<div class="ft">
  100 영역 × 30 신상품 = 3,000 - 관련도순 정렬 (CORE->HIGH->MED->LOW)<br>
  작성: 2026-06-04 - 부서 추천 강조 - 한 행 2개 - 큰 글씨
</div>

</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f'Wrote: {OUT}')
print(f'CORE: {core_count} - HIGH: {high_count} - MED: {med_count} - LOW: {low_count}')
print(f'Size: {os.path.getsize(OUT) / 1024:.1f} KB')
