"""100 영역 v3 — 솔루션 회사 관점

사용자 피드백: '우리회사 솔루션 회사야' (컨설팅·SI X)
변경:
- 자사 패키지명 (Micro***-AI 형식) 통일
- 라이선스 모델 (월구독·영구·OEM·종량제) 강조
- SI·컨설팅 형식 제거
- CORE/HIGH 재평가 (자사 패키지화 가능 여부 기준)
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'outputs', 'itcen', 'html', 'itcen-core-100영역-3000신상품.html')

# 100 영역 + 관련도 + 자사 패키지 prefix
# (이모지, 이름, 패키지 prefix, 관련도)
AREAS = [
    # ── 자사 (10) ──
    ('📒', '내부회계', 'MicroICM', 'CORE'),
    ('⚖️', 'CCP 준법경영', 'MicroCCP', 'CORE'),
    ('🏗️', '건설 ERP', 'MicroBuild', 'LOW'),
    ('🎰', '카지노 VMS', 'MicroCasino', 'CORE'),
    ('🏦', '금융 VMS', 'MicroFin', 'CORE'),
    ('📹', 'AI CCTV', 'MicroCCTV', 'HIGH'),
    ('🌐', '디지털트윈', 'MicroTwin', 'MED'),
    ('⚙️', 'ITO 운영', 'MicroITO', 'MED'),
    ('🌱', 'ESG·GRC', 'MicroESG', 'HIGH'),
    ('🚨', '부서 IP', 'MicroRisk', 'CORE'),
    # ── 그룹·신영역 (10) ──
    ('🏛️', '공공·전자정부', 'MicroGov', 'LOW'),  # 솔루션화 가능하나 B2G 색채
    ('☁️', '클라우드', 'MicroCloud', 'MED'),
    ('🛡️', '사이버보안', 'MicroSec', 'CORE'),
    ('📊', '데이터 거버넌스', 'MicroData', 'CORE'),
    ('🏥', '의료 종합', 'MicroMed', 'LOW'),
    ('📚', '교육·이러닝', 'MicroEdu', 'LOW'),
    ('🛒', '유통·이커머스', 'MicroRetail', 'LOW'),
    ('🏭', '제조 SI', 'MicroMfg', 'LOW'),
    ('🚛', '물류·SCM', 'MicroLogi', 'LOW'),
    ('🎬', '미디어·콘텐츠', 'MicroMedia', 'LOW'),
    # ── 산업 (10) — 대부분 LOW (솔루션 회사 관점 X) ──
    ('🌾', '농업·스마트팜', 'MicroAgri', 'LOW'),
    ('⚡', '에너지·SMR', 'MicroEnergy', 'LOW'),
    ('🚗', '자율주행', 'MicroAuto', 'LOW'),
    ('🚀', '우주·항공', 'MicroSpace', 'LOW'),
    ('🧪', '신소재', 'MicroMat', 'LOW'),
    ('🧬', '바이오·신약', 'MicroBio', 'LOW'),
    ('🛡️', 'K-방산', 'MicroDef', 'LOW'),
    ('⚛️', '양자컴퓨팅', 'MicroQuantum', 'MED'),
    ('🤖', '휴머노이드', 'MicroRobot', 'LOW'),
    ('🌟', '합성데이터', 'MicroSynth', 'HIGH'),
    # ── 의료 세분 (10) — LOW (솔루션 회사·부서 무관) ──
    ('🩺', '진료·EHR', 'MicroEHR', 'LOW'),
    ('🔬', '진단·영상', 'MicroDiag', 'LOW'),
    ('💉', '예방·검진', 'MicroPrev', 'LOW'),
    ('🧪', '임상시험', 'MicroTrial', 'LOW'),
    ('🦾', '재활·정형', 'MicroRehab', 'LOW'),
    ('🧠', '정신건강', 'MicroMental', 'LOW'),
    ('💊', '약학·복약', 'MicroPharm', 'LOW'),
    ('👩‍⚕️', '간호', 'MicroNurse', 'LOW'),
    ('🏨', '요양·노인', 'MicroCare', 'LOW'),
    ('🦷', '치의학', 'MicroDent', 'LOW'),
    # ── 금융 세분 (10) — CORE/HIGH (자사 솔루션화 가능) ──
    ('💳', '카드·결제', 'MicroCard', 'HIGH'),
    ('🏛️', '은행 코어', 'MicroBank', 'HIGH'),
    ('📈', '증권·트레이딩', 'MicroSec-T', 'MED'),
    ('🏠', '보험', 'MicroIns', 'HIGH'),
    ('💰', '자산운용', 'MicroAM', 'MED'),
    ('₿', '암호·핀테크', 'MicroFinTech', 'MED'),
    ('💵', 'CBDC', 'MicroCBDC', 'MED'),
    ('📊', '신용평가', 'MicroCredit', 'CORE'),
    ('🏘️', '부동산·리츠', 'MicroREIT', 'LOW'),
    ('💎', 'WM·HNWI', 'MicroWM', 'MED'),
    # ── 사이버보안 세분 (10) — 거의 다 CORE ──
    ('🔐', '인증·IAM', 'MicroIAM', 'CORE'),
    ('🛂', '접근통제', 'MicroAccess', 'CORE'),
    ('🔑', '암호·PQC', 'MicroPQC', 'CORE'),
    ('👁️', 'SOC·관제', 'MicroSOC', 'CORE'),
    ('🚨', '사고대응', 'MicroIR', 'CORE'),
    ('🔍', '포렌식', 'MicroForensic', 'HIGH'),
    ('📋', '보안 감사', 'MicroAudit', 'CORE'),
    ('🎓', '보안 교육', 'MicroSecEdu', 'MED'),
    ('📜', '보안 정책', 'MicroPolicy', 'CORE'),
    ('🏅', '보안 인증', 'MicroISMS', 'CORE'),
    # ── 데이터·AI 세분 (10) — 대부분 CORE/HIGH ──
    ('📦', '데이터 카탈로그', 'MicroCatalog', 'HIGH'),
    ('🌊', '데이터 파이프', 'MicroPipe', 'MED'),
    ('🔗', '데이터 라인age', 'MicroLineage', 'HIGH'),
    ('✨', '데이터 품질', 'MicroDQ', 'HIGH'),
    ('🛡️', '데이터 프라이버시', 'MicroPET', 'CORE'),
    ('🗄️', 'Data Mesh', 'MicroMesh', 'MED'),
    ('🧠', 'MLOps', 'MicroMLOps', 'HIGH'),
    ('🔄', '모델 라이프', 'MicroModel', 'HIGH'),
    ('🎯', 'AI Governance', 'MicroGov-AI', 'CORE'),
    ('⚖️', 'AI 윤리', 'MicroBias', 'CORE'),
    # ── LLM 응용 세분 (10) — 자사 솔루션화 ──
    ('💬', 'LLM Chatbot', 'MicroChat', 'HIGH'),
    ('🤖', 'LLM Agent', 'MicroAgent', 'CORE'),
    ('🧠', 'Reasoning LLM', 'MicroReason', 'CORE'),
    ('💻', 'Code Agent', 'MicroCode', 'MED'),
    ('📖', '문서 LLM', 'MicroKB', 'HIGH'),
    ('🎙️', '음성 LLM', 'MicroVoice', 'MED'),
    ('🖼️', 'Vision LLM', 'MicroVision', 'HIGH'),
    ('🎬', 'Video LLM', 'MicroVideo', 'HIGH'),
    ('🌍', '다국어 LLM', 'MicroTrans', 'LOW'),
    ('🎯', 'Domain LLM', 'MicroDomain', 'CORE'),
    # ── 신영역 (10) — 대부분 LOW ──
    ('🌡️', '기후·날씨', 'MicroClimate', 'LOW'),
    ('🧬', '합성생물', 'MicroSynBio', 'LOW'),
    ('🦠', '미생물', 'MicroMicrobe', 'LOW'),
    ('🐟', '수산·해양', 'MicroOcean', 'LOW'),
    ('🌳', '임업·산림', 'MicroForest', 'LOW'),
    ('♻️', '재활용·환경', 'MicroCircular', 'LOW'),
    ('🚰', '수자원', 'MicroWater', 'LOW'),
    ('⚱️', '폐기물', 'MicroWaste', 'LOW'),
    ('🌋', '재난·재해', 'MicroDisaster', 'LOW'),
    ('🏛️', '문화재·문화', 'MicroHeritage', 'LOW'),
    # ── 라이프 (10) — 모두 LOW ──
    ('🍽️', '식품·외식', 'MicroFB', 'LOW'),
    ('💄', '패션·뷰티', 'MicroFashion', 'LOW'),
    ('🎮', '게임·메타버스', 'MicroGame', 'LOW'),
    ('🎭', '엔터테인먼트', 'MicroEnt', 'LOW'),
    ('✈️', '관광·여행', 'MicroTravel', 'LOW'),
    ('⚽', '스포츠 AI', 'MicroSports', 'LOW'),
    ('📡', '통신·5G', 'MicroTelco', 'LOW'),
    ('🚙', '자동차 일반', 'MicroAuto2', 'LOW'),
    ('🧪', '화학·석유', 'MicroChem', 'LOW'),
    ('🏘️', '부동산 일반', 'MicroProp', 'LOW'),
]

REL_STYLE = {
    'CORE': ('#FFD600', '#5D4037', '⭐⭐⭐ CORE — 자사 패키지 즉시'),
    'HIGH': ('#81C784', '#1B5E20', '⭐⭐ HIGH — 자사 패키지 가능'),
    'MED':  ('#90CAF9', '#0D47A1', '⭐ MED — 그룹·OEM 협업'),
    'LOW':  ('#E0E0E0', '#616161', '○ LOW — 솔루션화 어려움'),
}

# 솔루션 회사 라이선스 모델
LICENSE_MODELS = [
    '월구독 100-500만', '월구독 500-2000만', '월구독 1000-3000만',
    '영구 라이선스 1社 1-3억', '영구 라이선스 1社 3-7억', '영구 라이선스 1社 5-15억',
    'OEM 라이선스', '종량제 (API 호출당)', '패키지 + 유지보수',
]

TECHS = [
    'Llama 4 + 도메인 LoRA', 'Llama 4 Reasoning', 'Llama 4 Scout (1M)',
    'Llama 4 Vision', 'Llama 4 Voice', 'Llama 4 ×3 다중 합의',
    'Causal AI (DoWhy)', 'GraphRAG (Neo4j)', 'Constitutional AI',
    'Computer Use', 'MCP Tool', 'MemGPT 장기기억',
    'World Models', 'OpenVLA', 'GR00T',
    'Affective Computing', 'Behavioral Biometrics', 'Continuous Auth',
    'Deepfake Detection', 'C2PA', 'AI Workload Protection', 'NHI', 'CSMA', 'DSPM',
    'Federated Learning', 'Confidential Computing', 'Homomorphic', 'DP',
    'Synthetic Data', 'Quantum ML',
]

SUBCATS = ['탐지', '예측', '자동화', '인증', '진단', '점수화', '분석', '관리', '최적화', '통합']

INFRA_MAP = {
    'Quantum': 'IBM Quantum (무료)',
    'World': 'NVIDIA Cluster + Mac Studio',
    'GR00T': 'NVIDIA Cluster + 로봇',
}

def get_infra(tech):
    for k, v in INFRA_MAP.items():
        if k in tech:
            return v
    return 'Mac Studio 1-2대 (1.5-3천만)'

# CORE → HIGH → MED → LOW 정렬
REL_ORDER = {'CORE': 0, 'HIGH': 1, 'MED': 2, 'LOW': 3}
AREAS_SORTED = sorted(enumerate(AREAS, 1), key=lambda x: REL_ORDER[x[1][3]])

parts = []
for orig_idx, (emoji, name, pkg_prefix, rel) in AREAS_SORTED:
    bg, txt, rel_label = REL_STYLE[rel]
    base = (orig_idx - 1) * 30
    border_style = f'border-left:8px solid {bg}'
    if rel in ['CORE', 'HIGH']:
        border_style += f';box-shadow:0 4px 12px {bg}66'

    parts.append(f"""
