# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\build-100-areas-v2.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/build-100-areas-v2.py b/.claude/scripts/build-100-areas-v2.py
new file mode 100644
index 0000000..0d6b1e6
--- /dev/null
+++ b/.claude/scripts/build-100-areas-v2.py
@@ -0,0 +1,322 @@
+"""100 영역 v2 — 부서 관련도 표시 + 강조 + 한 행 2개
+
+사용자 피드백:
+- 건설 ERP 같이 부서 무관 영역 표시
+- 글씨 작음 → 2 column
+- 부서가 해야 할 것 강조
+- 조사만 하지 말고 추천
+"""
+import os
+
+ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+OUT = os.path.join(ROOT, 'outputs', 'itcen', 'html', 'itcen-core-100영역-3000신상품.html')
+
+# 100 영역 + 부서 관련도 (CORE·HIGH·MED·LOW)
+# 부서 = 리스크모니터링·행동위험분석
+AREAS = [
+    # (이모지, 이름, 설명, 부서관련도)
+    # ── 자사 (10) ──
+    ('📒', '내부회계', 'MicroICM-C 1위', 'HIGH'),
+    ('⚖️', 'CCP 준법경영', 'EPM 1위', 'CORE'),
+    ('🏗️', '건설 ERP', '건설업 표준', 'LOW'),
+    ('🎰', '카지노 VMS', '9社 독점', 'CORE'),
+    ('🏦', '금융 VMS', '은행·증권', 'CORE'),
+    ('📹', 'AI CCTV', '영상 분석', 'HIGH'),
+    ('🌐', '디지털트윈', '제조·건설', 'MED'),
+    ('⚙️', 'ITO 운영', 'IT 운영', 'MED'),
+    ('🌱', 'ESG·GRC', '거버넌스', 'HIGH'),
+    ('🚨', '부서 IP', 'K-Standard', 'CORE'),
+    # ── 그룹·신영역 (10) ──
+    ('🏛️', '공공·전자정부', 'ENTEC 협업', 'MED'),
+    ('☁️', '클라우드', 'CTS·CLOIT', 'MED'),
+    ('🛡️', '사이버보안', 'PNS 협업', 'CORE'),
+    ('📊', '데이터 거버넌스', '데이터 관리', 'CORE'),
+    ('🏥', '의료 종합', 'AI 진료', 'LOW'),
+    ('📚', '교육·이러닝', 'AI 튜터', 'LOW'),
+    ('🛒', '유통·이커머스', 'AI 추천', 'LOW'),
+    ('🏭', '제조 SI', '스마트팩토리', 'LOW'),
+    ('🚛', '물류·SCM', '공급망', 'LOW'),
+    ('🎬', '미디어·콘텐츠', '영상·음악', 'LOW'),
+    # ── 산업 (10) ──
+    ('🌾', '농업·스마트팜', '농업 AI', 'LOW'),
+    ('⚡', '에너지·SMR', '발전', 'LOW'),
+    ('🚗', '자율주행', '모빌리티', 'LOW'),
+    ('🚀', '우주·항공', '위성', 'LOW'),
+    ('🧪', '신소재', 'AI 발견', 'LOW'),
+    ('🧬', '바이오·신약', 'AI 신약', 'LOW'),
+    ('🛡️', 'K-방산', '국방', 'MED'),
+    ('⚛️', '양자컴퓨팅', 'IBM Quantum', 'HIGH'),
+    ('🤖', '휴머노이드', '로봇 AI', 'MED'),
+    ('🌟', '합성데이터', '데이터 마켓', 'HIGH'),
+    # ── 의료 세분 (10) ──
+    ('🩺', '진료·EHR', 'AI scribe', 'LOW'),
+    ('🔬', '진단·영상', 'Med 영상', 'LOW'),
+    ('💉', '예방·검진', 'AI 검진', 'LOW'),
+    ('🧪', '임상시험', 'AI CRO', 'LOW'),
+    ('🦾', '재활·정형', 'AI 재활', 'LOW'),
+    ('🧠', '정신건강', 'AI 상담', 'LOW'),
+    ('💊', '약학·복약', 'AI 처방', 'LOW'),
+    ('👩‍⚕️', '간호 AI', '간호 보조', 'LOW'),
+    ('🏨', '요양·노인', 'AI 돌봄', 'LOW'),
+    ('🦷', '치의학', 'AI 진단', 'LOW'),
+    # ── 금융 세분 (10) ──
+    ('💳', '카드·결제', 'AI 결제', 'HIGH'),
+    ('🏛️', '은행 코어', '코어뱅킹', 'HIGH'),
+    ('📈', '증권·트레이딩', 'AI 트레이딩', 'MED'),
+    ('🏠', '보험 AI', '인수·청구', 'HIGH'),
+    ('💰', '자산운용', 'AI 펀드', 'MED'),
+    ('₿', '암호·핀테크', 'DeFi', 'MED'),
+    ('💵', 'CBDC', '한은 디지털', 'HIGH'),
+    ('📊', '신용평가', 'AI 신용', 'CORE'),
+    ('🏘️', '부동산·리츠', 'AI 가치', 'LOW'),
+    ('💎', 'WM·HNWI', 'AI 자문', 'MED'),
+    # ── 사이버보안 세분 (10) — 거의 다 CORE ──
+    ('🔐', '인증·IAM', 'AI 신원', 'CORE'),
+    ('🛂', '접근통제', 'Zero Trust', 'CORE'),
+    ('🔑', '암호·PKI', 'PQC', 'CORE'),
+    ('👁️', 'SOC·관제', '24/7 자율', 'CORE'),
+    ('🚨', '사고대응 IR', 'AI SOAR', 'CORE'),
+    ('🔍', '포렌식', 'AI 분석', 'HIGH'),
+    ('📋', '보안 감사', 'AI Audit', 'CORE'),
+    ('🎓', '보안 교육', 'AI 인식', 'MED'),
+    ('📜', '보안 정책', 'AI 정책', 'CORE'),
+    ('🏅', '보안 인증', 'ISMS-P', 'CORE'),
+    # ── 데이터·AI 세분 (10) ──
+    ('📦', '데이터 카탈로그', 'AI 카탈로그', 'HIGH'),
+    ('🌊', '데이터 파이프', 'ETL AI', 'MED'),
+    ('🔗', '데이터 라인age', '추적 AI', 'HIGH'),
+    ('✨', '데이터 품질', 'AI 검증', 'HIGH'),
+    ('🛡️', '데이터 프라이버시', 'PET', 'CORE'),
+    ('🗄️', 'Data Mesh', '분산', 'MED'),
+    ('🧠', 'MLOps', 'AI 운영', 'HIGH'),
+    ('🔄', '모델 라이프', 'AI 관리', 'HIGH'),
+    ('🎯', 'AI Governance', 'ISO 42001', 'CORE'),
+    ('⚖️', 'AI 윤리', 'Bias·Fairness', 'CORE'),
+    # ── LLM 응용 (10) ──
+    ('💬', 'LLM Chatbot', '기업 챗봇', 'HIGH'),
+    ('🤖', 'LLM Agent', 'Agentic', 'CORE'),
+    ('🧠', 'Reasoning LLM', 'o3급', 'CORE'),
+    ('💻', 'Code Agent', 'Devin', 'MED'),
+    ('📖', '문서 LLM', '회사 KB', 'HIGH'),
+    ('🎙️', '음성 LLM', 'Voice', 'MED'),
+    ('🖼️', 'Vision LLM', '이미지', 'HIGH'),
+    ('🎬', 'Video LLM', '영상', 'HIGH'),
+    ('🌍', '다국어 LLM', 'Translation', 'LOW'),
+    ('🎯', 'Domain LLM', '특화', 'CORE'),
+    # ── 신영역 (10) ──
+    ('🌡️', '기후·날씨', 'Climate AI', 'LOW'),
+    ('🧬', '합성생물', 'BioDesign', 'LOW'),
+    ('🦠', '미생물·식품', 'Microbiome', 'LOW'),
+    ('🐟', '수산·해양', 'Ocean AI', 'LOW'),
+    ('🌳', '임업·산림', 'Forest AI', 'LOW'),
+    ('♻️', '재활용·환경', 'Circular AI', 'LOW'),
+    ('🚰', '수자원', 'Water AI', 'LOW'),
+    ('⚱️', '폐기물', 'Waste AI', 'LOW'),
+    ('🌋', '재난·재해', 'Disaster AI', 'MED'),
+    ('🏛️', '문화재·문화', 'Heritage AI', 'LOW'),
+    # ── 라이프 (10) — 거의 LOW ──
+    ('🍽️', '식품·외식', 'F&B AI', 'LOW'),
+    ('💄', '패션·뷰티', 'Fashion AI', 'LOW'),
+    ('🎮', '게임·메타버스', 'Game AI', 'LOW'),
+    ('🎭', '엔터테인먼트', 'Entertainment', 'LOW'),
+    ('✈️', '관광·여행', 'Travel AI', 'LOW'),
+    ('⚽', '스포츠 AI', 'Sports', 'LOW'),
+    ('📡', '통신·5G', 'Telecom AI', 'MED'),
+    ('🚙', '자동차 일반', 'Auto AI', 'LOW'),
+    ('🧪', '화학·석유', 'Chemical AI', 'LOW'),
+    ('🏘️', '부동산 일반', 'PropTech', 'LOW'),
+]
+
+# 관련도별 색·표시
+REL_STYLE = {
+    'CORE': ('#FFD600', '#5D4037', '⭐⭐⭐ CORE — 부서 즉시 추진'),
+    'HIGH': ('#81C784', '#1B5E20', '⭐⭐ HIGH — 부서 우선순위'),
+    'MED':  ('#90CAF9', '#0D47A1', '⭐ MED — 그룹 협업 가능'),
+    'LOW':  ('#E0E0E0', '#616161', '○ LOW — 부서 무관 (참고용)'),
+}
+
+TECHS = [
+    'Llama 4 + 도메인 LoRA', 'Llama 4 Reasoning', 'Llama 4 Scout (1M)',
+    'Llama 4 Vision', 'Llama 4 Voice', 'Llama 4 ×3 다중 합의',
+    'Causal AI (DoWhy)', 'GraphRAG (Neo4j)', 'Constitutional AI',
+    'Computer Use', 'MCP Tool', 'MemGPT 장기기억',
+    'World Models', 'OpenVLA', 'GR00T',
+    'Affective Computing', 'Behavioral Biometrics', 'Continuous Auth',
+    'Deepfake Detection', 'C2PA', 'AI Workload Protection', 'NHI', 'CSMA', 'DSPM',
+    'Federated Learning', 'Confidential Computing', 'Homomorphic', 'DP',
+    'Synthetic Data', 'Quantum ML', 'PQC',
+]
+
+SUBCATS = ['진단·자동탐지', '예측·예방', '자동화·운영', '컨설팅·인증', '글로벌 진출',
+           '한국 표준', '데이터 마켓', '교육·자격', 'SaaS', '통합 SI']
+
+INFRA_MAP = {
+    'Quantum': 'IBM Quantum (무료)',
+    'World Models': 'NVIDIA Cluster + Mac Studio',
+    'GR00T': 'NVIDIA Cluster + 로봇',
+}
+
+REVENUES = ['1社 1-3억', '1社 3-7억', '월 100-500만', '월 500-2000만',
+            'B2G 5-30억', '1프로젝트 3-10억', '월구독', 'OEM 라이선스']
+
+def get_infra(tech):
+    for k, v in INFRA_MAP.items():
+        if k in tech:
+            return v
+    return 'Mac Studio 1-2대 (1.5-3천만)'
+
+# 관련도별 정렬 (CORE 먼저)
+REL_ORDER = {'CORE': 0, 'HIGH': 1, 'MED': 2, 'LOW': 3}
+AREAS_SORTED = sorted(enumerate(AREAS, 1), key=lambda x: REL_ORDER[x[1][3]])
+
+parts = []
+for orig_idx, (emoji, name, sub_desc, rel) in AREAS_SORTED:
+    bg_color, text_color, rel_label = REL_STYLE[rel]
+    base = (orig_idx - 1) * 30
+
+    # CORE/HIGH 강조
+    border_style = f'border-left:8px solid {bg_color}'
+    if rel in ['CORE', 'HIGH']:
+        border_style += f';box-shadow:0 4px 12px {bg_color}66'
+
+    parts.append(f"""
+<div class="area" id="a{orig_idx}" style="{border_style}">
+  <div class="area-head" style="background:{bg_color};color:{text_color}">
+    <div class="ae">{emoji}</div>
+    <div style="flex:1">
+      <div class="an">{orig_idx}. {name}</div>
+      <div class="ao">{sub_desc} · #{base+1:04d}-#{base+30:04d}</div>
+    </div>
+    <div class="rel" style="color:{text_color}">{rel_label}</div>
+  </div>
+  <div class="grid">""")
+
+    for i in range(30):
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
