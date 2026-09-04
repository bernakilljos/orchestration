"""100 신기술 영역 × 각 30 신상품 = 3000 신상품 HTML

영역 100개 = 기존 30 + 70 추가 세분화
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'outputs', 'itcen', 'html', 'itcen-core-100영역-3000신상품.html')

# 100 신기술 영역 (이모지-이름-세부 설명)
AREAS = [
    # ── 자사 솔루션 (10) ──
    ('', '내부회계', '국내 1위 MicroICM-C'),
    ('⚖', 'CCP 준법경영', 'EPM-Compliance 1위'),
    ('', '건설 ERP', '국내 1위'),
    ('', '카지노 VMS', '9社 독점'),
    ('', '금융 VMS', '은행-증권-카드'),
    ('', 'AI CCTV', '영상 분석'),
    ('', '디지털트윈', '제조-건설-인프라'),
    ('⚙', 'ITO 운영', 'IT 아웃소싱'),
    ('', 'ESG-GRC', '거버넌스'),
    ('', '부서 IP', 'K-Standard'),
    # ── 그룹-신영역 (10) ──
    ('', '공공-전자정부', 'ENTEC 협업'),
    ('☁', '클라우드', 'CTS-CLOIT'),
    ('', '사이버보안', 'PNS 협업'),
    ('[STAT]', '데이터 거버넌스', '데이터 관리'),
    ('', '의료 종합', 'AI 진료'),
    ('', '교육-이러닝', 'AI 튜터'),
    ('', '유통-이커머스', 'AI 추천'),
    ('', '제조 SI', '스마트팩토리'),
    ('', '물류-SCM', '공급망'),
    ('', '미디어-콘텐츠', '영상-음악'),
    # ── 산업 (10) ──
    ('', '농업-스마트팜', '농업 AI'),
    ('[FAST]', '에너지-SMR', '발전-전력'),
    ('', '자율주행', '모빌리티'),
    ('[GO]', '우주-항공', '위성-발사'),
    ('', '신소재', 'AI 발견'),
    ('', '바이오-신약', 'AI 신약'),
    ('', 'K-방산', '국방-무기'),
    ('⚛', '양자컴퓨팅', 'IBM Quantum'),
    ('', '휴머노이드', '로봇 AI'),
    ('', '합성데이터', '데이터 마켓'),
    # ── 의료 세분 (10) ──
    ('', '진료-EHR', 'AI scribe'),
    ('', '진단-영상', 'Med 영상 판독'),
    ('', '예방-검진', 'AI 검진'),
    ('', '임상시험', 'AI CRO'),
    ('', '재활-정형', 'AI 재활'),
    ('', '정신건강', 'AI 상담'),
    ('', '약학-복약', 'AI 처방'),
    ('‍⚕', '간호 AI', '간호 보조'),
    ('', '요양-노인', 'AI 돌봄'),
    ('', '치의학-구강', 'AI 진단'),
    # ── 금융 세분 (10) ──
    ('', '카드-결제', 'AI 결제'),
    ('', '은행 코어', '코어뱅킹'),
    ('[UP]', '증권-트레이딩', 'AI 트레이딩'),
    ('', '보험 AI', '인수-청구'),
    ('', '자산운용', 'AI 펀드'),
    ('₿', '암호-핀테크', 'DeFi AI'),
    ('', 'CBDC', '한은 디지털'),
    ('[STAT]', '신용평가', 'AI 신용'),
    ('', '부동산-리츠', 'AI 가치평가'),
    ('', 'WM-HNWI', 'AI 자문'),
    # ── 사이버 보안 세분 (10) ──
    ('', '인증-IAM', 'AI 신원'),
    ('', '접근통제', 'Zero Trust'),
    ('', '암호-PKI', 'PQC'),
    ('', 'SOC-관제', '24/7 자율'),
    ('', '사고대응 IR', 'AI SOAR'),
    ('[SIG]', '포렌식', 'AI 분석'),
    ('[LIST]', '보안 감사', 'AI Audit'),
    ('', '보안 교육', 'AI 인식'),
    ('', '보안 정책', 'AI 정책'),
    ('', '보안 인증', 'ISMS-P'),
    # ── 데이터-AI 세분 (10) ──
    ('', '데이터 카탈로그', 'AI 카탈로그'),
    ('', '데이터 파이프', 'ETL AI'),
    ('', '데이터 라인age', '추적 AI'),
    ('[NEW]', '데이터 품질', 'AI 검증'),
    ('', '데이터 프라이버시', 'PET'),
    ('', 'Data Mesh', '분산 거버넌스'),
    ('', 'MLOps', 'AI 운영'),
    ('', '모델 라이프', 'AI 관리'),
    ('[TGT]', 'AI Governance', 'ISO 42001'),
    ('⚖', 'AI 윤리', 'Bias-Fairness'),
    # ── LLM 응용 세분 (10) ──
    ('', 'LLM Chatbot', '기업 챗봇'),
    ('', 'LLM Agent', 'Agentic AI'),
    ('', 'Reasoning', 'o3급 추론'),
    ('', 'Code Agent', 'Devin-Cursor'),
    ('', '문서 LLM', '회사 KB'),
    ('', '음성 LLM', 'Voice Native'),
    ('', 'Vision LLM', '이미지 이해'),
    ('', 'Video LLM', '영상 이해'),
    ('', '다국어 LLM', 'Translation'),
    ('[TGT]', 'Domain LLM', '특화 LLM'),
    # ── 신영역-미래 (10) ──
    ('', '기후-날씨', 'Climate AI'),
    ('', '합성생물', 'BioDesign'),
    ('', '미생물-식품', 'Microbiome'),
    ('', '수산-해양', 'Ocean AI'),
    ('', '임업-산림', 'Forest AI'),
    ('♻', '재활용-환경', 'Circular AI'),
    ('', '수자원-수도', 'Water AI'),
    ('⚱', '폐기물', 'Waste AI'),
    ('', '재난-재해', 'Disaster AI'),
    ('', '문화재-문화', 'Heritage AI'),
    # ── 라이프-소비 (10) ──
    ('', '식품-외식', 'F&B AI'),
    ('', '패션-뷰티', 'Fashion AI'),
    ('', '게임-메타버스', 'Game AI'),
    ('', '엔터테인먼트', 'Entertainment'),
    ('✈', '관광-여행', 'Travel AI'),
    ('⚽', '스포츠 AI', 'Sports Analytics'),
    ('', '통신-5G', 'Telecom AI'),
    ('', '자동차 일반', 'Auto AI'),
    ('', '화학-석유', 'Chemical AI'),
    ('', '부동산 일반', 'PropTech'),
]

# 신기술 풀 (각 영역에 적용)
TECHS = [
    'Llama 4 + 도메인 LoRA', 'Llama 4 Reasoning (o3급)', 'Llama 4 Scout (1M context)',
    'Llama 4 Vision (Multimodal)', 'Llama 4 Voice (실시간)', 'Llama 4 ×3 다중 합의',
    'Llama 4 + Causal AI (DoWhy)', 'Llama 4 + GraphRAG (Neo4j)', 'Llama 4 + Constitutional',
    'Llama 4 + Computer Use', 'Llama 4 + MCP Tool', 'Llama 4 + MemGPT 장기기억',
    'NVIDIA Cosmos World Model', 'OpenVLA (Vision-Language-Action)', 'NVIDIA GR00T (Humanoid)',
    'Sim-to-Real (Isaac)', 'Affective Computing', 'Behavioral Biometrics',
    'Continuous Authentication', 'Deepfake Detection', 'C2PA Watermark',
    'AI Workload Protection', 'NHI (Non-Human Identity)', 'CSMA', 'DSPM',
    'Federated Learning (Flower)', 'Confidential Computing', 'Homomorphic Encryption',
    'Differential Privacy', 'Synthetic Data', 'Quantum ML (IBM)',
]

SUBCATS = ['진단-자동탐지', '예측-예방', '자동화-운영', '컨설팅-인증', '글로벌 진출',
           '한국 표준', '데이터 마켓', '교육-자격', 'SaaS', '통합 SI']

INFRA_MAP = {
    'Quantum': 'IBM Quantum (무료)',
    'Cosmos': 'NVIDIA Cluster (1억) + Mac Studio',
    'GR00T': 'NVIDIA Cluster + 로봇 HW',
    'Humanoid': 'Mac Studio 3대 + Robot',
    'AlphaFold': 'Mac Studio 3대 + GPU',
    'BCI': 'Mac Studio + BCI HW',
}

REVENUES = ['1社 1-3억', '1社 3-7억', '월 100-500만', '월 500-2000만',
            'B2G 5-30억', '대당 1-3억', '1프로젝트 3-10억', '월구독 100-1000만',
            'OEM 라이선스', '데이터 라이선스']


def get_infra(tech):
    for key, val in INFRA_MAP.items():
        if key in tech:
            return val
    return 'Mac Studio 1-2대 (1.5-3천만)'


COLORS = ['1976D2','7B1FA2','E64A19','388E3C','0288D1','9C27B0','455A64','9E9D24','558B2F','FFA000',
          '00838F','5D4037','827717','6A1B9A','C2185B','283593','00695C','EF6C00','BF360C','37474F'] * 5

parts = []
for area_idx, (emoji, area_name, sub_desc) in enumerate(AREAS):
    color = COLORS[area_idx % len(COLORS)]
    base = area_idx * 30

    parts.append(f"""