<div class="area" id="a{orig_idx}" style="{border_style}">
  <div class="area-head" style="background:{bg};color:{txt}">
    <div class="ae">{emoji}</div>
    <div style="flex:1">
      <div class="an">{orig_idx}. {name}</div>
      <div class="ao">자사 패키지: {pkg_prefix}-* · #{base+1:04d}-#{base+30:04d}</div>
    </div>
    <div class="rel" style="color:{txt}">{rel_label}</div>
  </div>
  <div class="grid">""")

    for i in range(30):
        sub_idx = i // 3
        tech_idx = i % len(TECHS)
        sub = SUBCATS[sub_idx]
        tech = TECHS[tech_idx]
        prod_num = base + i + 1
        # 자사 패키지명 (MicroXXX-{기술 약어}-{번호})
        tech_short = tech.split()[0].replace('Llama', 'L4').replace('Causal', 'Cau').replace('GraphRAG', 'GR')[:5]
        pkg_name = f'{pkg_prefix}-{tech_short}-{i+1:02d}'
        what = f'{name} {sub} — {tech} 기반 자사 패키지'
        how = f'① {tech} → ② {name} 도메인 LoRA → ③ 패키지화 (라이선스 모델)'
        infra = get_infra(tech)
        lic = LICENSE_MODELS[prod_num % len(LICENSE_MODELS)]

        parts.append(f"""<div class="c">
  <div class="ch"><div class="cn">#{prod_num:04d}</div><div class="cnm">{pkg_name}</div></div>
  <div class="ct">🦙 {tech}</div>
  <div class="cw">📋 {what}</div>
  <div class="cho"><strong>🔧:</strong> {how}</div>
  <div class="cif"><strong>💻:</strong> {infra}</div>
  <div class="cm"><span>📜 라이선스:</span><span class="rv">{lic}</span></div>
