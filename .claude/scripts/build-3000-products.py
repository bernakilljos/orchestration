"""3000 신상품 HTML — 30 영역 × 100 신상품 자동 생성

각 영역에 100 신상품 = sub-카테고리-세부 시나리오-산업별 변형
모두 Llama 4 base + Mac Studio 인프라
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'outputs', 'itcen', 'html', 'itcen-core-3000신상품.html')

# 30 영역 (300 신상품 base 동일)
AREAS_BASE = [
    ('', '내부회계', '국내 1위 MicroICM-C'),
    ('⚖', 'CCP 준법', 'EPM-Compliance 1위'),
    ('', '건설 ERP', '국내 1위'),
    ('', '카지노 VMS', '9社 독점'),
    ('', '금융 VMS', '은행-증권 30+'),
    ('', 'AI CCTV', '영상 분석'),
    ('', '디지털트윈', '제조-건설-인프라'),
    ('⚙', 'ITO', 'IT 아웃소싱'),
    ('', 'ESG-GRC', '거버넌스'),
    ('', '부서 IP', '한국 K-Standard'),
    ('', '공공-전자정부', 'ENTEC 협업'),
    ('☁', '클라우드', 'CTS-CLOIT'),
    ('', '사이버보안', 'PNS 협업'),
    ('[STAT]', '데이터-AI 거버넌스', '데이터 라이프사이클'),
    ('', '의료-헬스케어', 'AI 진료'),
    ('', '교육-이러닝', 'AI 튜터'),
    ('', '유통-이커머스', 'AI 추천-결제'),
    ('', '제조 SI', '스마트팩토리'),
    ('', '물류-SCM', '공급망-운송'),
    ('', '미디어-콘텐츠', '영상-음악'),
    ('', '농업-스마트팜', '농업 AI'),
    ('[FAST]', '에너지-SMR', '발전-전력망'),
    ('', '자율주행-모빌리티', '자율시스템'),
    ('[GO]', '우주-항공', '위성-발사'),
    ('', '신소재-반도체', 'AI 신소재'),
    ('', '바이오-신약', 'AI 신약'),
    ('', 'K-방산', '국방-무기'),
    ('⚛', '양자컴퓨팅', 'IBM Quantum'),
    ('', '휴머노이드-로봇', '로봇 AI'),
    ('', '합성데이터-신영역', '미래 사업'),
]

# 신기술 100개 (각 영역에 적용)
TECHS = [
    'Llama 4 + LoRA fine-tune', 'Llama 4 Reasoning (o3급)', 'Llama 4 Scout (1M context)',
    'Llama 4 Multimodal Vision', 'Llama 4 Voice (Whisper+TTS)', 'Llama 4 ×3 다중 합의',
    'Llama 4 + Causal AI (DoWhy)', 'Llama 4 + GraphRAG (Neo4j)', 'Llama 4 + Constitutional',
    'Llama 4 + Computer Use', 'Llama 4 + Tool Use (MCP)', 'Llama 4 + Memory (MemGPT)',
    'Mixture of Experts (DeepSeek V3 ported)', 'State Space Models (Mamba)', 'Test-Time Compute',
    'NVIDIA Cosmos World Model', 'OpenVLA (Vision-Language-Action)', 'NVIDIA GR00T (Humanoid)',
    'Sim-to-Real Transfer (Isaac)', 'Embodied AI', 'Affective Computing (Hume style)',
    'Behavioral Biometrics', 'Continuous Authentication', 'Passkeys/FIDO2', 'Deepfake Detection',
    'C2PA Content Provenance', 'AI Workload Protection', 'Non-Human Identity (NHI)',
    'CSMA (Cybersecurity Mesh)', 'DSPM', 'Federated Learning (Flower)', 'Confidential Computing',
    'Homomorphic Encryption', 'Differential Privacy', 'Synthetic Data Generation',
    'Mechanistic Interpretability', 'Bias Detection (Fairlearn)', 'Explainability (SHAP/LIME)',
    'AI Governance (ISO 42001)', 'Vector DB (ChromaDB)', 'HyDE', 'Long Context 1M+',
    'GraphRAG (Microsoft)', 'HippoRAG', 'RAPTOR', 'Corrective RAG', 'Adaptive RAG',
    'Multi-Agent (LangGraph)', 'Reflexion', 'Constitutional AI', 'RLHF-DPO-KTO',
    'LoRA-QLoRA-DoRA', 'Knowledge Distillation', 'Speculative Decoding', 'FlashAttention 3',
    'Quantization (GPTQ/AWQ)', 'Quantum ML (IBM)', 'Variational Quantum Circuit',
    'Quantum Optimization (QAOA)', 'PQC Migration (NIST)', 'Generative Video (Sora style)',
    'Text-to-3D', 'Voice Cloning', 'Music Generation', 'Avatar Generation',
    'Edge AI (Hailo/Jetson)', 'Neuromorphic (Loihi)', 'Photonic Computing',
    'Drone Detection', 'GPS Spoofing Defense', 'TEMPEST Defense', 'OT/ICS Security',
    '5G Private Network', 'WiFi Sensing', 'mmWave Radar', 'LiDAR 3D',
    'Spatial Computing (Vision Pro)', 'AR/VR 통합', 'Digital Twin Cybersecurity',
    'World Models for Robotics', 'Climate AI (GraphCast)', 'MatterGen (신소재)',
    'AlphaFold 3 (단백질)', 'Medical LLM (Med-PaLM)', 'Legal LLM (Harvey)',
    'Financial LLM (BloombergGPT)', 'Code Agent (Cursor/Devin)', 'AI Search (Perplexity)',
    'Ambient Intelligence', 'BCI (Brain-Computer)', 'Cyber Resilience Score',
    'Compliance Auto (Gov)', 'Audit Automation', 'Risk Score Bureau',
    'Self-Improving AI (AlphaEvolve)', 'Co-Scientist (AI 과학자)', 'AGI Governance',
    'Reasoning Chain Verifier', 'Causal Graph Builder', 'Active Learning',
    'Meta-Learning (MAML)', 'Continual Learning', 'Imitation Learning'
]

# 인프라 매핑
INFRA_MAP = {
    'Quantum': 'IBM Quantum Cloud (무료)',
    'NVIDIA Cosmos': 'NVIDIA Cluster (1억) + Mac Studio 3대',
    'GR00T': 'NVIDIA Cluster + 로봇 HW',
    'Humanoid': 'Mac Studio 3대 + Robot HW',
    'AlphaFold': 'Mac Studio 3대 + GPU',
    'MatterGen': 'Mac Studio 2대 + GPU',
    'Drone': 'Mac Studio 1대 + 드론 센서',
    'LiDAR': 'Mac Studio 1대 + LiDAR',
    'Vision Pro': 'Vision Pro + Mac Studio',
    'Spatial': 'Vision Pro + Mac Studio',
    'Edge AI': 'Edge 칩 (대당 100만)',
    'BCI': 'Mac Studio 1대 + BCI HW',
    '5G': 'Mac Studio 1대 + 5G 기지국',
    'mmWave': 'Mac Studio 1대 + mmWave 센서',
    'Federated': '각 사 Mac Studio 1대씩',
}

def get_infra(tech):
    for key, val in INFRA_MAP.items():
        if key in tech:
            return val
    return 'Mac Studio 1-2대 (1.5-3천만)'

# 매출 추정 (시나리오 다양)
REVENUES = [
    '1社 1-3억', '1社 3-7억', '1社 5-15억', '월 100-500만', '월 500-2000만',
    'B2G 5-30억', 'B2G 30-100억', '대당 1-3억', '대당 3-10억', '인증 5천만-3억',
    '1프로젝트 3-10억', '1프로젝트 10-30억', 'OEM 라이선스', 'API 종량제',
    '데이터 라이선스', '컨설팅', '월구독 100-1000만'
]

# 영역별 sub-카테고리 (각 영역에 10 sub × 10 신상품 = 100/영역)
def gen_subcats(area_name):
    """영역별 sub-카테고리 10개"""
    common_subs = [
        '진단-자동탐지', '예측-예방', '자동화-운영', '컨설팅-인증', '글로벌 진출',
        '한국 표준화', '데이터 마켓', '교육-자격', '플랫폼 SaaS', '통합 SI'
    ]
    return common_subs

# 영역별 100 신상품 생성
def gen_products(area_idx, emoji, area_name, sub_desc):
    subcats = gen_subcats(area_name)
    products = []
    base_num = area_idx * 100
    for i in range(100):
        sub_idx = i // 10  # 0-9 sub-카테고리
        tech_idx = i % len(TECHS)
        sub = subcats[sub_idx]
        tech = TECHS[tech_idx]

        # 신상품 이름 (영역 약어 + sub + 번호)
        area_short = area_name.replace('-', '-').replace(' ', '')[:8]
        name = f'{area_short}-{sub[:4]}-{i+1:02d}'

        # 무엇 (한 줄)
        what = f'{area_name} {sub} — {tech} 활용. {area_name} 도메인 특화 자동화-정확도 향상.'

        # 어떻게
        how = f'① {tech} base 운영 -> ② {area_name} 도메인 데이터 LoRA 학습 -> ③ 자사 패키지 모듈 통합'

        # 인프라
        infra = get_infra(tech)

        # 대상-매출 (랜덤 풀에서)
        target = f'{area_name} 도입 기업'
        rev = REVENUES[(base_num + i) % len(REVENUES)]

        products.append((base_num + i + 1, name, tech, what, how, infra, target, rev))
    return products


# HTML 생성
COLORS = ['1976D2','7B1FA2','E64A19','388E3C','0288D1','9C27B0','455A64','9E9D24','558B2F','FFA000',
          '00838F','5D4037','827717','6A1B9A','C2185B','283593','00695C','EF6C00','BF360C','37474F',
          '1A237E','004D40','3E2723','311B92','880E4F','01579B','BF360C','0D47A1','4A148C','E65100']

cards_html_parts = []
for area_idx, (emoji, area_name, sub_desc) in enumerate(AREAS_BASE):
    color = COLORS[area_idx % len(COLORS)]
    products = gen_products(area_idx, emoji, area_name, sub_desc)

    cards_html_parts.append(f"""