<div class="area" id="a{area_idx+1}" style="border-left-color:#{color}">
  <div class="area-head" style="background:linear-gradient(90deg,#{color},#{color}AA)">
    <div class="ae">{emoji}</div>
    <div><div class="an">{area_idx+1}. {area_name} (30개)</div><div class="ao">{sub_desc} - #{base+1:04d}-#{base+30:04d}</div></div>
  </div>
  <div class="grid">""")

    for i in range(30):
        sub_idx = i // 3
        tech_idx = i % len(TECHS)
        sub = SUBCATS[sub_idx]
        tech = TECHS[tech_idx]
        prod_num = base + i + 1
        name = f'{area_name[:6]}-{sub[:4]}-{i+1:02d}'
        what = f'{area_name} {sub} — {tech} 기반 자동화-정확도 향상'
        how = f'① {tech} -> ② {area_name} 도메인 LoRA -> ③ 자사 모듈 통합'
        infra = get_infra(tech)
        target = f'{area_name} 도입 기업'
        rev = REVENUES[prod_num % len(REVENUES)]

        parts.append(f"""<div class="c">
  <div class="ch"><div class="cn">#{prod_num:04d}</div><div class="cnm">{name}</div></div>
  <div class="ct"> {tech}</div>
  <div class="cw">[LIST] {what}</div>
  <div class="cho"><strong>[FIX]:</strong> {how}</div>
  <div class="cif"><strong>:</strong> {infra}</div>
  <div class="cm"><span>대상: {target}</span><span class="rv">{rev}</span></div>
