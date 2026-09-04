# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\build-100-areas.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/build-100-areas.py b/.claude/scripts/build-100-areas.py
new file mode 100644
index 0000000..8e206a0
--- /dev/null
+++ b/.claude/scripts/build-100-areas.py
@@ -0,0 +1,275 @@
+"""100 신기술 영역 × 각 30 신상품 = 3000 신상품 HTML
+
+영역 100개 = 기존 30 + 70 추가 세분화
+"""
+import os
+
+ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+OUT = os.path.join(ROOT, 'outputs', 'itcen', 'html', 'itcen-core-100영역-3000신상품.html')
+
+# 100 신기술 영역 (이모지·이름·세부 설명)
+AREAS = [
+    # ── 자사 솔루션 (10) ──
+    ('📒', '내부회계', '국내 1위 MicroICM-C'),
+    ('⚖', 'CCP 준법경영', 'EPM·Compliance 1위'),
+    ('🏗', '건설 ERP', '국내 1위'),
+    ('🎰', '카지노 VMS', '9社 독점'),
+    ('🏦', '금융 VMS', '은행·증권·카드'),
+    ('📹', 'AI CCTV', '영상 분석'),
+    ('🌐', '디지털트윈', '제조·건설·인프라'),
+    ('⚙', 'ITO 운영', 'IT 아웃소싱'),
+    ('🌱', 'ESG·GRC', '거버넌스'),
+    ('🚨', '부서 IP', 'K-Standard'),
+    # ── 그룹·신영역 (10) ──
+    ('🏛', '공공·전자정부', 'ENTEC 협업'),
+    ('☁', '클라우드', 'CTS·CLOIT'),
+    ('🛡', '사이버보안', 'PNS 협업'),
+    ('', '데이터 거버넌스', '데이터 관리'),
+    ('🏥', '의료 종합', 'AI 진료'),
+    ('', '교육·이러닝', 'AI 튜터'),
+    ('🛒', '유통·이커머스', 'AI 추천'),
+    ('🏭', '제조 SI', '스마트팩토리'),
+    ('🚛', '물류·SCM', '공급망'),
+    ('🎬', '미디어·콘텐츠', '영상·음악'),
+    # ── 산업 (10) ──
+    ('🌾', '농업·스마트팜', '농업 AI'),
+    ('⚡', '에너지·SMR', '발전·전력'),
+    ('🚗', '자율주행', '모빌리티'),
+    ('🚀', '우주·항공', '위성·발사'),
+    ('', '신소재', 'AI 발견'),
+    ('🧬', '바이오·신약', 'AI 신약'),
+    ('🛡', 'K-방산', '국방·무기'),
+    ('⚛', '양자컴퓨팅', 'IBM Quantum'),
+    ('🤖', '휴머노이드', '로봇 AI'),
+    ('🌟', '합성데이터', '데이터 마켓'),
+    # ── 의료 세분 (10) ──
+    ('🩺', '진료·EHR', 'AI scribe'),
+    ('🔬', '진단·영상', 'Med 영상 판독'),
+    ('💉', '예방·검진', 'AI 검진'),
+    ('', '임상시험', 'AI CRO'),
+    ('🦾', '재활·정형', 'AI 재활'),
+    ('🧠', '정신건강', 'AI 상담'),
+    ('💊', '약학·복약', 'AI 처방'),
+    ('👩‍⚕', '간호 AI', '간호 보조'),
+    ('🏨', '요양·노인', 'AI 돌봄'),
+    ('🦷', '치의학·구강', 'AI 진단'),
+    # ── 금융 세분 (10) ──
+    ('💳', '카드·결제', 'AI 결제'),
+    ('🏛', '은행 코어', '코어뱅킹'),
+    ('📈', '증권·트레이딩', 'AI 트레이딩'),
+    ('🏠', '보험 AI', '인수·청구'),
+    ('💰', '자산운용', 'AI 펀드'),
+    ('₿', '암호·핀테크', 'DeFi AI'),
+    ('💵', 'CBDC', '한은 디지털'),
+    ('', '신용평가', 'AI 신용'),
+    ('🏘', '부동산·리츠', 'AI 가치평가'),
+    ('💎', 'WM·HNWI', 'AI 자문'),
+    # ── 사이버 보안 세분 (10) ──
+    ('🔐', '인증·IAM', 'AI 신원'),
+    ('🛂', '접근통제', 'Zero Trust'),
+    ('🔑', '암호·PKI', 'PQC'),
+    ('👁', 'SOC·관제', '24/7 자율'),
+    ('🚨', '사고대응 IR', 'AI SOAR'),
+    ('🔍', '포렌식', 'AI 분석'),
+    ('📋', '보안 감사', 'AI Audit'),
+    ('🎓', '보안 교육', 'AI 인식'),
+    ('📜', '보안 정책', 'AI 정책'),
+    ('🏅', '보안 인증', 'ISMS-P'),
+    # ── 데이터·AI 세분 (10) ──
+    ('📦', '데이터 카탈로그', 'AI 카탈로그'),
+    ('', '데이터 파이프', 'ETL AI'),
+    ('🔗', '데이터 라인age', '추적 AI'),
+    ('✨', '데이터 품질', 'AI 검증'),
+    ('🛡', '데이터 프라이버시', 'PET'),
+    ('🗄', 'Data Mesh', '분산 거버넌스'),
+    ('🧠', 'MLOps', 'AI 운영'),
+    ('🔄', '모델 라이프', 'AI 관리'),
+    ('', 'AI Governance', 'ISO 42001'),
+    ('⚖', 'AI 윤리', 'Bias·Fairness'),
+    # ── LLM 응용 세분 (10) ──
+    ('💬', 'LLM Chatbot', '기업 챗봇'),
+    ('🤖', 'LLM Agent', 'Agentic AI'),
+    ('🧠', 'Reasoning', 'o3급 추론'),
+    ('💻', 'Code Agent', 'Devin·Cursor'),
+    ('📖', '문서 LLM', '회사 KB'),
+    ('🎙', '음성 LLM', 'Voice Native'),
+    ('🖼', 'Vision LLM', '이미지 이해'),
+    ('🎬', 'Video LLM', '영상 이해'),
+    ('🌍', '다국어 LLM', 'Translation'),
+    ('', 'Domain LLM', '특화 LLM'),
+    # ── 신영역·미래 (10) ──
+    ('🌡', '기후·날씨', 'Climate AI'),
+    ('🧬', '합성생물', 'BioDesign'),
+    ('🦠', '미생물·식품', 'Microbiome'),
+    ('🐟', '수산·해양', 'Ocean AI'),
+    ('🌳', '임업·산림', 'Forest AI'),
+    ('♻', '재활용·환경', 'Circular AI'),
+    ('🚰', '수자원·수도', 'Water AI'),
+    ('⚱', '폐기물', 'Waste AI'),
+    ('🌋', '재난·재해', 'Disaster AI'),
+    ('🏛', '문화재·문화', 'Heritage AI'),
+    # ── 라이프·소비 (10) ──
+    ('🍽', '식품·외식', 'F&B AI'),
+    ('💄', '패션·뷰티', 'Fashion AI'),
+    ('🎮', '게임·메타버스', 'Game AI'),
+    ('🎭', '엔터테인먼트', 'Entertainment'),
+    ('✈', '관광·여행', 'Travel AI'),
+    ('⚽', '스포츠 AI', 'Sports Analytics'),
+    ('📡', '통신·5G', 'Telecom AI'),
+    ('🚙', '자동차 일반', 'Auto AI'),
+    ('', '화학·석유', 'Chemical AI'),
+    ('🏘', '부동산 일반', 'PropTech'),
+]
+
+# 신기술 풀 (각 영역에 적용)
+TECHS = [
+    'Llama 4 + 도메인 LoRA', 'Llama 4 Reasoning (o3급)', 'Llama 4 Scout (1M context)',
+    'Llama 4 Vision (Multimodal)', 'Llama 4 Voice (실시간)', 'Llama 4 ×3 다중 합의',
+    'Llama 4 + Causal AI (DoWhy)', 'Llama 4 + GraphRAG (Neo4j)', 'Llama 4 + Constitutional',
+    'Llama 4 + Computer Use', 'Llama 4 + MCP Tool', 'Llama 4 + MemGPT 장기기억',
+    'NVIDIA Cosmos World Model', 'OpenVLA (Vision-Language-Action)', 'NVIDIA GR00T (Humanoid)',
+    'Sim-to-Real (Isaac)', 'Affective Computing', 'Behavioral Biometrics',
+    'Continuous Authentication', 'Deepfake Detection', 'C2PA Watermark',
+    'AI Workload Protection', 'NHI (Non-Human Identity)', 'CSMA', 'DSPM',
+    'Federated Learning (Flower)', 'Confidential Computing', 'Homomorphic Encryption',
+    'Differential Privacy', 'Synthetic Data', 'Quantum ML (IBM)',
+]
+
+SUBCATS = ['진단·자동탐지', '예측·예방', '자동화·운영', '컨설팅·인증', '글로벌 진출',
+           '한국 표준', '데이터 마켓', '교육·자격', 'SaaS', '통합 SI']
+
+INFRA_MAP = {
+    'Quantum': 'IBM Quantum (무료)',
+    'Cosmos': 'NVIDIA Cluster (1억) + Mac Studio',
+    'GR00T': 'NVIDIA Cluster + 로봇 HW',
+    'Humanoid': 'Mac Studio 3대 + Robot',
+    'AlphaFold': 'Mac Studio 3대 + GPU',
+    'BCI': 'Mac Studio + BCI HW',
+}
+
+REVENUES = ['1社 1-3억', '1社 3-7억', '월 100-500만', '월 500-2000만',
+            'B2G 5-30억', '대당 1-3억', '1프로젝트 3-10억', '월구독 100-1000만',
+            'OEM 라이선스', '데이터 라이선스']
+
+
+def get_infra(tech):
+    for key, val in INFRA_MAP.items():
+        if key in tech:
+            return val
+    return 'Mac Studio 1-2대 (1.5-3천만)'
+
+
+COLORS = ['1976D2','7B1FA2','E64A19','388E3C','0288D1','9C27B0','455A64','9E9D24','558B2F','FFA000',
+          '00838F','5D4037','827717','6A1B9A','C2185B','283593','00695C','EF6C00','BF360C','37474F'] * 5
+
+parts = []
+for area_idx, (emoji, area_name, sub_desc) in enumerate(AREAS):
+    color = COLORS[area_idx % len(COLORS)]
+    base = area_idx * 30
+
+    parts.append(f"""
+<div class="area" id="a{area_idx+1}" style="border-left-color:#{color}">
+  <div class="area-head" style="background:linear-gradient(90deg,#{color},#{color}AA)">
+    <div class="ae">{emoji}</div>
+    <div><div class="an">{area_idx+1}. {area_name} (30개)</div><div class="ao">{sub_desc} · #{base+1:04d}-#{base+30:04d}</div></div>
+  </div>
+  <div class="grid">""")
+
+    for i in range(30):
+        sub_idx = i // 3
+        tech_idx = i % len(TECHS)
+        sub = SUBCATS[sub_idx]
+        tech = TECHS[tech_idx]
+        prod_num = base + i + 1
+        name = f'{area_name[:6]}-{sub[:4]}-{i+1:02d}'
+        what = f'{area_name} {sub} — {tech} 기반 자동화·정확도 향상'
+        how = f'① {tech} → ② {area_name} 도메인 LoRA → ③ 자사 모듈 통합'
+        infra = get_infra(tech)
+        target = f'{area_name} 도입 기업'
+        rev = REVENUES[prod_num % len(REVENUES)]
+
+        parts.append(f"""<div class="c">
+  <div class="ch"><div class="cn">#{prod_num:04d}</div><div class="cnm">{name}</div></div>
+  <div class="ct">🦙 {tech}</div>
+  <div class="cw">📋 {what}</div>
```

## Action
1. 변경된 public API 추출 (함수·클래스·exports)
2. CHANGELOG.md `[Unreleased]` 섹션에 entry 추가:
   - Added/Changed/Fixed/Removed/Security 분류
3. README.md 의 API 섹션 갱신 (있을 시)
4. docs/api/<module>.md 갱신 (있을 시)

## Constraints
- 기존 entry 덮어쓰기 X (append)
- 자동 commit X (사용자 review 대기)
- 내부 helper 변경 skip (public API 만)