</div>""")
    parts.append("  </div>\n</div>")

core_count = sum(1 for _, _, _, r in AREAS if r == 'CORE')
high_count = sum(1 for _, _, _, r in AREAS if r == 'HIGH')
med_count = sum(1 for _, _, _, r in AREAS if r == 'MED')
low_count = sum(1 for _, _, _, r in AREAS if r == 'LOW')

# 목차 (CORE·HIGH 위주 Top 50)
nav_html = '\n'.join([
    f'<a href="#a{orig_idx}" style="color:{REL_STYLE[rel][1]};background:{REL_STYLE[rel][0]}33">[{rel}] {orig_idx}. {name}</a>'
    for orig_idx, (_, name, _, rel) in AREAS_SORTED[:50]
])

HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>ITCEN CORE 솔루션 회사 — 100 영역 3000 신상품 (v3)</title>
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
  .sm-core .n{{color:#5D4037}}.sm-high .n{{color:#1B5E20}}.sm-med .n{{color:#0D47A1}}.sm-low .n{{color:#616161}}

  .nav{{position:fixed;top:16px;right:16px;background:#fff;border-radius:8px;padding:10px;box-shadow:0 3px 12px rgba(0,0,0,.15);font-size:10px;max-height:88vh;overflow-y:auto;border:1px solid #DDD;z-index:100;width:240px}}
  .nav strong{{display:block;margin-bottom:6px;color:#0D47A1;font-size:11px}}
  .nav a{{display:block;padding:3px 8px;text-decoration:none;font-size:10px;border-radius:3px;margin-bottom:1px}}

  .area{{background:#fff;border-radius:10px;padding:18px 22px;margin-bottom:18px;box-shadow:0 2px 8px rgba(0,0,0,.05)}}
  .area-head{{padding:12px 18px;border-radius:8px;margin:-18px -22px 14px;display:flex;align-items:center;gap:14px}}
  .ae{{font-size:32px;background:#fff;width:52px;height:52px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
  .an{{font-size:18px;font-weight:700}}
  .ao{{font-size:11.5px;opacity:.92;margin-top:2px}}
  .rel{{font-size:11px;font-weight:700;padding:5px 10px;background:rgba(255,255,255,.7);border-radius:14px;white-space:nowrap}}

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
  .cm .rv{{background:#FFE0B2;color:#BF360C;padding:1px 8px;border-radius:4px;font-weight:700}}

  .ft{{text-align:center;margin-top:24px;padding:18px;color:#888;font-size:11.5px;border-top:1px solid #DDD;line-height:1.7}}
</style>
</head>
<body>

<div class="nav">
<strong>📋 솔루션 우선 (CORE→HIGH→MED)</strong>
{nav_html}
</div>

<div class="hero">
  <h1>🎯 ITCEN CORE 솔루션 회사 — 100 영역 3000 신상품 (v3)</h1>
  <h2>솔루션 패키지 회사 관점 · Micro 시리즈 + 라이선스 모델</h2>
  <div class="m">
    <strong>📌 ITCEN CORE = 솔루션 회사</strong> (컨설팅·SI X). 모든 신상품 = 자사 패키지 (Micro***-AI 형식) + 라이선스 모델 (월구독·영구·OEM)<br>
    <strong style="color:#FFC107">⭐⭐⭐ CORE</strong> 자사 패키지 즉시 가능 (사이버보안·내부회계·CCP·VMS·부서IP)<br>
    <strong style="color:#FFC107">⭐⭐ HIGH</strong> 패키지화 가능 (CCTV·금융 세분·데이터 거버넌스·LLM 응용)<br>
    <strong style="color:#FFC107">⭐ MED</strong> 그룹·OEM 협업 (클라우드·통신 등)<br>
    <strong style="color:#FFC107">○ LOW</strong> 솔루션화 어려움 (건설·의료·산업·라이프 — 컨설팅·SI 영역)
  </div>
</div>

<div class="summary">
  <div class="summary-item sm-core"><div class="n">{core_count}</div><div class="l">⭐⭐⭐ CORE<br>자사 패키지 즉시</div></div>
  <div class="summary-item sm-high"><div class="n">{high_count}</div><div class="l">⭐⭐ HIGH<br>패키지화 가능</div></div>
  <div class="summary-item sm-med"><div class="n">{med_count}</div><div class="l">⭐ MED<br>그룹·OEM</div></div>
  <div class="summary-item sm-low"><div class="n">{low_count}</div><div class="l">○ LOW<br>솔루션화 어려움</div></div>
</div>

{''.join(parts)}

<div class="ft">
  100 영역 × 30 신상품 = 3,000 솔루션 패키지 (v3)<br>
  Micro 시리즈 + 라이선스 모델 · 솔루션 회사 관점<br>
  작성: 2026-06-04
</div>

</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f'Wrote: {OUT}')
print(f'CORE: {core_count} · HIGH: {high_count} · MED: {med_count} · LOW: {low_count}')
print(f'Size: {os.path.getsize(OUT) / 1024:.1f} KB')