</div>""")
    parts.append("  </div>\n</div>")

# 목차
nav_html = '\n'.join([f'<a href="#a{i+1}">{a[0]} {i+1}. {a[1]}</a>' for i, a in enumerate(AREAS)])

HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>ITCEN CORE × Llama 4 — 100 영역 3000 신상품</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'맑은 고딕',sans-serif;background:#F5F5F0;padding:20px;line-height:1.45;font-size:11px}}
  .hero{{background:linear-gradient(135deg,#0D2A4D,#1565C0);color:#fff;padding:22px 28px;border-radius:12px;margin-bottom:18px}}
  .hero h1{{font-size:22px;margin-bottom:6px}}
  .hero h2{{font-size:13px;opacity:.92;margin-bottom:10px}}
  .hero .m{{background:rgba(255,255,255,.15);padding:10px 14px;border-radius:8px;font-size:11.5px;line-height:1.6}}
  .hero .m strong{{color:#FFC107}}

  .nav{{position:fixed;top:14px;right:14px;background:#fff;border-radius:8px;padding:8px;box-shadow:0 3px 10px rgba(0,0,0,.15);font-size:9.5px;max-height:90vh;overflow-y:auto;border:1px solid #DDD;z-index:100;width:200px}}
  .nav strong{{display:block;margin-bottom:4px;color:#0D47A1;font-size:10.5px}}
  .nav a{{display:block;color:#0D47A1;text-decoration:none;padding:1px 5px;font-size:9.5px}}
  .nav a:hover{{background:#E3F2FD}}

  .area{{background:#fff;border-radius:9px;padding:14px 18px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.05);border-left:5px solid #0D47A1}}
  .area-head{{padding:9px 14px;border-radius:7px;margin:-14px -18px 10px;color:#fff;display:flex;align-items:center;gap:10px}}
  .ae{{font-size:24px;background:#fff;width:42px;height:42px;border-radius:8px;display:flex;align-items:center;justify-content:center}}
  .an{{font-size:15px;font-weight:700}}
  .ao{{font-size:10px;opacity:.95;margin-top:1px}}

  .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}}
  .c{{background:#FAFBFC;border:1px solid #E0E0E0;border-left:3px solid #0D47A1;border-radius:5px;padding:6px 8px;font-size:9.5px}}
  .ch{{display:flex;align-items:center;gap:5px;margin-bottom:3px}}
  .cn{{background:#0D47A1;color:#fff;padding:1px 5px;border-radius:6px;font-weight:700;font-size:8px}}
  .cnm{{font-weight:700;color:#0D47A1;font-size:10px}}
  .ct{{font-size:9px;color:#7B1FA2;margin-bottom:2px;font-weight:600}}
  .cw{{font-size:9px;color:#444;line-height:1.4;margin-bottom:2px}}
  .cho{{background:#FFF8E1;border-left:2px solid #FFA000;padding:2px 5px;border-radius:3px;font-size:8.5px;color:#5D4037;line-height:1.35;margin-bottom:2px}}
  .cho strong{{color:#E65100}}
  .cif{{background:#E3F2FD;border-left:2px solid #1976D2;padding:2px 5px;border-radius:3px;font-size:8.5px;color:#0D47A1;margin-bottom:2px}}
  .cif strong{{color:#0D47A1}}
  .cm{{font-size:8.5px;color:#666;display:flex;gap:5px;flex-wrap:wrap;margin-top:2px;padding-top:2px;border-top:1px dashed #E0E0E0}}
  .cm .rv{{background:#E8F5E9;color:#1B5E20;padding:0 5px;border-radius:3px;font-weight:700}}

  .ft{{text-align:center;margin-top:20px;padding:16px;color:#888;font-size:10px;border-top:1px solid #DDD}}
</style>
</head>
<body>

<div class="nav">
<strong>[LIST] 100 영역 (3000)</strong>
{nav_html}
</div>

<div class="hero">
  <h1>[TGT] ITCEN CORE × Llama 4 — 100 신기술 영역 × 3000 신상품</h1>
  <h2>30 영역 부족 -> 100 영역으로 확장 - 각 영역 30 신상품</h2>
  <div class="m">
    <strong> 영역 100개:</strong> 자사 솔루션 10 + 그룹-신영역 10 + 산업 10 + 의료세분 10 + 금융세분 10 + 보안세분 10 + 데이터-AI 10 + LLM응용 10 + 신영역 10 + 미래 10<br>
    <strong style="color:#FFC107"> 모든 LLM = Llama 4 자체 운영</strong> (API 비용 0) - <strong style="color:#FFC107"> 인프라:</strong> Mac Studio M3 Ultra 512GB (1,500만/대)
  </div>
</div>

{''.join(parts)}

<div class="ft">
  100 영역 × 30 신상품 = 3,000 - 작성 2026-06-04 - 행동위험 외 ITCEN 자사 + 신영역 확장
</div>

</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f'Wrote: {OUT}')
print(f'Areas: {len(AREAS)} - Products: {len(AREAS)*30}')
print(f'Size: {os.path.getsize(OUT) / 1024:.1f} KB')