<div class="area" id="area{area_idx+1}" style="border-left-color:#{color}">
  <div class="area-head" style="background:linear-gradient(90deg,#{color},#{color}AA)">
    <div class="area-emoji">{emoji}</div>
    <div class="area-info"><div class="area-name">{area_idx+1}. {area_name} (100개)</div><div class="area-old">{sub_desc} - #{products[0][0]:04d}-#{products[-1][0]:04d}</div></div>
  </div>
  <div class="grid">""")

    for prod_num, name, tech, what, how, infra, target, rev in products:
        cards_html_parts.append(f"""
    <div class="card">
      <div class="card-head"><div class="card-num">#{prod_num:04d}</div><div class="card-name">{name}</div></div>
      <div class="card-tech"> {tech}</div>
      <div class="card-what">[LIST] {what}</div>
      <div class="card-how"><strong>[FIX] 어떻게:</strong> {how}</div>
      <div class="card-infra"><strong> 인프라:</strong> {infra}</div>
      <div class="card-meta"><span class="lbl">대상:</span><span>{target}</span><span class="rev">{rev}</span></div>
    </div>""")
    cards_html_parts.append("  </div>\n</div>")

# 목차
nav_html = '\n'.join([f'  <a href="#area{i+1}" style="display:block;color:#0D47A1;padding:2px 6px;font-size:10.5px">{a[0]} {i+1}. {a[1]}</a>' for i, a in enumerate(AREAS_BASE)])

HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>ITCEN CORE × Llama 4 — 3000 신상품 카탈로그</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'맑은 고딕',sans-serif;background:#F5F5F0;padding:24px;line-height:1.5;font-size:12px}}
  .hero{{background:linear-gradient(135deg,#0D2A4D,#1565C0);color:#fff;padding:24px 30px;border-radius:12px;margin-bottom:20px;box-shadow:0 4px 14px rgba(13,42,77,.2)}}
  .hero h1{{font-size:24px;margin-bottom:6px}}
  .hero h2{{font-size:13px;opacity:.92;margin-bottom:10px}}
  .hero .msg{{background:rgba(255,255,255,.15);padding:10px 14px;border-radius:8px;font-size:12px;line-height:1.6}}
  .hero .msg strong{{color:#FFC107}}

  .nav{{position:fixed;top:16px;right:16px;background:#fff;border-radius:8px;padding:10px;box-shadow:0 3px 10px rgba(0,0,0,.15);font-size:10px;max-height:88vh;overflow-y:auto;border:1px solid #DDD;z-index:100;width:200px}}
  .nav strong{{display:block;margin-bottom:4px;color:#0D47A1;font-size:11px}}
  .nav a:hover{{background:#E3F2FD}}

  .area{{background:#fff;border-radius:10px;padding:16px 20px;margin-bottom:18px;box-shadow:0 2px 8px rgba(0,0,0,.05);border-left:6px solid #0D47A1}}
  .area-head{{padding:10px 16px;border-radius:8px;margin:-16px -20px 12px;color:#fff;display:flex;align-items:center;gap:12px}}
  .area-emoji{{font-size:28px;flex-shrink:0;background:#fff;width:48px;height:48px;border-radius:10px;display:flex;align-items:center;justify-content:center}}
  .area-name{{font-size:17px;font-weight:700}}
  .area-old{{font-size:11px;opacity:.95;margin-top:1px}}

  .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
  .card{{background:#FAFBFC;border:1px solid #E0E0E0;border-left:3px solid #0D47A1;border-radius:6px;padding:8px 10px;font-size:10.5px}}
  .card-head{{display:flex;align-items:center;gap:6px;margin-bottom:4px}}
  .card-num{{background:#0D47A1;color:#fff;padding:1px 6px;border-radius:8px;font-weight:700;font-size:9px;flex-shrink:0}}
  .card-name{{font-weight:700;color:#0D47A1;font-size:11px}}
  .card-tech{{font-size:9.5px;color:#7B1FA2;margin-bottom:3px;font-weight:600}}
  .card-what{{font-size:10px;color:#444;line-height:1.45;margin-bottom:3px}}
  .card-how{{background:#FFF8E1;border-left:2px solid #FFA000;padding:3px 6px;border-radius:3px;font-size:9.5px;color:#5D4037;line-height:1.4;margin-bottom:3px}}
  .card-how strong{{color:#E65100}}
  .card-infra{{background:#E3F2FD;border-left:2px solid #1976D2;padding:3px 6px;border-radius:3px;font-size:9.5px;color:#0D47A1;margin-bottom:3px}}
  .card-infra strong{{color:#0D47A1}}
  .card-meta{{font-size:9px;color:#666;display:flex;gap:6px;flex-wrap:wrap;margin-top:3px;padding-top:3px;border-top:1px dashed #E0E0E0}}
  .card-meta .lbl{{font-weight:700;color:#1565C0}}
  .card-meta .rev{{background:#E8F5E9;color:#1B5E20;padding:1px 5px;border-radius:4px;font-weight:700}}

  .footer{{text-align:center;margin-top:20px;padding:18px;color:#888;font-size:10.5px;border-top:1px solid #DDD;line-height:1.7}}
</style>
</head>
<body>

<div class="nav">
  <strong>[LIST] 3000 신상품 목차 (30 영역)</strong>
{nav_html}
</div>

<div class="hero">
  <h1>[TGT] ITCEN CORE × Llama 4 — 3000 신상품 카탈로그</h1>
  <h2>30 영역 × 각 100 신상품 = 3000 사업 아이디어 - 모든 LLM = Llama 4 자체 운영</h2>
  <div class="msg">
    <strong> 각 카드:</strong> 신상품명 +  신기술 + [LIST] 무엇 + [FIX] 어떻게 +  인프라 + 대상 + 매출<br>
    <strong style="color:#FFC107"> LLM 모두 Llama 4 (오픈소스-자체 운영)</strong> — API 비용 0-데이터 유출 X-한국 도메인 LoRA 자유<br>
    <strong style="color:#FFC107"> 자체 인프라:</strong> Mac Studio M3 Ultra 512GB (1,500만원/대) - 양자=IBM Quantum 무료 - 로봇=별도 HW - BCI=별도 HW<br>
    <strong style="color:#FFC107">[STAT] 영역당 100 신상품:</strong> 10 sub-카테고리 (진단-예측-자동화-컨설팅-글로벌-표준-데이터-교육-SaaS-통합SI) × 10 신기술 변형
  </div>
</div>

{''.join(cards_html_parts)}

<div class="footer">
  ITCEN CORE × Llama 4 — 3000 신상품 (30 영역 × 100) - 자동 생성<br>
  작성: 2026-06-04 - 행동위험 외 ITCEN 자사 + 신영역 30 영역 모두 cover<br>
  세부 카드는 100-300 신상품 (별도 HTML) 참조
</div>

</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)
total = len(AREAS_BASE) * 100
print(f'Wrote: {OUT}')
print(f'Total products: {total}')
print(f'File size: {os.path.getsize(OUT) / 1024:.1f} KB')
